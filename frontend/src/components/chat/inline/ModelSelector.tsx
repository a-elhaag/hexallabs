"use client";

import { useState } from "react";
import { MODELS } from "~/components/chat/types";

interface Props {
  selected: string[];
  onChange: (ids: string[]) => void;
}

export function ModelSelector({ selected, onChange }: Props) {
  function toggle(id: string) {
    if (selected.includes(id)) {
      onChange(selected.filter((s) => s !== id));
    } else {
      onChange([...selected, id]);
    }
  }

  return (
    <div className="flex flex-wrap gap-2">
      {MODELS.map((m) => {
        const active = selected.includes(m.id);
        return (
          <button
            key={m.id}
            type="button"
            onClick={() => toggle(m.id)}
            className="flex items-center gap-2 px-4 py-2 rounded-[12px] border text-[0.78rem] font-semibold transition-all duration-200 cursor-pointer"
            style={{
              background:  active ? "rgba(98,144,195,0.1)" : "var(--color-card)",
              borderColor: active ? "var(--color-mode)"    : "var(--color-border)",
              color:       active ? "var(--color-mode)"    : "var(--color-muted)",
            }}
          >
            <span
              className="w-4 h-4 rounded-[4px] border flex items-center justify-center flex-shrink-0"
              style={{
                borderColor:     active ? "var(--color-mode)" : "var(--color-border)",
                backgroundColor: active ? "var(--color-mode)" : "transparent",
              }}
            >
              {active && (
                <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                  <path d="M1 4l3 3 5-6" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              )}
            </span>
            {m.label}
          </button>
        );
      })}
    </div>
  );
}
