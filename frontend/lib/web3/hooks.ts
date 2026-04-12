"use client";

import { useEffect, useMemo, useState } from "react";
import { decodeEventLog, parseAbiItem } from "viem";
import {
  useAccount,
  usePublicClient,
  useReadContract,
  useReadContracts,
  useWaitForTransactionReceipt,
  useWriteContract,
} from "wagmi";
import { erc20Abi, vaultAbi } from "./abi";
import { CHAIN, USDC_ADDRESS, USDC_DECIMALS, VAULT_ADDRESS } from "./constants";

export interface VaultState {
  totalAssets: bigint;
  totalSupply: bigint;
  positionOpen: boolean;
  sharePriceUsdc: number;
  isLoading: boolean;
}

export function useVaultState(): VaultState {
  const { data, isLoading } = useReadContracts({
    contracts: [
      { address: VAULT_ADDRESS, abi: vaultAbi, functionName: "totalAssets", chainId: CHAIN.id },
      { address: VAULT_ADDRESS, abi: vaultAbi, functionName: "totalSupply", chainId: CHAIN.id },
      { address: VAULT_ADDRESS, abi: vaultAbi, functionName: "positionOpen", chainId: CHAIN.id },
    ],
    query: { refetchInterval: 10_000 },
  });

  const totalAssets = (data?.[0]?.result as bigint | undefined) ?? 0n;
  const totalSupply = (data?.[1]?.result as bigint | undefined) ?? 0n;
  const positionOpen = (data?.[2]?.result as boolean | undefined) ?? false;

  const sharePriceUsdc =
    totalSupply > 0n ? Number(totalAssets) / Number(totalSupply) : 1;

  return { totalAssets, totalSupply, positionOpen, sharePriceUsdc, isLoading };
}

export interface UserPosition {
  shares: bigint;
  shareValueAssets: bigint;
  usdcBalance: bigint;
  usdcAllowance: bigint;
  refetch: () => void;
  isLoading: boolean;
}

export function useUserPosition(): UserPosition {
  const { address } = useAccount();
  const enabled = Boolean(address);

  const { data, isLoading, refetch } = useReadContracts({
    contracts: enabled
      ? [
          {
            address: VAULT_ADDRESS,
            abi: vaultAbi,
            functionName: "balanceOf",
            args: [address!],
            chainId: CHAIN.id,
          },
          {
            address: USDC_ADDRESS,
            abi: erc20Abi,
            functionName: "balanceOf",
            args: [address!],
            chainId: CHAIN.id,
          },
          {
            address: USDC_ADDRESS,
            abi: erc20Abi,
            functionName: "allowance",
            args: [address!, VAULT_ADDRESS],
            chainId: CHAIN.id,
          },
        ]
      : [],
    query: { enabled, refetchInterval: 10_000 },
  });

  const shares = (data?.[0]?.result as bigint | undefined) ?? 0n;
  const usdcBalance = (data?.[1]?.result as bigint | undefined) ?? 0n;
  const usdcAllowance = (data?.[2]?.result as bigint | undefined) ?? 0n;

  const { data: shareValueData, refetch: refetchShareValue } = useReadContract({
    address: VAULT_ADDRESS,
    abi: vaultAbi,
    functionName: "convertToAssets",
    args: [shares],
    chainId: CHAIN.id,
    query: { enabled: shares > 0n },
  });

  const shareValueAssets = (shareValueData as bigint | undefined) ?? 0n;

  return {
    shares,
    shareValueAssets,
    usdcBalance,
    usdcAllowance,
    refetch: () => {
      refetch();
      refetchShareValue();
    },
    isLoading,
  };
}

export type TxStatus =
  | "idle"
  | "awaiting_wallet"
  | "pending"
  | "success"
  | "error";

export interface DepositHandle {
  status: TxStatus;
  step: "approve" | "deposit" | "done";
  error?: string;
  txHash?: `0x${string}`;
  run: (amountUsdc: string) => Promise<void>;
  reset: () => void;
}

