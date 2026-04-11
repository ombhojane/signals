"""
Token Scan Router - Comprehensive token analysis for simulation workflow.

Orchestrates:
1. Token data fetching (DEX + safety)
2. Social sentiment (if available)
3. Risk/rug assessment
4. AI-powered prediction
"""

import asyncio
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any
from pydantic import BaseModel

from core.logging import logger
from core.cache import token_data_cache
from core.data_validator import validate_dex_data, validate_gmgn_data

# Import services
from services.dex_api import get_dex_data
from services.token_data_service import get_token_analysis as get_gmgn_token_analysis
from services.token_safety_service import get_safety_report
from services.crewat import token_agents
from core.constants import get_chain_id


router = APIRouter(prefix="/token-scan", tags=["Token Scan"])


class TokenScanRequest(BaseModel):
    """Request for comprehensive token scan."""
    token_address: str
    chain: str = "sol"
    pair_address: Optional[str] = None
    include_social: bool = True


class ScanResult(BaseModel):
    """Comprehensive scan result."""
    token_address: str
    chain: str
    token: Dict[str, Any]
    safety: Dict[str, Any]
    social: Optional[Dict[str, Any]]
    prediction: Dict[str, Any]
    data_status: Dict[str, str]


async def _fetch_dex_data(chain: str, pair_address: str):
    """Fetch DEX data using DexScreener search API."""
    import httpx
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Use search endpoint with the address/symbol directly
            resp = await client.get(
                "https://api.dexscreener.com/latest/dex/search",
                params={"q": pair_address}
            )
            resp.raise_for_status()
            data = resp.json()
            
            pairs = data.get("pairs", [])
            if not pairs:
                return None
            
            # Filter by chain
            dex_chain = get_chain_id(chain, "dex")
            chain_pairs = [p for p in pairs if p.get("chainId", "").lower() == dex_chain.lower()]
            best_pair = chain_pairs[0] if chain_pairs else pairs[0]
            
            return {"pairs": [best_pair]}
    except Exception as e:
        logger.warning(f"DEX fetch failed: {str(e)}")
        return None


async def _fetch_safety_report(token_address: str, chain: str) -> Dict[str, Any]:
    """Fetch safety/rug check report."""
    try:
        report = await get_safety_report(token_address, chain)
        return report.to_dict()
    except Exception as e:
        logger.warning(f"Safety report fetch failed: {str(e)}")
        return {
            "overall_risk_score": 50,
            "risk_level": "UNKNOWN",
            "error": str(e)
        }


