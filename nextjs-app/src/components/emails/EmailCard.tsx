"use client";

import { useRouter } from "next/navigation";
import { Email } from "@/types/email";
import { formatDate, getStatusColor, getRfqSubcategoryColor } from "@/lib/utils";
import Badge from "@/components/ui/Badge";

interface EmailCardProps {
  email: Email;
}

export default function EmailCard({ email }: EmailCardProps) {
  const router = useRouter();
  const statusColor = getStatusColor(email.analizaStatus);
  const statusLabel = email.analizaStatus || "Brez";

  return (
    <div
      onClick={() => router.push(`/emaili/${email.id}`)}
      className="bg-white rounded-md border border-navy/8 p-4 mb-2.5 hover:shadow-sm transition-shadow cursor-pointer"
    >
      {/* Header: subject + status */}
      <div className="flex items-center gap-2 mb-1.5">
        <span className="flex-1 text-sm font-bold text-navy truncate">
          {email.zadeva || "(brez zadeve)"}
        </span>
        <Badge label={statusLabel} color={statusColor} />
      </div>

      {/* Sender */}
      <p className="text-xs text-text-secondary truncate mb-2.5">
        {email.posiljatelj || ""}
      </p>

      {/* Footer: date + category + rfq subcategory + attachments */}
      <div className="flex items-center gap-2 flex-wrap">
        {email.datum && (
          <div className="flex items-center gap-1">
            <svg className="w-3.5 h-3.5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
            </svg>
            <span className="text-xs text-text-secondary">{formatDate(email.datum)}</span>
          </div>
        )}
        {email.kategorija && (
          <span className="px-2 py-0.5 text-[11px] font-medium text-text-secondary bg-navy/6 rounded-xl">
            {email.kategorija}
          </span>
        )}
        {email.rfqPodkategorija && (
          <Badge
            label={email.rfqPodkategorija}
            color={getRfqSubcategoryColor(email.rfqPodkategorija)}
          />
        )}
        <div className="flex-1" />
        {email.priloge && email.priloge.length > 0 && (
          <div className="flex items-center gap-0.5">
            <svg className="w-4 h-4 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
            </svg>
            <span className="text-xs text-text-muted">{email.priloge.length}</span>
          </div>
        )}
      </div>
    </div>
  );
}
