"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { 
  LayoutDashboard, 
  Trophy, 
  Settings, 
  LineChart, 
  Bot,
  LogOut,
  PlayCircle
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  {
    title: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    title: "Scan",
    href: "/simulation",
    icon: PlayCircle,
  },
  {
    title: "Leaderboard",
    href: "/leaderboard",
    icon: Trophy,
  },
  {
    title: "Models",
    href: "/models",
    icon: Bot,
  },
  {
    title: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-screen w-64 flex-col border-r border-border bg-sidebar text-sidebar-foreground">
      <div className="flex h-16 items-center border-b border-border px-6">
        <Link href="/" className="flex items-center gap-2 font-bold text-xl tracking-tight">
          <LineChart className="h-6 w-6 text-primary" />
          <span>Signals</span>
        </Link>
      </div>
      
      <div className="flex-1 overflow-y-auto py-6">
        <nav className="grid gap-1 px-4">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
            
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors duration-150",
                  isActive 
                    ? "bg-sidebar-accent text-sidebar-accent-foreground border-l-2 border-primary" 
                    : "text-muted-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground border-l-2 border-transparent"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.title}
              </Link>
            );
          })}
        </nav>
      </div>
      
      <div className="border-t border-border p-4">
        <button className="flex w-full items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium text-muted-foreground transition-colors hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground">
          <LogOut className="h-4 w-4" />
          Disconnect
        </button>
      </div>
    </div>
  );
}
