interface IconProps {
  size?: number;
  color?: string;
  className?: string;
}

export default function IconOracle({
  size = 20,
  color = "currentColor",
  className,
}: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 20 20"
      fill="none"
      aria-label="Oracle"
      className={className}
    >
      {/* Outer circle */}
      <circle cx="10" cy="10" r="7" stroke={color} strokeWidth="1.2" />
      {/* Vertical crosshair */}
      <line x1="10" y1="3" x2="10" y2="17" stroke={color} strokeWidth="0.7" opacity={0.5} />
      {/* Horizontal crosshair */}
      <line x1="3" y1="10" x2="17" y2="10" stroke={color} strokeWidth="0.7" opacity={0.5} />
      {/* Center dot */}
      <circle cx="10" cy="10" r="2" fill={color} />
    </svg>
  );
}
