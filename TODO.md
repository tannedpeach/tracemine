# TraceMine MVP

## Gate: Section 33
- [x] Read handover completely; inspect empty workspace and installed tools.
- [x] Inspect `codex --help` and `codex exec --help`.
- [x] Minimal backend/frontend skeleton and isolated capture script.
- [x] Prove real JSONL capture on a disposable Git repository.

## Implementation order
- [x] Repository snapshot, baseline tests, adapter, persistence, final tests/diff.
- [x] API and React form, saved runs, trajectory inspection.
- [x] Conservative structured diagnosis with validated event references (real failing-run validation pending).
- [x] Clean-baseline recovery and measured comparison (integration-tested; live validation pending).
- [ ] Error handling, process timeouts, isolation and lifecycle tests.
- [ ] Real reproducible demo evidence and polished UI.
- [ ] README, short demo recording, fresh-clone validation.
- [ ] Cursor submission review; address all eight review questions.

No stretch goals before the definition of done. All real logs remain in ignored local storage; only explicitly reviewed, sanitized evidence belongs in Git.

Section 33 verified with codex-cli 0.153.4: 13 real JSONL records, exit 0, isolated edit and compilation. Source file unchanged. Raw evidence retained outside Git.

Backend milestone: 16 tests passing; real caching task passed (7 actions, 2 files). Do not present that success as a failure or a recovery. API, React UI, conservative diagnosis and recovery are implemented. Need real failing evidence, visual review, and packaging.
