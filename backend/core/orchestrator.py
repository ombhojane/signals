"""
Orchestrator Agent — the planner that drives the enhanced AI pipeline.

Flow:
    1. THINK         — plan data sources based on chain capabilities
    2. ACT (fetch)   — fetch DEX + GMGN + Safety + Twitter in parallel
    3. STAGE 0       — build TokenFactBook from raw data (pure, no LLM)
    4. STAGE 1       — deterministic kill-switch (no LLM, short-circuits on hard Signals)
    5. STAGE 2       — three FactBook-aware worker agents in parallel
                       (Market / RugCheck / Social)
    6. STAGE 3       — scoring module placeholder (Step 7 plugs in here)
    7. STAGE 4       — prediction agent synthesizes everything
    8. return AnalysisResult (same shape as before + new `factbook` /
       `killswitch` / `signal_vector` fields)

This rewrite removes the magic-number `reflect()` logic — cross-pattern
checks now live in the scoring module (Step 7) and the Prediction agent's
prompt rules. Reflection stays as a *data* synthesis summary, not a
hard-coded penalty.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from core.constants import get_chain_id
from core.data_validator import (
    DataValidationResult,
    validate_dex_data,
    validate_gmgn_data,
    validate_safety_data,
    validate_twitter_data,
)
from core.factbook import TokenFactBook, build_token_factbook
from core.killswitch import KillSwitchResult, check_killswitch
from core.logging import logger
from core.parallel import gather_with_results, make_async, run_parallel_agents
from core.scoring import SignalVector, compute_signal_vector
from services.agents import (
    AgentOutcome,
    MarketAgent,
    PredictionAgent,
    RugCheckAgent,
    SocialAgent,
    empty_outcome,
    to_legacy_envelope,
)
from services.dex_api import get_dex_data
from services.social_preprocessor import preprocess_twitter_payload
from services.token_data_service import get_token_analysis
from services.token_safety_service import get_safety_report
from services.twitter_api_v2 import fetch_token_tweets


# ---------------------------------------------------------------------------
# Planning primitives (preserved from legacy orchestrator)
# ---------------------------------------------------------------------------


class DataSource(str, Enum):
    DEX = "dex"
    GMGN = "gmgn"
    SAFETY = "safety"
    TWITTER = "twitter"
    MORALIS = "moralis"


@dataclass
class ChainCapabilities:
    supports_dex: bool = True
    supports_gmgn_stats: bool = True
    supports_gmgn_trenches: bool = False
    supports_moralis: bool = False
    supports_twitter: bool = True


CHAIN_CAPABILITIES: Dict[str, ChainCapabilities] = {
    "sol": ChainCapabilities(supports_gmgn_trenches=True),
    "solana": ChainCapabilities(supports_gmgn_trenches=True),
    "bsc": ChainCapabilities(supports_gmgn_trenches=True),
    "base": ChainCapabilities(supports_moralis=True),
    "eth": ChainCapabilities(),
}


@dataclass
class AnalysisPlan:
    token_address: str
    chain: str
    capabilities: ChainCapabilities
    data_sources: List[DataSource] = field(default_factory=list)
    reasoning: str = ""

    def __post_init__(self) -> None:
        self.reasoning = f"Analyzing {self.chain.upper()} token. "
        self.data_sources.append(DataSource.DEX)
        self.reasoning += "Will fetch DEX data. "
        if self.capabilities.supports_gmgn_stats:
            self.data_sources.append(DataSource.GMGN)
            self.reasoning += "Will fetch token stats (DexScreener+GeckoTerminal). "
        self.data_sources.append(DataSource.SAFETY)
        self.reasoning += "Will run safety analysis (GoPlus+RugCheck). "
        if self.capabilities.supports_moralis:
            self.data_sources.append(DataSource.MORALIS)
            self.reasoning += "Will fetch Moralis data (Base chain). "
        if self.capabilities.supports_twitter:
            self.data_sources.append(DataSource.TWITTER)
            self.reasoning += "Will attempt Twitter search."


@dataclass
class AnalysisResult:
    """Top-level result of an orchestrated token analysis.

    Legacy fields (preserved for backwards compatibility with run.py and routers):
        token_address, chain, plan, dex_data, gmgn_data, safety_data,
        twitter_data, validations, ai_results, synthesis, confidence_adjustment,
        warnings

    New fields (v1 enhancement):
        factbook          — the immutable TokenFactBook all agents used
        killswitch        — KillSwitchResult (triggered or not)
        signal_vector     — placeholder for Step 7 scoring module
    """

    token_address: str
    chain: str
    plan: AnalysisPlan

    dex_data: Optional[Dict[str, Any]] = None
    gmgn_data: Optional[Dict[str, Any]] = None
    safety_data: Optional[Dict[str, Any]] = None
    twitter_data: Optional[Dict[str, Any]] = None

    validations: Dict[str, DataValidationResult] = field(default_factory=dict)
    ai_results: Dict[str, Any] = field(default_factory=dict)
    synthesis: Optional[Dict[str, Any]] = None
    confidence_adjustment: float = 1.0
    warnings: List[str] = field(default_factory=list)

    # New
    factbook: Optional[TokenFactBook] = None
    killswitch: Optional[KillSwitchResult] = None
    signal_vector: Optional[SignalVector] = None


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class OrchestratorAgent:
    """Plans and executes the enhanced AI pipeline for a single token."""

    def __init__(self) -> None:
        self._async_dex = make_async(get_dex_data)
        self.market_agent = MarketAgent()
        self.rug_check_agent = RugCheckAgent()
        self.social_agent = SocialAgent()
        self.prediction_agent = PredictionAgent()

    # ------------------------------------------------------------------ think

    def think(self, token_address: str, chain: str) -> AnalysisPlan:
        logger.info(f"Planning analysis for {chain} token...")
        capabilities = CHAIN_CAPABILITIES.get(chain.lower(), ChainCapabilities())
        plan = AnalysisPlan(
            token_address=token_address, chain=chain, capabilities=capabilities
        )
        logger.info(f"Plan: {plan.reasoning}")
        return plan

    # ------------------------------------------------------------------ fetch

    async def fetch_data(
        self,
        plan: AnalysisPlan,
        pair_address: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
        """Fetch all data sources in parallel. Returns raw blobs."""
        logger.section("PHASE 1: DATA FETCHING")

        dex_chain = get_chain_id(plan.chain, "dex")
        dex_address = pair_address if pair_address else plan.token_address

        tasks: Dict[str, Any] = {}
        if DataSource.DEX in plan.data_sources:
            tasks["dex"] = self._async_dex(dex_chain, dex_address)
        if DataSource.GMGN in plan.data_sources:
            tasks["gmgn"] = get_token_analysis(plan.token_address, plan.chain)
        if DataSource.SAFETY in plan.data_sources:
            tasks["safety"] = get_safety_report(plan.token_address, plan.chain)

        results = await gather_with_results(tasks, timeout=30.0)

        def _extract(key: str) -> Any:
            value = results.get(key)
            if value is None:
                return {}
            return value.data if getattr(value, "success", False) else {}

        dex_data = _extract("dex")
        gmgn_data = _extract("gmgn")

        safety_raw = _extract("safety")
        safety_dict = (
            safety_raw.to_dict() if hasattr(safety_raw, "to_dict") else (safety_raw or {})
        )

        # Fetch Twitter using whatever symbol/name we can derive from DEX or GMGN.
        token_symbol, token_name = self._derive_token_identity(dex_data, gmgn_data)
        twitter_data: Dict[str, Any] = {}
        if DataSource.TWITTER in plan.data_sources and token_symbol:
            try:
                twitter_data = await fetch_token_tweets(
                    token_symbol=token_symbol,
                    token_name=token_name,
                    token_address=plan.token_address,
                    max_tweets=20,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(f"Twitter fetch failed: {exc}")
                twitter_data = {"error": str(exc), "tweets": [], "status": "error"}

        return dex_data, gmgn_data, safety_dict, twitter_data

    @staticmethod
    def _derive_token_identity(
        dex_data: Dict[str, Any], gmgn_data: Dict[str, Any]
    ) -> Tuple[Optional[str], Optional[str]]:
        pairs = (dex_data or {}).get("pairs") or []
        if pairs:
            base = pairs[0].get("baseToken") or {}
            symbol = base.get("symbol")
            name = base.get("name")
            if symbol:
                return symbol, name
        stats = ((gmgn_data or {}).get("token_stats")) or {}
        return stats.get("symbol"), stats.get("name")

    # ----------------------------------------------------------------- workers

    async def run_workers(
        self, factbook: TokenFactBook, killswitch_triggered: bool
    ) -> Tuple[AgentOutcome, AgentOutcome, AgentOutcome]:
        """Run the three worker agents in parallel.

        If the kill-switch already triggered, we skip the workers entirely and
        return neutral outcomes. That's a cost-saving short-circuit: any data
        we could extract from a kill-switched token will be ignored anyway.
        """
        if killswitch_triggered:
            logger.section("PHASE 3: AI ANALYSIS (SKIPPED — kill-switch)")
            return (
                empty_outcome("market_agent", "killswitch triggered"),
                empty_outcome("rug_check_agent", "killswitch triggered"),
                empty_outcome("social_agent", "killswitch triggered"),
            )

        logger.section("PHASE 3: AI ANALYSIS")

        tasks: Dict[str, Any] = {}
        if factbook.market.has_data:
            tasks["market"] = self.market_agent.analyze(factbook.market)
        if factbook.rug.has_data:
            tasks["rug"] = self.rug_check_agent.analyze(factbook.rug)
        if factbook.social.has_data:
            tasks["social"] = self.social_agent.analyze(factbook.social)

        results = await run_parallel_agents(tasks, timeout=60.0)

        market = results.get("market") or empty_outcome(
            "market_agent", "market data missing"
        )
        rug = results.get("rug") or empty_outcome(
            "rug_check_agent", "safety data missing"
        )
        social = results.get("social") or empty_outcome(
            "social_agent", "social data missing"
        )

        return market, rug, social

    # ------------------------------------------------------------------ synth

    def _synthesize(
        self,
        *,
        factbook: TokenFactBook,
        killswitch: KillSwitchResult,
        market: AgentOutcome,
        rug: AgentOutcome,
        social: AgentOutcome,
        prediction: AgentOutcome,
    ) -> Tuple[Dict[str, Any], float, List[str]]:
        """Build a synthesis dict and a confidence adjustment from agent outcomes.

        Replaces the legacy magic-number penalties in `reflect()`. The new
        synthesis is *informational*, not punitive — calibration is the
        scoring module's job (Step 7).
        """
        logger.section("PHASE 4: SYNTHESIS")

        warnings: List[str] = []
        cross_analysis: List[Dict[str, Any]] = []

        # Aggregate the structured red_flags from every agent into the cross_analysis
        # list so consumers can see everything that was flagged in one place.
        for outcome in (market, rug, social):
            for flag in outcome.scored.red_flags:
                cross_analysis.append(
                    {
                        "source": outcome.agent_type,
                        "flag": flag,
                    }
                )

        # Kill-switch contributes its own reasons.
        if killswitch.triggered:
            for reason in killswitch.reasons:
                cross_analysis.append(
                    {
                        "source": "killswitch",
                        "pattern": reason.rule,
                        "severity": reason.severity.value,
                        "message": reason.message,
                    }
                )
                warnings.append(f"KILLSWITCH {reason.rule}: {reason.message}")

        # Confidence adjustment — no more magic numbers. It is simply the
        # average of the three worker confidences, optionally floored by the
        # kill-switch. The scoring module in Step 7 will replace this with a
        # calibrated weight.
        confidences = [market.scored.confidence, rug.scored.confidence, social.scored.confidence]
        avg_conf = sum(confidences) / 3
        if killswitch.triggered:
            avg_conf = max(avg_conf, 0.95)  # kill-switch decisions are high-confidence

        valid_sources = sum(
            1
            for fb_has_data in (
                factbook.market.has_data,
                factbook.rug.has_data,
                factbook.social.has_data,
            )
            if fb_has_data
        )

        synthesis = {
            "data_coverage": f"{valid_sources}/3 sources available",
            "confidence_adjustment": round(avg_conf, 3),
            "cross_analysis": cross_analysis,
            "killswitch_triggered": killswitch.triggered,
            "killswitch_action": killswitch.action,
            "worker_scores": {
                "market": round(market.scored.score, 3),
                "rug_safety": round(rug.scored.score, 3),
                "social": round(social.scored.score, 3),
            },
        }

        logger.info(
            f"Synthesis: coverage={valid_sources}/3, avg_conf={avg_conf:.2f}, "
            f"killswitch={killswitch.triggered}"
        )
        return synthesis, avg_conf, warnings

    # --------------------------------------------------------------- validate

    def _legacy_validations(
        self,
        dex_data: Dict[str, Any],
        gmgn_data: Dict[str, Any],
        safety_data: Dict[str, Any],
        twitter_data: Dict[str, Any],
    ) -> Dict[str, DataValidationResult]:
        """Run legacy validators for backwards-compatible AnalysisResult.validations."""
        return {
            "dex": validate_dex_data(dex_data),
            "gmgn": validate_gmgn_data(gmgn_data),
            "safety": validate_safety_data(safety_data),
            "twitter": validate_twitter_data(twitter_data),
        }

    # -------------------------------------------------------------------- run

    async def run(
        self,
        token_address: str,
        chain: str,
        pair_address: Optional[str] = None,
    ) -> AnalysisResult:
        """Execute the full enhanced pipeline for one token."""
        logger.section("ORCHESTRATOR: ENHANCED ANALYSIS")

        # 1. THINK
        plan = self.think(token_address, chain)

        # 2. ACT — fetch raw data
        dex_data, gmgn_data, safety_data, twitter_data = await self.fetch_data(
            plan, pair_address
        )

        return await self._run_from_raw(
            plan=plan,
            token_address=token_address,
            chain=chain,
            dex_data=dex_data,
            gmgn_data=gmgn_data,
            safety_data=safety_data,
            twitter_data=twitter_data,
        )

    async def run_from_snapshot(
        self,
        *,
        token_address: str,
        chain: str,
        dex_data: Dict[str, Any],
        gmgn_data: Dict[str, Any],
        safety_data: Dict[str, Any],
        twitter_data: Dict[str, Any],
    ) -> AnalysisResult:
        """Execute the pipeline from pre-fetched raw data (no network).

        Used by the eval harness for deterministic, free, reproducible runs.
        """
        logger.section("ORCHESTRATOR: SNAPSHOT REPLAY")
        plan = self.think(token_address, chain)
        return await self._run_from_raw(
            plan=plan,
            token_address=token_address,
            chain=chain,
            dex_data=dex_data,
            gmgn_data=gmgn_data,
            safety_data=safety_data,
            twitter_data=twitter_data,
        )

    async def _run_from_raw(
        self,
        *,
        plan: AnalysisPlan,
        token_address: str,
        chain: str,
        dex_data: Dict[str, Any],
        gmgn_data: Dict[str, Any],
        safety_data: Dict[str, Any],
        twitter_data: Dict[str, Any],
    ) -> AnalysisResult:
        """Run stages 2.5 through 5 on pre-fetched raw data."""
        # Legacy validations (for backwards-compatible AnalysisResult shape).
        validations = self._legacy_validations(
            dex_data, gmgn_data, safety_data, twitter_data
        )

        # 2.5. Preprocess Twitter before the FactBook sees it.
        logger.section("PHASE 2: PREPROCESSING")
        clean_twitter = preprocess_twitter_payload(twitter_data)

        # Stage 0: FactBook
        factbook = build_token_factbook(
            token_address=token_address,
            chain=chain,
            dex_data=dex_data,
            gmgn_data=gmgn_data,
            safety_data=safety_data,
            twitter_data=clean_twitter,
        )

        # Stage 1: Kill-switch
        killswitch = check_killswitch(factbook)
        if killswitch.triggered:
            logger.warning(
                f"KILL-SWITCH TRIGGERED: {killswitch.primary.rule if killswitch.primary else 'unknown'}"
            )

        # Stage 2: Workers
        market_outcome, rug_outcome, social_outcome = await self.run_workers(
            factbook, killswitch.triggered
        )

        # Stage 3: Scoring module — weighted soft-voting ensemble.
        # Uses the confirmed priors [market 0.35, rug 0.40, social 0.25]
        # (or the calibrator-learned weights from data/scoring_weights.json).
        logger.section("PHASE 4: SCORING")
        signal_vector = compute_signal_vector(
            market=market_outcome,
            rug=rug_outcome,
            social=social_outcome,
            killswitch=killswitch,
        )
        logger.info(
            f"SignalVector: overall={signal_vector.overall:.2f} "
            f"conf={signal_vector.confidence:.2f} hint={signal_vector.action_hint} "
            f"warnings={len(signal_vector.warnings)}"
        )

        # Stage 4: Prediction — the LLM sees the signal vector plus the raw
        # worker outputs and makes the final call. The scoring module's
        # `action_hint` is an explainable deterministic baseline; the LLM
        # may override it based on the full context.
        logger.section("PHASE 5: PREDICTION")
        prediction_outcome = await self.prediction_agent.predict(
            factbook=factbook,
            killswitch=killswitch,
            market=market_outcome,
            rug=rug_outcome,
            social=social_outcome,
            signal_vector=signal_vector.to_dict(),
        )

        # Synthesis
        synthesis, confidence_adjustment, warnings = self._synthesize(
            factbook=factbook,
            killswitch=killswitch,
            market=market_outcome,
            rug=rug_outcome,
            social=social_outcome,
            prediction=prediction_outcome,
        )

        # Build legacy ai_results dict from new AgentOutcomes.
        ai_results: Dict[str, Any] = {
            "market_analysis": to_legacy_envelope(market_outcome),
            "gmgn_analysis": to_legacy_envelope(rug_outcome),
            "social_analysis": to_legacy_envelope(social_outcome),
            "prediction": to_legacy_envelope(prediction_outcome),
        }

        return AnalysisResult(
            token_address=token_address,
            chain=chain,
            plan=plan,
            dex_data=dex_data,
            gmgn_data=gmgn_data,
            safety_data=safety_data,
            twitter_data=clean_twitter,  # store the cleaned version
            validations=validations,
            ai_results=ai_results,
            synthesis=synthesis,
            confidence_adjustment=confidence_adjustment,
            warnings=warnings,
            factbook=factbook,
            killswitch=killswitch,
            signal_vector=signal_vector,
        )


# Global orchestrator instance
orchestrator = OrchestratorAgent()
