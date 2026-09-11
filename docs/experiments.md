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
