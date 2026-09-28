const logos = ["Acme", "Globex", "Initech", "Umbrella", "Hooli"];

export function LogoCloud() {
  return (
    <section className="py-24 text-center">
      <p className="text-sm text-gray-500">Trusted by fast-growing teams</p>
      <div className="mt-6 flex justify-center gap-10 grayscale opacity-50">
        {logos.map((name) => (
          <span key={name} className="text-xl font-semibold">{name}</span>
        ))}
      </div>
    </section>
  );
}
