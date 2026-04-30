/**
 * Backend API Client - Connects frontend to real backend services.
 */

import { DEXData, GMGNData, TwitterData, TradeDecision } from '../types/simulation';
import { mapDexResponse, mapSafetyResponse, mapTwitterResponse, mapRLAgentDecision, mapTokenAnalysisResponse } from './mappers';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const error = await res.text().catch(() => 'Unknown error');
    throw new Error(`API error ${res.status}: ${error}`);
  }

  return res.json();
}

/**
 * Fetch DEX market data for a token.
 */
export async function fetchDEXData(coinAddress: string): Promise<DEXData> {
  const data = await apiFetch<any>(
    `/dex-analytics?chainId=solana&pairAddress=${encodeURIComponent(coinAddress)}`
  );
  return mapDexResponse(data);
}

/**
 * Fetch safety/rug check data (replaces GMGN).
 */
export async function fetchSafetyData(coinAddress: string): Promise<GMGNData> {
  const data = await apiFetch<any>(
    `/risk-assessment?coinAddress=${encodeURIComponent(coinAddress)}&pairAddress=${encodeURIComponent(coinAddress)}`
  );
  return mapSafetyResponse(data);
}

/**
 * Fetch Twitter/social data for a token.
 */
export async function fetchTwitterData(coinAddress: string, symbol?: string): Promise<TwitterData> {
  const params = new URLSearchParams();
  if (symbol) params.set('token_symbol', symbol);
  if (coinAddress) params.set('token_address', coinAddress);

  const data = await apiFetch<any>(
    `/ai-analysis/social?${params.toString()}`,
    { method: 'POST' }
  );
  return mapTwitterResponse(data);
}

/**
 * Run RL agent analysis on a real token.
 */
export async function fetchRLAgentAnalysis(
  coinAddress: string,
  chain: string = 'sol'
): Promise<{ token: any; decision: TradeDecision }> {
  const data = await apiFetch<any>(
    `/rl-agent/analyze?token_address=${encodeURIComponent(coinAddress)}&chain=${encodeURIComponent(chain)}`,
    { method: 'POST' }
  );
  return {
    token: data.token,
    decision: mapRLAgentDecision(data.decision, data.token?.price || 0),
  };
}

/**
 * Run comprehensive AI analysis (orchestrated).
 */
export async function fetchComprehensiveAnalysis(
  tokenAddress: string,
  chain: string = 'sol',
  pairAddress?: string
) {
  const params = new URLSearchParams({
    token_address: tokenAddress,
    chain,
  });
  if (pairAddress) params.set('pair_address', pairAddress);

  return apiFetch<any>(
    `/ai-analysis/orchestrated?${params.toString()}`,
    { method: 'POST' }
  );
}

/**
 * Fetch comprehensive token analysis (DEX data + safety report in one call).
 * Returns both DEXData and GMGNData from a single endpoint.
 */
export async function fetchTokenAnalysis(
  coinAddress: string,
  chain: string = 'sol'
): Promise<{ dexData: DEXData; gmgnData: GMGNData; symbol: string; name: string }> {
  const data = await apiFetch<any>(
    `/gmgn/token-analysis/${encodeURIComponent(coinAddress)}?chain=${chain}`
  );
  return mapTokenAnalysisResponse(data);
}

/**
 * Run comprehensive token scan for simulation.
 * This is the main endpoint for the simulation workflow.
 */
export async function fetchTokenScan(
  tokenAddress: string,
  chain: string = 'sol',
  includeSocial: boolean = false
): Promise<{
  token: {
    name: string;
    symbol: string;
    address: string;
    price: number;
    volume_24h: number;
    liquidity: number;
    market_cap: number;
    price_change_24h: number;
  };
  safety: {
    overall_risk_score: number;
    risk_level: string;
    liquidity_locked: boolean;
    holder_count: number;
    top_10_holder_pct: number;
  };
  prediction: {
    action: 'BUY' | 'SELL' | 'HOLD';
    confidence: number;
    reasoning: string;
    price_target?: number;
    stop_loss?: number;
  };
  data_status: Record<string, string>;
}> {
  return apiFetch<any>('/token-scan/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      token_address: tokenAddress,
      chain,
      include_social: includeSocial,
    }),
  });
}

/**
 * Fetch token stats (price, volume, etc.)
 */
export async function fetchTokenStats(coinAddress: string, chain: string = 'sol') {
  return apiFetch<any>(`/gmgn/token-analysis/${encodeURIComponent(coinAddress)}?chain=${chain}`);
}

/**
 * Fetch AI Signals
 */
export async function fetchAISignals(coinAddress: string) {
  return apiFetch<any>(
    `/ai-Signals?coinAddress=${encodeURIComponent(coinAddress)}&pairAddress=${encodeURIComponent(coinAddress)}`
  );
}

/**
 * Fetch trending tokens
 */
export async function fetchTrendingTokens(chain: string = 'sol', limit: number = 20) {
  return apiFetch<any>(`/gmgn/trending?chain=${chain}&limit=${limit}`);
}

/**
 * Check API health
 */
export async function checkHealth(): Promise<boolean> {
  try {
    await apiFetch('/health');
    return true;
  } catch {
    return false;
  }
}
