# Live experiment ledger

## Current checkpoint: historical suite v4 complete

Freeze commit: `e95f26e`. Each candidate below received exactly one normal Codex
attempt, with no overrides, intervention or recovery. All baseline, agent and final
processes exited zero without timeouts. Supplied-test counts include agent-added
tests discovered by the frozen command; evaluator results are reported separately.

| Candidate | Run | Supplied tests | Evaluator | Actions | Agent time |
|---|---|---|---|---:|---:|
| cachetools | `a546b88c5f274177b0d76aaf38876254` | 161 passed | Passed | 15 | 97.636 s |
| TinyDB | `6b8a6045d3d74e61a774c60660a7baf0` | 254 passed | Passed | 8 | 63.278 s |
| Marshmallow | `4bfb9f8ed7e94cdc9aa5ab31740cc781` | 451 passed | Passed | 8 | 65.277 s |

Manual review inspected the actual trajectories, source/test diffs and final logs.
No upstream lookup or evaluator access appeared in the recorded actions. Each patch
changes the implicated implementation and adds tests, without removing existing
checks. Cachetools recalculates net size after eviction, TinyDB filters missing IDs
inside update/remove, and Marshmallow resolves schema error aliases with declared
field fallback. These observations support the passing results, not a claim of
complete correctness or model generalization.

No qualifying coding failure occurred. No diagnosis or recovery was run, and the
passing-run GIF remains labeled as such. The fixed evaluation is closed; there will
be no increasingly difficult follow-up suite under this protocol. The useful result
is that independent historical regressions were reproducible and the agent solved
these three scoped tasks. Live diagnosis quality and recovery remain unmeasured.

All original JSONL, diffs, immutable evaluators, process results and snapshots remain
in ignored `.tracemine-candidates/runs/RUN_ID/`; the attempt index has exactly the
three candidate IDs above. A separate fresh clone reproduced all preflight outcomes
and matched every frozen source and evaluator digest. Setup, 45 backend tests,
frontend checks/build and the bundled passing patch reproduction also passed.

Suite v3 is closed. The one unchanged snapshot-catalog restart passed with baseline,
agent and final exits all zero. Its original missing-method verification error was
the expected result of unchanged code after an agent usage-limit error, not an
evaluator defect. Neither run supplies a coding-failure example.

Before any v4 model invocation, three historical candidates were validated in this
fixed order. Task text, source/fix commits and exact baseline commands are in
`scripts/historical_suite_v4.json`; evaluator hashes, source content digests and
measured preflight outcomes are in `scripts/historical_validation_v4.json`.

