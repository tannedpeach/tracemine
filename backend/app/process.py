"""One process owner: byte-exact logs, bounded event buffering, process-group cleanup."""

import asyncio
import os
import shutil
import signal
import subprocess
import sys
import time
from collections.abc import Awaitable, Callable
from functools import lru_cache
from pathlib import Path

from .models import ProcessResult

LineCallback = Callable[[bytes], Awaitable[None]]
MAX_LINE = 2 * 1024 * 1024
MAX_LOG = 64 * 1024 * 1024


@lru_cache(maxsize=1)
def git_binary_directory() -> str | None:
    # Apple's /usr/bin/git launcher may try to write Xcode caches in a sandbox.
    # Resolve the actual binary before launching restricted children.
    if sys.platform == "darwin" and shutil.which("xcrun"):
        resolved = subprocess.run(
            ["xcrun", "--find", "git"], capture_output=True, text=True, timeout=10, check=False
        )
        if resolved.returncode == 0 and Path(resolved.stdout.strip()).is_file():
            return str(Path(resolved.stdout.strip()).parent)
    return None


def clean_env() -> dict[str, str]:
    # Do not pass arbitrary application tokens to repository tests / agent commands.
    keys = ("PATH", "HOME", "LANG", "LC_ALL", "SYSTEMROOT", "CODEX_HOME")
    env = {key: os.environ[key] for key in keys if key in os.environ}
    entries = env.get("PATH", os.defpath).split(os.pathsep)
    if directory := git_binary_directory():
        index = entries.index("/usr/bin") if "/usr/bin" in entries else len(entries)
        entries.insert(index, directory)
        env["PATH"] = os.pathsep.join(entries)
    return env


async def execute(
    args: list[str],
    cwd: Path,
    logs: Path,
    name: str,
    timeout: float,
    on_line: LineCallback | None = None,
    stdin: str | None = None,
    env: dict[str, str] | None = None,
) -> ProcessResult:
    logs.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    proc = await asyncio.create_subprocess_exec(
        *args,
        cwd=cwd,
        env=env if env is not None else clean_env(),
        stdin=asyncio.subprocess.PIPE if stdin is not None else asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        start_new_session=True,
    )

    async def drain(reader: asyncio.StreamReader, path: Path, callback: LineCallback | None):
        pending = bytearray()
        count = 0
        oversized = False
        with path.open("wb") as output:
            while chunk := await reader.read(65536):
                output.write(chunk)
                output.flush()
                count += len(chunk)
                if count > MAX_LOG:
                    raise RuntimeError(
                        f"{path.name} exceeded 64 MiB; run stopped, raw prefix retained"
                    )
                if callback:
                    pending.extend(chunk)
                    while b"\n" in pending:
                        line, _, rest = pending.partition(b"\n")
                        pending = bytearray(rest)
                        if not oversized:
                            await callback(bytes(line))
                        oversized = False
                    if len(pending) > MAX_LINE:
                        await callback(
                            b'{"type":"capture.warning","message":"Oversized event; inspect raw log"}'
                        )
                        pending.clear()
                        oversized = True
            if callback and pending and not oversized:
                await callback(bytes(pending))

    async def feed():
        if proc.stdin is not None:
            try:
                proc.stdin.write((stdin or "").encode())
                await proc.stdin.drain()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                proc.stdin.close()

    assert proc.stdout is not None and proc.stderr is not None
    jobs = [
        asyncio.create_task(drain(proc.stdout, logs / f"{name}.stdout", on_line)),
        asyncio.create_task(drain(proc.stderr, logs / f"{name}.stderr", None)),
        asyncio.create_task(feed()),
        asyncio.create_task(proc.wait()),
    ]
    timed_out = False
    try:
        await asyncio.wait_for(asyncio.gather(*jobs), timeout)
    except TimeoutError:
        timed_out = True
    finally:
        # Also kill descendants that inherited pipes or outlived the leader.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        await proc.wait()
        for job in jobs:
            if not job.done():
                job.cancel()
        await asyncio.gather(*jobs, return_exceptions=True)
    assert proc.returncode is not None
    result = ProcessResult(
        exit_code=proc.returncode,
        timed_out=timed_out,
        duration_ms=round((time.monotonic() - started) * 1000),
    )
    (logs / f"{name}.result.json").write_text(result.model_dump_json(indent=2))
    return result
