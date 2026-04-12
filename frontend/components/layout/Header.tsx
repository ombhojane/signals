"use client";

import { useEffect, useState } from "react";
import { useApiStatus } from "@/lib/contexts/ApiStatusContext";
import { WalletConnectionButton } from "@/components/wallet/WalletConnectionButton";
import { SearchCommand } from "@/components/web3/SearchCommand";

export function Header() {
  const [mounted, setMounted] = useState(false);
  const { isBackendOnline } = useApiStatus();
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    setMounted(true);
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  if (!mounted) return null;

  return (
    <header
      className={`flex justify-between items-center px-8 w-full sticky top-0 transition-all duration-300 z-50 ${
        scrolled ? "nav-glass shadow-[0_4px_30px_rgba(0,0,0,0.5)] border-b border-[rgba(255,255,255,0.02)]" : "bg-transparent"
      }`}
      style={{
        height: '5.5rem',
        flexShrink: 0,
      }}
    >
      {/* Left: Search */}
      <div className="flex items-center gap-8 w-full max-w-md">
        <SearchCommand />
      </div>

      {/* Right: Status + Icons + Wallet */}
      <div className="flex items-center gap-6">
        {/* Action icons */}
        <div className="flex items-center gap-2">
          {/* Notifications */}
          <button
            className="relative flex items-center justify-center w-10 h-10 rounded-full text-neutral-400 hover:text-white hover:bg-neutral-800/80 transition-all active:scale-95 group"
          >
            <span className="material-symbols-outlined text-[1.3rem] group-hover:scale-110 transition-transform">notifications</span>
            {/* Notification Dot indicator */}
            <span className="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-primary ring-2 ring-[#0e0e0e]"></span>
          </button>
          
          <div className="w-[1px] h-6 bg-neutral-800 mx-2" />

          {/* Wallet Connection Button */}
          <div className="hover:scale-[1.02] active:scale-95 transition-transform duration-200">
            <WalletConnectionButton />
          </div>
        </div>
      </div>
    </header>
  );
}
