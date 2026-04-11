import {
    Agent,
    AIDecision,
    ChartDataPoint,
    Order,
    Position,
    PortfolioSnapshot,
    Trade,
    AgentStats,
    TimeRange,
} from "./types";
import {
    AGENT_COLORS,
    MODEL_CONFIGS,
    TRADING_SYMBOLS,
    DEFAULT_STARTING_BALANCE,
    DECISION_REASONS,
    TIME_RANGES,
} from "./constants";
import { generateId } from "./utils";

// Seed for reproducible randomness
let seed = 42;
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

// Generate AI agents
export function generateAgents(): Agent[] {
    const selectedModels = MODEL_CONFIGS.slice(0, 5); // Use first 5 models

    return selectedModels.map((model, index) => {
        const baseValue = DEFAULT_STARTING_BALANCE;
        const variation = randomBetween(-500, 500);
        const accountValue = baseValue + variation + (index === 0 ? 10 : 0); // First agent slightly ahead

        return {
            id: generateId(),
            name: model.name.toUpperCase().replace(/\s+/g, "-"),
            model: model.id,
            provider: model.provider,
            color: AGENT_COLORS[model.id] || "#888888",
            accountValue: Math.round(accountValue * 100) / 100,
            availableCash: Math.round(accountValue * randomBetween(0.3, 0.7) * 100) / 100,
            createdAt: new Date(Date.now() - randomInt(1, 30) * 24 * 60 * 60 * 1000),
        };
    });
}

// Generate portfolio history for charts
export function generatePortfolioHistory(
    agents: Agent[],
    timeRange: TimeRange
): PortfolioSnapshot[] {
    const config = TIME_RANGES[timeRange];
    const now = Date.now();
    const snapshots: PortfolioSnapshot[] = [];

    agents.forEach((agent) => {
        let currentValue = DEFAULT_STARTING_BALANCE;

        for (let i = 0; i < config.points; i++) {
            const timestamp = new Date(now - (config.points - i) * config.intervalMs);

            // Brownian motion with drift
            const drift = randomBetween(-0.002, 0.003);
            const volatility = randomBetween(-0.005, 0.005);
            currentValue = currentValue * (1 + drift + volatility);

            // Ensure we end up near the agent's current value
            if (i === config.points - 1) {
                currentValue = agent.accountValue;
            }

            snapshots.push({
                agentId: agent.id,
                timestamp,
                value: Math.round(currentValue * 100) / 100,
            });
        }
    });

    return snapshots;
}

// Convert portfolio snapshots to chart data format
export function getChartData(
    snapshots: PortfolioSnapshot[],
    agentId: string
): ChartDataPoint[] {
    return snapshots
        .filter((s) => s.agentId === agentId)
        .map((s) => ({
            time: Math.floor(s.timestamp.getTime() / 1000),
            value: s.value,
        }))
        .sort((a, b) => a.time - b.time);
}

// Generate positions for an agent
export function generatePositions(agentId: string): Position[] {
    const numPositions = randomInt(0, 3);
    const positions: Position[] = [];

    for (let i = 0; i < numPositions; i++) {
        const symbol = randomChoice(TRADING_SYMBOLS);
        const side = randomChoice(["LONG", "SHORT"] as const);
        const entryPrice = symbol === "BTC" ? randomBetween(85000, 95000) :
            symbol === "ETH" ? randomBetween(3000, 4000) :
                randomBetween(100, 500);
        const currentPrice = entryPrice * randomBetween(0.95, 1.05);
        const quantity = symbol === "BTC" ? randomBetween(0.1, 1) :
            symbol === "ETH" ? randomBetween(1, 10) :
                randomBetween(10, 100);
        const leverage = randomChoice([1, 2, 5, 10]);
        const margin = (entryPrice * quantity) / leverage;
        const unrealizedPnl = (currentPrice - entryPrice) * quantity * (side === "LONG" ? 1 : -1);

        positions.push({
            id: generateId(),
            agentId,
            symbol,
            side,
            quantity: Math.round(quantity * 100) / 100,
            entryPrice: Math.round(entryPrice * 100) / 100,
            currentPrice: Math.round(currentPrice * 100) / 100,
            entryTime: new Date(Date.now() - randomInt(1, 48) * 60 * 60 * 1000),
            leverage,
            liquidationPrice: Math.round((side === "LONG" ? entryPrice * 0.8 : entryPrice * 1.2) * 100) / 100,
            margin: Math.round(margin * 100) / 100,
            unrealizedPnl: Math.round(unrealizedPnl * 100) / 100,
        });
    }

    return positions;
}

