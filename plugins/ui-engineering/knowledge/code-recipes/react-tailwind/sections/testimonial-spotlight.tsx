/**
 * @recipe testimonial-spotlight
 *
 * Replaces three equal quote cards with one spotlight quote (large, with the person and an optional metric) and the
 * remaining quotes as a quiet list. Every existing quote and name is kept; pick the spotlight by specificity.
 *
 * Usage:
 *   <TestimonialSpotlight
 *     title="Loved by teams"
 *     quotes={[
 *       { text: "Flowbase saved us hours every week.", name: "Ana", role: "Ops lead, Acme", metric: "−6 h/week" },
 *       { text: "The best automation tool we've used.", name: "Ben" },
 *       { text: "Setup took five minutes.", name: "Chi" },
 *     ]}
 *   />
 */
import type { ReactNode } from "react";

export type Quote = { text: string; name: string; role?: string; avatar?: ReactNode; metric?: string };
export type TestimonialSpotlightProps = { id?: string; title: string; quotes: Quote[]; spotlightIndex?: number };

export function TestimonialSpotlight({ id = "testimonials", title, quotes, spotlightIndex = 0 }: TestimonialSpotlightProps) {
  const spotlight = quotes[spotlightIndex];
  const rest = quotes.filter((_, index) => index !== spotlightIndex);
  if (!spotlight) return null;
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="mx-auto w-full max-w-7xl px-6 py-24 lg:py-36">
      <h2 id={`${id}-title`} className="font-mono text-xs uppercase tracking-[0.18em] text-brand-700">{title}</h2>
      <div className="mt-8 grid gap-12 lg:grid-cols-12">
        <figure className="lg:col-span-8">
          <blockquote className="font-display text-3xl font-medium leading-tight tracking-tight text-ink-950 sm:text-4xl">
            <p>“{spotlight.text}”</p>
          </blockquote>
          <figcaption className="mt-8 flex items-center gap-4">
            {spotlight.avatar && <span className="size-11 overflow-hidden rounded-full bg-ink-100">{spotlight.avatar}</span>}
            <span>
              <span className="block font-semibold text-ink-950">{spotlight.name}</span>
              {spotlight.role && <span className="block text-sm text-ink-600">{spotlight.role}</span>}
            </span>
            {spotlight.metric && (
              <span className="ml-auto font-mono text-2xl tabular-nums text-brand-700">{spotlight.metric}</span>
            )}
          </figcaption>
        </figure>
        {rest.length > 0 && (
          <ul className="divide-y divide-ink-200 border-t border-ink-200 lg:col-span-4 lg:border-l lg:border-t-0 lg:pl-8">
            {rest.map((quote) => (
              <li key={quote.name + quote.text} className="py-5 first:pt-0 lg:first:pt-2">
                <figure>
                  <blockquote className="text-base/7 text-ink-800"><p>“{quote.text}”</p></blockquote>
                  <figcaption className="mt-2 text-sm text-ink-600">
                    {quote.name}{quote.role ? `, ${quote.role}` : ""}
                  </figcaption>
                </figure>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
