"""
Token Safety Service - Rug check and token security analysis using GoPlus + RugCheck APIs.
Both are free APIs with generous limits.
"""

import os
import time
import httpx
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from core.logging import logger
from core.resilience import resilient
from core.cache import safety_cache


@dataclass
class TokenSafetyReport:
    """Composite safety report from multiple sources."""
    token_address: str
    chain: str

    # Composite scores
    overall_risk_score: int = 50          # 0-100 (100 = highest risk)
    risk_level: str = "UNKNOWN"           # LOW, MEDIUM, HIGH, CRITICAL

    # Contract analysis
    is_honeypot: Optional[bool] = None
    is_mintable: Optional[bool] = None
    is_open_source: Optional[bool] = None
    ownership_renounced: Optional[bool] = None

    # Liquidity analysis
    liquidity_locked: Optional[bool] = None
    lock_remaining_days: int = 0
    liquidity_usd: float = 0.0

    # Holder analysis
    holder_count: int = 0
    top_10_holder_pct: float = 0.0
    dev_wallet_pct: float = 0.0

    # Smart money
    smart_money_flow: str = "neutral"     # buying, selling, neutral

    # Raw API responses
    goplus_data: Optional[Dict[str, Any]] = field(default=None, repr=False)
    rugcheck_data: Optional[Dict[str, Any]] = field(default=None, repr=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "token_address": self.token_address,
            "chain": self.chain,
            "overall_risk_score": self.overall_risk_score,
            "risk_level": self.risk_level,
            "is_honeypot": self.is_honeypot,
            "is_mintable": self.is_mintable,
            "is_open_source": self.is_open_source,
            "ownership_renounced": self.ownership_renounced,
            "liquidity_locked": self.liquidity_locked,
            "lock_remaining_days": self.lock_remaining_days,
            "liquidity_usd": self.liquidity_usd,
            "holder_count": self.holder_count,
            "top_10_holder_pct": self.top_10_holder_pct,
            "dev_wallet_pct": self.dev_wallet_pct,
            "smart_money_flow": self.smart_money_flow,
        }


# GoPlus chain ID mapping
GOPLUS_CHAINS = {
    "sol": "solana",
    "solana": "solana",
    "eth": "1",
    "ethereum": "1",
    "bsc": "56",
    "base": "8453",
}


