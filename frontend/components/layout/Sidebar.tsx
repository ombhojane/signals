"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { title: "Intelligence", href: "/dashboard", icon: "insights" },
  { title: "Portfolio", href: "/dashboard/portfolio", icon: "account_balance" },
  { title: "Signals", href: "/dashboard/simulation", icon: "sensors" },
  { title: "Market", href: "/dashboard/leaderboard", icon: "analytics" },
  { title: "Curator", href: "/dashboard/models", icon: "auto_awesome" },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <>
      {/* Google Material Symbols font */}
      <link
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
        rel="stylesheet"
      />

      <aside className="hidden md:flex h-screen w-72 flex-col py-10 px-6 gap-8 shrink-0" style={{ backgroundColor: 'rgb(3, 7, 18)', borderRadius: '0 1.5rem 1.5rem 0' }}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-2">
          <div className="w-10 h-10 rounded-full flex items-center justify-center" style={{ backgroundColor: '#254a65' }}>
            <span
              className="material-symbols-outlined"
              style={{ color: '#a7cbeb', fontVariationSettings: "'FILL' 1" }}
            >
              auto_awesome
            </span>
          </div>
          <div>
            <h1 className="text-lg font-black text-neutral-100 tracking-tighter">Signals Zen</h1>
            <p className="text-[10px] uppercase tracking-widest font-medium" style={{ color: '#acabaa' }}>Web3 Intelligence</p>
          </div>
        </div>

        {/* Main nav */}
        <nav className="flex flex-col gap-1 mt-4">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/dashboard" && pathname?.startsWith(item.href));

            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "rounded-full px-6 py-3 flex items-center gap-4 text-sm font-medium tracking-wide transition-all ease-in-out duration-200",
                  isActive
                    ? "text-[#b1d4f5]"
                    : "text-neutral-500 hover:text-neutral-300 hover:bg-neutral-900"
                )}
                style={isActive ? { backgroundColor: 'rgb(38,38,38)' } : undefined}
              >
                <span className="material-symbols-outlined" style={{ fontSize: '1.25rem' }}>{item.icon}</span>
                {item.title}
              </Link>
            );
          })}
        </nav>

        {/* Bottom section */}
        <div className="mt-auto flex flex-col gap-1">
          <button
            className="rounded-full px-6 py-4 font-bold text-sm tracking-tight mb-4 active:scale-95 duration-300 transition-all"
            style={{ backgroundColor: '#a7cbeb', color: '#1e435e' }}
          >
            Connect Wallet
          </button>
          <Link
            href="/dashboard/settings"
            className="text-neutral-600 hover:text-neutral-300 hover:bg-neutral-900 rounded-full px-6 py-3 flex items-center gap-4 text-xs uppercase tracking-[0.2em] transition-all"
          >
            <span className="material-symbols-outlined" style={{ fontSize: '1.1rem' }}>settings</span>
            Settings
          </Link>
          <Link
            href="#"
            className="text-neutral-600 hover:text-neutral-300 hover:bg-neutral-900 rounded-full px-6 py-3 flex items-center gap-4 text-xs uppercase tracking-[0.2em] transition-all"
          >
            <span className="material-symbols-outlined" style={{ fontSize: '1.1rem' }}>help_outline</span>
            Support
          </Link>
        </div>
      </aside>

      {/* Mobile bottom nav */}
      <nav className="md:hidden fixed bottom-0 left-0 right-0 h-16 flex justify-around items-center px-4 z-[100]" style={{ backgroundColor: 'rgba(0,0,0,0.9)', backdropFilter: 'blur(20px)' }}>
        {NAV_ITEMS.slice(0, 4).map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link key={item.href} href={item.href} className="flex flex-col items-center gap-1">
              <span
                className="material-symbols-outlined"
                style={{
                  fontSize: '1.25rem',
                  color: isActive ? '#b1d4f5' : '#737373',
                  fontVariationSettings: isActive ? "'FILL' 1" : "'FILL' 0",
                }}
              >
                {item.icon}
              </span>
              <span className="text-[8px] font-bold uppercase" style={{ color: isActive ? '#b1d4f5' : '#737373' }}>
                {item.title.slice(0, 4)}
              </span>
            </Link>
          );
        })}
        <Link href="/dashboard/models" className="flex flex-col items-center gap-1">
          <span className="material-symbols-outlined" style={{ fontSize: '1.25rem', color: '#737373' }}>auto_awesome</span>
          <span className="text-[8px] font-bold uppercase text-neutral-500">Zen</span>
        </Link>
      </nav>
    </>
  );
}
