const plans = [
  { name: "Starter", price: "$0", cta: "Start free" },
  { name: "Pro", price: "$29/mo", cta: "Upgrade" },
  { name: "Team", price: "$99/mo", cta: "Contact sales" },
];

export function Pricing() {
  return (
    <section id="pricing" className="py-24 text-center">
      <h2 className="text-3xl font-bold">Simple, transparent pricing</h2>
      <div className="mx-auto mt-12 grid max-w-5xl gap-6 md:grid-cols-3">
        {plans.map((p) => (
          <div key={p.name} className="rounded-2xl border p-8 shadow-lg">
            <h3 className="text-xl font-semibold">{p.name}</h3>
            <p className="mt-4 text-4xl font-bold">{p.price}</p>
            <button className="mt-6 w-full rounded-full bg-indigo-600 py-2 text-white">{p.cta}</button>
          </div>
        ))}
      </div>
    </section>
  );
}
