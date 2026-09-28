/**
 * @recipe editorial-index
 *
 * Numbered, left-aligned index for sequential or principle-like content (how it works, principles, chapters). A narrow
 * mono label column carries 01, 02, 03…; a wide column carries the heading and body. Replaces centered stacks and
 * equal card grids when the items are read in order.
 *
 * Usage:
 *   <EditorialIndex
 *     title="How Flowbase works"
 *     items={[
 *       { title: "Connect", body: "Link your tools with one click." },
 *       { title: "Automate", body: "Describe the workflow; Flowbase builds it." },
 *       { title: "Observe", body: "Every run is logged and replayable." },
 *     ]}
 *   />
 */
import type { ReactNode } from "react";

export type IndexItem = { title: string; body: ReactNode; meta?: string };
export type EditorialIndexProps = { id?: string; eyebrow?: string; title: string; items: IndexItem[] };

export function EditorialIndex({ id = "how-it-works", eyebrow, title, items }: EditorialIndexProps) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="mx-auto w-full max-w-7xl px-6 py-20 lg:py-28">
      <div className="grid gap-x-12 gap-y-10 lg:grid-cols-12">
        <header className="lg:col-span-4">
          {eyebrow && <p className="font-mono text-xs uppercase tracking-[0.18em] text-brand-700">{eyebrow}</p>}
          <h2 id={`${id}-title`} className="mt-3 font-display text-3xl font-semibold tracking-tight text-ink-950 sm:text-4xl">
            {title}
          </h2>
        </header>
        <ol className="divide-y divide-ink-200 border-y border-ink-200 lg:col-span-8">
          {items.map((item, index) => (
            <li key={item.title} className="grid gap-x-8 gap-y-2 py-8 sm:grid-cols-[6rem_1fr]">
              <span className="font-mono text-sm tabular-nums text-ink-500" aria-hidden="true">
                {String(index + 1).padStart(2, "0")}
              </span>
              <div>
                <h3 className="text-xl font-semibold tracking-tight text-ink-950">{item.title}</h3>
                <div className="mt-2 max-w-[62ch] text-base/7 text-ink-700">{item.body}</div>
                {item.meta && <p className="mt-3 font-mono text-xs uppercase tracking-widest text-ink-500">{item.meta}</p>}
              </div>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}
