import { Pricing } from "@/components/pricing";
import { Faq } from "@/components/faq";

export default function PricingPage() {
  return (
    <main>
      <h1 className="text-4xl font-bold text-center">Pricing</h1>
      <p className="text-center text-gray-400">Simple plans for every team.</p>
      <Pricing />
      <Faq />
    </main>
  );
}
