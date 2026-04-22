import Link from "next/link";

export const metadata = { title: "Sign up — Hexal" };

export default function SignupPage() {
  return (
    <main className="flex min-h-screen items-center justify-center px-6">
      <div className="w-full max-w-md rounded-3xl border border-white/5 bg-[color:var(--color-surface)]/5 p-10 text-center">
        <p className="font-mono text-xs tracking-[0.28em] uppercase text-[color:var(--color-accent)]">
          Sign up
        </p>
        <h1 className="mt-4 text-3xl font-semibold tracking-tight">
          Join the council.
        </h1>
        <p className="mt-4 text-[color:var(--color-muted)]">
          Sign-up is on the build list. This page is a stub.
        </p>
        <Link
          href="/"
          className="mt-8 inline-flex items-center justify-center rounded-full border border-[color:var(--color-muted)]/30 px-5 py-2 text-sm font-medium text-[color:var(--color-surface)]/85 transition-colors hover:text-[color:var(--color-surface)]"
        >
          ← Home
        </Link>
      </div>
    </main>
  );
}
