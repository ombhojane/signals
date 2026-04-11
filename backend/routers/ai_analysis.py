"""
AI Analysis Router - Endpoints for AI-powered token analysis with parallel execution.
"""

import asyncio
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict, Any

from services.dex_api import get_dex_data
from services.token_data_service import get_token_analysis
from services.token_safety_service import get_safety_report
from services.crewat import token_agents
from services.twitter_api_v2 import fetch_token_tweets
from models.schemas import AISignalsResponse, RiskAssessmentResponse, HistoricalResponse
from core.constants import get_chain_id
from core.logging import logger
from core.parallel import gather_with_results, run_parallel_agents, make_async


router = APIRouter(tags=["AI Analysis"])


# Wrap sync function for async execution
async_get_dex_data = make_async(get_dex_data)


@router.post("/analyze-token-price")
async def analyze_token_price(token_pair_address: str):
    """Analyze token price using AI agents."""
    from routers.dex import get_token_price

    price_data = get_token_price(token_pair_address)
    if "error" in price_data:
        raise HTTPException(status_code=400, detail=price_data["error"])
    analysis = await token_agents.market_signals(price_data)
    return analysis


@router.get("/ai-signals", response_model=AISignalsResponse)
async def get_ai_signals(coinAddress: str, pairAddress: str):
    """Get AI signals data from real analysis."""
    try:
        dex_chain = get_chain_id("sol", "dex")
        dex_data = await async_get_dex_data(dex_chain, pairAddress)
        safety_report = await get_safety_report(coinAddress, "sol")
        safety = safety_report.to_dict()

        # Run market analysis
        market_result = await token_agents.market_signals(dex_data)
        market = market_result.get("analysis", {}) if isinstance(market_result, dict) else {}

        # Derive signal strength from market health
        health = market.get("market_health", 5) if isinstance(market, dict) else 5
        if health >= 8:
            strength, pattern = "Strong Buy", "Accumulation"
        elif health >= 6:
            strength, pattern = "Buy", "Early Trend"
        elif health >= 4:
            strength, pattern = "Neutral", "Consolidation"
        elif health >= 2:
            strength, pattern = "Sell", "Distribution"
        else:
            strength, pattern = "Strong Sell", "Breakdown"

        risk_score = safety.get("overall_risk_score", 50)
        holder_concentration = safety.get("top_10_holder_pct", 0)

        return {
            "strength": strength,
            "confidence": max(0, min(100, health * 10)),
            "pattern": pattern,
            "patternPhase": f"Risk {safety.get('risk_level', 'UNKNOWN')}",
            "prediction": f"Risk Score: {risk_score}/100",
            "forecast": "Live Analysis",
            "featureEngineering": [
                {"name": "Market Health", "weight": 30, "color": "green" if health >= 6 else "yellow", "value": health * 10},
                {"name": "Safety Score", "weight": 35, "color": "green" if risk_score < 30 else "red", "value": max(0, 100 - risk_score)},
                {"name": "Liquidity Depth", "weight": 35, "color": "blue", "value": min(100, int((safety.get("liquidity_usd", 0) / 100000) * 100)) if safety.get("liquidity_usd") else 50},
            ],
            "blockchainRecognition": [
                {"name": "Honeypot Check", "timeFrame": "Real-time", "riskColor": "red" if safety.get("is_honeypot") else "green", "riskLevel": "DANGER" if safety.get("is_honeypot") else "Safe", "riskPercentage": 100 if safety.get("is_honeypot") else 0},
                {"name": "Holder Concentration", "timeFrame": "Current", "riskColor": "red" if holder_concentration > 50 else "green", "riskLevel": f"Top 10: {holder_concentration:.0f}%", "riskPercentage": int(holder_concentration)},
            ],
            "alertThresholds": [
                {"name": f"Ownership {'Renounced' if safety.get('ownership_renounced') else 'Active'}", "status": "Safe" if safety.get("ownership_renounced") else "Warning", "color": "green" if safety.get("ownership_renounced") else "yellow", "bgColor": "green" if safety.get("ownership_renounced") else "yellow"},
                {"name": f"Liquidity {'Locked' if safety.get('liquidity_locked') else 'Unlocked'}", "status": "Locked" if safety.get("liquidity_locked") else "Warning", "color": "green" if safety.get("liquidity_locked") else "red", "bgColor": "green" if safety.get("liquidity_locked") else "red"},
                {"name": f"Mintable: {'Yes' if safety.get('is_mintable') else 'No'}", "status": "Warning" if safety.get("is_mintable") else "Safe", "color": "yellow" if safety.get("is_mintable") else "green", "bgColor": "yellow" if safety.get("is_mintable") else "green"},
            ],
        }
    except Exception as e:
        logger.error(f"AI signals failed: {str(e)}, returning defaults")
        return {
            "strength": "Unknown", "confidence": 0, "pattern": "Error", "patternPhase": "N/A",
            "prediction": "Analysis failed", "forecast": "Retry",
            "featureEngineering": [], "blockchainRecognition": [], "alertThresholds": [],
        }


