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
    <div className="rounded-2xl p-6 flex flex-col gap-2 bg-card border border-border">
      <span className="text-[10px] font-semibold tracking-[0.2em] uppercase text-muted-foreground">
        {label}
      </span>
      <span className={`text-3xl font-black font-mono tracking-tight ${accent ? "text-primary" : "text-foreground"}`}>
        {value}
      </span>
      {sub ? (
        <span className="text-xs tracking-wide text-muted-foreground">{sub}</span>
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
    <section className="rounded-3xl p-8 flex flex-col gap-6 bg-card border border-border">
      <div className="flex items-start justify-between gap-6 flex-wrap">
        <div>
          <span className="text-[10px] font-bold tracking-[0.2em] uppercase text-primary">
            Signal API · Pay-per-inference
          </span>
          <h3 className="text-3xl font-black tracking-[-0.02em] mt-2 text-foreground">
            Other agents pay to call ours.
          </h3>
          <p className="mt-3 text-sm max-w-xl text-muted-foreground">
            Every signal our AI produces is priced per call using{" "}
            <span className="text-primary">x402</span> — HTTP-native
            micropayments over USDC. Send 0.01 USDC to the agent wallet, retry
            with the tx hash in the header, receive a signed signal with its
            on-chain reasoning hash. No API keys, no signups, no Stripe.
          </p>
        </div>
        <a
          href="/dashboard/simulation"
          className="flex items-center gap-2 text-xs font-bold tracking-widest uppercase px-5 py-3 rounded-full transition-colors shrink-0 bg-primary text-primary-foreground hover:opacity-90"
        >
          Try the Explorer
          <span className="material-symbols-outlined" style={{ fontSize: "1rem" }}>
            arrow_forward
          </span>
        </a>
      </div>

      <div className="rounded-2xl p-5 font-mono text-xs overflow-x-auto bg-background border border-border/60">
        <pre className="text-foreground/80" style={{ whiteSpace: "pre" }}>{curlExample}</pre>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="flex flex-col gap-1">
          <span className="text-[10px] tracking-widest uppercase text-muted-foreground">Price</span>
          <span className="text-base font-mono font-bold text-foreground">0.01 USDC / call</span>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-[10px] tracking-widest uppercase text-muted-foreground">Network</span>
          <span className="text-base font-mono font-bold text-foreground">Base Sepolia</span>
        </div>
        <div className="flex flex-col gap-1">
          <span className="text-[10px] tracking-widest uppercase text-muted-foreground">Endpoint</span>
          <span className="text-base font-mono font-bold truncate text-foreground">
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
      return { totalTrades: 0, totalVolumeUsdc: 0, avgConfidence: 0, volumeSeries: [] as VolumePoint[] };
    }

    const chronological = [...events].sort((a, b) => Number(a.timestamp - b.timestamp));
    let running = 0;
    const series: VolumePoint[] = chronological.map((e) => {
      const usdc =
        e.tokenIn.toLowerCase() === USDC_ADDRESS.toLowerCase()
          ? Number(formatUnits(e.amountIn, 6))
          : Number(formatUnits(e.amountOut, 6));
      running += usdc;
      return { time: Number(e.timestamp) as VolumePoint["time"], value: Math.round(running * 1e4) / 1e4 };
    });

    const sumConfidence = chronological.reduce((s, e) => s + e.confidence, 0);
    return { totalTrades: chronological.length, totalVolumeUsdc: running, avgConfidence: sumConfidence / chronological.length, volumeSeries: series };
  }, [events]);

  return (
    <div className="flex flex-col gap-8 max-w-6xl">
      <div className="flex items-start justify-between gap-6 flex-wrap">
        <div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight mt-2 text-foreground">
            Proof of Alpha
          </h1>
          <p className="mt-3 text-lg md:text-xl text-muted-foreground font-light leading-relaxed max-w-2xl">
            Every trade the Signals vault has ever made, live from Base Sepolia.
            Each one is linked to the AI reasoning that produced it via an
            on-chain hash. No edits, no cherry-picking, no retroactive spin.
          </p>
        </div>

        <a
          href={explorerAddress(VAULT_ADDRESS)}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2 text-xs font-mono tracking-tight px-4 py-2.5 rounded-full transition-colors shrink-0 bg-card text-primary border border-primary/20 hover:bg-accent"
        >
          <span className="material-symbols-outlined" style={{ fontSize: "0.9rem" }}>open_in_new</span>
          {VAULT_ADDRESS.slice(0, 8)}…{VAULT_ADDRESS.slice(-6)}
        </a>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Trades" value={totalTrades.toString()} sub={positionOpen ? "1 position currently open" : "No open position"} accent />
        <StatCard label="Total Volume" value={`${totalVolumeUsdc.toFixed(2)} USDC`} sub="Cumulative USDC traded" />
        <StatCard label="Avg Confidence" value={totalTrades > 0 ? `${avgConfidence.toFixed(0)} / 100` : "—"} sub="Across all trades" />
        <StatCard label="Live TVL" value={`${formatUsdc(totalAssets, 4)} USDC`} sub="Vault balance right now" />
      </div>

      <section className="rounded-3xl p-6 flex flex-col gap-4 bg-card border border-border">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-bold tracking-[0.2em] uppercase text-foreground">
              Cumulative Traded Volume
            </h2>
            <p className="text-xs mt-1 text-muted-foreground">
              Running total of USDC routed through every trade
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

        {totalTrades === 0 ? (
          <div className="h-64 flex items-center justify-center rounded-2xl bg-background border border-dashed border-border">
            <span className="text-xs text-muted-foreground/50">
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
