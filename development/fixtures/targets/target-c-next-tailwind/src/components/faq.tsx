const faqs = [
  { q: "Is there a free plan?", a: "Yes, Starter is free forever." },
  { q: "Can I cancel anytime?", a: "Yes, from your billing settings." },
];

export function Faq() {
  return (
    <section id="faq" className="py-24 text-center">
      <h2 className="text-3xl font-bold">Frequently asked questions</h2>
      <div className="mx-auto mt-8 max-w-3xl text-left">
        {faqs.map((f) => (
          <details key={f.q} className="border-b py-4">
            <summary className="font-medium">{f.q}</summary>
            <p className="mt-2 text-gray-600">{f.a}</p>
          </details>
        ))}
      </div>
    </section>
  );
}
