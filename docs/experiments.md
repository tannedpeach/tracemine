# Live experiment ledger

These are actual Codex invocations. Unit-test doubles are not experiments. All raw originals are retained in ignored local storage. Model results vary between runs.

| Experiment | Agent exit | Final test exit | Actions | Agent duration | Outcome |
|---|---:|---:|---:|---:|---|
| Section 33 isolated docstring + compilation | 0 | Separate compile in agent stream: 0 | Not measured by full runner | Not measured | JSONL capture gate passed (13 records) |
| Flask TTL caching (`11ab0…`) | 0 | 0 | 7 | 125.157 s | Supplied tests passed |
| Flask SQLite + idempotency (`1163b…`) | 0 | Not executed | 11 | 210.981 s | TraceMine verification preparation error |
| Flask SQLite/cache coherence (`b1a366…`) | 0 | 0 | 8 | 157.612 s | Supplied tests passed |
| Query tokenizer spans (`a14c5b…`) | 0 | 0 | 7 | 146.808 s | Supplied tests passed |
| GitHub import (`1c0be6…`) | 0 | 0 | 9 | 177.181 s | Supplied tests passed |
| Interval scheduler (`8b7251…`) | 0 | 0 | 7 | 93.024 s | Supplied tests passed |

The SQLite run reported 29 passing tests inside the agent workspace, but TraceMine did **not** independently verify them in that run: pytest generated temporary symlinks, and snapshot preparation rejected them. This was a TraceMine integration bug, not evidence of an agent coding failure. Temporary-directory handling was subsequently fixed. The original result and logs were not rewritten into a success.

The first bulk-pagination submission (`a1340…`) aborted before Codex because a
TraceMine PATH regression selected Xcode's Python without pytest. This was fixed.
The next submission (`e2bf9…`) hit the Codex account usage limit (agent exit 1);
its independent final test exit was 0. It remains an agent-process error, not a
claimed success or coding failure. A later cache-coherence experiment starts from
the actual successful cache implementation, with a prepared-environment verifier.

A genuine failed final test followed by diagnosed recovery is still being sought. Do not infer a recovery result from the unit-test suite or the example diagram.

## Finalization suite v1 (fixed, one pass)

| Candidate | Agent exit | Final test exit | Actions | Agent duration | Classification |
|---|---:|---:|---:|---:|---|
| Cursor pagination (`471b5f…`) | 0 | 0 | 7 | 147.059 s | Success; 52 tests passed |
| Idempotent orders (`98619d…`) | 0 | 0 | 7 | 112.850 s | Success; 21 tests passed |
| Sliding-window limiter (`2e84d4…`) | 1 | 5 | 5 | 58.247 s | Agent process error: Codex account usage limit; no final verification conclusion |

The suite was executed once in fixed order and stopped on the documented usage
error. No prompt mutation, environment sabotage or repeated attempt was used.

On September 12 the user authorized exactly one restart of the interrupted limiter.
It passed 6 tests (agent exit 0, final exit 0, 7 actions, 151.277 seconds).
The input digest and complete agent prompt match the interrupted attempt. This
completes suite v1 with no genuine coding failure. The original process error and
its raw logs remain retained. Suite v2 is fixed in docs/suite-v2.md before execution.

## cursor-pagination: 2026-09-11T22:58:50.840597+00:00

<!-- run:471b5f297cc84929b842008478f43404 -->
- Run: `471b5f297cc84929b842008478f43404`; fixture: `examples/cursor-pagination`
- Task: Add cursor pagination to GET /items. Return at most limit items ordered by (created_at, id), using both fields in an opaque next_cursor when more results exist. Default limit is 100; accept integer limits 1 through 100. Reject malformed cursors and invalid limits with HTTP 400, including structurally valid encodings with incorrect field types. Preserve the existing response shape when all results fit on one page (omit next_cursor if there is no next page). Preserve payloads and app isolation. Add deterministic tests for duplicate timestamps, first/middle/final pages, malformed cursors, limit=1, stable ordering and complete traversal without duplicate or missing IDs. Verify the full suite.
- Test command: `python3 -m pytest -q`
- Agent exit: 0; final test exit: 0
- Actions: 7; agent duration: 147059 ms
- Classification: **success**
- Parent: none

