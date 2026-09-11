import asyncio
import json
import sys

import pytest
from pydantic import ValidationError

from app.adapter import normalize
from app.diagnosis import recovery_prompt, validate_diagnosis
from app.lifecycle import Runner
from app.models import Diagnosis, ProcessResult, RunRequest
from app.process import execute
from app.repository import capture_diff, run_tests, snapshot, validate_source, working_copy
from app.store import Store


@pytest.fixture
def source(tmp_path):
    repo = tmp_path / "source"
    repo.mkdir()
    (repo / "app.py").write_text("VALUE = 1\n")
    return repo


def test_snapshot_independent_of_source_and_git_metadata(source, tmp_path):
    (source / ".git").write_text("gitdir: /not/copied")
    (source / ".env").write_text("TOKEN=not-a-real-token")
    saved = tmp_path / "snapshot"
    digest = snapshot(source, saved)
    working_copy(saved, tmp_path / "working")
    (tmp_path / "working" / "app.py").write_text("VALUE = 2\n")
    (tmp_path / "working" / "new.py").write_text("NEW = True\n")
    diff, names = capture_diff(saved, tmp_path / "working", tmp_path / "diff")
    assert "app.py" in names and "new.py" in names
    assert "+VALUE = 2" in diff
    assert (source / "app.py").read_text() == "VALUE = 1\n"
    assert not (saved / ".env").exists()
    assert len(digest) == 64


def test_symlinks_rejected(source, tmp_path):
    (source / "escape.py").symlink_to(tmp_path / "elsewhere")
    with pytest.raises(ValueError, match="Symlinks"):
        snapshot(source, tmp_path / "snapshot")
    assert not (tmp_path / "snapshot").exists()


def test_nested_storage_rejected(source):
    with pytest.raises(ValueError, match="separate"):
        validate_source(source, source / "data")


@pytest.mark.parametrize("line", [b"not json", b"null", b"[]", b'{"type":"future.event"}'])
def test_unknown_and_malformed_events_retained(line):
    event = normalize(line, 1)
    assert event.raw_event and event.id == "e00001"


def test_command_normalization():
    event = normalize(
        b'{"type":"item.completed","item":{"id":"x","type":"command_execution",'
        b'"command":"pytest -q","aggregated_output":"1 failed","exit_code":1}}',
        8,
    )
    assert event.action_id == "x" and event.summary == "1 failed"


async def test_subprocess_captures_exit_and_raw_bytes(tmp_path):
    result = await execute(
        [sys.executable, "-c", "import sys; print('hello'); sys.stderr.write('err'); sys.exit(7)"],
        tmp_path,
        tmp_path / "logs",
        "test",
        10,
    )
    assert result.exit_code == 7
    assert (tmp_path / "logs/test.stdout").read_bytes() == b"hello\n"
    assert (tmp_path / "logs/test.stderr").read_bytes() == b"err"


async def test_timeout_preserves_partial_logs(tmp_path):
    result = await execute(
        [sys.executable, "-u", "-c", "import time; print('start'); time.sleep(30)"],
        tmp_path,
        tmp_path / "logs",
        "test",
        0.15,
    )
    assert result.timed_out and result.exit_code != 0
    assert b"start" in (tmp_path / "logs/test.stdout").read_bytes()


async def test_test_shell_cannot_write_source(source, tmp_path):
    import shlex

    repo = tmp_path / "working"
    repo.mkdir()
    command = f"printf changed > {shlex.quote(str(source / 'app.py'))}"
    result = await run_tests(repo, command, tmp_path / "logs", "test", 10)
    assert result.exit_code != 0
    assert (source / "app.py").read_text() == "VALUE = 1\n"


def diagnosis_data():
    return dict(
        status="diagnosed",
        first_consequential_event_id="e00001",
        failure_mode="regression",
        explanation="Observed change caused the failing assertion.",
        evidence=["e00001 changes VALUE"],
        suggested_intervention="Check the existing value contract before editing.",
        confidence=0.6,
    )


def test_diagnosis_schema_and_event_reference():
    events = [normalize(b"{}", 1)]
    assert validate_diagnosis(json.dumps(diagnosis_data()), events).confidence == 0.6
    with pytest.raises(ValueError, match="does not exist"):
        validate_diagnosis(json.dumps(diagnosis_data()), [])
    with pytest.raises(ValidationError):
        Diagnosis(**(diagnosis_data() | {"confidence": 2}))
    with pytest.raises(ValidationError):
        Diagnosis(**(diagnosis_data() | {"status": "insufficient_evidence"}))


class FakeAgent:
    """Explicit test double. Never used as portfolio run evidence."""

    calls = 0

    async def run(self, working_directory, task, logs, on_event):
        self.calls += 1
        assert working_directory.name == "repo"
        assert (working_directory / "app.py").read_text() == "VALUE = 1\n"
        (working_directory / "app.py").write_text(
            "VALUE = 1\n" if "DIAGNOSTIC" in task else "VALUE = 2\n"
        )
        await on_event(
            normalize(b'{"type":"item.completed","item":{"id":"a","type":"file_change"}}', 1)
        )
        return ProcessResult(exit_code=0, duration_ms=1)


class FakeDiagnoser:
    async def diagnose(self, run, events, logs):
        return Diagnosis(**diagnosis_data())


async def test_baseline_failure_aborts_agent(source, tmp_path):
    agent = FakeAgent()
    store = Store(tmp_path / "data")
    runner = Runner(store, agent)
    run = runner.create(RunRequest(repo=str(source), task="change value", test_command="exit 3"))
    await runner.run(run)
    assert store.get(run.id).status == "baseline_failed"
    assert agent.calls == 0 and run.baseline.exit_code == 3


