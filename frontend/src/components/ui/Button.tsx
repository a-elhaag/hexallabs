import { type ButtonHTMLAttributes } from "react";

type Variant = "primary" | "ghost" | "dark" | "blue";
type Size = "default" | "sm";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
}

const variantStyles: Record<Variant, string> = {
  primary: "bg-surface text-bg",
  ghost: "bg-transparent text-muted border border-[rgba(168,144,128,0.3)]",
  dark: "bg-bg text-surface",
  blue: "bg-accent text-white",
};

const sizeStyles: Record<Size, string> = {
  default: "px-7 py-[0.72rem] text-[0.85rem]",
  sm: "px-[1.1rem] py-[0.45rem] text-[0.75rem]",
};

export function Button({
  variant = "primary",
  size = "default",
  className = "",
  children,
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center font-bold rounded-pill cursor-pointer transition-opacity duration-180 hover:opacity-[0.82] active:opacity-[0.65] whitespace-nowrap font-sans ${variantStyles[variant]} ${sizeStyles[size]} ${className}`}
    >
      {children}
    </button>
  );
}
