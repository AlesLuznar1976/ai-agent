"use client";

import { useState, useEffect, useCallback } from "react";
import { Projekt } from "@/types/projekt";
import { apiGetProjekti } from "@/lib/api";
import FilterChipBar from "@/components/ui/FilterChipBar";
import Spinner from "@/components/ui/Spinner";
import ErrorState from "@/components/ui/ErrorState";
import EmptyState from "@/components/ui/EmptyState";
import ProjectCard from "@/components/projects/ProjectCard";

const FAZE = [
  "Vse",
  "RFQ",
  "Ponudba",
  "Naročilo",
  "Tehnologija",
  "Nabava",
  "Proizvodnja",
  "Dostava",
  "Zaključek",
];

export default function ProjektiPage() {
  const [projekti, setProjekti] = useState<Projekt[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFaza, setSelectedFaza] = useState("Vse");

  const loadProjekti = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await apiGetProjekti(
        selectedFaza !== "Vse" ? { faza: selectedFaza } : undefined
      );
      setProjekti(data);
    } catch {
      setError("Napaka pri pridobivanju projektov");
    } finally {
      setIsLoading(false);
    }
  }, [selectedFaza]);

  useEffect(() => {
    loadProjekti();
  }, [loadProjekti]);

  return (
    <div className="flex flex-col h-full bg-surface">
      <FilterChipBar
        items={FAZE}
        selected={selectedFaza}
        onSelect={setSelectedFaza}
      />
      <div className="h-px bg-navy/6" />

      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center h-full">
            <Spinner />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={loadProjekti} />
        ) : projekti.length === 0 ? (
          <EmptyState
            icon={
              <svg className="w-12 h-12" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776" />
              </svg>
            }
            message="Ni projektov"
          />
        ) : (
          <div className="p-3">
            {projekti.map((p) => (
              <ProjectCard key={p.id} projekt={p} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