async def test_lifecycle_recovery_persistence_and_source_immutability(source, tmp_path):
    store = Store(tmp_path / "data")
    runner = Runner(store, FakeAgent(), FakeDiagnoser())
    req = RunRequest(
        repo=str(source),
        task="change value",
        test_command=f'{sys.executable} -c "from app import VALUE; assert VALUE == 1"',
    )
    original = runner.create(req)
    await runner.run(original)
    assert original.status == "failed"
    assert original.final_test.exit_code == 1
    assert original.action_count == 1
    assert original.diagnosis.first_consequential_event_id == "e00001"
    assert (source / "app.py").read_text() == "VALUE = 1\n"
    # Recovery must not silently use this new source state.
    (source / "app.py").write_text("VALUE = 99\n")
    recovery = runner.create(req, original)
    await runner.run(recovery)
    assert recovery.status == "succeeded"
    assert recovery.parent_run_id == original.id
    assert recovery.snapshot_digest == original.snapshot_digest
    reopened = Store(tmp_path / "data")
    assert reopened.get(recovery.id).final_test.exit_code == 0
    assert len(reopened.events(original.id)) == 1
    assert (source / "app.py").read_text() == "VALUE = 99\n"


def test_recovery_prompt_does_not_replace_task():
    text = recovery_prompt("Original task", "Targeted hint")
    assert "Original task" in text and "Targeted hint" in text
    assert "not as a guaranteed" in text


async def test_cancellation_is_persisted(source, tmp_path):
    class SlowAgent(FakeAgent):
        async def run(self, *args):
            await asyncio.sleep(30)

    store = Store(tmp_path / "data")
    runner = Runner(store, SlowAgent())
    run = runner.create(RunRequest(repo=str(source), task="wait", test_command="true"))
    task = asyncio.create_task(runner.run(run))
    for _ in range(200):
        if run.status == "running_agent":
            break
        await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert store.get(run.id).status == "cancelled"


def test_single_storage_owner(tmp_path):
    first = Store(tmp_path / "data")
    second = Store(tmp_path / "data")
    with first.claim():
        with pytest.raises(RuntimeError, match="already in use"):
            with second.claim():
                pass
    with second.claim():
        pass


def test_diff_ignores_agent_git_configuration(source, tmp_path):
    saved = tmp_path / "saved"
    snapshot(source, saved)
    repo = tmp_path / "working"
    working_copy(saved, repo)
    # A corrupted or hostile agent .git must not participate in diff capture.
    import shutil

    shutil.rmtree(repo / ".git")
    (repo / ".git").write_text("gitdir: /untrusted")
    (repo / "app.py").unlink()
    diff, files = capture_diff(saved, repo, tmp_path / "diff")
    assert files == ["app.py"] and "-VALUE = 1" in diff


async def test_large_line_and_invalid_utf8_remain_byte_exact(tmp_path):
    lines = []

    async def receive(line):
        lines.append(line)

    result = await execute(
        [sys.executable, "-c", "import sys; sys.stdout.buffer.write(b'x'*100000+b'\\n\\xff')"],
        tmp_path,
        tmp_path / "logs",
        "agent",
        10,
        on_line=receive,
    )
    assert result.exit_code == 0
    assert lines == [b"x" * 100000, b"\xff"]
    assert (tmp_path / "logs/agent.stdout").read_bytes() == b"x" * 100000 + b"\n\xff"


async def test_diagnosis_failure_does_not_erase_test_failure(source, tmp_path):
    class BrokenDiagnoser:
        async def diagnose(self, *args):
            raise ValueError("Model output did not match schema")

    store = Store(tmp_path / "data")
    runner = Runner(store, FakeAgent(), BrokenDiagnoser())
    run = runner.create(
        RunRequest(
            repo=str(source),
            task="change",
            test_command=f'{sys.executable} -c "from app import VALUE; assert VALUE == 1"',
        )
    )
    await runner.run(run)
    assert run.status == "failed" and run.final_test.exit_code == 1
    assert "schema" in run.diagnosis_error and run.diagnosis is None


async def test_baseline_mutation_does_not_leak_into_agent_input(source, tmp_path):
    store = Store(tmp_path / "data")
    runner = Runner(store, FakeAgent(), FakeDiagnoser())
    run = runner.create(
        RunRequest(repo=str(source), task="change", test_command="printf 'VALUE = 999' > app.py")
    )
    await runner.run(run)
    assert run.status == "succeeded"  # Exit code only; this command doesn't assert correctness.
    assert (source / "app.py").read_text() == "VALUE = 1\n"


async def test_tampered_snapshot_recovery_is_rejected(source, tmp_path):
    store = Store(tmp_path / "data")
    runner = Runner(store, FakeAgent(), FakeDiagnoser())
    request = RunRequest(
        repo=str(source),
        task="change",
        test_command=f'{sys.executable} -c "from app import VALUE; assert VALUE == 1"',
    )
    run = runner.create(request)
    await runner.run(run)
    assert run.status == "failed"
    (store.root / "snapshots" / run.snapshot_id / "app.py").write_text("VALUE = 999\n")
    retry = runner.create(request, run)
    await runner.run(retry)
    assert retry.status == "error" and "snapshot changed" in retry.error


def test_git_resolution_preserves_python_environment(monkeypatch):
    from app.process import clean_env

    monkeypatch.setenv("PATH", "/example/venv/bin:/usr/local/bin:/usr/bin:/bin")
    assert clean_env()["PATH"].split(":")[0] == "/example/venv/bin"
