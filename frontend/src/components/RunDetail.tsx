import { useState } from "react";
import { AgentEvent, Detail, Run, terminal } from "../types";
import { Badge, Metric, duration, labels } from "./shared";

export default function RunDetail({
  detail,
  parent,
  busy,
  action,
  navigate,
}: {
  detail: Detail;
  parent: Run | null;
  busy: boolean;
  action: (kind: "retry" | "cancel") => void;
  navigate: (id: string) => void;
}) {
  const { run, events, logs, recoveries, artifacts } = detail;
  const [tab, setTab] = useState("Trajectory");
  const [eventId, setEventId] = useState<string | null>(null);
  const diagnosis = run.diagnosis;
  const focus = eventId || diagnosis?.first_consequential_event_id;
  const event = events.find((e) => e.id === focus);
  const visibleEvents = events.filter(
    (e) =>
      (e.raw_event.type !== "item.started" &&
        e.raw_event.type !== "item.updated") ||
      e.id === diagnosis?.first_consequential_event_id,
  );
  const current = visibleEvents.findIndex(
    (e) => e.id === diagnosis?.first_consequential_event_id,
  );
  return (
    <div className="detail">
      <div className="detail-kicker">
        <span className="eyebrow">
          {run.parent_run_id
            ? "RECOVERY EXPERIMENT"
            : "CODING AGENT EXPERIMENT"}{" "}
          / {run.id.slice(0, 8)}
        </span>
        <Badge status={run.status} />
      </div>
      <h1 className="run-title">{run.source_repo.split("/").pop()}</h1>
      <p className="task-description">{run.task}</p>
      <div className="run-meta">
        <code>{run.test_command}</code>
        <span>{run.codex_version || "Codex"}</span>
        {run.recorded && <span className="recorded">Recorded real run</span>}
      </div>
      {!terminal.has(run.status) && (
        <div className="progress" role="status">
          <span className="pulse" />
          {labels[run.status]}… Raw evidence is being saved.
          <button onClick={() => action("cancel")} disabled={busy}>
            Cancel run
          </button>
        </div>
      )}
      {run.error && <div className="error-banner">{run.error}</div>}
      <div className="metrics">
        <Metric
          label="FINAL TEST EXIT"
          value={run.final_test?.exit_code ?? "—"}
        />
        <Metric label="TOOL ACTIONS" value={run.action_count} />
        <Metric label="FILES CHANGED" value={run.files_changed.length} />
        <Metric
          label="AGENT DURATION"
          value={duration(run.agent?.duration_ms)}
        />
        <Metric
          label="BASELINE"
          value={
            run.baseline
              ? run.baseline.exit_code === 0
                ? "Passed"
                : `Exit ${run.baseline.exit_code}`
              : "—"
          }
        />
      </div>
      {parent && <Comparison original={parent} recovery={run} />}
      <div className="tabs" role="tablist">
        {["Trajectory", "Tests & diff", "Artifacts"].map((name) => (
          <button
            key={name}
            role="tab"
            aria-selected={tab === name}
            className={tab === name ? "active" : ""}
            onClick={() => setTab(name)}
          >
            {name}
            {name === "Trajectory" && <span>{events.length}</span>}
          </button>
        ))}
      </div>
      {tab === "Trajectory" && (
        <div className="investigation">
          <section className="panel timeline-panel">
            <div className="panel-heading">
              <div>
                <h2>Agent trajectory</h2>
                <p>Ordered evidence from Codex JSONL</p>
              </div>
              <span className="subtle">{visibleEvents.length} events</span>
            </div>
            <div className="timeline">
              {visibleEvents.map((item) => (
                <EventRow
                  key={item.id}
                  event={item}
                  selected={focus === item.id}
                  causal={diagnosis?.first_consequential_event_id === item.id}
                  onClick={() => setEventId(item.id)}
                />
              ))}
              {!visibleEvents.length && (
                <div className="empty">
                  Waiting for the first event. Baseline tests run first.
                </div>
              )}
            </div>
            {event && (
              <div className="event-inspector">
                <div className="eyebrow">
                  EVENT {event.id} · {event.event_type}
                </div>
                <pre>{event.summary || event.title}</pre>
                <details>
                  <summary>Inspect raw event</summary>
                  <pre>{JSON.stringify(event.raw_event, null, 2)}</pre>
                </details>
              </div>
            )}
          </section>
          <aside className="diagnosis-column">
            {diagnosis ? (
              <section className="diagnosis-card">
                <div className="diagnosis-label">
                  <span>⌁</span> FAILURE ANALYSIS
                </div>
                <h2>
                  {diagnosis.status === "diagnosed"
                    ? "Likely first consequential mistake"
                    : "Insufficient evidence"}
                </h2>
                {diagnosis.first_consequential_event_id && (
                  <button
                    className="causal-link"
                    onClick={() =>
                      setEventId(diagnosis.first_consequential_event_id)
                    }
                  >
                    ↳{" "}
                    {current >= 0
                      ? `Event ${diagnosis.first_consequential_event_id}`
                      : diagnosis.first_consequential_event_id}
                  </button>
                )}
                <div className="failure-mode">{diagnosis.failure_mode}</div>
                <p>{diagnosis.explanation}</p>
                <h3>Evidence</h3>
                <ul>
                  {diagnosis.evidence.map((e, i) => (
                    <li key={i}>{e}</li>
                  ))}
                </ul>
                {diagnosis.suggested_intervention && (
                  <div className="intervention">
                    <h3>Targeted intervention</h3>
                    <p>{diagnosis.suggested_intervention}</p>
                  </div>
                )}
                <div className="confidence">
                  Model confidence{" "}
                  <b>{Math.round(diagnosis.confidence * 100)}%</b>
                  <small>Subjective · not calibrated</small>
                </div>
                {diagnosis.status === "diagnosed" && (
                  <button
                    className="primary retry"
                    disabled={
                      busy ||
                      run.status !== "failed" ||
                      recoveries.some((r) => !terminal.has(r.status))
                    }
                    onClick={() => action("retry")}
                  >
                    Retry with diagnosis <span>↗</span>
                  </button>
                )}
                <p className="caption">
                  Starts fresh from the saved input snapshot with this hint.
                </p>
              </section>
            ) : (
              <section className="panel diagnosis-empty">
                <div className="diagnosis-label">⌁ FAILURE ANALYSIS</div>
                <h2>
                  {run.status === "succeeded"
                    ? "The supplied tests passed."
                    : "Diagnosis follows failure."}
                </h2>
                <p>
                  {run.diagnosis_error ||
                    (run.status === "succeeded"
                      ? "No failure was diagnosed. Passing tests do not establish correctness beyond the supplied checks."
                      : "After a healthy baseline and a failed final test, TraceMine looks for an earlier consequential decision.")}
                </p>
              </section>
            )}
            {recoveries.length > 0 && (
              <section className="panel recovery-list">
                <h3>Recovery runs</h3>
                {recoveries.map((r) => (
                  <button key={r.id} onClick={() => navigate(r.id)}>
                    <span>{r.id.slice(0, 8)}</span>
                    <Badge status={r.status} />
                    <span>↗</span>
                  </button>
                ))}
              </section>
            )}
          </aside>
        </div>
      )}
      {tab === "Tests & diff" && (
        <div className="evidence-grid">
          <section className="panel evidence-panel">
            <h2>Test output</h2>
            {["baseline", "final"].map((stage) => (
              <div key={stage}>
                <h3>
                  {stage === "baseline" ? "Baseline" : "Final verification"}{" "}
                  <span>
                    exit{" "}
                    {stage === "baseline"
                      ? (run.baseline?.exit_code ?? "—")
                      : (run.final_test?.exit_code ?? "—")}
                  </span>
                </h3>
                <pre>
                  {logs[`${stage}.stdout`] || "No stdout recorded."}
                  {logs[`${stage}.stderr`]
                    ? `\nSTDERR\n${logs[`${stage}.stderr`]}`
                    : ""}
                </pre>
              </div>
            ))}
          </section>
          <section className="panel evidence-panel">
            <h2>Final repository diff</h2>
            <p className="subtle">
              Compared with the exact input snapshot. {run.files_changed.length}{" "}
              changed files.
            </p>
            <pre className="diff">
              {run.final_diff
                ? run.final_diff.split("\n").map((line, i) => (
                    <span
                      key={i}
                      className={
                        line.startsWith("+")
                          ? "added"
                          : line.startsWith("-")
                            ? "removed"
                            : ""
                      }
                    >
                      {line}
                      {"\n"}
                    </span>
                  ))
                : "No changes recorded."}
            </pre>
          </section>
        </div>
      )}
      {tab === "Artifacts" && (
        <section className="panel artifacts">
          <h2>Audit trail</h2>
          <p>
            Original process bytes are retained locally. Downloads may contain
            source code and private paths; review before sharing.
          </p>
          <div className="artifact-list">
            {artifacts.map((name) => (
              <a
                key={name}
                href={`/api/runs/${run.id}/artifacts/${name}`}
                download
              >
                <code>{name}</code>
                <span>Download ↓</span>
              </a>
            ))}
          </div>
          <h3>Input snapshot SHA-256</h3>
          <code className="digest">
            {run.snapshot_digest || "Not available"}
          </code>
        </section>
      )}
      <p className="footnote">
        A diagnosis is a hypothesis. A successful recovery after intervention
        does not prove causality.
      </p>
    </div>
  );
}

