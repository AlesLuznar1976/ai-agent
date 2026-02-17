"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import AppBar from "@/components/layout/AppBar";
import BottomNav from "@/components/layout/BottomNav";
import LuznarLogo from "@/components/brand/LuznarLogo";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isLoading, isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-navy-dark via-navy to-navy-light flex flex-col items-center justify-center">
        <LuznarLogo size={56} withGlow />
        <div className="mt-6 border-2 border-gold/30 border-t-gold rounded-full w-6 h-6 animate-spin" />
        <p className="mt-4 text-white/70 text-[13px]">Preverjam sejo...</p>
      </div>
    );
  }

  if (!isAuthenticated) return null;

  return (
    <div className="flex flex-col h-screen bg-surface">
      <AppBar />
      <main className="flex-1 overflow-hidden">{children}</main>
      <BottomNav />
    </div>
  );
}
