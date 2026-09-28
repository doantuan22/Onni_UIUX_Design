"use client";
/**
 * @recipe shared-layout-cards
 *
 * Shared-element transition: a card in a list expands into its detail panel (same element, animated position and size
 * via Motion layoutId). Keyboard: cards are buttons, Escape closes, focus returns to the opener. Reduced motion falls
 * back to an instant swap (MotionConfig reducedMotion="user").
 *
 * Requires: motion. Next.js: client component. For route-level transitions prefer the View Transitions API.
 *
 * Usage:
 *   <SharedLayoutCards items={[{ id: "a", title: "Invoices", summary: "…", detail: <InvoiceDetail /> }, …]} />
 */
import { useEffect, useRef, useState, type ReactNode } from "react";
import { AnimatePresence, MotionConfig, motion } from "motion/react";

export type LayoutCard = { id: string; title: string; summary: string; detail: ReactNode };

export function SharedLayoutCards({ items }: { items: LayoutCard[] }) {
  const [openId, setOpenId] = useState<string | null>(null);
  const openerRef = useRef<HTMLButtonElement | null>(null);
  const open = items.find((item) => item.id === openId) ?? null;

  useEffect(() => {
    if (!open) return;
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && setOpenId(null);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  useEffect(() => {
    if (!openId) openerRef.current?.focus();
  }, [openId]);

  return (
    <MotionConfig reducedMotion="user" transition={{ type: "spring", stiffness: 380, damping: 34 }}>
      <ul className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((item) => (
          <li key={item.id}>
            <motion.button
              layoutId={`card-${item.id}`}
              type="button"
              onClick={(event) => {
                openerRef.current = event.currentTarget;
                setOpenId(item.id);
              }}
              className="w-full rounded-[var(--radius-card)] border border-ink-200 bg-white p-5 text-left transition-colors hover:border-ink-400 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
            >
              <motion.h3 layoutId={`title-${item.id}`} className="font-semibold text-ink-950">{item.title}</motion.h3>
              <p className="mt-1 text-sm text-ink-600">{item.summary}</p>
            </motion.button>
          </li>
        ))}
      </ul>
      <AnimatePresence>
        {open && (
          <motion.div
            key="backdrop"
            className="fixed inset-0 z-40 bg-ink-950/40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setOpenId(null)}
          />
        )}
        {open && (
          <motion.div
            key={open.id}
            layoutId={`card-${open.id}`}
            role="dialog"
            aria-modal="true"
            aria-labelledby={`title-${open.id}`}
            className="fixed inset-x-4 top-[10vh] z-50 mx-auto max-w-2xl rounded-[var(--radius-panel)] border border-ink-200 bg-white p-8 shadow-[var(--shadow-overlay)]"
          >
            <motion.h3 id={`title-${open.id}`} layoutId={`title-${open.id}`} className="text-2xl font-semibold text-ink-950">
              {open.title}
            </motion.h3>
            <div className="mt-4 text-ink-700">{open.detail}</div>
            <button
              type="button"
              autoFocus
              onClick={() => setOpenId(null)}
              className="mt-8 text-sm font-semibold text-brand-700 underline underline-offset-4"
            >
              Close
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </MotionConfig>
  );
}
