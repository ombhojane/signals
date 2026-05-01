"use client";

import { useState } from "react";
import { formatUnits } from "viem";
import { API_BASE_URL, USDC_ADDRESS, explorerTx } from "@/lib/web3/constants";
import { TradeEvent, useTradeHistory } from "@/lib/web3/hooks";

interface ReasoningData {
  hash: string;
  text: string;
  confidence: number;
  created_at: string;
}

function shortHash(hash: string, head = 8, tail = 6): string {
  if (hash.length <= head + tail + 3) return hash;
  return `${hash.slice(0, head)}…${hash.slice(-tail)}`;
}

function timeAgo(ts: bigint): string {
  const now = Math.floor(Date.now() / 1000);
  const diff = now - Number(ts);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function isBuy(event: TradeEvent): boolean {
  return event.tokenIn.toLowerCase() === USDC_ADDRESS.toLowerCase();
}

function formatAmount(amount: bigint, isUsdc: boolean): string {
  if (isUsdc) {
    const n = Number(formatUnits(amount, 6));
    return n.toFixed(n < 1 ? 4 : 2);
  }
  const n = Number(formatUnits(amount, 18));
  return n < 0.01 ? n.toFixed(6) : n.toFixed(4);
}

function TradeRow({ event }: { event: TradeEvent }) {
  const [expanded, setExpanded] = useState(false);
  const [reasoning, setReasoning] = useState<ReasoningData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const buy = isBuy(event);
  const inIsUsdc = buy;
  const outIsUsdc = !buy;

  const toggle = async () => {
    const next = !expanded;
    setExpanded(next);
    if (next && !reasoning && !loading) {
      setLoading(true);
      setError(null);
      try {
        const res = await fetch(`${API_BASE_URL}/reasoning/${event.reasoningHash}`);
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = (await res.json()) as ReasoningData;
        setReasoning(data);
      } catch {
        setError("Reasoning not found in backend store");
      } finally {
        setLoading(false);
      }
    }
  };

  const actionIconClass = buy ? "text-primary bg-primary/20 border-primary/40" : "text-destructive bg-destructive/20 border-destructive/40";
  const actionBadgeClass = buy ? "text-primary bg-primary/15 border-primary/30" : "text-destructive bg-destructive/15 border-destructive/30";
  const actionLabel = buy ? "BUY" : "SELL";

  return (
    <div
      className="rounded-2xl overflow-hidden transition-colors bg-card border border-border"
    >
      <button
        onClick={toggle}
        className="w-full p-5 flex items-start gap-4 text-left hover:bg-accent transition-colors"
      >
        <div
          className={`mt-0.5 rounded-full h-8 w-8 flex items-center justify-center shrink-0 border ${actionIconClass}`}
        >
          <span
            className="material-symbols-outlined"
            style={{ fontSize: "1rem" }}
          >
            {buy ? "trending_up" : "trending_down"}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <span
              className={`text-[10px] font-bold tracking-[0.15em] uppercase px-2 py-0.5 rounded-full border ${actionBadgeClass}`}
            >
              {actionLabel}
            </span>
            <span className="text-sm font-mono tracking-tight text-foreground">
              {formatAmount(event.amountIn, inIsUsdc)}{" "}
              <span className="text-muted-foreground">{inIsUsdc ? "USDC" : "WETH"}</span>
              <span className="mx-2 text-muted-foreground/50">→</span>
              {formatAmount(event.amountOut, outIsUsdc)}{" "}
              <span className="text-muted-foreground">{outIsUsdc ? "USDC" : "WETH"}</span>
            </span>
          </div>

          <div className="mt-2 flex items-center gap-4 text-[11px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined" style={{ fontSize: "0.85rem" }}>
                psychology
              </span>
              conf {event.confidence}
            </span>
            <span>{timeAgo(event.timestamp)}</span>
            <span className="font-mono tracking-tight">
              hash {shortHash(event.reasoningHash)}
            </span>
          </div>
        </div>

        <span
          className="material-symbols-outlined transition-transform shrink-0 text-muted-foreground/50"
          style={{
            fontSize: "1.1rem",
            transform: expanded ? "rotate(180deg)" : "rotate(0)",
          }}
        >
          expand_more
        </span>
      </button>

      {expanded && (
        <div
          className="px-5 pb-5 pt-1 flex flex-col gap-3 border-t border-border/50"
        >
          <div className="pt-4">
            <p
              className="text-[10px] font-semibold tracking-[0.2em] uppercase mb-2 text-muted-foreground"
            >
              AI Reasoning
            </p>
            {loading && (
              <p className="text-xs italic text-muted-foreground/50">
                Loading from backend…
              </p>
            )}
            {error && (
              <p className="text-xs text-destructive">
                {error}
              </p>
            )}
            {reasoning && (
              <p
                className="text-xs leading-relaxed whitespace-pre-line text-foreground"
              >
                {reasoning.text}
              </p>
            )}
          </div>

          <div className="flex items-center gap-4 flex-wrap">
            <a
              href={explorerTx(event.txHash)}
              target="_blank"
              rel="noreferrer"
              className="text-xs flex items-center gap-1.5 transition-colors hover:underline font-mono text-primary"
            >
              <span className="material-symbols-outlined" style={{ fontSize: "0.9rem" }}>
                open_in_new
              </span>
              tx {shortHash(event.txHash)}
            </a>
            <button
              onClick={(e) => {
                e.stopPropagation();
                navigator.clipboard.writeText(event.reasoningHash);
              }}
              className="text-xs flex items-center gap-1.5 transition-colors hover:underline font-mono text-muted-foreground"
            >
              <span className="material-symbols-outlined" style={{ fontSize: "0.9rem" }}>
                content_copy
              </span>
              copy hash
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export function TradeHistory() {
  const { events, isLoading, refetch } = useTradeHistory();

  return (
    <section className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <h2
            className="text-sm font-bold tracking-[0.2em] uppercase text-foreground"
          >
            Recent Trades
          </h2>
          <p className="text-xs mt-1 text-muted-foreground">
            Every trade committed on-chain with its AI reasoning hash
          </p>
        </div>
        <button
          onClick={refetch}
          disabled={isLoading}
          className="text-[10px] font-bold tracking-widest uppercase px-4 py-2 rounded-full transition-colors disabled:opacity-40 bg-accent text-primary border border-primary/20 hover:bg-muted"
        >
          {isLoading ? "Loading…" : "Refresh"}
        </button>
      </div>

      {isLoading ? (
        <div
          className="rounded-2xl p-8 text-center bg-card border border-border"
        >
          <p className="text-sm text-muted-foreground/50">
            Fetching trade events from Base Sepolia…
          </p>
        </div>
      ) : events.length === 0 ? (
        <div
          className="rounded-2xl p-8 text-center bg-card border border-border"
        >
          <span
            className="material-symbols-outlined block mb-3 text-[2rem] text-primary"
          >
            hourglass_empty
          </span>
          <p className="text-sm text-foreground">
            No trades yet
          </p>
          <p className="text-xs mt-1 text-muted-foreground">
            The agent hasn&apos;t executed any trades in this window. Check back after the next signal.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {events.map((event) => (
            <TradeRow key={`${event.txHash}-${event.blockNumber}`} event={event} />
          ))}
        </div>
      )}
    </section>
  );
}
