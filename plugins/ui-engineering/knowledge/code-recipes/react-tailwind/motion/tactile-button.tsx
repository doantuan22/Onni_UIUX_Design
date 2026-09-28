/**
 * @recipe tactile-button
 *
 * Feedback instead of decoration: a press that compresses slightly, a hover that reveals affordance (arrow shift,
 * border/colour step) and a pending state that keeps the label width stable. Pure CSS (Tailwind utilities), so it
 * works in server components; replaces hover:scale-105 on cards and buttons.
 *
 * Usage:
 *   <TactileButton pending={isSubmitting} type="submit">Start free trial</TactileButton>
 */
import type { ButtonHTMLAttributes, ReactNode } from "react";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { pending?: boolean; children: ReactNode; variant?: "primary" | "quiet" };

const VARIANT = {
  primary: "bg-brand-600 text-white hover:bg-brand-700 focus-visible:outline-brand-600",
  quiet: "border border-ink-300 text-ink-900 hover:border-ink-900 focus-visible:outline-ink-900",
};

export function TactileButton({ pending = false, children, variant = "primary", className = "", ...rest }: Props) {
  return (
    <button
      {...rest}
      aria-busy={pending || undefined}
      disabled={pending || rest.disabled}
      className={`group relative inline-flex items-center justify-center gap-2 rounded-[var(--radius-control)] px-5 py-3 text-sm font-semibold transition-[background-color,border-color,transform] duration-150 ease-[var(--ease-out-quint)] active:scale-[0.97] disabled:cursor-not-allowed disabled:opacity-70 focus-visible:outline-2 focus-visible:outline-offset-2 motion-reduce:transition-none motion-reduce:active:scale-100 ${VARIANT[variant]} ${className}`}
    >
      <span className={pending ? "invisible" : undefined}>{children}</span>
      {!pending && (
        <span aria-hidden="true" className="transition-transform duration-150 group-hover:translate-x-0.5 motion-reduce:transition-none">→</span>
      )}
      {pending && (
        <span aria-hidden="true" className="absolute inset-0 grid place-items-center">
          <span className="size-4 animate-spin rounded-full border-2 border-current border-r-transparent motion-reduce:animate-none" />
        </span>
      )}
    </button>
  );
}
