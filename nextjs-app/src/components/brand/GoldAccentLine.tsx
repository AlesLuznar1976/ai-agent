interface GoldAccentLineProps {
  width?: number;
}

export default function GoldAccentLine({ width = 40 }: GoldAccentLineProps) {
  return (
    <div
      className="h-[2px] rounded-sm"
      style={{
        width,
        background: "linear-gradient(to right, #D4B366, #B8963E)",
      }}
    />
  );
}
