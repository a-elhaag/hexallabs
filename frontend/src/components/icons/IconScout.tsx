interface IconProps {
  size?: number;
  color?: string;
  className?: string;
}

export default function IconScout({
  size = 20,
  color = "currentColor",
  className,
}: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 26"
      fill="none"
      aria-label="Scout"
      className={className}
    >
      {/* Outer circle */}
      <circle cx="10" cy="11" r="7.5" stroke={color} strokeWidth="1.2" />
      {/* Vertical crosshair */}
      <line x1="10" y1="3.5" x2="10" y2="18.5" stroke={color} strokeWidth="0.7" opacity={0.5} />
      {/* Horizontal crosshair */}
      <line x1="2.5" y1="11" x2="17.5" y2="11" stroke={color} strokeWidth="0.7" opacity={0.5} />
      {/* Equatorial ellipse */}
      <ellipse cx="10" cy="12.5" rx="4.5" ry="2.5" stroke={color} strokeWidth="1" opacity={0.8} />
      {/* Handle */}
      <line x1="15.8" y1="17.2" x2="22" y2="25" stroke={color} strokeWidth="2.2" strokeLinecap="round" />
    </svg>
  );
}
