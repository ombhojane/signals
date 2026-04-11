"use client";

import { useEffect, useState } from "react";
import { useWallet as useSolanaWallet } from "@solana/wallet-adapter-react";
import { WalletMultiButton } from "@solana/wallet-adapter-react-ui";
import { useAccount, useConnect, useDisconnect } from "wagmi";
import { ConnectButton } from "@rainbow-me/rainbowkit";

export function WalletConnectionButton() {
  const [mounted, setMounted] = useState(false);
  const [chainType, setChainType] = useState<"solana" | "evm">("solana");

  // Solana wallet
  const solanaWallet = useSolanaWallet();

  // EVM wallet
  const { address: evmAddress } = useAccount();

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <div className="flex items-center gap-4">
      {/* Chain Selector */}
      <div className="flex gap-2 bg-neutral-800 p-1 rounded-full">
        <button
          onClick={() => setChainType("solana")}
          className={`px-3 py-1 rounded-full text-sm font-medium transition-all ${
            chainType === "solana"
              ? "bg-blue-500 text-white"
              : "text-neutral-300 hover:text-white"
          }`}
        >
          Solana
        </button>
        <button
          onClick={() => setChainType("evm")}
          className={`px-3 py-1 rounded-full text-sm font-medium transition-all ${
            chainType === "evm"
              ? "bg-blue-500 text-white"
              : "text-neutral-300 hover:text-white"
          }`}
        >
          EVM
        </button>
      </div>

      {/* Wallet Buttons */}
      {chainType === "solana" ? (
        <WalletMultiButton className="bg-blue-600! hover:bg-blue-700! text-white! rounded-full! px-6! py-2! font-semibold!" />
      ) : (
        <ConnectButton />
      )}

      {/* Status */}
      {solanaWallet.connected && chainType === "solana" && (
        <span className="text-xs text-green-400 font-medium">
          ✓ {solanaWallet.publicKey?.toString().slice(0, 8)}...
        </span>
      )}

      {evmAddress && chainType === "evm" && (
        <span className="text-xs text-green-400 font-medium">
          ✓ {evmAddress.slice(0, 8)}...
        </span>
      )}
    </div>
  );
}
