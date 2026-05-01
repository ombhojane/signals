"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { explorerAddress, explorerTx } from "@/lib/web3/constants";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";

type ResultKind = "page" | "address" | "tx" | "external";

interface Result {
  id: string;
  kind: ResultKind;
  icon: string;
  title: string;
  description: string;
  onSelect: () => void;
}

const PAGES = [
  {
    title: "Vault",
    href: "/dashboard/vault",
    icon: "savings",
    description: "Deposit, withdraw, manage your position",
    keywords: ["vault", "deposit", "withdraw", "position", "usdc", "home"],
  },
  {
    title: "Activity",
    href: "/dashboard/portfolio",
    icon: "history",
    description: "Your personal deposits, withdrawals & P&L",
    keywords: ["activity", "portfolio", "history", "pnl", "deposits", "withdrawals"],
  },
  {
    title: "Explore",
    href: "/dashboard/simulation",
    icon: "travel_explore",
    description: "Token scanner · signal playground",
    keywords: ["explore", "simulation", "Signals", "scan", "tokens", "analyze"],
  },
  {
    title: "Proof",
    href: "/dashboard/leaderboard",
    icon: "verified",
    description: "On-chain trade feed · x402 signal API",
    keywords: ["proof", "leaderboard", "market", "trades", "x402", "api"],
  },
  {
    title: "Settings",
    href: "/dashboard/settings",
    icon: "settings",
    description: "Theme · wallet · contract info",
    keywords: ["settings", "preferences", "theme", "wallet"],
  },
];

function isAddress(s: string): boolean {
  return /^0x[a-fA-F0-9]{40}$/.test(s.trim());
}

function isHash32(s: string): boolean {
  return /^0x[a-fA-F0-9]{64}$/.test(s.trim());
}

function shortHex(s: string, head = 10, tail = 6): string {
  return s.length > head + tail + 3 ? `${s.slice(0, head)}…${s.slice(-tail)}` : s;
}

