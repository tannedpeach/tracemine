# Validation review

Latest audit: September 13, 2026. TraceMine presents a complete local workflow for
capturing Codex trajectories, inspecting repository changes, independently verifying
behavior, and retrying from a retained snapshot. The fixed historical evaluation is
complete: cachetools, TinyDB, and Marshmallow all passed their supplied tests and
evaluator-owned regressions on the first attempt.

The repository is technically validated but has one evidence limitation. No fixed
evaluation produced a genuine coding failure with a defensible diagnosis and
targeted recovery, so the central failure-to-recovery story is not demonstrated by
the included 18-second passing-run GIF. This is stated in the README and ledger;
the project does not present a synthetic failure as real evidence.

- [x] The README explains the instrument, its motivation, and the Tinder failure-mining background.
- [x] Fresh-clone setup, imported recording, server inspection, and hosted CI passed on Python 3.11 and 3.13.
- [x] The bundled patch reproduces independently in a disposable copy with baseline and final tests passing.
- [x] Architecture, process boundaries, isolation, model uncertainty, and test-only success are documented.
- [x] The fixed v1, v2, and v3 experiments are recorded with their actual outcomes.
- [x] Historical suite v4 is complete and auditable: pinned source commits, exact task text, evaluator hashes, pre-fix failures, historical-fix passes, run IDs, trajectories, diffs, and final results are retained.
- [x] The current check runs 45 backend tests; frontend formatting, TypeScript, and production build also pass.
- [ ] A live failure, grounded diagnosis, targeted retry, and complete workflow recording remain unvalidated.

The public repo contains no local run databases, environments, machine-specific paths,
or credentials. Original logs and snapshots stay in ignored local storage. The
supplied test command remains the primary success signal, and evaluator-owned checks
cover only the behavior stated by each historical task. A passing result therefore
supports the checked behavior without establishing general correctness.

No new suite or feature is planned for this presentation pass. The experiment ledger
contains the detailed evidence and limitations, while [architecture.md](architecture.md)
explains the implementation decisions an engineer can inspect and discuss.
