"use client";

interface FilterChipBarProps {
  items: string[];
  selected: string;
  onSelect: (item: string) => void;
  accentColor?: string;
  showIcon?: boolean;
}

export default function FilterChipBar({
  items,
  selected,
  onSelect,
  accentColor = "#1A2744",
  showIcon = false,
}: FilterChipBarProps) {
  return (
    <div className="h-[52px] px-3 bg-white flex items-center overflow-x-auto no-scrollbar">
      {items.map((item) => {
        const isSelected = selected === item;
        return (
          <button
            key={item}
            onClick={() => onSelect(item)}
            className="flex items-center gap-1 shrink-0 px-3 py-1.5 mx-1 rounded-xl text-xs border transition-colors"
            style={{
              fontWeight: isSelected ? 600 : 400,
              color: isSelected ? accentColor : "#5A6577",
              backgroundColor: isSelected ? `${accentColor}1A` : "transparent",
              borderColor: isSelected ? `${accentColor}4D` : "#1A27441A",
            }}
          >
            {showIcon && item !== items[0] && (
              <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            )}
            {item}
            {isSelected && (
              <svg className="w-3 h-3 ml-0.5" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
            )}
          </button>
        );
      })}
    </div>
  );
}
