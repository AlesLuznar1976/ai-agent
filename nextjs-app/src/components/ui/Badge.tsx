interface BadgeProps {
  label: string;
  color: string;
  className?: string;
}

export default function Badge({ label, color, className = "" }: BadgeProps) {
  return (
    <span
      className={`inline-block px-2.5 py-0.5 text-[11px] font-semibold tracking-wide rounded-xl ${className}`}
      style={{
        backgroundColor: `${color}14`,
        color: color,
      }}
    >
      {label}
    </span>
  );
}
