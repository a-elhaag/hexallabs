"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Hex } from "./Hex";

export function Header() {
  const [scrolled, setScrolled] = useState(false);
  const raf = useRef<number | null>(null);

  useEffect(() => {
    const onScroll = () => {
      if (raf.current !== null) return;
      raf.current = requestAnimationFrame(() => {
        setScrolled(window.scrollY > 24);
        raf.current = null;
      });
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => {
      window.removeEventListener("scroll", onScroll);
      if (raf.current !== null) cancelAnimationFrame(raf.current);
    };
  }, []);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 transition-[background,backdrop-filter,border-color,box-shadow] duration-300 ${
        scrolled
          ? "border-b border-soft bg-[color:var(--bg-body)]/78 shadow-[0_1px_0_rgba(44,44,44,0.04)] backdrop-blur-md"
          : "border-b border-transparent bg-transparent"
      }`}
      style={{ transitionTimingFunction: "var(--ease-hexal)" }}
    >
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-5 py-3 sm:px-8 sm:py-4">
        <Link href="/" className="group flex items-center gap-2.5">
          <Hex
            size={28}
            variant="solid"
            ariaHidden
            className="transition-transform duration-300 group-hover:scale-110"
          />
          <span className="text-lg font-semibold tracking-tight text-ink sm:text-xl">
            Hexal
          </span>
        </Link>

        <div className="flex items-center gap-2 sm:gap-3">
          <Link
            href="/login"
            className="hidden rounded-full px-4 py-2 text-sm font-medium text-soft transition-colors duration-300 hover:text-ink sm:inline-flex"
          >
            Sign in
          </Link>
          <Link
            href="/signup"
            className="inline-flex items-center rounded-full bg-[color:var(--color-accent)] px-4 py-2 text-sm font-semibold text-[color:var(--color-surface)] shadow-[0_10px_24px_-12px_rgba(98,144,195,0.7)] transition-transform duration-300 hover:scale-[1.03] active:scale-[0.97] sm:px-5 sm:py-2.5"
            style={{ transitionTimingFunction: "var(--ease-hexal)" }}
          >
            Sign up
          </Link>
        </div>
      </nav>
    </header>
  );
}

export default Header;
