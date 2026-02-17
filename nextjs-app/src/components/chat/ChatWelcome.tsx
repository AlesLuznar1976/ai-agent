"use client";

import LuznarLogo from "@/components/brand/LuznarLogo";
import GoldAccentLine from "@/components/brand/GoldAccentLine";

interface ChatWelcomeProps {
  onSend: (message: string) => void;
}

const quickActions = [
  { label: "Preveri emaile", icon: "email" },
  { label: "Seznam projektov", icon: "folder" },
  { label: "Nov projekt", icon: "add" },
  { label: "Pomoč", icon: "help" },
];

function ActionIcon({ icon }: { icon: string }) {
  const cls = "w-[18px] h-[18px] text-gold";
  switch (icon) {
    case "email":
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" /></svg>;
    case "folder":
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" /></svg>;
    case "add":
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v6m3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>;
    case "help":
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" /></svg>;
    default:
      return null;
  }
}

export default function ChatWelcome({ onSend }: ChatWelcomeProps) {
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-6">
      <div className="w-20 h-20 bg-navy/6 rounded-[20px] flex items-center justify-center">
        <LuznarLogo size={48} color="#1A2744" />
      </div>
      <h2 className="mt-4 text-2xl font-semibold text-navy">Dobrodošli</h2>
      <p className="mt-2 text-[15px] text-text-secondary">Kako vam lahko pomagam danes?</p>
      <div className="mt-3">
        <GoldAccentLine width={32} />
      </div>
      <div className="mt-6 flex flex-wrap justify-center gap-3">
        {quickActions.map((action) => (
          <button
            key={action.label}
            onClick={() => onSend(action.label)}
            className="flex items-center gap-2 px-4 py-3 bg-white rounded-md border border-navy/10 hover:border-navy/25 transition-colors"
          >
            <ActionIcon icon={action.icon} />
            <span className="text-[13px] font-medium text-navy">{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
