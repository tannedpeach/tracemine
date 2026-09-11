#!/usr/bin/env python3
"""Re-test a recorded agent's patch against its bundled input; no model call.

This checks that the committed outcome is reproducible in your environment.
It is not a new agent run and does not claim to reproduce model randomness.
"""

import argparse
import asyncio
import json
import tempfile
from pathlib import Path

from app.repository import git, run_tests, working_copy

PROJECT = Path(__file__).resolve().parents[1]


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_id")
    args = parser.parse_args()
    bundle = PROJECT / "examples/sample-runs" / args.run_id
    run = json.loads((bundle / "run.json").read_text())
    if run["final_test"] is None:
        raise SystemExit("This recording has no completed final verification to reproduce")
    # Keep separate verification artifacts for auditability, never overwrite the recording.
    directory = Path(tempfile.mkdtemp(prefix="tracemine-reproduce-"))
    repo = directory / "repo"
    working_copy(bundle / "input", repo)
    baseline_repo = directory / "baseline"
    working_copy(bundle / "input", baseline_repo)
    baseline = await run_tests(
        baseline_repo, run["test_command"], directory / "logs", "baseline", 120
    )
    if baseline.exit_code:
        raise SystemExit(f"Baseline failed; inspect {directory / 'logs'}")
    patch = bundle / "logs/final.diff"
    if patch.read_text().strip():
        # Early recordings lack Git's terminating LF. Restore only that delimiter.
        replay_patch = directory / "replay.diff"
        replay_patch.write_text(patch.read_text().rstrip("\n") + "\n")
        git(repo, "apply", str(replay_patch))
    final = await run_tests(repo, run["test_command"], directory / "logs", "final", 120)
    expected = run["final_test"]["exit_code"]
    print(f"Recorded final exit: {expected}; reproduced final exit: {final.exit_code}")
    print(f"New verification logs: {directory / 'logs'}")
    return 0 if final.exit_code == expected and not final.timed_out else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
