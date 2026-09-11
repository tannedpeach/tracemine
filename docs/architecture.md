# Architecture and decisions

## State, not a distributed job system

`Runner` owns the lifecycle. FastAPI creates a task and polls SQLite-backed state. One filesystem lock owns a storage directory; one asyncio lock serializes runs. SQLite transactions persist each run update and normalized event. Raw bytes go directly to files rather than through a JSON database column.

The server marks previously unfinished runs as interrupted on startup. Graceful shutdown cancels tasks and kills their subprocess groups. This is a single-process MVP; there is no durable worker queue or transparent resume after a hard crash.

## Filesystem boundaries

Each experiment has four distinct kinds of state:

1. The user's source, read only during snapshot creation.
2. A retained input snapshot, outside agent write permissions.
3. Disposable baseline, agent, diff, and verification directories.
4. Metadata and append-only process output files outside the working copy.

The snapshot includes uncommitted files rather than silently checking out HEAD. It excludes `.git`, environments, secrets named `.env*`, and generated caches. It rejects symlinks and special files. Normalized executable permissions and file bytes contribute to a SHA-256 digest checked before running. The source commit is provenance; the content digest identifies the actual starting files.

A source can change while it is being copied; this is not an atomic filesystem snapshot. The retained bytes define the experiment input. Do not edit the source during snapshot creation if cross-file consistency matters.

Recovery references that snapshot even if the original directory has moved or changed. Baseline tests do not run in the agent's copy, because tests can write to configuration or create files. Final tests also use a separate copy, so the final diff remains the agent output.

Diff capture creates independent Git metadata and compares all changed tracked files plus untracked nonignored files. Agent-controlled hooks, filters, and Git configuration are never used for this comparison. Generated test temp files are excluded. Renames may appear as additions/deletions according to Git's detection.

## Process ownership

`execute` launches argument lists without a shell. The user-supplied test command is the deliberate exception: it runs through `/bin/sh -c` inside a filesystem/network sandbox. This allows ordinary test commands and pipelines while limiting writes to the disposable copy.

stdout/stderr are drained concurrently as bytes. JSONL parsing is an optional downstream callback; malformed text remains in the original stream. Event buffering is bounded at 2 MiB per incomplete line, and streams at 64 MiB. Oversized events get a visible capture warning and remain in the raw file. The log limit stops a process instead of silently exhausting the disk.

Timeout, exception, and cancellation paths kill the process group, including children that outlive the leader. This does not promise containment for deliberately daemonized hostile code. macOS uses `sandbox-exec`; Linux uses Bubblewrap. Unsupported environments fail closed. Apple's real Git executable is resolved via `xcrun` before sandboxing to avoid launcher cache writes.

## Diagnosis is an evidence consumer

A separate Codex invocation uses read-only mode and a JSON output schema. The prompt includes the task, ordered events, diff, and final stdout/stderr. Embedded repository instructions are treated as data. The model is asked not to use tools. Logs preserve both the exact submitted diagnosis context and the model stream.

Codex is both the coding agent and the separate diagnoser. This is not an unbiased
judge: event references and schema validation constrain the output, but human
review and measured recovery are still required. A future evaluation would compare
diagnoses with human labels or cross-model judges. Abnormally terminated agent
processes retain final verification evidence but do not trigger diagnosis.

Pydantic validates the response and requires a known event ID for a diagnosed result. Insufficient evidence must select no event. Invalid output becomes a visible diagnosis error without losing the failing-test outcome. The model's evidence statements still need human review; schema validation cannot establish causality.

The context includes up to 200 events with bounded fields, 40,000 diff characters and 24,000 bytes per test stream. Larger contexts are rejected or explicitly marked truncated. This trades full automatic analysis of enormous traces for a small, understandable MVP with complete raw evidence available manually.

## Measured comparisons

Tool actions are unique Codex tool item IDs across command, file-change, search, and tool events. Started and completed records count once. Agent time excludes baseline tests and diagnosis, so a failed run's diagnostic overhead does not inflate its coding time relative to recovery. Total run time is also retained separately, including queue wait.

Success means a normally completed agent and a final test exit code of zero. Agent process errors and verification timeouts have their own states. They are not mislabeled as ordinary test failures or successful recoveries.

## Choices deliberately omitted

No vector store, plugin framework, live streaming transport, task scheduler, Kubernetes, multiple agents, or checkpoint restoration. The interface protocol makes the Codex process testable; it is not a provider marketplace. Polling, SQLite, Git, and local files are enough to explain and reproduce the end-to-end loop.
