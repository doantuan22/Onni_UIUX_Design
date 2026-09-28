/**
 * @recipe dashboard-focus
 *
 * Content-first dashboard header: the metric the user opened the page for gets the largest area next to its chart;
 * secondary KPIs shrink into a hairline strip with deltas. Replaces rows of equal KPI cards with icons and shadows.
 * Keeps every KPI, label and data binding; only the hierarchy changes.
 *
 * Usage:
 *   <DashboardFocus
 *     primary={{ label: "Successful runs", value: "18,204", delta: "+12.4%", trend: "up", period: "Last 7 days" }}
 *     chart={<RunsChart data={runs} />}
 *     secondary={[{ label: "Failed", value: "42", delta: "−8%", trend: "down" }, { label: "Avg duration", value: "1.8 s" }]}
 *   />
 */
import type { ReactNode } from "react";

export type Kpi = { label: string; value: string; delta?: string; trend?: "up" | "down" | "flat"; period?: string };
export type DashboardFocusProps = { primary: Kpi; chart: ReactNode; secondary: Kpi[]; actions?: ReactNode };

const TREND: Record<NonNullable<Kpi["trend"]>, string> = {
  up: "text-emerald-700",
  down: "text-rose-700",
  flat: "text-ink-600",
};

function Delta({ kpi }: { kpi: Kpi }) {
  if (!kpi.delta) return null;
  return <span className={`font-mono text-sm tabular-nums ${TREND[kpi.trend ?? "flat"]}`}>{kpi.delta}</span>;
}

export function DashboardFocus({ primary, chart, secondary, actions }: DashboardFocusProps) {
  return (
    <section aria-label="Overview" className="rounded-[var(--radius-panel)] border border-ink-200 bg-white">
      <div className="grid xl:grid-cols-[minmax(16rem,1fr)_2fr]">
        <div className="flex flex-col gap-2 border-b border-ink-200 p-6 xl:border-b-0 xl:border-r">
          <div className="flex items-center justify-between gap-4">
            <h2 className="text-sm font-medium text-ink-700">{primary.label}</h2>
            {actions}
          </div>
          <p className="font-display text-5xl font-semibold tracking-tight tabular-nums text-ink-950">{primary.value}</p>
          <p className="flex items-center gap-3 text-sm text-ink-600">
            <Delta kpi={primary} />
            {primary.period}
          </p>
        </div>
        <div className="min-h-56 p-4 sm:p-6">{chart}</div>
      </div>
      {secondary.length > 0 && (
        <dl className="grid grid-cols-2 divide-ink-200 border-t border-ink-200 md:grid-cols-4 md:divide-x">
          {secondary.map((kpi) => (
            <div key={kpi.label} className="px-6 py-4">
              <dt className="text-xs font-medium uppercase tracking-wider text-ink-600">{kpi.label}</dt>
              <dd className="mt-1 flex items-baseline gap-2">
                <span className="text-xl font-semibold tabular-nums text-ink-950">{kpi.value}</span>
                <Delta kpi={kpi} />
              </dd>
            </div>
          ))}
        </dl>
      )}
    </section>
  );
}
