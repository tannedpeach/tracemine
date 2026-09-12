# TraceMine MVP

## Gate: Section 33
- [x] Read handover completely; inspect empty workspace and installed tools.
- [x] Inspect `codex --help` and `codex exec --help`.
- [x] Minimal backend/frontend skeleton and isolated capture script.
- [x] Prove real JSONL capture on a disposable Git repository.

## Implementation order
- [x] Finalization: fixed three-candidate suite and resumable bounded harness; no model overrides or repeated prompts.
- [x] Run fixed suite v1 once and record every outcome.
- [ ] Complete the one authorized restart of the interrupted rate-limiter candidate.
- [ ] Manually review a genuine candidate failure when one occurs.
- [x] Repository snapshot, baseline tests, adapter, persistence, final tests/diff.
- [x] API and React form, saved runs, trajectory inspection.
- [x] Conservative structured diagnosis with validated event references (real failing-run validation pending).
- [x] Clean-baseline recovery and measured comparison (integration-tested; live validation pending).
- [x] Error handling, process timeouts, isolation and lifecycle tests (37 passing, including candidate baselines; Python type checks pass).
- [x] Real reproducible evidence and polished UI (five completed live tasks passed; one redacted recording is reproducible).
- [x] README, setup/check scripts, CI configuration, desktop and narrow-window UI review.
- [x] Fresh-clone installation, complete checks and recorded patch reproduction.
- [x] Short GIF of real passing-run inspection, explicitly labeled as partial workflow coverage.
- [x] Public Git history scan for machine paths and common credential patterns.
- [x] Hosted GitHub CI passed on macOS with Python 3.11 and 3.13 after publication.
- [ ] Genuine failing Codex run, grounded diagnosis and targeted retry with measured comparison.
- [ ] Recording of the complete failure → diagnosis → retry → comparison story.
- [ ] Full 13-step Definition of Done from a fresh checkout and final Cursor submission approval.

No stretch goals before the definition of done. All real logs remain in ignored local storage; only explicitly reviewed, sanitized evidence belongs in Git.

Section 33 verified with codex-cli 0.153.4: 13 real JSONL records, exit 0, isolated edit and compilation. Source file unchanged. Raw evidence retained outside Git.

The real caching task passed (7 actions, 2 files). Do not present that success as a failure or a recovery. API, React UI, diagnosis and recovery are implemented; live failure/recovery evidence remains outstanding.

Publication audit: fresh clone setup and all checks passed; imported real recording inspected in the UI and its patch reproduced successfully. Fixed hidden history in narrow windows and added interrupted-agent outcome regression tests. See docs/submission-review.md for the eight-question review and remaining completion gate. No completion claim.