Suite v2 ran once in its frozen order. Transactional cache passed 28 tests,
lease queue passed 19 tests, and document transactions passed its full suite
(7 actions, 142.930 seconds).
No candidate met the criteria for diagnosis and recovery; no failure was
manufactured or relabeled.

## Immutable evaluator candidate

The first evaluator-backed attempt (`51e97d...`) stopped before Codex launched:
the account returned an explicit usage-limit error after 2.612 seconds. It is
retained as an agent process error. Final verification returned exit 1 after the agent process error; this is not a
coding failure. The one-time resume command, now consumed, was:

```bash
source .venv/bin/activate
python scripts/find_demo_failure.py --suite live --resume-process-error 51e97d32ff95470abee566ccd4fd8d89
```

That command rechecks the retained input digest and runs the same frozen task
with the same normal Codex settings. Final verification adds the immutable
evaluator from `evaluators/rate_limiter.py` only after the visible tests pass.

## idempotent-orders: 2026-09-11T23:01:18.885423+00:00

<!-- run:98619d8ce1074ab9ac83f22297650073 -->
- Run: `98619d8ce1074ab9ac83f22297650073`; fixture: `examples/idempotent-orders`
- Task: Add Idempotency-Key support to POST /orders. Same key and normalized body returns the original order and HTTP 201 without creating another order. Normalization is the existing SKU whitespace trimming, default quantity=1, and ignoring unknown fields. Different normalized body with the same key returns HTTP 409. Validation failure must not consume a key. Requests without the header keep existing behavior. Keys are scoped to an app instance. Store replay data independently of mutable request objects. Add deterministic tests for exact retry, normalized equivalent bodies, conflicts, validation failure followed by valid reuse, no-key behavior, and app isolation. Verify the full suite.
- Test command: `python3 -m pytest -q`
- Agent exit: 0; final test exit: 0
- Actions: 7; agent duration: 112850 ms
- Classification: **success**
- Parent: none

## rate-limiter: 2026-09-11T23:03:12.488455+00:00

<!-- run:2e84d4c255784c5d9953103da0598fb7 -->
- Run: `2e84d4c255784c5d9953103da0598fb7`; fixture: `examples/rate-limiter`
- Task: Migrate RateLimiter from fixed windows to a per-client sliding window allowing 3 accepted requests in any 10-second window. Keep the injectable monotonic clock and allow(client) API. The fourth request is rejected; rejected requests must not extend the window. Exactly 10 seconds after the oldest accepted request, another is allowed. Clients and instances are isolated. Prune expired timestamps and keep per-client history bounded by the accepted-request limit. Add deterministic tests using a fake clock (no sleeps) for exact and just-before boundaries, crossing the old fixed-window boundary, repeated rejections, simultaneous timestamps, client isolation and pruning after long idle periods. Verify the full suite.
- Test command: `python3 -m pytest -q`
- Agent exit: 1; final test exit: 5
- Actions: 5; agent duration: 58247 ms
- Classification: **agent process error**
- Parent: none

## rate-limiter: 2026-09-12T20:07:41.642673+00:00

<!-- run:2dc6e7948f864e7d9a4bbb57bb816d18 -->
- Run: `2dc6e7948f864e7d9a4bbb57bb816d18`; fixture: `examples/rate-limiter`
- Task: Migrate RateLimiter from fixed windows to a per-client sliding window allowing 3 accepted requests in any 10-second window. Keep the injectable monotonic clock and allow(client) API. The fourth request is rejected; rejected requests must not extend the window. Exactly 10 seconds after the oldest accepted request, another is allowed. Clients and instances are isolated. Prune expired timestamps and keep per-client history bounded by the accepted-request limit. Add deterministic tests using a fake clock (no sleeps) for exact and just-before boundaries, crossing the old fixed-window boundary, repeated rejections, simultaneous timestamps, client isolation and pruning after long idle periods. Verify the full suite.
- Test command: `python3 -m pytest -q`
- Agent exit: 0; final test exit: 0
- Actions: 7; agent duration: 151277 ms
- Classification: **success**
- Parent: none
- Authorized process restart of: `2e84d4c255784c5d9953103da0598fb7`; no diagnostic hint added.

## transactional-cache: 2026-09-12T20:14:02.975145+00:00