@router.get("/risk-assessment", response_model=RiskAssessmentResponse)
async def get_risk_assessment(coinAddress: str, pairAddress: str):
    """Get risk assessment from GoPlus + RugCheck."""
    try:
        import uuid
        safety_report = await get_safety_report(coinAddress, "sol")
        s = safety_report.to_dict()

        risk_score = s.get("overall_risk_score", 50)
        risk_level = s.get("risk_level", "MEDIUM")

        # Map risk level to display strings
        risk_labels = {"LOW": "Low Risk", "MEDIUM": "Medium Risk", "HIGH": "High Risk", "CRITICAL": "Critical Risk"}
        risk_scores = {"LOW": "2/10", "MEDIUM": "5/10", "HIGH": "7.5/10", "CRITICAL": "9.5/10"}

        ownership = s.get("ownership_renounced")
        mintable = s.get("is_mintable")
        liq_locked = s.get("liquidity_locked")
        concentration = s.get("top_10_holder_pct", 0)

        return {
            "sectionId": str(uuid.uuid4()),
            "overallRiskScore": risk_labels.get(risk_level, "Unknown"),
            "riskLevel": risk_scores.get(risk_level, f"{risk_score / 10:.1f}/10"),
            "smartContractSafetyPercentage": max(0, 100 - risk_score),
            "smartContractStatus": "Open Source" if s.get("is_open_source") else "Not Verified",
            "liquidityLockStatus": "Locked" if liq_locked else ("Unlocked" if liq_locked is False else "Unknown"),
            "liquidityLockRemainingDays": s.get("lock_remaining_days", 0),
            "ownershipStatus": "Renounced" if ownership else ("Active" if ownership is False else "Unknown"),
            "ownershipStatusDescription": "Contract ownership has been renounced" if ownership else "Ownership not renounced - owner can modify contract",
            "mintFunctionStatus": "Present" if mintable else ("Not Present" if mintable is False else "Unknown"),
            "mintFunctionDescription": "Contract contains mint function - potential supply inflation risk" if mintable else "No mint function found",
            "transferRestrictions": "None Detected" if not s.get("is_honeypot") else "HONEYPOT DETECTED",
            "transferRestrictionsDescription": "No transfer restrictions detected" if not s.get("is_honeypot") else "WARNING: Token may be a honeypot - cannot sell",
            "liquidityRisk": "Low" if liq_locked else "High",
            "liquidityRiskPercentage": 20 if liq_locked else 80,
            "concentrationRisk": "High" if concentration > 50 else ("Medium" if concentration > 25 else "Low"),
            "concentrationRiskPercentage": int(concentration),
            "smartContractRisk": risk_level.capitalize() if risk_level != "CRITICAL" else "Critical",
            "smartContractRiskPercentage": risk_score,
        }
    except Exception as e:
        logger.error(f"Risk assessment failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Risk assessment error: {str(e)}")


