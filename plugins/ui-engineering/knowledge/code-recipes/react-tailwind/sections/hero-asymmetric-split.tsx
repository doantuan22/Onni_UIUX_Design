/**
 * @recipe hero-asymmetric-split
 *
 * Replaces the centered badge + gradient headline + twin buttons hero with a 7/5 split: text anchored left, a real
 * product visual bleeding off the right edge, proof inline under the actions. Content comes in through props so the
 * existing copy, links and media are kept verbatim (Elevate invariant).
 *
 * Usage (Next.js):
 *   <HeroAsymmetricSplit
 *     eyebrow="New: AI workflows"
 *     title="Unlock the power of seamless automation"
 *     lead="Flowbase connects your tools so your team ships faster."
 *     primary={{ label: "Start free trial", href: "/signup" }}
 *     secondary={{ label: "Book a demo", href: "/demo" }}
 *     proof={["10k+ teams", "99.9% uptime", "24/7 support"]}
 *     media={<Image src="/product.png" alt="Flowbase run history" width={1440} height={960} priority />}
 *   />
 */
import type { ReactNode } from "react";

type Action = { label: string; href: string };

export type HeroAsymmetricSplitProps = {
  eyebrow?: string;
  title: string;
  lead?: string;
  primary: Action;
  secondary?: Action;
  proof?: string[];
  media: ReactNode;
  /** Render links with the router's component (next/link, react-router Link). Defaults to <a>. */
  LinkComponent?: (props: { href: string; className?: string; children: ReactNode }) => ReactNode;
};

const DefaultLink = ({ href, className, children }: { href: string; className?: string; children: ReactNode }) => (
  <a href={href} className={className}>{children}</a>
);

export function HeroAsymmetricSplit({
  eyebrow, title, lead, primary, secondary, proof = [], media, LinkComponent = DefaultLink,
}: HeroAsymmetricSplitProps) {
  return (
    <section className="relative overflow-hidden border-b border-ink-200 bg-ink-50">
      <div className="mx-auto grid max-w-7xl gap-y-12 px-6 pb-16 pt-20 lg:grid-cols-12 lg:gap-x-10 lg:pb-24 lg:pt-28">
        <div className="lg:col-span-7 lg:self-center">
          {eyebrow && (
            <p className="font-mono text-xs uppercase tracking-[0.18em] text-brand-700">{eyebrow}</p>
          )}
          <h1 className="mt-5 max-w-[16ch] font-display text-5xl font-semibold leading-[0.95] tracking-tight text-ink-950 sm:text-6xl lg:text-7xl">
            {title}
          </h1>
          {lead && <p className="mt-6 max-w-[52ch] text-lg/8 text-ink-700">{lead}</p>}
          <div className="mt-9 flex flex-wrap items-center gap-x-6 gap-y-4">
            <LinkComponent
              href={primary.href}
              className="group inline-flex items-center gap-2 rounded-[var(--radius-control)] bg-brand-600 px-5 py-3 text-sm font-semibold text-white transition-colors duration-150 hover:bg-brand-700 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
            >
              {primary.label}
              <span aria-hidden="true" className="transition-transform duration-150 group-hover:translate-x-0.5 motion-reduce:transition-none">→</span>
            </LinkComponent>
            {secondary && (
              <LinkComponent
                href={secondary.href}
                className="text-sm font-semibold text-ink-900 underline decoration-ink-300 underline-offset-4 hover:decoration-ink-900"
              >
                {secondary.label}
              </LinkComponent>
            )}
          </div>
          {proof.length > 0 && (
            <ul className="mt-12 flex flex-wrap gap-x-8 gap-y-2 border-t border-ink-200 pt-6 text-sm text-ink-600">
              {proof.map((item) => (
                <li key={item} className="font-mono tabular-nums">{item}</li>
              ))}
            </ul>
          )}
        </div>
        <div className="relative lg:col-span-5 lg:-mr-[max(1.5rem,calc((100vw-80rem)/2))]">
          <div className="overflow-hidden rounded-[var(--radius-panel)] border border-ink-200 bg-white shadow-[var(--shadow-raised)] lg:rounded-r-none">
            {media}
          </div>
        </div>
      </div>
    </section>
  );
}
