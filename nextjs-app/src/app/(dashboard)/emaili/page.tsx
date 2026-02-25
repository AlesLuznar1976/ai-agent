"use client";

import { useState, useEffect, useMemo } from "react";
import { Email } from "@/types/email";
import { apiGetEmaili } from "@/lib/api";
import { getRfqSubcategoryColor } from "@/lib/utils";
import { useAuth } from "@/lib/auth-context";
import FilterChipBar from "@/components/ui/FilterChipBar";
import Spinner from "@/components/ui/Spinner";
import ErrorState from "@/components/ui/ErrorState";
import EmptyState from "@/components/ui/EmptyState";
import EmailCard from "@/components/emails/EmailCard";

const STATUSI = ["Vse", "Končano", "Čaka", "V obdelavi", "Napaka", "Brez"];

const KATEGORIJE = [
  "RFQ",
  "Naročilo",
  "Sprememba",
  "Dokumentacija",
  "Reklamacija",
  "Splošno",
] as const;

const RFQ_PODKATEGORIJE = ["Vse RFQ", "Kompletno", "Nepopolno", "Povpraševanje", "Repeat Order"];

// Categories expanded by default
const DEFAULT_EXPANDED = new Set(["RFQ", "Naročilo"]);

const KATEGORIJA_COLORS: Record<string, string> = {
  RFQ: "#3B82F6",
  "Naročilo": "#10B981",
  Sprememba: "#F59E0B",
  Dokumentacija: "#8B5CF6",
  Reklamacija: "#EF4444",
  "Splošno": "#6B7280",
};

