#!/usr/bin/env python3
"""Run a fixed three-task suite once; retain every outcome and stop at a failure.

No model override, prompt mutation or automatic retry. Review a candidate failure
before using --recover RUN_ID. Resume skips recorded candidates in this data store.
"""

import argparse
import asyncio
import json
import tempfile
from pathlib import Path

from app.lifecycle import Runner
from app.models import Run, RunRequest
from app.repository import snapshot
from app.store import Store

PROJECT = Path(__file__).resolve().parents[1]
COMMAND = "python3 -m pytest -q"
CANDIDATES_V2 = tuple(json.loads((PROJECT / "scripts/candidate_suite_v2.json").read_text()))
CANDIDATES = (
    (
        "cursor-pagination",
        "Add cursor pagination to GET /items. Return at most limit items ordered by "
        "(created_at, id), using both fields in an opaque next_cursor when more results "
        "exist. Default limit is 100; accept integer limits 1 through 100. Reject malformed "
        "cursors and invalid limits with HTTP 400, including structurally valid encodings "
        "with incorrect field types. Preserve the existing response shape when all results "
        "fit on one page (omit next_cursor if there is no next page). Preserve payloads "
        "and app isolation. Add deterministic tests for duplicate timestamps, first/middle/"
        "final pages, malformed cursors, limit=1, stable ordering and complete traversal "
        "without duplicate or missing IDs. Verify the full suite.",
    ),
    (
        "idempotent-orders",
        "Add Idempotency-Key support to POST /orders. Same key and normalized body returns "
        "the original order and HTTP 201 without creating another order. Normalization is "
        "the existing SKU whitespace trimming, default quantity=1, and ignoring unknown "
        "fields. Different normalized body with the same key returns HTTP 409. Validation "
        "failure must not consume a key. Requests without the header keep existing behavior. "
        "Keys are scoped to an app instance. Store replay data independently of mutable "
        "request objects. Add deterministic tests for exact retry, normalized equivalent "
        "bodies, conflicts, validation failure followed by valid reuse, no-key behavior, "
        "and app isolation. Verify the full suite.",
    ),
    (
        "rate-limiter",
        "Migrate RateLimiter from fixed windows to a per-client sliding window allowing "
        "3 accepted requests in any 10-second window. Keep the injectable monotonic clock "
        "and allow(client) API. The fourth request is rejected; rejected requests must not "
        "extend the window. Exactly 10 seconds after the oldest accepted request, another "
        "is allowed. Clients and instances are isolated. Prune expired timestamps and keep "
        "per-client history bounded by the accepted-request limit. Add deterministic tests "
        "using a fake clock (no sleeps) for exact and just-before boundaries, crossing the "
        "old fixed-window boundary, repeated rejections, simultaneous timestamps, client "
        "isolation and pruning after long idle periods. Verify the full suite.",
    ),
)


def classify(run: Run) -> str:
    if run.status == "baseline_failed":
        return "baseline failure"
    if run.agent and (run.agent.exit_code or run.agent.timed_out):
        return "agent process error"
    if run.status == "succeeded":
        return "success"
    if (
        run.status == "failed"
        and run.agent_backend == "codex"
        and run.action_count > 0
        and run.baseline
        and run.baseline.exit_code == 0
        and not run.baseline.timed_out
        and run.agent
        and run.final_test
        and run.final_test.exit_code == 1
        and not run.final_test.timed_out
        and run.final_diff.strip()
        and run.snapshot_digest
        and not run.error
    ):
        return "coding failure candidate; manual review required"
    return "infrastructure error"


