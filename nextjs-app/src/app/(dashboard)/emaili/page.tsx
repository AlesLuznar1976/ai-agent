"use client";

import { useState, useEffect, useMemo } from "react";
import { Email } from "@/types/email";
import { apiGetEmaili } from "@/lib/api";
import { getRfqSubcategoryColor } from "@/lib/utils";
import FilterChipBar from "@/components/ui/FilterChipBar";
import Spinner from "@/components/ui/Spinner";
import ErrorState from "@/components/ui/ErrorState";
import EmptyState from "@/components/ui/EmptyState";
import EmailCard from "@/components/emails/EmailCard";

const STATUSI = ["Vse", "Končano", "Čaka", "V obdelavi", "Napaka", "Brez"];

const PREDALI = [
  "Vsi", "ales", "info", "spela", "nabava", "tehnolog",
  "martina", "oddaja", "anela", "cam", "matej", "prevzem", "skladisce",
];

const RFQ_PODKATEGORIJE = ["Vse RFQ", "Kompletno", "Nepopolno", "Povpraševanje", "Repeat Order"];

export default function EmailiPage() {
  const [vsiEmaili, setVsiEmaili] = useState<Email[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedStatus, setSelectedStatus] = useState("Vse");
  const [selectedMailbox, setSelectedMailbox] = useState("Vsi");
  const [selectedRfqPodkat, setSelectedRfqPodkat] = useState("Vse RFQ");

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

  const hasRfq = useMemo(
    () => vsiEmaili.some((e) => e.kategorija === "RFQ"),
    [vsiEmaili]
  );

  const filteredEmaili = useMemo(() => {
    let filtered = vsiEmaili;

    // Status filter
    if (selectedStatus !== "Vse") {
      filtered = filtered.filter(
        (e) => (e.analizaStatus || "Brez") === selectedStatus
      );
    }

    // Mailbox filter
    if (selectedMailbox !== "Vsi") {
      filtered = filtered.filter((e) => {
        const m = (e.izvleceniPodatki?.mailbox as string) || "";
        return m === `${selectedMailbox}@luznar.com` || m === selectedMailbox;
      });
    }

    // RFQ subcategory filter
    if (selectedRfqPodkat !== "Vse RFQ") {
      filtered = filtered.filter(
        (e) => e.kategorija === "RFQ" && e.rfqPodkategorija === selectedRfqPodkat
      );
    }

    return filtered;
  }, [vsiEmaili, selectedStatus, selectedMailbox, selectedRfqPodkat]);

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

      {/* Mailbox filter */}
      <FilterChipBar
        items={PREDALI}
        selected={selectedMailbox}
        onSelect={setSelectedMailbox}
        accentColor="#B8963E"
        showIcon
      />
      <div className="h-px bg-navy/6" />

      {/* RFQ subcategory filter (only when RFQ emails exist) */}
      {hasRfq && (
        <>
          <div className="h-[46px] px-3 bg-white flex items-center overflow-x-auto no-scrollbar">
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
          <div className="h-px bg-navy/6" />
        </>
      )}

      {/* Email list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Spinner />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={loadEmaili} />
        ) : filteredEmaili.length === 0 ? (
          <EmptyState
            icon={
              <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75" />
              </svg>
            }
            message="Ni emailov"
          />
        ) : (
          <div className="p-3">
            {filteredEmaili.map((email) => (
              <EmailCard key={email.id} email={email} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
