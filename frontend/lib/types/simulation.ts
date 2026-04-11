// Simulation-specific types

export type SimulationPhase = 
  | 'idle' 
  | 'fetching' 
  | 'analyzing' 
  | 'predicted' 
  | 'simulating' 
  | 'completed' 
  | 'error' 
  | 'paused';

export interface TokenSnapshot {
  // Identity
  name: string;
  symbol: string;
  address: string;
  chain: string;
  
  // Time
  timestamp: Date;
  step: number;
  
  // Price Data
  price: number;
  priceChange1h: number;
  priceChange24h: number;
  volume24h: number;
  marketCap: number;
  liquidity: number;
  
  // On-Chain Data (GMGN-like)
  holderCount: number;
  top10HolderPct: number;
  smartMoneyFlow: 'buying' | 'selling' | 'neutral';
  rugScore: number; // 0-100 (lower is safer)
  devWalletPct: number;
  liquidityLocked: boolean;
  lockDaysRemaining: number;
  
  // Social Data (Twitter-like)
  mentions24h: number;
  sentimentScore: number; // 0-100
  influencerMentions: number;
  trending: boolean;
  communitySize: number;
  
  // Technical Indicators
  rsi: number;
  macd: number;
  macdSignal: number;
  bollingerUpper: number;
  bollingerLower: number;
  bollingerPosition: number; // -1 to 1
  volatility: number;
  volumeRatio: number;
}

export interface DEXData {
  price: number;
  volume24h: number;
  liquidity: number;
  marketCap: number;
  priceHistory: Array<{ time: number; price: number }>;
}

export interface GMGNData {
  holderCount: number;
  top10HolderPct: number;
  smartMoneyFlow: 'buying' | 'selling' | 'neutral';
  rugScore: number;
  devWalletPct: number;
  liquidityLocked: boolean;
  lockDaysRemaining: number;
}

export interface TwitterData {
  mentions24h: number;
  sentimentScore: number;
  influencerMentions: number;
  trending: boolean;
  communitySize: number;
}

export interface TradeDecision {
  action: 'BUY' | 'SELL' | 'HOLD';
  confidence: number; // 0-100
  reasoning: string;
  riskAssessment: string;
  priceTarget?: number;
  stopLoss?: number;
  predictedValue: number; // Price prediction at end of duration
}

export interface SimulationResult {
  action: 'BUY' | 'SELL' | 'HOLD';
  entryPrice: number;
  exitPrice: number;
  predictedPrice: number;
  actualPrice: number;
  priceChange: number;
  priceChangePercent: number;
  profitLoss: number;
  profitLossPercent: number;
  status: 'profit' | 'loss' | 'equilized';
  accuracy: number; // How close prediction was to actual (0-100)
  duration: number;
  completedAt: Date;
}

export interface SimulationState {
  // Phase tracking
  phase: SimulationPhase;
  
  // Input
  coinAddress: string;
  duration: number; // minutes
  
  // Data
  marketData: TokenSnapshot[];
  fetchProgress?: string[];
  dexData?: DEXData;
  gmgnData?: GMGNData;
  twitterData?: TwitterData;
  
  // Prediction
  prediction?: TradeDecision;
  predictedValue?: number;
  predictedTimestamp?: Date;
  
  // Simulation
  startTime?: Date;
  currentTime?: Date;
  elapsedTime?: number;
  isPaused: boolean;
  
  // Results
  result?: SimulationResult;
  
  // History
  simulationId?: string;
  
  // Error
  error?: string;
}

export interface StoredSimulation {
  id: string;
  coinAddress: string;
  startedAt: Date;
  completedAt: Date;
  duration: number;
  prediction: TradeDecision;
  result: SimulationResult;
  marketData: TokenSnapshot[]; // Snapshot of key points
  chartData: Array<{ time: number; value: number }>; // Compressed chart data
}

export interface PricePoint {
  time: number;
  price: number;
}

export interface SimulationConfig {
  startPrice: number;
  predictedPrice: number;
  duration: number; // minutes
  volatility: number;
  updateInterval: number; // seconds
  entryPrice: number;
  action: 'BUY' | 'SELL' | 'HOLD';
}
