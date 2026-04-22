"use client";

import { forwardRef, type CSSProperties, type ReactNode } from "react";

export type HexVariant = "solid" | "outline" | "ghost";

export interface HexProps {
  size?: number;
  label?: string;
  sublabel?: string;
  glow?: boolean;
  variant?: HexVariant;
  className?: string;
  style?: CSSProperties;
  children?: ReactNode;
  /** Visually decorative only */
  ariaHidden?: boolean;
}

const VARIANT_CLASS: Record<HexVariant, string> = {
  solid:
    "bg-[color:var(--color-bg)] text-[color:var(--color-surface)]",
  outline:
    "bg-[color:var(--bg-card)] text-[color:var(--color-bg)] ring-1 ring-inset ring-[color:var(--line-strong)]",
  ghost:
    "bg-transparent text-[color:var(--color-bg)]",
};

export const Hex = forwardRef<HTMLDivElement, HexProps>(function Hex(
  {
    size = 120,
    label,
    sublabel,
    glow = false,
    variant = "solid",
    className = "",
    style,
    children,
    ariaHidden = false,
  },
  ref,
) {
  const height = Math.round(size * 0.866 * 2) / 2;

  return (
    <div
      ref={ref}
      aria-hidden={ariaHidden || undefined}
      className={`relative inline-flex items-center justify-center ${className}`}
      style={{ width: size, height, ...style }}
    >
      <div
        className={`hex-clip absolute inset-0 transition-[box-shadow,background,transform] duration-300 ${VARIANT_CLASS[variant]} ${glow ? "hex-glow" : ""}`}
        style={{
          transitionTimingFunction: "var(--ease-hexal)",
        }}
      />
      <div className="relative z-10 flex flex-col items-center justify-center gap-0.5 px-3 text-center">
        {children ?? (
          <>
            {label ? (
              <span className="text-[0.95em] leading-none font-semibold tracking-tight">
                {label}
              </span>
            ) : null}
            {sublabel ? (
              <span className="mt-1 text-[0.65em] font-mono uppercase tracking-[0.12em] opacity-70">
                {sublabel}
              </span>
            ) : null}
          </>
        )}
      </div>
    </div>
  );
});

export default Hex;
