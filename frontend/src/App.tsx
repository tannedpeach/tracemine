import { useEffect, useState } from "react";
import { api, initialize } from "./api";
import { Detail, Run } from "./types";
import RunDetail from "./components/RunDetail";
import { labels } from "./components/shared";

const demoTask =
  "Add a small in-memory TTL cache for GET /issues/<id>. The TTL is 60 seconds. Preserve the existing API behavior, ensure writes are immediately visible, keep app instances independent, and add tests covering caching, expiry, invalidation and missing issues. Run python3 -m pytest -q to verify.";
export default function App() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selected, setSelected] = useState(location.hash.slice(1));
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState("");
  const [loadError, setLoadError] = useState("");
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [repo, setRepo] = useState("");
  const [task, setTask] = useState("");
  const [command, setCommand] = useState("python3 -m pytest -q");
  const [example, setExample] = useState("");
  const [parent, setParent] = useState<Run | null>(null);

  useEffect(() => {
    initialize()
      .then((info) => {
        setExample(info.example_repo);
        setReady(true);
      })
      .catch((e) => setError(e.message));
  }, []);
  useEffect(() => {
    const onHash = () => setSelected(location.hash.slice(1));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);
  useEffect(() => {
    if (!ready) return;
    let live = true;
    let timeout: ReturnType<typeof setTimeout>;
    const refresh = async () => {
      try {
        const history = await api<Run[]>("/runs");
        const current = selected
          ? await api<Detail>(`/runs/${selected}`)
          : null;
        const prior = current?.run.parent_run_id
          ? (await api<Detail>(`/runs/${current.run.parent_run_id}`)).run
          : null;
        if (live) {
          setRuns(history);
          setDetail(current);
          setParent(prior);
          setLoadError("");
        }
      } catch (e) {
        if (live) setLoadError((e as Error).message);
      }
      if (live) timeout = setTimeout(refresh, 1500);
    };
    void refresh();
    return () => {
      live = false;
      clearTimeout(timeout);
    };
  }, [ready, selected]);

  const navigate = (id: string) => {
    setError("");
    setLoadError("");
    setDetail(null);
    setParent(null);
    setSelected(id);
    location.hash = id;
  };
  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const run = await api<Run>("/runs", {
        repo,
        task,
        test_command: command,
      });
      navigate(run.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function action(kind: "retry" | "cancel") {
    if (!detail) return;
    setBusy(true);
    setError("");
    try {
      const result = await api<Run>(`/runs/${detail.run.id}/${kind}`, {});
      if (kind === "retry") navigate(result.id);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <a className="brand" href="#" onClick={() => navigate("")}>
          <span className="mark">⌁</span> TraceMine
          <span className="version">v0.1</span>
        </a>
        <div className="workspace">
          <span className="online" /> LOCAL WORKSPACE
        </div>
        <button
          className={`new-run ${!selected ? "active" : ""}`}
          onClick={() => navigate("")}
        >
          ＋ New experiment
        </button>
        <div className="history-heading">
          RUN HISTORY <span>{runs.length.toString().padStart(2, "0")}</span>
        </div>
        <nav aria-label="Run history">
          {runs.map((run) => (
            <button
              key={run.id}
              className={`history ${selected === run.id ? "selected" : ""}`}
              onClick={() => navigate(run.id)}
            >
              <div>
                <span className={`status-dot ${run.status}`} />
                <strong>
                  {run.parent_run_id
                    ? "↳ Recovery"
                    : run.source_repo.split("/").pop()}
                </strong>
                <span className="tiny-id">{run.id.slice(0, 5)}</span>
              </div>
              <p>{run.task}</p>
              <small>
                {labels[run.status]} ·{" "}
                {new Date(run.created_at).toLocaleDateString(undefined, {
                  month: "short",
                  day: "numeric",
                })}
              </small>
            </button>
          ))}
        </nav>
        {!runs.length && (
          <p className="sidebar-empty">
            Your experiments will appear here. Every run keeps its original
            evidence.
          </p>
        )}
        <div className="sidebar-footer">
          <span>●</span> Evidence over intuition.
          <small>Local runs · Immutable inputs</small>
        </div>
      </aside>
      <main>
        <header className="topbar">
          <span>
            WORKSPACE <b>/</b> {selected ? "EXPERIMENT" : "OVERVIEW"}
          </span>
          <span className="local-label">
            <i /> Local-first evaluation
          </span>
        </header>
        {(error || loadError) && (
          <div className="error-banner" role="alert">
            {error || loadError}
          </div>
        )}
        {!selected ? (
          <div className="home">
            <div className="eyebrow">
              A DEBUGGER FOR CODING-AGENT TRAJECTORIES
            </div>
            <h1>
              Find where the run
              <br />
              first went wrong<span>.</span>
            </h1>
            <p className="intro">
              A failing test tells you the outcome. TraceMine connects it to an
              earlier decision, then tests a targeted intervention.
            </p>
            <div className="flow">
              <span>
                01 <b>Run Codex</b>
              </span>
              <em>→</em>
              <span>
                02 <b>Inspect the failure</b>
              </span>
              <em>→</em>
              <span>
                03 <b>Retry & compare</b>
              </span>
            </div>
            <section className="panel form-panel">
              <div className="panel-heading">
                <div>
                  <h2>Start an experiment</h2>
                  <p>A Python repository, a task, and a test command.</p>
                </div>
                <button
                  className="text-button"
                  onClick={() => {
                    setRepo(example);
                    setTask(demoTask);
                  }}
                >
                  Use example ↗
                </button>
              </div>
              <form onSubmit={submit}>
                <label>
                  Repository <span>LOCAL PATH</span>
                  <input
                    required
                    value={repo}
                    onChange={(e) => setRepo(e.target.value)}
                    placeholder="/path/to/python-repo"
                  />
                </label>
                <label>
                  Coding task
                  <textarea
                    required
                    value={task}
                    onChange={(e) => setTask(e.target.value)}
                    placeholder="What should Codex change? Include the behavior you expect."
                    rows={4}
                  />
                </label>
                <label>
                  Test command
                  <input
                    required
                    className="mono"
                    value={command}
                    onChange={(e) => setCommand(e.target.value)}
                  />
                </label>
                <div className="form-footer">
                  <p>
                    <span>▣</span> Runs in an isolated copy.
                    <br />
                    <small>Baseline must pass before Codex starts.</small>
                  </p>
                  <button
                    className="primary"
                    disabled={busy || !ready}
                    type="submit"
                  >
                    {busy ? "Starting…" : "Run agent"} <span>↗</span>
                  </button>
                </div>
              </form>
            </section>
            <div className="footnote">
              Model-generated diagnoses are hypotheses. Recovery tests their
              usefulness, not causality.
            </div>
          </div>
        ) : detail ? (
          <RunDetail
            key={detail.run.id}
            detail={detail}
            parent={parent}
            busy={busy}
            action={action}
            navigate={navigate}
          />
        ) : (
          <div className="loading" role="status">
            Loading experiment…
          </div>
        )}
      </main>
    </div>
  );
}
