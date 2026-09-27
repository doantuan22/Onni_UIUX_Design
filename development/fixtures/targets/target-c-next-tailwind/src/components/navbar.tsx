import Link from "next/link";

const links = [{ href: "/#features", label: "Features" }, { href: "/pricing", label: "Pricing" }];

export default function Navbar() {
  return (
    <header className="sticky top-0 z-50 backdrop-blur bg-white/70 border-b">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4" aria-label="Main">
        <Link href="/" className="font-bold">Flowbase</Link>
        <ul className="flex gap-6">
          {links.map((l) => (
            <li key={l.href}><Link href={l.href}>{l.label}</Link></li>
          ))}
        </ul>
        <Link href="/signup" className="rounded-full bg-indigo-600 px-4 py-2 text-white">Get started</Link>
      </nav>
    </header>
  );
}
