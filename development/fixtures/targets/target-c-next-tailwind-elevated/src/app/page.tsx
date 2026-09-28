import Link from "next/link";
import { Zap, Shield, BarChart } from "lucide-react";
import { HeroAsymmetricSplit } from "@/components/recipes/sections/hero-asymmetric-split";
import { LogoMarquee } from "@/components/recipes/sections/logo-marquee";
import { BentoFeatures } from "@/components/recipes/sections/bento-features";
import { PricingEmphasis } from "@/components/recipes/sections/pricing-emphasis";
import { TestimonialSpotlight } from "@/components/recipes/sections/testimonial-spotlight";
import { FaqSplit } from "@/components/recipes/sections/faq-split";
import { CtaBand } from "@/components/recipes/sections/cta-band";
import { HeroEntrance } from "@/components/recipes/motion/hero-entrance";
import { GrainTexture } from "@/components/recipes/surfaces/grain-texture";
import { ProductShot } from "@/components/product-shot";

const plans = [
  { name: "Starter", price: "$0", cadence: "forever", cta: { label: "Start free", href: "/signup" } },
  { name: "Pro", price: "$29", cadence: "/mo", cta: { label: "Upgrade", href: "/signup?plan=pro" }, recommended: true },
  { name: "Team", price: "$99", cadence: "/mo", cta: { label: "Contact sales", href: "/contact" } },
];

const faqs = [
  { q: "Is there a free plan?", a: "Yes, Starter is free forever." },
  { q: "Can I cancel anytime?", a: "Yes, from your billing settings." },
];

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col">
      <div className="relative isolate">
        <GrainTexture pattern="dots" />
        <HeroEntrance>
          <HeroAsymmetricSplit
            eyebrow="New: AI workflows"
            title="Unlock the power of seamless automation"
            lead="Flowbase connects your tools so your team ships faster."
            primary={{ label: "Start free trial", href: "/signup" }}
            secondary={{ label: "Book a demo", href: "/demo" }}
            proof={["10k+ teams", "99.9% uptime", "24/7 support"]}
            media={<ProductShot />}
            LinkComponent={Link}
          />
        </HeroEntrance>
      </div>
      <LogoMarquee
        label="Trusted by fast-growing teams"
        logos={[{ name: "Acme" }, { name: "Globex" }, { name: "Initech" }, { name: "Umbrella" }, { name: "Hooli" }]}
      />
      <BentoFeatures
        title="Everything you need"
        intro="Supercharge your workflow with powerful features."
        features={[
          { title: "Fast", body: "Automations run in milliseconds.", icon: <Zap className="size-4" />, visual: <ProductShot /> },
          { title: "Secure", body: "SOC 2 compliant by default.", icon: <Shield className="size-4" /> },
          { title: "Insightful", body: "See every run in one dashboard.", icon: <BarChart className="size-4" /> },
        ]}
      />
      <PricingEmphasis title="Simple, transparent pricing" plans={plans} />
      <TestimonialSpotlight
        title="Loved by teams"
        quotes={[
          { text: "Flowbase saved us hours every week.", name: "Ana" },
          { text: "The best automation tool we've used.", name: "Ben" },
          { text: "Setup took five minutes.", name: "Chi" },
        ]}
      />
      <FaqSplit title="Frequently asked questions" items={faqs} />
      <CtaBand title="Ready to get started?" primary={{ label: "Start free trial", href: "/signup" }} />
    </main>
  );
}
