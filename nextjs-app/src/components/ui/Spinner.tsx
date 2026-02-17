interface SpinnerProps {
  size?: number;
}

export default function Spinner({ size = 32 }: SpinnerProps) {
  return (
    <div className="flex items-center justify-center">
      <div
        className="border-2 border-gold/30 border-t-gold rounded-full animate-spin"
        style={{ width: size, height: size }}
      />
    </div>
  );
}
