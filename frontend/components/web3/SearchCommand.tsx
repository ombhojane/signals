"use client";

import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { explorerAddress, explorerTx } from "@/lib/web3/constants";

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
    keywords: ["explore", "simulation", "signals", "scan", "tokens", "analyze"],
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
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Click outside to close
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  // Global keyboard shortcut: Cmd/Ctrl + K
  useEffect(() => {
    function handleKey(e: KeyboardEvent) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        inputRef.current?.focus();
        inputRef.current?.select();
        setOpen(true);
      }
      if (e.key === "Escape") {
        setOpen(false);
        inputRef.current?.blur();
      }
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, []);

  const closeAndReset = () => {
    setOpen(false);
    setQuery("");
    setActiveIndex(0);
    inputRef.current?.blur();
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
          router.push(`/dashboard/simulation?token=${q}`);
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
    <div ref={containerRef} className="relative">
      <div className="relative flex items-center">
        <span
          className="material-symbols-outlined absolute left-4 text-[#acabaa] pointer-events-none"
          style={{ fontSize: "1.1rem" }}
        >
          search
        </span>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
            setActiveIndex(0);
          }}
          onFocus={(e) => {
            setOpen(true);
            e.target.style.boxShadow = "0 0 0 1px rgba(167,203,235,0.3)";
          }}
          onBlur={(e) => {
            e.target.style.boxShadow = "none";
          }}
          onKeyDown={handleKeyDown}
          placeholder="Search tokens, txs, pages…"
          className="rounded-full py-2 pl-12 pr-16 text-sm w-80 outline-none placeholder:text-neutral-600 text-[#e7e5e5]"
          style={{
            backgroundColor: "#252626",
            border: "none",
          }}
        />
        <kbd
          className="absolute right-3 text-[9px] font-bold tracking-widest uppercase px-2 py-0.5 rounded pointer-events-none"
          style={{
            backgroundColor: "#131313",
            color: "#acabaa",
            border: "1px solid rgba(72,72,72,0.4)",
          }}
        >
          ⌘K
        </kbd>
      </div>

      {open && (
        <div
          className="absolute top-full left-0 mt-2 w-[26rem] rounded-2xl overflow-hidden card-shadow z-[60]"
          style={{
            backgroundColor: "#191a1a",
            border: "1px solid rgba(72,72,72,0.3)",
          }}
        >
          {results.length === 0 ? (
            <div className="p-6 text-center">
              <p className="text-xs" style={{ color: "#737373" }}>
                No results. Try a token address, tx hash, or page name.
              </p>
            </div>
          ) : (
            <div className="flex flex-col py-2">
              <div
                className="px-4 py-2 text-[9px] font-bold tracking-[0.2em] uppercase"
                style={{ color: "#737373" }}
              >
                {query.trim() === "" ? "Jump to" : "Results"}
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
                    className="flex items-center gap-3 px-4 py-3 text-left transition-colors"
                    style={{
                      backgroundColor: active ? "#252626" : "transparent",
                      color: "#e7e5e5",
                    }}
                  >
                    <span
                      className="material-symbols-outlined shrink-0"
                      style={{ fontSize: "1.1rem", color: "#a7cbeb" }}
                    >
                      {r.icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-semibold truncate">{r.title}</div>
                      <div
                        className="text-[11px] truncate font-mono"
                        style={{ color: "#acabaa" }}
                      >
                        {r.description}
                      </div>
                    </div>
                    {active && (
                      <span
                        className="text-[9px] uppercase tracking-widest font-bold"
                        style={{ color: "#a7cbeb" }}
                      >
                        ↵
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          )}
          <div
            className="px-4 py-2.5 flex items-center gap-4 text-[9px] tracking-widest uppercase font-semibold"
            style={{
              backgroundColor: "#0e0e0e",
              borderTop: "1px solid rgba(72,72,72,0.2)",
              color: "#737373",
            }}
          >
            <span>↑↓ navigate</span>
            <span>↵ select</span>
            <span>esc close</span>
          </div>
        </div>
      )}
    </div>
  );
}