export function useDepositFlow(onSuccess?: () => void): DepositHandle {
  const { address } = useAccount();
  const { writeContractAsync } = useWriteContract();

  const [status, setStatus] = useState<TxStatus>("idle");
  const [step, setStep] = useState<"approve" | "deposit" | "done">("approve");
  const [error, setError] = useState<string | undefined>();
  const [txHash, setTxHash] = useState<`0x${string}` | undefined>();

  const { isSuccess: txConfirmed } = useWaitForTransactionReceipt({
    hash: txHash,
    chainId: CHAIN.id,
    query: { enabled: Boolean(txHash) },
  });

  useEffect(() => {
    if (txConfirmed && status === "pending") {
      if (step === "approve") {
        setStep("deposit");
        setStatus("idle");
      } else {
        setStep("done");
        setStatus("success");
        onSuccess?.();
      }
    }
  }, [txConfirmed, status, step, onSuccess]);

  const reset = () => {
    setStatus("idle");
    setStep("approve");
    setError(undefined);
    setTxHash(undefined);
  };

  const run = async (amountUsdc: string) => {
    if (!address) {
      setError("Wallet not connected");
      setStatus("error");
      return;
    }

    const amount = parseUsdc(amountUsdc);
    if (amount <= 0n) {
      setError("Enter a positive amount");
      setStatus("error");
      return;
    }

    setError(undefined);

    try {
      if (step === "approve") {
        setStatus("awaiting_wallet");
        const hash = await writeContractAsync({
          address: USDC_ADDRESS,
          abi: erc20Abi,
          functionName: "approve",
          args: [VAULT_ADDRESS, amount],
          chainId: CHAIN.id,
        });
        setTxHash(hash);
        setStatus("pending");
        return;
      }

      if (step === "deposit") {
        setStatus("awaiting_wallet");
        const hash = await writeContractAsync({
          address: VAULT_ADDRESS,
          abi: vaultAbi,
          functionName: "deposit",
          args: [amount, address],
          chainId: CHAIN.id,
        });
        setTxHash(hash);
        setStatus("pending");
      }
    } catch (e: unknown) {
      setError(friendlyError(e));
      setStatus("error");
    }
  };

  return { status, step, error, txHash, run, reset };
}

export interface WithdrawHandle {
  status: TxStatus;
  error?: string;
  txHash?: `0x${string}`;
  run: (shareAmount: string) => Promise<void>;
  reset: () => void;
}

export function useWithdrawFlow(onSuccess?: () => void): WithdrawHandle {
  const { address } = useAccount();
  const { writeContractAsync } = useWriteContract();

  const [status, setStatus] = useState<TxStatus>("idle");
  const [error, setError] = useState<string | undefined>();
  const [txHash, setTxHash] = useState<`0x${string}` | undefined>();

  const { isSuccess: txConfirmed } = useWaitForTransactionReceipt({
    hash: txHash,
    chainId: CHAIN.id,
    query: { enabled: Boolean(txHash) },
  });

  useEffect(() => {
    if (txConfirmed && status === "pending") {
      setStatus("success");
      onSuccess?.();
    }
  }, [txConfirmed, status, onSuccess]);

  const reset = () => {
    setStatus("idle");
    setError(undefined);
    setTxHash(undefined);
  };

  const run = async (shareAmount: string) => {
    if (!address) {
      setError("Wallet not connected");
      setStatus("error");
      return;
    }

    const shares = parseUsdc(shareAmount);
    if (shares <= 0n) {
      setError("Enter a positive amount");
      setStatus("error");
      return;
    }

    setError(undefined);

    try {
      setStatus("awaiting_wallet");
      const hash = await writeContractAsync({
        address: VAULT_ADDRESS,
        abi: vaultAbi,
        functionName: "redeem",
        args: [shares, address, address],
        chainId: CHAIN.id,
      });
      setTxHash(hash);
      setStatus("pending");
    } catch (e: unknown) {
      setError(friendlyError(e));
      setStatus("error");
    }
  };

  return { status, error, txHash, run, reset };
}

export interface TradeEvent {
  txHash: `0x${string}`;
  blockNumber: bigint;
  tokenIn: `0x${string}`;
  tokenOut: `0x${string}`;
  amountIn: bigint;
  amountOut: bigint;
  reasoningHash: `0x${string}`;
  confidence: number;
  timestamp: bigint;
}

const TRADE_EVENT = parseAbiItem(
  "event TradeExecuted(address indexed tokenIn, address indexed tokenOut, uint256 amountIn, uint256 amountOut, bytes32 indexed reasoningHash, uint8 confidence, uint256 timestamp)"
);

