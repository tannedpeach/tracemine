"""Content snapshots, independent Git metadata, and constrained test execution."""

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

from .models import ProcessResult
from .process import clean_env, execute

EXCLUDED = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tracemine",
    ".DS_Store",
    ".tracemine-tmp",
}
MAX_BYTES = 100 * 1024 * 1024


def git(repo: Path, *args: str) -> str:
    env = clean_env() | {
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_TERMINAL_PROMPT": "0",
    }
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", *args],
        cwd=repo,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode:
        raise ValueError(f"Git failed: {result.stderr.strip()[:2000]}")
    return result.stdout


def validate_source(source: Path, storage: Path) -> Path:
    source = source.expanduser().resolve(strict=True)
    if not source.is_dir():
        raise ValueError("Repository must be a local directory")
    if source == storage or source in storage.parents or storage in source.parents:
        raise ValueError("Source repository and TraceMine storage must be separate directories")
    return source


def snapshot(source: Path, target: Path, require_python: bool = True) -> str:
    """Reject symlinks/special files; never copy Git hooks, config, or external worktree links."""
    target.mkdir(parents=True)
    digest = hashlib.sha256()
    total = 0
    try:
        for directory, folders, files in os.walk(source, followlinks=False):
            folders[:] = sorted(
                n for n in folders if n not in EXCLUDED and not n.startswith("pytest-of-")
            )
            for name in folders + sorted(files):
                item = Path(directory) / name
                relative = item.relative_to(source)
                if name in EXCLUDED or name == ".env" or name.startswith(".env."):
                    if name in folders:
                        folders.remove(name)
                    continue
                mode = item.lstat().st_mode
                if stat.S_ISLNK(mode):
                    raise ValueError(f"Symlinks are not supported in MVP: {relative}")
                destination = target / relative
                if stat.S_ISDIR(mode):
                    destination.mkdir(exist_ok=True)
                elif stat.S_ISREG(mode):
                    total += item.stat().st_size
                    if total > MAX_BYTES:
                        raise ValueError("Repository exceeds the MVP 100 MiB snapshot limit")
                    data = item.read_bytes()
                    destination.write_bytes(data)
                    destination.chmod(0o755 if mode & stat.S_IXUSR else 0o644)
                    digest.update(
                        str(relative).encode()
                        + b"\0"
                        + str(0o111 if mode & stat.S_IXUSR else 0).encode()
                        + b"\0"
                        + data
                        + b"\0"
                    )
                else:
                    raise ValueError(f"Special files are not supported: {relative}")
    except BaseException:
        shutil.rmtree(target)
        raise
    if require_python and not any(target.rglob("*.py")):
        shutil.rmtree(target)
        raise ValueError("MVP supports Python repositories; no .py files found")
    return digest.hexdigest()


def working_copy(saved: Path, target: Path) -> str:
    shutil.copytree(saved, target)
    git(target, "init", "-q", "--template=")
    git(target, "add", "-f", ".")
    git(
        target,
        "-c",
        "user.name=TraceMine",
        "-c",
        "user.email=local@tracemine.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-qm",
        "TraceMine input snapshot",
        "--allow-empty",
    )
    return git(target, "rev-parse", "HEAD").strip()


def capture_diff(saved: Path, repo: Path, target: Path) -> tuple[str, list[str]]:
    # Agent-controlled Git configuration can define executable filters/hooks.
    # Compute the diff in fresh metadata outside the agent's writable directory.
    base = working_copy(saved, target)
    for item in target.iterdir():
        if item.name != ".git":
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
    clean = target.parent / "diff-content"
    snapshot(repo, clean, require_python=False)
    shutil.copytree(clean, target, dirs_exist_ok=True)
    git(target, "add", "-N", ".")
    diff = git(target, "diff", "--no-ext-diff", "--no-textconv", "--binary", base, "--")
    names = git(target, "diff", "--name-only", "-z", base, "--")
    return diff, [name for name in names.split("\0") if name]


def sandbox_command(repo: Path, command: str) -> tuple[list[str], dict[str, str]]:
    """Fail closed on unsupported platforms. The test shell can only write in its copy."""
    scratch = repo / ".tracemine-tmp"
    scratch.mkdir(exist_ok=True)
    env = clean_env() | {
        "TMPDIR": str(scratch),
        "TMP": str(scratch),
        "TEMP": str(scratch),
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    if sys.platform == "darwin" and shutil.which("sandbox-exec"):
        # sandbox-exec's profile is Scheme; JSON string quoting safely quotes paths.
        profile = (
            "(version 1)(allow default)(deny file-write*)(deny network*)"
            f"(allow file-write* (subpath {json.dumps(str(repo.resolve()))})"
            '(literal "/dev/null"))'
        )
        return ["sandbox-exec", "-p", profile, "/bin/sh", "-c", command], env
    if sys.platform == "linux" and shutil.which("bwrap"):
        return [
            "bwrap",
            "--die-with-parent",
            "--unshare-net",
            "--ro-bind",
            "/",
            "/",
            "--bind",
            str(repo),
            str(repo),
            "--dev",
            "/dev",
            "--proc",
            "/proc",
            "--chdir",
            str(repo),
            "/bin/sh",
            "-c",
            command,
        ], env
    raise RuntimeError(
        "Safe test execution requires macOS sandbox-exec or Linux bubblewrap (bwrap)"
    )


async def run_tests(
    repo: Path, command: str, logs: Path, name: str, timeout: float
) -> ProcessResult:
    args, env = sandbox_command(repo, command)
    return await execute(args, repo, logs, name, timeout, env=env)
