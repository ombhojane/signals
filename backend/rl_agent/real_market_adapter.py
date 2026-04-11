"""
Real Market Adapter - Maps real API data to TokenSnapshot format for the RL agent.
Enables the agent to analyze real Solana tokens instead of only synthetic data.
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List

from rl_agent.synthetic_market import TokenSnapshot
from rl_agent.indicators import (
    calculate_rsi,
    calculate_macd,
    calculate_bollinger,
    calculate_volatility,
    calculate_volume_ratio,
)
from services.token_data_service import token_data_service
from services.token_safety_service import token_safety_service
from services.twitter_api_v2 import fetch_token_tweets


class RealMarketAdapter:
    """
    Adapts real API data to TokenSnapshot format for the RL trading agent.

    Usage:
        adapter = RealMarketAdapter()
        snapshot = await adapter.get_snapshot("TokenMintAddress", "sol")
        # snapshot is a TokenSnapshot with real data
    """

    async def get_snapshot(self, token_address: str, chain: str = "sol") -> TokenSnapshot:
        """
        Fetch real data from all services and map to TokenSnapshot.

        Args:
            token_address: Token mint/contract address
            chain: Blockchain chain

        Returns:
            TokenSnapshot populated with real data
        """
        # Fetch all data in parallel
        results = await asyncio.gather(
            self._fetch_token_data(token_address, chain),
            self._fetch_safety_data(token_address, chain),
            self._fetch_ohlcv(token_address, chain),
            self._fetch_twitter_data(token_address),
            return_exceptions=True,
        )

        token_data = results[0] if not isinstance(results[0], Exception) else {}
        safety_data = results[1] if not isinstance(results[1], Exception) else None
        ohlcv = results[2] if not isinstance(results[2], Exception) else []
        twitter_data = results[3] if not isinstance(results[3], Exception) else {}

        return self._map_to_snapshot(token_address, chain, token_data, safety_data, ohlcv, twitter_data)

    async def _fetch_token_data(self, token_address: str, chain: str) -> Dict[str, Any]:
        """Fetch token price/volume data."""
        stats = await token_data_service.get_token_stats([token_address], chain)
        if stats:
            return stats[0].model_dump()
        return {}

    async def _fetch_safety_data(self, token_address: str, chain: str):
        """Fetch safety report."""
        return await token_safety_service.get_safety_report(token_address, chain)

    async def _fetch_ohlcv(self, token_address: str, chain: str) -> List[Dict[str, Any]]:
        """Fetch OHLCV for technical indicators."""
        return await token_data_service.get_token_ohlcv(token_address, chain, "hour")

    async def _fetch_twitter_data(self, token_address: str) -> Dict[str, Any]:
        """Fetch Twitter data - need symbol first."""
        # We'll get symbol from token data; if not available, skip
        try:
            stats = await token_data_service.get_token_stats([token_address], "sol")
            if stats and stats[0].symbol:
                return await fetch_token_tweets(
                    token_symbol=stats[0].symbol,
                    token_name=stats[0].name,
                    token_address=token_address,
                    max_tweets=20,
                )
        except Exception:
            pass
        return {}

    def _map_to_snapshot(
        self,
        token_address: str,
        chain: str,
        token_data: Dict[str, Any],
        safety_data: Optional[Any],
        ohlcv: List[Dict[str, Any]],
        twitter_data: Dict[str, Any],
    ) -> TokenSnapshot:
        """Map all API data to a TokenSnapshot."""

        # Extract OHLCV prices for indicators
        close_prices = [bar["close"] for bar in ohlcv] if ohlcv else []
        volumes = [bar["volume"] for bar in ohlcv] if ohlcv else []

        # Calculate technical indicators from real OHLCV
        current_price = token_data.get("price", close_prices[-1] if close_prices else 0)
        rsi = calculate_rsi(close_prices) if close_prices else 50.0
        macd_val, macd_sig = calculate_macd(close_prices) if close_prices else (0.0, 0.0)
        boll_upper, boll_lower, boll_pos = calculate_bollinger(close_prices, current_price) if close_prices else (current_price * 1.1, current_price * 0.9, 0.0)
        volatility = calculate_volatility(close_prices) if close_prices else 0.0
        vol_ratio = calculate_volume_ratio(volumes) if volumes else 1.0

        # Price changes from OHLCV
        if len(close_prices) >= 2:
            price_change_1h = ((close_prices[-1] / close_prices[-2]) - 1) * 100
        else:
            price_change_1h = 0.0

        price_change_24h = token_data.get("price_change_24h", 0.0) or 0.0

        # Safety data extraction
        safety_dict = safety_data.to_dict() if hasattr(safety_data, 'to_dict') else (safety_data or {})

        # Twitter data extraction
        tweets = twitter_data.get("tweets", [])
        total_tweets = twitter_data.get("total_tweets", 0)
        influencer_count = sum(
            1 for t in tweets
            if isinstance(t, dict) and t.get("author", {}).get("isBlueVerified")
        )
        total_followers = sum(
            (t.get("author", {}).get("followers", 0) or 0)
            for t in tweets if isinstance(t, dict)
        )

        return TokenSnapshot(
            # Identity
            name=token_data.get("name", "Unknown"),
            symbol=token_data.get("symbol", "???"),
            address=token_address,
            chain=chain,

            # Time
            timestamp=datetime.now().isoformat(),
            step=0,

            # Price Data
            price=current_price or 0,
            price_change_1h=price_change_1h,
            price_change_24h=price_change_24h,
            volume_24h=token_data.get("volume_24h", 0) or 0,
            market_cap=token_data.get("market_cap", 0) or 0,
            liquidity=token_data.get("liquidity", 0) or 0,

            # On-Chain Data from Safety Service
            holder_count=safety_dict.get("holder_count", 0),
            top_10_holder_pct=safety_dict.get("top_10_holder_pct", 0),
            smart_money_flow=safety_dict.get("smart_money_flow", "neutral"),
            rug_score=safety_dict.get("overall_risk_score", 50),
            dev_wallet_pct=safety_dict.get("dev_wallet_pct", 0),
            liquidity_locked=safety_dict.get("liquidity_locked", False) or False,
            lock_days_remaining=safety_dict.get("lock_remaining_days", 0),

            # Social Data from Twitter
            mentions_24h=total_tweets,
            sentiment_score=50,  # Will be calculated by AI agent
            influencer_mentions=influencer_count,
            trending=total_tweets > 50,
            community_size=total_followers,

            # Technical Indicators from OHLCV
            rsi=rsi,
            macd=macd_val,
            macd_signal=macd_sig,
            bollinger_upper=boll_upper,
            bollinger_lower=boll_lower,
            bollinger_position=boll_pos,
            volatility=volatility,
            volume_ratio=vol_ratio,
        )
