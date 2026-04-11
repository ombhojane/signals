// AI Model Providers
export type Provider = 
  | "OPENAI" 
  | "ANTHROPIC" 
  | "GOOGLE" 
  | "DEEPSEEK" 
  | "XAI" 
  | "ALIBABA";

// Trade side
export type Side = "LONG" | "SHORT";

// Operation type for AI decisions
export type Operation = "BUY" | "SELL" | "HOLD";

// AI Agent/Trader
export interface Agent {
  id: string;
  name: string;
  model: string;
  provider: Provider;
  color: string;
  accountValue: number;
  availableCash: number;
  createdAt: Date;
}

// Portfolio snapshot for time-series charts
export interface PortfolioSnapshot {
  agentId: string;
  timestamp: Date;
  value: number;
}

// Active position
export interface Position {
  id: string;
  agentId: string;
  symbol: string;
  side: Side;
  quantity: number;
  entryPrice: number;
  currentPrice: number;
  entryTime: Date;
  leverage: number;
  liquidationPrice: number;
  margin: number;
  unrealizedPnl: number;
}

// Executed trade
export interface Trade {
  id: string;
  agentId: string;
  symbol: string;
  side: Side;
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  holdingTime: string;
  notionalEntry: number;
  notionalExit: number;
  totalFees: number;
  netPnl: number;
}

// AI decision log entry
export interface AIDecision {
  id: string;
  agentId: string;
  timestamp: Date;
  operation: Operation;
  symbol: string;
  prevPercent: number;
  targetPercent: number;
  balance: number;
  executed: boolean;
  reason: string;
}

// Order (pending)
export interface Order {
  id: string;
  agentId: string;
  symbol: string;
  side: Side;
  type: "MARKET" | "LIMIT" | "STOP";
  quantity: number;
  price: number;
  status: "PENDING" | "FILLED" | "CANCELLED";
  createdAt: Date;
}

// Agent stats summary
export interface AgentStats {
  totalPnl: number;
  totalFees: number;
  netRealized: number;
  averageLeverage: number;
  averageConfidence: number;
  biggestWin: number;
  biggestLoss: number;
  holdTimes: {
    long: number;
    short: number;
    flat: number;
  };
}

// Chart data point for lightweight-charts
export interface ChartDataPoint {
  time: number;
  value: number;
}

// Time range options
export type TimeRange = "5m" | "1h" | "1d";
