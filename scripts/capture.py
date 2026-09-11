#!/usr/bin/env python3
"""Section 33 gate: preserve a real Codex stream without touching the source."""

import argparse
import asyncio
import json
import os
import shutil
import signal
import subprocess
import tempfile
from pathlib import Path


async def capture(source: Path, task: str, timeout: float) -> int:
    source = source.resolve(strict=True)
    if not source.is_dir():
        raise ValueError("Repository must be a directory")
    root = Path(tempfile.mkdtemp(prefix="tracemine-capture-"))
    repo = root / "repo"

    # Never retain symlinks, Git hooks/config, or an external .git worktree link.
    def ignore(directory: str, names: list[str]) -> list[str]:
        return [
            n
            for n in names
            if n in {".git", ".venv", "node_modules", "__pycache__", ".env"}
            or (Path(directory) / n).is_symlink()
        ]

    shutil.copytree(source, repo, ignore=ignore)
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    print(f"Artifacts: {root}", flush=True)
    with (root / "events.jsonl").open("wb") as stdout, (root / "stderr.log").open("wb") as stderr:
        proc = await asyncio.create_subprocess_exec(
            "codex",
            "exec",
            "--json",
            "--ephemeral",
            "--ignore-user-config",
            "--sandbox",
            "workspace-write",
            "-C",
            str(repo),
            "-",
            stdin=asyncio.subprocess.PIPE,
            stdout=stdout,
            stderr=stderr,
            start_new_session=True,
        )
        try:
            await asyncio.wait_for(proc.communicate(task.encode()), timeout)
        except (TimeoutError, asyncio.CancelledError):
            os.killpg(proc.pid, signal.SIGKILL)
            await proc.wait()
            raise
    records = []
    for line in (root / "events.jsonl").read_text().splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            records.append({"unparseable": line})
    (root / "capture.json").write_text(
        json.dumps({"exit_code": proc.returncode, "record_count": len(records)}, indent=2)
    )
    print(f"Codex exit code: {proc.returncode}; captured records: {len(records)}")
    return proc.returncode or 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("task")
    parser.add_argument("--timeout", type=float, default=180)
    args = parser.parse_args()
    raise SystemExit(asyncio.run(capture(args.repo, args.task, args.timeout)))
