"use client";

import { ChatAction } from "@/types/chat";

interface ActionButtonsProps {
  actions: ChatAction[];
  onConfirm: (actionId: string) => void;
  onReject: (actionId: string) => void;
}

export default function ActionButtons({ actions, onConfirm, onReject }: ActionButtonsProps) {
  return (
    <div className="mt-2 space-y-2">
      {actions.map((action) => {
        if (action.status === "Čaka") {
          return (
            <div
              key={action.id}
              className="p-3 bg-warning/5 border border-warning/20 rounded-sm"
            >
              <div className="flex items-center gap-2 mb-2">
                <svg className="w-[18px] h-[18px] text-gold" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="text-sm text-text-primary">{action.description}</span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => onConfirm(action.id)}
                  className="text-sm font-medium text-success hover:text-success/80 transition-colors"
                >
                  Potrdi
                </button>
                <button
                  onClick={() => onReject(action.id)}
                  className="text-sm font-medium text-error hover:text-error/80 transition-colors"
                >
                  Zavrni
                </button>
              </div>
            </div>
          );
        }

        const isConfirmed = action.status === "Potrjeno";
        return (
          <div key={action.id} className="flex items-center gap-2 p-2">
            <svg
              className={`w-4 h-4 ${isConfirmed ? "text-success" : "text-error"}`}
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={2}
            >
              {isConfirmed ? (
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              )}
            </svg>
            <span className={`text-sm ${isConfirmed ? "text-success" : "text-error"}`}>
              {action.description} - {action.status}
            </span>
          </div>
        );
      })}
    </div>
  );
}
