"""
Social Preprocessor — cleans raw Twitter payloads before they reach the
FactBook extractor or the Social agent.

Why this exists:
- twitterapi.io returns up to 20 tweets with no quality filter; memecoin
  launches attract large swarms of throwaway bot accounts that drown out
  real signal.
- The Social agent reading 20 raw tweets will dutifully report "high
  engagement" on what is actually coordinated shilling. The preprocessor
  gives the agent ~5 high-quality tweets from distinct authors with all
  the bot/dup noise stripped.
- Filtering lives in its own module (not inside factbook.py) so the rules
  can be audited and tuned independently — and so we can apply the same
  cleanup before storing raw data for later analysis.

Heuristics are intentionally simple and explainable. A fine-tuned bot
classifier is a v2 concern (see specs/aiimprove.md).
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Thresholds — tunable. Matched against eval harness outcomes.
# ---------------------------------------------------------------------------

MIN_FOLLOWERS_BOT_FLOOR = 50          # accounts below this are suspected bots
MIN_DESC_LEN_BOT_FLOOR = 5            # bare-profile heuristic
MIN_AGE_DAYS_BOT_FLOOR = 7            # accounts < 7d old are suspicious
INFLUENCER_FOLLOWERS = 10_000         # "influencer" threshold
MAX_RETURNED_TWEETS = 8               # what the Social agent actually reads
MIN_ORGANIC_ENGAGEMENT = 1            # likes + retweets to count as engaged
MAX_TWEETS_PER_AUTHOR = 2             # cap per-author to prevent one account dominating the feed

# A crude shilly-copypaste detector: if normalized text collides for multiple
# authors, drop duplicates (one per collision cluster).
_WHITESPACE_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
_MENTION_RE = re.compile(r"@\w+")
# Wallet addresses, contract addresses, tx hashes, CIDs — anything that looks
# like a long opaque token. These vary per-shill but the surrounding pitch is
# identical, so stripping them is what makes the dedup actually collapse the
# copypaste. Matches any non-whitespace sequence of 25+ chars (EVM addresses
# are 42, Solana pubkeys ~44, tx hashes 64+).
_LONG_TOKEN_RE = re.compile(r"\S{25,}")
# Also strip standalone number tokens that vary (prices, amounts, counts) so
# "buy 1000 $X" and "buy 2500 $X" collapse.
_LONG_NUMBER_RE = re.compile(r"\b\d{3,}\b")


@dataclass(frozen=True)
class PreprocessedSocial:
    """Result of running preprocessing over a raw Twitter payload."""

    cleaned_tweets: Tuple[Dict[str, Any], ...]
    dropped_bot_count: int
    dropped_duplicate_count: int
    original_count: int
    unique_authors: int
    influencer_count: int
    verified_count: int
    bot_ratio: float
    duplicate_ratio: float

    def to_twitter_data(self) -> Dict[str, Any]:
        """Repackage as a Twitter-shaped dict the FactBook / agent can consume."""
        return {
            "tweets": list(self.cleaned_tweets),
            "status": "success",
            "meta": {
                "original_count": self.original_count,
                "dropped_bot_count": self.dropped_bot_count,
                "dropped_duplicate_count": self.dropped_duplicate_count,
                "bot_ratio": self.bot_ratio,
                "duplicate_ratio": self.duplicate_ratio,
                "unique_authors": self.unique_authors,
                "influencer_count": self.influencer_count,
                "verified_count": self.verified_count,
            },
        }


def _normalize_text(text: str) -> str:
    """Strip URLs, mentions, wallet addresses, numbers, whitespace.

    The goal is to collapse copypaste shills that differ only in a wallet
    address or a dollar amount. After normalization, the remaining text is
    just the pitch, so hash collision reliably flags them as duplicates.
    """
    if not text:
        return ""
    t = text.lower()
    t = _URL_RE.sub("", t)
    t = _MENTION_RE.sub("", t)
    t = _LONG_TOKEN_RE.sub("", t)
    t = _LONG_NUMBER_RE.sub("", t)
    t = _WHITESPACE_RE.sub(" ", t).strip()
    return t


def _text_hash(text: str) -> str:
    return hashlib.md5(_normalize_text(text).encode("utf-8")).hexdigest()


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _get_author(tweet: Dict[str, Any]) -> Dict[str, Any]:
    """Extract the author subdict, tolerating pydantic wrappers."""
    author = tweet.get("author") or {}
    if hasattr(author, "model_dump"):
        author = author.model_dump()
    return author if isinstance(author, dict) else {}


def _is_bot(tweet: Dict[str, Any]) -> bool:
    """Single-tweet bot heuristic.

    A tweet is bot-like if ANY of the following hold:
      - author followers < MIN_FOLLOWERS_BOT_FLOOR
      - author description is empty / near-empty AND engagement is zero
      - account age < MIN_AGE_DAYS_BOT_FLOOR AND zero engagement
    """
    author = _get_author(tweet)
    followers = _safe_int(author.get("followers"))
    if followers < MIN_FOLLOWERS_BOT_FLOOR:
        return True

    description = str(author.get("description") or "").strip()
    likes = _safe_int(tweet.get("likeCount"))
    retweets = _safe_int(tweet.get("retweetCount"))
    engagement = likes + retweets

    if len(description) < MIN_DESC_LEN_BOT_FLOOR and engagement < MIN_ORGANIC_ENGAGEMENT:
        return True

    # createdAt is ISO string in twitterapi.io responses; skip if missing.
    created_at = author.get("createdAt") or author.get("created_at")
    if created_at and engagement == 0:
        try:
            # Accept "2025-01-15" or full ISO; fall back gracefully if format unknown.
            from datetime import datetime, timezone
            if isinstance(created_at, str):
                ts = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                age_days = (datetime.now(timezone.utc) - ts).days
                if age_days < MIN_AGE_DAYS_BOT_FLOOR:
                    return True
        except (ValueError, TypeError):
            pass

    return False


def _normalize_tweet(tweet: Any) -> Optional[Dict[str, Any]]:
    """Turn a pydantic TweetData or dict into a plain dict. None on garbage."""
    if tweet is None:
        return None
    if hasattr(tweet, "model_dump"):
        return tweet.model_dump()
    if isinstance(tweet, dict):
        return tweet
    return None


def preprocess_tweets(
    raw_tweets: Iterable[Any],
) -> PreprocessedSocial:
    """Clean a collection of raw tweets.

    Steps (in order):
      1. Normalize shape — convert pydantic models to dicts, drop garbage.
      2. Bot filter — drop tweets failing `_is_bot`.
      3. Dedup near-identical content (copy-paste shills) via normalized hash.
      4. Rank surviving tweets by engagement, return top N.
    """
    # 1. Normalize
    normalized: List[Dict[str, Any]] = []
    for t in raw_tweets:
        nt = _normalize_tweet(t)
        if nt is not None:
            normalized.append(nt)
    original_count = len(normalized)

    if original_count == 0:
        return PreprocessedSocial(
            cleaned_tweets=(),
            dropped_bot_count=0,
            dropped_duplicate_count=0,
            original_count=0,
            unique_authors=0,
            influencer_count=0,
            verified_count=0,
            bot_ratio=0.0,
            duplicate_ratio=0.0,
        )

    # 2. Bot filter
    non_bot: List[Dict[str, Any]] = []
    dropped_bots = 0
    for t in normalized:
        if _is_bot(t):
            dropped_bots += 1
        else:
            non_bot.append(t)

    # 3. Dedup
    seen_hashes: Dict[str, Dict[str, Any]] = {}
    dropped_dups = 0
    for t in non_bot:
        h = _text_hash(str(t.get("text") or ""))
        if not h:
            # Keep empty-text tweets separately (rare, edge case)
            seen_hashes[f"empty-{len(seen_hashes)}"] = t
            continue
        if h in seen_hashes:
            dropped_dups += 1
            # Keep the one with higher engagement
            current = seen_hashes[h]
            current_eng = _safe_int(current.get("likeCount")) + _safe_int(
                current.get("retweetCount")
            )
            new_eng = _safe_int(t.get("likeCount")) + _safe_int(t.get("retweetCount"))
            if new_eng > current_eng:
                seen_hashes[h] = t
        else:
            seen_hashes[h] = t

    deduped = list(seen_hashes.values())

    # 4. Rank by engagement (likes + 2*rts + replies) and cap per-author.
    # Without the per-author cap, one account posting 10 slight variations of
    # the same shill text can dominate the clean residue — we saw this in
    # the BONK smoke test. Keeping at most 2 per author forces diversity.
    def _score(t: Dict[str, Any]) -> int:
        return (
            _safe_int(t.get("likeCount"))
            + 2 * _safe_int(t.get("retweetCount"))
            + _safe_int(t.get("replyCount"))
        )

    deduped.sort(key=_score, reverse=True)

    author_counts: Dict[str, int] = {}
    author_capped: List[Dict[str, Any]] = []
    dropped_per_author = 0
    for t in deduped:
        author = _get_author(t)
        user = author.get("userName") or author.get("id") or "_anon"
        count = author_counts.get(user, 0)
        if count >= MAX_TWEETS_PER_AUTHOR:
            dropped_per_author += 1
            continue
        author_counts[user] = count + 1
        author_capped.append(t)

    top = author_capped[:MAX_RETURNED_TWEETS]

    # Stats
    authors = set()
    influencer_count = 0
    verified_count = 0
    for t in deduped:
        author = _get_author(t)
        user = author.get("userName") or author.get("id") or ""
        if user:
            authors.add(user)
        if _safe_int(author.get("followers")) >= INFLUENCER_FOLLOWERS:
            influencer_count += 1
        if author.get("isBlueVerified"):
            verified_count += 1

    bot_ratio = dropped_bots / original_count if original_count > 0 else 0.0
    dup_ratio = dropped_dups / max(len(non_bot), 1)
    # Track the per-author drops in the duplicate_ratio tally — they're
    # effectively duplicates from a signal-quality perspective.
    total_dup_like = dropped_dups + dropped_per_author
    dup_ratio_effective = total_dup_like / max(len(non_bot), 1)

    return PreprocessedSocial(
        cleaned_tweets=tuple(top),
        dropped_bot_count=dropped_bots,
        dropped_duplicate_count=total_dup_like,
        original_count=original_count,
        unique_authors=len(authors),
        influencer_count=influencer_count,
        verified_count=verified_count,
        bot_ratio=round(bot_ratio, 3),
        duplicate_ratio=round(dup_ratio_effective, 3),
    )


def preprocess_twitter_payload(
    twitter_data: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Clean a full twitter_data payload and return a new dict in the same shape.

    Safe to call on None / error payloads — returns the input shape verbatim
    so downstream `validate_twitter_data` still sees the same error signal.
    """
    if not twitter_data:
        return {"tweets": [], "status": "empty"}

    if twitter_data.get("status") == "error":
        return twitter_data  # leave error payloads alone

    tweets = twitter_data.get("tweets") or []
    result = preprocess_tweets(tweets)
    cleaned = result.to_twitter_data()

    # Preserve pagination / cursor info if present
    for key in ("has_next_page", "next_cursor"):
        if key in twitter_data:
            cleaned[key] = twitter_data[key]

    return cleaned
