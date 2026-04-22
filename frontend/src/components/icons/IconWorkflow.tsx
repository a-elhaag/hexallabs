interface IconProps {
  size?: number;
  color?: string;
  className?: string;
}

export default function IconWorkflow({
  size = 20,
  color = "currentColor",
  className,
}: IconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 20 22"
      fill="none"
      aria-label="Workflow"
      className={className}
    >
      {/* Input node left */}
      <rect x="0.5" y="0.5" width="7" height="5" rx="1.5" stroke={color} strokeWidth="1" opacity={0.5} />
      {/* Input node right */}
      <rect x="12.5" y="0.5" width="7" height="5" rx="1.5" stroke={color} strokeWidth="1" opacity={0.5} />
      {/* Bezier edge left→center */}
      <path d="M4 5.5 C4 10 10 10 10 11.5" stroke={color} strokeWidth="0.9" opacity={0.7} />
      {/* Bezier edge right→center */}
      <path d="M16 5.5 C16 10 10 10 10 11.5" stroke={color} strokeWidth="0.9" opacity={0.7} />
      {/* Center node — active */}
      <rect x="5.5" y="11.5" width="9" height="5" rx="1.5" stroke={color} strokeWidth="1.3" fill={color} fillOpacity={0.15} />
      {/* Edge center→output */}
      <line x1="10" y1="16.5" x2="10" y2="19" stroke={color} strokeWidth="0.9" opacity={0.5} />
      {/* Output node */}
      <rect x="5.5" y="19" width="9" height="4" rx="1.5" stroke={color} strokeWidth="1" opacity={0.3} />
    </svg>
  );
}
