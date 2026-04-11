/**
 * Response Mappers - Convert backend API responses to frontend TypeScript types.
 */

import { DEXData, GMGNData, TwitterData, TradeDecision } from '../types/simulation';

/**
 * Map DexScreener response to frontend DEXData type.
 */
export function mapDexResponse(data: any): DEXData {
  // Handle direct pair data or pairs array
  const pair = data?.pairs?.[0] || data?.pair || data || {};

  const price = parseFloat(pair.priceUsd || pair.price || '0') || 0;
  const volume24h = parseFloat(pair.volume?.h24 || pair.volume24h || '0') || 0;
  const liquidity = parseFloat(pair.liquidity?.usd || pair.liquidity || '0') || 0;
  const marketCap = parseFloat(pair.marketCap || pair.fdv || '0') || 0;

  // Build price history from OHLCV if available, otherwise generate from priceChange
  const priceHistory: Array<{ time: number; price: number }> = [];
  if (data.ohlcv && Array.isArray(data.ohlcv)) {
    for (const bar of data.ohlcv) {
      priceHistory.push({ time: bar.timestamp * 1000, price: bar.close });
    }
  } else {
    // Generate approximate 24h history from price changes
    const now = Date.now();
    const priceChange24h = parseFloat(pair.priceChange?.h24 || '0') / 100;
    const startPrice = price / (1 + priceChange24h);

    for (let i = 23; i >= 0; i--) {
      const t = now - i * 60 * 60 * 1000;
      const progress = (24 - i) / 24;
      const p = startPrice + (price - startPrice) * progress;
      priceHistory.push({ time: t, price: p });
    }
  }

  return { price, volume24h, liquidity, marketCap, priceHistory };
}

/**
 * Map safety/risk-assessment response to frontend GMGNData type.
 */
export function mapSafetyResponse(data: any): GMGNData {
  // Can handle both /risk-assessment format and raw safety report format
  if (data.overallRiskScore !== undefined) {
    // /risk-assessment endpoint format
    const riskMap: Record<string, number> = {
      'Low Risk': 20, 'Medium Risk': 50, 'High Risk': 75, 'Critical Risk': 95,
    };
    return {
      holderCount: 0, // Not available from this endpoint
      top10HolderPct: data.concentrationRiskPercentage || 0,
      smartMoneyFlow: 'neutral' as const,
      rugScore: riskMap[data.overallRiskScore] || 50,
      devWalletPct: 0,
      liquidityLocked: data.liquidityLockStatus === 'Locked',
      lockDaysRemaining: data.liquidityLockRemainingDays || 0,
    };
  }

  // Raw safety report format
  return {
    holderCount: data.holder_count || 0,
    top10HolderPct: data.top_10_holder_pct || 0,
    smartMoneyFlow: (data.smart_money_flow || 'neutral') as 'buying' | 'selling' | 'neutral',
    rugScore: data.overall_risk_score || 50,
    devWalletPct: data.dev_wallet_pct || 0,
    liquidityLocked: data.liquidity_locked ?? false,
    lockDaysRemaining: data.lock_remaining_days || 0,
  };
}

/**
 * Map Twitter API response to frontend TwitterData type.
 */
export function mapTwitterResponse(data: any): TwitterData {
  const rawData = data?.raw_data || data || {};
  const tweets = rawData.tweets || [];

  const totalTweets = rawData.total_tweets || tweets.length || 0;

  // Count verified/influencer authors
  const influencerCount = tweets.filter(
    (t: any) => t?.author?.isBlueVerified
  ).length;

  // Sum follower counts as community size proxy
  const communitySize = tweets.reduce(
    (sum: number, t: any) => sum + (t?.author?.followers || 0), 0
  );

  // Simple sentiment from engagement
  const avgEngagement = tweets.length > 0
    ? tweets.reduce((sum: number, t: any) =>
        sum + (t?.likeCount || 0) + (t?.retweetCount || 0), 0) / tweets.length
    : 0;
  const sentimentScore = Math.min(100, Math.max(0, Math.round(avgEngagement / 10)));

  return {
    mentions24h: totalTweets,
    sentimentScore,
    influencerMentions: influencerCount,
    trending: totalTweets > 50,
    communitySize,
  };
}

/**
 * Map /gmgn/token-analysis response to both DEXData and GMGNData.
 * This endpoint returns token_stats + safety_report in one call.
 */
export function mapTokenAnalysisResponse(data: any): {
  dexData: DEXData;
  gmgnData: GMGNData;
  symbol: string;
  name: string;
} {
  const tokenStats = data?.token_stats || {};
  const safetyReport = data?.safety_report || {};

  // Map token_stats → DEXData
  const price = tokenStats.price || 0;
  const volume24h = tokenStats.volume_24h || 0;
  const liquidity = tokenStats.liquidity || 0;
  const marketCap = tokenStats.market_cap || 0;

  // Build price history from raw DexScreener pair data if available
  const priceHistory: Array<{ time: number; price: number }> = [];
  const rawPair = tokenStats.raw_data || {};
  const now = Date.now();
  const priceChange24h = parseFloat(rawPair.priceChange?.h24 || tokenStats.price_change_24h || '0') / 100;
  const startPrice = price / (1 + (priceChange24h || 0));

  for (let i = 23; i >= 0; i--) {
    const t = now - i * 60 * 60 * 1000;
    const progress = (24 - i) / 24;
    const p = startPrice + (price - startPrice) * progress;
    priceHistory.push({ time: t, price: p });
  }

  const dexData: DEXData = { price, volume24h, liquidity, marketCap, priceHistory };

  // Map safety_report → GMGNData
  const gmgnData: GMGNData = {
    holderCount: safetyReport.holder_count || tokenStats.holders || 0,
    top10HolderPct: safetyReport.top_10_holder_pct || 0,
    smartMoneyFlow: (safetyReport.smart_money_flow || 'neutral') as 'buying' | 'selling' | 'neutral',
    rugScore: safetyReport.overall_risk_score || 50,
    devWalletPct: safetyReport.dev_wallet_pct || 0,
    liquidityLocked: safetyReport.liquidity_locked ?? false,
    lockDaysRemaining: safetyReport.lock_remaining_days || 0,
  };

  return {
    dexData,
    gmgnData,
    symbol: tokenStats.symbol || '',
    name: tokenStats.name || '',
  };
}

/**
 * Map RL agent decision response to frontend TradeDecision type.
 */
export function mapRLAgentDecision(decision: any, currentPrice: number): TradeDecision {
  const action = (decision.action || 'HOLD').toUpperCase();
  const validActions = ['BUY', 'SELL', 'HOLD'];

  return {
    action: (validActions.includes(action) ? action : 'HOLD') as 'BUY' | 'SELL' | 'HOLD',
    confidence: decision.confidence || 50,
    reasoning: decision.reasoning || 'No reasoning provided',
    riskAssessment: decision.risk_assessment || 'Unknown',
    priceTarget: decision.price_target,
    stopLoss: decision.stop_loss,
    predictedValue: decision.price_target || currentPrice,
  };
}
