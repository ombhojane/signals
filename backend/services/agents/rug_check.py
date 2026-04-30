"""Rug Check Agent — analyzes the RugFactBook slice (GMGN + Safety combined)."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Tuple

from core.factbook import RugFactBook
from core.logging import logger
from models.agent_responses import GMGNAnalysisResponse
from services.agents.base import (
    AgentOutcome,
    empty_outcome,
    invoke_structured,
    log_agent_error,
    make_llm,
    outcome_from_pydantic,
)


_AGENT_TYPE = "rug_check_agent"
_TEMPERATURE = 0.2  # low — safety judgments should be stable across runs


class RugCheckAgent:
    """Turns a RugFactBook into a scored safety assessment.

    Consumes the merged GMGN + GoPlus + RugCheck features from the FactBook.
    Outputs a SAFETY score where higher = safer (1.0 = clean, 0.0 = catastrophic)
    so the scoring module can combine all three agent scores in the same direction.
    """

    def __init__(self) -> None:
        self.llm = make_llm(temperature=_TEMPERATURE)

    async def analyze(self, factbook: RugFactBook) -> AgentOutcome:
        if not factbook.has_data:
            return empty_outcome(_AGENT_TYPE, "safety data missing")

        prompt = self._build_prompt(factbook)
        try:
            response: GMGNAnalysisResponse = await invoke_structured(
                self.llm, GMGNAnalysisResponse, prompt
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

        # Safety score: invert rug_risk_score so higher = safer.
        score = response.score
        if score == 0.5:  # default — LLM didn't override
            score = max(0.0, min(1.0, 1.0 - (response.rug_risk_score / 100.0)))

        red_flags: Tuple[str, ...] = tuple(response.red_flags or response.risk_factors or [])

        logger.info(
            f"{_AGENT_TYPE}: safety={score:.2f} conf={response.confidence:.2f} "
            f"rec={response.recommendation} flags={len(red_flags)}"
        )
        return outcome_from_pydantic(
            agent_type=_AGENT_TYPE,
            model=response,
            score=score,
            confidence=response.confidence,
            red_flags=red_flags,
        )

    def _build_prompt(self, fb: RugFactBook) -> str:
        # Split fields into (a) fields with real values and (b) fields the
        # upstream providers failed to supply. The LLM sees both, so it can
        # distinguish "0 holders (bad!)" from "0 holders (unknown, ignore)".
        known, unknown = _split_known_unknown(fb)
        return (
            "You are a smart-contract and on-chain safety auditor specializing in "
            "detecting rug pulls, honeypots, and dilution attacks.\n\n"
            "A deterministic kill-switch has already run — tokens with certain-death "
            "conditions (honeypot, top10 > 90%, liquidity < $1k) never reach you. "
            "Your job is to assess the subtler risk HypeScan using ONLY the known facts below.\n\n"
            "CRITICAL — data completeness rules (read carefully):\n"
            "- Fields listed under UNKNOWN_FIELDS were NOT returned by the upstream providers. "
            "You MUST treat them as 'not verified' (absent evidence), NOT as '0' or 'false'.\n"
            "- Do NOT cite UNKNOWN_FIELDS values as risk factors. Do NOT claim 'liquidity is not locked' "
            "when liquidity_locked is unknown — say 'lock status unverified' instead.\n"
            "- If more than 3 safety-critical fields are unknown, your confidence must be ≤ 0.5.\n"
            "- GoPlus does not support Solana tokens, so Solana tokens will always have more unknowns. "
            "That is a data limitation, not a red flag in itself.\n\n"
            "KNOWN_FACTS (real data from providers):\n"
            f"{json.dumps(known, separators=(',', ':'))}\n\n"
            "UNKNOWN_FIELDS (providers did not supply these — ignore for red flags):\n"
            f"{json.dumps(unknown, separators=(',', ':'))}\n\n"
            "Focus on:\n"
            "1. Holder concentration — top_10_holder_pct between 30-90% is a "
            "concentration concern; > 50% is high risk. Only use if KNOWN.\n"
            "2. Dev wallet — dev_wallet_pct > 10% warrants caution; > 20% is alarming. Only use if KNOWN.\n"
            "3. Liquidity lock — ONLY flag as unlocked if liquidity_locked is explicitly False in KNOWN_FACTS.\n"
            "4. Mint authority — ONLY flag if unbounded_mint_flag is True in KNOWN_FACTS.\n"
            "5. Contract transparency — closed-source contracts deserve caution, if known.\n"
            "6. derived_danger_score is our composite (0=safe, 1=catastrophic); "
            "use it as a prior but form your own judgement from the KNOWN fields only.\n\n"
            "Return a GMGNAnalysisResponse JSON with:\n"
            "- rug_risk_score: integer 0-100 (RISK score; 100 = confirmed scam)\n"
            "- score: float 0.0-1.0 (normalized SAFETY score — higher = safer, NOT risk)\n"
            "- confidence: float 0.0-1.0 (MUST be ≤ 0.5 if > 3 safety-critical fields are unknown)\n"
            "- red_flags: array of concerns cited ONLY from KNOWN_FACTS (empty if none known)\n"
            "- recommendation: SAFE | CAUTION | AVOID\n"
            "- safety_factors, risk_factors, holder_analysis, summary"
        )


def _split_known_unknown(fb: RugFactBook) -> tuple[dict, list[str]]:
    """Separate populated fields from unverified ones.

    A field is 'unknown' if its value is None OR it's a numeric 0 for a field
    that providers are supposed to fill (holder_count, top_10_holder_pct,
    dev_wallet_pct, lock_days_remaining). 'risk_level = UNKNOWN' also counts.

    Derived flags (lp_secure_flag, concentration_flag, unbounded_mint_flag)
    are computed from the underlying values — if the underlying is unknown,
    the derived flag is also unknown and is moved to the UNKNOWN list so the
    agent cannot cite it as a red flag.
    """
    raw = asdict(fb)
    numeric_fillables = {
        "holder_count",
        "top_10_holder_pct",
        "dev_wallet_pct",
        "lock_days_remaining",
        "liquidity_usd",
    }
    # Derived flags depend on specific underlying fields.
    # If the underlying is unknown, the derived flag is also unreliable.
    derived_deps = {
        "lp_secure_flag": fb.liquidity_locked is None,
        "concentration_flag": fb.top_10_holder_pct == 0,
        "unbounded_mint_flag": fb.is_mintable is None or fb.ownership_renounced is None,
    }

    known: dict = {}
    unknown: list[str] = []
    for k, v in raw.items():
        if k == "has_data":
            continue
        if v is None:
            unknown.append(k)
            continue
        if k == "risk_level" and v == "UNKNOWN":
            unknown.append(k)
            continue
        if k in numeric_fillables and v == 0:
            unknown.append(k)
            continue
        # Default overall_risk_score of 50 is also "unknown prior"
        if k == "overall_risk_score" and v == 50:
            unknown.append(k)
            continue
        # smart_money_flow default "neutral" is uninformative — mark unknown
        if k == "smart_money_flow" and v == "neutral":
            unknown.append(k)
            continue
        # Derived flag with unknown underlying data — move to UNKNOWN
        if k in derived_deps and derived_deps[k]:
            unknown.append(k)
            continue
        known[k] = v
    return known, unknown