export function SearchCommand() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Global keyboard shortcut: Cmd/Ctrl + K
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        setOpen((o) => !o);
      }
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, []);

  // Autofocus input when dialog opens
  useEffect(() => {
    if (open) {
      setTimeout(() => {
        inputRef.current?.focus();
        inputRef.current?.select();
      }, 50);
    } else {
      setQuery("");
      setActiveIndex(0);
    }
  }, [open]);

  const closeAndReset = () => {
    setOpen(false);
    setQuery("");
    setActiveIndex(0);
  };

  const results: Result[] = useMemo(() => {
    const q = query.trim();

    // Empty query → all pages as a quick-nav menu
    if (!q) {
      return PAGES.map((p) => ({
        id: `page-${p.href}`,
        kind: "page" as const,
        icon: p.icon,
        title: p.title,
        description: p.description,
        onSelect: () => {
          router.push(p.href);
          closeAndReset();
        },
      }));
    }

    const items: Result[] = [];

    // Address → analyze on Explore + BaseScan
    if (isAddress(q)) {
      items.push({
        id: "analyze",
        kind: "address",
        icon: "travel_explore",
        title: "Analyze this token on Explore",
        description: shortHex(q, 12, 10),
        onSelect: () => {
          router.push(`/dashboard/simulation?address=${q}`);
          closeAndReset();
        },
      });
      items.push({
        id: "basescan-addr",
        kind: "external",
        icon: "open_in_new",
        title: "Open address on BaseScan",
        description: shortHex(q, 12, 10),
        onSelect: () => {
          window.open(explorerAddress(q), "_blank", "noopener");
          closeAndReset();
        },
      });
    } else if (isHash32(q)) {
      // 32-byte hash — could be a tx hash or a reasoning hash
      items.push({
        id: "basescan-tx",
        kind: "external",
        icon: "open_in_new",
        title: "Open transaction on BaseScan",
        description: shortHex(q, 12, 10),
        onSelect: () => {
          window.open(explorerTx(q), "_blank", "noopener");
          closeAndReset();
        },
      });
    }

    // Fuzzy match pages
    const lower = q.toLowerCase();
    PAGES.forEach((p) => {
      const matches =
        p.title.toLowerCase().includes(lower) ||
        p.description.toLowerCase().includes(lower) ||
        p.keywords.some((k) => k.includes(lower));
      if (matches) {
        items.push({
          id: `page-${p.href}`,
          kind: "page",
          icon: p.icon,
          title: p.title,
          description: p.description,
          onSelect: () => {
            router.push(p.href);
            closeAndReset();
          },
        });
      }
    });

    return items;
  }, [query, router]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => Math.min(i + 1, Math.max(0, results.length - 1)));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => Math.max(0, i - 1));
    } else if (e.key === "Enter" && results[activeIndex]) {
      e.preventDefault();
      results[activeIndex].onSelect();
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="flex items-center justify-center md:justify-start gap-2 rounded-full py-2 w-11 h-11 md:h-auto md:w-64 md:px-4 text-sm transition-all duration-300 ease-in-out bg-input text-muted-foreground hover:bg-accent shrink-0 cursor-pointer border border-border"
        title="Search (Cmd+K)"
      >
        <span className="material-symbols-outlined shrink-0" style={{ fontSize: "1.2rem" }}>
          search
        </span>
        <span className="hidden md:inline flex-1 text-left truncate">Search tokens, txs, pages…</span>
        <kbd
          className="hidden md:flex items-center gap-1 text-[9px] font-bold tracking-widest uppercase px-2 py-0.5 rounded pointer-events-none bg-background text-muted-foreground border border-border"
        >
          ⌘K
        </kbd>
      </button>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent 
          showCloseButton={false}
          className="p-0 overflow-hidden bg-popover border-border w-[92vw] max-w-[400px] sm:max-w-[600px] gap-0 translate-y-[-40%] mx-auto"
        >
          <DialogTitle className="sr-only">Search</DialogTitle>
          <div className="flex flex-col">
            <div className="flex items-center border-b border-border px-4">
               <span className="material-symbols-outlined text-primary shrink-0" style={{ fontSize: "1.3rem" }}>
                 search
               </span>
               <input
                 ref={inputRef}
                 type="text"
                 value={query}
                 onChange={(e) => {
                   setQuery(e.target.value);
                   setActiveIndex(0);
                 }}
                 onKeyDown={handleKeyDown}
                 placeholder="Search token address, tx hash, or jump to page…"
                 className="flex-1 bg-transparent border-none py-5 px-4 text-sm outline-none text-foreground placeholder:text-muted-foreground font-medium"
               />
               <kbd
                 className="hidden sm:inline-flex text-[9px] font-bold tracking-widest uppercase px-2 py-1 rounded pointer-events-none bg-background text-muted-foreground border border-border"
               >
                 ESC
               </kbd>
            </div>
            
            <div className="max-h-[60vh] overflow-y-auto py-2" style={{ scrollbarWidth: 'none' }}>
              {results.length === 0 ? (
                <div className="p-8 text-center text-sm text-muted-foreground">
                  No results found for &quot;{query}&quot;
                </div>
              ) : (
                <div className="flex flex-col">
                  <div className="px-5 py-2 text-[10px] font-bold tracking-[0.15em] uppercase text-muted-foreground">
                    {query.trim() === "" ? "Jump To" : "Results"}
                  </div>
                  {results.map((r, i) => {
                    const active = i === activeIndex;
                    return (
                      <button
                        key={r.id}
                        onMouseDown={(e) => {
                          e.preventDefault();
                          r.onSelect();
                        }}
                        onMouseEnter={() => setActiveIndex(i)}
                        className={`flex items-center gap-4 px-5 py-3.5 text-left transition-colors w-full group ${active ? 'bg-accent text-accent-foreground' : 'bg-transparent text-foreground'}`}
                      >
                        <span
                          className={`material-symbols-outlined shrink-0 ${active ? 'text-primary' : 'text-muted-foreground'}`}
                          style={{ fontSize: "1.2rem", transition: "color 0.2s" }}
                        >
                          {r.icon}
                        </span>
                        <div className="flex-1 min-w-0 flex flex-col">
                          <div className={`text-sm font-semibold truncate ${active ? 'text-foreground' : 'text-muted-foreground/80'}`}>
                            {r.title}
                          </div>
                          <div
                            className="text-[11px] truncate font-mono mt-0.5 text-muted-foreground"
                          >
                            {r.description}
                          </div>
                        </div>
                        {active && (
                          <span
                            className="text-[10px] uppercase tracking-widest font-bold text-primary"
                          >
                            ↵
                          </span>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
            
            <div
              className="px-5 py-3 flex items-center gap-5 text-[9px] tracking-[0.15em] uppercase font-bold bg-background border-t border-border text-muted-foreground"
            >
              <span className="flex items-center gap-1.5"><span className="text-[12px]">↑↓</span> navigate</span>
              <span className="flex items-center gap-1.5"><span className="text-[12px]">↵</span> select</span>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