const DEPOSIT_EVENT = parseAbiItem(
  "event Deposit(address indexed sender, address indexed owner, uint256 assets, uint256 shares)"
);

const WITHDRAW_EVENT = parseAbiItem(
  "event Withdraw(address indexed sender, address indexed receiver, address indexed owner, uint256 assets, uint256 shares)"
);

// Base Sepolia public RPC caps eth_getLogs at 10,000 blocks per call.
// We chunk at 9,000 to stay under that safely.
const LOG_CHUNK_SIZE = 9_000n;
const LOG_WINDOW_BLOCKS = 100_000n; // ~55 hours on Base Sepolia

async function chunkedGetLogs<T>(
  fetcher: (fromBlock: bigint, toBlock: bigint) => Promise<T[]>,
  fromBlock: bigint,
  toBlock: bigint,
  chunkSize: bigint = LOG_CHUNK_SIZE
): Promise<T[]> {
  const results: T[] = [];
  let start = fromBlock;
  while (start <= toBlock) {
    const tentativeEnd = start + chunkSize - 1n;
    const end = tentativeEnd > toBlock ? toBlock : tentativeEnd;
    try {
      const chunk = await fetcher(start, end);
      results.push(...chunk);
    } catch (e) {
      // eslint-disable-next-line no-console
      console.error(`[chunkedGetLogs] chunk ${start}-${end} failed`, e);
    }
    start = end + 1n;
  }
  return results;
}

export interface UserDepositEvent {
  txHash: `0x${string}`;
  blockNumber: bigint;
  assets: bigint;
  shares: bigint;
}

export type UserWithdrawEvent = UserDepositEvent;

export function useUserActivity() {
  const { address } = useAccount();
  const client = usePublicClient({ chainId: CHAIN.id });
  const [deposits, setDeposits] = useState<UserDepositEvent[]>([]);
  const [withdrawals, setWithdrawals] = useState<UserWithdrawEvent[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!client || !address) {
        setDeposits([]);
        setWithdrawals([]);
        return;
      }
      setIsLoading(true);
      try {
        const latest = await client.getBlockNumber();
        const fromBlock =
          latest > LOG_WINDOW_BLOCKS ? latest - LOG_WINDOW_BLOCKS : 0n;
        const me = address.toLowerCase();

        const [depositLogs, withdrawLogs] = await Promise.all([
          chunkedGetLogs(
            (from, to) =>
              client.getLogs({
                address: VAULT_ADDRESS,
                event: DEPOSIT_EVENT,
                fromBlock: from,
                toBlock: to,
              }),
            fromBlock,
            latest
          ),
          chunkedGetLogs(
            (from, to) =>
              client.getLogs({
                address: VAULT_ADDRESS,
                event: WITHDRAW_EVENT,
                fromBlock: from,
                toBlock: to,
              }),
            fromBlock,
            latest
          ),
        ]);

        const deps: UserDepositEvent[] = [];
        for (const log of depositLogs) {
          try {
            const parsed = decodeEventLog({
              abi: [DEPOSIT_EVENT],
              data: log.data,
              topics: log.topics,
            });
            const args = parsed.args as unknown as {
              sender: `0x${string}`;
              owner: `0x${string}`;
              assets: bigint;
              shares: bigint;
            };
            if (args.owner.toLowerCase() !== me) continue;
            deps.push({
              txHash: log.transactionHash!,
              blockNumber: log.blockNumber!,
              assets: args.assets,
              shares: args.shares,
            });
          } catch {
            /* skip malformed log */
          }
        }

        const wds: UserWithdrawEvent[] = [];
        for (const log of withdrawLogs) {
          try {
            const parsed = decodeEventLog({
              abi: [WITHDRAW_EVENT],
              data: log.data,
              topics: log.topics,
            });
            const args = parsed.args as unknown as {
              sender: `0x${string}`;
              receiver: `0x${string}`;
              owner: `0x${string}`;
              assets: bigint;
              shares: bigint;
            };
            if (args.owner.toLowerCase() !== me) continue;
            wds.push({
              txHash: log.transactionHash!,
              blockNumber: log.blockNumber!,
              assets: args.assets,
              shares: args.shares,
            });
          } catch {
            /* skip malformed log */
          }
        }

        deps.sort((a, b) => Number(b.blockNumber - a.blockNumber));
        wds.sort((a, b) => Number(b.blockNumber - a.blockNumber));

        if (!cancelled) {
          setDeposits(deps);
          setWithdrawals(wds);
        }
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error("[useUserActivity] load failed", e);
        if (!cancelled) {
          setDeposits([]);
          setWithdrawals([]);
        }
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [client, address, nonce]);

  const totalDeposited = useMemo(
    () => deposits.reduce((s, d) => s + d.assets, 0n),
    [deposits]
  );
  const totalWithdrawn = useMemo(
    () => withdrawals.reduce((s, w) => s + w.assets, 0n),
    [withdrawals]
  );

  return {
    deposits,
    withdrawals,
    totalDeposited,
    totalWithdrawn,
    isLoading,
    refetch: () => setNonce((n) => n + 1),
  };
}

