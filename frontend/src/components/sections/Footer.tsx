import Link from "next/link";

const links = ["About", "Models", "Docs"];

export function Footer() {
  return (
    <footer className="px-14 py-6 border-t border-[rgba(168,144,128,0.12)] flex items-center justify-between">
      <div className="text-[0.82rem] font-extrabold text-[var(--color-muted)]">
        hexallabs
      </div>
      <nav className="flex gap-6">
        {links.map((l) => (
          <Link
            key={l}
            href={`/${l.toLowerCase()}`}
            className="text-[0.72rem] font-semibold text-[var(--color-muted)] opacity-60 hover:opacity-100 transition-opacity no-underline"
          >
            {l}
          </Link>
        ))}
      </nav>
      <div className="text-[0.68rem] font-medium text-[var(--color-muted)] opacity-45">
        © 2026 HexalLabs
      </div>
    </footer>
  );
}
