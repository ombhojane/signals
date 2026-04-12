"""Domain-specific AI agents that consume FactBook slices and return scored analyses."""

from services.agents.base import (
    AgentOutcome,
    ScoredResponse,
    empty_outcome,
    invoke_structured,
    make_llm,
    outcome_from_pydantic,
    to_legacy_envelope,
)
from services.agents.market import MarketAgent
from services.agents.prediction import PredictionAgent
from services.agents.rug_check import RugCheckAgent
from services.agents.social import SocialAgent

__all__ = [
    "AgentOutcome",
    "ScoredResponse",
    "MarketAgent",
    "RugCheckAgent",
    "SocialAgent",
    "PredictionAgent",
    "empty_outcome",
    "invoke_structured",
    "make_llm",
    "outcome_from_pydantic",
    "to_legacy_envelope",
]
