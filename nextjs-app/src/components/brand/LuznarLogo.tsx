"use client";

interface LuznarLogoProps {
  size?: number;
  color?: string;
  withGlow?: boolean;
}

export default function LuznarLogo({ size = 48, color = "#B8963E", withGlow = false }: LuznarLogoProps) {
  const cx = size / 2;
  const cy = size / 2;

  return (
    <svg
      width={size}
      height={size}
      viewBox={`0 0 ${size} ${size}`}
      style={withGlow ? { filter: `drop-shadow(0 0 12px ${color}40)` } : undefined}
    >
      {/* Outer diamond */}
      <path
        d={`M${cx},0 L${size},${cy} L${cx},${size} L0,${cy} Z`}
        fill={color}
      />
      {/* Inner arrow/chevron */}
      <path
        d={`M${cx * 0.55},${cy * 0.55} L${cx * 1.3},${cy} L${cx * 0.55},${cy * 1.45} L${cx * 0.75},${cy} Z`}
        fill="#1A2744"
      />
    </svg>
  );
}
