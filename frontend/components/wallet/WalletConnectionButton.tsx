"use client";

import { useEffect, useState } from "react";
import { useWallet as useSolanaWallet } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import { useAccount, useConnect, useDisconnect, useChainId, useSwitchChain } from "wagmi";

// ── EVM Wallet Dropdown ────────────────────────────────────────────────────────
function EVMWalletButton() {
  const { address, isConnected } = useAccount();
  const { connectors, connect, isPending } = useConnect();
  const { disconnect } = useDisconnect();
  const chainId = useChainId();
  const { chains, switchChain } = useSwitchChain();
  const [open, setOpen] = useState(false);

  const shortAddr = address
    ? `${address.slice(0, 6)}…${address.slice(-4)}`
    : null;

  if (isConnected && address) {
    return (
      <div className="relative">
        <button
          onClick={() => setOpen((o) => !o)}
          className="flex items-center gap-2 bg-violet-600 hover:bg-violet-700 text-white text-sm font-semibold px-4 py-2 rounded-full transition-all cursor-pointer"
        >
          <span className="w-2 h-2 rounded-full bg-green-400 inline-block" />
          {shortAddr}
          <svg className="w-3 h-3 opacity-70" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clipRule="evenodd" />
          </svg>
        </button>

        {open && (
          <div className="absolute right-0 mt-2 w-52 bg-neutral-900 border border-neutral-700 rounded-xl shadow-2xl z-50 overflow-hidden">
            {/* Chain switcher */}
            <div className="px-3 py-2 border-b border-neutral-800">
              <p className="text-xs text-neutral-400 mb-1 font-medium">Switch chain</p>
              <div className="flex flex-col gap-1">
                {chains.map((c) => (
                  <button
                    key={c.id}
                    onClick={() => { switchChain({ chainId: c.id }); setOpen(false); }}
                    className={`text-left text-xs px-2 py-1 rounded-lg transition-colors cursor-pointer ${
                      c.id === chainId
                        ? "bg-violet-600/30 text-violet-300"
                        : "text-neutral-300 hover:bg-neutral-800"
                    }`}
                  >
                    {c.id === chainId ? "✓ " : ""}{c.name}
                  </button>
                ))}
              </div>
            </div>
            {/* Disconnect */}
            <button
              onClick={() => { disconnect(); setOpen(false); }}
              className="w-full text-left px-4 py-3 text-sm text-red-400 hover:bg-red-500/10 transition-colors cursor-pointer"
            >
              Disconnect
            </button>
          </div>
        )}
      </div>
    );
  }

  // Not connected — show wallet picker
  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        disabled={isPending}
        className="flex items-center gap-2 bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white text-sm font-semibold px-4 py-2 rounded-full transition-all cursor-pointer"
      >
        {isPending ? "Connecting…" : "Connect EVM Wallet"}
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-56 bg-neutral-900 border border-neutral-700 rounded-xl shadow-2xl z-50 overflow-hidden">
          <p className="px-4 pt-3 pb-1 text-xs text-neutral-400 font-medium uppercase tracking-wide">
            Choose wallet
          </p>
          {connectors.map((connector) => (
            <button
              key={connector.uid}
              onClick={() => { connect({ connector }); setOpen(false); }}
              className="w-full flex items-center gap-3 px-4 py-3 text-sm text-neutral-200 hover:bg-neutral-800 transition-colors cursor-pointer"
            >
              {/* Wallet icon if available */}
              {connector.icon && (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={connector.icon} alt="" className="w-5 h-5 rounded" />
              )}
              <span>{connector.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main Component ─────────────────────────────────────────────────────────────
export function WalletConnectionButton() {
  const [mounted, setMounted] = useState(false);
  const [chainType, setChainType] = useState<"solana" | "evm">("solana");

  const solanaWallet = useSolanaWallet();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="flex items-center gap-3">
      {/* Chain Selector Desktop */}
      <div className="hidden sm:flex gap-1 bg-neutral-800 p-1 rounded-full">
        <button
          onClick={() => setChainType("solana")}
          className={`px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
            chainType === "solana"
              ? "bg-blue-500 text-white shadow"
              : "text-neutral-400 hover:text-white"
          }`}
        >
          Solana
        </button>
        <button
          onClick={() => setChainType("evm")}
          className={`px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
            chainType === "evm"
              ? "bg-violet-500 text-white shadow"
              : "text-neutral-400 hover:text-white"
          }`}
        >
          EVM
        </button>
      </div>

      {/* Chain Selector Mobile (Toggle) */}
      <div className="flex sm:hidden">
        <button
          onClick={() => setChainType(chainType === "solana" ? "evm" : "solana")}
          className={`flex items-center gap-1.5 min-w-[54px] px-2.5 py-1.5 rounded-full text-[10px] font-bold tracking-wider transition-all active:scale-95 cursor-pointer ${
            chainType === "solana" ? "bg-blue-500 text-white" : "bg-violet-500 text-white"
          }`}
        >
          {chainType === "solana" ? "SOL" : "EVM"}
          <span className="material-symbols-outlined opacity-70" style={{ fontSize: '10px' }}>swap_horiz</span>
        </button>
      </div>

      {/* Wallet Button */}
      {chainType === "solana" ? (
        <WalletMultiButton
          style={{
            background: "rgb(59 130 246)",
            borderRadius: "9999px",
            fontSize: "0.875rem",
            fontWeight: 600,
            padding: "0.1rem 1.2rem",
            height: "auto",
          }}
        />
      ) : (
        <EVMWalletButton />
      )}
    </div>
  );
}
