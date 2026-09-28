/** A static product view (run history) used as the hero and feature visual; replace with a real screenshot. */
const RUNS = [
  { name: "Sync CRM → Warehouse", status: "Succeeded", time: "1.2 s" },
  { name: "Invoice reminders", status: "Succeeded", time: "0.8 s" },
  { name: "Churn alert", status: "Retrying", time: "3.4 s" },
  { name: "Weekly digest", status: "Succeeded", time: "2.1 s" },
];

export function ProductShot() {
  return (
    <figure aria-label="Flowbase run history" className="bg-white">
      <div className="flex items-center justify-between border-b border-ink-200 px-5 py-3">
        <span className="text-sm font-semibold text-ink-900">Run history</span>
        <span className="font-mono text-xs text-ink-500">Last 24 h</span>
      </div>
      <ul className="divide-y divide-ink-100">
        {RUNS.map((run) => (
          <li key={run.name} className="grid grid-cols-[1fr_auto_auto] items-center gap-4 px-5 py-3 text-sm">
            <span className="truncate text-ink-800">{run.name}</span>
            <span className={run.status === "Succeeded" ? "text-emerald-700" : "text-amber-700"}>{run.status}</span>
            <span className="font-mono tabular-nums text-ink-500">{run.time}</span>
          </li>
        ))}
      </ul>
      <div className="grid grid-cols-3 border-t border-ink-200 text-center">
        {[["18,204", "runs"], ["99.6%", "success"], ["1.8 s", "median"]].map(([value, label]) => (
          <div key={label} className="px-3 py-4">
            <div className="font-display text-xl font-semibold tabular-nums text-ink-950">{value}</div>
            <div className="text-xs text-ink-500">{label}</div>
          </div>
        ))}
      </div>
    </figure>
  );
}
