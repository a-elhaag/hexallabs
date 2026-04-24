"use client";

import { MODES, type Mode } from "~/components/chat/types";

interface Props {
  activeMode: Mode;
  onSelect: (mode: Mode) => void;
}

export function ModeSelector({ activeMode, onSelect }: Props) {
  return (
    <div className="flex flex-wrap gap-2">
      {MODES.map((m) => {
        const active = m.id === activeMode;
        return (
          <button
            key={m.id}
            type="button"
            onClick={() => onSelect(m.id)}
            className="flex flex-col gap-1 px-4 py-3 rounded-[16px] border text-left transition-all duration-200 cursor-pointer"
            style={{
              background:   active ? "rgba(var(--color-mode-rgb, 98,144,195), 0.08)" : "var(--color-card)",
              borderColor:  active ? "var(--color-mode)"                               : "var(--color-border)",
              boxShadow:    active ? "0 0 0 1px var(--color-mode)"                     : "none",
            }}
          >
            <div className="flex items-center gap-2">
              <span className="text-[1rem]">{m.icon}</span>
              <span
                className="text-[0.8rem] font-bold"
                style={{ color: active ? "var(--color-mode)" : "var(--color-surface)" }}
              >
                {m.label}
              </span>
            </div>
            <span className="text-[0.68rem] leading-[1.4]" style={{ color: "var(--color-muted)" }}>
              {m.desc}
            </span>
          </button>
        );
      })}
    </div>
  );
}
