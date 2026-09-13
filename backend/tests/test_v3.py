"""Validate the frozen evaluator expectations without making any model calls."""

from pathlib import Path

import pytest

from app.repository import run_tests, snapshot

PROJECT = Path(__file__).resolve().parents[2]
CASES = [
    ("async-cache", "async_cache", "cache"),
    ("durable-delivery", "durable_delivery", "worker"),
    ("snapshot-catalog", "snapshot_catalog", "catalog"),
]


@pytest.mark.parametrize("fixture,evaluator,module", CASES)
async def test_v3_baseline_and_evaluator_reference(fixture, evaluator, module, tmp_path):
    repo = tmp_path / "repo"
    snapshot(PROJECT / "examples" / fixture, repo)
    logs = tmp_path / "logs"
    baseline = await run_tests(repo, "python3 -m pytest -q", logs, "baseline", 30)
    assert baseline.exit_code == 0, (logs / "baseline.stderr").read_text()
    grader = PROJECT / "evaluators/v3" / f"{evaluator}.py"
    # The unchanged baseline is healthy but does not implement the new requirements.
    unchanged = await run_tests(repo, "true", logs, "unchanged", 30, grader)
    assert unchanged.exit_code != 0 and not unchanged.timed_out
    (repo / f"{module}.py").write_text((Path(__file__).parent / "v3_reference.py").read_text())
    if fixture == "snapshot-catalog":
        api = repo / "api.py"
        api.write_text(
            api.read_text() + "\n    def page_items(self, limit=20, cursor=None):\n"
            "        return self.catalog.page(limit=limit, cursor=cursor)\n"
        )
    reference = await run_tests(repo, "python3 -m pytest -q", logs, "reference", 30, grader)
    assert reference.exit_code == 0, (logs / "reference.stderr").read_text()
