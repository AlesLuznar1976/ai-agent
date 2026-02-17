"use client";

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import { Email } from "@/types/email";
import { apiGetEmaili, apiGetEmailAnalysis, apiTriggerAnalysis } from "@/lib/api";
import { formatDateTime, getStatusColor, getRfqSubcategoryColor } from "@/lib/utils";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";

export default function EmailDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [email, setEmail] = useState<Email | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadEmail = async () => {
      try {
        const emaili = await apiGetEmaili();
        const found = emaili.find((e) => e.id === Number(id));
        if (found) {
          setEmail(found);
          // Fetch analysis if completed but no result loaded
          if (found.analizaStatus === "Končano" && !found.analizaRezultat) {
            try {
              const analysis = await apiGetEmailAnalysis(found.id);
              setEmail((prev) =>
                prev ? { ...prev, analizaStatus: "Končano", analizaRezultat: analysis } : prev
              );
            } catch {
              // ignore
            }
          }
        }
      } catch {
        // ignore
      } finally {
        setIsLoading(false);
      }
    };
    loadEmail();
  }, [id]);

  const triggerAnalysis = async () => {
    if (!email) return;
    setIsAnalyzing(true);
    try {
      const result = await apiTriggerAnalysis(email.id);
      setEmail((prev) =>
        prev
          ? {
              ...prev,
              analizaStatus: "Končano",
              analizaRezultat: result,
            }
          : prev
      );
    } catch {
      // ignore
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner />
      </div>
    );
  }

  if (!email) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-text-secondary">Email ni najden</p>
        <button onClick={() => router.back()} className="mt-4 text-sm text-navy underline">
          Nazaj
        </button>
      </div>
    );
  }

  const rezultat = email.analizaRezultat as Record<string, unknown> | undefined;
  const stranka = rezultat?.stranka as Record<string, string> | undefined;
  const izdelki = rezultat?.izdelki as Array<Record<string, unknown>> | undefined;
  const dokumenti = rezultat?.prilozeni_dokumenti as Array<Record<string, string>> | undefined;
  const podano = rezultat?.podano_od_stranke as string[] | undefined;
  const manjkajoci = rezultat?.manjkajoci_podatki as string[] | undefined;
  const povzetek = rezultat?.povzetek as string | undefined;
  const prioriteta = rezultat?.prioriteta as string | undefined;
  const koraki = rezultat?.priporoceni_naslednji_koraki as string[] | undefined;

  return (
    <div className="h-full overflow-y-auto bg-surface">
      {/* Back button */}
      <div className="sticky top-0 z-10 bg-navy px-4 py-3 flex items-center gap-3">
        <button onClick={() => router.back()} className="text-white/80 hover:text-white">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
        </button>
        <h1 className="text-white text-sm font-medium truncate flex-1">
          {email.zadeva || "(brez zadeve)"}
        </h1>
      </div>

      <div className="p-4 space-y-3">
        {/* Header card */}
        <div className="bg-white rounded-md border border-navy/8 p-4">
          <div className="flex items-center gap-2 mb-2">
            <svg className="w-4 h-4 text-text-muted shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
            </svg>
            <span className="text-sm">{email.posiljatelj}</span>
          </div>
          {email.datum && (
            <div className="flex items-center gap-2 mb-3">
              <svg className="w-4 h-4 text-text-muted shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
              </svg>
              <span className="text-[13px] text-text-secondary">{formatDateTime(email.datum)}</span>
            </div>
          )}

          <div className="flex items-center gap-2 flex-wrap mb-3">
            {email.kategorija && (
              <Badge label={email.kategorija} color="#1A2744" />
            )}
            {email.rfqPodkategorija && (
              <Badge
                label={email.rfqPodkategorija}
                color={getRfqSubcategoryColor(email.rfqPodkategorija)}
              />
            )}
            <Badge
              label={email.analizaStatus || "Brez"}
              color={getStatusColor(email.analizaStatus)}
            />
            {email.priloge && email.priloge.length > 0 && (
              <div className="flex items-center gap-1 ml-auto">
                <svg className="w-4 h-4 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
                </svg>
                <span className="text-xs text-text-muted">{email.priloge.length}</span>
              </div>
            )}
          </div>

          {email.analizaStatus !== "Končano" && (
            <button
              onClick={triggerAnalysis}
              disabled={isAnalyzing}
              className="w-full py-2.5 bg-navy text-white rounded-sm text-sm font-semibold flex items-center justify-center gap-2 hover:bg-navy-light transition-colors disabled:opacity-50"
            >
              {isAnalyzing ? (
                <>
                  <div className="border-2 border-white/30 border-t-white rounded-full w-4 h-4 animate-spin" />
                  Analiziranje...
                </>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                  </svg>
                  Analiziraj
                </>
              )}
            </button>
          )}
        </div>

        {/* Analysis sections */}
        {rezultat && (
          <>
            {/* Stranka */}
            {stranka && (
              <SectionCard title="Stranka" icon="business">
                <InfoRow label="Ime" value={stranka.ime} />
                <InfoRow label="Kontakt" value={stranka.kontakt} />
                <InfoRow label="Email" value={stranka.email} />
              </SectionCard>
            )}

            {/* Izdelki */}
            {izdelki && izdelki.length > 0 && (
              <SectionCard title="Izdelki" icon="inventory">
                {izdelki.map((item, idx) => (
                  <div key={idx}>
                    {idx > 0 && <div className="h-px bg-navy/6 my-2" />}
                    <p className="text-sm font-semibold text-navy mb-1">
                      {item.naziv as string}
                    </p>
                    {item.kolicina ? (
                      <InfoRow label="Količina" value={String(item.kolicina)} />
                    ) : null}
                    {item.specifikacije
                      ? Object.entries(item.specifikacije as Record<string, string>).map(
                          ([key, val]) => <InfoRow key={key} label={key} value={val} />
                        )
                      : null}
                  </div>
                ))}
              </SectionCard>
            )}

            {/* Dokumenti */}
            {dokumenti && dokumenti.length > 0 && (
              <SectionCard title="Dokumenti" icon="description">
                {dokumenti.map((doc, idx) => (
                  <div key={idx} className={idx > 0 ? "mt-3" : ""}>
                    <div className="flex items-center gap-2">
                      <svg className="w-4 h-4 text-text-muted shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                      </svg>
                      <span className="text-sm font-medium">{doc.ime}</span>
                      {doc.tip && (
                        <span className="px-1.5 py-0.5 text-[10px] text-info bg-info/8 rounded">
                          {doc.tip}
                        </span>
                      )}
                    </div>
                    {doc.vsebina_povzetek && (
                      <p className="text-xs text-text-secondary mt-1 ml-6">
                        {doc.vsebina_povzetek}
                      </p>
                    )}
                  </div>
                ))}
              </SectionCard>
            )}

            {/* Podano vs Manjkajoče */}
            {((podano && podano.length > 0) || (manjkajoci && manjkajoci.length > 0)) && (
              <SectionCard title="Podano vs Manjkajoče" icon="checklist">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-xs font-semibold text-success mb-2">Podano</p>
                    {podano?.map((item, idx) => (
                      <div key={idx} className="flex items-start gap-1.5 mb-1.5">
                        <svg className="w-3.5 h-3.5 text-success shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-xs text-text-primary">{item}</span>
                      </div>
                    ))}
                  </div>
                  <div>
                    <p className="text-xs font-semibold text-error mb-2">Manjkajoče</p>
                    {manjkajoci?.map((item, idx) => (
                      <div key={idx} className="flex items-start gap-1.5 mb-1.5">
                        <svg className="w-3.5 h-3.5 text-error shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 9.75l4.5 4.5m0-4.5l-4.5 4.5M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-xs text-text-primary">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </SectionCard>
            )}

            {/* Povzetek */}
            {(povzetek || prioriteta || (koraki && koraki.length > 0)) && (
              <SectionCard title="Povzetek" icon="summarize">
                {povzetek && (
                  <p className="text-[13px] leading-relaxed text-text-primary mb-3">
                    {povzetek}
                  </p>
                )}
                {prioriteta && (
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xs text-text-muted">Prioriteta:</span>
                    <Badge
                      label={prioriteta}
                      color={
                        prioriteta === "Visoka"
                          ? "#C53030"
                          : prioriteta === "Srednja"
                          ? "#B8963E"
                          : "#2E7D4F"
                      }
                    />
                  </div>
                )}
                {koraki && koraki.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-text-secondary mb-2">
                      Priporočeni naslednji koraki:
                    </p>
                    {koraki.map((korak, idx) => (
                      <div key={idx} className="flex items-start gap-2 mb-1.5">
                        <span className="w-[22px] text-xs text-text-muted text-right shrink-0">
                          {idx + 1}.
                        </span>
                        <span className="text-[13px] text-text-primary">{korak}</span>
                      </div>
                    ))}
                  </div>
                )}
              </SectionCard>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// Helper components

function SectionCard({
  title,
  icon,
  children,
}: {
  title: string;
  icon: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-md border border-navy/8 p-4">
      <div className="flex items-center gap-2 mb-3">
        <SectionIcon name={icon} />
        <h3 className="text-sm font-semibold text-navy">{title}</h3>
      </div>
      {children}
    </div>
  );
}

function SectionIcon({ name }: { name: string }) {
  const cls = "w-5 h-5 text-gold";
  switch (name) {
    case "business":
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5M3.75 3v18h16.5V3H3.75zm3.75 3.75h3m-3 3.75h3m-3 3.75h3m6-7.5h3m-3 3.75h3m-3 3.75h3" /></svg>;
    case "inventory":
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" /></svg>;
    case "description":
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" /></svg>;
    case "checklist":
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M11.35 3.836c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m8.9-4.414c.376.023.75.05 1.124.08 1.131.094 1.976 1.057 1.976 2.192V16.5A2.25 2.25 0 0118 18.75h-2.25m-7.5-10.5H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V18.75m-7.5-10.5h6.375c.621 0 1.125.504 1.125 1.125v9.375m-8.25-3l1.5 1.5 3-3.75" /></svg>;
    case "summarize":
      return <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}><path strokeLinecap="round" strokeLinejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z" /></svg>;
    default:
      return null;
  }
}

function InfoRow({ label, value }: { label: string; value?: string }) {
  if (!value) return null;
  return (
    <div className="flex items-baseline gap-2 mb-1">
      <span className="w-20 text-[13px] text-text-muted shrink-0">{label}</span>
      <span className="text-[13px] text-text-primary">{value}</span>
    </div>
  );
}
