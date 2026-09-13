# TraceMine status

TraceMine's MVP is implemented and the repository is maintained as a focused local
coding-agent debugging tool.

Completed:

- End-to-end Codex capture with isolated snapshots, baseline and final verification,
  retained diffs, raw logs, SQLite persistence, and a React inspection UI.
- Conservative diagnosis and clean-snapshot retry flows, with explicit process and
  verification error states.
- Fresh-clone setup, backend and frontend checks, reproducible demo recording, and
  public documentation of architecture and trust boundaries.
- Fixed evaluations v1 through v3, plus historical suite v4 using three pinned
  public-repository bugs. Every v4 baseline passed, each pre-fix regression failed,
  each historical fix passed, and all three first Codex attempts passed.

Known limitation:

- The fixed evaluations produced no genuine live coding failure with a defensible
  diagnosis and targeted recovery. The included GIF therefore shows a passing-run
  inspection, and the missing failure-to-recovery recording is documented honestly.

Possible future work:

- Add human-labeled diagnosis evaluation if a carefully scoped research phase is
  justified. This is outside the current MVP and submission scope.
