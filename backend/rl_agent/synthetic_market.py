"""
Enhanced Synthetic Market Generator V2 - Rich token data for agentic trading.

Generates realistic synthetic cryptocurrency data with full token schema:
- Identity (name, symbol, address)
- Price data (OHLCV, market cap, liquidity)
- On-chain data (holders, rug score, smart money)
- Social data (mentions, sentiment, influencers)
- Technical indicators (RSI, MACD, Bollinger)
"""

import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import random
import string


# Token name generators
PREFIXES = ["Moon", "Doge", "Shib", "Pepe", "Wojak", "Chad", "Giga", "Based", "Frog", "Cat"]
SUFFIXES = ["Coin", "Token", "Inu", "Moon", "Rocket", "AI", "GPT", "Swap", "Fi", "X"]


def generate_token_name() -> tuple:
    """Generate random meme token name and symbol."""
    prefix = random.choice(PREFIXES)
    suffix = random.choice(SUFFIXES)
    name = f"{prefix}{suffix}"
    symbol = f"${prefix[:3].upper()}{suffix[0].upper()}"
    return name, symbol


def generate_address(chain: str = "sol") -> str:
    """Generate fake token address."""
    if chain == "sol":
        chars = string.ascii_letters + string.digits
        return ''.join(random.choice(chars) for _ in range(44))
    else:
        return "0x" + ''.join(random.choice("0123456789abcdef") for _ in range(40))


@dataclass
class TokenSnapshot:
    """Complete token state at a point in time."""
    
    # Identity
    name: str
    symbol: str
    address: str
    chain: str
    
    # Time
    timestamp: str
    step: int
    
    # Price Data
    price: float
    price_change_1h: float
    price_change_24h: float
    volume_24h: float
    market_cap: float
    liquidity: float
    
    # On-Chain Data (GMGN-like)
    holder_count: int
    top_10_holder_pct: float
    smart_money_flow: str  # "buying", "selling", "neutral"
    rug_score: int  # 0-100 (lower is safer)
    dev_wallet_pct: float
    liquidity_locked: bool
    lock_days_remaining: int
    
    # Social Data (Twitter-like)
    mentions_24h: int
    sentiment_score: int  # 0-100
    influencer_mentions: int
    trending: bool
    community_size: int
    
    # Technical Indicators
    rsi: float
    macd: float
    macd_signal: float
    bollinger_upper: float
    bollinger_lower: float
    bollinger_position: float  # -1 to 1
    volatility: float
    volume_ratio: float  # vs average
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def to_market_summary(self) -> str:
        """Format as human-readable summary for LLM."""
        return f"""## Token: {self.name} ({self.symbol})
Chain: {self.chain} | Address: {self.address[:8]}...

### Price & Volume
- Price: ${self.price:.6f}
- 1h Change: {self.price_change_1h:+.2f}%
- 24h Change: {self.price_change_24h:+.2f}%
- Volume 24h: ${self.volume_24h:,.0f}
- Market Cap: ${self.market_cap:,.0f}
- Liquidity: ${self.liquidity:,.0f}

### On-Chain Analysis
- Holders: {self.holder_count:,}
- Top 10 Holders: {self.top_10_holder_pct:.1f}%
- Smart Money: {self.smart_money_flow.upper()}
- Rug Score: {self.rug_score}/100 ({'SAFE' if self.rug_score < 30 else 'CAUTION' if self.rug_score < 60 else 'DANGER'})
- Dev Wallet: {self.dev_wallet_pct:.1f}%
- Liquidity Locked: {'Yes' if self.liquidity_locked else 'No'} ({self.lock_days_remaining} days)

### Social Sentiment
- 24h Mentions: {self.mentions_24h}
- Sentiment: {self.sentiment_score}/100 ({'Bullish' if self.sentiment_score > 60 else 'Neutral' if self.sentiment_score > 40 else 'Bearish'})
- Influencer Mentions: {self.influencer_mentions}
- Trending: {'🔥 Yes' if self.trending else 'No'}
- Community Size: {self.community_size:,}

### Technical Indicators
- RSI: {self.rsi:.1f} ({'Overbought' if self.rsi > 70 else 'Oversold' if self.rsi < 30 else 'Neutral'})
- MACD: {self.macd:.4f} (Signal: {self.macd_signal:.4f})
- Bollinger Position: {self.bollinger_position:.2f} ({'+' if self.bollinger_position > 0 else ''}{self.bollinger_position*100:.0f}%)
- Volatility: {self.volatility:.2f}
- Volume Ratio: {self.volume_ratio:.2f}x average"""


