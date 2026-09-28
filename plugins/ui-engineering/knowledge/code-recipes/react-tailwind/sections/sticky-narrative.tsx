/**
 * @recipe sticky-narrative
 *
 * A sticky left column (title, intro, progress) while the steps scroll on the right. The progress bar uses CSS
 * scroll-driven animation (animation-timeline: view()) where supported and is simply full elsewhere; no JavaScript
 * and no dependency. Below `lg` it degrades to a normal stacked list.
 *
 * Usage:
 *   <StickyNarrative title="From idea to production" intro="Four steps, one workspace." steps={[...]} />
 */
import type { ReactNode } from "react";

export type NarrativeStep = { title: string; body: ReactNode; media?: ReactNode };
export type StickyNarrativeProps = { id?: string; title: string; intro?: string; steps: NarrativeStep[] };

export function StickyNarrative({ id = "workflow", title, intro, steps }: StickyNarrativeProps) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="border-y border-ink-200 bg-ink-50">
      <div className="mx-auto grid max-w-7xl gap-x-16 gap-y-10 px-6 py-20 lg:grid-cols-12 lg:py-28">
        <div className="lg:sticky lg:top-24 lg:col-span-4 lg:self-start">
          <h2 id={`${id}-title`} className="font-display text-3xl font-semibold tracking-tight text-ink-950 sm:text-4xl">
            {title}
          </h2>
          {intro && <p className="mt-4 max-w-[40ch] text-lg/8 text-ink-700">{intro}</p>}
          <div aria-hidden="true" className="mt-8 hidden h-1 w-40 overflow-hidden rounded-full bg-ink-200 lg:block">
            <div className="narrative-progress h-full origin-left bg-brand-600" />
          </div>
        </div>
        <ol className="space-y-6 lg:col-span-7 lg:col-start-6">
          {steps.map((step, index) => (
            <li key={step.title} className="rounded-[var(--radius-card)] border border-ink-200 bg-white p-6 lg:p-8">
              <p className="font-mono text-xs uppercase tracking-[0.18em] text-brand-700">Step {index + 1}</p>
              <h3 className="mt-2 text-xl font-semibold text-ink-950">{step.title}</h3>
              <div className="mt-2 text-base/7 text-ink-700">{step.body}</div>
              {step.media && <div className="mt-6 overflow-hidden rounded-[var(--radius-control)] border border-ink-200">{step.media}</div>}
            </li>
          ))}
        </ol>
      </div>
      <style>{`
        @supports (animation-timeline: view()) {
          @media (prefers-reduced-motion: no-preference) {
            #${id} .narrative-progress {
              animation: narrative-grow linear both;
              animation-timeline: view();
              animation-range: entry 20% exit 80%;
            }
          }
        }
        @keyframes narrative-grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
      `}</style>
    </section>
  );
}
