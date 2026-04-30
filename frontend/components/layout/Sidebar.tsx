"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { ConnectWalletButton } from "@/components/web3/ConnectWalletButton";

const NAV_ITEMS = [
  { title: "Vault", href: "/dashboard/vault", icon: "savings" },
  { title: "Scan", href: "/dashboard/scan", icon: "radar" },
  { title: "Activity", href: "/dashboard/portfolio", icon: "history" },
  { title: "Explore", href: "/dashboard/simulation", icon: "travel_explore" },
  { title: "Research", href: "/dashboard/research", icon: "science" },
  { title: "Proof", href: "/dashboard/leaderboard", icon: "verified" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <>
      <aside className="hidden md:flex h-screen w-72 flex-col py-10 px-6 gap-8 shrink-0 relative z-50 border-r border-[rgba(255,255,255,0.02)]" style={{ backgroundColor: '#0a0a0a' }}>
        {/* Ambient lighting */}
        <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-primary/5 to-transparent pointer-events-none" />

        {/* Logo */}
        <Link href="/" className="flex items-center gap-4 px-2 group">
          <div className="relative w-10 h-10 rounded-full overflow-hidden flex items-center justify-center transition-transform duration-500 group-hover:scale-105">
            <Image 
              src="/signal_logo.svg" 
              alt="HypeScan Logo" 
              fill
              className="object-cover"
            />
          </div>
          <div>
            <h1 className="text-[1.35rem] font-bold text-white tracking-tighter" style={{ fontFamily: 'var(--font-space)' }}>HypeScan</h1>
            <p className="text-[9px] uppercase tracking-[0.2em] font-semibold text-neutral-500 mt-0.5 group-hover:text-neutral-400 transition-colors">Web3 Intelligence</p>
          </div>
        </Link>

        {/* Main nav */}
        <nav className="flex flex-col gap-2 mt-6">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href));

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "relative rounded-xl px-4 py-3.5 flex items-center gap-4 text-[13px] font-medium tracking-wide transition-all ease-out duration-300 group overflow-hidden",
                  isActive
                    ? "text-primary"
                    : "text-neutral-500 hover:text-white hover:bg-white/[0.03]"
                )}
              >
                {isActive && (
                  <div className="absolute inset-0 bg-primary/10 transition-transform" />
                )}
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[3px] h-1/2 rounded-r-full bg-primary" />
                )}
                <span className={cn(
                  "material-symbols-outlined relative z-10 transition-transform duration-300",
                  !isActive && "group-hover:scale-110",
                  isActive && "[font-variation-settings:'FILL'1]"
                )} style={{ fontSize: '1.3rem' }}>
                  {item.icon}
                </span>
                <span className="relative z-10" style={{ fontFamily: isActive ? 'var(--font-space)' : 'inherit' }}>{item.title}</span>
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        <div className="mt-auto flex flex-col gap-2 relative z-10">
          <div className="mb-6 hover:scale-[1.02] transition-transform duration-300">
            <ConnectWalletButton />
          </div>
          
          <div className="w-full h-[1px] bg-gradient-to-r from-white/[0.05] to-transparent mb-2" />

          <Link
            href="/dashboard/settings"
            className="text-neutral-500 hover:text-white rounded-xl px-4 py-3 flex items-center gap-4 text-xs font-medium tracking-wide transition-colors group"
          >
            <span className="material-symbols-outlined group-hover:rotate-45 transition-transform duration-500" style={{ fontSize: '1.2rem' }}>settings</span>
            Settings
          </Link>
          <Link
            href="#"
            className="text-neutral-500 hover:text-white rounded-xl px-4 py-3 flex items-center gap-4 text-xs font-medium tracking-wide transition-colors group"
          >
            <span className="material-symbols-outlined group-hover:scale-110 transition-transform duration-300" style={{ fontSize: '1.2rem' }}>help_outline</span>
            Support
          </Link>
        </div>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 h-[4.5rem] flex justify-around items-center px-4 border-t border-[rgba(255,255,255,0.05)]" style={{ backgroundColor: 'rgba(10,10,10,0.85)', backdropFilter: 'blur(20px)', zIndex: 100 }}>
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href || (pathname?.startsWith(item.href) ?? false);
          return (
            <Link key={item.href} href={item.href} className="flex flex-col items-center gap-1.5 p-2 rounded-xl active:scale-95 transition-transform">
              <span
                className="material-symbols-outlined transition-colors duration-300"
                style={{
                  fontSize: '1.4rem',
                  color: isActive ? 'var(--primary)' : '#737373',
                  fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0",
                }}
              >
                {item.icon}
              </span>
              <span className="text-[9px] font-bold uppercase tracking-wider" style={{ color: isActive ? 'var(--primary)' : '#737373', fontFamily: 'var(--font-space)' }}>
                {item.title}
              </span>
            </Link>
          );
        })}
      </nav>
    </>
  );
}
