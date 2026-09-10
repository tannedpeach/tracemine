import { useEffect, useState } from 'react';
import { api, initialize } from './api';
import { AgentEvent, Detail, Run, terminal } from './types';

const demoTask = 'Add a small in-memory TTL cache for GET /issues/<id>. The TTL is 60 seconds. Preserve the existing API behavior, ensure writes are immediately visible, keep app instances independent, and add tests covering caching, expiry, invalidation and missing issues. Run python3 -m pytest -q to verify.';
const duration = (ms: number | null | undefined) => ms == null ? '—' : ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`;
const labels: Record<string, string> = { succeeded: 'Tests passed', failed: 'Tests failed', baseline_failed: 'Baseline failed', running_agent: 'Codex running', baseline_testing: 'Checking baseline', testing: 'Verifying', diagnosing: 'Diagnosing', created: 'Queued', preparing: 'Preparing', cancelled: 'Cancelled', error: 'Run error' };
function Badge({ status }: { status: string }) { return <span className={`badge ${status}`}><i />{labels[status] || status}</span>; }
function Metric({ label, value }: { label: string; value: React.ReactNode }) { return <div className="metric"><small>{label}</small><strong>{value}</strong></div>; }

export default function App() {
  const [runs, setRuns] = useState<Run[]>([]);
  const [selected, setSelected] = useState(location.hash.slice(1));
  const [detail, setDetail] = useState<Detail | null>(null);
  const [error, setError] = useState('');
  const [ready, setReady] = useState(false);
  const [busy, setBusy] = useState(false);
  const [repo, setRepo] = useState('');
  const [task, setTask] = useState('');
  const [command, setCommand] = useState('python3 -m pytest -q');
  const [example, setExample] = useState('');
  const [parent, setParent] = useState<Run | null>(null);

  useEffect(() => { initialize().then(info => { setExample(info.example_repo); setReady(true); }).catch(e => setError(e.message)); }, []);
  useEffect(() => { const onHash = () => setSelected(location.hash.slice(1)); window.addEventListener('hashchange', onHash); return () => window.removeEventListener('hashchange', onHash); }, []);
  useEffect(() => {
    if (!ready) return;
    let live = true;
    let timeout: ReturnType<typeof setTimeout>;
    const refresh = async () => {
      try {
        const history = await api<Run[]>('/runs');
        const current = selected ? await api<Detail>(`/runs/${selected}`) : null;
        const prior = current?.run.parent_run_id ? (await api<Detail>(`/runs/${current.run.parent_run_id}`)).run : null;
        if (live) { setRuns(history); setDetail(current); setParent(prior); setError(''); }
      } catch (e) { if (live) setError((e as Error).message); }
      if (live) timeout = setTimeout(refresh, 1500);
    };
    void refresh();
    return () => { live = false; clearTimeout(timeout); };
  }, [ready, selected]);

  const navigate = (id: string) => { setDetail(null); setParent(null); setSelected(id); location.hash = id; };
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setBusy(true); setError('');
    try { const run = await api<Run>('/runs', { repo, task, test_command: command }); navigate(run.id); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }
  async function action(kind: 'retry' | 'cancel') {
    if (!detail) return;
    setBusy(true); setError('');
    try { const result = await api<Run>(`/runs/${detail.run.id}/${kind}`, {}); if (kind === 'retry') navigate(result.id); }
    catch (e) { setError((e as Error).message); } finally { setBusy(false); }
  }

  return <div className="shell">
    <aside className="sidebar">
      <a className="brand" href="#" onClick={() => navigate('')}><span className="mark">⌁</span> TraceMine<span className="version">v0.1</span></a>
      <div className="workspace"><span className="online" /> LOCAL WORKSPACE</div>
      <button className={`new-run ${!selected ? 'active' : ''}`} onClick={() => navigate('')}>＋ New experiment</button>
      <div className="history-heading">RUN HISTORY <span>{runs.length.toString().padStart(2, '0')}</span></div>
      <nav aria-label="Run history">{runs.map(run => <button key={run.id} className={`history ${selected === run.id ? 'selected' : ''}`} onClick={() => navigate(run.id)}><div><span className={`status-dot ${run.status}`} /><strong>{run.parent_run_id ? '↳ Recovery' : run.source_repo.split('/').pop()}</strong><span className="tiny-id">{run.id.slice(0, 5)}</span></div><p>{run.task}</p><small>{labels[run.status]} · {new Date(run.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}</small></button>)}</nav>
      {!runs.length && <p className="sidebar-empty">Your experiments will appear here. Every run keeps its original evidence.</p>}
      <div className="sidebar-footer"><span>●</span> Evidence over intuition.<small>Local runs · Immutable inputs</small></div>
    </aside>
    <main>
      <header className="topbar"><span>WORKSPACE <b>/</b> {selected ? 'EXPERIMENT' : 'OVERVIEW'}</span><span className="local-label"><i /> Local-first evaluation</span></header>
      {error && <div className="error-banner" role="alert">{error}</div>}
      {!selected ? <div className="home">
        <div className="eyebrow">A DEBUGGER FOR CODING-AGENT TRAJECTORIES</div>
        <h1>Find where the run<br />first went wrong<span>.</span></h1>
        <p className="intro">A failing test tells you the outcome. TraceMine connects it to an earlier decision, then tests a targeted intervention.</p>
        <div className="flow"><span>01 <b>Run Codex</b></span><em>→</em><span>02 <b>Inspect the failure</b></span><em>→</em><span>03 <b>Retry & compare</b></span></div>
        <section className="panel form-panel"><div className="panel-heading"><div><h2>Start an experiment</h2><p>A Python repository, a task, and a test command.</p></div><button className="text-button" onClick={() => { setRepo(example); setTask(demoTask); }}>Use example ↗</button></div>
          <form onSubmit={submit}>
            <label>Repository <span>LOCAL PATH</span><input required value={repo} onChange={e => setRepo(e.target.value)} placeholder="/path/to/python-repo" /></label>
            <label>Coding task<textarea required value={task} onChange={e => setTask(e.target.value)} placeholder="What should Codex change? Include the behavior you expect." rows={4} /></label>
            <label>Test command<input required className="mono" value={command} onChange={e => setCommand(e.target.value)} /></label>
            <div className="form-footer"><p><span>▣</span> Runs in an isolated copy.<br /><small>Baseline must pass before Codex starts.</small></p><button className="primary" disabled={busy || !ready} type="submit">{busy ? 'Starting…' : 'Run agent'} <span>↗</span></button></div>
          </form>
        </section>
        <div className="footnote">Model-generated diagnoses are hypotheses. Recovery tests their usefulness, not causality.</div>
      </div> : detail ? <RunDetail key={detail.run.id} detail={detail} parent={parent} busy={busy} action={action} navigate={navigate} /> : <div className="loading" role="status">Loading experiment…</div>}
    </main>
  </div>;
}

function RunDetail({ detail, parent, busy, action, navigate }: { detail: Detail; parent: Run | null; busy: boolean; action: (kind: 'retry' | 'cancel') => void; navigate: (id: string) => void }) {
  const { run, events, logs, recoveries, artifacts } = detail;
  const [tab, setTab] = useState('Trajectory');
  const [eventId, setEventId] = useState<string | null>(null);
  const diagnosis = run.diagnosis;
  const focus = eventId || diagnosis?.first_consequential_event_id;
  const event = events.find(e => e.id === focus);
  const visibleEvents = events.filter(e => e.raw_event.type !== 'item.started' && e.raw_event.type !== 'item.updated');
  const current = visibleEvents.findIndex(e => e.id === diagnosis?.first_consequential_event_id);
  return <div className="detail">
    <div className="detail-kicker"><span className="eyebrow">{run.parent_run_id ? 'RECOVERY EXPERIMENT' : 'CODING AGENT EXPERIMENT'} / {run.id.slice(0, 8)}</span><Badge status={run.status} /></div>
    <h1 className="run-title">{run.source_repo.split('/').pop()}</h1>
    <p className="task-description">{run.task}</p>
    <div className="run-meta"><code>{run.test_command}</code><span>{run.codex_version || 'Codex'}</span>{run.recorded && <span className="recorded">Recorded real run</span>}</div>
    {!terminal.has(run.status) && <div className="progress" role="status"><span className="pulse" />{labels[run.status]}… Raw evidence is being saved.<button onClick={() => action('cancel')} disabled={busy}>Cancel run</button></div>}
    {run.error && <div className="error-banner">{run.error}</div>}
    <div className="metrics"><Metric label="FINAL TEST EXIT" value={run.final_test?.exit_code ?? '—'} /><Metric label="TOOL ACTIONS" value={run.action_count} /><Metric label="FILES CHANGED" value={run.files_changed.length} /><Metric label="AGENT DURATION" value={duration(run.agent?.duration_ms)} /><Metric label="BASELINE" value={run.baseline ? (run.baseline.exit_code === 0 ? 'Passed' : `Exit ${run.baseline.exit_code}`) : '—'} /></div>
    {parent && <Comparison original={parent} recovery={run} />}
    <div className="tabs" role="tablist">{['Trajectory', 'Tests & diff', 'Artifacts'].map(name => <button key={name} role="tab" aria-selected={tab === name} className={tab === name ? 'active' : ''} onClick={() => setTab(name)}>{name}{name === 'Trajectory' && <span>{events.length}</span>}</button>)}</div>
    {tab === 'Trajectory' && <div className="investigation">
      <section className="panel timeline-panel"><div className="panel-heading"><div><h2>Agent trajectory</h2><p>Ordered evidence from Codex JSONL</p></div><span className="subtle">{visibleEvents.length} events</span></div>
        <div className="timeline">{visibleEvents.map((item) => <EventRow key={item.id} event={item} selected={focus === item.id} causal={diagnosis?.first_consequential_event_id === item.id} onClick={() => setEventId(item.id)} />)}{!visibleEvents.length && <div className="empty">Waiting for the first event. Baseline tests run first.</div>}</div>
        {event && <div className="event-inspector"><div className="eyebrow">EVENT {event.id} · {event.event_type}</div><pre>{event.summary || event.title}</pre><details><summary>Inspect raw event</summary><pre>{JSON.stringify(event.raw_event, null, 2)}</pre></details></div>}
      </section>
      <aside className="diagnosis-column">{diagnosis ? <section className="diagnosis-card"><div className="diagnosis-label"><span>⌁</span> FAILURE ANALYSIS</div><h2>{diagnosis.status === 'diagnosed' ? 'Likely first consequential mistake' : 'Insufficient evidence'}</h2>{diagnosis.first_consequential_event_id && <button className="causal-link" onClick={() => setEventId(diagnosis.first_consequential_event_id)}>↳ {current >= 0 ? `Event ${diagnosis.first_consequential_event_id}` : diagnosis.first_consequential_event_id}</button>}<div className="failure-mode">{diagnosis.failure_mode}</div><p>{diagnosis.explanation}</p><h3>Evidence</h3><ul>{diagnosis.evidence.map((e, i) => <li key={i}>{e}</li>)}</ul>{diagnosis.suggested_intervention && <div className="intervention"><h3>Targeted intervention</h3><p>{diagnosis.suggested_intervention}</p></div>}<div className="confidence">Model confidence <b>{Math.round(diagnosis.confidence * 100)}%</b><small>Subjective · not calibrated</small></div>{diagnosis.status === 'diagnosed' && <button className="primary retry" disabled={busy || run.status !== 'failed' || recoveries.some(r => !terminal.has(r.status))} onClick={() => action('retry')}>Retry with diagnosis <span>↗</span></button>}<p className="caption">Starts fresh from the saved input snapshot with this hint.</p></section> : <section className="panel diagnosis-empty"><div className="diagnosis-label">⌁ FAILURE ANALYSIS</div><h2>{run.status === 'succeeded' ? 'The supplied tests passed.' : 'Diagnosis follows failure.'}</h2><p>{run.diagnosis_error || (run.status === 'succeeded' ? 'No failure was diagnosed. Passing tests do not establish correctness beyond the supplied checks.' : 'After a healthy baseline and a failed final test, TraceMine looks for an earlier consequential decision.')}</p></section>}
        {recoveries.length > 0 && <section className="panel recovery-list"><h3>Recovery runs</h3>{recoveries.map(r => <button key={r.id} onClick={() => navigate(r.id)}><span>{r.id.slice(0, 8)}</span><Badge status={r.status} /><span>↗</span></button>)}</section>}
      </aside>
    </div>}
    {tab === 'Tests & diff' && <div className="evidence-grid"><section className="panel evidence-panel"><h2>Test output</h2>{['baseline', 'final'].map(stage => <div key={stage}><h3>{stage === 'baseline' ? 'Baseline' : 'Final verification'} <span>exit {stage === 'baseline' ? run.baseline?.exit_code ?? '—' : run.final_test?.exit_code ?? '—'}</span></h3><pre>{logs[`${stage}.stdout`] || 'No stdout recorded.'}{logs[`${stage}.stderr`] ? `\nSTDERR\n${logs[`${stage}.stderr`]}` : ''}</pre></div>)}</section><section className="panel evidence-panel"><h2>Final repository diff</h2><p className="subtle">Compared with the exact input snapshot. {run.files_changed.length} changed files.</p><pre className="diff">{run.final_diff ? run.final_diff.split('\n').map((line, i) => <span key={i} className={line.startsWith('+') ? 'added' : line.startsWith('-') ? 'removed' : ''}>{line}{'\n'}</span>) : 'No changes recorded.'}</pre></section></div>}
    {tab === 'Artifacts' && <section className="panel artifacts"><h2>Audit trail</h2><p>Original process bytes are retained locally. Downloads may contain source code and private paths; review before sharing.</p><div className="artifact-list">{artifacts.map(name => <a key={name} href={`/api/runs/${run.id}/artifacts/${name}`} download><code>{name}</code><span>Download ↓</span></a>)}</div><h3>Input snapshot SHA-256</h3><code className="digest">{run.snapshot_digest || 'Not available'}</code></section>}
    <p className="footnote">A diagnosis is a hypothesis. A successful recovery after intervention does not prove causality.</p>
  </div>;
}

function EventRow({ event, selected, causal, onClick }: { event: AgentEvent; selected: boolean; causal: boolean; onClick: () => void }) {
  const rawItem = event.raw_event.item as { exit_code?: number; status?: string } | undefined;
  const failed = (rawItem?.exit_code != null && rawItem.exit_code !== 0) || event.event_type === 'error';
  const symbol = causal ? '!' : failed ? '×' : event.event_type === 'file_change' ? '±' : event.event_type === 'command' ? '›_' : '·';
  const title = event.title.replace(/\/[^\s,]*\/repo\//g, '').replace(/^\/bin\/(?:zsh|bash) -lc /, '');
  return <button className={`event-row ${selected ? 'selected' : ''} ${causal ? 'causal' : ''}`} onClick={onClick}><span className="sequence">{event.sequence.toString().padStart(2, '0')}</span><span className={`event-icon ${failed ? 'failed' : ''}`}>{symbol}</span><div><span className="event-type">{event.event_type.replace('_', ' ')}</span><strong>{title}</strong>{causal && <small className="causal-tag">FIRST LIKELY CAUSAL ERROR</small>}</div><span className="event-arrow">↗</span></button>;
}

function Comparison({ original, recovery }: { original: Run; recovery: Run }) {
  return <section className="panel comparison"><div><div className="eyebrow">RECOVERY EXPERIMENT</div><h2>{recovery.status === 'succeeded' ? 'Recovery succeeded after intervention' : 'Compare the two attempts'}</h2><p>Same task. Same input snapshot. One targeted hint.</p></div><table><thead><tr><th>Measured outcome</th><th>Original</th><th>Recovery</th></tr></thead><tbody><tr><th>Result</th><td><Badge status={original.status} /></td><td><Badge status={recovery.status} /></td></tr><tr><th>Test exit code</th><td>{original.final_test?.exit_code ?? '—'}</td><td>{recovery.final_test?.exit_code ?? '—'}</td></tr><tr><th>Tool actions</th><td>{original.action_count}</td><td>{recovery.action_count}</td></tr><tr><th>Files changed</th><td>{original.files_changed.length}</td><td>{recovery.files_changed.length}</td></tr><tr><th>Agent duration</th><td>{duration(original.agent?.duration_ms)}</td><td>{duration(recovery.agent?.duration_ms)}</td></tr></tbody></table></section>;
}
