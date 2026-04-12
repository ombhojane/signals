import { baseSepolia } from "wagmi/chains";

export const CHAIN = baseSepolia;

export const VAULT_ADDRESS = (process.env.NEXT_PUBLIC_VAULT_ADDRESS ??
  "0xdf57590D27f02BcFA8522d4a59E07Ca7a31b9a6a") as `0x${string}`;

export const USDC_ADDRESS =
  "0x036CbD53842c5426634e7929541eC2318f3dCF7e" as const;

export const USDC_DECIMALS = 6;

export const EXPLORER_BASE = "https://sepolia.basescan.org";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8001";

export const explorerTx = (hash: string): string => `${EXPLORER_BASE}/tx/${hash}`;
export const explorerAddress = (addr: string): string =>
  `${EXPLORER_BASE}/address/${addr}`;
