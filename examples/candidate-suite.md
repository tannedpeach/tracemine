# Fixed finalization suite, version 1

The three candidates are fixed before execution in `scripts/find_demo_failure.py`.
Existing tests cover the original behavior and must pass before the agent starts.
Each task adds or changes behavior and asks the agent to add deterministic tests;
there are no hidden tests or deliberately damaged environments. This can miss bugs
the agent does not test. Passing is not evidence of complete requirement coverage.

1. **cursor-pagination**: add opaque compound-key cursors, preserve the legacy
   response shape when one page suffices, validate input and traverse timestamp ties.
2. **idempotent-orders**: normalize bodies, reject key conflicts, avoid reserving
   keys on validation failure and preserve no-key behavior.
3. **rate-limiter**: migrate a fixed-window limiter to a sliding window with exact
   boundaries, client isolation, rejected-request semantics and bounded history.

Run each once with normal installed Codex settings. Stop at the first candidate
coding failure for human review. The classifier is provisional: a human must check
that failed tests represent an implementation error, not an environment problem.
If all pass, retain the ledger and stop; do not mutate prompts to force a failure.

From the project root after setup:

```bash
source .venv/bin/activate
python scripts/find_demo_failure.py
# Only after manually reviewing a genuine failure and its diagnosis:
python scripts/find_demo_failure.py --recover PARENT_RUN_ID
```

The default `.tracemine-candidates` store retains raw logs and a durable attempt
index. Rerunning skips already attempted candidates; never delete that index to
repeat the same suite. The harness stops on execution problems for investigation.
Classification is provisional until the final output and diff are reviewed.
