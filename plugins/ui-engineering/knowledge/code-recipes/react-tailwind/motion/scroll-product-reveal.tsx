"use client";
/**
 * @recipe scroll-product-reveal
 *
 * The key product visual tilts and scales into place as it enters the viewport, tied to scroll position (no timers).
 * Motion's useScroll/useTransform drive transform and opacity only (GPU-friendly). With reduced motion the visual is
 * static. For a dependency-free version use the CSS variant below the component (animation-timeline: view()).
 *
 * Requires: motion. Next.js: client component; pass next/image as children.
 *
 * Usage:
 *   <ScrollProductReveal><Image src="/product.png" alt="Run history" width={1600} height={1000} /></ScrollProductReveal>
 */
import { useRef, type ReactNode } from "react";
import { motion, useReducedMotion, useScroll, useTransform } from "motion/react";

export function ScrollProductReveal({ children, className }: { children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null);
  const reduce = useReducedMotion();
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "center center"] });
  const rotateX = useTransform(scrollYProgress, [0, 1], [18, 0]);
  const scale = useTransform(scrollYProgress, [0, 1], [0.9, 1]);
  const opacity = useTransform(scrollYProgress, [0, 0.4], [0.4, 1]);

  return (
    <div ref={ref} className={`[perspective:1200px] ${className ?? ""}`}>
      <motion.div
        style={reduce ? undefined : { rotateX, scale, opacity, transformOrigin: "50% 100%" }}
        className="overflow-hidden rounded-[var(--radius-panel)] border border-ink-200 bg-white shadow-[var(--shadow-overlay)]"
      >
        {children}
      </motion.div>
    </div>
  );
}

/**
 * Dependency-free variant: add `className="scroll-reveal"` to the frame and include this CSS once.
 *
 * @supports (animation-timeline: view()) {
 *   @media (prefers-reduced-motion: no-preference) {
 *     .scroll-reveal {
 *       animation: scroll-reveal linear both;
 *       animation-timeline: view();
 *       animation-range: entry 0% cover 45%;
 *       transform-origin: 50% 100%;
 *     }
 *   }
 * }
 * @keyframes scroll-reveal {
 *   from { opacity: 0.4; transform: perspective(1200px) rotateX(18deg) scale(0.9); }
 *   to { opacity: 1; transform: none; }
 * }
 */
