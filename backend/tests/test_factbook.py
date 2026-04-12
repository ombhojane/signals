"""Unit tests for core.factbook extractors."""

from __future__ import annotations

import time

import pytest

from core.factbook import (
    MarketFactBook,
    RugFactBook,
    SocialFactBook,
    TokenFactBook,
    build_token_factbook,
    extract_market_factbook,
    extract_rug_factbook,
    extract_social_factbook,
)


# ---------------------------------------------------------------------------
# Market
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_market_factbook_empty_input() -> None:
    fb = extract_market_factbook(None, chain="sol")
    assert isinstance(fb, MarketFactBook)
    assert fb.has_data is False
    assert fb.chain == "sol"
    assert fb.price_usd == 0.0


@pytest.mark.unit
def test_market_factbook_missing_pairs() -> None:
    fb = extract_market_factbook({"pairs": []}, chain="sol")
    assert fb.has_data is False


@pytest.mark.unit
def test_market_factbook_happy_path() -> None:
    # Fresh launch: pairCreatedAt 2h ago
    created_ms = int((time.time() - 2 * 3600) * 1000)
    dex = {
        "pairs": [
            {
                "chainId": "solana",
                "pairAddress": "PAIRX",
                "baseToken": {"symbol": "BONK", "name": "Bonk"},
                "priceUsd": "0.0000123",
                "liquidity": {"usd": 50_000},
                "volume": {"h24": 250_000, "h6": 80_000, "h1": 15_000},
                "priceChange": {"h24": 12.5, "h6": 3.2, "h1": -1.1},
                "txns": {"h24": {"buys": 420, "sells": 180}},
                "fdv": 1_000_000,
                "marketCap": 800_000,
                "pairCreatedAt": created_ms,
            }
        ]
    }
    fb = extract_market_factbook(dex, chain="sol")
    assert fb.has_data is True
    assert fb.symbol == "BONK"
    assert fb.liquidity_usd == 50_000
    assert fb.volume_24h_usd == 250_000
    assert fb.buys_24h == 420
    assert fb.sells_24h == 180
    # Derived
    assert fb.vol_to_liq_ratio == 5.0
    assert round(fb.buy_sell_ratio, 2) == round(420 / 180, 2)
    assert fb.volatility_24h == 12.5
    assert fb.is_fresh_launch is True
    assert 1.5 < fb.age_hours < 3.0  # rough check


@pytest.mark.unit
def test_market_factbook_tolerates_nulls() -> None:
    dex = {"pairs": [{"baseToken": None, "liquidity": None, "priceUsd": None}]}
    fb = extract_market_factbook(dex, chain="base")
    assert fb.has_data is True
    assert fb.price_usd == 0.0
    assert fb.liquidity_usd == 0.0
    # Division-by-zero avoided
    assert fb.vol_to_liq_ratio == 0.0


# ---------------------------------------------------------------------------
# Rug
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_rug_factbook_empty() -> None:
    fb = extract_rug_factbook(None, None)
    assert fb.has_data is False
    assert fb.overall_risk_score == 50  # default uncertain


@pytest.mark.unit
def test_rug_factbook_honeypot_boosts_danger() -> None:
    safety = {
        "overall_risk_score": 60,
        "risk_level": "HIGH",
        "is_honeypot": True,
        "is_mintable": False,
        "ownership_renounced": True,
        "liquidity_locked": True,
        "lock_remaining_days": 90,
        "liquidity_usd": 25_000,
        "holder_count": 1_500,
        "top_10_holder_pct": 40,
        "dev_wallet_pct": 5,
    }
    fb = extract_rug_factbook(None, safety)
    assert fb.is_honeypot is True
    # Honeypot must floor danger at 0.95
    assert fb.derived_danger_score >= 0.95


@pytest.mark.unit
def test_rug_factbook_unbounded_mint_flag() -> None:
    safety = {
        "overall_risk_score": 30,
        "is_mintable": True,
        "ownership_renounced": False,
    }
    fb = extract_rug_factbook(None, safety)
    assert fb.unbounded_mint_flag is True
    # Danger should be boosted
    assert fb.derived_danger_score > 0.30


@pytest.mark.unit
def test_rug_factbook_concentration_flag_fires_above_50() -> None:
    fb = extract_rug_factbook(None, {"top_10_holder_pct": 55})
    assert fb.concentration_flag is True
    fb2 = extract_rug_factbook(None, {"top_10_holder_pct": 49})
    assert fb2.concentration_flag is False