<!-- run:c6cf16dc31094306b7da0d5cf686a341 -->
- Run: `c6cf16dc31094306b7da0d5cf686a341`; fixture: `examples/transactional-cache`
- Task: Optimize Store.apply so a small transaction does not deepcopy every record and cache entry before starting. Use a write-proportional rollback mechanism while preserving the existing observable contract, including sequential version checks for repeated keys, deletion followed by recreation, exact restoration of cache membership and contents on any exception, and independent mutable values returned by reads, callbacks and results. The staging callback may read other records through Store.read before it raises. Keep the API and exception behavior. Do not weaken existing tests. Add deterministic tests for repeated-key rollback, cold-cache reads during failed staging, stale optimistic versions, late failures and mutation aliasing. Verify the full suite.
- Test command: `python3 -m pytest -q`
- Agent exit: 0; final test exit: 0
- Actions: 10; agent duration: 155217 ms
- Classification: **success**
- Parent: none

## lease-queue: 2026-09-12T20:16:38.988512+00:00

<!-- run:ca0db6cdfe714eb591bac0c7416437c3 -->
- Run: `ca0db6cdfe714eb591bac0c7416437c3`; fixture: `examples/lease-queue`
- Task: Replace Queue.claim's full scan with heap-based indexes for delayed jobs and lease expirations. Preserve the existing contract exactly: select eligible jobs by original ready time then insertion order, expire leases at the exact deadline, increment fencing generations on each claim, reject stale finish calls without state changes, retain submit idempotency even for completed jobs, and respect retry_at. dump and restore must remain compatible with the existing serialized data and rebuild indexes, including active leases. Obsolete heap entries must never cause duplicate claims or resurrect done jobs. Avoid scanning all jobs on each claim; lazy invalidation is acceptable. Preserve input/output payload isolation. Add deterministic coverage for stale heap entries, retries, exact expiration and restore. Verify all existing and added tests.
- Test command: `python3 -m pytest -q`
- Agent exit: 0; final test exit: 0
- Actions: 7; agent duration: 144259 ms
- Classification: **success**
- Parent: none

## document-transactions: 2026-09-12T20:19:04.001900+00:00

<!-- run:b49390f3fd4d40ecbaeae05618edf9b4 -->
- Run: `b49390f3fd4d40ecbaeae05618edf9b4`; fixture: `examples/document-transactions`
- Task: Extend the atomic JSON-tree edit engine with move operations using the existing list-of-components paths: remove the value at from, then place it at path, interpreting the destination against the document after removal. At a list destination insert before the specified index (index equal to length appends); a dict destination replaces or creates that key. Moving a path to itself is a no-op. Reject moving a container into its descendant before modification, and reject removing the root except that moving root to itself is a no-op. A destination [] replaces the root. All operations in a batch observe earlier edits; a later failed test or invalid move must leave the caller's document and operation objects unchanged. Preserve existing set/remove/append/copy/test behavior and complete mutable isolation of the result. Add deterministic tests for same-list forward/backward moves, descendant rejection, overlapping siblings, root destination, copying a moved value, and rollback after a late invalid transition. Verify the full suite.
- Test command: `python3 -m pytest -q`
- Agent exit: 0; final test exit: 0
- Actions: 7; agent duration: 142930 ms
- Classification: **success**
- Parent: none

## rate-limiter-live: 2026-09-12T20:42:04.111487+00:00

<!-- run:51e97d32ff95470abee566ccd4fd8d89 -->
- Run: `51e97d32ff95470abee566ccd4fd8d89`; fixture: `examples/rate-limiter-live`
- Task: Implement a per-client sliding-window rate limiter allowing 3 accepted requests in any 10-second window. Keep the injectable clock and allow(client) API. The fourth request inside the window is rejected. A request exactly 10 seconds after the oldest accepted request is allowed, while requests at the other timestamps remain inside the rolling window. Rejected requests do not extend the window. Clients are isolated and expired timestamps are pruned. Add deterministic tests for staggered timestamps, exact boundaries, rejected requests and isolation. Run the full supplied test suite.
- Test command: `python3 -m pytest -q`
- Agent exit: 1; final test exit: 1
- Actions: 0; agent duration: 2612 ms
- Classification: **agent process error**
- Parent: none

## rate-limiter-live: 2026-09-13T05:31:19.490714+00:00

