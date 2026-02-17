"use client";

interface SuggestedCommandsProps {
  commands: string[];
  onSelect: (command: string) => void;
}

export default function SuggestedCommands({ commands, onSelect }: SuggestedCommandsProps) {
  if (commands.length === 0) return null;

  return (
    <div className="h-11 px-3 flex items-center overflow-x-auto no-scrollbar">
      {commands.map((cmd) => (
        <button
          key={cmd}
          onClick={() => onSelect(cmd)}
          className="shrink-0 mx-1 px-3 py-1.5 bg-white text-navy text-xs font-medium border border-navy/15 rounded-xl hover:bg-navy/5 transition-colors"
        >
          {cmd}
        </button>
      ))}
    </div>
  );
}
