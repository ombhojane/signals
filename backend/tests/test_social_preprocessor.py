"""Unit tests for services.social_preprocessor."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from services.social_preprocessor import (
    MAX_RETURNED_TWEETS,
    PreprocessedSocial,
    preprocess_tweets,
    preprocess_twitter_payload,
)


def _tweet(
    *,
    user: str,
    followers: int = 500,
    description: str = "crypto trader since 2021",
    text: str = "Just bought this — looks clean",
    likes: int = 10,
    retweets: int = 2,
    replies: int = 1,
    views: int = 500,
    verified: bool = False,
) -> Dict[str, Any]:
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


# ---------------------------------------------------------------------------
# Empty / error paths
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_preprocess_empty_iterable() -> None:
    result = preprocess_tweets([])
    assert isinstance(result, PreprocessedSocial)
    assert result.original_count == 0
    assert result.cleaned_tweets == ()
    assert result.bot_ratio == 0.0


@pytest.mark.unit
def test_preprocess_payload_error_passthrough() -> None:
    error = {"status": "error", "error": "rate limited"}
    assert preprocess_twitter_payload(error) == error


@pytest.mark.unit
def test_preprocess_payload_none_returns_empty_shape() -> None:
    result = preprocess_twitter_payload(None)
    assert result["tweets"] == []
    assert result["status"] == "empty"


# ---------------------------------------------------------------------------
# Bot filtering
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_preprocess_filters_low_follower_bots() -> None:
    tweets = [
        _tweet(user="real", followers=1_200),
        _tweet(user="bot1", followers=5, description="", likes=0, retweets=0),
        _tweet(user="bot2", followers=10, description="", likes=0, retweets=0),
    ]
    result = preprocess_tweets(tweets)
    assert result.dropped_bot_count == 2
    assert len(result.cleaned_tweets) == 1
    assert result.cleaned_tweets[0]["author"]["userName"] == "real"


@pytest.mark.unit
def test_preprocess_filters_bare_profile_zero_engagement() -> None:
    tweets = [
        _tweet(user="bare", followers=500, description="", likes=0, retweets=0),
    ]
    result = preprocess_tweets(tweets)
    assert result.dropped_bot_count == 1


@pytest.mark.unit
def test_preprocess_keeps_bare_profile_with_engagement() -> None:
    tweets = [
        _tweet(user="keeper", followers=500, description="", likes=50, retweets=10),
    ]
    result = preprocess_tweets(tweets)
    assert result.dropped_bot_count == 0
    assert len(result.cleaned_tweets) == 1


# ---------------------------------------------------------------------------
# Duplicate detection
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_preprocess_dedupes_copypaste_shills() -> None:
    tweets = [
        _tweet(user="alice", followers=800, text="Just aped into $TOKEN — wagmi"),
        _tweet(user="bob", followers=800, text="Just aped into $TOKEN — wagmi"),
        _tweet(user="carol", followers=800, text="Just aped into $TOKEN — wagmi"),
        _tweet(user="dave", followers=800, text="Genuinely bullish on this one"),
    ]
    result = preprocess_tweets(tweets)
    assert result.dropped_duplicate_count == 2
    assert len(result.cleaned_tweets) == 2


@pytest.mark.unit
def test_preprocess_dedup_normalizes_urls_and_mentions() -> None:
    tweets = [
        _tweet(user="alice", followers=800, text="Check @a $X https://example.com pump"),
        _tweet(user="bob", followers=800, text="Check @b $X https://other.com pump"),
    ]
    result = preprocess_tweets(tweets)
    # After URL+mention normalization the bodies should collapse
    assert result.dropped_duplicate_count == 1


@pytest.mark.unit
def test_preprocess_dedup_collapses_shills_with_different_wallet_addresses() -> None:
    """Real-world regression: presale shills post identical text with different
    wallet/mint addresses per tweet. Those addresses must be normalized away
    so dedup catches the copy-paste pitch. Discovered during BONK smoke test."""
    tweets = [
        _tweet(
            user="shill1",
            followers=800,
            text="Send SOL to this address BjNCKT2ugchgHcTGeWjwZr2DVA9UHW5nuCHhDEiQxvx for presale",
        ),
        _tweet(
            user="shill2",
            followers=800,
            text="Send SOL to this address 7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU for presale",
        ),
        _tweet(
            user="shill3",
            followers=800,
            text="Send SOL to this address 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM for presale",
        ),
    ]
    result = preprocess_tweets(tweets)
    # All three should collapse into one
    assert result.dropped_duplicate_count == 2
    assert len(result.cleaned_tweets) == 1


@pytest.mark.unit
def test_preprocess_dedup_collapses_shills_with_different_amounts() -> None:
    """Another real-world pattern: same pitch with different token amounts."""
    tweets = [
        _tweet(user="a", followers=800, text="Just bought 1000 tokens going parabolic"),
        _tweet(user="b", followers=800, text="Just bought 2500 tokens going parabolic"),
        _tweet(user="c", followers=800, text="Just bought 9999 tokens going parabolic"),
    ]
    result = preprocess_tweets(tweets)
    assert result.dropped_duplicate_count == 2
    assert len(result.cleaned_tweets) == 1


@pytest.mark.unit
def test_preprocess_caps_per_author_when_one_account_dominates() -> None:
    """BONK-smoke-test regression: if one account posts 10 slight variations
    of the same shill, they should be capped at MAX_TWEETS_PER_AUTHOR."""
    # 10 tweets from same author, all unique enough to survive hash dedup
    tweets = [
        _tweet(
            user="shill",
            followers=50_000,
            text=f"Presale alpha drop number {i} dont miss this one",
            likes=100 + i,
        )
        for i in range(10)
    ]
    # 3 tweets from different authors
    tweets.extend(
        [
            _tweet(user="legit1", followers=5_000, text="Genuine analysis thread here"),
            _tweet(user="legit2", followers=5_000, text="Different take on the market"),
            _tweet(user="legit3", followers=5_000, text="Third independent opinion"),
        ]
    )
    result = preprocess_tweets(tweets)
    # shill should be capped at 2; total after cap = 2 + 3 legits = 5
    shill_tweets = [
        t for t in result.cleaned_tweets if t["author"]["userName"] == "shill"
    ]
    assert len(shill_tweets) <= 2
    # All 3 legit authors should survive
    legit_authors = {
        t["author"]["userName"]
        for t in result.cleaned_tweets
        if t["author"]["userName"].startswith("legit")
    }
    assert legit_authors == {"legit1", "legit2", "legit3"}


@pytest.mark.unit
def test_preprocess_dedup_keeps_higher_engagement_copy() -> None:
    tweets = [
        _tweet(user="low", followers=800, text="Gem spotted", likes=2, retweets=0),
        _tweet(user="high", followers=800, text="Gem spotted", likes=200, retweets=40),
    ]
    result = preprocess_tweets(tweets)
    # Kept one, dropped one
    assert len(result.cleaned_tweets) == 1
    assert result.cleaned_tweets[0]["author"]["userName"] == "high"


# ---------------------------------------------------------------------------
# Ranking + cap
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_preprocess_caps_to_max_returned_tweets() -> None:
    tweets = [
        _tweet(user=f"user{i}", followers=1_000, text=f"unique tweet body {i}", likes=i)
        for i in range(20)
    ]
    result = preprocess_tweets(tweets)
    assert len(result.cleaned_tweets) == MAX_RETURNED_TWEETS
    # Top tweets should be sorted desc by engagement
    engagements = [
        t["likeCount"] + 2 * t["retweetCount"] + t["replyCount"]
        for t in result.cleaned_tweets
    ]
    assert engagements == sorted(engagements, reverse=True)


@pytest.mark.unit
def test_preprocess_counts_influencers_and_verified() -> None:
    tweets = [
        _tweet(user="whale", followers=50_000, text="whale thesis on chain growth"),
        _tweet(user="blue", followers=2_000, verified=True, text="blue checkmark take"),
        _tweet(user="rand", followers=800, text="random trader opinion"),
    ]
    result = preprocess_tweets(tweets)
    assert result.influencer_count == 1
    assert result.verified_count == 1
    assert result.unique_authors == 3


@pytest.mark.unit
def test_preprocess_payload_passthrough_cursor_fields() -> None:
    payload = {
        "tweets": [_tweet(user="a", followers=1_000)],
        "has_next_page": True,
        "next_cursor": "abc123",
    }
    result = preprocess_twitter_payload(payload)
    assert result["has_next_page"] is True
    assert result["next_cursor"] == "abc123"
    assert "meta" in result
    assert result["status"] == "success"
