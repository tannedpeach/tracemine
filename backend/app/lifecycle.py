"""The MVP state machine. A retry always branches from the retained input snapshot."""

import asyncio
import shlex
import time
import uuid
from pathlib import Path

from .adapter import CodexAdapter, CodingAgentAdapter
from .diagnosis import Diagnoser, recovery_prompt
from .models import Event, Run, RunRequest, Status
from .process import clean_env, execute
from .repository import capture_diff, git, run_tests, snapshot, validate_source, working_copy
from .store import Store


class Runner:
    def __init__(
        self,
        store: Store,
        adapter: CodingAgentAdapter | None = None,
        diagnoser: Diagnoser | None = None,
        test_timeout: float = 120,
    ):
        self.store = store
        self.adapter = adapter or CodexAdapter()
        self.diagnoser = diagnoser or Diagnoser()
        self.test_timeout = test_timeout
        self.lock = asyncio.Lock()

    def create(self, request: RunRequest, parent: Run | None = None) -> Run:
        source = (
            parent.source_repo
            if parent
            else str(validate_source(Path(request.repo), self.store.root))
        )
        if parent:
            if (
                parent.status != "failed"
                or not parent.diagnosis
                or parent.diagnosis.status != "diagnosed"
            ):
                raise ValueError("Retry requires a failed run with a grounded diagnosis")
            if not (self.store.root / "snapshots" / parent.snapshot_id).is_dir():
                raise ValueError(
                    "Original input snapshot is unavailable; cannot perform a comparable retry"
                )
        run_id = uuid.uuid4().hex
        run = Run(
            id=run_id,
            source_repo=source,
            task=request.task,
            test_command=request.test_command,
            snapshot_id=parent.snapshot_id if parent else run_id,
            snapshot_digest=parent.snapshot_digest if parent else None,
            source_commit=parent.source_commit if parent else None,
            parent_run_id=parent.id if parent else None,
            intervention=parent.diagnosis.suggested_intervention
            if parent and parent.diagnosis
            else None,
        )
        self.store.save(run)
        return run

    def state(self, run: Run, status: Status) -> None:
        run.status = status
        self.store.save(run)

    async def run(self, run: Run) -> None:
        started = time.monotonic()
        try:
            async with self.lock:
                await self._run(run)
        except asyncio.CancelledError:
            run.error = "Run cancelled; partial raw logs are retained."
            self.state(run, "cancelled")
            raise
        except Exception as exc:
            run.error = f"{type(exc).__name__}: {exc}"
            self.state(run, "error")
        finally:
            run.duration_ms = round((time.monotonic() - started) * 1000)
            self.store.save(run)
            self.store.export_metadata(run)

    async def _run(self, run: Run) -> None:
        directory = self.store.run_dir(run.id)
        logs = directory / "logs"
        logs.mkdir(parents=True, exist_ok=True)
        saved = self.store.root / "snapshots" / run.snapshot_id
        self.state(run, "preparing")
        if not run.parent_run_id:
            source = validate_source(Path(run.source_repo), self.store.root)
            try:
                run.source_commit = (
                    await asyncio.to_thread(git, source, "rev-parse", "HEAD")
                ).strip()
            except ValueError:
                run.source_commit = None
            run.snapshot_digest = await asyncio.to_thread(snapshot, source, saved)
        repo = directory / "repo"
        run.working_repo = str(repo)
        run.original_commit = await asyncio.to_thread(working_copy, saved, repo)
        self.state(run, "baseline_testing")
        # Baseline tests may themselves mutate files: use a separate disposable copy.
        baseline_repo = directory / "baseline"
        baseline_digest = await asyncio.to_thread(snapshot, saved, baseline_repo)
        if baseline_digest != run.snapshot_digest:
            raise ValueError("Retained input snapshot changed; refusing a non-comparable run")
        run.baseline = await run_tests(
            baseline_repo, run.test_command, logs, "baseline", self.test_timeout
        )
        if run.baseline.timed_out:
            raise RuntimeError("Baseline tests timed out; agent was not started")
        if run.baseline.exit_code:
            run.error = (
                "Baseline tests already fail. TraceMine cannot attribute later failures "
                "to the agent until the baseline is healthy."
            )
            self.state(run, "baseline_failed")
            return

        self.state(run, "running_agent")
        if isinstance(self.adapter, CodexAdapter):
            version = await execute(["codex", "--version"], repo, logs, "codex-version", 15)
            if version.exit_code:
                raise RuntimeError("Unable to inspect Codex CLI version")
            run.codex_version = (logs / "codex-version.stdout").read_text().strip()
        action_ids: set[str] = set()

        async def on_event(event: Event):
            self.store.add_event(run.id, event)
            if event.action_id and event.event_type in {"command", "file_change", "tool", "search"}:
                action_ids.add(event.action_id)
                run.action_count = len(action_ids)
                self.store.save(run)

        prompt = recovery_prompt(run.task, run.intervention)
        # Login profiles may reset PATH. Give Codex the same prepared environment
        # that passed the baseline, without asking it to reinstall dependencies.
        scratch = repo / ".tracemine-tmp"
        scratch.mkdir(exist_ok=True)
        verifier = scratch / "verify"
        verifier.write_text(
            "#!/bin/sh\nset -eu\n"
            + "export PATH="
            + shlex.quote(clean_env()["PATH"])
            + "\n"
            + 'export TMPDIR="$PWD/.tracemine-tmp"\n'
            + "exec /bin/sh -c "
            + shlex.quote(run.test_command)
            + "\n"
        )
        prompt += (
            "\n\nTRACEMINE VERIFICATION ENVIRONMENT\n"
            "The baseline passed. Run `/bin/sh .tracemine-tmp/verify` to execute "
            "the supplied test command in the prepared Python environment. "
            "Login shells can reset PATH; the verifier restores the same PATH "
            "used for the baseline. Dependencies are already installed. "
            "The .tracemine-tmp directory is generated run infrastructure.\n"
        )
        (logs / "agent.prompt.txt").write_text(prompt)
        run.agent = await self.adapter.run(repo, prompt, logs, on_event)
        run.final_diff, run.files_changed = await asyncio.to_thread(
            capture_diff, saved, repo, directory / "diff-repo"
        )
        (logs / "final.diff").write_text(run.final_diff)
        self.state(run, "testing")
        # Final verification also uses a separate copy, preserving the exact agent output.
        final_repo = directory / "verification"
        await asyncio.to_thread(snapshot, repo, final_repo, False)
        run.final_test = await run_tests(
            final_repo, run.test_command, logs, "final", self.test_timeout
        )
        if run.agent.timed_out or run.agent.exit_code:
            raise RuntimeError(
                f"Agent process did not complete normally (exit {run.agent.exit_code}, "
                f"timeout {run.agent.timed_out}); final tests were still captured"
            )
        if run.final_test.timed_out:
            raise RuntimeError("Final tests timed out; no pass/fail conclusion")
        if run.final_test.exit_code == 0:
            self.state(run, "succeeded")
            return
        self.state(run, "diagnosing")
        try:
            run.diagnosis = await self.diagnoser.diagnose(run, self.store.events(run.id), logs)
        except Exception as exc:
            run.diagnosis_error = f"{type(exc).__name__}: {exc}"
        self.state(run, "failed")
