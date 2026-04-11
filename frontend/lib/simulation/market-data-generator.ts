import { TokenSnapshot, DEXData, GMGNData, TwitterData } from '../types/simulation';

// Token name generators (matching backend)
const PREFIXES = ["Moon", "Doge", "Shib", "Pepe", "Wojak", "Chad", "Giga", "Based", "Frog", "Cat"];
const SUFFIXES = ["Coin", "Token", "Inu", "Moon", "Rocket", "AI", "GPT", "Swap", "Fi", "X"];

let seed = Date.now();
function seededRandom(): number {
  seed = (seed * 9301 + 49297) % 233280;
  return seed / 233280;
}

function randomBetween(min: number, max: number): number {
  return min + seededRandom() * (max - min);
}

function randomInt(min: number, max: number): number {
  return Math.floor(randomBetween(min, max + 1));
}

function randomChoice<T>(arr: T[]): T {
  return arr[randomInt(0, arr.length - 1)];
}

function generateTokenName(): { name: string; symbol: string } {
  const prefix = randomChoice(PREFIXES);
  const suffix = randomChoice(SUFFIXES);
  const name = `${prefix}${suffix}`;
  const symbol = `$${prefix.slice(0, 3).toUpperCase()}${suffix[0].toUpperCase()}`;
  return { name, symbol };
}

function generateAddress(chain: string = "sol"): string {
  if (chain === "sol") {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    return Array.from({ length: 44 }, () => randomChoice(chars.split(''))).join('');
  } else {
    return "0x" + Array.from({ length: 40 }, () => randomChoice("0123456789abcdef".split(''))).join('');
  }
}

/**
 * Generate synthetic DEX data
 */
export async function generateDEXData(coinAddress: string): Promise<DEXData> {
  await new Promise(resolve => setTimeout(resolve, 3500));
  
  const basePrice = randomBetween(0.0001, 0.01);
  const volume24h = randomBetween(10000, 1000000);
  const liquidity = randomBetween(50000, 500000);
  const marketCap = basePrice * randomBetween(1000000, 100000000);
  
  // Generate 24h price history (hourly points)
  const priceHistory: Array<{ time: number; price: number }> = [];
  const now = Date.now();
  let currentPrice = basePrice;
  
  for (let i = 23; i >= 0; i--) {
    const time = now - (i * 60 * 60 * 1000);
    // Random walk with slight drift
    const change = randomBetween(-0.05, 0.05);
    currentPrice = currentPrice * (1 + change);
    priceHistory.push({ time, price: currentPrice });
  }
  
  return {
    price: currentPrice,
    volume24h,
    liquidity,
    marketCap,
    priceHistory,
  };
}

/**
 * Generate synthetic GMGN data
 */
export async function generateGMGNData(coinAddress: string): Promise<GMGNData> {
  await new Promise(resolve => setTimeout(resolve, 3500));
  
  return {
    holderCount: randomInt(100, 10000),
    top10HolderPct: randomBetween(10, 50),
    smartMoneyFlow: randomChoice(['buying', 'selling', 'neutral']),
    rugScore: randomInt(0, 100),
    devWalletPct: randomBetween(5, 30),
    liquidityLocked: randomBetween(0, 1) > 0.3,
    lockDaysRemaining: randomInt(0, 365),
  };
}

/**
 * Generate synthetic Twitter data
 */
export async function generateTwitterData(coinAddress: string): Promise<TwitterData> {
  await new Promise(resolve => setTimeout(resolve, 3500));
  
  return {
    mentions24h: randomInt(10, 1000),
    sentimentScore: randomInt(0, 100),
    influencerMentions: randomInt(0, 50),
    trending: randomBetween(0, 1) > 0.7,
    communitySize: randomInt(1000, 50000),
  };
}

/**
 * Generate initial token snapshot from fetched data
 */