export function useTradeHistory() {
  const client = usePublicClient({ chainId: CHAIN.id });
  const [events, setEvents] = useState<TradeEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!client) return;
      setIsLoading(true);
      try {
        const latest = await client.getBlockNumber();
        const fromBlock =
          latest > LOG_WINDOW_BLOCKS ? latest - LOG_WINDOW_BLOCKS : 0n;

        const logs = await chunkedGetLogs(
          (from, to) =>
            client.getLogs({
              address: VAULT_ADDRESS,
              event: TRADE_EVENT,
              fromBlock: from,
              toBlock: to,
            }),
          fromBlock,
          latest
        );

        const decoded: TradeEvent[] = [];
        for (const log of logs) {
          try {
            const parsed = decodeEventLog({
              abi: [TRADE_EVENT],
              data: log.data,
              topics: log.topics,
            });
            const args = parsed.args as unknown as {
              tokenIn: `0x${string}`;
              tokenOut: `0x${string}`;
              amountIn: bigint;
              amountOut: bigint;
              reasoningHash: `0x${string}`;
              confidence: number;
              timestamp: bigint;
            };
            decoded.push({
              txHash: log.transactionHash!,
              blockNumber: log.blockNumber!,
              ...args,
            });
          } catch {
            /* skip malformed log */
          }
        }

        decoded.sort((a, b) => Number(b.blockNumber - a.blockNumber));
        if (!cancelled) setEvents(decoded);
      } catch (e) {
        // eslint-disable-next-line no-console
        console.error("[useTradeHistory] load failed", e);
        if (!cancelled) setEvents([]);
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [client, nonce]);

  return { events, isLoading, refetch: () => setNonce((n) => n + 1) };
}

// ─── Helpers ──────────────────────────────────────────────────────

export function parseUsdc(value: string): bigint {
  if (!value || value.trim() === "") return 0n;
  const [whole, frac = ""] = value.trim().split(".");
  const fracPadded = (frac + "0".repeat(USDC_DECIMALS)).slice(0, USDC_DECIMALS);
  try {
    return BigInt(whole || "0") * 10n ** BigInt(USDC_DECIMALS) + BigInt(fracPadded || "0");
  } catch {
    return 0n;
  }
}

export function formatUsdc(value: bigint, decimals = 4): string {
  const divisor = 10n ** BigInt(USDC_DECIMALS);
  const whole = value / divisor;
  const frac = value % divisor;
  const fracStr = frac.toString().padStart(USDC_DECIMALS, "0").slice(0, decimals);
  return decimals > 0 ? `${whole}.${fracStr}` : `${whole}`;
}

export function friendlyError(err: unknown): string {
  if (err instanceof Error) {
    const msg = err.message;
    if (msg.includes("User rejected") || msg.includes("User denied")) {
      return "You rejected the transaction";
    }
    if (msg.includes("PositionCurrentlyOpen")) {
      return "Vault is trading — deposits and withdrawals are locked until the position closes";
    }
    if (msg.includes("insufficient funds")) {
      return "Insufficient ETH for gas";
    }
    if (msg.includes("ERC20InsufficientBalance")) {
      return "Insufficient USDC balance";
    }
    return msg.split("\n")[0].slice(0, 160);
  }
  return "Transaction failed";
}
