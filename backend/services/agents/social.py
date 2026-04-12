"""Social Sentiment Agent — analyzes the SocialFactBook slice."""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Tuple

from core.factbook import SocialFactBook
from core.logging import logger
from models.agent_responses import SocialAnalysisResponse
from services.agents.base import (
    AgentOutcome,
    empty_outcome,
    invoke_structured,
    log_agent_error,
    make_llm,
    outcome_from_pydantic,
)


_AGENT_TYPE = "social_agent"
_TEMPERATURE = 0.4  # slightly higher — sentiment benefits from variety


class SocialAgent:
    """Turns a SocialFactBook into a scored social assessment.

    Receives the output of `social_preprocessor.preprocess_twitter_payload`,
    so bot noise and copy-paste duplicates are already stripped. Reads
    ~5 top tweets plus aggregate stats, not 20 raw tweets.
    """

    def __init__(self) -> None:
        self.llm = make_llm(temperature=_TEMPERATURE)

    async def analyze(self, factbook: SocialFactBook) -> AgentOutcome:
        if not factbook.has_data or factbook.filtered_tweets == 0:
            return empty_outcome(_AGENT_TYPE, "social data missing or all filtered")

        prompt = self._build_prompt(factbook)
        try:
            response: SocialAnalysisResponse = await invoke_structured(
                self.llm, SocialAnalysisResponse, prompt
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

        # Social score: normalized sentiment.
        score = response.score
        if score == 0.5:
            score = max(0.0, min(1.0, response.sentiment_score / 100.0))

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

    def _build_prompt(self, fb: SocialFactBook) -> str:
        facts = {
            "total_tweets_observed": fb.total_tweets,
            "clean_tweets_after_filter": fb.filtered_tweets,
            "unique_authors": fb.unique_authors,
            "influencer_count": fb.influencer_count,
            "bot_tweet_ratio": fb.bot_tweet_ratio,
            "verified_tweet_ratio": fb.verified_tweet_ratio,
            "total_likes": fb.total_likes,
            "total_retweets": fb.total_retweets,
            "total_replies": fb.total_replies,
            "total_views": fb.total_views,
            "avg_engagement": fb.avg_engagement,
            "organic_signal_strength": fb.organic_signal_strength,
            "top_tweets_preview": list(fb.top_tweets_preview),
        }
        return (
            "You are a social-media analyst specializing in crypto Twitter sentiment "
            "and coordinated-shill detection.\n\n"
            "The raw tweet stream has already been preprocessed: known bots and "
            "copy-paste duplicates were stripped, and per-author posts are capped. "
            "You are looking at the *clean* residue. Your job is to assess whether "
            "what remains looks organic.\n\n"
            "CRITICAL — relevance and confidence rules:\n"
            "- These tweets came from a keyword search for the token's symbol/name. "
            "Symbols are often reused across unrelated scam tokens. If the top tweets "
            "reference a DIFFERENT project (e.g. a pre-sale for a new token that happens "
            "to share the keyword), the signal is NOISE about the target token — your "
            "confidence MUST be ≤ 0.4 and your score should be neutral (~0.5), not negative.\n"
            "- Do NOT flag a target token as a scam based on tweets that are clearly "
            "about a different token using the same keyword.\n"
            "- If unique_authors < 3 while clean_tweets_after_filter > 3, the feed is "
            "dominated by one account — cap your confidence at 0.4.\n"
            "- If clean_tweets_after_filter < 3, you do not have enough data — return "
            "confidence ≤ 0.3 and a neutral score.\n\n"
            "SOCIAL FACTS:\n"
            f"{json.dumps(facts, separators=(',', ':'))}\n\n"
            "Focus on:\n"
            "1. Is there real discussion (diverse authors, replies) or one-way promotion?\n"
            "2. Do influencers (> 10k followers) participate, or only new accounts?\n"
            "3. Does engagement per tweet make sense given author followers?\n"
            "4. Do the top-tweet previews discuss the target token substantively, or "
            "are they about a different project that happens to match the keyword?\n"
            "5. bot_tweet_ratio > 0.4 before filtering → organic concern even after cleanup.\n\n"
            "Return a SocialAnalysisResponse JSON with:\n"
            "- sentiment_score: integer 0-100 (100 = bullish organic; 50 = neutral/no data)\n"
            "- community_health: integer 0-100\n"
            "- score: float 0.0-1.0 (normalized social-health score; higher = stronger organic signal; 0.5 = no signal)\n"
            "- confidence: float 0.0-1.0 (apply the caps above)\n"
            "- red_flags: array of manipulation/hype concerns identified in the TARGET token's discussion\n"
            "- engagement_level, influencer_impact, hype_assessment, trend_analysis, summary"
        )
