"use client";

import { useState, useEffect, use } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ProjektFull } from "@/types/projekt";
import { Email } from "@/types/email";
import { apiGetProjektFull } from "@/lib/api";
import { formatDate, formatDateTime, getFazaColor, getPrioritetaColor } from "@/lib/utils";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import { SectionCard, InfoRow } from "@/components/ui/SectionCard";

export default function ProjektDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const router = useRouter();
  const [data, setData] = useState<ProjektFull | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const result = await apiGetProjektFull(Number(id));
        setData(result);
      } catch {
        // ignore
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [id]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Spinner />
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex flex-col items-center justify-center h-full">
        <p className="text-text-secondary">Projekt ni najden</p>
        <button onClick={() => router.back()} className="mt-4 text-sm text-navy underline">
          Nazaj
        </button>
      </div>
    );
  }

  const { projekt, emaili, casovnica } = data;

  // Get analysis from first email with analysis
  const emailWithAnalysis = emaili.find((e) => e.analizaRezultat);
  const rezultat = emailWithAnalysis?.analizaRezultat as Record<string, unknown> | undefined;
  const stranka = rezultat?.stranka as Record<string, string> | undefined;
  const izdelki = rezultat?.izdelki as Array<Record<string, unknown>> | undefined;
  const podano = rezultat?.podano_od_stranke as string[] | undefined;
  const manjkajoci = rezultat?.manjkajoci_podatki as string[] | undefined;
  const povzetek = rezultat?.povzetek as string | undefined;
  const prioriteta = rezultat?.prioriteta as string | undefined;
  const koraki = rezultat?.priporoceni_naslednji_koraki as string[] | undefined;

  return (
    <div className="h-full overflow-y-auto bg-surface">
      {/* Header */}
      <div className="sticky top-0 z-10 bg-navy px-4 py-3 flex items-center gap-3">
        <button onClick={() => router.back()} className="text-white/80 hover:text-white">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
        </button>
        <h1 className="text-white text-sm font-medium truncate flex-1">
          {projekt.stevilkaProjekta}: {projekt.naziv}
        </h1>
      </div>

      <div className="p-4 space-y-3">
        {/* Projekt info card */}
        <SectionCard title="Projekt info" icon="info">
          <InfoRow label="Številka" value={projekt.stevilkaProjekta} />
          <InfoRow label="Naziv" value={projekt.naziv} />
          <div className="flex items-center gap-2 mb-1">
            <span className="w-20 text-[13px] text-text-muted shrink-0">Faza</span>
            <Badge label={projekt.faza} color={getFazaColor(projekt.faza)} />
          </div>
          <div className="flex items-center gap-2 mb-1">
            <span className="w-20 text-[13px] text-text-muted shrink-0">Status</span>
            <div className="flex items-center gap-1.5">
              <div
                className="w-[7px] h-[7px] rounded-full"
                style={{ backgroundColor: projekt.status === "Aktiven" ? "#2E7D4F" : "#8B95A5" }}
              />
              <span className="text-[13px] text-text-primary">{projekt.status}</span>
            </div>
          </div>
          <InfoRow label="Datum RFQ" value={formatDate(projekt.datumRfq)} />
          {projekt.datumZakljucka && (
            <InfoRow label="Zaključek" value={formatDate(projekt.datumZakljucka)} />
          )}
          {projekt.opombe && (
            <div className="mt-2 pt-2 border-t border-navy/6">
              <p className="text-[13px] text-text-secondary leading-relaxed">{projekt.opombe}</p>
            </div>
          )}
        </SectionCard>

        {/* Analysis sections - from first email */}
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

            {/* Povzetek + Koraki */}
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
                    <Badge label={prioriteta} color={getPrioritetaColor(prioriteta)} />
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

        {/* Povezani emaili */}
        {emaili.length > 0 && (
          <SectionCard title={`Povezani emaili (${emaili.length})`} icon="email">
            {emaili.map((email, idx) => (
              <Link key={email.id} href={`/emaili/${email.id}`}>
                <div className={`${idx > 0 ? "mt-2 pt-2 border-t border-navy/6" : ""} hover:bg-surface/50 rounded -mx-1 px-1 py-1 transition-colors`}>
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="text-[13px] font-medium text-navy truncate flex-1 mr-2">
                      {email.zadeva || "(brez zadeve)"}
                    </span>
                    {email.analizaStatus && (
                      <span className={`text-[10px] px-1.5 py-0.5 rounded shrink-0 ${
                        email.analizaStatus === "Končano"
                          ? "text-success bg-success/8"
                          : "text-text-muted bg-navy/5"
                      }`}>
                        {email.analizaStatus}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-text-secondary truncate">{email.posiljatelj}</span>
                    {email.datum && (
                      <span className="text-xs text-text-muted shrink-0">{formatDate(email.datum)}</span>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </SectionCard>
        )}

        {/* Časovnica */}
        {casovnica.length > 0 && (
          <SectionCard title="Časovnica" icon="timeline">
            <div className="relative">
              {casovnica.map((event, idx) => (
                <div key={event.id} className="flex gap-3 mb-3 last:mb-0">
                  {/* Timeline dot + line */}
                  <div className="flex flex-col items-center">
                    <div className="w-2 h-2 rounded-full bg-gold mt-1.5 shrink-0" />
                    {idx < casovnica.length - 1 && (
                      <div className="w-px flex-1 bg-navy/10 mt-1" />
                    )}
                  </div>
                  {/* Content */}
                  <div className="flex-1 pb-1">
                    <p className="text-[13px] font-medium text-navy">{event.dogodek}</p>
                    <p className="text-xs text-text-secondary">{event.opis}</p>
                    {(event.staraVrednost || event.novaVrednost) && (
                      <p className="text-xs text-text-muted mt-0.5">
                        {event.staraVrednost && <span className="line-through">{event.staraVrednost}</span>}
                        {event.staraVrednost && event.novaVrednost && " → "}
                        {event.novaVrednost && <span className="font-medium">{event.novaVrednost}</span>}
                      </p>
                    )}
                    <div className="flex items-center gap-2 mt-0.5">
                      <span className="text-[11px] text-text-muted">{formatDateTime(event.datum)}</span>
                      <span className="text-[11px] text-text-muted">•</span>
                      <span className="text-[11px] text-text-muted">{event.uporabnikAliAgent}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </SectionCard>
        )}
      </div>
    </div>
  );
}
