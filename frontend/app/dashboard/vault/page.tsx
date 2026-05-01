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
    <div className="flex flex-col gap-8 max-w-6xl">
      {/* Header */}
      <div className="flex items-start justify-between gap-6 flex-wrap">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span
              className="text-[10px] font-bold tracking-[0.2em] uppercase text-muted-foreground"
            >
              On-chain Vault
            </span>
            <span
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] font-bold tracking-widest uppercase bg-card text-primary border border-primary/20"
            >
              <span
                className="inline-block w-1.5 h-1.5 rounded-full bg-primary"
              />
              {CHAIN.name}
            </span>
          </div>
          <h1
            className="text-5xl font-black tracking-[-0.03em] text-foreground"
          >
            Signals Vault
          </h1>
          <p className="mt-3 text-sm max-w-xl text-muted-foreground">
            Deposit USDC, the AI agent trades it on Uniswap V3, and every decision
            is committed on-chain with its reasoning hash. Proof-of-alpha, built in.
          </p>
        </div>

        <a
          href={explorerAddress(VAULT_ADDRESS)}
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-2 text-xs font-mono tracking-tight px-4 py-2.5 rounded-full transition-colors bg-card text-primary border border-primary/20 hover:bg-accent"
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
          className="rounded-2xl p-4 flex items-center gap-3 bg-destructive/10 border border-destructive/30"
        >
          <span className="material-symbols-outlined text-destructive">
            warning
          </span>
          <span className="text-sm flex-1 text-destructive">
            Your wallet is on the wrong network. Switch to <strong>{CHAIN.name}</strong> to deposit & withdraw.
          </span>
          <button
            onClick={() => switchChain({ chainId: CHAIN.id })}
            className="px-4 py-1.5 rounded-full text-xs font-bold tracking-wide transition-all hover:brightness-110 bg-primary text-primary-foreground"
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
          className="rounded-3xl p-10 text-center bg-card border border-border"
        >
          <span
            className="material-symbols-outlined block mb-3 text-[2rem] text-primary"
          >
            account_balance_wallet
          </span>
          <h3 className="text-base font-semibold mb-1 text-foreground">
            Connect your wallet to interact with the vault
          </h3>
          <p className="text-sm text-muted-foreground">
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