// Generate trades for an agent
export function generateTrades(agentId: string, count: number = 25): Trade[] {
    const trades: Trade[] = [];

    for (let i = 0; i < count; i++) {
        const symbol = randomChoice(TRADING_SYMBOLS);
        const side = randomChoice(["LONG", "SHORT"] as const);
        const entryPrice = symbol === "BTC" ? randomBetween(80000, 100000) :
            symbol === "ETH" ? randomBetween(2500, 4500) :
                randomBetween(50, 800);
        const exitPrice = entryPrice * randomBetween(0.9, 1.15);
        const quantity = symbol === "BTC" ? randomBetween(0.1, 2) :
            symbol === "ETH" ? randomBetween(1, 20) :
                randomBetween(5, 200);
        const holdingMs = randomInt(5, 48 * 60) * 60 * 1000;
        const notionalEntry = entryPrice * quantity;
        const notionalExit = exitPrice * quantity;
        const totalFees = notionalEntry * 0.001 + notionalExit * 0.001;
        const grossPnl = (exitPrice - entryPrice) * quantity * (side === "LONG" ? 1 : -1);
        const netPnl = grossPnl - totalFees;

        trades.push({
            id: generateId(),
            agentId,
            symbol,
            side,
            entryPrice: Math.round(entryPrice * 100) / 100,
            exitPrice: Math.round(exitPrice * 100) / 100,
            quantity: Math.round(quantity * 100) / 100,
            holdingTime: `${Math.floor(holdingMs / 3600000)}H ${Math.floor((holdingMs % 3600000) / 60000)}M`,
            notionalEntry: Math.round(notionalEntry * 100) / 100,
            notionalExit: Math.round(notionalExit * 100) / 100,
            totalFees: Math.round(totalFees * 100) / 100,
            netPnl: Math.round(netPnl * 100) / 100,
        });
    }

    return trades;
}

// Generate AI decisions for an agent
export function generateDecisions(agentId: string, count: number = 10): AIDecision[] {
    const decisions: AIDecision[] = [];
    let balance = DEFAULT_STARTING_BALANCE;

    for (let i = 0; i < count; i++) {
        const operation = randomChoice(["BUY", "SELL", "HOLD"] as const);
        const symbol = randomChoice(TRADING_SYMBOLS);
        const prevPercent = randomBetween(0, 30);
        const targetPercent = operation === "BUY" ? prevPercent + randomBetween(5, 25) :
            operation === "SELL" ? Math.max(0, prevPercent - randomBetween(5, 15)) :
                prevPercent;

        // Update balance based on operation
        const change = randomBetween(-200, 300);
        balance += change;

        decisions.push({
            id: generateId(),
            agentId,
            timestamp: new Date(Date.now() - i * randomInt(5, 30) * 60 * 1000),
            operation,
            symbol,
            prevPercent: Math.round(prevPercent * 100) / 100,
            targetPercent: Math.round(targetPercent * 100) / 100,
            balance: Math.round(balance * 100) / 100,
            executed: randomBetween(0, 1) > 0.1,
            reason: randomChoice(DECISION_REASONS[operation]),
        });
    }

    return decisions.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
}

// Generate orders for an agent
export function generateOrders(agentId: string): Order[] {
    const numOrders = randomInt(0, 5);
    const orders: Order[] = [];

    for (let i = 0; i < numOrders; i++) {
        const symbol = randomChoice(TRADING_SYMBOLS);
        const side = randomChoice(["LONG", "SHORT"] as const);
        const price = symbol === "BTC" ? randomBetween(80000, 100000) :
            symbol === "ETH" ? randomBetween(2500, 4500) :
                randomBetween(50, 800);

        orders.push({
            id: generateId(),
            agentId,
            symbol,
            side,
            type: randomChoice(["LIMIT", "STOP"] as const),
            quantity: Math.round(randomBetween(1, 50) * 100) / 100,
            price: Math.round(price * 100) / 100,
            status: "PENDING",
            createdAt: new Date(Date.now() - randomInt(1, 24) * 60 * 60 * 1000),
        });
    }

    return orders;
}

// Calculate agent stats from trades
export function calculateAgentStats(trades: Trade[]): AgentStats {
    if (trades.length === 0) {
        return {
            totalPnl: 0,
            totalFees: 0,
            netRealized: 0,
            averageLeverage: 1,
            averageConfidence: 50,
            biggestWin: 0,
            biggestLoss: 0,
            holdTimes: { long: 33, short: 33, flat: 34 },
        };
    }

    const totalPnl = trades.reduce((sum, t) => sum + t.netPnl + t.totalFees, 0);
    const totalFees = trades.reduce((sum, t) => sum + t.totalFees, 0);
    const netRealized = trades.reduce((sum, t) => sum + t.netPnl, 0);
    const wins = trades.filter((t) => t.netPnl > 0).map((t) => t.netPnl);
    const losses = trades.filter((t) => t.netPnl < 0).map((t) => t.netPnl);

    const longTrades = trades.filter((t) => t.side === "LONG").length;
    const shortTrades = trades.filter((t) => t.side === "SHORT").length;
    const totalTrades = trades.length;

    return {
        totalPnl: Math.round(totalPnl * 100) / 100,
        totalFees: Math.round(totalFees * 100) / 100,
        netRealized: Math.round(netRealized * 100) / 100,
        averageLeverage: Math.round(randomBetween(5, 15) * 10) / 10,
        averageConfidence: Math.round(randomBetween(40, 80) * 10) / 10,
        biggestWin: wins.length > 0 ? Math.round(Math.max(...wins) * 100) / 100 : 0,
        biggestLoss: losses.length > 0 ? Math.round(Math.min(...losses) * 100) / 100 : 0,
        holdTimes: {
            long: Math.round((longTrades / totalTrades) * 100),
            short: Math.round((shortTrades / totalTrades) * 100),
            flat: Math.round(((totalTrades - longTrades - shortTrades) / totalTrades) * 100) || 100 - Math.round((longTrades / totalTrades) * 100) - Math.round((shortTrades / totalTrades) * 100),
        },
    };
}

// Reset seed for reproducibility
export function resetSeed(newSeed: number = 42): void {
    seed = newSeed;
}
