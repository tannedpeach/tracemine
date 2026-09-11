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
| Idempotent orders (`98619d…`) | 0 | 0 | 8 | 112.850 s | Success; 21 tests passed |
| Sliding-window limiter (`2e84d4…`) | 1 | 5 | 5 | 58.247 s | Agent process error: Codex account usage limit; no final verification conclusion |

The suite was executed once in fixed order and stopped on the documented usage
error. No prompt mutation, environment sabotage or repeated attempt was used.

## cursor-pagination — 2026-09-11T22:58:50.840597+00:00

<!-- run:471b5f297cc84929b842008478f43404 -->
- Run: `471b5f297cc84929b842008478f43404`; fixture: `examples/cursor-pagination`
- Task: Add cursor pagination to GET /items. Return at most limit items ordered by (created_at, id), using both fields in an opaque next_cursor when more results exist. Default limit is 100; accept integer limits 1 through 100. Reject malformed cursors and invalid limits with HTTP 400, including structurally valid encodings with incorrect field types. Preserve the existing response shape when all results fit on one page (omit next_cursor if there is no next page). Preserve payloads and app isolation. Add deterministic tests for duplicate timestamps, first/middle/final pages, malformed cursors, limit=1, stable ordering and complete traversal without duplicate or missing IDs. Verify the full suite.
- Test command: `python3 -m pytest -q`
- Agent exit: 0; final test exit: 0
- Actions: 7; agent duration: 147059 ms
- Classification: **success**
- Parent: none

## idempotent-orders — 2026-09-11T23:01:18.885423+00:00

<!-- run:98619d8ce1074ab9ac83f22297650073 -->
- Run: `98619d8ce1074ab9ac83f22297650073`; fixture: `examples/idempotent-orders`
- Task: Add Idempotency-Key support to POST /orders. Same key and normalized body returns the original order and HTTP 201 without creating another order. Normalization is the existing SKU whitespace trimming, default quantity=1, and ignoring unknown fields. Different normalized body with the same key returns HTTP 409. Validation failure must not consume a key. Requests without the header keep existing behavior. Keys are scoped to an app instance. Store replay data independently of mutable request objects. Add deterministic tests for exact retry, normalized equivalent bodies, conflicts, validation failure followed by valid reuse, no-key behavior, and app isolation. Verify the full suite.
- Test command: `python3 -m pytest -q`
- Agent exit: 0; final test exit: 0
- Actions: 7; agent duration: 112850 ms
- Classification: **success**
- Parent: none

## rate-limiter — 2026-09-11T23:03:12.488455+00:00

<!-- run:2e84d4c255784c5d9953103da0598fb7 -->
- Run: `2e84d4c255784c5d9953103da0598fb7`; fixture: `examples/rate-limiter`
- Task: Migrate RateLimiter from fixed windows to a per-client sliding window allowing 3 accepted requests in any 10-second window. Keep the injectable monotonic clock and allow(client) API. The fourth request is rejected; rejected requests must not extend the window. Exactly 10 seconds after the oldest accepted request, another is allowed. Clients and instances are isolated. Prune expired timestamps and keep per-client history bounded by the accepted-request limit. Add deterministic tests using a fake clock (no sleeps) for exact and just-before boundaries, crossing the old fixed-window boundary, repeated rejections, simultaneous timestamps, client isolation and pruning after long idle periods. Verify the full suite.
- Test command: `python3 -m pytest -q`
- Agent exit: 1; final test exit: 5
- Actions: 5; agent duration: 58247 ms
- Classification: **agent process error**
- Parent: none
