"use client";

import { useRef, useEffect, forwardRef } from "react";
import { Chip } from "~/components/ui/Chip";
import type { ModelData, SpeedTier } from "./modelData";

const speedColors: Record<SpeedTier, { bg: string; text: string }> = {
  Fast:     { bg: "rgba(91,160,138,0.16)", text: "#5ba08a" },
  Medium:   { bg: "rgba(98,144,195,0.16)", text: "#6290c3" },
  Thorough: { bg: "rgba(192,144,80,0.16)", text: "#c09050" },
};

interface ModelCardProps {
  model: ModelData;
  visible: boolean;
  isSelected: boolean;
  onToggleCompare: (id: string) => void;
  shakeCompare: boolean;
}

export const ModelCard = forwardRef<HTMLDivElement, ModelCardProps>(
  function ModelCard(
    { model, visible, isSelected, onToggleCompare, shakeCompare },
    ref
  ) {
    const speed = speedColors[model.speedTier];
    const cardRef = useRef<HTMLDivElement>(null);

    // Expose the inner card div via forwardRef for GSAP
    useEffect(() => {
      if (typeof ref === "function") {
        ref(cardRef.current);
      } else if (ref) {
        (ref as React.MutableRefObject<HTMLDivElement | null>).current =
          cardRef.current;
      }
    }, [ref]);

    // Shake animation when compare limit hit
    useEffect(() => {
      if (!shakeCompare || !cardRef.current) return;
      const el = cardRef.current;
      el.animate(
        [
          { transform: "translateX(0)" },
          { transform: "translateX(-6px)" },
          { transform: "translateX(6px)" },
          { transform: "translateX(-4px)" },
          { transform: "translateX(4px)" },
          { transform: "translateX(0)" },
        ],
        { duration: 360, easing: "ease-in-out" }
      );
    }, [shakeCompare]);

    return (
      <div
        style={{
          opacity: visible ? 1 : 0,
          pointerEvents: visible ? "auto" : "none",
          transition: "opacity 0.28s cubic-bezier(0.16,1,0.3,1)",
        }}
      >
        <div
          ref={cardRef}
          className="group rounded-card p-5 flex flex-col gap-3 h-full"
          style={{
            background: "#faf7f4",
            border: isSelected
              ? `1.5px solid var(--color-accent)`
              : "1.5px solid rgba(168,144,128,0.14)",
            boxShadow: isSelected
              ? "0 0 0 3px rgba(98,144,195,0.18), 0 4px 20px rgba(0,0,0,0.13)"
              : "0 1px 8px rgba(0,0,0,0.10)",
            transition:
              "transform 0.3s cubic-bezier(0.16,1,0.3,1), box-shadow 0.3s cubic-bezier(0.16,1,0.3,1), border-color 0.22s",
          }}
          onMouseEnter={(e) => {
            if (!isSelected) {
              (e.currentTarget as HTMLDivElement).style.transform =
                "translateY(-4px)";
              (e.currentTarget as HTMLDivElement).style.boxShadow =
                "0 12px 40px rgba(0,0,0,0.18)";
            }
          }}
          onMouseLeave={(e) => {
            if (!isSelected) {
              (e.currentTarget as HTMLDivElement).style.transform = "";
              (e.currentTarget as HTMLDivElement).style.boxShadow =
                "0 1px 8px rgba(0,0,0,0.10)";
            }
          }}
        >
          {/* Header row */}
          <div className="flex items-start justify-between gap-2">
            <div className="flex items-center gap-2 min-w-0">
              {/* Role color dot */}
              <span
                className="w-2 h-2 rounded-full shrink-0 mt-0.5"
                style={{ background: model.roleColor }}
              />
              <div className="min-w-0">
                <div
                  className="font-extrabold leading-tight text-[var(--color-bg)] truncate"
                  style={{ fontSize: "1.08rem" }}
                >
                  {model.whitelabel}
                </div>
                <div
                  className="font-mono text-[0.67rem] text-[#9a8a82] mt-[2px] truncate"
                  style={{ fontFamily: "var(--font-mono)" }}
                >
                  {model.realName}
                </div>
              </div>
            </div>

            {/* Compare checkbox */}
            <button
              onClick={() => onToggleCompare(model.id)}
              aria-label={`${isSelected ? "Remove" : "Add"} ${model.whitelabel} to compare`}
              className="shrink-0 w-5 h-5 rounded-[5px] flex items-center justify-center cursor-pointer transition-all duration-[180ms]"
              style={
                isSelected
                  ? {
                      background: "var(--color-accent)",
                      border: "1.5px solid var(--color-accent)",
                    }
                  : {
                      background: "transparent",
                      border: "1.5px solid rgba(98,144,195,0.45)",
                    }
              }
            >
              {isSelected && (
                <svg
                  width="11"
                  height="11"
                  viewBox="0 0 11 11"
                  fill="none"
                  stroke="#fff"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                >
                  <polyline points="2,6 4.5,8.5 9,3" />
                </svg>
              )}
            </button>
          </div>

          {/* Role badge */}
          <div>
            <span
              className="inline-flex items-center rounded-pill px-[0.65rem] py-[0.18rem] text-[0.63rem] font-bold"
              style={{
                background: model.roleColor + "26",
                color: model.roleColor,
              }}
            >
              {model.role}
            </span>
          </div>

          {/* Speed row */}
          <div className="flex items-center justify-between gap-2">
            <span className="text-[0.67rem] font-semibold text-[#9a8a82]">
              Speed
            </span>
            <span
              className="inline-flex items-center rounded-pill px-[0.6rem] py-[0.15rem] text-[0.63rem] font-bold"
              style={{ background: speed.bg, color: speed.text }}
            >
              {model.speedTier}
            </span>
          </div>

          {/* Context row */}
          <div className="flex items-center justify-between gap-2">
            <span className="text-[0.67rem] font-semibold text-[#9a8a82]">
              Context
            </span>
            <span
              className="text-[0.67rem] font-bold text-[var(--color-bg)]"
              style={{ fontFamily: "var(--font-mono)" }}
            >
              {model.contextWindow} tokens
            </span>
          </div>

          <div
            className="h-px"
            style={{ background: "rgba(168,144,128,0.14)" }}
          />

          {/* Strengths */}
          <div>
            <div className="text-[0.63rem] font-semibold text-[#9a8a82] mb-[6px] uppercase tracking-[0.08em]">
              Strengths
            </div>
            <div className="flex flex-wrap gap-[5px]">
              {model.strengths.map((s) => (
                <Chip key={s} variant="outline">
                  {s}
                </Chip>
              ))}
            </div>
          </div>

          {/* Best for */}
          <div>
            <div className="text-[0.63rem] font-semibold text-[#9a8a82] mb-[6px] uppercase tracking-[0.08em]">
              Best for
            </div>
            <div className="flex flex-wrap gap-[5px]">
              {model.bestFor.map((b) => (
                <span
                  key={b}
                  className="text-[0.62rem] font-medium text-[#9a8a82]"
                >
                  {b}
                  {model.bestFor.indexOf(b) < model.bestFor.length - 1 && (
                    <span className="opacity-40 ml-[5px]">/</span>
                  )}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }
);
