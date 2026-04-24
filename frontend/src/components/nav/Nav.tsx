"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { Button } from "~/components/ui/Button";

const links = [
  { href: "/",       label: "Home" },
  { href: "/models", label: "Models" },
  { href: "/docs",   label: "Docs" },
];

export function Nav() {
  const pathname = usePathname();
  const [light, setLight] = useState(false);

  useEffect(() => {
    document.documentElement.dataset.theme = light ? "light" : "";
  }, [light]);

  return (
    <nav
      className="sticky top-0 z-50 flex items-center justify-between px-14 py-[1.4rem] backdrop-blur-[14px]"
      style={{ background: "var(--color-nav)" }}
    >
      {/* Logo */}
      <Link href="/" className="text-[1rem] font-extrabold text-[var(--color-surface)] tracking-[-0.01em] no-underline">
        hexallabs
      </Link>

      {/* Pill — absolutely centered */}
      <div className="absolute left-1/2 -translate-x-1/2 flex items-center gap-[0.2rem] bg-white rounded-pill p-[0.28rem]">
        {links.map(({ href, label }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={[
                "inline-flex items-center px-4 py-[0.38rem] rounded-pill text-[0.8rem] font-semibold no-underline transition-colors duration-180",
                active
                  ? "bg-[var(--color-accent)] text-white"
                  : "text-[#7a6a62] hover:text-[var(--color-bg)]",
              ].join(" ")}
            >
              {label}
            </Link>
          );
        })}
      </div>

      {/* Right side */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setLight(v => !v)}
          aria-label="Toggle light mode"
          className="w-8 h-8 flex items-center justify-center rounded-full text-[var(--color-muted)] hover:text-[var(--color-surface)] transition-colors duration-180"
        >
          {light ? (
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/>
            </svg>
          ) : (
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5"/>
              <line x1="12" y1="1" x2="12" y2="3"/>
              <line x1="12" y1="21" x2="12" y2="23"/>
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/>
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/>
              <line x1="1" y1="12" x2="3" y2="12"/>
              <line x1="21" y1="12" x2="23" y2="12"/>
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/>
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/>
            </svg>
          )}
        </button>
        <Button variant="primary" size="sm">Get started</Button>
      </div>
    </nav>
  );
}
