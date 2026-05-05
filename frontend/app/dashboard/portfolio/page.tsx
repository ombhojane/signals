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
  const colorClass = accent || tone === "positive"
    ? "text-primary"
    : tone === "negative"
    ? "text-destructive"
    : "text-foreground";

  return (
    <div className="rounded-2xl p-6 flex flex-col gap-2 bg-card border border-border">
      <span className="text-[10px] font-semibold tracking-[0.2em] uppercase text-muted-foreground">
        {label}
      </span>
      <span className={`text-3xl font-black font-mono tracking-tight ${colorClass}`}>
        {value}
      </span>
      {sub ? (
        <span className="text-xs tracking-wide text-muted-foreground">{sub}</span>
      ) : null}
    </div>
  );
}

function shortHash(hash: string, head = 8, tail = 6): string {
  if (hash.length <= head + tail + 3) return hash;
  return `${hash.slice(0, head)}…${hash.slice(-tail)}`;
}

function EventRow({ event, kind }: { event: UserDepositEvent; kind: "deposit" | "withdraw" }) {
  const isDeposit = kind === "deposit";
  const iconClass = isDeposit ? "text-primary bg-primary/20 border-primary/40" : "text-destructive bg-destructive/20 border-destructive/40";
  const badgeClass = isDeposit ? "text-primary bg-primary/15 border-primary/30" : "text-destructive bg-destructive/15 border-destructive/30";
  const label = isDeposit ? "DEPOSIT" : "WITHDRAW";
  const symbol = isDeposit ? "south_east" : "north_east";

  return (
    <a
      href={explorerTx(event.txHash)}
      target="_blank"
      rel="noreferrer"
      className="flex items-center gap-4 rounded-2xl p-4 transition-colors hover:bg-accent bg-card border border-border"
    >
      <div className={`rounded-full h-8 w-8 flex items-center justify-center shrink-0 border ${iconClass}`}>
        <span className="material-symbols-outlined" style={{ fontSize: "1rem" }}>
          {symbol}
        </span>
      </div>

      <div className="flex-1 min-w-0 flex items-center gap-3 flex-wrap">
        <span className={`text-[10px] font-bold tracking-[0.15em] uppercase px-2 py-0.5 rounded-full border ${badgeClass}`}>
          {label}
        </span>
        <span className="text-sm font-mono font-bold text-foreground">
          {formatUsdc(event.assets, 4)} USDC
        </span>
        <span className="text-xs font-mono text-muted-foreground">
          · {formatUsdc(event.shares, 4)} sVAULT
        </span>
      </div>

      <span className="text-[10px] font-mono tracking-tight text-muted-foreground/50">
        {shortHash(event.txHash)}
      </span>
      <span className="material-symbols-outlined shrink-0 text-muted-foreground/50" style={{ fontSize: "1rem" }}>
        open_in_new
      </span>
    </a>
  );
}

export default function ActivityPage() {
  const { isConnected } = useAccount();
  const { shares, shareValueAssets } = useUserPosition();
  const { deposits, withdrawals, totalDeposited, totalWithdrawn, isLoading, refetch } = useUserActivity();

  const netValue = shareValueAssets + totalWithdrawn;
  const pnl = totalDeposited === 0n ? 0n : netValue - totalDeposited;
  const pnlPositive = pnl >= 0n;

  return (
    <div className="flex flex-col gap-8 max-w-6xl">
      <div className="flex items-start justify-between gap-6 flex-wrap">
        <div>
          <h1 className="text-4xl md:text-5xl font-bold tracking-tight mt-2 text-foreground">
            Your Activity
          </h1>
          <p className="mt-3 text-lg md:text-xl text-muted-foreground font-light leading-relaxed max-w-2xl">
            Your personal vault history — every deposit, every withdrawal, and
            your current share position. All read straight from Base Sepolia.
          </p>
        </div>

        <a
          href={explorerAddress(VAULT_ADDRESS)}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2 text-xs font-mono tracking-tight px-4 py-2.5 rounded-full transition-colors shrink-0 bg-card text-primary border border-primary/20 hover:bg-accent"
        >
          <span className="material-symbols-outlined" style={{ fontSize: "0.9rem" }}>open_in_new</span>
          Vault contract
        </a>
      </div>

      {!isConnected ? (
        <div className="rounded-3xl p-10 text-center bg-card border border-border">
          <span className="material-symbols-outlined block mb-3 text-[2rem] text-primary">
            account_balance_wallet
          </span>
          <h3 className="text-base font-semibold mb-1 text-foreground">
            Connect your wallet to see your activity
          </h3>
          <p className="text-sm text-muted-foreground">
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
              value={`${pnlPositive ? "+" : ""}${formatUsdc(pnlPositive ? pnl : -pnl, 4)} USDC`}
              sub="Withdrawn + current − deposited"
              tone={pnlPositive ? "positive" : "negative"}
            />
          </div>

          <section className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-bold tracking-[0.2em] uppercase text-foreground">
                  Your Deposits & Withdrawals
                </h2>
                <p className="text-xs mt-1 text-muted-foreground">
                  Live from the vault&apos;s Deposit / Withdraw events
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
              <div className="rounded-2xl p-8 text-center bg-card border border-border">
                <p className="text-sm text-muted-foreground/50">Fetching your events from Base Sepolia…</p>
              </div>
            ) : deposits.length === 0 && withdrawals.length === 0 ? (
              <div className="rounded-2xl p-8 text-center bg-card border border-border">
                <span className="material-symbols-outlined block mb-3 text-[2rem] text-primary">
                  hourglass_empty
                </span>
                <p className="text-sm text-foreground">No activity yet</p>
                <p className="text-xs mt-1 text-muted-foreground">
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
