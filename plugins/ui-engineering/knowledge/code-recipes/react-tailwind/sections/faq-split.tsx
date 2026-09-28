/**
 * @recipe faq-split
 *
 * Replaces a centered heading over a centered accordion with a two-column FAQ: a sticky heading and support link on
 * the left, native <details> disclosures on the right (keyboard and screen-reader friendly without JavaScript). The
 * open/close marker rotates with a CSS transition that respects reduced motion.
 *
 * Usage:
 *   <FaqSplit title="Frequently asked questions" items={[{ q: "Is there a free plan?", a: "Yes, Starter is free forever." }]}
 *     support={{ label: "Contact support", href: "/support" }} />
 */
import type { ReactNode } from "react";

export type FaqItem = { q: string; a: ReactNode };
export type FaqSplitProps = { id?: string; title: string; items: FaqItem[]; support?: { label: string; href: string } };

export function FaqSplit({ id = "faq", title, items, support }: FaqSplitProps) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="mx-auto w-full max-w-7xl px-6 py-16 lg:py-20">
      <div className="grid gap-x-16 gap-y-10 lg:grid-cols-12">
        <div className="lg:sticky lg:top-24 lg:col-span-4 lg:self-start">
          <h2 id={`${id}-title`} className="font-display text-3xl font-semibold tracking-tight text-ink-950 sm:text-4xl">{title}</h2>
          {support && (
            <a href={support.href} className="mt-6 inline-block text-sm font-semibold text-brand-700 underline underline-offset-4">
              {support.label}
            </a>
          )}
        </div>
        <div className="divide-y divide-ink-200 border-y border-ink-200 lg:col-span-8">
          {items.map((item) => (
            <details key={item.q} className="group py-5">
              <summary className="flex cursor-pointer list-none items-start justify-between gap-6 text-left text-lg font-medium text-ink-950 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-brand-600 [&::-webkit-details-marker]:hidden">
                {item.q}
                <span aria-hidden="true" className="mt-1 text-ink-500 transition-transform duration-200 group-open:rotate-45 motion-reduce:transition-none">+</span>
              </summary>
              <div className="mt-3 max-w-[64ch] text-base/7 text-ink-700">{item.a}</div>
            </details>
          ))}
        </div>
      </div>
    </section>
  );
}
