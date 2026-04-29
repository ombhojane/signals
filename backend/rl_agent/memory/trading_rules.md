# Trading Rules

> Autonomous Trading Agent - Learned Rules
> Last Updated: 2026-04-29 11:03
> Total Rules: 15

---

## Entry Rules (When to BUY)

### Smart Money Inflow
**ID**: RULE_006 | **Created**: 2026-04-29

- **Conditions**: smart_money_flow == 'buying' AND volume_ratio >= 1.5 AND rug_score < 50
- **Description**: Sophisticated wallets accumulating with above-average volume on a clean token.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00

### Oversold Bounce
**ID**: RULE_007 | **Created**: 2026-04-29

- **Conditions**: rsi <= 30 AND bollinger_position <= -0.85 AND rug_score < 60
- **Description**: Mean-reversion long when oversold and price tagging lower band.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00

### Trending With Influencer
**ID**: RULE_008 | **Created**: 2026-04-29

- **Conditions**: trending == True AND influencer_mentions >= 1 AND sentiment_score >= 60 AND rug_score < 60
- **Description**: Social momentum + verified attention can mark the start of a leg up.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00

### Fresh Mover Breakout
**ID**: RULE_009 | **Created**: 2026-04-29

- **Conditions**: price_change_1h between 4 and 25 AND volume_ratio > 2 AND rsi 50..70
- **Description**: Healthy momentum, not yet overbought; trend follow.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00

### MACD Cross From Below
**ID**: RULE_010 | **Created**: 2026-04-29

- **Conditions**: macd > macd_signal AND previous macd <= previous macd_signal AND rsi < 65
- **Description**: Bullish MACD crossover before overheating.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00


---

## Exit Rules (When to SELL)

### RSI Blow-off
**ID**: RULE_011 | **Created**: 2026-04-29

- **Conditions**: rsi >= 80 AND bollinger_position >= 0.85
- **Description**: Late-stage euphoria. Take profit before mean reversion.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00

### Smart Money Distribution
**ID**: RULE_012 | **Created**: 2026-04-29

- **Conditions**: smart_money_flow == 'selling' AND held position
- **Description**: If smart wallets rotate out, ride the wave down at your peril. Exit.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00

### Volume Capitulation Dump
**ID**: RULE_013 | **Created**: 2026-04-29

- **Conditions**: price_change_1h <= -8 AND volume_ratio >= 1.5
- **Description**: Heavy red candle on volume = distribution. Cut and reassess.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00

### Lock In At +30%
**ID**: RULE_014 | **Created**: 2026-04-29

- **Conditions**: unrealized_pnl_pct >= 30
- **Description**: Tighten stop to entry; let runners run, never give back a 30%er.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00

### Sentiment Collapse
**ID**: RULE_015 | **Created**: 2026-04-29

- **Conditions**: sentiment_score < 35 AND trending == False
- **Description**: Narrative dead, exit before reflexive sell-off.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00


---

## Avoid Rules (When to HOLD)

### Rug Score Gate
**ID**: RULE_001 | **Created**: 2026-04-29

- **Conditions**: rug_score >= 75
- **Description**: Composite rug indicator high. Skip — capital preservation > FOMO.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00

### Whale Concentration
**ID**: RULE_002 | **Created**: 2026-04-29

- **Conditions**: top_10_holder_pct >= 80
- **Description**: Top-10 holders own most supply → exit liquidity for insiders.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00

### Unlocked Liquidity
**ID**: RULE_003 | **Created**: 2026-04-29

- **Conditions**: liquidity_locked == False AND rug_score > 40
- **Description**: Unlocked LP + non-zero risk = soft rug pattern. Skip.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00

### Dev Bag Risk
**ID**: RULE_004 | **Created**: 2026-04-29

- **Conditions**: dev_wallet_pct > 12
- **Description**: Dev holding > 12% supply leaves heavy distribution overhang.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00

### Illiquid Token
**ID**: RULE_005 | **Created**: 2026-04-29

- **Conditions**: liquidity < 10000 OR volume_24h < 5000
- **Description**: Not enough liquidity to enter and exit cleanly.
- **Performance**: 0W / 0L (N/A)
- **Total P&L**: $+0.00

