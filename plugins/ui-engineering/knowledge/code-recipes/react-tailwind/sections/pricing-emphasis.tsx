/**
 * @recipe pricing-emphasis
 *
 * Replaces three identical pricing cards with a comparison that has a point of view: plans share one hairline frame,
 * the recommended plan is raised and carries the single brand accent, prices use tabular figures, and features are
 * listed so plans can be compared line by line. Keeps every plan, price, feature and action from the current page.
 *
 * Usage:
 *   <PricingEmphasis
 *     title="Simple, transparent pricing"
 *     plans={[
 *       { name: "Starter", price: "$0", cadence: "forever", cta: { label: "Start free", href: "/signup" }, features: ["1 workspace"] },
 *       { name: "Pro", price: "$29", cadence: "/mo", cta: { label: "Upgrade", href: "/signup?plan=pro" }, features: ["Unlimited runs"], recommended: true },
 *       { name: "Team", price: "$99", cadence: "/mo", cta: { label: "Contact sales", href: "/contact" }, features: ["SSO"] },
 *     ]}
 *   />
 */
export type Plan = {
  name: string;
  price: string;
  cadence?: string;
  description?: string;
  features?: string[];
  cta: { label: string; href: string };
  recommended?: boolean;
};

export type PricingEmphasisProps = { id?: string; title: string; intro?: string; plans: Plan[] };

export function PricingEmphasis({ id = "pricing", title, intro, plans }: PricingEmphasisProps) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="mx-auto w-full max-w-7xl px-6 py-16 lg:py-24">
      <div className="max-w-2xl">
        <h2 id={`${id}-title`} className="font-display text-3xl font-semibold tracking-tight text-ink-950 sm:text-4xl">{title}</h2>
        {intro && <p className="mt-4 text-lg/8 text-ink-700">{intro}</p>}
      </div>
      <ul className="mt-12 grid gap-px overflow-visible rounded-[var(--radius-panel)] border border-ink-200 bg-ink-200 lg:grid-cols-3">
        {plans.map((plan) => (
          <li
            key={plan.name}
            className={
              plan.recommended
                ? "relative z-10 flex flex-col bg-white p-8 shadow-[var(--shadow-raised)] ring-2 ring-brand-600 lg:-my-4 lg:rounded-[var(--radius-panel)] lg:py-12"
                : "flex flex-col bg-white p-8"
            }
          >
            <div className="flex items-baseline justify-between gap-4">
              <h3 className="text-lg font-semibold text-ink-950">{plan.name}</h3>
              {plan.recommended && (
                <span className="font-mono text-xs uppercase tracking-[0.18em] text-brand-700">Recommended</span>
              )}
            </div>
            <p className="mt-6 flex items-baseline gap-1">
              <span className="font-display text-5xl font-semibold tracking-tight tabular-nums text-ink-950">{plan.price}</span>
              {plan.cadence && <span className="text-sm text-ink-600">{plan.cadence}</span>}
            </p>
            {plan.description && <p className="mt-3 text-sm/6 text-ink-700">{plan.description}</p>}
            {plan.features && plan.features.length > 0 && (
              <ul className="mt-8 space-y-3 border-t border-ink-200 pt-6 text-sm text-ink-700">
                {plan.features.map((feature) => (
                  <li key={feature} className="flex gap-3">
                    <span aria-hidden="true" className="mt-2 size-1.5 shrink-0 rounded-full bg-brand-600" />
                    {feature}
                  </li>
                ))}
              </ul>
            )}
            <div className="mt-auto pt-10">
              <a
                href={plan.cta.href}
                className={
                  plan.recommended
                    ? "inline-flex w-full justify-center rounded-[var(--radius-control)] bg-brand-600 px-4 py-3 text-sm font-semibold text-white hover:bg-brand-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
                    : "inline-flex w-full justify-center rounded-[var(--radius-control)] border border-ink-300 px-4 py-3 text-sm font-semibold text-ink-900 hover:border-ink-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-ink-900"
                }
              >
                {plan.cta.label}
              </a>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}
