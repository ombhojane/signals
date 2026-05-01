"use client";

import { useMemo, useState } from "react";
import { useAccount } from "wagmi";
import { Button } from "@/components/ui/button";
import {
  formatUsdc,
  parseUsdc,
  useUserPosition,
  useVaultState,
  useWithdrawFlow,
} from "@/lib/web3/hooks";
import { explorerTx } from "@/lib/web3/constants";

export function WithdrawCard() {
  const { isConnected } = useAccount();
  const { positionOpen } = useVaultState();
  const { shares, shareValueAssets, refetch } = useUserPosition();
  const [amount, setAmount] = useState("");
  const flow = useWithdrawFlow(refetch);

  const amountWei = useMemo(() => parseUsdc(amount), [amount]);
  const balanceOk = amountWei > 0n && amountWei <= shares;
  const busy = flow.status === "awaiting_wallet" || flow.status === "pending";

  const buttonLabel = (() => {
    if (!isConnected) return "Connect wallet";
    if (positionOpen) return "Vault trading — locked";
    if (shares === 0n) return "No shares to redeem";
    if (amountWei === 0n) return "Enter an amount";
    if (!balanceOk) return "Exceeds share balance";
    if (flow.status === "awaiting_wallet") return "Confirm in wallet…";
    if (flow.status === "pending") return "Withdrawing…";
    if (flow.status === "success") return "Withdrawn ✓";
    return `Withdraw ${amount} sVAULT`;
  })();

  const disabled =
    !isConnected ||
    positionOpen ||
    shares === 0n ||
    amountWei === 0n ||
    !balanceOk ||
    busy;

  const setMax = () => setAmount(formatUsdc(shares, 6));

  const estimatedAssets =
    shares > 0n && amountWei > 0n
      ? (amountWei * shareValueAssets) / shares
      : 0n;

  return (
    <div
      className="rounded-3xl p-6 flex flex-col gap-4 bg-card border border-border"
    >
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold tracking-[0.2em] uppercase text-foreground">
          Withdraw
        </h3>
        <span className="text-[10px] tracking-widest uppercase text-muted-foreground">
          sVAULT → USDC
        </span>
      </div>

      <div
        className="rounded-2xl p-4 flex items-center gap-3 bg-background border border-border/50"
      >
        <input
          type="text"
          inputMode="decimal"
          placeholder="0.00"
          value={amount}
          onChange={(e) => setAmount(e.target.value.replace(/[^0-9.]/g, ""))}
          className="bg-transparent flex-1 text-2xl font-mono font-bold outline-none text-foreground placeholder:text-muted-foreground"
          disabled={busy || !isConnected || shares === 0n}
        />
        <button
          type="button"
          onClick={setMax}
          disabled={!isConnected || shares === 0n}
          className="text-[10px] font-semibold tracking-widest uppercase px-3 py-1.5 rounded-full transition-colors disabled:opacity-40 cursor-pointer bg-accent text-primary border border-primary/20 hover:bg-muted"
        >
          Max
        </button>
      </div>

      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span className="tracking-wide">
          Shares: <span className="font-mono">{formatUsdc(shares, 4)}</span>
        </span>
        {amountWei > 0n && estimatedAssets > 0n && (
          <span className="font-mono text-primary">
            ≈ {formatUsdc(estimatedAssets, 4)} USDC
          </span>
        )}
      </div>

      <Button
        onClick={() => flow.run(amount)}
        disabled={disabled}
        className="w-full"
        size="lg"
      >
        {buttonLabel}
      </Button>

      {flow.error && (
        <p className="text-xs text-destructive">
          {flow.error}
        </p>
      )}

      {flow.txHash && (
        <a
          href={explorerTx(flow.txHash)}
          target="_blank"
          rel="noreferrer"
          className="text-xs font-mono tracking-tight flex items-center gap-1.5 transition-colors hover:underline text-primary"
        >
          <span className="material-symbols-outlined" style={{ fontSize: "0.9rem" }}>
            open_in_new
          </span>
          View on BaseScan
        </a>
      )}
    </div>
  );
}
