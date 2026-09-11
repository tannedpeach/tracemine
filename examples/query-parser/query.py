"""Token values for a shell-like search box. Positions are not yet available."""
import shlex


def tokenize(query: str) -> list[str]:
    return shlex.split(query, comments=False, posix=True)
