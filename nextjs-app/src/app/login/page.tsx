"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import LuznarLogo from "@/components/brand/LuznarLogo";
import GoldAccentLine from "@/components/brand/GoldAccentLine";
import DiamondPattern from "@/components/brand/DiamondPattern";
import { useAuth } from "@/lib/auth-context";

export default function LoginPage() {
  const router = useRouter();
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) router.replace("/chat");
  }, [isAuthenticated, router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !password) return;

    setError(null);
    setIsLoading(true);
    const success = await login(username, password);
    setIsLoading(false);

    if (success) {
      router.replace("/chat");
    } else {
      setError("Napačno uporabniško ime ali geslo");
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-navy-dark via-navy to-navy-light flex flex-col items-center justify-center">
        <LuznarLogo size={56} withGlow />
        <div className="mt-6 border-2 border-gold/30 border-t-gold rounded-full w-6 h-6 animate-spin" />
        <p className="mt-4 text-white/70 text-[13px]">Preverjam sejo...</p>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen bg-gradient-to-b from-navy-dark via-navy to-navy-light flex flex-col items-center justify-center px-6">
      <DiamondPattern />

      <div className="relative z-10 flex flex-col items-center animate-fade-in">
        <LuznarLogo size={72} withGlow />
        <h1 className="mt-4 text-2xl font-bold text-white tracking-[1.5px]">LUZNAR</h1>
        <p className="mt-1 text-[13px] text-gold tracking-[2px]">ELECTRONICS</p>
        <div className="mt-3">
          <GoldAccentLine width={48} />
        </div>

        <div className="mt-8 w-full max-w-[400px] bg-white rounded-md shadow-lg p-8">
          <h2 className="text-[22px] font-semibold text-navy text-center">Prijava</h2>
          <p className="text-[13px] text-text-muted text-center mt-1 mb-6">AI Agent ERP System</p>

          {error && (
            <div className="mb-4 px-3 py-2.5 bg-error/5 border border-error/20 rounded-sm flex items-center gap-2">
              <svg className="w-4 h-4 text-error shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
              </svg>
              <span className="text-error text-sm">{error}</span>
            </div>
          )}

          <form onSubmit={handleLogin}>
            <label className="block text-[11px] font-semibold text-text-muted tracking-wider mb-1.5">
              UPORABNIŠKO IME
            </label>
            <div className="relative mb-4">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
              </svg>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Vnesite uporabniško ime"
                className="w-full pl-10 pr-4 py-3 bg-white border border-navy/15 rounded-sm text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-navy focus:ring-1 focus:ring-navy/30"
              />
            </div>

            <label className="block text-[11px] font-semibold text-text-muted tracking-wider mb-1.5">
              GESLO
            </label>
            <div className="relative mb-6">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Vnesite geslo"
                className="w-full pl-4 pr-10 py-3 bg-white border border-navy/15 rounded-sm text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-navy focus:ring-1 focus:ring-navy/30"
                onKeyDown={(e) => e.key === "Enter" && handleLogin(e)}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-text-muted hover:text-text-secondary"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  {showPassword ? (
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                  ) : (
                    <>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                    </>
                  )}
                </svg>
              </button>
            </div>

            <button
              type="submit"
              disabled={isLoading || authLoading}
              className="w-full h-12 bg-navy text-white rounded-sm text-[15px] font-semibold tracking-wide hover:bg-navy-light transition-colors disabled:opacity-50"
            >
              {isLoading ? (
                <div className="flex items-center justify-center gap-2">
                  <div className="border-2 border-white/30 border-t-white rounded-full w-5 h-5 animate-spin" />
                </div>
              ) : (
                "Prijava"
              )}
            </button>
          </form>

          <p className="text-center text-[11px] text-text-muted mt-4">
            Privzeto: admin / admin123
          </p>
        </div>

        <p className="mt-8 text-[11px] text-white/40">Luznar Electronics d.o.o.</p>
        <p className="mt-1 text-[10px] text-white/25">Hrastje 52g, SI-4000 Kranj</p>
      </div>
    </div>
  );
}
