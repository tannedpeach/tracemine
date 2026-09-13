#!/usr/bin/env python3
"""Fetch pinned history and validate evaluators in disposable copies. No model calls."""

import asyncio
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from app.repository import git, run_tests, snapshot

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT / ".tracemine-history"
SUITE = json.loads((PROJECT / "scripts/historical_suite_v4.json").read_text())


def checkout(candidate: dict, revision: str, group: str) -> Path:
    upstream = ROOT / "upstream" / candidate["name"]
    if not upstream.exists():
        upstream.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--quiet", candidate["repository"], str(upstream)],
            check=True,
            timeout=120,
        )
    target = ROOT / group / candidate["name"]
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        git(upstream, "worktree", "add", "--detach", str(target), revision)
    if git(target, "rev-parse", "HEAD").strip() != revision:
        raise ValueError(f"Unexpected revision in {target}")
    if git(target, "status", "--porcelain").strip():
        raise ValueError(f"Source checkout is dirty: {target}")
    return target


async def main():
    ROOT.mkdir(exist_ok=True)
    audit = Path(tempfile.mkdtemp(prefix="preflight-", dir=ROOT))
    summary = []
    for candidate in SUITE:
        name = candidate["name"]
        evaluator = PROJECT / candidate["evaluator"]
        outcomes = {}
        for kind, field, expected in [("inputs", "base_commit", 1), ("fixes", "fix_commit", 0)]:
            source = checkout(candidate, candidate[field], kind)
            directory = audit / name / kind
            copied = directory / "baseline"
            digest = snapshot(source, copied)
            baseline = await run_tests(
                copied, candidate["test_command"], directory / "logs", "baseline", 120
            )
            regression_copy = directory / "regression"
            snapshot(source, regression_copy)
            result = await run_tests(
                regression_copy, "true", directory / "logs", "evaluator", 120, evaluator
            )
            outcomes[kind] = {
                "commit": candidate[field],
                "snapshot_digest": digest,
                "baseline": baseline.model_dump(),
                "evaluator": result.model_dump(),
            }
            print(
                name,
                kind,
                "baseline",
                baseline.exit_code,
                "evaluator",
                result.exit_code,
                flush=True,
            )
            if (
                baseline.exit_code
                or baseline.timed_out
                or result.timed_out
                or result.exit_code != expected
            ):
                raise RuntimeError(f"Historical preflight failed; inspect {directory / 'logs'}")
        summary.append(
            {
                "name": name,
                "evaluator_sha256": hashlib.sha256(evaluator.read_bytes()).hexdigest(),
                **outcomes,
            }
        )
    report = audit / "validation.json"
    report.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"Validated every historical candidate. Audit report: {report}")


if __name__ == "__main__":
    asyncio.run(main())