export function createTokenSnapshot(
  coinAddress: string,
  dexData: DEXData,
  gmgnData: GMGNData,
  twitterData: TwitterData,
  step: number = 0
): TokenSnapshot {
  const { name, symbol } = generateTokenName();
  
  // Calculate technical indicators
  const rsi = randomBetween(20, 80);
  const macd = randomBetween(-0.001, 0.001);
  const macdSignal = macd * randomBetween(0.8, 1.2);
  const volatility = randomBetween(0.01, 0.1);
  
  const bollingerUpper = dexData.price * (1 + volatility * 2);
  const bollingerLower = dexData.price * (1 - volatility * 2);
  const bollingerPosition = (dexData.price - bollingerLower) / (bollingerUpper - bollingerLower) * 2 - 1;
  
  const avgVolume = dexData.volume24h / 24;
  const volumeRatio = dexData.volume24h / avgVolume;
  
  return {
    name,
    symbol,
    address: coinAddress,
    chain: coinAddress.length === 44 ? 'sol' : 'eth',
    timestamp: new Date(),
    step,
    price: dexData.price,
    priceChange1h: randomBetween(-0.1, 0.1),
    priceChange24h: randomBetween(-0.2, 0.2),
    volume24h: dexData.volume24h,
    marketCap: dexData.marketCap,
    liquidity: dexData.liquidity,
    holderCount: gmgnData.holderCount,
    top10HolderPct: gmgnData.top10HolderPct,
    smartMoneyFlow: gmgnData.smartMoneyFlow,
    rugScore: gmgnData.rugScore,
    devWalletPct: gmgnData.devWalletPct,
    liquidityLocked: gmgnData.liquidityLocked,
    lockDaysRemaining: gmgnData.lockDaysRemaining,
    mentions24h: twitterData.mentions24h,
    sentimentScore: twitterData.sentimentScore,
    influencerMentions: twitterData.influencerMentions,
    trending: twitterData.trending,
    communitySize: twitterData.communitySize,
    rsi,
    macd,
    macdSignal,
    bollingerUpper,
    bollingerLower,
    bollingerPosition,
    volatility,
    volumeRatio,
  };
}

/**
 * Generate next token snapshot with realistic price movement
 */
export function generateNextSnapshot(
  previous: TokenSnapshot,
  targetPrice?: number,
  volatility?: number
): TokenSnapshot {
  const currentVolatility = volatility ?? previous.volatility;
  
  // Geometric Brownian motion with optional drift toward target
  let priceChange = 0;
  if (targetPrice) {
    const drift = (targetPrice - previous.price) / previous.price * 0.1; // 10% drift per step
    const randomWalk = randomBetween(-currentVolatility, currentVolatility);
    priceChange = drift + randomWalk;
  } else {
    priceChange = randomBetween(-currentVolatility, currentVolatility);
  }
  
  // Occasional pump/dump (5% chance)
  if (randomBetween(0, 1) < 0.05) {
    priceChange += randomBetween(-0.2, 0.2);
  }
  
  const newPrice = previous.price * (1 + priceChange);
  
  // Update correlated metrics
  const volumeMultiplier = Math.abs(priceChange) > 0.05 ? 1.5 : 1;
  const sentimentChange = priceChange > 0 ? randomBetween(0, 5) : randomBetween(-5, 0);
  
  return {
    ...previous,
    timestamp: new Date(previous.timestamp.getTime() + 60000), // 1 minute later
    step: previous.step + 1,
    price: newPrice,
    priceChange1h: priceChange * 60,
    volume24h: previous.volume24h * volumeMultiplier,
    sentimentScore: Math.max(0, Math.min(100, previous.sentimentScore + sentimentChange)),
    mentions24h: previous.mentions24h + (previous.trending ? randomInt(1, 10) : randomInt(0, 2)),
    rsi: Math.max(0, Math.min(100, previous.rsi + randomBetween(-2, 2))),
    macd: previous.macd + randomBetween(-0.0001, 0.0001),
    bollingerUpper: newPrice * (1 + currentVolatility * 2),
    bollingerLower: newPrice * (1 - currentVolatility * 2),
    bollingerPosition: (newPrice - (newPrice * (1 - currentVolatility * 2))) / (newPrice * currentVolatility * 4) * 2 - 1,
  };
}
