import LuznarLogo from "@/components/brand/LuznarLogo";

export default function TypingIndicator() {
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="w-8 h-8 bg-navy rounded-lg flex items-center justify-center shrink-0">
        <LuznarLogo size={18} color="#B8963E" />
      </div>
      <div className="bg-white rounded-md rounded-tl-[4px] border border-navy/6 shadow-sm px-4 py-3">
        <div className="flex gap-1.5">
          <div className="typing-dot w-[7px] h-[7px] rounded-full bg-gold" />
          <div className="typing-dot w-[7px] h-[7px] rounded-full bg-gold" />
          <div className="typing-dot w-[7px] h-[7px] rounded-full bg-gold" />
        </div>
      </div>
    </div>
  );
}
