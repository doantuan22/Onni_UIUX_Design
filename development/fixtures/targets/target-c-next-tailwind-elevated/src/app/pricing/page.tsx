import { PricingEmphasis } from "@/components/recipes/sections/pricing-emphasis";
import { FaqSplit } from "@/components/recipes/sections/faq-split";

const plans = [
  { name: "Starter", price: "$0", cadence: "forever", cta: { label: "Start free", href: "/signup" } },
  { name: "Pro", price: "$29", cadence: "/mo", cta: { label: "Upgrade", href: "/signup?plan=pro" }, recommended: true },
  { name: "Team", price: "$99", cadence: "/mo", cta: { label: "Contact sales", href: "/contact" } },
];

export default function PricingPage() {
  return (
    <main>
      <header className="mx-auto max-w-7xl px-6 pt-20">
        <h1 className="font-display text-5xl font-semibold tracking-tight text-ink-950">Pricing</h1>
        <p className="mt-4 max-w-[52ch] text-lg/8 text-ink-700">Simple plans for every team.</p>
      </header>
      <PricingEmphasis title="Simple, transparent pricing" plans={plans} />
      <FaqSplit
        title="Frequently asked questions"
        items={[
          { q: "Is there a free plan?", a: "Yes, Starter is free forever." },
          { q: "Can I cancel anytime?", a: "Yes, from your billing settings." },
        ]}
      />
    </main>
  );
}
