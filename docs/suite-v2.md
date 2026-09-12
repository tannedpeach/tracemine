# Fixed suite v2

Frozen before execution on September 12, 2026. Every task and fixture is committed
before the first model invocation. Run each candidate once, in the listed order.
No model override, prompt adjustment or hidden test injection.

1. Transactional cache: optimize rollback while preserving optimistic versions,
   repeated-key semantics, cache state and mutable-value isolation.
2. Lease queue: replace scanning with heaps while preserving delayed retries,
   fencing tokens, expired leases, idempotency and serialized state.
3. Document transactions: add move operations with sequential path interpretation,
   structural constraints, caller isolation and atomic failure.

These begin with correct small reference implementations and deterministic
regression tests. The model may add new tests. Existing tests are provided up
front and cannot establish complete requirement coverage on their own.

The exact task text is in [candidate_suite_v2.json](../scripts/candidate_suite_v2.json).
Run `source .venv/bin/activate` then
`python scripts/find_demo_failure.py --suite v2`.
The attempt index is retained in ignored local storage. The harness stops at the
first potential coding failure for manual review, or an execution problem.
All outcomes go to the experiment ledger, including passing attempts.

One targeted recovery is allowed after manual evidence review:
`python scripts/find_demo_failure.py --suite v2 --recover RUN_ID`.
It uses the parent's retained snapshot, original task, test command and stored
diagnosis hint. It is a fresh attempt, not execution checkpoint replay.
