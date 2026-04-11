"use client";

import React, { createContext, useContext, useState, useCallback } from "react";

export interface Wallet {
  id: string;
  name: string;
  icon: string;
  chains: string[];
  installed: boolean;
}

export interface WalletSession {
  connected: boolean;
  address: string | null;
  wallet_id: string | null;
  chain: string | null;
}

interface WalletContextType {
  // State
  session: WalletSession;
  availableWallets: Wallet[];
  isLoading: boolean;
  error: string | null;

  // Actions
  fetchAvailableWallets: (chain?: string) => Promise<void>;
  connectWallet: (walletId: string, chain: string) => Promise<void>;
  disconnectWallet: () => Promise<void>;
  clearError: () => void;
}

const WalletContext = createContext<WalletContextType | undefined>(undefined);

export function WalletProvider({ children }: { children: React.ReactNode }) {
  const [session, setSession] = useState<WalletSession>({
    connected: false,
    address: null,
    wallet_id: null,
    chain: null,
  });

  const [availableWallets, setAvailableWallets] = useState<Wallet[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  const fetchAvailableWallets = useCallback(
    async (chain?: string) => {
      setIsLoading(true);
      setError(null);

      try {
        const url = chain
          ? `${API_BASE}/api/wallet/available/${chain}`
          : `${API_BASE}/api/wallet/available`;

        const response = await fetch(url);
        if (!response.ok) throw new Error("Failed to fetch wallets");

        const wallets = await response.json();
        setAvailableWallets(wallets);
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to fetch wallets";
        setError(message);
        console.error("Wallet fetch error:", message);
      } finally {
        setIsLoading(false);
      }
    },
    [API_BASE]
  );

  const connectWallet = useCallback(
    async (walletId: string, chain: string = "solana") => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`${API_BASE}/api/wallet/connect`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            wallet_id: walletId,
            chain: chain,
          }),
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(
            errorData.detail || "Failed to connect wallet"
          );
        }

        const data = await response.json();

        // Store session
        setSession({
          connected: data.success,
          address: data.address,
          wallet_id: data.wallet_id,
          chain: data.chain,
        });

        // Persist to localStorage
        if (data.success) {
          localStorage.setItem(
            "walletSession",
            JSON.stringify({
              address: data.address,
              wallet_id: data.wallet_id,
              chain: data.chain,
            })
          );
        }
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to connect wallet";
        setError(message);
        console.error("Wallet connection error:", message);
        throw err;
      } finally {
        setIsLoading(false);
      }
    },
    [API_BASE]
  );

  const disconnectWallet = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE}/api/wallet/disconnect`, {
        method: "POST",
      });

      if (!response.ok) throw new Error("Failed to disconnect wallet");

      setSession({
        connected: false,
        address: null,
        wallet_id: null,
        chain: null,
      });

      localStorage.removeItem("walletSession");
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Failed to disconnect wallet";
      setError(message);
      console.error("Wallet disconnection error:", message);
    } finally {
      setIsLoading(false);
    }
  }, [API_BASE]);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return (
    <WalletContext.Provider
      value={{
        session,
        availableWallets,
        isLoading,
        error,
        fetchAvailableWallets,
        connectWallet,
        disconnectWallet,
        clearError,
      }}
    >
      {children}
    </WalletContext.Provider>
  );
}

export function useWallet() {
  const context = useContext(WalletContext);
  if (!context) {
    throw new Error("useWallet must be used within WalletProvider");
  }
  return context;
}