class TokenSafetyService:
    """Token safety analysis using GoPlus Security + RugCheck APIs."""

    def __init__(self):
        self.goplus_api_key = os.getenv("GOPLUS_API_KEY")
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=15.0)
        return self._client

    # ─── GoPlus Security API (Free, API key optional but recommended) ───

    @resilient(service_name="goplus", max_retries=2, fallback_value=None)
    async def _fetch_goplus(self, token_address: str, chain: str) -> Optional[Dict[str, Any]]:
        """Fetch token security data from GoPlus (EVM chains only - Solana not supported)."""
        goplus_chain = GOPLUS_CHAINS.get(chain, chain)

        # GoPlus doesn't reliably support Solana - skip and rely on RugCheck
        if goplus_chain == "solana":
            return None

        start = time.time()
        logger.api_call("GoPlus Security", endpoint=f"{goplus_chain}/{token_address[:16]}...")
        client = await self._get_client()

        url = f"https://api.gopluslabs.io/api/v1/token_security/{goplus_chain}"
        params = {"contract_addresses": token_address}

        headers = {}
        if self.goplus_api_key:
            headers["Authorization"] = self.goplus_api_key

        resp = await client.get(url, params=params, headers=headers)
        resp.raise_for_status()

        duration = (time.time() - start) * 1000
        logger.api_success("GoPlus Security", duration)

        result = resp.json().get("result", {})

        # For EVM chains, result is keyed by address
        if isinstance(result, dict):
            result = result.get(token_address.lower(), result)

        return result if result else None

    # ─── RugCheck API (Free, Solana-native) ───

    @resilient(service_name="rugcheck", max_retries=2, fallback_value=None)
    async def _fetch_rugcheck(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Fetch token security report from RugCheck (Solana only)."""
        start = time.time()
        logger.api_call("RugCheck", endpoint=f"tokens/{token_address[:16]}...")
        client = await self._get_client()

        resp = await client.get(
            f"https://api.rugcheck.xyz/v1/tokens/{token_address}/report/summary"
        )
        resp.raise_for_status()

        duration = (time.time() - start) * 1000
        logger.api_success("RugCheck", duration)
        return resp.json()

    # ─── Public API ───

    async def get_safety_report(self, token_address: str, chain: str = "sol") -> TokenSafetyReport:
        """
        Get comprehensive safety report by querying GoPlus + RugCheck in parallel.

        Args:
            token_address: Token contract address
            chain: Blockchain chain

        Returns:
            TokenSafetyReport with composite safety scores
        """
        # Check cache
        cache_key = f"safety:{chain}:{token_address}"
        cached = safety_cache.get(cache_key)
        if cached:
            logger.debug(f"Cache hit for safety report: {token_address[:16]}...")
            return cached

        report = TokenSafetyReport(token_address=token_address, chain=chain)

        # Fetch from both sources in parallel
        tasks = {"goplus": self._fetch_goplus(token_address, chain)}
        if chain in ("sol", "solana"):
            tasks["rugcheck"] = self._fetch_rugcheck(token_address)

        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        fetched = {}
        for key, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                logger.warning(f"{key} fetch failed: {result}")
                fetched[key] = None
            else:
                fetched[key] = result

        goplus_data = fetched.get("goplus")
        rugcheck_data = fetched.get("rugcheck")

        report.goplus_data = goplus_data
        report.rugcheck_data = rugcheck_data

        # Parse GoPlus data
        if goplus_data:
            self._parse_goplus(report, goplus_data)

        # Parse RugCheck data (Solana only)
        if rugcheck_data:
            self._parse_rugcheck(report, rugcheck_data)

        # Calculate composite risk score
        self._calculate_risk_score(report)

        safety_cache.set(cache_key, report)
        return report

    def _parse_goplus(self, report: TokenSafetyReport, data: Dict[str, Any]):
        """Extract safety info from GoPlus response."""
        report.is_honeypot = _bool_field(data.get("is_honeypot"))
        report.is_mintable = _bool_field(data.get("is_mintable"))
        report.is_open_source = _bool_field(data.get("is_open_source"))
        report.ownership_renounced = _bool_field(data.get("can_take_back_ownership"), invert=True)

        # Holder analysis from GoPlus
        holders = data.get("holders") or data.get("holder_count")
        if holders:
            if isinstance(holders, list):
                report.holder_count = len(holders)
            elif isinstance(holders, (int, str)):
                try:
                    report.holder_count = int(holders)
                except (ValueError, TypeError):
                    pass

        # Top holders concentration
        top_holders = data.get("holders", [])
        if isinstance(top_holders, list) and top_holders:
            top_10 = top_holders[:10]
            total_pct = sum(float(h.get("percent", 0)) for h in top_10 if isinstance(h, dict))
            report.top_10_holder_pct = round(total_pct * 100, 2)

        # Creator/dev info
        creator_pct = data.get("creator_percent")
        if creator_pct:
            try:
                report.dev_wallet_pct = round(float(creator_pct) * 100, 2)
            except (ValueError, TypeError):
                pass

        # LP info
        lp_holders = data.get("lp_holders", [])
        if isinstance(lp_holders, list):
            for lp in lp_holders:
                if isinstance(lp, dict) and _bool_field(lp.get("is_locked")):
                    report.liquidity_locked = True
                    break

    def _parse_rugcheck(self, report: TokenSafetyReport, data: Dict[str, Any]):
        """Extract safety info from RugCheck response."""
        # Use normalised score (0-10 scale, lower = safer) -> map to 0-100 risk
        score_norm = data.get("score_normalised")
        if score_norm is not None:
            try:
                # score_normalised: 0-10 (lower = safer). Map to 0-100 risk.
                report.overall_risk_score = min(int(float(score_norm) * 10), 100)
            except (ValueError, TypeError):
                pass
        else:
            # Fallback to raw score
            score = data.get("score")
            if score is not None:
                try:
                    report.overall_risk_score = min(int(score), 100)
                except (ValueError, TypeError):
                    pass

        # Risk level from score_label or derive from normalised score
        risk_level = data.get("score_label") or data.get("riskLevel")
        if risk_level:
            risk_map = {
                "Good": "LOW",
                "Warning": "MEDIUM",
                "Danger": "HIGH",
                "Critical": "CRITICAL",
            }
            report.risk_level = risk_map.get(risk_level, report.risk_level)

        # Parse risks list
        risks = data.get("risks", [])
        if isinstance(risks, list):
            for risk in risks:
                name = (risk.get("name") or "").lower()
                if "mint" in name:
                    report.is_mintable = True
                if "honeypot" in name:
                    report.is_honeypot = True
                if "freeze" in name or "frozen" in name:
                    pass  # Could track freeze authority

        # LP locked percentage from RugCheck
        lp_locked_pct = data.get("lpLockedPct")
        if lp_locked_pct is not None:
            try:
                pct = float(lp_locked_pct)
                report.liquidity_locked = pct > 50  # Consider locked if >50% LP locked
            except (ValueError, TypeError):
                pass

        # Liquidity data
        if data.get("liquidity_locked") is not None:
            report.liquidity_locked = bool(data["liquidity_locked"])

    def _calculate_risk_score(self, report: TokenSafetyReport):
        """Calculate composite risk score from all available data."""
        # If we have GoPlus data, calculate composite score from risk factors
        if report.goplus_data:
            risk_factors = []

            if report.is_honeypot is True:
                risk_factors.append(40)
            elif report.is_honeypot is False:
                risk_factors.append(0)

            if report.is_mintable is True:
                risk_factors.append(15)
            elif report.is_mintable is False:
                risk_factors.append(0)

            if report.ownership_renounced is False:
                risk_factors.append(10)
            elif report.ownership_renounced is True:
                risk_factors.append(0)

            if report.top_10_holder_pct > 50:
                risk_factors.append(20)
            elif report.top_10_holder_pct > 30:
                risk_factors.append(10)

            if report.liquidity_locked is False:
                risk_factors.append(15)
            elif report.liquidity_locked is True:
                risk_factors.append(0)

            if risk_factors:
                report.overall_risk_score = min(sum(risk_factors), 100)

        # RugCheck score is already set in _parse_rugcheck, so we just update risk level
        if report.overall_risk_score <= 20:
            report.risk_level = "LOW"
        elif report.overall_risk_score <= 45:
            report.risk_level = "MEDIUM"
        elif report.overall_risk_score <= 70:
            report.risk_level = "HIGH"
        else:
            report.risk_level = "CRITICAL"

    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()


def _bool_field(value, invert: bool = False) -> Optional[bool]:
    """Convert GoPlus '0'/'1' string fields to bool."""
    if value is None:
        return None
    if isinstance(value, bool):
        return (not value) if invert else value
    if isinstance(value, str):
        result = value == "1"
        return (not result) if invert else result
    return None


# Global service instance
token_safety_service = TokenSafetyService()


async def get_safety_report(token_address: str, chain: str = "sol") -> TokenSafetyReport:
    """Convenience function for getting a safety report."""
    return await token_safety_service.get_safety_report(token_address, chain)