async def _run_prediction(
    dex_data: Optional[Dict],
    gmgn_data: Optional[Dict],
    safety_data: Dict,
    chain: str
) -> Dict[str, Any]:
    """Run AI prediction based on available data."""
    try:
        # Build combined data payload
        combined = {
            "dex": dex_data or {},
            "gmgn": gmgn_data or {},
            "safety": safety_data
        }
        
        # Run market signals analysis
        market_analysis = {}
        if dex_data and validate_dex_data(dex_data).is_valid:
            try:
                market_analysis = await token_agents.market_signals(dex_data)
            except Exception as e:
                logger.warning(f"Market analysis failed: {str(e)}")
        
        # Run GMGN/safety analysis
        safety_analysis = {}
        if gmgn_data and validate_gmgn_data(gmgn_data).is_valid:
            try:
                safety_analysis = await token_agents.gmgn_signals(gmgn_data)
            except Exception as e:
                logger.warning(f"Safety analysis failed: {str(e)}")
        
        # Determine action based on analysis
        market_health = market_analysis.get("market_health", 5) if isinstance(market_analysis, dict) else 5
        risk_score = safety_data.get("overall_risk_score", 50)
        risk_level = safety_data.get("risk_level", "UNKNOWN")
        
        # Use AI agent's safety recommendation if available (more reliable)
        safety_rec = safety_analysis.get("recommendation") if isinstance(safety_analysis, dict) else None
        rug_risk_score = safety_analysis.get("rug_risk_score", 100) if isinstance(safety_analysis, dict) else 100
        
        # If we have real data (risk_score is set from actual API, not default 50)
        has_real_safety_data = risk_score != 50 or safety_data.get("liquidity_usd", 0) > 0
        
        # AI safety recommendation takes precedence
        if safety_rec and safety_rec.upper() in ["AVOID", "RUG", "DANGER", "DO NOT BUY"]:
            action = "SELL"
            confidence = 85
            reasoning = f"AI safety warning: {safety_rec}"
        elif safety_rec and safety_rec.upper() == "SAFE":
            # AI says safe - base decision on market health
            if market_health >= 7:
                action = "BUY"
                confidence = min(90, market_health * 10 + 10)
                reasoning = f"AI: {safety_rec}, Market: {market_health}/10"
            else:
                action = "HOLD"
                confidence = 50 + int(market_health * 5)
                reasoning = f"AI: {safety_rec}, weak market"
        elif safety_rec and safety_rec.upper() == "CAUTION":
            # CAUTION - use market health to decide
            if market_health >= 7:
                action = "BUY"
                confidence = 60
                reasoning = f"AI: {safety_rec}, strong market ({market_health}/10)"
            else:
                action = "HOLD"
                confidence = 45
                reasoning = f"AI: {safety_rec}, moderate risk"
        elif has_real_safety_data and risk_score >= 70:
            action = "SELL"
            confidence = max(20, 100 - risk_score)
            reasoning = f"High risk ({risk_level}): {risk_score}/100"
        elif has_real_safety_data and risk_score >= 40:
            action = "HOLD"
            confidence = 50
            reasoning = f"Medium risk ({risk_level}): {risk_score}/100"
        elif has_real_safety_data and risk_score < 30 and market_health >= 7:
            action = "BUY"
            confidence = int(min(market_health * 10 + 20, 90))
            reasoning = f"Low risk ({risk_score}/100), market: {market_health}/10"
        elif has_real_safety_data and risk_score < 30:
            action = "BUY" if market_health >= 5 else "HOLD"
            confidence = int(market_health * 10)
            reasoning = f"Risk: {risk_score}/100, Market: {market_health}/10"
        elif has_real_safety_data and risk_score >= 70:
            action = "SELL"
            confidence = max(20, 100 - risk_score)
            reasoning = f"High risk ({risk_level}): {risk_score}/100"
        elif has_real_safety_data and risk_score >= 40:
            action = "HOLD"
            confidence = 50
            reasoning = f"Medium risk ({risk_level}): {risk_score}/100"
        elif has_real_safety_data and risk_score < 30 and market_health >= 7:
            action = "BUY"
            confidence = int(min(market_health * 10 + 20, 90))
            reasoning = f"Low risk ({risk_score}/100), market: {market_health}/10"
        elif has_real_safety_data and risk_score < 30:
            action = "BUY" if market_health >= 5 else "HOLD"
            confidence = int(market_health * 10)
            reasoning = f"Risk: {risk_score}/100, Market: {market_health}/10"
        elif market_health >= 7:
            action = "BUY"
            confidence = int(market_health * 10)
            reasoning = f"Strong market health: {market_health}/10"
        elif market_health >= 5:
            action = "BUY"
            confidence = 50
            reasoning = f"Moderate market health: {market_health}/10"
        else:
            action = "HOLD"
            confidence = 30
            reasoning = f"Weak market health: {market_health}/10"
        
        # Calculate price target and stop loss
        current_price = 0.0
        if dex_data and "pairs" in dex_data and dex_data["pairs"]:
            pair = dex_data["pairs"][0]
            current_price = float(pair.get("priceUsd", 0) or 0)
        
        price_target = None
        stop_loss = None
        if current_price > 0:
            if action == "BUY":
                price_target = current_price * 1.5  # 50% upside target
                stop_loss = current_price * 0.85  # 15% stop loss
            elif action == "SELL":
                price_target = current_price * 0.8  # 20% downside target
        
        return {
            "action": action,
            "confidence": confidence,
            "reasoning": reasoning,
            "risk_assessment": f"Risk score: {risk_score}/100, Market health: {market_health}/10",
            "price_target": price_target,
            "stop_loss": stop_loss,
            "predicted_price": price_target or current_price,
            "market_analysis": market_analysis,
            "safety_analysis": safety_analysis
        }
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        return {
            "action": "HOLD",
            "confidence": 0,
            "reasoning": f"Prediction failed: {str(e)}",
            "risk_assessment": "Error",
            "error": str(e)
        }


