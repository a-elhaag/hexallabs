"use client";

import Link from "next/link";
import { type Mode, type Theme, MODES } from "~/components/chat/types";

interface Props {
  mode: Mode;
  theme: Theme;
  scoutOn: boolean;
  primalOn: boolean;
  sidebarOpen: boolean;
  userEmail?: string;
  onModeChange: (m: Mode) => void;
  onThemeToggle: () => void;
  onScoutToggle: () => void;
  onPrimalToggle: () => void;
  onSidebarToggle: () => void;
}

export function ChatNav({
  mode,
  theme,
  scoutOn,
  primalOn,
  sidebarOpen,
  userEmail,
  onModeChange,
  onThemeToggle,
  onScoutToggle,
  onPrimalToggle,
  onSidebarToggle,
}: Props) {
  return (
    <nav
      className="flex items-center px-4 gap-3 h-12 border-b flex-shrink-0"
      style={{
        background:   "var(--color-panel)",
        borderColor:  "var(--color-border)",
      }}
    >
      {/* Sidebar toggle */}
      <button
        type="button"
        onClick={onSidebarToggle}
        className="w-8 h-8 flex items-center justify-center rounded-[8px] transition-all duration-150 hover:opacity-70 cursor-pointer flex-shrink-0"
        style={{ color: "var(--color-muted)" }}
        title={sidebarOpen ? "Collapse sidebar" : "Expand sidebar"}
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <rect x="1" y="3.5" width="14" height="1.5" rx="0.75" fill="currentColor" />
          <rect x="1" y="7.25" width="14" height="1.5" rx="0.75" fill="currentColor" />
          <rect x="1" y="11" width="14" height="1.5" rx="0.75" fill="currentColor" />
        </svg>
      </button>

      {/* Logo */}
      <Link
        href="/"
        className="text-[0.88rem] font-extrabold tracking-[-0.02em] no-underline flex-shrink-0"
        style={{ color: "var(--color-surface)" }}
      >
        hexallabs
      </Link>

      {/* Mode pill — center */}
      <div className="flex-1 flex justify-center">
        <div
          className="flex items-center gap-0.5 rounded-full p-1"
          style={{
            background:  "var(--color-card)",
            border:      "1px solid var(--color-border)",
          }}
        >
          {MODES.map((m) => {
            const active = m.id === mode;
            return (
              <button
                key={m.id}
                type="button"
                onClick={() => onModeChange(m.id)}
                className="px-3 py-1 rounded-full text-[0.7rem] font-semibold transition-all duration-200 cursor-pointer"
                style={{
                  background:  active ? "var(--color-mode)"    : "transparent",
                  color:       active ? "#fff"                  : "var(--color-muted)",
                }}
              >
                {m.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Toggles */}
      <div className="flex items-center gap-2 flex-shrink-0">
        <button
          type="button"
          onClick={onScoutToggle}
          className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[0.68rem] font-semibold transition-all duration-200 cursor-pointer"
          style={{
            background:  "var(--color-card)",
            border:      `1px solid ${scoutOn ? "var(--color-mode)" : "var(--color-border)"}`,
            color:       scoutOn ? "var(--color-mode)" : "var(--color-muted)",
          }}
        >
          <span
            className="w-1.5 h-1.5 rounded-full flex-shrink-0"
            style={{ background: scoutOn ? "var(--color-mode)" : "var(--color-border)" }}
          />
          Scout
        </button>

        <button
          type="button"
          onClick={onPrimalToggle}
          className="flex items-center gap-1.5 px-3 py-1 rounded-full text-[0.68rem] font-semibold transition-all duration-200 cursor-pointer"
          style={{
            background:  "var(--color-card)",
            border:      `1px solid ${primalOn ? "#c09050" : "var(--color-border)"}`,
            color:       primalOn ? "#c09050" : "var(--color-muted)",
          }}
        >
          <span
            className="w-1.5 h-1.5 rounded-full flex-shrink-0"
            style={{ background: primalOn ? "#c09050" : "var(--color-border)" }}
          />
          Primal
        </button>
      </div>

      {/* Theme toggle */}
      <button
        type="button"
        onClick={onThemeToggle}
        className="w-8 h-8 flex items-center justify-center rounded-[8px] transition-opacity hover:opacity-70 cursor-pointer flex-shrink-0"
        style={{ color: "var(--color-muted)" }}
        title={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
      >
        {theme === "dark" ? (
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" />
          </svg>
        ) : (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
          </svg>
        )}
      </button>

      {/* Email + sign-out */}
      <div className="flex items-center gap-2 flex-shrink-0">
        {userEmail && (
          <span
            className="hidden sm:block text-[0.65rem] max-w-[140px] truncate"
            style={{ color: "#a89080" }}
            title={userEmail}
          >
            {userEmail}
          </span>
        )}
        <form action="/auth/signout" method="post">
          <button
            type="submit"
            className="px-2.5 py-1 rounded-full text-[0.68rem] font-semibold transition-all duration-200 cursor-pointer"
            style={{
              background: "var(--color-card)",
              border:     "1px solid var(--color-border)",
              color:      "var(--color-muted)",
            }}
          >
            Sign out
          </button>
        </form>
      </div>

      {/* Avatar */}
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center text-[0.7rem] font-bold flex-shrink-0"
        style={{ background: "var(--color-mode)", color: "#fff" }}
      >
        {userEmail ? userEmail[0]!.toUpperCase() : "A"}
      </div>
    </nav>
  );
}
