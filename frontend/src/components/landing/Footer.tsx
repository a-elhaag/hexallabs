import Link from "next/link";
import { Hex } from "./Hex";

export function Footer() {
  return (
    <footer className="relative mt-24 overflow-hidden border-t border-soft">
      <div className="relative mx-auto max-w-5xl px-5 py-20 text-center sm:px-8 sm:py-28">
        <div className="mx-auto mb-8 flex justify-center">
          <Hex size={72} variant="solid" glow ariaHidden />
        </div>
        <h2 className="text-balance text-3xl font-semibold tracking-tight text-ink sm:text-5xl">
          Ready to ask a council?
        </h2>
        <p className="mx-auto mt-5 max-w-xl text-balance text-base text-soft sm:text-lg">
          Stop settling for one model&rsquo;s best guess. Get seven minds on
          every question.
        </p>
        <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
          <Link
            href="/signup"
            className="inline-flex items-center justify-center rounded-full bg-[color:var(--color-accent)] px-7 py-3.5 text-base font-semibold text-[color:var(--color-surface)] shadow-[0_20px_40px_-16px_rgba(98,144,195,0.7)] transition-transform duration-300 hover:scale-[1.03] active:scale-[0.97]"
            style={{ transitionTimingFunction: "var(--ease-hexal)" }}
          >
            Try the Council
          </Link>
          <Link
            href="#how"
            className="text-sm font-medium text-soft underline-offset-4 transition-colors duration-300 hover:text-ink hover:underline"
          >
            See how it works
          </Link>
        </div>
      </div>

      <div className="border-t border-soft">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-5 py-6 text-xs text-soft sm:flex-row sm:px-8">
          <span className="font-mono tracking-[0.18em] uppercase">
            Hexal © {new Date().getUTCFullYear()}
          </span>
          <div className="flex items-center gap-5">
            <Link
              href="/about"
              className="transition-colors hover:text-ink"
            >
              About
            </Link>
            <Link
              href="/privacy"
              className="transition-colors hover:text-ink"
            >
              Privacy
            </Link>
            <Link
              href="/terms"
              className="transition-colors hover:text-ink"
            >
              Terms
            </Link>
          </div>
        </div>
      </div>
    </footer>
  );
}

export default Footer;
