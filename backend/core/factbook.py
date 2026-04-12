"""
FactBook extractor — Stage 0 of the enhanced AI pipeline.

Turns messy raw JSON from DEX / GMGN / Safety / Twitter APIs into compact,
typed, immutable dataclasses containing ~25 numeric facts per domain plus
derived features. The FactBook is what LLM agents anchor on — they never
see raw JSON again.

Why this exists:
- Raw JSON dumps waste tokens and tempt the LLM to hallucinate fields
- Derived features (vol/liq ratio, holder concentration, bot ratio) are
  cheaper and more accurate to compute deterministically than via prompt
- Immutable dataclasses make the pipeline stateless and testable

All extractors are tolerant of missing or malformed fields and return a
FactBook with sensible defaults. None of them raise.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Domain dataclasses (frozen — immutable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class MarketFactBook:
    """DEX + price / volume facts for one token."""

    # Identity
    symbol: str = ""
    name: str = ""
    chain: str = ""
    pair_address: str = ""

    # Raw price / liquidity
    price_usd: float = 0.0
    liquidity_usd: float = 0.0
    market_cap_usd: float = 0.0
    fdv_usd: float = 0.0

    # Volume
    volume_1h_usd: float = 0.0
    volume_6h_usd: float = 0.0
    volume_24h_usd: float = 0.0

    # Price change
    price_change_1h_pct: float = 0.0
    price_change_6h_pct: float = 0.0
    price_change_24h_pct: float = 0.0

    # Txn activity
    buys_24h: int = 0
    sells_24h: int = 0

    # Age
    pair_created_at_ms: int = 0
    age_hours: float = 0.0

    # Derived (computed post-extract)
    vol_to_liq_ratio: float = 0.0  # volume_24h / liquidity
    buy_sell_ratio: float = 1.0  # buys / max(sells, 1)
    volatility_24h: float = 0.0  # abs(price_change_24h)
    trading_velocity: float = 0.0  # txns / hour since creation
    is_fresh_launch: bool = False  # age < 24h

    # Availability flag
    has_data: bool = False


@dataclass(frozen=True)
class RugFactBook:
    """Contract + holder + safety facts combined from GMGN and Safety APIs."""

    # Composite risk from providers
    overall_risk_score: int = 50  # 0-100, higher = riskier
    risk_level: str = "UNKNOWN"  # LOW / MEDIUM / HIGH / CRITICAL / UNKNOWN

    # Contract flags (None means unknown)
    is_honeypot: Optional[bool] = None
    is_mintable: Optional[bool] = None
    is_open_source: Optional[bool] = None
    ownership_renounced: Optional[bool] = None

    # Liquidity lock
    liquidity_locked: Optional[bool] = None
    lock_days_remaining: int = 0
    liquidity_usd: float = 0.0

    # Holder distribution
    holder_count: int = 0
    top_10_holder_pct: float = 0.0
    dev_wallet_pct: float = 0.0

    # Smart money signal
    smart_money_flow: str = "neutral"  # buying / selling / neutral

    # Derived flags
    concentration_flag: bool = False  # top_10 > 50
    lp_secure_flag: bool = False  # locked AND lock_days >= 30
    unbounded_mint_flag: bool = False  # mintable AND not renounced

    # Composite derived safety (0 = safe, 1 = catastrophic)
    derived_danger_score: float = 0.5

    has_data: bool = False


@dataclass(frozen=True)
class SocialFactBook:
    """Social sentiment facts with basic bot filtering applied."""

    # Volume
    total_tweets: int = 0
    filtered_tweets: int = 0  # after bot filter
    unique_authors: int = 0
    influencer_count: int = 0  # authors with > 10k followers

    # Engagement
    total_likes: int = 0
    total_retweets: int = 0
    total_replies: int = 0
    total_views: int = 0
    avg_engagement: float = 0.0

    # Bot signal
    bot_tweet_ratio: float = 0.0  # fraction of tweets from suspected bots
    verified_tweet_ratio: float = 0.0  # fraction from blue-verified accounts

    # Content signal
    top_tweets_preview: Tuple[str, ...] = ()  # up to 5 highest engagement, truncated

    # Derived
    has_meaningful_social: bool = False  # >= 5 non-bot tweets
    organic_signal_strength: float = 0.0  # 0-1

    has_data: bool = False


@dataclass(frozen=True)
class TokenFactBook:
    """Top-level container combining all three domains for one token."""

    token_address: str
    chain: str
    market: MarketFactBook
    rug: RugFactBook
    social: SocialFactBook
    extracted_at: float = field(default_factory=time.time)

    def to_llm_dict(self) -> Dict[str, Any]:
        """Flatten to a compact dict for LLM prompt injection.

        Drops empty / default-only fields to keep prompts short.
        """
        return {
            "token": self.token_address,
            "chain": self.chain,
            "market": _compact(asdict(self.market)),
            "rug": _compact(asdict(self.rug)),
            "social": _compact(asdict(self.social)),
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _compact(d: Dict[str, Any]) -> Dict[str, Any]:
    """Drop zero / empty / None fields so LLM prompts stay short."""
    out: Dict[str, Any] = {}
    for k, v in d.items():
        if v is None:
            continue
        if isinstance(v, (int, float)) and v == 0:
            continue
        if isinstance(v, str) and v in ("", "UNKNOWN", "neutral"):
            continue
        if isinstance(v, (list, tuple)) and not v:
            continue
        if isinstance(v, bool) and v is False:
            continue
        out[k] = v
    return out


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any) -> Optional[bool]:
    """Parse GoPlus-style bool ('0'/'1') and Python bools."""
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("1", "true", "yes"):
            return True
        if v in ("0", "false", "no"):
            return False
    return None


# ---------------------------------------------------------------------------
# Extractors — one per data source
# ---------------------------------------------------------------------------


def extract_market_factbook(
    dex_data: Optional[Dict[str, Any]],
    *,
    chain: str = "",
) -> MarketFactBook:
    """Build MarketFactBook from DexScreener-shaped response."""
    if not dex_data:
        return MarketFactBook(chain=chain)

    pairs = dex_data.get("pairs") or []
    if not pairs or not isinstance(pairs, list):
        return MarketFactBook(chain=chain)

    pair = pairs[0] or {}
    base = pair.get("baseToken") or {}
    liquidity = pair.get("liquidity") or {}
    volume = pair.get("volume") or {}
    price_change = pair.get("priceChange") or {}
    txns = pair.get("txns") or {}
    txns_24h = txns.get("h24") or {}

    price_usd = _safe_float(pair.get("priceUsd"))
    liq_usd = _safe_float(liquidity.get("usd"))
    volume_24h = _safe_float(volume.get("h24"))
    volume_6h = _safe_float(volume.get("h6"))
    volume_1h = _safe_float(volume.get("h1"))

    buys_24h = _safe_int(txns_24h.get("buys"))
    sells_24h = _safe_int(txns_24h.get("sells"))

    pair_created_ms = _safe_int(pair.get("pairCreatedAt"))
    now_ms = int(time.time() * 1000)
    age_hours = (
        max(0.0, (now_ms - pair_created_ms) / (1000 * 60 * 60))
        if pair_created_ms > 0
        else 0.0
    )

    # Derived
    vol_to_liq = volume_24h / liq_usd if liq_usd > 0 else 0.0
    buy_sell = buys_24h / max(sells_24h, 1)
    price_change_24h = _safe_float(price_change.get("h24"))
    volatility = abs(price_change_24h)
    total_txns = buys_24h + sells_24h
    trading_velocity = total_txns / max(age_hours, 1.0)

    return MarketFactBook(
        symbol=str(base.get("symbol") or ""),
        name=str(base.get("name") or ""),
        chain=chain or str(pair.get("chainId") or ""),
        pair_address=str(pair.get("pairAddress") or ""),
        price_usd=price_usd,
        liquidity_usd=liq_usd,
        market_cap_usd=_safe_float(pair.get("marketCap")),
        fdv_usd=_safe_float(pair.get("fdv")),
        volume_1h_usd=volume_1h,
        volume_6h_usd=volume_6h,
        volume_24h_usd=volume_24h,
        price_change_1h_pct=_safe_float(price_change.get("h1")),
        price_change_6h_pct=_safe_float(price_change.get("h6")),
        price_change_24h_pct=price_change_24h,
        buys_24h=buys_24h,
        sells_24h=sells_24h,
        pair_created_at_ms=pair_created_ms,
        age_hours=round(age_hours, 2),
        vol_to_liq_ratio=round(vol_to_liq, 3),
        buy_sell_ratio=round(buy_sell, 3),
        volatility_24h=round(volatility, 3),
        trading_velocity=round(trading_velocity, 3),
        is_fresh_launch=0 < age_hours < 24,
        has_data=True,
    )


def extract_rug_factbook(
    gmgn_data: Optional[Dict[str, Any]],
    safety_data: Optional[Dict[str, Any]],
) -> RugFactBook:
    """Build RugFactBook by merging GMGN token stats and Safety report data."""
    if not gmgn_data and not safety_data:
        return RugFactBook()

    safety = safety_data or {}
    gmgn = gmgn_data or {}
    token_stats = gmgn.get("token_stats") or {}

    overall_risk = _safe_int(safety.get("overall_risk_score"), default=50)
    risk_level = str(safety.get("risk_level") or "UNKNOWN").upper()

    is_honeypot = _safe_bool(safety.get("is_honeypot"))
    is_mintable = _safe_bool(safety.get("is_mintable"))
    is_open_source = _safe_bool(safety.get("is_open_source"))
    ownership_renounced = _safe_bool(safety.get("ownership_renounced"))
    liquidity_locked = _safe_bool(safety.get("liquidity_locked"))

    lock_days = _safe_int(safety.get("lock_remaining_days"))
    liq_usd = _safe_float(safety.get("liquidity_usd")) or _safe_float(
        token_stats.get("liquidity")
    )

    holder_count = _safe_int(safety.get("holder_count")) or _safe_int(
        token_stats.get("holder_count")
    )
    top_10 = _safe_float(safety.get("top_10_holder_pct"))
    dev_pct = _safe_float(safety.get("dev_wallet_pct"))

    smart_money = str(safety.get("smart_money_flow") or "neutral").lower()

    # Derived flags
    concentration_flag = top_10 > 50.0
    lp_secure = liquidity_locked is True and lock_days >= 30
    unbounded_mint = is_mintable is True and ownership_renounced is False

    # Composite derived danger in [0, 1].
    # Start from overall_risk (0-100 → 0-1), add penalties for flagged booleans.
    danger = overall_risk / 100.0
    if is_honeypot:
        danger = max(danger, 0.95)
    if unbounded_mint:
        danger = min(1.0, danger + 0.15)
    if concentration_flag:
        danger = min(1.0, danger + 0.10)
    if liquidity_locked is False:
        danger = min(1.0, danger + 0.10)
    if dev_pct > 15.0:
        danger = min(1.0, danger + 0.05)

    return RugFactBook(
        overall_risk_score=overall_risk,
        risk_level=risk_level,
        is_honeypot=is_honeypot,
        is_mintable=is_mintable,
        is_open_source=is_open_source,
        ownership_renounced=ownership_renounced,
        liquidity_locked=liquidity_locked,
        lock_days_remaining=lock_days,
        liquidity_usd=liq_usd,
        holder_count=holder_count,
        top_10_holder_pct=round(top_10, 2),
        dev_wallet_pct=round(dev_pct, 2),
        smart_money_flow=smart_money,
        concentration_flag=concentration_flag,
        lp_secure_flag=lp_secure,
        unbounded_mint_flag=unbounded_mint,
        derived_danger_score=round(danger, 3),
        has_data=True,
    )


# Bot heuristics — intentionally simple. Step 5 will replace with a dedicated
# preprocessor. A tweet is "bot-like" if its author has < MIN_FOLLOWERS or
# no profile description and zero engagement.
_BOT_MIN_FOLLOWERS = 50
_INFLUENCER_MIN_FOLLOWERS = 10_000


def _is_bot_tweet(tweet: Dict[str, Any]) -> bool:
    author = tweet.get("author") or {}
    followers = _safe_int(author.get("followers"))
    if followers < _BOT_MIN_FOLLOWERS:
        return True
    description = str(author.get("description") or "").strip()
    likes = _safe_int(tweet.get("likeCount"))
    retweets = _safe_int(tweet.get("retweetCount"))
    if not description and likes == 0 and retweets == 0:
        return True
    return False


def extract_social_factbook(
    twitter_data: Optional[Dict[str, Any]],
) -> SocialFactBook:
    """Build SocialFactBook with basic bot filtering."""
    if not twitter_data:
        return SocialFactBook()

    if twitter_data.get("status") == "error":
        return SocialFactBook()

    tweets: List[Dict[str, Any]] = list(twitter_data.get("tweets") or [])
    total = len(tweets)
    if total == 0:
        return SocialFactBook()

    # Normalize pydantic objects if present
    normalized: List[Dict[str, Any]] = []
    for t in tweets:
        if hasattr(t, "model_dump"):
            normalized.append(t.model_dump())
        elif isinstance(t, dict):
            normalized.append(t)
    tweets = normalized

    bot_count = sum(1 for t in tweets if _is_bot_tweet(t))
    clean = [t for t in tweets if not _is_bot_tweet(t)]

    authors = set()
    influencer_count = 0
    verified_count = 0
    total_likes = total_retweets = total_replies = total_views = 0

    for t in clean:
        author = t.get("author") or {}
        user = author.get("userName") or author.get("id") or ""
        if user:
            authors.add(user)
        followers = _safe_int(author.get("followers"))
        if followers >= _INFLUENCER_MIN_FOLLOWERS:
            influencer_count += 1
        if author.get("isBlueVerified"):
            verified_count += 1
        total_likes += _safe_int(t.get("likeCount"))
        total_retweets += _safe_int(t.get("retweetCount"))
        total_replies += _safe_int(t.get("replyCount"))
        total_views += _safe_int(t.get("viewCount"))

    clean_count = len(clean)
    avg_engagement = (
        (total_likes + total_retweets * 2 + total_replies) / clean_count
        if clean_count > 0
        else 0.0
    )

    bot_ratio = bot_count / total if total > 0 else 0.0
    verified_ratio = verified_count / clean_count if clean_count > 0 else 0.0

    # Top 5 by engagement for LLM preview (truncate each tweet)
    ranked = sorted(
        clean,
        key=lambda t: _safe_int(t.get("likeCount"))
        + _safe_int(t.get("retweetCount")) * 2,
        reverse=True,
    )[:5]
    top_previews = tuple(
        (str(t.get("text") or "")[:180]).replace("\n", " ").strip() for t in ranked
    )

    organic_strength = 0.0
    if clean_count > 0:
        organic_strength = min(
            1.0,
            (clean_count / 20.0) * 0.4  # volume of clean tweets
            + (influencer_count / 3.0) * 0.3  # influencers
            + (1.0 - bot_ratio) * 0.3,  # clean ratio
        )

    return SocialFactBook(
        total_tweets=total,
        filtered_tweets=clean_count,
        unique_authors=len(authors),
        influencer_count=influencer_count,
        total_likes=total_likes,
        total_retweets=total_retweets,
        total_replies=total_replies,
        total_views=total_views,
        avg_engagement=round(avg_engagement, 2),
        bot_tweet_ratio=round(bot_ratio, 3),
        verified_tweet_ratio=round(verified_ratio, 3),
        top_tweets_preview=top_previews,
        has_meaningful_social=clean_count >= 5,
        organic_signal_strength=round(organic_strength, 3),
        has_data=True,
    )


# ---------------------------------------------------------------------------
# Unified extractor
# ---------------------------------------------------------------------------


def build_token_factbook(
    *,
    token_address: str,
    chain: str,
    dex_data: Optional[Dict[str, Any]] = None,
    gmgn_data: Optional[Dict[str, Any]] = None,
    safety_data: Optional[Dict[str, Any]] = None,
    twitter_data: Optional[Dict[str, Any]] = None,
) -> TokenFactBook:
    """Build a TokenFactBook from the raw API blobs the orchestrator already has."""
    return TokenFactBook(
        token_address=token_address,
        chain=chain,
        market=extract_market_factbook(dex_data, chain=chain),
        rug=extract_rug_factbook(gmgn_data, safety_data),
        social=extract_social_factbook(twitter_data),
    )
