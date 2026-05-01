"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useAccount, useChainId, usePublicClient, useWriteContract } from "wagmi";
import { Button } from "@/components/ui/button";
import { erc20Abi, vaultAbi } from "@/lib/web3/abi";
import {
  CHAIN,
  USDC_ADDRESS,
  VAULT_ADDRESS,
  explorerTx,
} from "@/lib/web3/constants";
import {
  formatUsdc,
  friendlyError,
  parseUsdc,
  useUserPosition,
  useVaultState,
} from "@/lib/web3/hooks";

type Stage = "idle" | "approving" | "depositing" | "success" | "error";

export function DepositCard() {
  const { address, isConnected } = useAccount();
  const chainId = useChainId();
  const { positionOpen } = useVaultState();
  const { usdcBalance, usdcAllowance, refetch } = useUserPosition();
  const publicClient = usePublicClient({ chainId: CHAIN.id });
  const { writeContractAsync } = useWriteContract();
  const queryClient = useQueryClient();

  const [amount, setAmount] = useState("");
  const [stage, setStage] = useState<Stage>("idle");
  const [error, setError] = useState<string | undefined>();
  const [lastTxHash, setLastTxHash] = useState<`0x${string}` | undefined>();

  const amountWei = useMemo(() => parseUsdc(amount), [amount]);
  const needsApprove = amountWei > 0n && usdcAllowance < amountWei;
  const balanceOk = amountWei > 0n && amountWei <= usdcBalance;
  const wrongNetwork = isConnected && chainId !== CHAIN.id;
  const busy = stage === "approving" || stage === "depositing";

  const buttonLabel = (() => {
    if (!isConnected) return "Connect wallet";
    if (wrongNetwork) return "Switch to Base Sepolia";
    if (positionOpen) return "Vault trading — locked";
    if (amountWei === 0n) return "Enter an amount";
    if (!balanceOk) return "Insufficient USDC";
    if (stage === "approving") return "Approving…";
    if (stage === "depositing") return "Depositing…";
    if (stage === "success") return "Deposited ✓";
    return needsApprove ? `Approve & Deposit ${amount} USDC` : `Deposit ${amount} USDC`;
  })();

  const disabled =
    !isConnected ||
    wrongNetwork ||
    positionOpen ||
    amountWei === 0n ||
    !balanceOk ||
    busy;

  const setMax = () => setAmount(formatUsdc(usdcBalance, 6));

  const handleClick = async () => {
    if (!address || !publicClient || amountWei === 0n) return;

    setError(undefined);
    setStage("idle");

    try {
      // 1. Approve only if current allowance is insufficient
      if (usdcAllowance < amountWei) {
        setStage("approving");
        const approveHash = await writeContractAsync({
          address: USDC_ADDRESS,
          abi: erc20Abi,
          functionName: "approve",
          args: [VAULT_ADDRESS, amountWei],
          chainId: CHAIN.id,
        });
        setLastTxHash(approveHash);

        const approveReceipt = await publicClient.waitForTransactionReceipt({
          hash: approveHash,
        });
        if (approveReceipt.status !== "success") {
          throw new Error("Approval reverted");
        }
      }

      // 2. Deposit
      setStage("depositing");
      const depositHash = await writeContractAsync({
        address: VAULT_ADDRESS,
        abi: vaultAbi,
        functionName: "deposit",
        args: [amountWei, address],
        chainId: CHAIN.id,
      });
      setLastTxHash(depositHash);

      const depositReceipt = await publicClient.waitForTransactionReceipt({
        hash: depositHash,
      });
      if (depositReceipt.status !== "success") {
        throw new Error("Deposit reverted");
      }

      // 3. Force refresh of all on-chain reads
      await queryClient.invalidateQueries();
      refetch();

      setStage("success");
      setAmount("");
    } catch (e) {
      setError(friendlyError(e));
      setStage("error");
    }
  };

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
          Deposit
        </h3>
        <span className="text-[10px] tracking-widest uppercase" style={{ color: "#acabaa" }}>
          USDC → sVAULT
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
          disabled={busy || !isConnected}
        />
        <button
          type="button"
          onClick={setMax}
          disabled={!isConnected || usdcBalance === 0n}
          className="text-[10px] font-semibold tracking-widest uppercase px-3 py-1.5 rounded-full transition-colors disabled:opacity-40 cursor-pointer"
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
          Wallet: <span className="font-mono">{formatUsdc(usdcBalance, 4)}</span> USDC
        </span>
        {!needsApprove && amountWei > 0n && (
          <span style={{ color: "#a7cbeb" }}>Approved ✓</span>
        )}
      </div>

      <Button
        onClick={handleClick}
        disabled={disabled}
        className="w-full"
        size="lg"
      >
        {buttonLabel}
      </Button>

      {error && (
        <p className="text-xs" style={{ color: "#ee7d77" }}>
          {error}
        </p>
      )}

      {lastTxHash && (
        <a
          href={explorerTx(lastTxHash)}
          target="_blank"
          rel="noreferrer"
          className="text-xs font-mono tracking-tight flex items-center gap-1.5 transition-colors hover:underline"
          style={{ color: "#a7cbeb" }}
        >
          <span className="material-symbols-outlined" style={{ fontSize: "0.9rem" }}>
            open_in_new
          </span>
          View last tx on BaseScan
        </a>
      )}
    </div>
  );
}
