import { Zap, Shield, BarChart } from "lucide-react";
import { FeatureCard } from "./feature-card";

const features = [
  { icon: Zap, title: "Fast", body: "Automations run in milliseconds." },
  { icon: Shield, title: "Secure", body: "SOC 2 compliant by default." },
  { icon: BarChart, title: "Insightful", body: "See every run in one dashboard." },
];

export function Features() {
  return (
    <section id="features" className="py-24 text-center">
      <h2 className="text-3xl font-bold">Everything you need</h2>
      <p className="mt-2 text-gray-400">Supercharge your workflow with powerful features.</p>
      <div className="mx-auto mt-12 grid max-w-6xl gap-6 md:grid-cols-3">
        {features.map((f) => (
          <FeatureCard key={f.title} icon={<f.icon className="h-6 w-6" />} title={f.title} body={f.body} />
        ))}
      </div>
    </section>
  );
}
