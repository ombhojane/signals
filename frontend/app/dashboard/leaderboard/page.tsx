"use client";

import { useMemo } from "react";
import { formatUnits } from "viem";
import { TradeHistory } from "@/components/web3/TradeHistory";
import { VolumeChart, type VolumePoint } from "@/components/web3/VolumeChart";
import {
  API_BASE_URL,
  USDC_ADDRESS,
  VAULT_ADDRESS,
  explorerAddress,
} from "@/lib/web3/constants";
import { formatUsdc, useTradeHistory, useVaultState } from "@/lib/web3/hooks";

function StatCard({
  label,
  value,
  sub,
  accent = false,
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: boolean;
}) {
  return (
    <div
      className="rounded-2xl p-6 flex flex-col gap-2"
      style={{
        backgroundColor: "#131313",
        border: "1px solid rgba(72,72,72,0.25)",
      }}
    >
      <span
        className="text-[10px] font-semibold tracking-[0.2em] uppercase"
        style={{ color: "#acabaa" }}
      >
        {label}
      </span>
      <span
        className="text-3xl font-black font-mono tracking-tight"
        style={{ color: accent ? "#a7cbeb" : "#e7e5e5" }}
      >
        {value}
      </span>
      {sub ? (
        <span className="text-xs tracking-wide" style={{ color: "#acabaa" }}>
          {sub}
        </span>
      ) : null}
    </div>
  );
}

function SignalApiShowcase() {
  const curlExample = `# Sample (unauthenticated → 402)
curl ${API_BASE_URL}/signal/base/0x4200000000000000000000000000000000000006

# After paying 0.01 USDC on Base Sepolia to the agent wallet:
curl -H "X-Payment: 0x<your-tx-hash>" \\
  ${API_BASE_URL}/signal/base/0x4200000000000000000000000000000000000006
`;

  return (
    <section
      className="rounded-3xl p-8 flex flex-col gap-6"
      style={{
        backgroundColor: "#131313",
        border: "1px solid rgba(72,72,72,0.25)",
      }}
    >
      <div className="flex items-start justify-between gap-6 flex-wrap">
        <div>
          <span
            className="text-[10px] font-bold tracking-[0.2em] uppercase"
            style={{ color: "#a7cbeb" }}
          >
            Signal API · Pay-per-inference
          </span>
          <h3
            className="text-3xl font-black tracking-[-0.02em] mt-2"
            style={{ color: "#e7e5e5" }}
          >
            Other agents pay to call ours.
          </h3>
          <p className="mt-3 text-sm max-w-xl" style={{ color: "#acabaa" }}>
            Every signal our AI produces is priced per call using{" "}
            <span style={{ color: "#a7cbeb" }}>x402</span> — HTTP-native
            micropayments over USDC. Send 0.01 USDC to the agent wallet, retry
            with the tx hash in the header, receive a signed signal with its
            on-chain reasoning hash. No API keys, no signups, no Stripe.
          </p>
        </div>
        <a
          href="/dashboard/simulation"
          className="flex items-center gap-2 text-xs font-bold tracking-widest uppercase px-5 py-3 rounded-full transition-colors shrink-0"
          style={{
            backgroundColor: "#a7cbeb",
            color: "#1e435e",
          }}
        >
          Try the Explorer
          <span className="material-symbols-outlined" style={{ fontSize: "1rem" }}>
            arrow_forward
          </span>
        </a>
      </div>

      <div
        className="rounded-2xl p-5 font-mono text-xs overflow-x-auto"
        style={{
          backgroundColor: "#0a0a0a",
          border: "1px solid rgba(72,72,72,0.2)",
        }}
      >
        <pre style={{ whiteSpace: "pre", color: "#cdcdcd" }}>{curlExample}</pre>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="flex flex-col gap-1">
          <span className="text-[10px] tracking-widest uppercase" style={{ color: "#acabaa" }}>
            Price
          </span>
          <span className="text-base font-mono font-bold" style={{ color: "#e7e5e5" }}>
            0.01 USDC / call
          </span>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-[10px] tracking-widest uppercase" style={{ color: "#acabaa" }}>
            Network
          </span>
          <span className="text-base font-mono font-bold" style={{ color: "#e7e5e5" }}>
            Base Sepolia
          </span>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-[10px] tracking-widest uppercase" style={{ color: "#acabaa" }}>
            Endpoint
          </span>
          <span className="text-base font-mono font-bold truncate" style={{ color: "#e7e5e5" }}>
            /signal/&#123;chain&#125;/&#123;mint&#125;
          </span>
        </div>
      </div>
    </section>
  );
}

