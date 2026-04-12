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
      className="rounded-3xl p-6 flex flex-col gap-4"
      style={{
        backgroundColor: "#131313",
        border: "1px solid rgba(72,72,72,0.25)",
      }}
    >
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold tracking-[0.2em] uppercase" style={{ color: "#e7e5e5" }}>
          Withdraw
        </h3>
        <span className="text-[10px] tracking-widest uppercase" style={{ color: "#acabaa" }}>
          sVAULT → USDC
        </span>
      </div>

      <div
        className="rounded-2xl p-4 flex items-center gap-3"
        style={{ backgroundColor: "#0e0e0e", border: "1px solid rgba(72,72,72,0.2)" }}
      >
        <input
          type="text"
          inputMode="decimal"
          placeholder="0.00"
          value={amount}
          onChange={(e) => setAmount(e.target.value.replace(/[^0-9.]/g, ""))}
          className="bg-transparent flex-1 text-2xl font-mono font-bold outline-none placeholder:text-neutral-700"
          style={{ color: "#e7e5e5" }}
          disabled={busy || !isConnected || shares === 0n}
        />
        <button
          type="button"
          onClick={setMax}
          disabled={!isConnected || shares === 0n}
          className="text-[10px] font-semibold tracking-widest uppercase px-3 py-1.5 rounded-full transition-colors disabled:opacity-40"
          style={{
            backgroundColor: "#191a1a",
            color: "#a7cbeb",
            border: "1px solid rgba(167,203,235,0.2)",
          }}
        >
          Max
        </button>
      </div>

      <div className="flex items-center justify-between text-xs" style={{ color: "#acabaa" }}>
        <span className="tracking-wide">
          Shares: <span className="font-mono">{formatUsdc(shares, 4)}</span>
        </span>
        {amountWei > 0n && estimatedAssets > 0n && (
          <span className="font-mono" style={{ color: "#a7cbeb" }}>
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
        <p className="text-xs" style={{ color: "#ee7d77" }}>
          {flow.error}
        </p>
      )}

      {flow.txHash && (
        <a
          href={explorerTx(flow.txHash)}
          target="_blank"
          rel="noreferrer"
          className="text-xs font-mono tracking-tight flex items-center gap-1.5 transition-colors hover:underline"
          style={{ color: "#a7cbeb" }}
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
