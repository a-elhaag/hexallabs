"use client";

import { useEffect, useRef } from "react";
import { gsap } from "gsap";

interface Props {
  original: string;
  improved: string;
  onUseOriginal: () => void;
  onUseImproved: () => void;
}

export function PromptForge({ original, improved, onUseOriginal, onUseImproved }: Props) {
  const cardRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!cardRef.current) return;
    gsap.fromTo(
      cardRef.current,
      { y: 20, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.4, ease: "power3.out" },
    );
  }, []);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center pb-[88px] px-4"
      style={{ background: "rgba(0,0,0,0.45)" }}
    >
      <div
        ref={cardRef}
        className="w-full max-w-[580px] rounded-[20px] p-5"
        style={{
          background:  "var(--color-panel)",
          border:      "1.5px solid var(--color-border)",
          boxShadow:   "0 24px 80px rgba(0,0,0,0.5)",
        }}
      >
        <div
          className="text-[0.62rem] font-bold uppercase tracking-[0.14em] mb-1"
          style={{ color: "var(--color-mode)" }}
        >
          ✦ Prompt Forge
        </div>
        <div
          className="text-[0.88rem] font-bold mb-4"
          style={{ color: "var(--color-surface)" }}
        >
          Your prompt has been sharpened
        </div>

        <div
          className="rounded-[12px] px-4 py-3 mb-2"
          style={{ background: "var(--color-card)", border: "1px solid var(--color-border)" }}
        >
          <div
            className="text-[0.58rem] font-bold uppercase tracking-[0.1em] mb-1.5"
            style={{ color: "var(--color-muted)" }}
          >
            Original
          </div>
          <div className="text-[0.8rem] leading-[1.55]" style={{ color: "rgba(168,144,128,0.7)" }}>
            {original}
          </div>
        </div>

        <div
          className="rounded-[12px] px-4 py-3 mb-4"
          style={{ background: "var(--color-card)", border: "1px solid rgba(98,144,195,0.25)" }}
        >
          <div
            className="text-[0.58rem] font-bold uppercase tracking-[0.1em] mb-1.5"
            style={{ color: "var(--color-mode)" }}
          >
            Improved
          </div>
          <div className="text-[0.8rem] leading-[1.6]" style={{ color: "var(--color-surface)" }}>
            {improved}
          </div>
        </div>

        <div className="flex gap-2">
          <button
            type="button"
            onClick={onUseOriginal}
            className="flex-1 py-2.5 rounded-[10px] text-[0.78rem] font-semibold transition-opacity hover:opacity-80 cursor-pointer"
            style={{
              background: "rgba(168,144,128,0.12)",
              color:      "var(--color-muted)",
            }}
          >
            Use original
          </button>
          <button
            type="button"
            onClick={onUseImproved}
            className="flex-1 py-2.5 rounded-[10px] text-[0.78rem] font-semibold transition-opacity hover:opacity-80 cursor-pointer"
            style={{
              background: "var(--color-mode)",
              color:      "#fff",
            }}
          >
            Use improved ▶
          </button>
        </div>
      </div>
    </div>
  );
}
