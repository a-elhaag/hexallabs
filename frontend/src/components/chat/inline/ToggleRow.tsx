"use client";

import { useRef } from "react";
import { gsap } from "gsap";

interface ToggleItem {
  id: string;
  label: string;
  desc: string;
  value: boolean;
  onChange: (v: boolean) => void;
}

function Toggle({ label, desc, value, onChange }: Omit<ToggleItem, "id">) {
  const thumbRef = useRef<HTMLDivElement>(null);

  function handleClick() {
    const next = !value;
    onChange(next);
    if (thumbRef.current) {
      gsap.to(thumbRef.current, {
        x: next ? 16 : 0,
        duration: 0.28,
        ease: "power3.out",
      });
    }
  }

  return (
    <div className="flex items-center justify-between py-3 border-b last:border-b-0" style={{ borderColor: "var(--color-border)" }}>
      <div>
        <div className="text-[0.82rem] font-semibold" style={{ color: "var(--color-surface)" }}>{label}</div>
        <div className="text-[0.7rem] mt-0.5" style={{ color: "var(--color-muted)" }}>{desc}</div>
      </div>
      <button
        type="button"
        onClick={handleClick}
        className="relative flex-shrink-0 w-9 h-5 rounded-full transition-colors duration-200 ml-6"
        style={{ background: value ? "var(--color-mode)" : "var(--color-border)" }}
      >
        <div
          ref={thumbRef}
          className="absolute top-0.5 left-0.5 w-4 h-4 rounded-full bg-white shadow-sm"
          style={{ transform: `translateX(${value ? 16 : 0}px)` }}
        />
      </button>
    </div>
  );
}

interface Props {
  scoutOn: boolean;
  primalOn: boolean;
  onScoutChange: (v: boolean) => void;
  onPrimalChange: (v: boolean) => void;
}

export function ToggleRow({ scoutOn, primalOn, onScoutChange, onPrimalChange }: Props) {
  return (
    <div
      className="rounded-[16px] px-4 border"
      style={{ background: "var(--color-card)", borderColor: "var(--color-border)" }}
    >
      <Toggle
        label="Scout"
        desc="Inject live web search as context before models respond"
        value={scoutOn}
        onChange={onScoutChange}
      />
      <Toggle
        label="Primal Protocol"
        desc="Apex rewrites synthesis in brutally compressed, signal-dense form"
        value={primalOn}
        onChange={onPrimalChange}
      />
    </div>
  );
}
