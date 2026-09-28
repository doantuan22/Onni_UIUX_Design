"use client";
/**
 * @recipe pinned-steps-gsap
 *
 * Pinned walkthrough: the section pins while 3–5 steps advance with the scroll, the active step's media cross-fades.
 * GSAP ScrollTrigger inside gsap.matchMedia so it only runs on large screens without reduced motion; everywhere else
 * the steps stay a normal stacked list (fully readable and keyboard scrollable). Cleans up on unmount.
 *
 * Requires: gsap (ScrollTrigger ships with gsap). Choose this over Motion only for pinned/scrubbed timelines.
 * Next.js: client component.
 *
 * Usage:
 *   <PinnedStepsGsap title="How it works" steps={[{ title: "Connect", body: "…", media: <img … /> }, …]} />
 */
import { useLayoutEffect, useRef, type ReactNode } from "react";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

export type PinnedStep = { title: string; body: ReactNode; media: ReactNode };

export function PinnedStepsGsap({ title, steps }: { title: string; steps: PinnedStep[] }) {
  const root = useRef<HTMLElement>(null);

  useLayoutEffect(() => {
    const el = root.current;
    if (!el) return;
    const mm = gsap.matchMedia();
    mm.add("(min-width: 1024px) and (prefers-reduced-motion: no-preference)", () => {
      const texts = gsap.utils.toArray<HTMLElement>("[data-step]", el);
      const medias = gsap.utils.toArray<HTMLElement>("[data-media]", el);
      gsap.set(medias.slice(1), { autoAlpha: 0 });
      gsap.set(texts.slice(1), { autoAlpha: 0.35 });
      const tl = gsap.timeline({
        defaults: { ease: "power2.inOut", duration: 1 },
        scrollTrigger: { trigger: el, pin: true, scrub: 0.6, start: "top top", end: () => `+=${steps.length * 70}%` },
      });
      for (let i = 1; i < steps.length; i += 1) {
        tl.to(medias[i - 1], { autoAlpha: 0 }, i)
          .to(medias[i], { autoAlpha: 1 }, i)
          .to(texts[i - 1], { autoAlpha: 0.35 }, i)
          .to(texts[i], { autoAlpha: 1 }, i);
      }
    });
    return () => mm.revert();
  }, [steps.length]);

  return (
    <section ref={root} aria-label={title} className="bg-ink-50 lg:h-screen">
      <div className="mx-auto grid h-full max-w-7xl gap-12 px-6 py-20 lg:grid-cols-12 lg:items-center lg:py-0">
        <div className="lg:col-span-5">
          <h2 className="font-display text-3xl font-semibold tracking-tight text-ink-950 sm:text-4xl">{title}</h2>
          <ol className="mt-8 space-y-6">
            {steps.map((step, index) => (
              <li key={step.title} data-step className="border-l-2 border-ink-200 pl-5">
                <p className="font-mono text-xs uppercase tracking-[0.18em] text-brand-700">{String(index + 1).padStart(2, "0")}</p>
                <h3 className="mt-1 text-lg font-semibold text-ink-950">{step.title}</h3>
                <div className="mt-1 text-base/7 text-ink-700">{step.body}</div>
                <div className="mt-4 overflow-hidden rounded-[var(--radius-card)] border border-ink-200 lg:hidden">{step.media}</div>
              </li>
            ))}
          </ol>
        </div>
        <div className="relative hidden aspect-[4/3] lg:col-span-7 lg:block">
          {steps.map((step) => (
            <div key={step.title} data-media className="absolute inset-0 overflow-hidden rounded-[var(--radius-panel)] border border-ink-200 bg-white shadow-[var(--shadow-raised)]">
              {step.media}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