@pytest.mark.unit
def test_rug_factbook_lp_secure_flag_requires_lock_and_duration() -> None:
    # Locked but short
    fb = extract_rug_factbook(
        None, {"liquidity_locked": True, "lock_remaining_days": 5}
    )
    assert fb.lp_secure_flag is False
    # Locked and long
    fb2 = extract_rug_factbook(
        None, {"liquidity_locked": True, "lock_remaining_days": 120}
    )
    assert fb2.lp_secure_flag is True


@pytest.mark.unit
def test_rug_factbook_parses_goplus_string_bools() -> None:
    fb = extract_rug_factbook(None, {"is_honeypot": "1", "is_mintable": "0"})
    assert fb.is_honeypot is True
    assert fb.is_mintable is False


# ---------------------------------------------------------------------------
# Social
# ---------------------------------------------------------------------------


def _tweet(
    *,
    user: str = "alice",
    followers: int = 500,
    description: str = "crypto trader",
    likes: int = 10,
    retweets: int = 2,
    replies: int = 1,
    views: int = 500,
    verified: bool = False,
    text: str = "Just bought $BONK — looks clean.",
) -> dict:
    return {
        "id": f"id-{user}",
        "text": text,
        "likeCount": likes,
        "retweetCount": retweets,
        "replyCount": replies,
        "viewCount": views,
        "author": {
            "userName": user,
            "name": user,
            "id": user,
            "isBlueVerified": verified,
            "followers": followers,
            "description": description,
        },
    }


@pytest.mark.unit
def test_social_factbook_empty() -> None:
    assert extract_social_factbook(None).has_data is False
    assert extract_social_factbook({}).has_data is False
    assert extract_social_factbook({"tweets": []}).has_data is False


@pytest.mark.unit
def test_social_factbook_error_status_returns_empty() -> None:
    fb = extract_social_factbook({"status": "error", "error": "rate limited"})
    assert fb.has_data is False


@pytest.mark.unit
def test_social_factbook_filters_obvious_bots() -> None:
    tweets = [
        _tweet(user="real1", followers=1_500),
        _tweet(user="real2", followers=800),
        # Bot: very few followers
        _tweet(user="bot1", followers=5, description="", likes=0, retweets=0),
        # Bot: no description, no engagement
        _tweet(user="bot2", followers=200, description="", likes=0, retweets=0),
    ]
    fb = extract_social_factbook({"tweets": tweets})
    assert fb.total_tweets == 4
    assert fb.filtered_tweets == 2
    assert fb.bot_tweet_ratio == 0.5
    assert fb.unique_authors == 2


@pytest.mark.unit
def test_social_factbook_detects_influencers() -> None:
    tweets = [
        _tweet(user="whale", followers=50_000),
        _tweet(user="mid", followers=3_000),
        _tweet(user="newbie", followers=200),
    ]
    fb = extract_social_factbook({"tweets": tweets})
    assert fb.influencer_count == 1


@pytest.mark.unit
def test_social_factbook_meaningful_requires_at_least_five_clean() -> None:
    tweets = [_tweet(user=f"real{i}", followers=800) for i in range(5)]
    fb = extract_social_factbook({"tweets": tweets})
    assert fb.has_meaningful_social is True
    fb2 = extract_social_factbook({"tweets": tweets[:3]})
    assert fb2.has_meaningful_social is False


# ---------------------------------------------------------------------------
# Unified
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_build_token_factbook_combines_all_three() -> None:
    tfb = build_token_factbook(
        token_address="TOKEN123",
        chain="sol",
        dex_data={
            "pairs": [
                {
                    "baseToken": {"symbol": "T", "name": "T"},
                    "priceUsd": "0.01",
                    "liquidity": {"usd": 10_000},
                    "volume": {"h24": 5_000},
                }
            ]
        },
        safety_data={"overall_risk_score": 20, "top_10_holder_pct": 35},
        twitter_data={"tweets": [_tweet(user=f"u{i}", followers=1_000) for i in range(6)]},
    )
    assert isinstance(tfb, TokenFactBook)
    assert tfb.market.has_data
    assert tfb.rug.has_data
    assert tfb.social.has_data
    # Compact dict drops zero fields
    d = tfb.to_llm_dict()
    assert "market" in d and "rug" in d and "social" in d
