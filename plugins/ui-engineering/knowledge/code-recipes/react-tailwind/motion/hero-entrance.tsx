"use client";
/**
 * @recipe hero-entrance
 *
 * One choreographed entrance for the hero (eyebrow → headline → lead → actions → visual, 70 ms apart), played once.
 * Use it on the hero only; the rest of the page should not fade up. Motion (`motion`, formerly Framer Motion) with a
 * reduced-motion path: when the user prefers reduced motion the children render in place with a short opacity fade.
 *
 * Requires: motion (import from "motion/react"; with an existing framer-motion install use "framer-motion").
 * Next.js App Router: this file is a client component; keep the hero content itself in a server component and wrap it.
 *
 * Usage:
 *   <HeroEntrance>
 *     <p>eyebrow</p><h1>…</h1><p>lead</p><div>actions</div>
 *   </HeroEntrance>
 */
import { Children, type ReactNode } from "react";
import { motion, useReducedMotion, type Variants } from "motion/react";

const EASE_OUT_QUINT = [0.22, 1, 0.36, 1] as const;

export function HeroEntrance({ children, className }: { children: ReactNode; className?: string }) {
  const reduce = useReducedMotion();
  const container: Variants = {
    hidden: {},
    shown: { transition: { staggerChildren: reduce ? 0 : 0.07, delayChildren: reduce ? 0 : 0.05 } },
  };
  // Both variants end in the same resting state: `reduce` can flip after hydration, and a variant that omits
  // y/filter would leave the element stuck mid-transform (e.g. permanently blurred).
  const item: Variants = reduce
    ? {
        hidden: { opacity: 0, y: 0, filter: "blur(0px)" },
        shown: { opacity: 1, y: 0, filter: "blur(0px)", transition: { duration: 0.2 } },
      }
    : {
        hidden: { opacity: 0, y: 18, filter: "blur(4px)" },
        shown: { opacity: 1, y: 0, filter: "blur(0px)", transition: { duration: 0.6, ease: EASE_OUT_QUINT } },
      };
  return (
    <motion.div className={className} variants={container} initial="hidden" animate="shown">
      {Children.map(children, (child) => (
        <motion.div variants={item}>{child}</motion.div>
      ))}
    </motion.div>
  );
}
