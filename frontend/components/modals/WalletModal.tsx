"use client";

import { useEffect, useState } from "react";
import { useWallet } from "@/lib/contexts/WalletContext";

interface WalletModalProps {
  isOpen: boolean;
  onClose: () => void;
  selectedChain?: string;
}

export function WalletModal({
  isOpen,
  onClose,
  selectedChain = "solana",
}: WalletModalProps) {
  const {
    availableWallets,
    isLoading,
    error,
    fetchAvailableWallets,
    connectWallet,
    clearError,
  } = useWallet();

  const [connecting, setConnecting] = useState<string | null>(null);
  const [chain, setChain] = useState(selectedChain);

  useEffect(() => {
    if (isOpen) {
      fetchAvailableWallets(chain);
    }
  }, [isOpen, chain, fetchAvailableWallets]);

  if (!isOpen) return null;

  const handleConnectWallet = async (walletId: string) => {
    try {
      setConnecting(walletId);
      await connectWallet(walletId, chain);
      // Close modal after successful connection
      setTimeout(() => {
        onClose();
      }, 500);
    } catch (err) {
      console.error("Connection failed:", err);
    } finally {
      setConnecting(null);
    }
  };

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div
          className="bg-neutral-900 rounded-2xl shadow-2xl max-w-md w-full p-6 border border-neutral-800"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">Connect Wallet</h2>
            <button
              onClick={onClose}
              className="text-neutral-400 hover:text-white transition-colors text-2xl leading-none"
            >
              ×
            </button>
          </div>

          {/* Chain Selector */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-neutral-300 mb-3">
              Select Network
            </label>
            <select
              value={chain}
              onChange={(e) => setChain(e.target.value)}
              className="w-full px-4 py-3 rounded-lg bg-neutral-800 text-white border border-neutral-700 focus:border-blue-500 focus:outline-none transition-colors"
              disabled={connecting !== null}
            >
              <option value="solana">Solana</option>
              <option value="ethereum">Ethereum</option>
              <option value="polygon">Polygon</option>
              <option value="arbitrum">Arbitrum</option>
              <option value="optimism">Optimism</option>
            </select>
          </div>

          {/* Error Message */}
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-300 text-sm flex justify-between items-center">
              <span>{error}</span>
              <button
                onClick={clearError}
                className="text-red-300 hover:text-red-200 text-lg leading-none"
              >
                ×
              </button>
            </div>
          )}

          {/* Wallets List */}
          <div className="space-y-3 mb-6">
            {isLoading && !availableWallets.length ? (
              <div className="py-8 text-center">
                <div className="inline-block w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                <p className="text-neutral-400 mt-2">Loading wallets...</p>
              </div>
            ) : availableWallets.length === 0 ? (
              <p className="text-center text-neutral-400 py-8">
                No wallets available for {chain}
              </p>
            ) : (
              availableWallets.map((wallet) => (
                <button
                  key={wallet.id}
                  onClick={() => handleConnectWallet(wallet.id)}
                  disabled={connecting !== null}
                  className="w-full flex items-center gap-4 p-4 rounded-lg bg-neutral-800 hover:bg-neutral-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed border border-neutral-700 hover:border-neutral-600"
                >
                  {/* Icon */}
                  <span className="text-3xl">{wallet.icon}</span>

                  {/* Wallet Info */}
                  <div className="flex-1 text-left">
                    <p className="font-semibold text-white">{wallet.name}</p>
                    <p className="text-xs text-neutral-400">
                      {wallet.chains.join(", ")}
                    </p>
                  </div>

                  {/* Loading indicator */}
                  {connecting === wallet.id && (
                    <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
                  )}

                  {/* Installed badge */}
                  {!connecting && wallet.installed && (
                    <span className="text-xs font-medium text-green-400">
                      ✓ Ready
                    </span>
                  )}
                </button>
              ))
            )}
          </div>

          {/* Footer Info */}
          <div className="text-center text-xs text-neutral-500">
            <p>Don't have a wallet?</p>
            <button className="text-blue-400 hover:text-blue-300 transition-colors font-medium mt-1">
              Learn more about wallets
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
