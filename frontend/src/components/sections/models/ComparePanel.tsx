"use client";

import type { ModelData, SpeedTier } from "./modelData";
import { Button } from "~/components/ui/Button";

const speedColors: Record<SpeedTier, { bg: string; text: string }> = {
  Fast:     { bg: "rgba(91,160,138,0.22)", text: "#5ba08a" },
  Medium:   { bg: "rgba(98,144,195,0.22)", text: "#6290c3" },
  Thorough: { bg: "rgba(192,144,80,0.22)", text: "#c09050" },
};

interface ComparePanelProps {
  models: ModelData[];
  onClear: () => void;
}

export function ComparePanel({ models, onClear }: ComparePanelProps) {
  const visible = models.length >= 2;

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-50"
      style={{
        transform: visible ? "translateY(0)" : "translateY(100%)",
        transition: "transform 0.5s cubic-bezier(0.16,1,0.3,1)",
        willChange: "transform",
      }}
    >
      <div
        style={{
          background: "#1e1e1e",
          borderTop: "1px solid rgba(168,144,128,0.18)",
          backdropFilter: "blur(16px)",
          WebkitBackdropFilter: "blur(16px)",
        }}
      >
        {/* Header */}
        <div className="px-10 pt-4 pb-3 flex items-center justify-between border-b border-[rgba(168,144,128,0.1)]">
          <span className="text-[0.78rem] font-bold text-[var(--color-muted)] uppercase tracking-[0.1em]">
            Comparing{" "}
            <span className="text-[var(--color-surface)]">{models.length}</span>{" "}
            models
          </span>
          <Button variant="ghost" size="sm" onClick={onClear}>
            Clear
          </Button>
        </div>

        {/* Columns */}
        <div
          className="flex overflow-x-auto"
          style={{ minHeight: "220px", maxHeight: "260px" }}
        >
          {models.map((model, idx) => {
            const speed = speedColors[model.speedTier];
            const isLast = idx === models.length - 1;
            return (
              <div
                key={model.id}
                className="flex-1 min-w-[200px] px-7 py-5 flex flex-col gap-3"
                style={
                  isLast
                    ? {}
                    : { borderRight: "1px solid rgba(168,144,128,0.12)" }
                }
              >
                {/* Name */}
                <div>
                  <div
                    className="font-extrabold text-[1rem] leading-tight"
                    style={{ color: model.roleColor }}
                  >
                    {model.whitelabel}
                  </div>
                  <div
                    className="text-[0.65rem] text-[var(--color-muted)] mt-[2px]"
                    style={{ fontFamily: "var(--font-mono)" }}
                  >
                    {model.realName}
                  </div>
                </div>

                {/* Provider chip */}
                <span
                  className="inline-flex self-start items-center rounded-pill px-[0.6rem] py-[0.14rem] text-[0.62rem] font-bold"
                  style={{
                    background: "rgba(168,144,128,0.12)",
                    color: "var(--color-muted)",
                    border: "1px solid rgba(168,144,128,0.2)",
                  }}
                >
                  {model.provider}
                </span>

                {/* Speed */}
                <div className="flex items-center gap-2">
                  <span className="text-[0.62rem] font-semibold text-[var(--color-muted)]">
                    Speed
                  </span>
                  <span
                    className="inline-flex items-center rounded-pill px-[0.55rem] py-[0.12rem] text-[0.6rem] font-bold"
                    style={{ background: speed.bg, color: speed.text }}
                  >
                    {model.speedTier}
                  </span>
                </div>

                {/* Context */}
                <div className="flex items-center gap-2">
                  <span className="text-[0.62rem] font-semibold text-[var(--color-muted)]">
                    Context
                  </span>
                  <span
                    className="text-[0.63rem] font-bold text-[var(--color-surface)]"
                    style={{ fontFamily: "var(--font-mono)" }}
                  >
                    {model.contextWindow}
                  </span>
                </div>

                {/* Strengths */}
                <div className="flex flex-wrap gap-[4px]">
                  {model.strengths.map((s) => (
                    <span
                      key={s}
                      className="inline-flex items-center rounded-pill px-[0.5rem] py-[0.1rem] text-[0.6rem] font-bold"
                      style={{
                        background: "rgba(168,144,128,0.1)",
                        color: "var(--color-muted)",
                      }}
                    >
                      {s}
                    </span>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