def record(ledger: Path, name: str, run: Run) -> None:
    """Idempotent append; write only measured values and portable identifiers."""
    marker = f"<!-- run:{run.id} -->"
    existing = ledger.read_text() if ledger.exists() else "# Live experiment ledger\n"
    if marker in existing:
        return
    with ledger.open("a") as output:
        output.write(
            f"\n## {name}: {run.created_at}\n\n{marker}\n"
            f"- Run: `{run.id}`; fixture: `examples/{name}`\n"
            f"- Task: {run.task}\n"
            f"- Test command: `{run.test_command}`\n"
            f"- Agent exit: {run.agent.exit_code if run.agent else 'not started'}; "
            f"final test exit: {run.final_test.exit_code if run.final_test else 'not run'}\n"
            f"- Actions: {run.action_count}; "
            f"agent duration: {run.agent.duration_ms if run.agent else 'not measured'} ms\n"
            f"- Classification: **{classify(run)}**\n"
            f"- Parent: {run.parent_run_id or 'none'}\n"
        )


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=PROJECT / ".tracemine-candidates")
    parser.add_argument("--ledger", type=Path, default=PROJECT / "docs/experiments.md")
    parser.add_argument("--recover", help="One manually reviewed parent run ID")
    parser.add_argument("--suite", choices=("v1", "v2"), default="v1")
    parser.add_argument(
        "--resume-process-error", help="One explicitly authorized process-error restart"
    )
    args = parser.parse_args()
    store = Store(args.data)
    runner = Runner(store)
    selected_candidates = CANDIDATES if args.suite == "v1" else CANDIDATES_V2
    index = store.root / f"candidate-suite-{args.suite}.json"
    with store.claim():
        store.interrupt_pending()
        attempted = json.loads(index.read_text()) if index.exists() else {}
        resumed = None
        if args.recover and args.resume_process_error:
            raise SystemExit("Choose either recovery or process restart")
        if args.resume_process_error:
            resumed = store.get(args.resume_process_error)
            if not resumed or classify(resumed) != "agent process error":
                raise SystemExit("Restart requires a retained agent process error")
            name = next((key for key, value in attempted.items() if value == resumed.id), None)
            if name not in dict(selected_candidates):
                raise SystemExit("Only an original suite candidate may be restarted once")
            with tempfile.TemporaryDirectory(prefix="tracemine-input-check-") as check:
                digest = snapshot(Path(resumed.source_repo), Path(check) / "copy")
            if digest != resumed.snapshot_digest:
                raise SystemExit("Candidate input changed; refusing restart")
            if f"{name}-process-restart" in attempted:
                raise SystemExit("This candidate already received its one authorized restart")
            parent = None
            candidates = [(name, resumed.task)]
        elif args.recover:
            parent = store.get(args.recover)
            if not parent or not classify(parent).startswith("coding failure candidate"):
                raise SystemExit("Recovery requires a normally completed coding failure")
            name = next((key for key, value in attempted.items() if value == parent.id), None)
            if name is None:
                raise SystemExit("Parent is not part of this fixed suite")
            name = Path(parent.source_repo).name
            key = f"{name}-recovery"
            if key in attempted:
                raise SystemExit(f"Recovery already attempted: {attempted[key]}")
            candidates = [(name, parent.task)]
        else:
            parent = None
            candidates = list(selected_candidates)
        for name, task in candidates:
            key = f"{name}-process-restart" if resumed else f"{name}-recovery" if parent else name
            if key in attempted:
                previous = store.get(attempted[key])
                if previous is None:
                    raise SystemExit("Suite index references a missing run; inspect storage")
                record(args.ledger, name, previous)
                print(f"Already attempted {key}: {previous.id} ({classify(previous)})", flush=True)
                continue
            run = runner.create(
                RunRequest(repo=str(PROJECT / "examples" / name), task=task, test_command=COMMAND),
                parent,
            )
            attempted[key] = run.id
            temporary = index.with_suffix(".tmp")
            temporary.write_text(json.dumps(attempted, indent=2) + "\n")
            temporary.replace(index)
            print(f"Running {key}: {run.id}", flush=True)
            try:
                await runner.run(run)
            finally:
                record(args.ledger, name, run)
                if resumed:
                    with args.ledger.open("a") as output:
                        output.write(
                            f"- Authorized process restart of: `{resumed.id}`; no diagnostic hint added.\n"
                        )
            outcome = classify(run)
            print(f"{run.id}: {outcome}", flush=True)
            if outcome.startswith("coding failure candidate"):
                print("Stop for manual diagnosis/evidence review before --recover.", flush=True)
                return 0
            if outcome != "success":
                print("Stop to resolve execution problems without consuming remaining candidates.")
                return 1
    print("Fixed suite exhausted. No new prompts or repeated attempts were generated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
