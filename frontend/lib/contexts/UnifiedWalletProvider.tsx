"use client";

import React from "react";
import { WalletAdapterNetwork } from "@solana/wallet-adapter-base";
import {
  ConnectionProvider,
  WalletProvider as SolanaWalletProvider,
} from "@solana/wallet-adapter-react";
import { WalletModalProvider } from "@solana/wallet-adapter-react-ui";
import {
  PhantomWalletAdapter,
  SolflareWalletAdapter,
} from "@solana/wallet-adapter-wallets";
import { clusterApiUrl } from "@solana/web3.js";
import {
  WagmiProvider,
  createConfig,
  http,
  injected,
} from "wagmi";
import { walletConnect } from "wagmi/connectors";
import {
  mainnet,
  sepolia,
  polygon,
  polygonMumbai,
  arbitrum,
  arbitrumSepolia,
  optimism,
  optimismSepolia,
} from "wagmi/chains";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import "@solana/wallet-adapter-react-ui/styles.css";

// Solana configuration
const solanaNetwork = WalletAdapterNetwork.Mainnet;
const endpoint = clusterApiUrl(solanaNetwork);

const solanaWallets = [
  new PhantomWalletAdapter(),
  new SolflareWalletAdapter(),
];

// Wagmi configuration (no RainbowKit - using simple injected + walletconnect)
const wagmiConfig = createConfig({
  chains: [mainnet, sepolia, polygon, polygonMumbai, arbitrum, arbitrumSepolia, optimism, optimismSepolia],
  connectors: [
    injected(),
    walletConnect({
      projectId: "signals-wallet-connection",
    }),
  ],
  transports: {
    [mainnet.id]: http(),
    [sepolia.id]: http(),
    [polygon.id]: http(),
    [polygonMumbai.id]: http(),
    [arbitrum.id]: http(),
    [arbitrumSepolia.id]: http(),
    [optimism.id]: http(),
    [optimismSepolia.id]: http(),
  },
});

interface UnifiedWalletProviderProps {
  children: React.ReactNode;
}

export function UnifiedWalletProvider({ children }: UnifiedWalletProviderProps) {
  // Create a new QueryClient instance for each provider to avoid shared state
  const [client] = React.useState(() => new QueryClient());

  return (
    <QueryClientProvider client={client}>
      {/* EVM Wallet Provider (Wagmi) */}
      <WagmiProvider config={wagmiConfig}>
        {/* Solana Wallet Provider */}
        <ConnectionProvider endpoint={endpoint}>
          <SolanaWalletProvider wallets={solanaWallets} autoConnect>
            <WalletModalProvider>
              {children}
            </WalletModalProvider>
          </SolanaWalletProvider>
        </ConnectionProvider>
      </WagmiProvider>
    </QueryClientProvider>
  );
}
