import { Provider } from "./types";

// Agent color scheme - each AI model has a distinct color
export const AGENT_COLORS: Record<string, string> = {
    "gpt-4": "#8b5cf6",           // Purple - OpenAI
    "gpt-4o": "#a78bfa",          // Light Purple - OpenAI
    "claude-3-5-sonnet": "#f97316", // Orange - Anthropic
    "claude-3-opus": "#fb923c",    // Light Orange - Anthropic
    "gemini-2.0": "#22c55e",       // Green - Google
    "gemini-1.5-pro": "#4ade80",   // Light Green - Google
    "deepseek-v3": "#3b82f6",      // Blue - DeepSeek
    "grok-2": "#ef4444",           // Red - xAI
    "qwen-2.5": "#06b6d4",         // Cyan - Alibaba
};

// Provider display names
export const PROVIDER_NAMES: Record<Provider, string> = {
    OPENAI: "OpenAI",
    ANTHROPIC: "Anthropic",
    GOOGLE: "Google",
    DEEPSEEK: "DeepSeek",
    XAI: "xAI",
    ALIBABA: "Alibaba",
};

// Model configurations
export const MODEL_CONFIGS = [
    { id: "gpt-4", name: "GPT-4", provider: "OPENAI" as Provider },
    { id: "gpt-4o", name: "GPT-4o", provider: "OPENAI" as Provider },
    { id: "claude-3-5-sonnet", name: "Claude 3.5 Sonnet", provider: "ANTHROPIC" as Provider },
    { id: "claude-3-opus", name: "Claude 3 Opus", provider: "ANTHROPIC" as Provider },
    { id: "gemini-2.0", name: "Gemini 2.0", provider: "GOOGLE" as Provider },
    { id: "gemini-1.5-pro", name: "Gemini 1.5 Pro", provider: "GOOGLE" as Provider },
    { id: "deepseek-v3", name: "DeepSeek V3", provider: "DEEPSEEK" as Provider },
    { id: "grok-2", name: "Grok 2", provider: "XAI" as Provider },
    { id: "qwen-2.5", name: "Qwen 2.5", provider: "ALIBABA" as Provider },
];

// Trading symbols
export const TRADING_SYMBOLS = ["BTC", "ETH", "SOL", "NVDA", "MSFT", "PLTR", "NDX", "AAPL"];

// Time range configurations
export const TIME_RANGES = {
    "5m": { label: "5 Minutes", intervalMs: 5000, points: 60 },
    "1h": { label: "1 Hour", intervalMs: 60000, points: 60 },
    "1d": { label: "1 Day", intervalMs: 3600000, points: 24 },
} as const;

// Default starting balance for agents
export const DEFAULT_STARTING_BALANCE = 10000;

// AI decision reasons templates
export const DECISION_REASONS = {
    BUY: [
        "Bitcoin has dipped below key support, showing bullish reversal signals",
        "Bitcoin has retreated to a favorable entry point",
        "Bitcoin shows momentum breakout above resistance",
        "BTC has retreated and RSI indicates oversold conditions",
        "Bitcoin is stable at support, entering accumulation zone",
        "Strong buying pressure detected with increasing volume",
    ],
    SELL: [
        "Taking profits as price reaches resistance level",
        "Risk management triggered, reducing exposure",
        "Bearish divergence detected on momentum indicators",
        "Price approaching overbought territory",
        "Market structure weakening, securing gains",
    ],
    HOLD: [
        "Bitcoin shows mixed signals, maintaining current position",
        "Waiting for clearer market direction",
        "Current position aligns with medium-term thesis",
        "No significant change in market conditions",
        "Consolidation phase, holding for breakout",
    ],
};
