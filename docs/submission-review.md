# Cursor submission review

Publication audit: September 11, 2026. The MVP code path is implemented, but submission completion remains open until a real failed-run recovery and recording are captured.

- [x] First README screen explains the instrument: inspect an earlier mistake, test a targeted hint.
- [x] Why the problem matters is specific to coding-agent evaluation and grounded in the author's failure-mining experience.
- [x] Fresh clone on macOS / Python 3.13: setup, all checks, imported recording, server and browser inspection passed. Hosted GitHub CI also passed on Python 3.11 and 3.13 ([publication run](https://github.com/tannedpeach/tracemine/actions/runs/34652899278)).
- [ ] Full core-story recording: the included 18-second GIF shows actual passing-run inspection, tests/diff and audit artifacts. It is a sequence of UI captures, not failure/recovery evidence.
- [x] A small actual Python repository and real model run exist; no fabricated run evidence.
- [x] Architecture, process boundaries, model uncertainty, and test-only success are explained.
- [x] Small modules, explicit state transitions, typed contracts and 37 backend tests support interview discussion. Frontend formatting, TypeScript and production build pass. The fixed candidate suite and all three isolated baselines also pass hosted CI ([suite validation](https://github.com/tannedpeach/tracemine/actions/runs/34656282215)).
- [x] No misleading completion claim; known gaps and actual run outcomes are documented.

The bundled recording's patch was independently applied to its retained input in a disposable copy. Baseline and final tests both returned exit 0; new verification logs were retained separately. Desktop and narrow-window UI review caught hidden mobile history; that navigation issue is fixed.

Tracked files and all existing commits were scanned for machine-specific home paths and common credential/private-key patterns; no matches. Original local run stores, environments and caches remain ignored. Public evidence is redacted and checksummed.

Outstanding: genuine failed-run diagnosis/recovery evidence, a recording of that complete story, and all 13 Definition of Done steps on a fresh checkout. Five normally completed live experiments passed; infrastructure errors and test doubles are not relabeled as model failures. No stretch goals until these gaps are resolved.

Finalization suite v1 added three fixed realistic candidates. Pagination and idempotent orders passed; the limiter's one authorized restart passed after the initial Codex usage-limit process error. Suite v2 then ran three new interacting-requirement tasks once; all passed. No candidate produced a valid coding-failure artifact, so no diagnosis or recovery was fabricated.

The submission gate remains intentionally open. Across v1 and v2, every normally completed candidate passed; the only non-pass was the documented usage-limit process error. There is still no valid live failure to diagnose or recover.

An immutable-evaluator candidate is prepared and its first attempt is retained. Codex hit the account usage limit before launch, so it produced no coding result. The one permitted resume was completed on September 13; its manual review is recorded below.

September 13 follow-up: the authorized evaluator restart completed normally and
passed five supplied tests. Manual review rejected its apparent failure because
the evaluator contradicted the exact-boundary requirement. Diagnosis conservatively
returned insufficient evidence. The corrected evaluator passed against the retained
agent output without another model invocation. No recovery was warranted; the
submission evidence gate remains open.
