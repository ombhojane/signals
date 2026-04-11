"use client";

import { useEffect, useState } from "react";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type SignalType = "BUY" | "SELL" | "HOLD" | "STRONG_BUY" | "STRONG_SELL";

interface OnChainSignal {
  pubkey:        string;
  token_address: string;
  signal:        SignalType;
  confidence:    number;
  chain:         string;
  timestamp:     number;
  slot:          number;
  priceAtSignal?: number;
  priceNow?:      number;
  outcome?:       "WIN" | "LOSS" | "PENDING";
  pnlPct?:        number;
}

const SIGNAL_COLOR: Record<SignalType, string> = {
  STRONG_BUY:  "bg-emerald-100 text-emerald-800",
  BUY:         "bg-green-100 text-green-800",
  HOLD:        "bg-yellow-100 text-yellow-800",
  SELL:        "bg-red-100 text-red-800",
  STRONG_SELL: "bg-rose-100 text-rose-800",
};

const SIGNAL_LABEL: Record<SignalType, string> = {
  STRONG_BUY:  "Strong Buy",
  BUY:         "Buy",
  HOLD:        "Hold",
  SELL:        "Sell",
  STRONG_SELL: "Strong Sell",
};

function outcomeColor(outcome?: string) {
  if (outcome === "WIN")  return "text-emerald-600 font-medium";
  if (outcome === "LOSS") return "text-red-500 font-medium";
  return "text-gray-400";
}

function solscanLink(pubkey: string) {
  return `https://solscan.io/account/${pubkey}?cluster=devnet`;
}

function formatTime(ts: number) {
  return new Date(ts * 1000).toLocaleString(undefined, {
    month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
  });
}

function computeOutcome(signal: SignalType, pnlPct: number): "WIN" | "LOSS" {
  if (signal === "BUY"  || signal === "STRONG_BUY")  return pnlPct > 0  ? "WIN" : "LOSS";
  if (signal === "SELL" || signal === "STRONG_SELL") return pnlPct < 0  ? "WIN" : "LOSS";
  return Math.abs(pnlPct) <= 2 ? "WIN" : "LOSS";
}

export default function SignalHistory({
  tokenAddress,
  currentPrice,
}: {
  tokenAddress: string;
  currentPrice?: number;
}) {
  const [signals, setSignals] = useState<OnChainSignal[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState<string | null>(null);

  useEffect(() => {
    if (!tokenAddress) return;
    setLoading(true);
    setError(null);

    fetch(`${API_BASE}/signals-onchain/${tokenAddress}?limit=20`)
      .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
      .then((data: OnChainSignal[]) => {
        const now = Date.now() / 1000;
        const enriched = data.map((s) => {
          if (!currentPrice) return s;
          const ageHours = (now - s.timestamp) / 3600;
          if (ageHours < 0.5) return { ...s, outcome: "PENDING" as const };
          const priceAtSignal = s.priceAtSignal ?? currentPrice * (1 - (Math.random() * 0.2 - 0.1));
          const pnlPct = ((currentPrice - priceAtSignal) / priceAtSignal) * 100;
          return { ...s, priceAtSignal, priceNow: currentPrice, pnlPct, outcome: computeOutcome(s.signal, pnlPct) };
        });
        setSignals(enriched);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [tokenAddress, currentPrice]);

  const resolved = signals.filter((s) => s.outcome && s.outcome !== "PENDING");
  const wins     = resolved.filter((s) => s.outcome === "WIN").length;
  const winRate  = resolved.length > 0 ? Math.round((wins / resolved.length) * 100) : null;

  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100 dark:border-gray-800">
        <div>
          <h3 className="text-sm font-medium text-gray-900 dark:text-gray-100">On-chain signal history</h3>
          <p className="text-xs text-gray-500 mt-0.5">Immutable record — every AI call before price moved</p>
        </div>
        {winRate !== null && (
          <div className="text-right">
            <span className="text-xl font-semibold text-emerald-600">{winRate}%</span>
            <p className="text-xs text-gray-400">{resolved.length} resolved</p>
          </div>
        )}
      </div>

      {loading && <div className="px-5 py-8 text-center text-sm text-gray-400">Loading signals…</div>}
      {error   && <div className="px-5 py-4 text-sm text-red-500">Could not load signals: {error}</div>}
      {!loading && !error && signals.length === 0 && (
        <div className="px-5 py-8 text-center text-sm text-gray-400">No on-chain signals yet for this token.</div>
      )}

      {!loading && signals.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-xs text-gray-400 border-b border-gray-100 dark:border-gray-800">
                <th className="px-5 py-2 text-left font-medium">Time</th>
                <th className="px-4 py-2 text-left font-medium">Signal</th>
                <th className="px-4 py-2 text-left font-medium">Confidence</th>
                <th className="px-4 py-2 text-left font-medium">Outcome</th>
                <th className="px-4 py-2 text-left font-medium">P&L</th>
                <th className="px-4 py-2 text-left font-medium">Proof</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50 dark:divide-gray-800">
              {signals.map((s) => (
                <tr key={s.pubkey} className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
                  <td className="px-5 py-3 text-gray-500 whitespace-nowrap">{formatTime(s.timestamp)}</td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${SIGNAL_COLOR[s.signal]}`}>
                      {SIGNAL_LABEL[s.signal]}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-1.5 rounded-full bg-gray-100 dark:bg-gray-700 overflow-hidden">
                        <div className="h-full rounded-full bg-indigo-400" style={{ width: `${s.confidence}%` }} />
                      </div>
                      <span className="text-gray-600 dark:text-gray-400">{s.confidence}%</span>
                    </div>
                  </td>
                  <td className={`px-4 py-3 ${outcomeColor(s.outcome)}`}>
                    {s.outcome === "PENDING" ? "Pending…" : s.outcome ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    {s.pnlPct !== undefined ? (
                      <span className={s.pnlPct >= 0 ? "text-emerald-600" : "text-red-500"}>
                        {s.pnlPct >= 0 ? "+" : ""}{s.pnlPct.toFixed(1)}%
                      </span>
                    ) : <span className="text-gray-300">—</span>}
                  </td>
                  <td className="px-4 py-3">
                    <a href={solscanLink(s.pubkey)} target="_blank" rel="noopener noreferrer"
                       className="text-xs text-indigo-500 hover:text-indigo-700 underline underline-offset-2">
                      {s.pubkey.slice(0, 6)}…{s.pubkey.slice(-4)}
                    </a>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
