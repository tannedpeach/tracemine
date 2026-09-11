"""Codex JSONL adapter; normalization is a view over the original byte stream."""

import json
import shutil
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from .models import Event, ProcessResult
from .process import clean_env, execute


def normalize(line: bytes, sequence: int) -> Event:
    text = line.decode("utf-8", errors="replace")
    try:
        raw = json.loads(text)
        if not isinstance(raw, dict):
            raw = {"type": "unknown", "value": raw}
    except json.JSONDecodeError:
        raw = {"type": "unparseable", "line": text}
    item = raw.get("item")
    item = item if isinstance(item, dict) else {}
    kind = str(item.get("type", raw.get("type", "unknown")))
    category = {
        "command_execution": "command",
        "file_change": "file_change",
        "agent_message": "message",
        "reasoning": "message",
        "mcp_tool_call": "tool",
        "web_search": "search",
    }.get(kind, "unknown")
    if "error" in str(kind) or kind == "turn.failed":
        category = "error"
    title = item.get("command") or item.get("text") or raw.get("message") or kind
    if kind == "file_change":
        changes = item.get("changes", [])
        if not isinstance(changes, list):
            changes = []
        title = "Edit " + ", ".join(str(c.get("path", "?")) for c in changes if isinstance(c, dict))
    return Event(
        id=f"e{sequence:05d}",
        sequence=sequence,
        timestamp=datetime.now(UTC).isoformat(),
        event_type=category,
        title=str(title)[:500],
        summary=str(item.get("aggregated_output", ""))[:12000],
        raw_event=raw,
        action_id=item.get("id") if isinstance(item.get("id"), str) else None,
    )


class CodingAgentAdapter(Protocol):
    async def run(
        self,
        working_directory: Path,
        task: str,
        logs: Path,
        on_event: Callable[[Event], Awaitable[None]],
    ) -> ProcessResult: ...


class CodexAdapter:
    def __init__(self, timeout: float = 600):
        self.timeout = timeout

    async def run(
        self,
        working_directory: Path,
        task: str,
        logs: Path,
        on_event: Callable[[Event], Awaitable[None]],
    ) -> ProcessResult:
        if not shutil.which("codex"):
            raise RuntimeError("Codex CLI not found on PATH. Install Codex and run codex login.")
        sequence = 0

        async def receive(line: bytes):
            nonlocal sequence
            sequence += 1
            await on_event(normalize(line, sequence))

        scratch = working_directory / ".tracemine-tmp"
        scratch.mkdir(exist_ok=True)
        env = clean_env() | {"TMPDIR": str(scratch), "TMP": str(scratch), "TEMP": str(scratch)}
        return await execute(
            [
                "codex",
                "exec",
                "--json",
                "--ephemeral",
                "--ignore-user-config",
                "--sandbox",
                "workspace-write",
                "-c",
                "sandbox_workspace_write.exclude_slash_tmp=true",
                "-c",
                "sandbox_workspace_write.exclude_tmpdir_env_var=true",
                "-C",
                str(working_directory),
                "-",
            ],
            working_directory,
            logs,
            "agent",
            self.timeout,
            on_line=receive,
            stdin=task,
            env=env,
        )
