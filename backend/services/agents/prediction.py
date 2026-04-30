"""Prediction Agent — synthesizes the three worker scores into a final action.

In v1, this is a single-shot prediction that reads the three agent outcomes
plus the kill-switch result. Step 8 will upgrade it to self-consistency
(N=3 samples, majority vote) and few-shot retrieval from the RL experience
buffer. Until then we keep the surface small and deterministic.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple

from core.factbook import TokenFactBook
from core.killswitch import KillSwitchResult
from core.logging import logger
from models.agent_responses import PredictionResponse
from services.agents.base import (
    AgentOutcome,
    empty_outcome,
    invoke_structured,
    log_agent_error,
    make_llm,
    outcome_from_pydantic,
)


_AGENT_TYPE = "predictor"
_TEMPERATURE = 0.1  # lowest temp — decisions should be stable


class PredictionAgent:
    """Synthesize worker outcomes + FactBook Signals into a trading action."""

    def __init__(self) -> None:
        self.llm = make_llm(temperature=_TEMPERATURE)

    async def predict(
        self,
        *,
        factbook: TokenFactBook,
        killswitch: KillSwitchResult,
        market: AgentOutcome,
        rug: AgentOutcome,
        social: AgentOutcome,
        signal_vector: Optional[Dict[str, Any]] = None,
        few_shot_examples: Optional[List[Dict[str, Any]]] = None,
    ) -> AgentOutcome:
        """Run the prediction.

        - If kill-switch triggered, return a deterministic AVOID without calling
          the LLM (cost + latency savings, no hallucination risk).
        - Otherwise, build a prompt from the agent outcomes + factbook summary
          and let Gemini make the call.
        """
        if killswitch.triggered:
            return self._killswitch_outcome(killswitch)

        prompt = self._build_prompt(
            factbook=factbook,
            market=market,
            rug=rug,
            social=social,
            signal_vector=signal_vector,
            few_shot_examples=few_shot_examples or [],
        )

        try:
            response: PredictionResponse = await invoke_structured(
                self.llm, PredictionResponse, prompt
            )
        except Exception as exc:  # noqa: BLE001
            log_agent_error(_AGENT_TYPE, exc)
            return AgentOutcome(
                agent_type=_AGENT_TYPE,
                status="error",
                scored=empty_outcome(_AGENT_TYPE).scored,
                raw=None,
                error=str(exc),
            )

        # Prediction "score" maps action to [0,1] for downstream consumers.
        # STRONG_BUY=1.0, BUY=0.75, HOLD=0.5, SELL=0.25, STRONG_SELL=0.0.
        score = _action_to_score(response.action_signal.value)
        confidence = response.confidence_level / 100.0

        logger.info(
            f"{_AGENT_TYPE}: action={response.action_signal} conf={confidence:.2f} "
            f"risk={response.risk_level}"
        )
        return outcome_from_pydantic(
            agent_type=_AGENT_TYPE,
            model=response,
            score=score,
            confidence=confidence,
            red_flags=tuple(response.key_factors or []),
        )

    # ------------------------------------------------------------------ helpers

    def _killswitch_outcome(self, killswitch: KillSwitchResult) -> AgentOutcome:
        """Return a deterministic AVOID outcome without calling the LLM."""
        primary = killswitch.primary
        rule = primary.rule if primary else "KILL_SWITCH"
        message = primary.message if primary else "Kill-switch triggered"
        # Construct a PredictionResponse directly so downstream consumers still
        # see the same shape.
        response = PredictionResponse(
            action_signal="STRONG_SELL",  # type: ignore[arg-type]
            confidence_level=99,
            short_term_prediction=f"Kill-switch: {rule}. Avoid entirely.",
            medium_term_prediction="Do not engage.",
            key_factors=[r.rule for r in killswitch.reasons],
            risk_level="HIGH",  # type: ignore[arg-type]
            summary=message,
        )
        return outcome_from_pydantic(
            agent_type=_AGENT_TYPE,
            model=response,
            score=0.0,
            confidence=0.99,
            red_flags=tuple(r.rule for r in killswitch.reasons),
        )

    def _build_prompt(
        self,
        *,
        factbook: TokenFactBook,
        market: AgentOutcome,
        rug: AgentOutcome,
        social: AgentOutcome,
        signal_vector: Optional[Dict[str, Any]],
        few_shot_examples: List[Dict[str, Any]],
    ) -> str:
        summary_facts = factbook.to_llm_dict()
        worker_scores = {
            "market": {
                "score": round(market.scored.score, 3),
                "confidence": round(market.scored.confidence, 3),
                "red_flags": list(market.scored.red_flags),
            },
            "rug_safety": {
                "score": round(rug.scored.score, 3),
                "confidence": round(rug.scored.confidence, 3),
                "red_flags": list(rug.scored.red_flags),
            },
            "social": {
                "score": round(social.scored.score, 3),
                "confidence": round(social.scored.confidence, 3),
                "red_flags": list(social.scored.red_flags),
            },
        }

        few_shot_block = ""
        if few_shot_examples:
            few_shot_block = (
                "\nSIMILAR PAST PREDICTIONS AND THEIR ACTUAL OUTCOMES "
                "(learn from these — weight patterns that were correct):\n"
                f"{json.dumps(few_shot_examples, separators=(',', ':'))}\n"
            )

        signal_block = ""
        if signal_vector is not None:
            hint = signal_vector.get("action_hint", "HOLD")
            overall = signal_vector.get("overall", 0.5)
            conf = signal_vector.get("confidence", 0.0)
            signal_block = (
                "\nSCORING MODULE SIGNAL VECTOR (calibrated weighted aggregate):\n"
                f"{json.dumps(signal_vector, separators=(',', ':'))}\n"
                f"\nDETERMINISTIC BASELINE HINT: {hint} "
                f"(overall={overall:.2f}, confidence={conf:.2f})\n"
                "The action_hint is a deterministic mapping from the weighted score vector. "
                "You may AGREE with it (matching its output) or OVERRIDE it, but if you override, "
                "your reasoning must cite specific evidence from the worker outputs that the "
                "deterministic scoring couldn't see.\n"
            )

        return (
            "You are the final decision layer for a multi-agent crypto analysis "
            "system. Three specialist agents have already analyzed market, safety, "
            "and social Signals. Your job is to synthesize their outputs into a "
            "single trading recommendation.\n\n"
            "DECISION RULES (strict — check in order, first match wins):\n"
            "- Rug safety score < 0.30 AND rug confidence ≥ 0.50 → SELL or STRONG_SELL.\n"
            "- Rug safety score < 0.50 AND rug confidence ≥ 0.60 AND market score < 0.50 → HOLD or SELL.\n"
            "- INSUFFICIENT DATA RULE: if rug confidence < 0.50 OR any score is in "
            "[0.40, 0.60] with its confidence < 0.50 → HOLD. You do not have enough "
            "verified safety data to recommend BUY or SELL. Do NOT cite 'unverified' "
            "fields as evidence of risk in this case.\n"
            "- BUY requires: rug safety ≥ 0.60 AND rug confidence ≥ 0.50 AND at least "
            "one other agent (market or social) with score ≥ 0.60.\n"
            "- STRONG_BUY requires: all three scores ≥ 0.60 AND all confidences ≥ 0.60.\n"
            "- If no BUY/SELL condition fires, default to HOLD.\n"
            "- Your red_flags must only cite KNOWN evidence from the worker outputs, "
            "not derived flags whose underlying data was unverified.\n\n"
            "TOKEN FACTS (compact):\n"
            f"{json.dumps(summary_facts, separators=(',', ':'))}\n\n"
            "WORKER AGENT OUTPUTS:\n"
            f"{json.dumps(worker_scores, separators=(',', ':'))}\n"
            f"{signal_block}"
            f"{few_shot_block}\n"
            "Return a PredictionResponse JSON with:\n"
            "- action_signal: STRONG_BUY | BUY | HOLD | SELL | STRONG_SELL\n"
            "- confidence_level: integer 0-100\n"
            "- short_term_prediction, medium_term_prediction, summary\n"
            "- key_factors: array listing the top drivers of your decision\n"
            "- risk_level: LOW | MEDIUM | HIGH"
        )


def _action_to_score(action: str) -> float:
    """Map action signal to [0,1]."""
    mapping = {
        "STRONG_BUY": 1.0,
        "BUY": 0.75,
        "HOLD": 0.5,
        "SELL": 0.25,
        "STRONG_SELL": 0.0,
    }
    return mapping.get(action, 0.5)
