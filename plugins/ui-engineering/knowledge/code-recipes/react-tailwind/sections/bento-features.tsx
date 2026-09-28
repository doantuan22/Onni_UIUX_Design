/**
 * @recipe bento-features
 *
 * Replaces a 3-column grid of identical icon cards with a bento grid whose spans follow importance: one lead tile
 * (can hold a product visual), two mid tiles, the rest small. Hairline surfaces instead of rounded-2xl + shadow-lg on
 * every card; the icon sits inline with the title instead of floating in a tinted circle.
 *
 * Order `features` by importance before passing them; weight defaults to the position (first = lead).
 *
 * Usage:
 *   <BentoFeatures
 *     title="Everything you need"
 *     intro="Automations, security and insight in one place."
 *     features={[
 *       { title: "Fast", body: "Automations run in milliseconds.", icon: <Zap className="size-4" />, visual: <RunChart /> },
 *       { title: "Secure", body: "SOC 2 compliant by default.", icon: <Shield className="size-4" /> },
 *       { title: "Insightful", body: "See every run in one dashboard.", icon: <BarChart className="size-4" /> },
 *     ]}
 *   />
 */
import type { ReactNode } from "react";

export type BentoFeature = {
  title: string;
  body: string;
  icon?: ReactNode;
  /** Optional product visual; shown in the lead tile only. */
  visual?: ReactNode;
  weight?: "lead" | "mid" | "small";
};

export type BentoFeaturesProps = { id?: string; title: string; intro?: string; features: BentoFeature[] };

const SPAN: Record<NonNullable<BentoFeature["weight"]>, string> = {
  lead: "md:col-span-6 lg:col-span-4 lg:row-span-2",
  mid: "md:col-span-3 lg:col-span-2",
  small: "md:col-span-3 lg:col-span-2",
};

function weightOf(feature: BentoFeature, index: number): NonNullable<BentoFeature["weight"]> {
  return feature.weight ?? (index === 0 ? "lead" : index <= 2 ? "mid" : "small");
}

export function BentoFeatures({ id = "features", title, intro, features }: BentoFeaturesProps) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="mx-auto w-full max-w-7xl px-6 py-20 lg:py-28">
      <div className="grid gap-6 lg:grid-cols-12">
        <h2 id={`${id}-title`} className="font-display text-3xl font-semibold tracking-tight text-ink-950 sm:text-4xl lg:col-span-5">
          {title}
        </h2>
        {intro && <p className="max-w-[56ch] text-lg/8 text-ink-700 lg:col-span-6 lg:col-start-7 lg:self-end">{intro}</p>}
      </div>
      <ul className="mt-12 grid auto-rows-[minmax(11rem,auto)] gap-px overflow-hidden rounded-[var(--radius-panel)] border border-ink-200 bg-ink-200 md:grid-cols-6">
        {features.map((feature, index) => {
          const weight = weightOf(feature, index);
          return (
            <li key={feature.title} className={`flex flex-col bg-white p-6 lg:p-8 ${SPAN[weight]}`}>
              <h3 className="flex items-center gap-2 text-base font-semibold text-ink-950">
                {feature.icon && <span aria-hidden="true" className="text-brand-600">{feature.icon}</span>}
                {feature.title}
              </h3>
              <p className={`mt-2 text-ink-600 ${weight === "lead" ? "max-w-[44ch] text-lg/8" : "text-sm/6"}`}>{feature.body}</p>
              {weight === "lead" && feature.visual && (
                <div className="mt-8 flex-1 overflow-hidden rounded-[var(--radius-card)] border border-ink-200 bg-ink-50">
                  {feature.visual}
                </div>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
