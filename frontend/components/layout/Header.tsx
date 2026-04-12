"use client";

import { useEffect, useState } from "react";
import { useApiStatus } from "@/lib/contexts/ApiStatusContext";
import { WalletConnectionButton } from "@/components/wallet/WalletConnectionButton";
import { SearchCommand } from "@/components/web3/SearchCommand";

export function Header() {
  const [mounted, setMounted] = useState(false);
  const { isBackendOnline } = useApiStatus();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <>
      {/* Google Material Symbols */}
      <link
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
        rel="stylesheet"
      />

      <header
        className="flex justify-between items-center px-8 w-full"
        style={{
          height: '5rem',
          backgroundColor: 'rgba(23,23,23,0.6)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          zIndex: 50,
          flexShrink: 0,
        }}
      >
        {/* Left: Search */}
        <div className="flex items-center gap-8">
          <SearchCommand />
        </div>

        {/* Right: Status + Icons + Wallet */}
        <div className="flex items-center gap-6">
          {/* Live Network badge */}
          <div className="flex items-center gap-2 px-4 py-2 rounded-full" style={{ backgroundColor: '#131313' }}>
            <div className={`zen-pulse ${!isBackendOnline ? 'opacity-50' : ''}`} />
            <span className="text-[10px] font-bold tracking-widest uppercase" style={{ color: '#a7cbeb' }}>
              {isBackendOnline ? 'Live Network' : 'Demo Mode'}
            </span>
          </div>

          {/* Action icons */}
          <div className="flex items-center gap-3">
            {/* Wallet Connection Button */}
            <WalletConnectionButton />

            {/* Notifications */}
            <button
              className="cursor-pointer active:scale-95 duration-300 p-2 rounded-full text-neutral-400 hover:bg-neutral-800/50 hover:text-white transition-all"
            >
              <span className="material-symbols-outlined" style={{ fontSize: '1.25rem' }}>notifications</span>
            </button>
          </div>
        </div>
      </header>
    </>
  );
}