export default function EmailiPage() {
  const { user } = useAuth();
  const [vsiEmaili, setVsiEmaili] = useState<Email[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState("Vse");
  const [selectedRfqPodkat, setSelectedRfqPodkat] = useState("Vse RFQ");
  const [expanded, setExpanded] = useState<Set<string>>(new Set(DEFAULT_EXPANDED));

  const isAdmin = user?.role === "admin";

  const loadEmaili = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiGetEmaili();
      setVsiEmaili(data);
    } catch {
      setError("Napaka pri nalaganju emailov");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadEmaili();
  }, []);

  const toggleSection = (kategorija: string) => {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(kategorija)) {
        next.delete(kategorija);
      } else {
        next.add(kategorija);
      }
      return next;
    });
  };

  // Ignore emails before cutoff date for clean overview
  const recentEmaili = useMemo(() => {
    return vsiEmaili.filter((e) => e.datum && e.datum >= "2026-02-19");
  }, [vsiEmaili]);

  // Filter by mailbox (non-admin sees only their mailbox)
  const mailboxFiltered = useMemo(() => {
    if (isAdmin || !user?.mailbox) return recentEmaili;
    return recentEmaili.filter((e) => {
      const m = (e.izvleceniPodatki?.mailbox as string) || "";
      return m === user.mailbox;
    });
  }, [recentEmaili, isAdmin, user?.mailbox]);

  // Apply status filter
  const statusFiltered = useMemo(() => {
    if (selectedStatus === "Vse") return mailboxFiltered;
    return mailboxFiltered.filter(
      (e) => (e.analizaStatus || "Brez") === selectedStatus
    );
  }, [mailboxFiltered, selectedStatus]);

  // Group by category
  const grouped = useMemo(() => {
    const map: Record<string, Email[]> = {};
    for (const kat of KATEGORIJE) {
      map[kat] = [];
    }
    for (const email of statusFiltered) {
      const kat = email.kategorija || "Splošno";
      if (map[kat]) {
        map[kat].push(email);
      } else {
        map["Splošno"].push(email);
      }
    }
    return map;
  }, [statusFiltered]);

  // RFQ subcategory filter applied within the RFQ section
  const getVisibleEmails = (kategorija: string, emails: Email[]) => {
    if (kategorija !== "RFQ" || selectedRfqPodkat === "Vse RFQ") return emails;
    return emails.filter((e) => e.rfqPodkategorija === selectedRfqPodkat);
  };

  // Color function for RFQ filter chips
  const getRfqChipColor = (podkat: string) => {
    if (podkat === "Vse RFQ") return "#1A2744";
    return getRfqSubcategoryColor(podkat);
  };

  return (
    <div className="flex flex-col h-full bg-surface">
      {/* Status filter */}
      <FilterChipBar
        items={STATUSI}
        selected={selectedStatus}
        onSelect={setSelectedStatus}
      />
      <div className="h-px bg-navy/6" />

      {/* Mailbox info bar */}
      {!isLoading && !error && (
        <div className="px-4 py-2.5 bg-white flex items-center gap-2 text-xs text-text-secondary">
          <svg className="w-4 h-4 text-text-muted shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
          </svg>
          <span>
            {isAdmin
              ? `Vsi nabiralniki | ${statusFiltered.length} emailov`
              : `Nabiralnik: ${user?.mailbox || "ni nastavljeno"} | ${statusFiltered.length} emailov`}
          </span>
        </div>
      )}
      <div className="h-px bg-navy/6" />

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Spinner />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={loadEmaili} />
        ) : statusFiltered.length === 0 ? (
          <EmptyState
            icon={
              <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
              </svg>
            }
            message="Ni emailov"
          />
        ) : (
          <div className="p-3 space-y-2">
            {KATEGORIJE.map((kat) => {
              const emails = grouped[kat];
              const visibleEmails = getVisibleEmails(kat, emails);
              const isExpanded = expanded.has(kat);
              const katColor = KATEGORIJA_COLORS[kat] || "#6B7280";

              return (
                <div key={kat} className="bg-white rounded-lg border border-navy/8 overflow-hidden">
                  {/* Category header */}
                  <button
                    onClick={() => toggleSection(kat)}
                    className="w-full flex items-center gap-3 px-4 py-3 hover:bg-navy/[0.02] transition-colors"
                  >
                    <div
                      className="w-1 h-5 rounded-full shrink-0"
                      style={{ backgroundColor: katColor }}
                    />
                    <span className="text-sm font-semibold text-navy flex-1 text-left">
                      {kat}
                    </span>
                    <span
                      className="px-2 py-0.5 text-[11px] font-semibold rounded-full min-w-[28px] text-center"
                      style={{
                        backgroundColor: `${katColor}14`,
                        color: katColor,
                      }}
                    >
                      {emails.length}
                    </span>
                    <svg
                      className={`w-4 h-4 text-text-muted transition-transform ${isExpanded ? "rotate-180" : ""}`}
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      strokeWidth={2}
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
                    </svg>
                  </button>

                  {/* Expanded content */}
                  {isExpanded && (
                    <div>
                      {/* RFQ subcategory filter */}
                      {kat === "RFQ" && emails.length > 0 && (
                        <>
                          <div className="h-px bg-navy/6" />
                          <div className="h-[42px] px-3 bg-navy/[0.02] flex items-center overflow-x-auto no-scrollbar">
                            {RFQ_PODKATEGORIJE.map((podkat) => {
                              const isSelected = selectedRfqPodkat === podkat;
                              const chipColor = getRfqChipColor(podkat);
                              return (
                                <button
                                  key={podkat}
                                  onClick={() => setSelectedRfqPodkat(podkat)}
                                  className="shrink-0 mx-1 px-3 py-1 rounded-xl text-[11px] border transition-colors"
                                  style={{
                                    fontWeight: isSelected ? 600 : 400,
                                    color: isSelected ? chipColor : "#5A6577",
                                    backgroundColor: isSelected ? `${chipColor}1A` : "transparent",
                                    borderColor: isSelected ? `${chipColor}4D` : "#1A27441A",
                                  }}
                                >
                                  {podkat}
                                </button>
                              );
                            })}
                          </div>
                        </>
                      )}

                      <div className="h-px bg-navy/6" />

                      {/* Email cards */}
                      {visibleEmails.length === 0 ? (
                        <div className="px-4 py-6 text-center text-xs text-text-muted">
                          Ni emailov v tej kategoriji
                        </div>
                      ) : (
                        <div className="p-3">
                          {visibleEmails.map((email) => (
                            <EmailCard key={email.id} email={email} />
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
