import { Projekt } from "@/types/projekt";
import { formatDate, getFazaColor } from "@/lib/utils";
import Badge from "@/components/ui/Badge";

interface ProjectCardProps {
  projekt: Projekt;
}

export default function ProjectCard({ projekt }: ProjectCardProps) {
  return (
    <div className="bg-white rounded-md border border-navy/8 p-4 mb-2.5 hover:shadow-sm transition-shadow cursor-pointer">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[15px] font-bold text-navy">{projekt.stevilkaProjekta}</span>
        <Badge label={projekt.faza} color={getFazaColor(projekt.faza)} />
      </div>
      <p className="text-sm text-text-primary mb-2">{projekt.naziv}</p>
      <div className="flex items-center gap-3">
        {projekt.datumRfq && (
          <div className="flex items-center gap-1">
            <svg className="w-3.5 h-3.5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 18.75V7.5a2.25 2.25 0 012.25-2.25h13.5A2.25 2.25 0 0121 7.5v11.25m-18 0A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75m-18 0v-7.5A2.25 2.25 0 015.25 9h13.5A2.25 2.25 0 0121 11.25v7.5" />
            </svg>
            <span className="text-xs text-text-secondary">{formatDate(projekt.datumRfq)}</span>
          </div>
        )}
        <div className="flex items-center gap-1.5">
          <div
            className="w-[7px] h-[7px] rounded-full"
            style={{ backgroundColor: projekt.status === "Aktiven" ? "#2E7D4F" : "#8B95A5" }}
          />
          <span className="text-xs text-text-secondary">{projekt.status}</span>
        </div>
      </div>
    </div>
  );
}
