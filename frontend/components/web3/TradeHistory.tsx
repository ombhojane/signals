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

  const actionColor = buy ? "#a7cbeb" : "#ee7d77";
  const actionLabel = buy ? "BUY" : "SELL";

  return (
    <div
      className="rounded-2xl overflow-hidden transition-colors"
      style={{
        backgroundColor: "#131313",
        border: "1px solid rgba(72,72,72,0.25)",
      }}
    >
      <button
        onClick={toggle}
        className="w-full p-5 flex items-start gap-4 text-left hover:bg-[#161616] transition-colors"
      >
        <div
          className="mt-0.5 rounded-full h-8 w-8 flex items-center justify-center shrink-0"
          style={{
            backgroundColor: `${actionColor}20`,
            border: `1px solid ${actionColor}40`,
          }}
        >
          <span
            className="material-symbols-outlined"
            style={{ fontSize: "1rem", color: actionColor }}
          >
            {buy ? "trending_up" : "trending_down"}
          </span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-3 flex-wrap">
            <span
              className="text-[10px] font-bold tracking-[0.15em] uppercase px-2 py-0.5 rounded-full"
              style={{
                backgroundColor: `${actionColor}15`,
                color: actionColor,
                border: `1px solid ${actionColor}30`,
              }}
            >
              {actionLabel}
            </span>
            <span className="text-sm font-mono tracking-tight" style={{ color: "#e7e5e5" }}>
              {formatAmount(event.amountIn, inIsUsdc)}{" "}
              <span style={{ color: "#acabaa" }}>{inIsUsdc ? "USDC" : "WETH"}</span>
              <span className="mx-2" style={{ color: "#737373" }}>→</span>
              {formatAmount(event.amountOut, outIsUsdc)}{" "}
              <span style={{ color: "#acabaa" }}>{outIsUsdc ? "USDC" : "WETH"}</span>
            </span>
          </div>

          <div className="mt-2 flex items-center gap-4 text-[11px]" style={{ color: "#acabaa" }}>
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
          className="material-symbols-outlined transition-transform shrink-0"
          style={{
            fontSize: "1.1rem",
            color: "#737373",
            transform: expanded ? "rotate(180deg)" : "rotate(0)",
          }}
        >
          expand_more
        </span>
      </button>

      {expanded && (
        <div
          className="px-5 pb-5 pt-1 flex flex-col gap-3"
          style={{ borderTop: "1px solid rgba(72,72,72,0.2)" }}
        >
          <div className="pt-4">
            <p
              className="text-[10px] font-semibold tracking-[0.2em] uppercase mb-2"
              style={{ color: "#acabaa" }}
            >
              AI Reasoning
            </p>
            {loading && (
              <p className="text-xs italic" style={{ color: "#737373" }}>
                Loading from backend…
              </p>
            )}
            {error && (
              <p className="text-xs" style={{ color: "#ee7d77" }}>
                {error}
              </p>
            )}
            {reasoning && (
              <p
                className="text-xs leading-relaxed whitespace-pre-line"
                style={{ color: "#e7e5e5" }}
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
              className="text-xs flex items-center gap-1.5 transition-colors hover:underline font-mono"
              style={{ color: "#a7cbeb" }}
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
              className="text-xs flex items-center gap-1.5 transition-colors hover:underline font-mono"
              style={{ color: "#acabaa" }}
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
            className="text-sm font-bold tracking-[0.2em] uppercase"
            style={{ color: "#e7e5e5" }}
          >
            Recent Trades
          </h2>
          <p className="text-xs mt-1" style={{ color: "#acabaa" }}>
            Every trade committed on-chain with its AI reasoning hash
          </p>
        </div>
        <button
          onClick={refetch}
          disabled={isLoading}
          className="text-[10px] font-bold tracking-widest uppercase px-4 py-2 rounded-full transition-colors disabled:opacity-40"
          style={{
            backgroundColor: "#191a1a",
            color: "#a7cbeb",
            border: "1px solid rgba(167,203,235,0.2)",
          }}
        >
          {isLoading ? "Loading…" : "Refresh"}
        </button>
      </div>

      {isLoading ? (
        <div
          className="rounded-2xl p-8 text-center"
          style={{ backgroundColor: "#131313", border: "1px solid rgba(72,72,72,0.25)" }}
        >
          <p className="text-sm" style={{ color: "#737373" }}>
            Fetching trade events from Base Sepolia…
          </p>
        </div>
      ) : events.length === 0 ? (
        <div
          className="rounded-2xl p-8 text-center"
          style={{ backgroundColor: "#131313", border: "1px solid rgba(72,72,72,0.25)" }}
        >
          <span
            className="material-symbols-outlined block mb-3"
            style={{ fontSize: "2rem", color: "#a7cbeb" }}
          >
            hourglass_empty
          </span>
          <p className="text-sm" style={{ color: "#e7e5e5" }}>
            No trades yet
          </p>
          <p className="text-xs mt-1" style={{ color: "#acabaa" }}>
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
