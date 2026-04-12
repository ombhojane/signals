"""Market Signals Agent — analyzes the MarketFactBook slice."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Tuple

from core.factbook import MarketFactBook
from core.logging import logger
from models.agent_responses import MarketAnalysisResponse
from services.agents.base import (
    AgentOutcome,
    empty_outcome,
    invoke_structured,
    log_agent_error,
    make_llm,
    outcome_from_pydantic,
)


_AGENT_TYPE = "market_agent"
_TEMPERATURE = 0.3


class MarketAgent:
    """Turns a MarketFactBook into a scored market assessment.

    The agent never sees raw DEX JSON — only the pre-extracted FactBook, which
    is ~25 numeric features plus symbol/name. This eliminates the class of
    hallucinations where the LLM misreads a field in a messy JSON blob.
    """

    def __init__(self) -> None:
        self.llm = make_llm(temperature=_TEMPERATURE)

    async def analyze(self, factbook: MarketFactBook) -> AgentOutcome:
        if not factbook.has_data:
            return empty_outcome(_AGENT_TYPE, "market data missing")

        prompt = self._build_prompt(factbook)
        try:
            response: MarketAnalysisResponse = await invoke_structured(
                self.llm, MarketAnalysisResponse, prompt
            )
        except Exception as exc:  # noqa: BLE001 — we surface SDK/validation errors
            log_agent_error(_AGENT_TYPE, exc)
            return AgentOutcome(
                agent_type=_AGENT_TYPE,
                status="error",
                scored=empty_outcome(_AGENT_TYPE).scored,
                raw=None,
                error=str(exc),
            )

        # Trust the LLM's declared score/confidence; fall back to deriving from
        # market_health (1-10) if the model forgot to fill `score`.
        score = response.score
        if score == 0.5:  # default — LLM probably didn't provide one
            score = max(0.0, min(1.0, (response.market_health - 1) / 9.0))

        red_flags: Tuple[str, ...] = tuple(response.red_flags or [])

        logger.info(
            f"{_AGENT_TYPE}: score={score:.2f} conf={response.confidence:.2f} "
            f"flags={len(red_flags)}"
        )
        return outcome_from_pydantic(
            agent_type=_AGENT_TYPE,
            model=response,
            score=score,
            confidence=response.confidence,
            red_flags=red_flags,
        )

    def _build_prompt(self, fb: MarketFactBook) -> str:
        """Build a compact, grounded prompt from the MarketFactBook."""
        facts = asdict(fb)
        # Drop identity + raw timestamp — they're not decision-relevant for this agent.
        for k in ("pair_created_at_ms", "pair_address"):
            facts.pop(k, None)

        return (
            "You are a cryptocurrency market-microstructure analyst.\n"
            "Analyze the following numeric market facts for one token and return a "
            "structured assessment. Ground every claim in the numbers provided — do not "
            "invent values. If a field is 0 or missing, treat it as 'unknown', not 'zero'.\n\n"
            "MARKET FACTS (pre-extracted, no raw JSON):\n"
            f"{json.dumps(facts, separators=(',', ':'))}\n\n"
            "Cover:\n"
            "1. Volume health — is volume commensurate with liquidity? "
            "(vol_to_liq_ratio > 10 is suspicious wash-trading; < 0.1 is dead.)\n"
            "2. Trade flow — is buy_sell_ratio balanced or one-sided?\n"
            "3. Age and velocity — is a very young token showing unnatural trade count?\n"
            "4. Price behaviour — volatility_24h coherent with liquidity depth?\n"
            "5. Overall risk factors you can cite from the facts.\n\n"
            "Return a MarketAnalysisResponse JSON with:\n"
            "- market_health: integer 1-10 (10 = excellent health)\n"
            "- score: float 0.0-1.0 (your normalized health score; higher = better)\n"
            "- confidence: float 0.0-1.0 (how confident are you in your score, given data completeness)\n"
            "- red_flags: array of specific concerns you identified (empty if none)\n"
            "- summary, volume_analysis, liquidity_analysis, trading_patterns, "
            "risk_assessment, recommendations"
        )
