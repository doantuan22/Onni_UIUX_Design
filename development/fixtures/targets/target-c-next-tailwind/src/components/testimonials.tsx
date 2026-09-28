const quotes = [
  { name: "Ana", text: "Flowbase saved us hours every week." },
  { name: "Ben", text: "The best automation tool we've used." },
  { name: "Chi", text: "Setup took five minutes." },
];

export function Testimonials() {
  return (
    <section className="py-24 text-center">
      <h2 className="text-3xl font-bold">Loved by teams</h2>
      <div className="mx-auto mt-12 grid max-w-6xl gap-6 md:grid-cols-3">
        {quotes.map((q) => (
          <figure key={q.name} className="rounded-2xl border p-6 shadow-lg">
            <blockquote>“{q.text}”</blockquote>
            <figcaption className="mt-4 font-semibold">{q.name}</figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}