function EventRow({
  event,
  selected,
  causal,
  onClick,
}: {
  event: AgentEvent;
  selected: boolean;
  causal: boolean;
  onClick: () => void;
}) {
  const rawItem = event.raw_event.item as
    { exit_code?: number; status?: string } | undefined;
  const failed =
    (rawItem?.exit_code != null && rawItem.exit_code !== 0) ||
    event.event_type === "error";
  const symbol = causal
    ? "!"
    : failed
      ? "×"
      : event.event_type === "file_change"
        ? "±"
        : event.event_type === "command"
          ? "›_"
          : "·";
  const title = event.title
    .replace(/\/[^\s,]*\/repo\//g, "")
    .replace(/^\/bin\/(?:zsh|bash) -lc /, "");
  return (
    <button
      className={`event-row ${selected ? "selected" : ""} ${causal ? "causal" : ""}`}
      onClick={onClick}
    >
      <span className="sequence">
        {event.sequence.toString().padStart(2, "0")}
      </span>
      <span className={`event-icon ${failed ? "failed" : ""}`}>{symbol}</span>
      <div>
        <span className="event-type">{event.event_type.replace("_", " ")}</span>
        <strong>{title}</strong>
        {causal && (
          <small className="causal-tag">FIRST LIKELY CAUSAL ERROR</small>
        )}
      </div>
      <span className="event-arrow">↗</span>
    </button>
  );
}

function Comparison({ original, recovery }: { original: Run; recovery: Run }) {
  return (
    <section className="panel comparison">
      <div>
        <div className="eyebrow">RECOVERY EXPERIMENT</div>
        <h2>
          {recovery.status === "succeeded"
            ? "Recovery succeeded after intervention"
            : "Compare the two attempts"}
        </h2>
        <p>Same task. Same input snapshot. One targeted hint.</p>
      </div>
      <table>
        <thead>
          <tr>
            <th>Measured outcome</th>
            <th>Original</th>
            <th>Recovery</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th>Result</th>
            <td>
              <Badge status={original.status} />
            </td>
            <td>
              <Badge status={recovery.status} />
            </td>
          </tr>
          <tr>
            <th>Test exit code</th>
            <td>{original.final_test?.exit_code ?? "—"}</td>
            <td>{recovery.final_test?.exit_code ?? "—"}</td>
          </tr>
          <tr>
            <th>Tool actions</th>
            <td>{original.action_count}</td>
            <td>{recovery.action_count}</td>
          </tr>
          <tr>
            <th>Files changed</th>
            <td>{original.files_changed.length}</td>
            <td>{recovery.files_changed.length}</td>
          </tr>
          <tr>
            <th>Agent duration</th>
            <td>{duration(original.agent?.duration_ms)}</td>
            <td>{duration(recovery.agent?.duration_ms)}</td>
          </tr>
        </tbody>
      </table>
    </section>
  );
}
