"""
OrchestratorAgent - Intelligent analysis orchestration with ReAct pattern.

This implements a lightweight ReAct (Reason + Act) orchestrator that:
1. Plans which data sources to query based on chain
2. Validates data before sending to AI agents  
3. Adjusts confidence/weights based on data availability
4. Synthesizes insights by analyzing cross-data patterns
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from core.logging import logger
from core.data_validator import (
    validate_dex_data,
    validate_gmgn_data,
    validate_twitter_data,
    validate_safety_data,
    DataValidationResult
)
from core.parallel import gather_with_results, run_parallel_agents, make_async
from core.constants import get_chain_id

from services.dex_api import get_dex_data
from services.token_data_service import get_token_analysis
from services.token_safety_service import get_safety_report
from services.twitter_api_v2 import fetch_token_tweets
from services.crewat import token_agents


class DataSource(str, Enum):
    """Available data sources."""
    DEX = "dex"
    GMGN = "gmgn"        # Now powered by DexScreener + GeckoTerminal
    SAFETY = "safety"     # GoPlus + RugCheck
    TWITTER = "twitter"
    MORALIS = "moralis"


@dataclass
class ChainCapabilities:
    """What services are available for each chain."""
    supports_dex: bool = True
    supports_gmgn_stats: bool = True
    supports_gmgn_trenches: bool = False  # Only sol/bsc
    supports_moralis: bool = False  # Only base
    supports_twitter: bool = True


# Chain-specific capabilities
CHAIN_CAPABILITIES: Dict[str, ChainCapabilities] = {
    "sol": ChainCapabilities(supports_gmgn_trenches=True),
    "solana": ChainCapabilities(supports_gmgn_trenches=True),
    "bsc": ChainCapabilities(supports_gmgn_trenches=True),
    "base": ChainCapabilities(supports_moralis=True, supports_gmgn_trenches=False),
    "eth": ChainCapabilities(supports_gmgn_trenches=False),
}


@dataclass
class AnalysisPlan:
    """Execution plan for token analysis."""
    token_address: str
    chain: str
    capabilities: ChainCapabilities
    data_sources: List[DataSource] = field(default_factory=list)
    reasoning: str = ""
    
    def __post_init__(self):
        """Auto-generate reasoning based on chain capabilities."""
        self.reasoning = f"Analyzing {self.chain.upper()} token. "

        # Always include DEX
        self.data_sources.append(DataSource.DEX)
        self.reasoning += "Will fetch DEX data. "

        # Include token data (replaces GMGN, available for all chains)
        if self.capabilities.supports_gmgn_stats:
            self.data_sources.append(DataSource.GMGN)
            self.reasoning += "Will fetch token data (DexScreener+GeckoTerminal). "

        # Always include safety check
        self.data_sources.append(DataSource.SAFETY)
        self.reasoning += "Will run safety analysis (GoPlus+RugCheck). "

        # Include Moralis for Base chain
        if self.capabilities.supports_moralis:
            self.data_sources.append(DataSource.MORALIS)
            self.reasoning += "Will fetch Moralis data (Base chain). "

        # Always try Twitter
        self.data_sources.append(DataSource.TWITTER)
        self.reasoning += "Will attempt Twitter search."


@dataclass
class AnalysisResult:
    """Result of the orchestrated analysis."""
    token_address: str
    chain: str
    plan: AnalysisPlan
    
    # Raw data
    dex_data: Optional[Dict[str, Any]] = None
    gmgn_data: Optional[Dict[str, Any]] = None
    safety_data: Optional[Dict[str, Any]] = None
    twitter_data: Optional[Dict[str, Any]] = None
    
    # Validation results
    validations: Dict[str, DataValidationResult] = field(default_factory=dict)
    
    # AI analysis results
    ai_results: Dict[str, Any] = field(default_factory=dict)
    
    # Synthesis
    synthesis: Optional[Dict[str, Any]] = None
    confidence_adjustment: float = 1.0
    warnings: List[str] = field(default_factory=list)


class OrchestratorAgent:
    """
    Intelligent orchestrator that plans and executes token analysis.
    
    Implements a simplified ReAct pattern:
    1. THINK: Analyze the request and create a plan
    2. ACT: Execute data fetching in parallel
    3. OBSERVE: Validate results and adjust plan
    4. ACT: Run AI analysis on valid data only
    5. REFLECT: Synthesize insights and adjust confidence
    """
    
    def __init__(self):
        self.async_get_dex_data = make_async(get_dex_data)
    
    def think(self, token_address: str, chain: str) -> AnalysisPlan:
        """
        THINK: Create an analysis plan based on chain capabilities.
        """
        logger.info(f"Planning analysis for {chain} token...")
        
        # Get chain capabilities
        capabilities = CHAIN_CAPABILITIES.get(
            chain.lower(), 
            ChainCapabilities()  # Default: basic capabilities
        )
        
        plan = AnalysisPlan(
            token_address=token_address,
            chain=chain,
            capabilities=capabilities
        )
        
        logger.info(f"Plan: {plan.reasoning}")
        return plan
    
    async def act_fetch_data(
        self,
        plan: AnalysisPlan,
        pair_address: Optional[str] = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """
        ACT: Fetch data from planned sources in parallel.
        Returns (dex_data, gmgn_data, safety_data, twitter_data).
        """
        logger.section("PHASE 1: DATA FETCHING")

        dex_chain = get_chain_id(plan.chain, "dex")
        dex_address = pair_address if pair_address else plan.token_address

        # Build tasks based on plan
        data_tasks = {}

        if DataSource.DEX in plan.data_sources:
            data_tasks["dex"] = self.async_get_dex_data(dex_chain, dex_address)

        if DataSource.GMGN in plan.data_sources:
            data_tasks["gmgn"] = get_token_analysis(plan.token_address, plan.chain)

        if DataSource.SAFETY in plan.data_sources:
            data_tasks["safety"] = get_safety_report(plan.token_address, plan.chain)

        # Execute in parallel
        results = await gather_with_results(data_tasks, timeout=30.0)

        # Extract results
        dex_data = results.get("dex", {})
        dex_data = dex_data.data if hasattr(dex_data, 'data') and dex_data.success else {}

        gmgn_data = results.get("gmgn", {})
        gmgn_data = gmgn_data.data if hasattr(gmgn_data, 'data') and gmgn_data.success else {}

        safety_data = results.get("safety", {})
        safety_raw = safety_data.data if hasattr(safety_data, 'data') and safety_data.success else None
        safety_dict = safety_raw.to_dict() if hasattr(safety_raw, 'to_dict') else (safety_raw or {})

        # Get token info for Twitter search
        token_symbol = None
        token_name = None

        if dex_data and 'pairs' in dex_data and dex_data['pairs']:
            pair = dex_data['pairs'][0]
            token_symbol = pair.get('baseToken', {}).get('symbol')
            token_name = pair.get('baseToken', {}).get('name')

        # Fallback: try to get symbol from token_data_service
        if not token_symbol and gmgn_data:
            token_stats = gmgn_data.get('token_stats')
            if token_stats:
                token_symbol = token_stats.get('symbol')
                token_name = token_stats.get('name')

        # Fetch Twitter data
        twitter_data = {}
        if DataSource.TWITTER in plan.data_sources and token_symbol:
            try:
                twitter_data = await fetch_token_tweets(
                    token_symbol=token_symbol,
                    token_name=token_name,
                    token_address=plan.token_address,
                    max_tweets=20
                )
            except Exception as e:
                logger.warning(f"Twitter fetch failed: {str(e)}")
                twitter_data = {"error": str(e), "tweets": []}

        return dex_data, gmgn_data, safety_dict, twitter_data
    
    def observe(
        self,
        dex_data: Dict[str, Any],
        gmgn_data: Dict[str, Any],
        safety_data: Dict[str, Any],
        twitter_data: Dict[str, Any]
    ) -> Tuple[Dict[str, DataValidationResult], List[str]]:
        """
        OBSERVE: Validate data and identify issues.
        """
        logger.section("PHASE 2: DATA VALIDATION")

        validations = {
            "dex": validate_dex_data(dex_data),
            "gmgn": validate_gmgn_data(gmgn_data),
            "safety": validate_safety_data(safety_data),
            "twitter": validate_twitter_data(twitter_data)
        }

        warnings = []
        for source, result in validations.items():
            if result.is_valid:
                logger.success(f"{source.upper()} data validated")
            else:
                msg = f"{source.upper()}: {result.reason}"
                warnings.append(msg)
                logger.warning(f"Skipping {source}: {result.reason}")

        return validations, warnings
    
    async def act_analyze(
        self,
        dex_data: Dict[str, Any],
        gmgn_data: Dict[str, Any],
        safety_data: Dict[str, Any],
        twitter_data: Dict[str, Any],
        validations: Dict[str, DataValidationResult]
    ) -> Dict[str, Any]:
        """
        ACT: Run AI analysis only on validated data.
        """
        logger.section("PHASE 3: AI ANALYSIS")

        agent_tasks = {}

        if validations["dex"].is_valid:
            agent_tasks["market_analysis"] = token_agents.market_signals(dex_data)

        # Combine gmgn + safety data for the safety analysis agent
        combined_gmgn = gmgn_data.copy() if gmgn_data else {}
        if safety_data:
            combined_gmgn["safety_report"] = safety_data
        if validations.get("gmgn", DataValidationResult(is_valid=False, source="gmgn")).is_valid or \
           validations.get("safety", DataValidationResult(is_valid=False, source="safety")).is_valid:
            agent_tasks["gmgn_analysis"] = token_agents.gmgn_signals(combined_gmgn)

        if validations["twitter"].is_valid:
            agent_tasks["social_analysis"] = token_agents.analyze_social_data(twitter_data)

        if not agent_tasks:
            logger.warning("No valid data for AI analysis")
            return {}

        # Run in parallel
        return await run_parallel_agents(agent_tasks, timeout=60.0)
    
    def reflect(
        self,
        ai_results: Dict[str, Any],
        safety_data: Dict[str, Any],
        validations: Dict[str, DataValidationResult],
        warnings: List[str]
    ) -> Tuple[float, Dict[str, Any]]:
        """
        REFLECT: Synthesize insights and adjust confidence.

        Key insight: Analyze cross-data patterns
        - High volume on DEX but 0 Twitter mentions = Suspicious
        - High rug risk + low Twitter engagement = RED FLAG
        """
        logger.section("PHASE 4: SYNTHESIS")

        # Calculate confidence adjustment based on data availability
        valid_sources = sum(1 for v in validations.values() if v.is_valid)
        total_sources = len(validations)

        # Base confidence: proportion of valid sources
        confidence_adjustment = valid_sources / total_sources if total_sources > 0 else 0.5

        synthesis = {
            "data_coverage": f"{valid_sources}/{total_sources} sources valid",
            "confidence_adjustment": confidence_adjustment,
            "cross_analysis": []
        }

        # Pattern 1: High trading activity but no social presence
        if validations["dex"].is_valid and not validations["twitter"].is_valid:
            synthesis["cross_analysis"].append({
                "pattern": "NO_SOCIAL_PRESENCE",
                "severity": "warning",
                "insight": "Token has no detectable social media activity. Could indicate organic growth or manipulation."
            })

        # Pattern 2: High rug risk from safety report
        if safety_data:
            rug_risk = safety_data.get("overall_risk_score", 0)
            risk_level = safety_data.get("risk_level", "UNKNOWN")
            if rug_risk > 70 or risk_level in ("HIGH", "CRITICAL"):
                synthesis["cross_analysis"].append({
                    "pattern": "HIGH_RUG_RISK",
                    "severity": "critical",
                    "insight": f"Safety risk score is {rug_risk}/100 ({risk_level}). Exercise extreme caution."
                })
                confidence_adjustment *= 0.5

            if safety_data.get("is_honeypot") is True:
                synthesis["cross_analysis"].append({
                    "pattern": "HONEYPOT_DETECTED",
                    "severity": "critical",
                    "insight": "Token detected as a honeypot. DO NOT BUY."
                })
                confidence_adjustment *= 0.1

        # Pattern 3: AI analysis cross-check
        gmgn = ai_results.get("gmgn_analysis", {}).get("analysis", {})
        if isinstance(gmgn, dict) and gmgn.get("rug_risk_score", 0) > 70:
            synthesis["cross_analysis"].append({
                "pattern": "AI_HIGH_RISK",
                "severity": "critical",
                "insight": f"AI rug analysis score: {gmgn.get('rug_risk_score')}/100."
            })
            confidence_adjustment *= 0.6

        logger.info(f"Synthesis complete. Confidence adjustment: {confidence_adjustment:.2f}")

        return confidence_adjustment, synthesis
    
    async def run(
        self,
        token_address: str,
        chain: str,
        pair_address: Optional[str] = None
    ) -> AnalysisResult:
        """
        Execute the full ReAct analysis loop.

        1. THINK -> Create plan
        2. ACT -> Fetch data
        3. OBSERVE -> Validate
        4. ACT -> AI analysis
        5. REFLECT -> Synthesize
        """
        logger.section("ORCHESTRATOR: REACT ANALYSIS")

        # 1. THINK
        plan = self.think(token_address, chain)

        # 2. ACT (fetch)
        dex_data, gmgn_data, safety_data, twitter_data = await self.act_fetch_data(plan, pair_address)

        # 3. OBSERVE
        validations, warnings = self.observe(dex_data, gmgn_data, safety_data, twitter_data)

        # 4. ACT (analyze)
        ai_results = await self.act_analyze(dex_data, gmgn_data, safety_data, twitter_data, validations)

        # 5. REFLECT
        confidence_adjustment, synthesis = self.reflect(ai_results, safety_data, validations, warnings)

        # Run final prediction with all data
        logger.section("PHASE 5: PREDICTION")
        combined_data = {
            "market_data": dex_data,
            "gmgn_data": gmgn_data,
            "safety_data": safety_data,
            "social_data": twitter_data,
            "ai_analysis": ai_results,
            "data_coverage": synthesis.get("data_coverage"),
            "confidence_adjustment": confidence_adjustment
        }

        prediction = await token_agents.predict_token_movement(combined_data)
        ai_results["prediction"] = prediction

        return AnalysisResult(
            token_address=token_address,
            chain=chain,
            plan=plan,
            dex_data=dex_data,
            gmgn_data=gmgn_data,
            safety_data=safety_data,
            twitter_data=twitter_data,
            validations=validations,
            ai_results=ai_results,
            synthesis=synthesis,
            confidence_adjustment=confidence_adjustment,
            warnings=warnings
        )


# Global orchestrator instance
orchestrator = OrchestratorAgent()
