"use client";

import { useAccount } from "wagmi";
import { TradeHistory } from "@/components/web3/TradeHistory";
import { VAULT_ADDRESS, explorerAddress, explorerTx } from "@/lib/web3/constants";
import {
  formatUsdc,
  useUserActivity,
  useUserPosition,
  type UserDepositEvent,
} from "@/lib/web3/hooks";

function StatCard({
  label,
  value,
  sub,
  accent = false,
  tone = "neutral",
}: {
  label: string;
  value: string;
  sub?: string;
  accent?: boolean;
  tone?: "neutral" | "positive" | "negative";
}) {
  const color = accent
    ? "#a7cbeb"
    : tone === "positive"
    ? "#a7cbeb"
    : tone === "negative"
    ? "#ee7d77"
    : "#e7e5e5";
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
        style={{ color }}
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

function shortHash(hash: string, head = 8, tail = 6): string {
  if (hash.length <= head + tail + 3) return hash;
  return `${hash.slice(0, head)}…${hash.slice(-tail)}`;
}

function EventRow({
  event,
  kind,
}: {
  event: UserDepositEvent;
  kind: "deposit" | "withdraw";
}) {
  const color = kind === "deposit" ? "#a7cbeb" : "#ee7d77";
  const label = kind === "deposit" ? "DEPOSIT" : "WITHDRAW";
  const symbol = kind === "deposit" ? "south_east" : "north_east";

  return (
    <a
      href={explorerTx(event.txHash)}
      target="_blank"
      rel="noreferrer"
      className="flex items-center gap-4 rounded-2xl p-4 transition-colors hover:bg-[#161616]"
      style={{
        backgroundColor: "#131313",
        border: "1px solid rgba(72,72,72,0.25)",
      }}
    >
      <div
        className="rounded-full h-8 w-8 flex items-center justify-center shrink-0"
        style={{
          backgroundColor: `${color}20`,
          border: `1px solid ${color}40`,
        }}
      >
        <span
          className="material-symbols-outlined"
          style={{ fontSize: "1rem", color }}
        >
          {symbol}
        </span>
      </div>

      <div className="flex-1 min-w-0 flex items-center gap-3 flex-wrap">
        <span
          className="text-[10px] font-bold tracking-[0.15em] uppercase px-2 py-0.5 rounded-full"
          style={{
            backgroundColor: `${color}15`,
            color,
            border: `1px solid ${color}30`,
          }}
        >
          {label}
        </span>
        <span className="text-sm font-mono font-bold" style={{ color: "#e7e5e5" }}>
          {formatUsdc(event.assets, 4)} USDC
        </span>
        <span className="text-xs font-mono" style={{ color: "#acabaa" }}>
          · {formatUsdc(event.shares, 4)} sVAULT
        </span>
      </div>

      <span className="text-[10px] font-mono tracking-tight" style={{ color: "#737373" }}>
        {shortHash(event.txHash)}
      </span>
      <span
        className="material-symbols-outlined shrink-0"
        style={{ fontSize: "1rem", color: "#737373" }}
      >
        open_in_new
      </span>
    </a>
  );
}

export default function ActivityPage() {
  const { isConnected } = useAccount();
  const { shares, shareValueAssets } = useUserPosition();
  const {
    deposits,
    withdrawals,
    totalDeposited,
    totalWithdrawn,
    isLoading,
    refetch,
  } = useUserActivity();

  // Realised P&L from closed flows + current unrealised from open shares
  const netValue = shareValueAssets + totalWithdrawn;
  const pnl = totalDeposited === 0n ? 0n : netValue - totalDeposited;
  const pnlPositive = pnl >= 0n;

  return (
    <div className="flex flex-col gap-8 max-w-6xl">
      <div className="flex items-start justify-between gap-6 flex-wrap">
        <div>
          <h1
            className="text-5xl font-black tracking-[-0.03em] mt-2"
            style={{ color: "#e7e5e5" }}
          >
            Your Activity
          </h1>
          <p className="mt-3 text-sm max-w-xl" style={{ color: "#acabaa" }}>
            Your personal vault history — every deposit, every withdrawal, and
            your current share position. All read straight from Base Sepolia.
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
          Vault contract
        </a>
      </div>

      {!isConnected ? (
        <div
          className="rounded-3xl p-10 text-center"
          style={{
            backgroundColor: "#131313",
            border: "1px solid rgba(72,72,72,0.25)",
          }}
        >
          <span
            className="material-symbols-outlined block mb-3"
            style={{ fontSize: "2rem", color: "#a7cbeb" }}
          >
            account_balance_wallet
          </span>
          <h3 className="text-base font-semibold mb-1" style={{ color: "#e7e5e5" }}>
            Connect your wallet to see your activity
          </h3>
          <p className="text-sm" style={{ color: "#acabaa" }}>
            Use the Connect Wallet button in the sidebar.
          </p>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              label="Total Deposited"
              value={`${formatUsdc(totalDeposited, 4)} USDC`}
              sub={`${deposits.length} deposit${deposits.length === 1 ? "" : "s"}`}
            />
            <StatCard
              label="Total Withdrawn"
              value={`${formatUsdc(totalWithdrawn, 4)} USDC`}
              sub={`${withdrawals.length} withdrawal${withdrawals.length === 1 ? "" : "s"}`}
            />
            <StatCard
              label="Current Position"
              value={`${formatUsdc(shareValueAssets, 4)} USDC`}
              sub={`${formatUsdc(shares, 4)} sVAULT held`}
              accent
            />
            <StatCard
              label="Net P&L"
              value={`${pnlPositive ? "+" : ""}${formatUsdc(
                pnlPositive ? pnl : -pnl,
                4
              )} USDC`}
              sub="Withdrawn + current − deposited"
              tone={pnlPositive ? "positive" : "negative"}
            />
          </div>

          <section className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <h2
                  className="text-sm font-bold tracking-[0.2em] uppercase"
                  style={{ color: "#e7e5e5" }}
                >
                  Your Deposits & Withdrawals
                </h2>
                <p className="text-xs mt-1" style={{ color: "#acabaa" }}>
                  Live from the vault&apos;s Deposit / Withdraw events
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
                style={{
                  backgroundColor: "#131313",
                  border: "1px solid rgba(72,72,72,0.25)",
                }}
              >
                <p className="text-sm" style={{ color: "#737373" }}>
                  Fetching your events from Base Sepolia…
                </p>
              </div>
            ) : deposits.length === 0 && withdrawals.length === 0 ? (
              <div
                className="rounded-2xl p-8 text-center"
                style={{
                  backgroundColor: "#131313",
                  border: "1px solid rgba(72,72,72,0.25)",
                }}
              >
                <span
                  className="material-symbols-outlined block mb-3"
                  style={{ fontSize: "2rem", color: "#a7cbeb" }}
                >
                  hourglass_empty
                </span>
                <p className="text-sm" style={{ color: "#e7e5e5" }}>
                  No activity yet
                </p>
                <p className="text-xs mt-1" style={{ color: "#acabaa" }}>
                  Head to the Vault page and make your first deposit.
                </p>
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                {deposits.map((e) => (
                  <EventRow key={`d-${e.txHash}`} event={e} kind="deposit" />
                ))}
                {withdrawals.map((e) => (
                  <EventRow key={`w-${e.txHash}`} event={e} kind="withdraw" />
                ))}
              </div>
            )}
          </section>
        </>
      )}

      <TradeHistory />
    </div>
  );
}