class SyntheticMarket:
    """
    Enhanced synthetic market generator with rich token data.
    
    Generates realistic market scenarios with:
    - Multiple market regimes (bull, bear, sideways, volatile)
    - Correlated on-chain and social metrics
    - Pump & dump events
    - Rug pull scenarios
    """
    
    def __init__(
        self,
        initial_price: float = 0.001,
        chain: str = "sol",
        seed: Optional[int] = None
    ):
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
        
        self.chain = chain
        self.initial_price = initial_price
        
        # Generate token identity
        self.name, self.symbol = generate_token_name()
        self.address = generate_address(chain)
        
        # Initialize state
        self.price = initial_price
        self.step = 0
        self.regime = "sideways"
        self.regime_duration = 0
        
        # Base metrics
        self.base_volume = np.random.uniform(50000, 500000)
        self.base_liquidity = np.random.uniform(10000, 100000)
        self.base_holders = np.random.randint(100, 2000)
        self.base_community = np.random.randint(500, 10000)
        
        # Safety metrics (constant for token)
        self.dev_wallet_pct = np.random.uniform(1, 15)
        self.liquidity_locked = np.random.random() > 0.3
        self.lock_days = np.random.randint(30, 365) if self.liquidity_locked else 0
        self.base_rug_score = np.random.randint(5, 50)
        
        # Price history for indicators
        self.price_history = [initial_price]
        self.volume_history = [self.base_volume]
        
    def _update_regime(self):
        """Randomly transition between market regimes."""
        self.regime_duration += 1
        
        # Change regime every 50-150 steps on average
        if self.regime_duration > np.random.randint(50, 150):
            regimes = ["bull", "bear", "sideways", "volatile"]
            weights = [0.25, 0.25, 0.35, 0.15]
            self.regime = np.random.choice(regimes, p=weights)
            self.regime_duration = 0
    
    def _generate_price_change(self) -> float:
        """Generate price change based on current regime."""
        if self.regime == "bull":
            drift = 0.002
            volatility = 0.03
        elif self.regime == "bear":
            drift = -0.002
            volatility = 0.03
        elif self.regime == "volatile":
            drift = 0.0
            volatility = 0.08
        else:  # sideways
            drift = 0.0
            volatility = 0.015
        
        # Random pump/dump events (5% chance)
        if np.random.random() < 0.05:
            return np.random.choice([-0.15, 0.20]) + np.random.normal(0, 0.02)
        
        return np.random.normal(drift, volatility)
    
    def _calculate_rsi(self, window: int = 14) -> float:
        """Calculate RSI from price history."""
        if len(self.price_history) < window + 1:
            return 50.0
        
        prices = np.array(self.price_history[-window-1:])
        deltas = np.diff(prices)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains) if len(gains) > 0 else 0
        avg_loss = np.mean(losses) if len(losses) > 0 else 0.0001
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return np.clip(rsi, 0, 100)
    
    def _calculate_macd(self) -> tuple:
        """Calculate MACD and signal line (numpy EMA)."""
        if len(self.price_history) < 26:
            return 0.0, 0.0

        def _ema(vals, span):
            alpha = 2.0 / (span + 1.0)
            ema = vals[0]
            for v in vals[1:]:
                ema = alpha * v + (1 - alpha) * ema
            return ema

        ema12 = _ema(self.price_history, 12)
        ema26 = _ema(self.price_history, 26)
        macd = ema12 - ema26
        signal = macd * 0.8  # simplified 9-period EMA of MACD
        return float(macd), float(signal)
    
    def _calculate_bollinger(self) -> tuple:
        """Calculate Bollinger Bands position."""
        if len(self.price_history) < 20:
            return self.price * 1.1, self.price * 0.9, 0.0
        
        prices = np.array(self.price_history[-20:])
        sma = np.mean(prices)
        std = np.std(prices)
        
        upper = sma + 2 * std
        lower = sma - 2 * std
        
        # Position: -1 (at lower), 0 (at middle), 1 (at upper)
        if std > 0:
            position = (self.price - sma) / (2 * std)
        else:
            position = 0
        
        return float(upper), float(lower), float(np.clip(position, -1, 1))
    
    def step_market(self) -> TokenSnapshot:
        """Advance market by one step and return current state."""
        self.step += 1
        self._update_regime()
        
        # Update price
        price_change_pct = self._generate_price_change()
        self.price *= (1 + price_change_pct)
        self.price = max(self.price, 0.0000001)  # Floor
        
        self.price_history.append(self.price)
        if len(self.price_history) > 100:
            self.price_history = self.price_history[-100:]
        
        # Calculate 1h and 24h changes
        price_1h_ago = self.price_history[-min(12, len(self.price_history))]
        price_24h_ago = self.price_history[-min(96, len(self.price_history))]
        price_change_1h = ((self.price / price_1h_ago) - 1) * 100
        price_change_24h = ((self.price / price_24h_ago) - 1) * 100
        
        # Volume (correlated with price movement)
        volume_mult = 1 + abs(price_change_pct) * 10 + np.random.uniform(-0.3, 0.3)
        volume = self.base_volume * volume_mult
        self.volume_history.append(volume)
        if len(self.volume_history) > 100:
            self.volume_history = self.volume_history[-100:]
        
        # Market cap & liquidity
        market_cap = self.price * np.random.uniform(1e9, 1e11)  # Total supply
        liquidity = self.base_liquidity * (1 + price_change_24h / 100)
        
        # On-chain metrics (evolve slowly)
        holder_change = np.random.randint(-5, 10) if price_change_pct > 0 else np.random.randint(-10, 5)
        self.base_holders = max(50, self.base_holders + holder_change)
        
        # Top 10 holder concentration
        top_10_pct = 30 + np.random.uniform(-5, 5) + (50 - self.base_holders / 100)
        top_10_pct = np.clip(top_10_pct, 20, 80)
        
        # Smart money flow
        if price_change_24h > 5:
            smart_money = "buying"
        elif price_change_24h < -5:
            smart_money = "selling"
        else:
            smart_money = np.random.choice(["buying", "selling", "neutral"], p=[0.3, 0.3, 0.4])
        
        # Rug score (increases if suspicious activity)
        rug_adjustment = 0
        if top_10_pct > 60:
            rug_adjustment += 10
        if not self.liquidity_locked:
            rug_adjustment += 15
        if self.dev_wallet_pct > 10:
            rug_adjustment += 10
        rug_score = int(np.clip(self.base_rug_score + rug_adjustment + np.random.randint(-5, 5), 0, 100))
        
        # Social metrics (correlated with price movement)
        sentiment_base = 50 + price_change_24h * 2
        sentiment = int(np.clip(sentiment_base + np.random.randint(-10, 10), 0, 100))
        
        mentions = max(0, int(self.base_community * 0.01 * (1 + price_change_24h / 20) + np.random.randint(-10, 20)))
        influencer_mentions = max(0, np.random.poisson(2 if sentiment > 60 else 0.5))
        trending = mentions > 100 and sentiment > 65
        
        community_change = np.random.randint(-20, 50) if price_change_24h > 0 else np.random.randint(-50, 20)
        self.base_community = max(100, self.base_community + community_change)
        
        # Technical indicators
        rsi = self._calculate_rsi()
        macd, macd_signal = self._calculate_macd()
        bb_upper, bb_lower, bb_position = self._calculate_bollinger()
        
        avg_volume = np.mean(self.volume_history) if self.volume_history else volume
        volume_ratio = volume / avg_volume if avg_volume > 0 else 1.0
        
        volatility = np.std(self.price_history[-20:]) / np.mean(self.price_history[-20:]) if len(self.price_history) >= 20 else 0.5
        
        # Lock days decrease
        lock_remaining = max(0, self.lock_days - self.step // 96)  # 1 day = 96 steps
        
        return TokenSnapshot(
            name=self.name,
            symbol=self.symbol,
            address=self.address,
            chain=self.chain,
            timestamp=datetime.now().isoformat(),
            step=self.step,
            price=round(self.price, 8),
            price_change_1h=round(price_change_1h, 2),
            price_change_24h=round(price_change_24h, 2),
            volume_24h=round(volume, 2),
            market_cap=round(market_cap, 2),
            liquidity=round(liquidity, 2),
            holder_count=self.base_holders,
            top_10_holder_pct=round(top_10_pct, 1),
            smart_money_flow=smart_money,
            rug_score=rug_score,
            dev_wallet_pct=round(self.dev_wallet_pct, 1),
            liquidity_locked=self.liquidity_locked,
            lock_days_remaining=lock_remaining,
            mentions_24h=mentions,
            sentiment_score=sentiment,
            influencer_mentions=influencer_mentions,
            trending=trending,
            community_size=self.base_community,
            rsi=round(rsi, 1),
            macd=round(macd, 6),
            macd_signal=round(macd_signal, 6),
            bollinger_upper=round(bb_upper, 8),
            bollinger_lower=round(bb_lower, 8),
            bollinger_position=round(bb_position, 2),
            volatility=round(volatility, 3),
            volume_ratio=round(volume_ratio, 2)
        )
    
    def reset(self, seed: Optional[int] = None):
        """Reset market to initial state with new token."""
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
        
        self.name, self.symbol = generate_token_name()
        self.address = generate_address(self.chain)
        
        self.price = self.initial_price * np.random.uniform(0.5, 2.0)
        self.step = 0
        self.regime = "sideways"
        self.regime_duration = 0
        
        self.base_volume = np.random.uniform(50000, 500000)
        self.base_liquidity = np.random.uniform(10000, 100000)
        self.base_holders = np.random.randint(100, 2000)
        self.base_community = np.random.randint(500, 10000)
        
        self.dev_wallet_pct = np.random.uniform(1, 15)
        self.liquidity_locked = np.random.random() > 0.3
        self.lock_days = np.random.randint(30, 365) if self.liquidity_locked else 0
        self.base_rug_score = np.random.randint(5, 50)
        
        self.price_history = [self.price]
        self.volume_history = [self.base_volume]
        
        return self.step_market()
