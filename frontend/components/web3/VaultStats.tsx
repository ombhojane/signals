"use client";

import { useAccount } from "wagmi";
import { formatUsdc, useUserPosition, useVaultState } from "@/lib/web3/hooks";

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

export function VaultStats() {
  const { isConnected } = useAccount();
  const { totalAssets, totalSupply, positionOpen, sharePriceUsdc } = useVaultState();
  const { shares, shareValueAssets } = useUserPosition();

  const statusLabel = positionOpen ? "Trading" : "Idle";
  const statusDot = positionOpen ? "#f5c14b" : "#a7cbeb";
  const statusSub = positionOpen
    ? "Position open — deposits locked"
    : "Ready for deposits & withdrawals";

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <StatCard
        label="Total Value Locked"
        value={`${formatUsdc(totalAssets, 4)} USDC`}
        sub={`${formatUsdc(totalSupply, 4)} sVAULT outstanding · 1 share ≈ ${sharePriceUsdc.toFixed(4)} USDC`}
      />
      <StatCard
        label="Your Position"
        value={isConnected ? `${formatUsdc(shares, 4)} sVAULT` : "— sVAULT"}
        sub={
          isConnected
            ? `≈ ${formatUsdc(shareValueAssets, 4)} USDC redeemable`
            : "Connect wallet to view"
        }
        accent={isConnected && shares > 0n}
      />
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
          Vault Status
        </span>
        <div className="flex items-center gap-3">
          <span
            className="inline-block w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: statusDot, boxShadow: `0 0 12px ${statusDot}` }}
          />
          <span
            className="text-3xl font-black tracking-tight"
            style={{ color: "#e7e5e5" }}
          >
            {statusLabel}
          </span>
        </div>
        <span className="text-xs tracking-wide" style={{ color: "#acabaa" }}>
          {statusSub}
        </span>
      </div>
    </div>
  );
}