| Order | Historical evidence | Regression scope | Pre-fix baseline / evaluator | Fixed baseline / evaluator |
|---|---|---|---|---|
| 1 | [cachetools #405](https://github.com/tkem/cachetools/issues/405), [accepted fix](https://github.com/tkem/cachetools/commit/39b31bc9b63abe98497409945e9d382d8918c8fb) | Custom-size replacement, eviction and accounting across cache policies | 0 / 1 | 0 / 0 |
| 2 | [TinyDB #591](https://github.com/msiemens/tinydb/issues/591), [accepted fix](https://github.com/msiemens/tinydb/commit/76d21d26c682e1ca6ca25bd8e81edf9f609ac52f) | Missing/mixed document IDs, callback updates, query cache and upsert | 0 / 1 | 0 / 0 |
| 3 | [Marshmallow #2170](https://github.com/marshmallow-code/marshmallow/issues/2170), [accepted fix](https://github.com/marshmallow-code/marshmallow/commit/9f751e1cef943e2ca1a77f93d3483b4a171d4303) | Aliased schema error merging, many, excluded fields and literal dictionaries | 0 / 1 | 0 / 0 |

All preflight processes exited normally. Cachetools and Marshmallow use the named
affected upstream test modules, not the entire upstream test matrix. TinyDB uses
its full tests directory. The first preflight stopped because TinyDB's pytest
configuration required the missing coverage plugin; dependencies were installed
and pinned before repeating preflight. This is setup evidence, not an agent result.
All attempts remain in ignored `.tracemine-history/preflight-*` directories.

Manual task/evaluator review: every asserted behavior is in the frozen task.
TinyDB promises skipping absent IDs, not rollback of arbitrary callback exceptions.
Marshmallow's accepted fix preserves literal error dictionaries, so the task says
that explicitly. Cachetools includes replacement-key eviction and size accounting;
the public report credits AI-assisted discovery. These are accepted real historical
bugs, not claims about who first found them.

To reproduce preflight after normal setup:

```bash
source .venv/bin/activate
python -m pip install -r scripts/history-requirements.lock
python scripts/prepare_history.py
```

Original upstream checkouts remain unchanged and ignored. Tests run in disposable
copies. Agent copies contain pre-fix files and fresh Git metadata, without upstream
history, fixes, issue links or evaluator files in the task workspace. The existing
local trust boundary still allows reads outside that workspace; review trajectories
for upstream or evaluator access before accepting evidence.

Protocol: `python scripts/find_demo_failure.py --suite v4` uses the normal runner
and settings, once per candidate, in frozen order. Stop at the first potential
coding failure for manual review. Supplied tests precede evaluator checks in retained
final logs; a supplied-test failure prevents evaluator execution. Record both
outcomes separately after inspecting those logs. Only a grounded normal diagnosis
warrants one `--suite v4 --recover RUN_ID` attempt from the retained input. Stop
after this fixed suite even if every candidate passes. No v5 or tuned retries.

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

## async-cache: 2026-09-13T06:04:38.489677+00:00

<!-- run:4cd2710a429c4fc6b8da079417ddea4e -->
- Run: `4cd2710a429c4fc6b8da079417ddea4e`; fixture: `examples/async-cache`
- Task: Extend Cache.get to coalesce concurrent cache misses per key without serializing unrelated keys. Preserve the existing Cache and MetadataService APIs, detached mutable return values, exact TTL expiry and TTL measured from successful load completion. A caller cancellation must not cancel a load while other callers still await it. If the last waiter cancels, cancel and release that load so a later request can start normally. Loader failures propagate to all current waiters, are not cached, and permit later retries. invalidate(key) must immediately detach that key from its current flight: existing waiters may still receive the old result, but subsequent callers start a new load and an old completion must neither overwrite a newer cached value nor remove a newer flight. Use one asyncio event loop; no threads or external packages. Add deterministic tests using events/futures for overlap, cancellation and invalidation races, and run the supplied test suite.
- Test command: `python3 -m pytest -q`
- Agent exit: 0; final test exit: 0
- Actions: 7; agent duration: 155376 ms
- Classification: **success**
- Parent: none

## durable-delivery: 2026-09-13T06:07:14.541061+00:00

<!-- run:8154b13fe51c49ad8608ab9431fde09d -->
- Run: `8154b13fe51c49ad8608ab9431fde09d`; fixture: `examples/durable-delivery`
- Task: Add bounded transient retries to Worker.drain(max_attempts=1). The positive integer max_attempts excludes bool, is validated even for an empty queue, and counts total send invocations per pending message in this drain call. Retry only TimeoutError and ConnectionError from send; exhaustion returns the count of messages durably acknowledged in this call and stops before later messages. A successful send must be durably acknowledged before advancing. Storage load/save failures and other transport errors propagate immediately; storage errors must not enter the send retry loop. A transport timeout may occur after the receiver already performed its side effect: retain the same str(message id) key and original payload on every retry, including after reconstructing Worker from the same storage. The receiver owns idempotency; do not claim exactly-once delivery locally. Keep the persisted format and enqueue API compatible. Every send receives an independent deep copy, because transports may mutate payloads even when raising. Re-read durable state on each drain so a failed acknowledgement is retried correctly on the next call. Preserve ordering, add tests for ambiguous success and acknowledgement failure, and run the supplied tests. Single synchronous worker only; no concurrent writers or real network needed.
- Test command: `python3 -m pytest -q`
- Agent exit: 0; final test exit: 1
- Actions: 6; agent duration: 113154 ms
- Classification: **coding failure candidate; manual review required**
- Parent: none

### Manual review: durable-delivery `8154b13fe51c49ad8608ab9431fde09d`

**Rejected as a coding failure: evaluator overconstraint.** Baseline and agent
exited normally, 17 supplied tests passed, and the independent evaluator completed
its transport/acknowledgement checks before failing in argument validation. The
frozen task requires rejection of bool/non-integer max_attempts but does not name
an exception class. The evaluator catches only ValueError; the implementation
raises TypeError for wrong types and ValueError for non-positive integers. That is
a defensible contract interpretation, not a demonstrated incorrect implementation.

The normal diagnosis returned insufficient_evidence and selected no event. Its
explanation identifies the exception mismatch and the task's missing exception-class
requirement. No recovery hint was used. No test, prompt, result or evaluator bytes
were changed after this outcome. The passing reference test did not catch this
specification mismatch: it validated one permissible implementation, not all valid
implementations. The remaining snapshot-catalog candidate is still unattempted and
will run once in the frozen order. This is a verification-design limitation, not
failure-to-recovery portfolio evidence.

## snapshot-catalog: 2026-09-13T06:10:17.969750+00:00

<!-- run:2391b8ee037d4d60bae946fd48f9961b -->
- Run: `2391b8ee037d4d60bae946fd48f9961b`; fixture: `examples/snapshot-catalog`
- Task: Add Catalog.page(limit=20, cursor=None) returning {"items": [...], "next_cursor": opaque string or None}, and Service.page_items with the same parameters delegating to it. A new traversal snapshots the current rows sorted by (created_at,id). Every later page in that traversal must retain the original membership, full payload values and ordering even after put, delete or sort-key changes; new traversals see current state. Limit may change between pages and must be a non-bool integer 1 through 100. Replaying the same cursor and limit must return the same entire response, including next_cursor. Returned mutable values must not alias stored snapshots or current records. Cursors are scoped to their Catalog instance; reject foreign, empty or malformed cursors with ValueError. Empty and last pages have next_cursor=None. Keep existing list, put, delete and Service.list_items behavior. Retaining snapshots for the Catalog lifetime is acceptable for this local tool; no expiry or disk persistence needed. Add deterministic mutation/traversal tests and run the supplied suite.
- Test command: `python3 -m pytest -q`
- Agent exit: 1; final test exit: 1
- Actions: 0; agent duration: 2204 ms
- Classification: **agent process error**
- Parent: none

### Suite v3 execution outcomes

The frozen suite began after evaluator references and healthy baselines passed.
`async-cache` completed normally and passed six supplied tests plus its evaluator.
`durable-delivery` completed normally and passed 17 supplied tests; manual review
rejected the evaluator's TypeError-versus-ValueError assumption, and diagnosis
returned insufficient evidence. No recovery was run.
`snapshot-catalog` had a passing baseline, but Codex was rejected by the account
usage limit before launch. It has no trajectory, diff or coding result. The suite
stopped as required. No candidate was rerun.

The v3 attempt index and raw logs retain all three outcomes. The account limit is
an execution constraint, not a measured task result. The suite remains frozen; a
future run may resume only under the explicitly documented one-attempt policy after
reviewing whether an authorized process restart is appropriate.

## snapshot-catalog: 2026-09-13T20:03:40.940828+00:00

<!-- run:e87d4c60f6ff4ec787191258225695d1 -->
- Run: `e87d4c60f6ff4ec787191258225695d1`; fixture: `examples/snapshot-catalog`
- Task: Add Catalog.page(limit=20, cursor=None) returning {"items": [...], "next_cursor": opaque string or None}, and Service.page_items with the same parameters delegating to it. A new traversal snapshots the current rows sorted by (created_at,id). Every later page in that traversal must retain the original membership, full payload values and ordering even after put, delete or sort-key changes; new traversals see current state. Limit may change between pages and must be a non-bool integer 1 through 100. Replaying the same cursor and limit must return the same entire response, including next_cursor. Returned mutable values must not alias stored snapshots or current records. Cursors are scoped to their Catalog instance; reject foreign, empty or malformed cursors with ValueError. Empty and last pages have next_cursor=None. Keep existing list, put, delete and Service.list_items behavior. Retaining snapshots for the Catalog lifetime is acceptable for this local tool; no expiry or disk persistence needed. Add deterministic mutation/traversal tests and run the supplied suite.
- Test command: `python3 -m pytest -q`
- Agent exit: 0; final test exit: 0
- Actions: 6; agent duration: 110279 ms
- Classification: **success**
- Parent: none
- Authorized process restart of: `2391b8ee037d4d60bae946fd48f9961b`; no diagnostic hint added.

## cachetools: 2026-09-13T20:14:50.495273+00:00

<!-- run:a546b88c5f274177b0d76aaf38876254 -->
- Run: `a546b88c5f274177b0d76aaf38876254`; source: `https://github.com/tkem/cachetools.git`
- Source commit: `16e88894ef7d79b25a68f5a3b5411ed881342725`; input digest: `f53ba468cc840bf8ee865bbda47f36c33fafccec31faf91a324f7374751ac06c`
- Baseline exit: 0
- Task: Users of caches with custom value sizes report that replacing an existing value with a larger one unexpectedly discards other entries, even when the resulting contents fit within maxsize. Fix replacement behavior across the cache implementations: growing a value that fits, replacing with the same size, and shrinking must preserve unrelated entries and accurate currsize. When real eviction is necessary, preserve the documented eviction policy and valid size accounting, including when the policy chooses the key being replaced. Keep existing APIs and add regression tests. Run the supplied tests. Work from this checkout and its tests; do not look up upstream fixes.
- Test command: `PYTHONPATH=src python3 -m pytest -q tests/test_cache.py tests/test_fifo.py tests/test_lru.py tests/test_lfu.py tests/test_rr.py tests/test_ttl.py tests/test_tlru.py`
- Agent exit: 0; final test exit: 0
- Actions: 15; agent duration: 97636 ms
- Classification: **success**
- Parent: none

## tinydb: 2026-09-13T20:16:29.232524+00:00

<!-- run:6b8a6045d3d74e61a774c60660a7baf0 -->
- Run: `6b8a6045d3d74e61a774c60660a7baf0`; source: `https://github.com/msiemens/tinydb.git`
- Source commit: `8a2dc204c265c07ce8506a3599a28e720b6dcdd7`; input digest: `58fff8b95e913bffd308f62f217b473bbe173793320679a6f5f8621769731c86`
- Baseline exit: 0
- Task: TinyDB get handles absent document IDs gracefully, but update and remove raise KeyError when doc_ids contains a missing ID. A mixed batch can leave earlier documents modified before the exception. Make ID-based update and remove skip missing IDs, process every existing target and return only affected IDs in request order. Preserve iterable doc_ids, mapping and callable updates, query-cache invalidation, and unrelated documents. Upsert with a Document ID must still update an existing document or insert a missing one. Preserve other query-based behavior. Add regression tests and run the supplied suite. Work from this checkout and its tests; do not look up upstream fixes.
- Test command: `PYTHONPATH=. python3 -m pytest -q tests`
- Agent exit: 0; final test exit: 0
- Actions: 8; agent duration: 63278 ms
- Classification: **success**
- Parent: none

## marshmallow: 2026-09-13T20:17:34.578788+00:00

<!-- run:4bfb9f8ed7e94cdc9aa5ab31740cc781 -->
- Run: `4bfb9f8ed7e94cdc9aa5ab31740cc781`; source: `https://github.com/marshmallow-code/marshmallow.git`
- Source commit: `a578ed23092bd558acfbd9cd09a164108689326d`; input digest: `967905ffae07e32e3befb14eff55fade7f487a3436eb02cc53429bb25bc2cf2f`
- Baseline exit: 0
- Task: Validation errors are inconsistent for fields with data_key aliases. Field validators report the external key, but schema validators raising ValidationError(message, field_name=attribute_name) report the internal name. Make those schema-validator errors use the field's external data_key, merging with field errors under one key. Preserve error indexing for many=True, handling of declared fields excluded from the active schema, ordinary fields without aliases, unknown field names and schema-level errors. Explicit error dictionaries must retain their literal keys; do not reinterpret arbitrary user-supplied dictionaries. Add regression tests and run the supplied tests. Work from this checkout and its tests; do not look up upstream fixes.
- Test command: `PYTHONPATH=src python3 -m pytest -q tests/test_decorators.py tests/test_error_store.py tests/test_deserialization.py`
- Agent exit: 0; final test exit: 0
- Actions: 8; agent duration: 65277 ms
- Classification: **success**
- Parent: none
