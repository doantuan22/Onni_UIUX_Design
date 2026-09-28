export function FeatureCard({ icon, title, body }: { icon: React.ReactNode; title: string; body: string }) {
  return (
    <div className="rounded-2xl border bg-white p-6 shadow-lg hover:scale-105 transition">
      <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-indigo-500/10">{icon}</div>
      <h3 className="mt-4 text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-gray-400">{body}</p>
    </div>
  );
}
