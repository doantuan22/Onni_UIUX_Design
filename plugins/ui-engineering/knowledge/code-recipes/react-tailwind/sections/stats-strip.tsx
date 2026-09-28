/**
 * @recipe stats-strip
 *
 * Metrics as a definition list with hairline dividers and tabular figures instead of floating round numbers. Each
 * metric can carry its source or period so the numbers read as evidence; render only metrics the product can back.
 *
 * Usage:
 *   <StatsStrip items={[{ value: "10,400", label: "teams", note: "active in Sept 2026" }, { value: "99.95%", label: "uptime", note: "last 12 months" }]} />
 */
export type Stat = { value: string; label: string; note?: string };
export type StatsStripProps = { items: Stat[]; label?: string };

export function StatsStrip({ items, label = "Key figures" }: StatsStripProps) {
  return (
    <section aria-label={label} className="border-y border-ink-200">
      <dl className="mx-auto grid max-w-7xl grid-cols-2 divide-ink-200 px-6 md:grid-cols-4 md:divide-x">
        {items.map((item) => (
          <div key={item.label} className="flex flex-col-reverse gap-1 py-8 md:px-8 md:first:pl-0">
            <dt className="text-sm text-ink-600">
              {item.label}
              {item.note && <span className="block font-mono text-xs text-ink-500">{item.note}</span>}
            </dt>
            <dd className="font-display text-4xl font-semibold tracking-tight tabular-nums text-ink-950">{item.value}</dd>
          </div>
        ))}
      </dl>
    </section>
  );
}
