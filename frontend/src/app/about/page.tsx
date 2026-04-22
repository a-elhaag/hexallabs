import Link from "next/link";

export const metadata = { title: "About — Hexal" };

export default function AboutPage() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-24">
      <p className="font-mono text-xs tracking-[0.28em] uppercase text-[color:var(--color-accent)]">
        About
      </p>
      <h1 className="mt-4 text-balance text-4xl font-semibold tracking-tight sm:text-5xl">
        What&rsquo;s behind each hex.
      </h1>
      <p className="mt-6 text-lg text-[color:var(--color-muted)]">
        Hexal&rsquo;s white-label names stand in for real models under the
        hood. This page is where full model attribution lives.
      </p>
      <p className="mt-4 text-[color:var(--color-muted)]">
        Attribution details are coming. This page is a stub.
      </p>
      <Link
        href="/"
        className="mt-10 inline-flex items-center justify-center rounded-full border border-[color:var(--color-muted)]/30 px-5 py-2 text-sm font-medium text-[color:var(--color-surface)]/85 transition-colors hover:text-[color:var(--color-surface)]"
      >
        ← Home
      </Link>
    </main>
  );
}
