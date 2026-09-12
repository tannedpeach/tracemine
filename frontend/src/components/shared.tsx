export const duration = (ms: number | null | undefined) =>
  ms == null ? "N/A" : ms < 1000 ? `${ms} ms` : `${(ms / 1000).toFixed(1)} s`;
export const labels: Record<string, string> = {
  succeeded: "Tests passed",
  failed: "Tests failed",
  baseline_failed: "Baseline failed",
  running_agent: "Codex running",
  baseline_testing: "Checking baseline",
  testing: "Verifying",
  diagnosing: "Diagnosing",
  created: "Queued",
  preparing: "Preparing",
  cancelled: "Cancelled",
  error: "Run error",
};
export function Badge({ status }: { status: string }) {
  return (
    <span className={`badge ${status}`}>
      <i />
      {labels[status] || status}
    </span>
  );
}
export function Metric({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="metric">
      <small>{label}</small>
      <strong>{value}</strong>
    </div>
  );
}
