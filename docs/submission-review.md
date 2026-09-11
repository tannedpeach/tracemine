# Cursor submission review

Publication audit: September 11, 2026. The MVP code path is implemented, but submission completion remains open until a real failed-run recovery and recording are captured.

- [x] First README screen explains the instrument: inspect an earlier mistake, test a targeted hint.
- [x] Why the problem matters is specific to coding-agent evaluation and grounded in the author's failure-mining experience.
- [x] Fresh clone on macOS / Python 3.13: setup, all checks, imported recording, server and browser inspection passed. Python 3.11 is in the hosted CI matrix, pending verification.
- [ ] Full core-story recording: the included 18-second GIF shows actual passing-run inspection, tests/diff and audit artifacts. It is a sequence of UI captures, not failure/recovery evidence.
- [x] A small actual Python repository and real model run exist; no fabricated run evidence.
- [x] Architecture, process boundaries, model uncertainty, and test-only success are explained.
- [x] Small modules, explicit state transitions, typed contracts and 32 backend tests support interview discussion. Frontend formatting, TypeScript and production build pass.
- [x] No misleading completion claim; known gaps and actual run outcomes are documented.

The bundled recording's patch was independently applied to its retained input in a disposable copy. Baseline and final tests both returned exit 0; new verification logs were retained separately. Desktop and narrow-window UI review caught hidden mobile history; that navigation issue is fixed.

Tracked files and all existing commits were scanned for machine-specific home paths and common credential/private-key patterns; no matches. Original local run stores, environments and caches remain ignored. Public evidence is redacted and checksummed.

Outstanding: genuine failed-run diagnosis/recovery evidence, a recording of that complete story, and all 13 Definition of Done steps on a fresh checkout. Five normally completed live experiments passed; infrastructure errors and test doubles are not relabeled as model failures. No stretch goals until these gaps are resolved.
