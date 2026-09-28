/**
 * @recipe logo-marquee
 *
 * Replaces the grey, half-transparent "Trusted by" logo row with a slow, pausable marquee placed next to the claim it
 * supports. CSS-only: the list is duplicated for a seamless loop (the copy is aria-hidden), hovering or focusing pauses
 * it, and with reduced motion it becomes a static wrapped row. Use only with real customer logos.
 *
 * Usage:
 *   <LogoMarquee label="Trusted by fast-growing teams" logos={[{ name: "Acme", logo: <AcmeLogo /> }, ...]} />
 */
import type { ReactNode } from "react";

export type LogoItem = { name: string; logo?: ReactNode };
export type LogoMarqueeProps = { label: string; logos: LogoItem[]; durationSeconds?: number };

function Row({ logos, hidden = false }: { logos: LogoItem[]; hidden?: boolean }) {
  return (
    <ul aria-hidden={hidden || undefined} className="flex shrink-0 items-center gap-14 pr-14">
      {logos.map((item) => (
        <li key={item.name} className="text-lg font-semibold tracking-tight text-ink-700">
          {item.logo ?? item.name}
          {item.logo && <span className="sr-only">{item.name}</span>}
        </li>
      ))}
    </ul>
  );
}

export function LogoMarquee({ label, logos, durationSeconds = 40 }: LogoMarqueeProps) {
  return (
    <section aria-label={label} className="border-y border-ink-200 bg-white">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-10 lg:flex-row lg:items-center lg:gap-12">
        <p className="shrink-0 text-sm font-medium text-ink-700 lg:max-w-[14rem]">{label}</p>
        <div className="marquee group relative flex overflow-hidden [mask-image:linear-gradient(to_right,transparent,black_8%,black_92%,transparent)]">
          <div
            className="marquee-track flex group-hover:[animation-play-state:paused] group-focus-within:[animation-play-state:paused]"
            style={{ animationDuration: `${durationSeconds}s` }}
          >
            <Row logos={logos} />
            <Row logos={logos} hidden />
          </div>
        </div>
      </div>
      <style>{`
        .marquee-track { animation: marquee-scroll linear infinite; }
        @keyframes marquee-scroll { to { transform: translateX(-50%); } }
        @media (prefers-reduced-motion: reduce) {
          .marquee-track { animation: none; flex-wrap: wrap; }
          .marquee-track > ul { flex-wrap: wrap; row-gap: 1rem; padding-right: 0; }
          .marquee-track > ul[aria-hidden] { display: none; }
          .marquee { mask-image: none; }
        }
      `}</style>
    </section>
  );
}
