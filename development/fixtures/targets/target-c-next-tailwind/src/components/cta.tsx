import Link from "next/link";

export function Cta() {
  return (
    <section className="py-24 text-center">
      <h2 className="text-4xl font-bold">Ready to get started?</h2>
      <Link href="/signup" className="mt-6 inline-block rounded-full bg-indigo-600 px-6 py-3 text-white">Start free trial</Link>
    </section>
  );
}
