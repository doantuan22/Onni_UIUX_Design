import Link from "next/link";

export function Hero() {
  return (
    <section className="relative overflow-hidden py-24 text-center">
      <div className="absolute -top-40 left-1/2 h-96 w-96 rounded-full bg-purple-500/30 blur-3xl" />
      <span className="rounded-full bg-indigo-50 px-3 py-1 text-sm">✨ New: AI workflows</span>
      <h1 className="mt-6 text-6xl font-bold bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 bg-clip-text text-transparent">
        Unlock the power of seamless automation
      </h1>
      <p className="mx-auto mt-4 max-w-2xl text-gray-400">Flowbase connects your tools so your team ships faster.</p>
      <div className="mt-8 flex justify-center gap-4">
        <Link href="/signup" className="rounded-full bg-gradient-to-r from-indigo-500 to-pink-500 px-6 py-3 text-white hover:scale-105 transition">Start free trial</Link>
        <Link href="/demo" className="rounded-full border px-6 py-3">Book a demo</Link>
      </div>
      <p className="mt-6 text-sm">10k+ teams · 99.9% uptime · 24/7 support</p>
    </section>
  );
}