@router.get("/historical", response_model=HistoricalResponse)
async def get_historical_data(coinAddress: str, pairAddress: str):
    """Get historical data from OHLCV analysis."""
    try:
        from services.token_data_service import token_data_service

        ohlcv = await token_data_service.get_token_ohlcv(coinAddress, "sol", "hour")

        if not ohlcv:
            # Return zeros instead of mock data when no data available
            return {
                "roi": 0, "pumpPatterns": 0, "averagePumpReturn": 0, "recoveryTime": 0,
                "activeAlerts": 0, "highPriority": 0, "triggeredToday": 0,
                "triggeredChange": 0, "successRate": 0, "responseTime": 0.0,
            }

        # Calculate metrics from OHLCV
        closes = [bar["close"] for bar in ohlcv]
        if len(closes) >= 2:
            roi = int(((closes[-1] - closes[0]) / closes[0]) * 100) if closes[0] > 0 else 0
        else:
            roi = 0

        # Detect pump patterns (>20% rise in 4 consecutive hours)
        pump_count = 0
        pump_returns = []
        for i in range(len(closes) - 4):
            window_return = ((closes[i + 4] - closes[i]) / closes[i]) * 100 if closes[i] > 0 else 0
            if window_return > 20:
                pump_count += 1
                pump_returns.append(window_return)

        avg_pump = int(sum(pump_returns) / len(pump_returns)) if pump_returns else 0

        # Volatility-based alerts
        if len(closes) >= 2:
            changes = [abs((closes[i] - closes[i - 1]) / closes[i - 1]) * 100 for i in range(1, len(closes)) if closes[i - 1] > 0]
            high_vol_count = sum(1 for c in changes if c > 5)
        else:
            high_vol_count = 0

        return {
            "roi": roi,
            "pumpPatterns": pump_count,
            "averagePumpReturn": avg_pump,
            "recoveryTime": min(len(closes), 48),
            "activeAlerts": high_vol_count,
            "highPriority": sum(1 for c in pump_returns if c > 50) if pump_returns else 0,
            "triggeredToday": min(high_vol_count, 24),
            "triggeredChange": pump_count,
            "successRate": int((pump_count / max(len(closes) // 4, 1)) * 100) if pump_count else 0,
            "responseTime": 0.5,
        }
    except Exception as e:
        logger.error(f"Historical data failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Historical data error: {str(e)}")


@router.post("/ai-analysis/comprehensive")
async def comprehensive_ai_analysis(
    token_address: str,
    chain: str = "sol",
    pair_address: Optional[str] = None
):
    """
    Get comprehensive AI analysis from all agents including Twitter data.
    
    Uses parallel execution for:
    1. Data fetching (DEX, GMGN, Twitter) - runs in parallel
    2. AI analysis (market, gmgn, social) - runs in parallel
    3. Final prediction - runs after all analysis complete
    """
    logger.section("COMPREHENSIVE TOKEN ANALYSIS")
    logger.info(f"Analyzing token", address=token_address[:16] + "...", chain=chain)
    
    try:
        # Get chain ID for DexScreener
        dex_chain = get_chain_id(chain, "dex")
        dex_address = pair_address if pair_address else token_address
        
        # ═══════════════════════════════════════════════════════════════
        # PHASE 1: Parallel Data Fetching
        # ═══════════════════════════════════════════════════════════════
        logger.section("PHASE 1: DATA FETCHING")
        
        data_tasks = {
            "dex": async_get_dex_data(dex_chain, dex_address),
            "gmgn": get_token_analysis(token_address, chain),
        }
        
        data_results = await gather_with_results(data_tasks, timeout=30.0)
        
        # Extract results (with fallbacks for failures)
        dex_data = data_results["dex"].data if data_results["dex"].success else {}
        gmgn_data = data_results["gmgn"].data if data_results["gmgn"].success else {}
        
        # Extract token info for Twitter search
        token_symbol = None
        token_name = None
        
        if dex_data and 'pairs' in dex_data and dex_data['pairs']:
            pair = dex_data['pairs'][0]
            token_symbol = pair.get('baseToken', {}).get('symbol')
            token_name = pair.get('baseToken', {}).get('name')
            logger.success(f"Token identified", symbol=token_symbol, name=token_name)
        
        if not token_symbol and gmgn_data:
            token_stats = gmgn_data.get('token_stats') or (gmgn_data.get('analysis') or {}).get('token_stats')
            if token_stats:
                token_symbol = token_stats.get('symbol')
                token_name = token_stats.get('name')
        
        # Fetch tweets (can run after we have token info)
        logger.info("Fetching Twitter data...")
        try:
            social_data = await fetch_token_tweets(
                token_symbol=token_symbol,
                token_name=token_name,
                token_address=token_address,
                max_tweets=20,
                query_type="Latest"
            )
            logger.success("Twitter data fetched", tweets=social_data.get('total_tweets', 0))
        except Exception as e:
            logger.warning(f"Twitter fetch failed: {str(e)}")
            social_data = {"tweets": [], "total_tweets": 0, "error": str(e)}
        
        # ═══════════════════════════════════════════════════════════════
        # PHASE 2: Parallel AI Analysis (with data validation)
        # ═══════════════════════════════════════════════════════════════
        logger.section("PHASE 2: AI ANALYSIS")
        
        from core.data_validator import validate_dex_data, validate_gmgn_data, validate_twitter_data
        
        # Validate data before sending to AI
        dex_valid = validate_dex_data(dex_data)
        gmgn_valid = validate_gmgn_data(gmgn_data)
        twitter_valid = validate_twitter_data(social_data)
        
        # Only run analysis if data is valid
        agent_tasks = {}
        skipped_agents = []
        
        if dex_valid.is_valid:
            agent_tasks["market_analysis"] = token_agents.market_signals(dex_data)
        else:
            skipped_agents.append(f"market ({dex_valid.reason})")
            logger.warning(f"Skipping market analysis: {dex_valid.reason}")
        
        if gmgn_valid.is_valid:
            agent_tasks["gmgn_analysis"] = token_agents.gmgn_signals(gmgn_data)
        else:
            skipped_agents.append(f"gmgn ({gmgn_valid.reason})")
            logger.warning(f"Skipping GMGN analysis: {gmgn_valid.reason}")
        
        if twitter_valid.is_valid:
            agent_tasks["social_analysis"] = token_agents.analyze_social_data(social_data)
        else:
            skipped_agents.append(f"social ({twitter_valid.reason})")
            logger.warning(f"Skipping social analysis: {twitter_valid.reason}")
        
        if agent_tasks:
            agent_results = await run_parallel_agents(agent_tasks, timeout=60.0)
        else:
            agent_results = {}
            logger.warning("No valid data available for AI analysis")
        
        # ═══════════════════════════════════════════════════════════════
        # PHASE 3: Final Prediction
        # ═══════════════════════════════════════════════════════════════
        logger.section("PHASE 3: PREDICTION")
        
        # Combine all data for prediction
        combined_data = {
            "market_data": dex_data,
            "gmgn_data": gmgn_data,
            "social_data": social_data
        }
        
        logger.info("Running prediction model...")
        prediction = await token_agents.predict_token_movement(combined_data)
        logger.success("Prediction complete")
        
        # Build response
        logger.section("ANALYSIS COMPLETE")
        
        # Log data source status
        logger.info("Data sources", 
                   dex="✓" if dex_data else "✗",
                   gmgn="✓" if gmgn_data else "✗",
                   twitter="✓" if social_data.get('tweets') else "✗")
        
        return {
            "status": "success",
            "token_address": token_address,
            "chain": chain,
            "data_status": {
                "dex": "success" if data_results["dex"].success else "failed",
                "gmgn": "success" if data_results["gmgn"].success else "failed",
                "twitter": "success" if social_data.get('tweets') else "failed"
            },
            "ai_analysis": {
                "market_analysis": agent_results.get("market_analysis", {"status": "skipped"}),
                "gmgn_analysis": agent_results.get("gmgn_analysis", {"status": "skipped"}),
                "social_analysis": agent_results.get("social_analysis", {"status": "skipped"}),
                "prediction": prediction
            },
            "raw_data": {
                "dex": dex_data,
                "gmgn": gmgn_data,
                "twitter": social_data
            }
        }
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in AI analysis: {str(e)}")


@router.post("/ai-analysis/dex")
async def analyze_dex_with_ai(chain_id: str, pair_address: str):
    """Analyze DEX data with AI agent."""
    logger.info("DEX Analysis", chain=chain_id, pair=pair_address[:16] + "...")
    
    try:
        dex_data = await async_get_dex_data(chain_id, pair_address)
        analysis = await token_agents.market_signals(dex_data)
        
        logger.success("DEX analysis complete")
        return {
            "status": "success",
            "analysis": analysis,
            "raw_data": dex_data
        }
    except Exception as e:
        logger.error(f"DEX analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in DEX AI analysis: {str(e)}")


@router.post("/ai-analysis/gmgn")
async def analyze_gmgn_with_ai(token_address: str, chain: str = "sol"):
    """Analyze token safety data with AI agent."""
    logger.info("Token Safety Analysis", token=token_address[:16] + "...", chain=chain)

    try:
        import asyncio as _asyncio
        token_data, safety_report = await _asyncio.gather(
            get_token_analysis(token_address, chain),
            get_safety_report(token_address, chain),
        )

        combined = token_data.copy() if isinstance(token_data, dict) else {}
        combined["safety_report"] = safety_report.to_dict() if hasattr(safety_report, 'to_dict') else {}

        analysis = await token_agents.gmgn_signals(combined)

        logger.success("Token safety analysis complete")
        return {
            "status": "success",
            "analysis": analysis,
            "raw_data": combined
        }
    except Exception as e:
        logger.error(f"Token safety analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in token safety AI analysis: {str(e)}")


@router.post("/ai-analysis/social")
async def analyze_social_with_ai(
    token_symbol: Optional[str] = None,
    token_name: Optional[str] = None,
    token_address: Optional[str] = None,
):
    """Analyze social sentiment with AI agent using real Twitter data."""
    logger.info("Social Analysis", symbol=token_symbol or "N/A")

    try:
        if token_symbol or token_name or token_address:
            social_data = await fetch_token_tweets(
                token_symbol=token_symbol,
                token_name=token_name,
                token_address=token_address,
                max_tweets=20,
            )
        else:
            return {"status": "error", "error": "Provide at least one of: token_symbol, token_name, token_address"}

        analysis = await token_agents.analyze_social_data(social_data)

        logger.success("Social analysis complete")
        return {
            "status": "success",
            "analysis": analysis,
            "raw_data": social_data
        }
    except Exception as e:
        logger.error(f"Social analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in social AI analysis: {str(e)}")


@router.get("/system/circuit-breakers")
async def get_circuit_breaker_status():
    """Get status of all circuit breakers for monitoring."""
    from core.resilience import get_all_circuit_states
    return get_all_circuit_states()


@router.post("/ai-analysis/orchestrated")
async def orchestrated_analysis(
    token_address: str,
    chain: str = "sol",
    pair_address: Optional[str] = None
):
    """
    Advanced AI analysis using the ReAct orchestrator.
    
    This endpoint uses intelligent orchestration:
    - Chain-aware service routing
    - Data validation before AI analysis
    - Cross-data pattern detection
    - Confidence adjustment based on data availability
    """
    from core.orchestrator import orchestrator
    
    logger.section("ORCHESTRATED ANALYSIS")
    logger.info(f"Starting orchestrated analysis", token=token_address[:16] + "...", chain=chain)
    
    try:
        result = await orchestrator.run(
            token_address=token_address,
            chain=chain,
            pair_address=pair_address
        )
        
        logger.success("Orchestrated analysis complete")
        
        return {
            "status": "success",
            "token_address": result.token_address,
            "chain": result.chain,
            "plan": {
                "reasoning": result.plan.reasoning,
                "data_sources": [s.value for s in result.plan.data_sources]
            },
            "data_status": {
                source: {
                    "valid": val.is_valid,
                    "reason": val.reason if not val.is_valid else None
                }
                for source, val in result.validations.items()
            },
            "synthesis": result.synthesis,
            "confidence_adjustment": result.confidence_adjustment,
            "warnings": result.warnings,
            "ai_analysis": result.ai_results,
            "raw_data": {
                "dex": result.dex_data,
                "gmgn": result.gmgn_data,
                "safety": result.safety_data,
                "twitter": result.twitter_data
            }
        }
    except Exception as e:
        logger.error(f"Orchestrated analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error in orchestrated analysis: {str(e)}")


@router.post("/rl-agent/analyze")
async def rl_agent_analyze(token_address: str, chain: str = "sol"):
    """
    Run the RL trading agent on a real token.

    Returns the agent's trading decision based on real market data.
    """
    logger.section("RL AGENT ANALYSIS")
    logger.info(f"Analyzing token with RL agent", token=token_address[:16] + "...", chain=chain)

    try:
        from rl_agent.real_market_adapter import RealMarketAdapter
        from rl_agent.agentic_trader import AgenticTrader

        adapter = RealMarketAdapter()
        snapshot = await adapter.get_snapshot(token_address, chain)

        agent = AgenticTrader(initial_balance=100.0, verbose=False)
        decision = await agent.think(snapshot)

        logger.success("RL agent analysis complete", action=decision.action, confidence=decision.confidence)

        return {
            "status": "success",
            "token": {
                "name": snapshot.name,
                "symbol": snapshot.symbol,
                "address": snapshot.address,
                "chain": snapshot.chain,
                "price": snapshot.price,
                "volume_24h": snapshot.volume_24h,
                "market_cap": snapshot.market_cap,
                "liquidity": snapshot.liquidity,
                "rug_score": snapshot.rug_score,
                "holder_count": snapshot.holder_count,
                "rsi": snapshot.rsi,
                "sentiment_score": snapshot.sentiment_score,
            },
            "decision": {
                "action": decision.action,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "risk_assessment": decision.risk_assessment,
                "price_target": decision.price_target,
                "stop_loss": decision.stop_loss,
            }
        }
    except Exception as e:
        logger.error(f"RL agent analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RL agent error: {str(e)}")

