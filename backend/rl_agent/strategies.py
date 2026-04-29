"""
Seed strategies for the adaptive RL agent.

Curated memecoin trading rules (2025 meta) used to bootstrap the agent so
it doesn't have to rediscover everything from scratch. The agent will
re-weight these rules through reflection (success_count / failure_count)
and add new ones via REFLECT.

Source mix: Solana memecoin trader playbooks + on-chain forensics
heuristics (smart-money, holder concentration, liquidity locks),
classical TA (RSI/MACD/Bollinger), and recent rug-pattern observations.
"""

from typing import List, Dict


SEED_RULES: List[Dict[str, str]] = [
    # ---------- AVOID gates (hard filters) ----------
    {
        "type": "AVOID",
        "name": "Rug Score Gate",
        "conditions": "rug_score >= 75",
        "description": "Composite rug indicator high. Skip — capital preservation > FOMO.",
    },
    {
        "type": "AVOID",
        "name": "Whale Concentration",
        "conditions": "top_10_holder_pct >= 80",
        "description": "Top-10 holders own most supply → exit liquidity for insiders.",
    },
    {
        "type": "AVOID",
        "name": "Unlocked Liquidity",
        "conditions": "liquidity_locked == False AND rug_score > 40",
        "description": "Unlocked LP + non-zero risk = soft rug pattern. Skip.",
    },
    {
        "type": "AVOID",
        "name": "Dev Bag Risk",
        "conditions": "dev_wallet_pct > 12",
        "description": "Dev holding > 12% supply leaves heavy distribution overhang.",
    },
    {
        "type": "AVOID",
        "name": "Illiquid Token",
        "conditions": "liquidity < 10000 OR volume_24h < 5000",
        "description": "Not enough liquidity to enter and exit cleanly.",
    },

    # ---------- ENTRY rules ----------
    {
        "type": "ENTRY",
        "name": "Smart Money Inflow",
        "conditions": "smart_money_flow == 'buying' AND volume_ratio >= 1.5 AND rug_score < 50",
        "description": "Sophisticated wallets accumulating with above-average volume on a clean token.",
    },
    {
        "type": "ENTRY",
        "name": "Oversold Bounce",
        "conditions": "rsi <= 30 AND bollinger_position <= -0.85 AND rug_score < 60",
        "description": "Mean-reversion long when oversold and price tagging lower band.",
    },
    {
        "type": "ENTRY",
        "name": "Trending With Influencer",
        "conditions": "trending == True AND influencer_mentions >= 1 AND sentiment_score >= 60 AND rug_score < 60",
        "description": "Social momentum + verified attention can mark the start of a leg up.",
    },
    {
        "type": "ENTRY",
        "name": "Fresh Mover Breakout",
        "conditions": "price_change_1h between 4 and 25 AND volume_ratio > 2 AND rsi 50..70",
        "description": "Healthy momentum, not yet overbought; trend follow.",
    },
    {
        "type": "ENTRY",
        "name": "MACD Cross From Below",
        "conditions": "macd > macd_signal AND previous macd <= previous macd_signal AND rsi < 65",
        "description": "Bullish MACD crossover before overheating.",
    },

    # ---------- EXIT rules ----------
    {
        "type": "EXIT",
        "name": "RSI Blow-off",
        "conditions": "rsi >= 80 AND bollinger_position >= 0.85",
        "description": "Late-stage euphoria. Take profit before mean reversion.",
    },
    {
        "type": "EXIT",
        "name": "Smart Money Distribution",
        "conditions": "smart_money_flow == 'selling' AND held position",
        "description": "If smart wallets rotate out, ride the wave down at your peril. Exit.",
    },
    {
        "type": "EXIT",
        "name": "Volume Capitulation Dump",
        "conditions": "price_change_1h <= -8 AND volume_ratio >= 1.5",
        "description": "Heavy red candle on volume = distribution. Cut and reassess.",
    },
    {
        "type": "EXIT",
        "name": "Lock In At +30%",
        "conditions": "unrealized_pnl_pct >= 30",
        "description": "Tighten stop to entry; let runners run, never give back a 30%er.",
    },
    {
        "type": "EXIT",
        "name": "Sentiment Collapse",
        "conditions": "sentiment_score < 35 AND trending == False",
        "description": "Narrative dead, exit before reflexive sell-off.",
    },
]


def seed_memory(memory) -> int:
    """Inject SEED_RULES into a MemoryManager instance if not already present.

    Returns number of rules added.
    """
    existing = {r.name for r in memory.rules}
    added = 0
    for spec in SEED_RULES:
        if spec["name"] in existing:
            continue
        memory.add_rule(
            rule_type=spec["type"],
            name=spec["name"],
            description=spec["description"],
            conditions=spec["conditions"],
            source_trade_id=None,
        )
        added += 1
    return added
