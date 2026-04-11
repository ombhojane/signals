"""
Token Data Service - Aggregated token data from free APIs (DexScreener + GeckoTerminal + Jupiter).
Replaces the expensive GMGN/Apify service.
"""

import time
import httpx
import asyncio
from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel

from core.logging import logger
from core.resilience import resilient
from core.rate_limiter import get_rate_limiter
from core.cache import token_data_cache


# Rate limiters for free tiers
gecko_limiter = get_rate_limiter("geckoterminal", max_requests=28, window_seconds=60)

# GeckoTerminal network ID mapping
GECKO_NETWORKS = {
    "sol": "solana",
    "solana": "solana",
    "eth": "eth",
    "ethereum": "eth",
    "base": "base",
    "bsc": "bsc",
}


class TokenStatData(BaseModel):
    """Token statistics - backward compatible with old GMGN model."""
    token_address: str
    chain: str
    name: Optional[str] = None
    symbol: Optional[str] = None
    price: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    liquidity: Optional[float] = None
    holders: Optional[int] = None
    transactions: Optional[int] = None
    price_change_24h: Optional[float] = None
    created_at: Optional[Union[str, int]] = None
    raw_data: Optional[Dict[str, Any]] = None


class TokenDataService:
    """Aggregated token data from multiple free sources."""

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    # ─── DexScreener (Primary - 300 req/min, no auth) ───

    @resilient(service_name="dexscreener_token", max_retries=2, fallback_value=None)
    async def _fetch_dexscreener_token(self, token_address: str, chain: str) -> Optional[Dict[str, Any]]:
        """Fetch token data from DexScreener search endpoint."""
        start = time.time()
        logger.api_call("DexScreener", endpoint=f"search/{token_address[:16]}...")
        client = await self._get_client()

        resp = await client.get(
            f"https://api.dexscreener.com/latest/dex/search",
            params={"q": token_address}
        )
        resp.raise_for_status()
        data = resp.json()

        duration = (time.time() - start) * 1000
        logger.api_success("DexScreener", duration)

        pairs = data.get("pairs", [])
        if not pairs:
            return None

        # Filter for the correct chain if possible
        dex_chain = GECKO_NETWORKS.get(chain, chain)
        chain_pairs = [p for p in pairs if p.get("chainId", "").lower() == dex_chain.lower()]
        best_pair = chain_pairs[0] if chain_pairs else pairs[0]

        return best_pair

    @resilient(service_name="dexscreener_trending", max_retries=2, fallback_value=[])
    async def _fetch_dexscreener_trending(self) -> List[Dict[str, Any]]:
        """Fetch trending tokens from DexScreener."""
        start = time.time()
        logger.api_call("DexScreener", endpoint="token-boosts/latest")
        client = await self._get_client()

        resp = await client.get("https://api.dexscreener.com/token-boosts/latest/v1")
        resp.raise_for_status()

        duration = (time.time() - start) * 1000
        logger.api_success("DexScreener Trending", duration)
        return resp.json()

    # ─── GeckoTerminal (OHLCV - 30 req/min, no auth) ───

    @resilient(service_name="geckoterminal", max_retries=2, fallback_value=None)
    async def _fetch_gecko_token(self, token_address: str, chain: str) -> Optional[Dict[str, Any]]:
        """Fetch token info from GeckoTerminal."""
        await gecko_limiter.acquire()
        start = time.time()
        network = GECKO_NETWORKS.get(chain, chain)
        logger.api_call("GeckoTerminal", endpoint=f"tokens/{token_address[:16]}...")
        client = await self._get_client()

        resp = await client.get(
            f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{token_address}",
            headers={"Accept": "application/json"}
        )
        resp.raise_for_status()

        duration = (time.time() - start) * 1000
        logger.api_success("GeckoTerminal", duration)
        return resp.json().get("data", {})

    @resilient(service_name="geckoterminal_pools", max_retries=2, fallback_value=None)
    async def _fetch_gecko_pools(self, token_address: str, chain: str) -> Optional[List[Dict[str, Any]]]:
        """Fetch pools for a token from GeckoTerminal."""
        await gecko_limiter.acquire()
        start = time.time()
        network = GECKO_NETWORKS.get(chain, chain)
        logger.api_call("GeckoTerminal", endpoint=f"pools for {token_address[:16]}...")
        client = await self._get_client()

        resp = await client.get(
            f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{token_address}/pools",
            params={"page": 1},
            headers={"Accept": "application/json"}
        )
        resp.raise_for_status()

        duration = (time.time() - start) * 1000
        logger.api_success("GeckoTerminal Pools", duration)
        return resp.json().get("data", [])

    @resilient(service_name="geckoterminal_ohlcv", max_retries=2, fallback_value=[])
    async def _fetch_gecko_ohlcv(self, pool_address: str, chain: str, timeframe: str = "hour") -> List[Dict[str, Any]]:
        """Fetch OHLCV data from GeckoTerminal."""
        await gecko_limiter.acquire()
        start = time.time()
        network = GECKO_NETWORKS.get(chain, chain)
        logger.api_call("GeckoTerminal", endpoint=f"ohlcv/{timeframe}")
        client = await self._get_client()

        resp = await client.get(
            f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}",
            headers={"Accept": "application/json"}
        )
        resp.raise_for_status()

        duration = (time.time() - start) * 1000
        logger.api_success("GeckoTerminal OHLCV", duration)

        ohlcv_list = resp.json().get("data", {}).get("attributes", {}).get("ohlcv_list", [])
        # Format: [[timestamp, open, high, low, close, volume], ...]
        return [
            {
                "timestamp": row[0],
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[5]),
            }
            for row in ohlcv_list
        ]

    # ─── Jupiter Price API (Solana only, free, no auth) ───

    @resilient(service_name="jupiter_price", max_retries=2, fallback_value=None)
    async def _fetch_jupiter_price(self, token_address: str) -> Optional[float]:
        """Fetch current price from Jupiter (Solana only)."""
        start = time.time()
        logger.api_call("Jupiter", endpoint=f"price/{token_address[:16]}...")
        client = await self._get_client()

        resp = await client.get(
            f"https://api.jup.ag/price/v2",
            params={"ids": token_address}
        )
        resp.raise_for_status()

        duration = (time.time() - start) * 1000
        logger.api_success("Jupiter Price", duration)

        data = resp.json().get("data", {})
        token_data = data.get(token_address, {})
        price = token_data.get("price")
        return float(price) if price else None

    # ─── Public API Methods ───

    async def get_token_stats(self, token_addresses: List[str], chain: str = "sol") -> List[TokenStatData]:
        """
        Get token statistics - backward compatible with old GMGN service.

        Args:
            token_addresses: List of token addresses
            chain: Blockchain chain

        Returns:
            List of TokenStatData objects
        """
        results = []
        for addr in token_addresses:
            stat = await self._get_single_token_stat(addr, chain)
            if stat:
                results.append(stat)
        return results

    async def _get_single_token_stat(self, token_address: str, chain: str) -> Optional[TokenStatData]:
        """Get stats for a single token."""
        # Check cache
        cache_key = f"stat:{chain}:{token_address}"
        cached = token_data_cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for token stats: {token_address[:16]}...")
            return cached

        # Primary: DexScreener
        pair = await self._fetch_dexscreener_token(token_address, chain)
        if not pair:
            return None

        base_token = pair.get("baseToken", {})
        price_change = pair.get("priceChange", {})
        txns = pair.get("txns", {})
        h24_txns = txns.get("h24", {})

        stat = TokenStatData(
            token_address=token_address,
            chain=chain,
            name=base_token.get("name"),
            symbol=base_token.get("symbol"),
            price=_safe_float(pair.get("priceUsd")),
            market_cap=_safe_float(pair.get("marketCap") or pair.get("fdv")),
            volume_24h=_safe_float(pair.get("volume", {}).get("h24")),
            liquidity=_safe_float(pair.get("liquidity", {}).get("usd")),
            holders=None,  # DexScreener doesn't provide holders
            transactions=_safe_int(h24_txns.get("buys", 0)) + _safe_int(h24_txns.get("sells", 0)) if h24_txns else None,
            price_change_24h=_safe_float(price_change.get("h24")),
            created_at=pair.get("pairCreatedAt"),
            raw_data=pair,
        )

        token_data_cache.set(cache_key, stat, ttl=60)
        return stat

    async def get_token_analysis(self, token_address: str, chain: str = "sol") -> Dict[str, Any]:
        """
        Get comprehensive token analysis - drop-in replacement for get_gmgn_analysis().

        Returns same dict structure the orchestrator expects.
        """
        # Check cache
        cache_key = f"analysis:{chain}:{token_address}"
        cached = token_data_cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for token analysis: {token_address[:16]}...")
            return cached

        stats = await self.get_token_stats([token_address], chain)
        token_stat = stats[0] if stats else None

        result = {
            "token_address": token_address,
            "chain": chain,
            "token_stats": token_stat.model_dump() if token_stat else None,
            "status": "success" if token_stat else "no_data",
        }

        if token_stat:
            token_data_cache.set(cache_key, result, ttl=60)

        return result

    async def get_token_ohlcv(self, token_address: str, chain: str = "sol", timeframe: str = "hour") -> List[Dict[str, Any]]:
        """
        Get OHLCV historical data from GeckoTerminal.

        Args:
            token_address: Token address
            chain: Blockchain chain
            timeframe: "minute", "hour", or "day"

        Returns:
            List of OHLCV bars
        """
        cache_key = f"ohlcv:{chain}:{token_address}:{timeframe}"
        cached = token_data_cache.get(cache_key)
        if cached:
            return cached

        # First get pools to find the main pool address
        pools = await self._fetch_gecko_pools(token_address, chain)
        if not pools:
            return []

        pool_address = pools[0].get("attributes", {}).get("address") or pools[0].get("id", "").split("_")[-1]
        if not pool_address:
            return []

        ohlcv = await self._fetch_gecko_ohlcv(pool_address, chain, timeframe)
        if ohlcv:
            token_data_cache.set(cache_key, ohlcv, ttl=120)
        return ohlcv

    async def get_trending_tokens(self, chain: str = "sol", limit: int = 20) -> Dict[str, Any]:
        """
        Get trending tokens - replaces GMGN trenches.

        Returns:
            Dict with tokens list and metadata
        """
        cache_key = f"trending:{chain}"
        cached = token_data_cache.get(cache_key)
        if cached:
            return cached

        raw_tokens = await self._fetch_dexscreener_trending()
        if not raw_tokens:
            return {"tokens": [], "total_count": 0, "chain": chain, "data_type": "trending"}

        # Filter by chain
        filtered = []
        for item in raw_tokens:
            if item.get("chainId", "").lower() == GECKO_NETWORKS.get(chain, chain).lower():
                filtered.append({
                    "tokenAddress": item.get("tokenAddress"),
                    "name": item.get("description", ""),
                    "symbol": "",
                    "url": item.get("url"),
                    "icon": item.get("icon"),
                })

        result = {
            "tokens": filtered[:limit],
            "total_count": len(filtered),
            "chain": chain,
            "data_type": "trending",
        }

        token_data_cache.set(cache_key, result, ttl=120)
        return result

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


def _safe_float(value) -> Optional[float]:
    """Safely convert value to float."""
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def _safe_int(value) -> int:
    """Safely convert value to int."""
    try:
        return int(value) if value is not None else 0
    except (ValueError, TypeError):
        return 0


# Global service instance
token_data_service = TokenDataService()


# Convenience functions - backward compatible with old gmgn_apify_service
async def get_token_stats(token_addresses: List[str], chain: str = "sol") -> List[TokenStatData]:
    """Get token statistics for given addresses."""
    return await token_data_service.get_token_stats(token_addresses, chain)


async def get_trending_tokens(chain: str = "sol", limit: int = 80) -> Dict[str, Any]:
    """Get trending tokens."""
    return await token_data_service.get_trending_tokens(chain, limit)


async def get_token_analysis(token_address: str, chain: str = "sol") -> Dict[str, Any]:
    """Get comprehensive token analysis - drop-in replacement for get_gmgn_analysis."""
    return await token_data_service.get_token_analysis(token_address, chain)
