"""Candidate suite integrity; these tests do not invoke the model."""

import runpy
from pathlib import Path

import pytest

from app.models import ProcessResult, Run
from app.repository import run_tests, snapshot

PROJECT = Path(__file__).resolve().parents[2]
HARNESS = runpy.run_path(str(PROJECT / "scripts/find_demo_failure.py"))


@pytest.mark.parametrize("name,task", (*HARNESS["CANDIDATES"], *HARNESS["CANDIDATES_V2"]))
async def test_candidate_has_healthy_isolated_baseline(name, task, tmp_path):
    repo = tmp_path / "repo"
    snapshot(PROJECT / "examples" / name, repo)
    result = await run_tests(repo, HARNESS["COMMAND"], tmp_path / "logs", "baseline", 30)
    assert result.exit_code == 0, (tmp_path / "logs/baseline.stdout").read_text()
    assert not result.timed_out


def test_classifier_does_not_promote_process_errors_or_synthetic_runs():
    run = Run(
        id="test-only",
        source_repo="fixture",
        task="test",
        test_command="pytest",
        status="failed",
        snapshot_digest="digest",
        final_diff="diff",
        action_count=1,
        baseline=ProcessResult(exit_code=0, duration_ms=1),
        agent=ProcessResult(exit_code=0, duration_ms=1),
        final_test=ProcessResult(exit_code=1, duration_ms=1),
    )
    classify = HARNESS["classify"]
    assert classify(run).startswith("coding failure candidate")
    run.agent.exit_code = 1
    assert classify(run) == "agent process error"
    run.agent.exit_code = 0
    run.agent_backend = "test-double"
    assert classify(run) == "infrastructure error"


def test_ledger_is_idempotent_and_contains_no_source_path(tmp_path):
    run = Run(id="test-only", source_repo=str(tmp_path), task="test", test_command="pytest")
    ledger = tmp_path / "ledger.md"
    HARNESS["record"](ledger, "fixture", run)
    HARNESS["record"](ledger, "fixture", run)
    text = ledger.read_text()
    assert text.count("<!-- run:test-only -->") == 1
    assert str(tmp_path) not in text
