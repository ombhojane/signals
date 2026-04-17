"""
Shared agent utilities — LLM factory, invocation helper, response envelopes.

The legacy `services/crewat.py` module returns a dict envelope:
    {"agent_type": str, "analysis": dict | None, "status": "success"|"error", ...}

The new agents in this package return a typed `AgentOutcome` dataclass whose
`score`, `confidence`, and `red_flags` fields are what the scoring module
(Step 7) and the orchestrator consume directly. `to_legacy_envelope` converts
an `AgentOutcome` back to the dict shape for routers and callers that still
read the old format.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple, Type, TypeVar

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from core.logging import logger

load_dotenv()

MODEL_NAME = "gemma-4-31b-it"
_GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

T = TypeVar("T", bound=BaseModel)


def make_llm(
    temperature: float,
    model: str = MODEL_NAME,
) -> ChatGoogleGenerativeAI:
    """Build a Gemini 2.5 Flash LLM with the given temperature."""
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        google_api_key=_GOOGLE_API_KEY,
    )


async def invoke_structured(
    llm: ChatGoogleGenerativeAI,
    schema: Type[T],
    prompt: str,
) -> T:
    """Call Gemini with a Pydantic schema; return a validated model or raise."""
    structured = llm.with_structured_output(schema)
    result = await structured.ainvoke([HumanMessage(content=prompt)])
    if not isinstance(result, schema):
        result = schema.model_validate(result)
    return result


# ---------------------------------------------------------------------------
# Typed agent outcomes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ScoredResponse:
    """Normalized score extracted from any agent's Pydantic response."""

    score: float  # [0,1] — higher = better (market/social) or safer (rug)
    confidence: float  # [0,1] — agent's self-reported confidence
    red_flags: Tuple[str, ...]  # structured concerns

    def __post_init__(self) -> None:
        # Defensive clamping — schema should already enforce, but trust-but-verify.
        object.__setattr__(self, "score", max(0.0, min(1.0, self.score)))
        object.__setattr__(self, "confidence", max(0.0, min(1.0, self.confidence)))


@dataclass(frozen=True)
class AgentOutcome:
    """Result of a single agent run.

    `status` mirrors the legacy envelope's status field so conversions are lossless.
    On success, `scored` and `raw` are populated. On error, `error` is set and
    `scored` defaults to a neutral (0.5) low-confidence response so the scoring
    module still has something to combine.
    """

    agent_type: str
    status: str  # "success" | "error"
    scored: ScoredResponse
    raw: Optional[Dict[str, Any]] = None  # Pydantic model_dump if available
    error: Optional[str] = None


def empty_outcome(agent_type: str, reason: str = "no data") -> AgentOutcome:
    """Neutral outcome for when the agent was skipped (no FactBook data)."""
    return AgentOutcome(
        agent_type=agent_type,
        status="error",
        scored=ScoredResponse(score=0.5, confidence=0.0, red_flags=(reason,)),
        raw=None,
        error=reason,
    )


def outcome_from_pydantic(
    agent_type: str,
    model: BaseModel,
    score: float,
    confidence: float,
    red_flags: Tuple[str, ...],
) -> AgentOutcome:
    """Build a successful AgentOutcome from a validated Pydantic response."""
    return AgentOutcome(
        agent_type=agent_type,
        status="success",
        scored=ScoredResponse(score=score, confidence=confidence, red_flags=red_flags),
        raw=model.model_dump(),
        error=None,
    )


def to_legacy_envelope(outcome: AgentOutcome) -> Dict[str, Any]:
    """Convert an AgentOutcome to the legacy dict shape used by existing routers.

    Shape:
      {
        "agent_type": str,
        "analysis": dict | None,
        "status": "success" | "error",
        "parsed": bool,
        "score": float,       # NEW — normalized
        "confidence": float,  # NEW — normalized
        "red_flags": list[str], # NEW
        "error": str | None,
      }
    """
    return {
        "agent_type": outcome.agent_type,
        "analysis": outcome.raw,
        "status": outcome.status,
        "parsed": outcome.raw is not None,
        "score": outcome.scored.score,
        "confidence": outcome.scored.confidence,
        "red_flags": list(outcome.scored.red_flags),
        "error": outcome.error,
    }


def log_agent_error(agent_type: str, exc: Exception) -> None:
    """Uniform error log line for all agents."""
    logger.error(f"{agent_type} failed: {exc}")