@router.post("/analyze", response_model=ScanResult)
async def analyze_token(request: TokenScanRequest) -> ScanResult:
    """
    Perform comprehensive token scan.
    
    This is the main endpoint for the simulation workflow that:
    1. Fetches token data from DEX (DexScreener)
    2. Fetches safety/rug check (GoPlus + custom)
    3. Optionally fetches social data
    4. Runs AI prediction
    """
    logger.section("TOKEN SCAN")
    logger.info(f"Scanning token", address=request.token_address[:16] + "...", chain=request.chain)
    
    token_address = request.token_address
    chain = request.chain
    pair_address = request.pair_address or token_address
    
    # Try cache first
    cache_key = f"scan:{chain}:{token_address}"
    cached = token_data_cache.get(cache_key)
    if cached:
        logger.info("Using cached scan result")
        return cached
    
    try:
        # ═══════════════════════════════════════════════════════════════
        # PHASE 1: Parallel Data Fetching
        # ═══════════════════════════════════════════════════════════════
        logger.section("PHASE 1: FETCHING DATA")
        
        # Run data fetches in parallel
        dex_task = _fetch_dex_data(chain, pair_address)
        gmgn_task = get_gmgn_token_analysis(token_address, chain)
        safety_task = _fetch_safety_report(token_address, chain)
        
        dex_data, gmgn_analysis, safety_data = await asyncio.gather(
            dex_task, gmgn_task, safety_task
        )
        
        # Extract token info
        token_info = {}
        if dex_data and "pairs" in dex_data and dex_data["pairs"]:
            pair = dex_data["pairs"][0]
            base_token = pair.get("baseToken", {})
            token_info = {
                "name": base_token.get("name"),
                "symbol": base_token.get("symbol"),
                "address": base_token.get("address"),
                "price": float(pair.get("priceUsd", 0) or 0),
                "volume_24h": float(pair.get("volume", {}).get("h24", 0) or 0),
                "liquidity": float(pair.get("liquidity", {}).get("usd", 0) or 0),
                "market_cap": float(pair.get("marketCap", 0) or pair.get("fdv", 0) or 0),
                "price_change_24h": float(pair.get("priceChange", {}).get("h24", 0) or 0),
            }
        elif gmgn_analysis and gmgn_analysis.get("token_stats"):
            ts = gmgn_analysis["token_stats"]
            token_info = {
                "name": ts.get("name"),
                "symbol": ts.get("symbol"),
                "address": token_address,
                "price": ts.get("price"),
                "volume_24h": ts.get("volume_24h"),
                "liquidity": ts.get("liquidity"),
                "market_cap": ts.get("market_cap"),
                "price_change_24h": ts.get("price_change_24h"),
            }
        
        # Social data (optional)
        social_data = None
        if request.include_social:
            try:
                from services.twitter_api_v2 import fetch_token_tweets
                social = await fetch_token_tweets(
                    token_symbol=token_info.get("symbol"),
                    token_name=token_info.get("name"),
                    token_address=token_address,
                    max_tweets=10,
                    query_type="Latest"
                )
                social_data = social
            except Exception as e:
                logger.warning(f"Social data fetch failed: {str(e)}")
        
        # ═══════════════════════════════════════════════════════════════
        # PHASE 2: Prediction
        # ═══════════════════════════════════════════════════════════════
        logger.section("PHASE 2: PREDICTION")
        
        prediction = await _run_prediction(dex_data, gmgn_analysis, safety_data, chain)
        
        # ═══════════════════════════════════════════════════════════════
        # Build Response
        # ═══════════════════════════════════════════════════════
        logger.section("SCAN COMPLETE")
        
        # Determine data status
        data_status = {
            "dex": "success" if dex_data else "failed",
            "gmgn": "success" if gmgn_analysis and gmgn_analysis.get("token_stats") else "no_data",
            "safety": "success" if safety_data.get("overall_risk_score", 50) < 100 else "failed",
            "social": "success" if social_data and social_data.get("tweets") else "no_data",
        }
        
        result = ScanResult(
            token_address=token_address,
            chain=chain,
            token=token_info,
            safety=safety_data,
            social=social_data,
            prediction=prediction,
            data_status=data_status
        )
        
        # Cache the result
        token_data_cache.set(cache_key, result, ttl=120)
        
        logger.success("Scan complete", 
                   action=prediction.get("action"),
                   confidence=prediction.get("confidence"),
                   risk_score=safety_data.get("overall_risk_score"))
        
        return result
        
    except Exception as e:
        logger.error(f"Token scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Token scan failed: {str(e)}")


@router.get("/status/{token_address}")
async def get_scan_status(token_address: str, chain: str = "sol"):
    """Check if token has been scanned recently."""
    cache_key = f"scan:{chain}:{token_address}"
    cached = token_data_cache.get(cache_key)
    if cached:
        return {"status": "cached", "token_address": token_address}
    return {"status": "not_scanned", "token_address": token_address}