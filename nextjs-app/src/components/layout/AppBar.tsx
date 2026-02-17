"use client";

import { useState } from "react";
import LuznarLogo from "@/components/brand/LuznarLogo";
import { useAuth } from "@/lib/auth-context";
import LogoutDialog from "./LogoutDialog";

export default function AppBar() {
  const { user, logout } = useAuth();
  const [showLogout, setShowLogout] = useState(false);

  return (
    <>
      <header className="bg-navy h-14 px-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <LuznarLogo size={28} color="#B8963E" />
          <div className="flex flex-col">
            <span className="text-[15px] font-bold text-white tracking-wider leading-tight">
              LUZNAR
            </span>
            <span className="text-[11px] text-gold/90 tracking-wide">
              AI Agent
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {user && (
            <div className="flex items-center gap-1.5 px-3 py-1 bg-white/10 border border-white/15 rounded-xl">
              <svg className="w-4 h-4 text-gold/80" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
              </svg>
              <span className="text-white text-[13px] font-medium">{user.username}</span>
            </div>
          )}
          <button
            onClick={() => setShowLogout(true)}
            className="p-2 text-white/70 hover:text-white transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15m3 0l3-3m0 0l-3-3m3 3H9" />
            </svg>
          </button>
        </div>
      </header>

      {showLogout && (
        <LogoutDialog
          onConfirm={() => { logout(); setShowLogout(false); }}
          onCancel={() => setShowLogout(false)}
        />
      )}
    </>
  );
}
