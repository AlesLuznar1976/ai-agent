"use client";

import ReactMarkdown from "react-markdown";
import { ChatMessage } from "@/types/chat";
import LuznarLogo from "@/components/brand/LuznarLogo";
import ActionButtons from "./ActionButtons";
import { formatTime } from "@/lib/utils";

interface MessageBubbleProps {
  message: ChatMessage;
  onConfirm: (actionId: string) => void;
  onReject: (actionId: string) => void;
}

export default function MessageBubble({ message, onConfirm, onReject }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isUser) {
    return (
      <div className="flex items-start gap-3 mb-4 justify-end">
        <div className="max-w-[80%]">
          <div className="bg-navy text-white px-4 py-3 rounded-md rounded-tr-[4px]">
            <p className="text-sm leading-relaxed">{message.content}</p>
          </div>
          <p className="text-[10px] text-white/50 mt-1 text-right">
            {formatTime(message.timestamp)}
          </p>
        </div>
        <div className="w-8 h-8 bg-gold/15 rounded-lg flex items-center justify-center shrink-0">
          <svg className="w-[18px] h-[18px] text-gold" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
          </svg>
        </div>
      </div>
    );
  }

  if (isSystem) {
    return (
      <div className="flex items-start gap-3 mb-4">
        <div className="w-8 h-8 bg-warning/10 rounded-lg flex items-center justify-center shrink-0">
          <svg className="w-4 h-4 text-warning" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
          </svg>
        </div>
        <div className="max-w-[80%]">
          <div className="bg-warning/5 border border-warning/15 px-4 py-3 rounded-md rounded-tl-[4px]">
            <div className="prose prose-sm max-w-none text-text-primary">
              <ReactMarkdown>{message.content}</ReactMarkdown>
            </div>
          </div>
          <p className="text-[10px] text-text-muted mt-1">
            {formatTime(message.timestamp)}
          </p>
        </div>
      </div>
    );
  }

  // Agent message
  return (
    <div className="flex items-start gap-3 mb-4">
      <div className="w-8 h-8 bg-navy rounded-lg flex items-center justify-center shrink-0">
        <LuznarLogo size={18} color="#B8963E" />
      </div>
      <div className="max-w-[80%]">
        <div className="bg-white border border-navy/6 shadow-sm px-4 py-3 rounded-md rounded-tl-[4px]">
          <div className="prose prose-sm max-w-none text-text-primary [&_p]:text-sm [&_p]:leading-relaxed [&_strong]:text-navy [&_strong]:font-semibold [&_h1]:text-xl [&_h1]:font-bold [&_h1]:text-navy [&_h2]:text-lg [&_h2]:font-semibold [&_h2]:text-navy [&_h3]:text-base [&_h3]:font-semibold [&_h3]:text-navy [&_code]:text-[13px] [&_code]:bg-surface [&_code]:px-1 [&_code]:rounded [&_pre]:bg-surface [&_pre]:rounded-sm [&_pre]:border [&_pre]:border-navy/8 [&_table]:text-[13px] [&_th]:text-navy [&_th]:font-semibold [&_td]:border-b [&_td]:border-navy/8 [&_td]:py-1 [&_td]:px-2 [&_th]:border-b [&_th]:border-navy/8 [&_th]:py-1 [&_th]:px-2 [&_ul]:list-disc [&_ol]:list-decimal [&_li]:text-sm">
            <ReactMarkdown>{message.content}</ReactMarkdown>
          </div>
          {message.needsConfirmation && message.actions && (
            <ActionButtons
              actions={message.actions}
              onConfirm={onConfirm}
              onReject={onReject}
            />
          )}
        </div>
        <p className="text-[10px] text-text-muted mt-1">
          {formatTime(message.timestamp)}
        </p>
      </div>
    </div>
  );
}
