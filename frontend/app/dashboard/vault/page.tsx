"use client";

import { useEffect } from "react";
import { useAccount, useChainId, useSwitchChain } from "wagmi";
import { DepositCard } from "@/components/web3/DepositCard";
import { TradeHistory } from "@/components/web3/TradeHistory";
import { VaultStats } from "@/components/web3/VaultStats";
import { WithdrawCard } from "@/components/web3/WithdrawCard";
import { CHAIN, VAULT_ADDRESS, explorerAddress } from "@/lib/web3/constants";

export default function VaultPage() {
  const { isConnected } = useAccount();
  const chainId = useChainId();
  const { switchChain } = useSwitchChain();
  const wrongNetwork = isConnected && chainId !== CHAIN.id;

  // Auto-switch wallet to Base Sepolia when the vault page loads.
  // This prompts MetaMask once; if the user rejects, the wrong-network
  // banner below stays visible with a manual "Switch" button.
  useEffect(() => {
    if (wrongNetwork && switchChain) {
      switchChain({ chainId: CHAIN.id });
    }
  }, [wrongNetwork, switchChain]);

  return (
    <div className="flex flex-col gap-8 p-8 max-w-6xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-6 flex-wrap">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span
              className="text-[10px] font-bold tracking-[0.2em] uppercase"
              style={{ color: "#acabaa" }}
            >
              On-chain Vault
            </span>
            <span
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase"
              style={{
                backgroundColor: "#131313",
                color: "#a7cbeb",
                border: "1px solid rgba(167,203,235,0.2)",
              }}
            >
              <span
                className="inline-block w-1.5 h-1.5 rounded-full"
                style={{ backgroundColor: "#a7cbeb" }}
              />
              {CHAIN.name}
            </span>
          </div>
          <h1
            className="text-5xl font-black tracking-[-0.03em]"
            style={{ color: "#e7e5e5" }}
          >
            Signals Vault
          </h1>
          <p className="mt-3 text-sm max-w-xl" style={{ color: "#acabaa" }}>
            Deposit USDC, the AI agent trades it on Uniswap V3, and every decision
            is committed on-chain with its reasoning hash. Proof-of-alpha, built in.
          </p>
        </div>

        <a
          href={explorerAddress(VAULT_ADDRESS)}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2 text-xs font-mono tracking-tight px-4 py-2.5 rounded-full transition-colors"
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

      {/* Wrong-network banner */}
      {wrongNetwork && (
        <div
          className="rounded-2xl p-4 flex items-center gap-3"
          style={{
            backgroundColor: "rgba(238,125,119,0.08)",
            border: "1px solid rgba(238,125,119,0.3)",
          }}
        >
          <span className="material-symbols-outlined" style={{ color: "#ee7d77" }}>
            warning
          </span>
          <span className="text-sm flex-1" style={{ color: "#ee7d77" }}>
            Your wallet is on the wrong network. Switch to <strong>{CHAIN.name}</strong> to deposit & withdraw.
          </span>
          <button
            onClick={() => switchChain({ chainId: CHAIN.id })}
            className="px-4 py-1.5 rounded-full text-xs font-bold tracking-wide transition-all hover:brightness-110"
            style={{ backgroundColor: "#a7cbeb", color: "#1e435e" }}
          >
            Switch to {CHAIN.name}
          </button>
        </div>
      )}

      {/* Stats */}
      <VaultStats />

      {/* Actions */}
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
            Connect your wallet to interact with the vault
          </h3>
          <p className="text-sm" style={{ color: "#acabaa" }}>
            Use the Connect Wallet button in the sidebar.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <DepositCard />
          <WithdrawCard />
        </div>
      )}

      {/* Trade history */}
      <TradeHistory />
    </div>
  );
}