export default function ProofPage() {
  const { totalAssets, positionOpen } = useVaultState();
  const { events, isLoading, refetch } = useTradeHistory();

  const { totalTrades, totalVolumeUsdc, avgConfidence, volumeSeries } = useMemo(() => {
    if (events.length === 0) {
      return {
        totalTrades: 0,
        totalVolumeUsdc: 0,
        avgConfidence: 0,
        volumeSeries: [] as VolumePoint[],
      };
    }

    const chronological = [...events].sort((a, b) => Number(a.timestamp - b.timestamp));

    let running = 0;
    const series: VolumePoint[] = chronological.map((e) => {
      const usdc =
        e.tokenIn.toLowerCase() === USDC_ADDRESS.toLowerCase()
          ? Number(formatUnits(e.amountIn, 6))
          : Number(formatUnits(e.amountOut, 6));
      running += usdc;
      return {
        time: Number(e.timestamp) as VolumePoint["time"],
        value: Math.round(running * 1e4) / 1e4,
      };
    });

    const sumConfidence = chronological.reduce((s, e) => s + e.confidence, 0);

    return {
      totalTrades: chronological.length,
      totalVolumeUsdc: running,
      avgConfidence: sumConfidence / chronological.length,
      volumeSeries: series,
    };
  }, [events]);

  return (
    <div className="flex flex-col gap-8 max-w-6xl">
      <div className="flex items-start justify-between gap-6 flex-wrap">
        <div>
          <h1
            className="text-5xl font-black tracking-[-0.03em] mt-2"
            style={{ color: "#e7e5e5" }}
          >
            Proof of Alpha
          </h1>
          <p className="mt-3 text-sm max-w-xl" style={{ color: "#acabaa" }}>
            Every trade the Signals vault has ever made, live from Base Sepolia.
            Each one is linked to the AI reasoning that produced it via an
            on-chain hash. No edits, no cherry-picking, no retroactive spin.
          </p>
        </div>

        <a
          href={explorerAddress(VAULT_ADDRESS)}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2 text-xs font-mono tracking-tight px-4 py-2.5 rounded-full transition-colors shrink-0"
          style={{
            backgroundColor: "#131313",
            color: "#a7cbeb",
            border: "1px solid rgba(167,203,235,0.2)",
          }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: "0.9rem" }}>
            open_in_new
          </span>
          {VAULT_ADDRESS.slice(0, 8)}…{VAULT_ADDRESS.slice(-6)}
        </a>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          label="Total Trades"
          value={totalTrades.toString()}
          sub={positionOpen ? "1 position currently open" : "No open position"}
          accent
        />
        <StatCard
          label="Total Volume"
          value={`${totalVolumeUsdc.toFixed(2)} USDC`}
          sub="Cumulative USDC traded"
        />
        <StatCard
          label="Avg Confidence"
          value={totalTrades > 0 ? `${avgConfidence.toFixed(0)} / 100` : "—"}
          sub="Across all trades"
        />
        <StatCard
          label="Live TVL"
          value={`${formatUsdc(totalAssets, 4)} USDC`}
          sub="Vault balance right now"
        />
      </div>

      <section
        className="rounded-3xl p-6 flex flex-col gap-4"
        style={{
          backgroundColor: "#131313",
          border: "1px solid rgba(72,72,72,0.25)",
        }}
      >
        <div className="flex items-center justify-between">
          <div>
            <h2
              className="text-sm font-bold tracking-[0.2em] uppercase"
              style={{ color: "#e7e5e5" }}
            >
              Cumulative Traded Volume
            </h2>
            <p className="text-xs mt-1" style={{ color: "#acabaa" }}>
              Running total of USDC routed through every trade
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

        {totalTrades === 0 ? (
          <div
            className="h-64 flex items-center justify-center rounded-2xl"
            style={{ backgroundColor: "#0e0e0e", border: "1px dashed rgba(72,72,72,0.3)" }}
          >
            <span className="text-xs" style={{ color: "#737373" }}>
              {isLoading ? "Loading on-chain events…" : "No trades yet"}
            </span>
          </div>
        ) : (
          <VolumeChart data={volumeSeries} height={280} />
        )}
      </section>

      <SignalApiShowcase />

      <TradeHistory />
    </div>
  );
}