<!-- run:695aa2d98f0941dc8146dc922953bf81 -->
- Run: `695aa2d98f0941dc8146dc922953bf81`; fixture: `examples/rate-limiter-live`
- Task: Implement a per-client sliding-window rate limiter allowing 3 accepted requests in any 10-second window. Keep the injectable clock and allow(client) API. The fourth request inside the window is rejected. A request exactly 10 seconds after the oldest accepted request is allowed, while requests at the other timestamps remain inside the rolling window. Rejected requests do not extend the window. Clients are isolated and expired timestamps are pruned. Add deterministic tests for staggered timestamps, exact boundaries, rejected requests and isolation. Run the full supplied test suite.
- Test command: `python3 -m pytest -q`
- Agent exit: 0; final test exit: 1
- Actions: 5; agent duration: 51433 ms
- Classification: **coding failure candidate; manual review required**
- Parent: none
- Authorized process restart of: `51e97d32ff95470abee566ccd4fd8d89`; no diagnostic hint added.

## Manual review of evaluator restart (September 13, 2026)

Run `695aa2d98f0941dc8146dc922953bf81` completed normally: baseline exit 0,
agent exit 0, five actions, 51.433 seconds, and five supplied tests passed.
Final verification exited 1 because the evaluator incorrectly required rejection
at time 10 after accepted requests at 0, 1 and 2. The task explicitly expires the
request at 0 at this boundary, leaving room for one accepted request.

**Reviewed classification: evaluator defect, not a coding failure.** The automatic
candidate label above is preliminary. Diagnosis returned `insufficient_evidence`,
selected no event, and noted that the implementation matched the task. No targeted
recovery was run. The original result, diff, diagnosis and logs remain unchanged;
the original evaluator is retained alongside the local run logs and in Git history.

The corrected evaluator accepts the first request at 10 and rejects a second
request at 10, retaining requests at 1, 2 and 10. Separate sandboxed verification
of the unchanged agent output passed five tests and the corrected evaluator
(exit 0, 250 ms). This was a verifier-only check, not a new agent attempt or recovery.
A regression test checks the evaluator against a labeled test-only sliding-window
reference and the original fixed-window implementation. No live failure/recovery
evidence has been established.

## Candidate audit and next fixed suite (September 13, 2026)

The older request's v1 status is superseded by the retained ledger: v1 and v2
have completed, and the evaluator limiter has consumed its authorized restart.
None will be rerun. The next suite is v3, preserving the meaning of earlier results.

### What the actual candidates measure

Line counts below include blank lines in the initial Python files, before Codex.
Each named v1/v2 candidate has just one production file and one test file.
Difficulty is a qualitative assessment of the observed task, not a model benchmark.

| Candidate | Production / test lines | Difficulty and interaction | Verification and visible trajectory |
|---|---:|---|---|
| v1 cursor pagination | 16 / 29 | Low to moderate: immutable list, compound ordering and input validation. Requirements explicitly enumerate boundaries; no data mutation or concurrency. | Three original tests only cover old listing. Agent writes new pagination tests and passes 52. Event e00008 describes the eventual design before e00010 edits. No observed failed coding test; e00007 exit 1 is an empty AGENTS search. |
| v1 idempotent orders | 28 / 24 | Low to moderate: normalize, validate, memoize. No persistence, crashes or cross-process coordination required. | Original eight cases cover old behavior; new key requirements depend on agent-authored tests. e00009 implements locking and replay, e00015 passes 21. No observed corrected coding failure. |
| v1 rate limiter | 19 / 24 | Low: a deque of at most three timestamps; every boundary and pruning rule is stated. | Three initial tests do not distinguish rolling from fixed windows. Restart e00012 exits 5 with no tests collected, e00014 edits files, e00016 passes six. This is an in-run editing/collection issue, not a failed final implementation. |
| v2 transactional cache | 51 / 98 | Moderate: rollback plus versions, mutable isolation and callback cache fills. A correct deepcopy reference makes the contract directly inspectable. | Sixteen supplied cases already expose late rollback and cold-cache fill. e00008 explicitly identifies journaling reads before e00012 implements it. Added tests include nested transactions and copy failures; 28 pass without an observed failed coding assertion. |
| v2 lease queue | 61 / 84 | Moderate: indexes, fencing, expiry priority, persistence and stale entries. All state fits in a single mapping. | Fifteen initial cases include 12 seeded scan-oracle cases. e00010 identifies ready-time versus expiry-time ordering before e00012 edits. Nineteen pass, including an agent-added no-scan check. No observed failed coding assertion. |
| v2 document transactions | 42 / 70 | Low to moderate: remove then insert, path overlap, caller isolation. Existing whole-tree deepcopy already solves atomic rollback. | Eight baseline cases cover old operations, not new moves. e00009 edits before e00010 describes post-removal lookup. New move tests are agent-authored; 29 pass without an observed failed coding assertion. |
| evaluator rate limiter | 19 / 15 | Low: essentially the same standard limiter operation, not a materially harder task. | Five supplied tests pass; the external assertion contradicts the task. Diagnosis abstains and corrected verification passes. This is evidence of a verifier defect, not an agent failure. |

