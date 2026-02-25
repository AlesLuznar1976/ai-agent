"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import { ChatMessage } from "@/types/chat";
import { apiGenerateDocument } from "@/lib/api";
import LuznarLogo from "@/components/brand/LuznarLogo";
import ActionButtons from "./ActionButtons";
import DocumentForm from "./DocumentForm";
import { formatTime } from "@/lib/utils";

const DOCUMENT_TYPES = [
  { key: "reklamacija", label: "Reklamacija", icon: "!" },
  { key: "rfq_analiza", label: "RFQ analiza", icon: "Q" },
  { key: "bom_pregled", label: "BOM pregled", icon: "B" },
  { key: "porocilo", label: "Poročilo", icon: "P" },
];

interface MessageBubbleProps {
  message: ChatMessage;
  onConfirm: (actionId: string) => void;
  onReject: (actionId: string) => void;
  onFormSubmit?: (docType: string, formData: Record<string, string>) => void;
}

export default function MessageBubble({ message, onConfirm, onReject, onFormSubmit }: MessageBubbleProps) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";
  const [showDocMenu, setShowDocMenu] = useState(false);
  const [generating, setGenerating] = useState<string | null>(null);

  const handleGenerateDoc = async (templateType: string) => {
    setGenerating(templateType);
    setShowDocMenu(false);
    try {
      await apiGenerateDocument(message.content, templateType);
    } catch (e) {
      alert(e instanceof Error ? e.message : "Napaka pri generiranju dokumenta");
    } finally {
      setGenerating(null);
    }
  };

  if (isUser) {
    return (
      <div className="flex items-start gap-3 mb-4 justify-end">
        <div className="max-w-[80%]">
          <div className="bg-navy text-white px-4 py-3 rounded-md rounded-tr-[4px]">
            {message.content && (
              <p className="text-sm leading-relaxed">{message.content}</p>
            )}
            {message.attachments && message.attachments.length > 0 && (
              <div className={`flex flex-wrap gap-1.5 ${message.content ? "mt-2" : ""}`}>
                {message.attachments.map((att, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-1.5 bg-white/10 rounded px-2 py-1 text-[11px] text-white/80"
                  >
                    <AttachmentIcon mime={att.mime_type} />
                    <span className="max-w-[120px] truncate">{att.filename}</span>
                  </div>
                ))}
              </div>
            )}
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
  const showDocButtons = message.content && message.content.length > 100;

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
          {message.documentForm && message.documentForm.fields.length > 0 && onFormSubmit && (
            <DocumentForm
              form={message.documentForm}
              onSubmit={onFormSubmit}
            />
          )}
        </div>

        {/* Timestamp + Document export */}
        <div className="flex items-center gap-2 mt-1">
          <p className="text-[10px] text-text-muted">
            {formatTime(message.timestamp)}
          </p>

          {showDocButtons && (
            <div className="relative">
              <button
                onClick={() => setShowDocMenu(!showDocMenu)}
                disabled={generating !== null}
                className="flex items-center gap-1 text-[10px] text-navy/40 hover:text-navy transition-colors disabled:opacity-50"
                title="Prenesi kot dokument"
              >
                {generating ? (
                  <>
                    <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                    </svg>
                    Generiram...
                  </>
                ) : (
                  <>
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
                    </svg>
                    Word
                    <svg className="w-2.5 h-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                    </svg>
                  </>
                )}
              </button>

              {/* Dropdown menu */}
              {showDocMenu && (
                <div className="absolute bottom-full left-0 mb-1 bg-white border border-navy/10 rounded-lg shadow-lg py-1 z-50 min-w-[180px]">
                  {DOCUMENT_TYPES.map((dt) => (
                    <button
                      key={dt.key}
                      onClick={() => handleGenerateDoc(dt.key)}
                      className="w-full text-left px-3 py-1.5 text-xs text-text-primary hover:bg-surface transition-colors flex items-center gap-2"
                    >
                      <span className="w-5 h-5 bg-navy/8 rounded text-[10px] font-bold text-navy flex items-center justify-center shrink-0">
                        {dt.icon}
                      </span>
                      {dt.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function AttachmentIcon({ mime }: { mime: string }) {
  if (mime.startsWith("image/")) {
    return (
      <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="m2.25 15.75 5.159-5.159a2.25 2.25 0 0 1 3.182 0l5.159 5.159m-1.5-1.5 1.409-1.409a2.25 2.25 0 0 1 3.182 0l2.909 2.909M3.75 21h16.5A2.25 2.25 0 0 0 22.5 18.75V5.25A2.25 2.25 0 0 0 20.25 3H3.75A2.25 2.25 0 0 0 1.5 5.25v13.5A2.25 2.25 0 0 0 3.75 21Z" />
      </svg>
    );
  }
  if (mime === "application/pdf") {
    return (
      <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
      </svg>
    );
  }
  return (
    <svg className="w-3 h-3 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
    </svg>
  );
}
