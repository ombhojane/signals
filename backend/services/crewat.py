"""
Token Analysis Agents — Gemini 2.5 Flash agents with native structured output.

Step 1 of the v1 enhancement plan:
- All agents upgraded from gemma-4-31b-it-lite.
- Uses LangChain's `with_structured_output(PydanticModel)` which under the hood
  drives Gemini's native JSON-schema-constrained generation. No more regex
  parsing, no more retry loops — the SDK returns a validated Pydantic object
  or raises.
- Return shape is preserved so existing callers (orchestrator, routers) don't
  need to change in this step. Later steps (4, 7, 8) will split this class
  into dedicated agent modules with FactBook inputs.
"""

import json
import os
from typing import Any, Dict, Optional, Type, TypeVar

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel

from core.logging import logger
from models.agent_responses import (
    GMGNAnalysisResponse,
    MarketAnalysisResponse,
    PredictionResponse,
    SocialAnalysisResponse,
)

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemma-4-31b-it"

T = TypeVar("T", bound=BaseModel)


def _make_llm(temperature: float) -> ChatGoogleGenerativeAI:
    """Build a Gemini 2.5 Flash chat model with the given temperature."""
    return ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=temperature,
        google_api_key=GOOGLE_API_KEY,
    )


# Per-agent LLM instances. Temperatures follow the v1 plan:
# - predictor lowest (decision-making should be stable)
# - social highest (sentiment benefits from a little variety)
_llm_market = _make_llm(temperature=0.3)
_llm_rug = _make_llm(temperature=0.2)
_llm_social = _make_llm(temperature=0.4)
_llm_predictor = _make_llm(temperature=0.1)


def _ok(agent_type: str, validated: BaseModel) -> Dict[str, Any]:
    """Success envelope preserving the legacy return shape."""
    return {
        "agent_type": agent_type,
        "analysis": validated.model_dump(),
        "status": "success",
        "parsed": True,
    }


def _err(agent_type: str, error: Exception) -> Dict[str, Any]:
    """Error envelope preserving the legacy return shape."""
    logger.error(f"{agent_type} error: {str(error)}")
    return {
        "agent_type": agent_type,
        "analysis": None,
        "status": "error",
        "error": str(error),
    }


async def _invoke_structured(
    llm: ChatGoogleGenerativeAI,
    schema: Type[T],
    prompt: str,
) -> T:
    """Invoke Gemini with a Pydantic output schema and return the parsed model.

    Raises on any failure — callers handle.
    """
    structured = llm.with_structured_output(schema)
    result = await structured.ainvoke([HumanMessage(content=prompt)])
    if not isinstance(result, schema):
        # LangChain sometimes returns a dict under older versions — coerce.
        result = schema.model_validate(result)
    return result


class TokenAnalysisAgents:
    """Token analysis agents using Gemini 2.5 Flash with structured outputs.

    Same public API as the previous implementation so callers don't break:
      - market_HypeScan(dex_data)
      - gmgn_HypeScan(gmgn_data)
      - analyze_social_data(social_data) / analyze_social_sentiment(social_data)
      - predict_token_movement(combined_data)

    Each method returns the legacy envelope:
      {"agent_type": str, "analysis": dict | None, "status": "success"|"error", ...}
    """

    def __init__(self) -> None:
        self.llm_analyzer = _llm_market
        self.llm_gmgn = _llm_rug
        self.llm_social = _llm_social
        self.llm_predictor = _llm_predictor

    # ------------------------------------------------------------------ market

    async def market_HypeScan(self, dex_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze DEX/market data and provide structured insights."""
        logger.info("Running market HypeScan analysis...")
        prompt = (
            "As a cryptocurrency data analyst expert, analyze the following DEX/market "
            "data and return a structured assessment.\n\n"
            f"DEX Data:\n{json.dumps(dex_data, separators=(',', ':'))}\n\n"
            "Cover: (1) volume trends & significance, (2) liquidity and market depth, "
            "(3) trading activity patterns, (4) price impact assessment, "
            "(5) market health indicators, (6) risk factors."
        )
        try:
            validated = await _invoke_structured(
                self.llm_analyzer, MarketAnalysisResponse, prompt
            )
            return _ok("dex_analyzer", validated)
        except Exception as e:  # noqa: BLE001 — surface any SDK/validation error
            return _err("dex_analyzer", e)

    # --------------------------------------------------------------- rug check

    async def gmgn_HypeScan(self, gmgn_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze GMGN + safety data for rug detection."""
        logger.info("Running rug-check analysis...")
        prompt = (
            "As a GMGN analysis expert specializing in rug detection and token safety, "
            "analyze this data and return a structured risk report.\n\n"
            f"GMGN + Safety Data:\n{json.dumps(gmgn_data, separators=(',', ':'))}\n\n"
            "Focus on: (1) rug pull risk, (2) holder distribution, (3) creator behavior, "
            "(4) liquidity lock status, (5) trading anomalies, (6) overall safety score. "
            "Your rug_risk_score must be 0 (safe) to 100 (scam)."
        )
        try:
            validated = await _invoke_structured(
                self.llm_gmgn, GMGNAnalysisResponse, prompt
            )
            return _ok("gmgn_analyzer", validated)
        except Exception as e:  # noqa: BLE001
            return _err("gmgn_analyzer", e)

    # ------------------------------------------------------------------ social

    async def analyze_social_data(self, social_data: Dict[str, Any]) -> Dict[str, Any]:
        """Alias retained for backwards compatibility with existing callers."""
        return await self.analyze_social_sentiment(social_data)

    async def analyze_social_sentiment(
        self, social_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze social media sentiment for a token."""
        logger.info("Running social sentiment analysis...")
        prompt = (
            "As a social sentiment analyst, analyze this social-media data for a crypto "
            "token and return a structured sentiment report.\n\n"
            f"Social Data:\n{json.dumps(social_data, separators=(',', ':'))}\n\n"
            "Cover: (1) overall sentiment, (2) community engagement, (3) influencer impact, "
            "(4) hype vs genuine interest, (5) trending patterns, (6) manipulation signs. "
            "sentiment_score and community_health must be 0-100."
        )
        try:
            validated = await _invoke_structured(
                self.llm_social, SocialAnalysisResponse, prompt
            )
            return _ok("social_analyzer", validated)
        except Exception as e:  # noqa: BLE001
            return _err("social_analyzer", e)

    # -------------------------------------------------------------- prediction

    async def predict_token_movement(
        self, combined_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Synthesize all analyses into a final action signal."""
        logger.info("Running prediction model...")
        prompt = (
            "As a cryptocurrency prediction expert, synthesize all available HypeScan "
            "into a single trading recommendation. Weight safety (rug-risk) highest — "
            "an unsafe token is always HOLD or SELL regardless of hype.\n\n"
            f"Combined Analysis Data:\n{json.dumps(combined_data, separators=(',', ':'))}\n\n"
            "Provide: short-term (24-48h), medium-term (1-7d), key factors, confidence "
            "(0-100), action_signal (STRONG_BUY/BUY/HOLD/SELL/STRONG_SELL), and risk_level "
            "(LOW/MEDIUM/HIGH)."
        )
        try:
            validated = await _invoke_structured(
                self.llm_predictor, PredictionResponse, prompt
            )
            return _ok("predictor", validated)
        except Exception as e:  # noqa: BLE001
            return _err("predictor", e)


# Global instance used by orchestrator and routers.
token_agents = TokenAnalysisAgents()
