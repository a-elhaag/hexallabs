interface IconProps {
  size?: number;
  color?: string;
  className?: string;
}

export default function IconRelay({
  size = 20,
  color = "currentColor",
  className,
}: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 16"
      fill="none"
      aria-label="The Relay"
      className={className}
    >
      {/* Node A */}
      <circle cx="3.5" cy="8" r="3" stroke={color} strokeWidth="1" opacity={0.5} />
      {/* Dashed line A→B */}
      <line x1="6.5" y1="8" x2="9.5" y2="8" stroke={color} strokeWidth="0.9" strokeDasharray="1.5,1.5" opacity={0.5} />
      {/* Node B — active */}
      <circle cx="12" cy="8" r="3.5" stroke={color} strokeWidth="1.4" fill={color} fillOpacity={0.15} />
      <circle cx="12" cy="8" r="1.2" fill={color} />
      {/* Dashed line B→C */}
      <line x1="15.5" y1="8" x2="17.5" y2="8" stroke={color} strokeWidth="0.9" strokeDasharray="1.5,1.5" opacity={0.3} />
      {/* Node C */}
      <circle cx="20.5" cy="8" r="3" stroke={color} strokeWidth="1" opacity={0.25} />
    </svg>
  );
}
