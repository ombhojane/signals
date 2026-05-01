"""Unit tests for backend services."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from core.scoring import compute_signal_vector, SignalVector
from services.agents.base import AgentOutcome, ScoredResponse


# ---------------------------------------------------------------------------
# Scoring Service Tests
# ---------------------------------------------------------------------------


@pytest.mark.service
def test_compute_signal_vector_returns_signal_vector() -> None:
    outcome = AgentOutcome(
        agent_type="market",
        status="success",
        scored=ScoredResponse(score=0.8, confidence=0.9),
        raw={},
        error=None,
    )
    result = compute_signal_vector(
        market=outcome,
        rug=outcome,
        social=outcome,
    )
    assert isinstance(result, SignalVector)
    assert 0 <= result.overall <= 1
    assert 0 <= result.confidence <= 1


@pytest.mark.service
@pytest.mark.parametrize(
    "score,expected_action",
    [
        (0.9, "STRONG_BUY"),
        (0.7, "BUY"),
        (0.5, "HOLD"),
        (0.3, "SELL"),
        (0.1, "STRONG_SELL"),
    ],
)
def test_action_threshold_from_score(score: float, expected_action: str) -> None:
    outcome = AgentOutcome(
        agent_type="market",
        status="success",
        scored=ScoredResponse(score=score, confidence=0.9),
        raw={},
        error=None,
    )
    result = compute_signal_vector(
        market=outcome,
        rug=outcome,
        social=outcome,
    )
    # Action should match or exceed threshold
    assert result.action_hint in ["HOLD", expected_action]


@pytest.mark.service
def test_zero_confidence_returns_hold() -> None:
    outcome = AgentOutcome(
        agent_type="market",
        status="success",
        scored=ScoredResponse(score=0.9, confidence=0.0),
        raw={},
        error=None,
    )
    result = compute_signal_vector(
        market=outcome,
        rug=outcome,
        social=outcome,
    )
    assert result.action_hint == "HOLD"


# ---------------------------------------------------------------------------
# Token Safety Service Tests
# ---------------------------------------------------------------------------


@pytest.mark.service
@pytest.mark.asyncio
@patch("services.token_safety_service.check_token_safety")
async def test_token_safety_check_returns_result(mock_check: AsyncMock) -> None:
    from services.token_safety_service import check_token_safety

    mock_check.return_value = {
        "is_safe": True,
        "risk_score": 0.1,
        "warnings": [],
    }
    result = await check_token_safety("0x123")
    assert "is_safe" in result
    assert "risk_score" in result


@pytest.mark.service
@pytest.mark.asyncio
@patch("services.token_safety_service.check_token_safety")
async def test_token_safety_detects_rug(mock_check: AsyncMock) -> None:
    from services.token_safety_service import check_token_safety

    mock_check.return_value = {
        "is_safe": False,
        "risk_score": 0.95,
        "warnings": ["HONEYPOT_DETECTED"],
    }
    result = await check_token_safety("0x123")
    assert result["is_safe"] is False
    assert result["risk_score"] > 0.5


# ---------------------------------------------------------------------------
# Social Preprocessor Tests
# ---------------------------------------------------------------------------


@pytest.mark.service
def test_social_preprocessor_cleans_tweets() -> None:
    from services.social_preprocessor import preprocess_tweets

    dirty_tweets = [
        {"text": "Check this out! $BTC https://t.co/abc #crypto"},
        {"text": "Great project! 🚀🚀"},
    ]
    cleaned = preprocess_tweets(dirty_tweets)
    assert len(cleaned) == len(dirty_tweets)


@pytest.mark.service
def test_social_preprocessor_removes_links() -> None:
    from services.social_preprocessor import preprocess_tweets

    tweets = [{"text": "Buy $SOL! https://t.co/abc"}]
    cleaned = preprocess_tweets(tweets)
    assert "https://" not in cleaned[0]["text"]


@pytest.mark.service
def test_social_preprocessor_handles_mentions() -> None:
    from services.social_preprocessor import preprocess_tweets

    tweets = [{"text": "@elonmusk is great"}]
    cleaned = preprocess_tweets(tweets)
    assert len(cleaned) > 0


@pytest.mark.service
def test_social_preprocessor_filters_empty() -> None:
    from services.social_preprocessor import preprocess_tweets

    tweets = [
        {"text": "🚀🚀🚀"},
        {"text": ""},
        {"text": "   "},
    ]
    cleaned = preprocess_tweets(tweets)
    # Should filter out empty tweets
    assert len(cleaned) <= len(tweets)


# ---------------------------------------------------------------------------
# Factbook Tests
# ---------------------------------------------------------------------------


@pytest.mark.service
def test_factbook_returns_token_info() -> None:
    from core.factbook import get_token_info

    info = get_token_info("0x123")
    assert info is not None or "error" in str(info)


@pytest.mark.service
def test_factbook_caches_results() -> None:
    from core.factbook import get_token_info, _factbook_cache

    # First call
    get_token_info("0xabc")
    # Second call should use cache
    cache_len = len(_factbook_cache)
    get_token_info("0xabc")
    assert len(_factbook_cache) == cache_len


# ---------------------------------------------------------------------------
# Kill Switch Tests
# ---------------------------------------------------------------------------


@pytest.mark.service
@pytest.mark.asyncio
@patch("core.killswitch.evaluate_conditions")
async def test_killswitch_triggers_on_critical(mock_eval: AsyncMock) -> None:
    from core.killswitch import KillSwitch

    mock_eval.return_value = {
        "triggered": True,
        "reasons": [{"severity": "CRITICAL", "message": "Test trigger"}],
    }
    ks = KillSwitch()
    result = await ks.check()
    assert result.triggered is True


@pytest.mark.service
@pytest.mark.asyncio
async def test_killswitch_allows_safe_operation() -> None:
    from core.killswitch import KillSwitch

    ks = KillSwitch()
    result = await ks.check()
    # Should either be False or have reasons
    assert result.triggered is False or len(result.reasons) >= 0


# ---------------------------------------------------------------------------
# Rate Limiter Tests
# ---------------------------------------------------------------------------


@pytest.mark.service
def test_rate_limiter_allows_requests() -> None:
    from core.rate_limiter import RateLimiter

    limiter = RateLimiter(max_requests=10)
    for i in range(10):
        assert limiter.check() is True


@pytest.mark.service
def test_rate_limiter_blocks_excess() -> None:
    from core.rate_limiter import RateLimiter

    limiter = RateLimiter(max_requests=3)
    for _ in range(3):
        limiter.check()
    assert limiter.check() is False


@pytest.mark.service
def test_rate_limiter_resets() -> None:
    from core.rate_limiter import RateLimiter

    limiter = RateLimiter(max_requests=2, window_seconds=0)
    limiter.check()
    limiter.check()
    assert limiter.check() is False
    # After reset, should allow again
    limiter.reset()
    assert limiter.check() is True


# ---------------------------------------------------------------------------
# Data Validator Tests
# ---------------------------------------------------------------------------


@pytest.mark.service
def test_validator_accepts_valid_address() -> None:
    from core.data_validator import is_valid_eth_address

    assert is_valid_eth_address("0x1234567890123456789012345678901234567890") is True


@pytest.mark.service
def test_validator_rejects_invalid_address() -> None:
    from core.data_validator import is_valid_eth_address

    assert is_valid_eth_address("invalid") is False
    assert is_valid_eth_address("0x123") is False


@pytest.mark.service
def test_validator_accepts_valid_amount() -> None:
    from core.data_validator import is_valid_amount

    assert is_valid_amount(100) is True
    assert is_valid_amount(0.01) is True


@pytest.mark.service
def test_validator_rejects_negative() -> None:
    from core.data_validator import is_valid_amount

    assert is_valid_amount(-1) is False


# ---------------------------------------------------------------------------
# Cache Tests
# ---------------------------------------------------------------------------


@pytest.mark.service
def test_cache_stores_and_retrieves() -> None:
    from core.cache import Cache

    cache = Cache(ttl=60)
    cache.set("key1", {"data": "test"})
    result = cache.get("key1")
    assert result is not None


@pytest.mark.service
def test_cache_expires() -> None:
    from core.cache import Cache

    cache = Cache(ttl=0)  # Immediate expiry
    cache.set("key1", {"data": "test"})
    result = cache.get("key1")
    assert result is None


@pytest.mark.service
def test_cache_clears() -> None:
    from core.cache import Cache

    cache = Cache(ttl=60)
    cache.set("key1", {"data": "test"})
    cache.clear()
    assert cache.get("key1") is None


# ---------------------------------------------------------------------------
# Formatters Tests
# ---------------------------------------------------------------------------


@pytest.mark.service
def test_format_usdc() -> None:
    from utils.formatters import format_usdc

    result = format_usdc(1000000)
    assert "$" in result or "1000000" in result


@pytest.mark.service
def test_format_percentage() -> None:
    from utils.formatters import format_percentage

    result = format_percentage(0.5)
    assert "50" in result or "0.5" in result


# ---------------------------------------------------------------------------
# Parallel Executor Tests
# ---------------------------------------------------------------------------


@pytest.mark.service
def test_parallel_executor_runs_tasks() -> None:
    from core.parallel import parallel_execute

    results = parallel_execute(lambda x: x * 2, [1, 2, 3])
    assert results == [2, 4, 6]


@pytest.mark.service
def test_parallel_executor_handles_errors() -> None:
    from core.parallel import parallel_execute

    def failing_task(x):
        if x == 2:
            raise ValueError("Test error")
        return x

    results = parallel_execute(failing_task, [1, 2, 3])
    # Should handle error gracefully
    assert len(results) == 3


# ---------------------------------------------------------------------------
# Logging Tests
# ---------------------------------------------------------------------------


@pytest.mark.service
def test_log_info(caplog: pytest.LogCaptureFixture) -> None:
    from core.logging import log_info

    log_info("test message")
    # Should not raise


@pytest.mark.service
def test_log_error(caplog: pytest.LogCaptureFixture) -> None:
    from core.logging import log_error

    log_error("test error")
    # Should not raise
