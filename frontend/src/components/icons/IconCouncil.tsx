interface IconProps {
  size?: number;
  color?: string;
  className?: string;
}

const HEX = "polygon(50% 0%, 93% 25%, 93% 75%, 50% 100%, 7% 75%, 7% 25%)";

export default function IconCouncil({
  size = 20,
  color = "currentColor",
  className,
}: IconProps) {
  // Render as SVG hexagons for crisp scaling at any size
  const s = size;
  const cx = s / 2;
  const cy = s / 2;
  const r = s * 0.18; // outer hex radius
  const apexR = s * 0.14; // apex hex half-size

  // 6 outer hex centers at 60° intervals, offset from center
  const dist = s * 0.3;
  const outerPositions = Array.from({ length: 6 }, (_, i) => {
    const angle = (Math.PI / 3) * i - Math.PI / 6;
    return {
      x: cx + dist * Math.cos(angle),
      y: cy + dist * Math.sin(angle),
    };
  });

  function hexPoints(x: number, y: number, r: number) {
    return Array.from({ length: 6 }, (_, i) => {
      const a = (Math.PI / 3) * i - Math.PI / 6;
      return `${x + r * Math.cos(a)},${y + r * Math.sin(a)}`;
    }).join(" ");
  }

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      fill="none"
      aria-label="The Council"
      className={className}
    >
      {/* Connecting lines apex→outer */}
      {outerPositions.map((pos, i) => (
        <line
          key={i}
          x1={cx} y1={cy}
          x2={pos.x} y2={pos.y}
          stroke={color}
          strokeWidth={0.6}
          opacity={0.3}
        />
      ))}
      {/* Outer hexes */}
      {outerPositions.map((pos, i) => (
        <polygon
          key={i}
          points={hexPoints(pos.x, pos.y, r)}
          stroke={color}
          strokeWidth={0.8}
          fill={color}
          fillOpacity={0.12}
          opacity={0.7}
        />
      ))}
      {/* Apex hex — center, larger, accent */}
      <polygon
        points={hexPoints(cx, cy, apexR * 1.5)}
        stroke={color}
        strokeWidth={1.2}
        fill={color}
        fillOpacity={0.25}
      />
    </svg>
  );
}
