/**
 * @recipe cta-band
 *
 * Replaces a centered "Ready to get started?" block with a full-bleed band in the darkest brand step: left-aligned
 * heading, one primary action (the page's single accent moment) and an optional secondary link. It also works as the
 * full-bleed break that separates long pages into chapters.
 *
 * Usage:
 *   <CtaBand title="Ready to get started?" primary={{ label: "Start free trial", href: "/signup" }} />
 */
export type CtaBandProps = {
  title: string;
  body?: string;
  primary: { label: string; href: string };
  secondary?: { label: string; href: string };
};

export function CtaBand({ title, body, primary, secondary }: CtaBandProps) {
  return (
    <section className="relative overflow-hidden bg-brand-950 text-brand-50">
      <div className="mx-auto grid max-w-7xl gap-8 px-6 py-16 lg:grid-cols-12 lg:items-end lg:py-24">
        <div className="lg:col-span-8">
          <h2 className="max-w-[20ch] font-display text-4xl font-semibold leading-tight tracking-tight text-white sm:text-5xl">{title}</h2>
          {body && <p className="mt-4 max-w-[52ch] text-lg/8 text-brand-100">{body}</p>}
        </div>
        <div className="flex flex-wrap items-center gap-6 lg:col-span-4 lg:justify-end">
          <a
            href={primary.href}
            className="inline-flex items-center rounded-[var(--radius-control)] bg-white px-5 py-3 text-sm font-semibold text-brand-950 transition-colors hover:bg-brand-100 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
          >
            {primary.label}
          </a>
          {secondary && (
            <a href={secondary.href} className="text-sm font-semibold text-brand-100 underline underline-offset-4 hover:text-white">
              {secondary.label}
            </a>
          )}
        </div>
      </div>
    </section>
  );
}