For every v1/v2 task the agent could inspect and edit all tests later determining
success. Tests expose baseline behavior directly, and prompts provide detailed
implementation checklists. They are useful regressions, especially the queue's
scan oracle, but agent-authored tests cannot independently establish the new
requirements. None of these fixtures contains a large integration surface. The
v2 interactions require reasoning, but the agent visibly anticipated their main
invariants. The evidence supports the bounded-task explanation; it does not show
that coding agents generally do not fail or that these implementations are complete.

Earlier exploratory tasks show the same pattern: TTL caching (26 production
lines), SQLite/cache coherence (47), query spans (24 across two modules), GitHub
import (26), and interval scheduling (22). Query spans and scheduling have visible
independent oracles for existing semantics; new requirements still partly rely on
agent-added tests. The scheduler explicitly reasons about zero-weight lexicographic
prefixes before editing. The cache and SQLite trajectories include dependency or
sandbox/tool setup problems, not normal final coding failures. These issues remain
in raw logs and are not counted as recovered implementation mistakes.

Success currently means agent exit 0 and supplied command exit 0. Important gaps:
mutable tests can omit requirements; a test count is not coverage; performance
claims may lack independent checks; a nonzero command may be a collection or
process error; and even evaluator-owned assertions can be wrong. Per-edit diffs
and internal reasoning are not always emitted, so absence of a visible wrong turn
is not proof that no wrong turn occurred. No retrospective test was added to turn
a prior passing candidate into a failure.

### Suite v3: frozen definitions and evaluator strategy

Exact prompts: `scripts/candidate_suite_v3.json`. Fixed execution order:

1. **async-cache**: coalesce concurrent metadata loads while preserving cancellation
   ownership, generation invalidation, completion-based TTL and mutable isolation.
   The existing two-module service has healthy sequential behavior. Controlled
   futures drive deterministic overlapping calls; no real network or timed sleeps.
2. **durable-delivery**: bound retries while preserving ordered durable acknowledgements
   and stable receiver idempotency keys across ambiguous send outcomes and restarts.
   The worker and atomic state-file adapter have healthy successful-delivery behavior.
   An evaluator-owned fake transport performs an effect before raising, and a fake
   durable store rejects acknowledgement writes. Assertions distinguish these errors.
3. **snapshot-catalog**: add repeatable pagination across inserts, deletes, sort-key
   changes and payload updates while retaining current-state reads. The catalog and
   service adapter have passing listing behavior. The oracle is a detached list taken
   before mutation; traversal is compared with it, including complete cursor replay.

These are realistic ownership and state-boundary problems; all required behavior
is specified in the prompt. Evaluator cases are not copied into the agent repository
or supplied as hints. Normal tests remain visible, and agents can add tests. Each
external evaluator is validated against a labeled test-only reference implementation
and rejects the unchanged baseline's missing feature. References are not trajectories,
solutions given to the coding agent, or recovery evidence. This does not prove the
verifier infallible: every candidate failure still requires manual review.

The runner retains evaluator bytes and their SHA-256 before coding, outside the
working copy, and checks the bytes before final verification. Recovery uses that
same retained evaluator and original input. This is procedural separation for trusted
local experiments, not a read-isolation security boundary: the CLI sandbox allows
filesystem reads. Trajectories must be inspected for evaluator access before an
example is accepted. Evaluator files are not exposed in the task or agent verifier.

Run `python scripts/find_demo_failure.py --suite v3` in the activated environment.
One attempt per candidate, fixed order, stop at a potential coding failure or process
error. Never reset its attempt index. Review the trajectory, diff, evaluator and
normal termination before `--suite v3 --recover RUN_ID`. One short diagnosis-derived
hint is allowed only for a defensible diagnosis. If all pass, report the suite's
coverage and limitations and design a subsequent suite based on this evidence.
