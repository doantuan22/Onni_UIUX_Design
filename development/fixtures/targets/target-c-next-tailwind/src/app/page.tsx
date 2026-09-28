import { Hero } from "@/components/hero";
import { LogoCloud } from "@/components/logo-cloud";
import { Features } from "@/components/features";
import { Pricing } from "@/components/pricing";
import { Testimonials } from "@/components/testimonials";
import { Faq } from "@/components/faq";
import { Cta } from "@/components/cta";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col">
      <Hero />
      <LogoCloud />
      <Features />
      <Pricing />
      <Testimonials />
      <Faq />
      <Cta />
    </main>
  );
}
