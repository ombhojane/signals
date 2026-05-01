"use client";

import { useEffect, useState } from "react";
import { useApiStatus } from "@/lib/contexts/ApiStatusContext";
import { WalletConnectionButton } from "@/components/wallet/WalletConnectionButton";
import { SearchCommand } from "@/components/web3/SearchCommand";
import { useSidebar } from "@/lib/sidebar-context";
import { ThemeToggle } from "@/components/ui/ThemeToggle";

export function Header() {
  const [mounted, setMounted] = useState(false);
  const { isBackendOnline } = useApiStatus();
  const [scrolled, setScrolled] = useState(false);
  const { toggle: toggleSidebar, isOpen: sidebarOpen } = useSidebar();

  useEffect(() => {
    setMounted(true);
    const handleScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  if (!mounted) return null;

  return (
    <header
      className={`flex justify-between items-center px-4 md:px-8 w-full sticky top-0 transition-all duration-300 z-50 backdrop-blur-xl ${
        scrolled ? "bg-background/70 shadow-[0_4px_30px_rgba(0,0,0,0.1)] dark:shadow-[0_4px_30px_rgba(0,0,0,0.5)] border-b border-border/50" : "bg-transparent"
      }`}
      style={{
        height: '5.5rem',
        flexShrink: 0,
      }}
    >
      {/* Left: Mobile Logo & Search */}
      <div className="flex items-center gap-3 flex-1 min-w-0 pr-2">
        {/* Sidebar Toggle */}
        <button
          onClick={toggleSidebar}
          className="hidden md:flex items-center justify-center w-10 h-10 rounded-full text-muted-foreground hover:text-foreground hover:bg-black/5 dark:hover:bg-white/10 transition-all active:scale-95 cursor-pointer"
        >
          <span className="material-symbols-outlined text-[1.3rem]">
            {sidebarOpen ? "menu_open" : "menu"}
          </span>
        </button>
        {/* Mobile Logo */}
        <div className="flex md:hidden items-center shrink-0">
          <img src="/signal_logo.svg" alt="Signals" className="w-8 h-8 rounded-full" />
        </div>
        {/* Search */}
        <div className="flex-1 min-w-0 flex items-center">
          <SearchCommand />
        </div>
      </div>

      {/* Right: Status + Icons + Wallet */}
      <div className="flex items-center gap-3 md:gap-6 shrink-0">
        {/* Action icons */}
        <div className="flex items-center gap-2">
          {/* Theme Toggle */}
          {/* <ThemeToggle /> */}

          {/* Notifications (Hidden on mobile) */}
          <button
            className="relative hidden md:flex items-center justify-center w-10 h-10 rounded-full text-muted-foreground hover:text-foreground hover:bg-black/5 dark:hover:bg-white/10 transition-all active:scale-95 group cursor-pointer"
          >
            <span className="material-symbols-outlined text-[1.3rem] group-hover:scale-110 transition-transform">notifications</span>
            {/* Notification Dot indicator */}
            <span className="absolute top-2.5 right-2.5 w-2 h-2 rounded-full bg-primary ring-2 ring-background"></span>
          </button>
          
          <div className="hidden md:block w-[1px] h-6 bg-border mx-2" />

          {/* Wallet Connection Button */}
          <div className="hover:scale-[1.02] active:scale-95 transition-transform duration-200">
            <WalletConnectionButton />
          </div>
        </div>
      </div>
    </header>
  );
}
