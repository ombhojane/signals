"""Unit tests for core.killswitch rules."""

from __future__ import annotations

import pytest

from core.factbook import MarketFactBook, RugFactBook, SocialFactBook, TokenFactBook
from core.killswitch import (
    KillSeverity,
    MAX_DEV_WALLET_PCT,
    MAX_TOP10_CONCENTRATION_PCT,
    MIN_LIQUIDITY_USD,
    check_killswitch,
)


def _make_factbook(
    *,
    market: MarketFactBook | None = None,
    rug: RugFactBook | None = None,
) -> TokenFactBook:
    return TokenFactBook(
        token_address="TEST",
        chain="sol",
        market=market or MarketFactBook(has_data=True, liquidity_usd=100_000),
        rug=rug or RugFactBook(has_data=True, liquidity_usd=100_000),
        social=SocialFactBook(),
    )


# ---------------------------------------------------------------------------
# Happy path: clean token should pass
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_killswitch_passes_clean_token() -> None:
    tfb = _make_factbook(
        rug=RugFactBook(
            has_data=True,
            overall_risk_score=15,
            is_honeypot=False,
            is_mintable=False,
            ownership_renounced=True,
            liquidity_locked=True,
            lock_days_remaining=180,
            liquidity_usd=250_000,
            top_10_holder_pct=25.0,
            dev_wallet_pct=3.0,
        )
    )
    result = check_killswitch(tfb)
    assert result.triggered is False
    assert result.action == "PROCEED"
    assert result.primary is None


# ---------------------------------------------------------------------------
# Individual rules
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_killswitch_fires_on_honeypot() -> None:
    tfb = _make_factbook(
        rug=RugFactBook(has_data=True, is_honeypot=True, liquidity_usd=100_000)
    )
    result = check_killswitch(tfb)
    assert result.triggered is True
    assert result.action == "AVOID"
    assert result.primary.rule == "HONEYPOT_DETECTED"
    assert result.primary.severity is KillSeverity.CRITICAL


@pytest.mark.unit
def test_killswitch_fires_on_insufficient_liquidity() -> None:
    tfb = _make_factbook(
        market=MarketFactBook(has_data=True, liquidity_usd=500.0),
        rug=RugFactBook(has_data=True, liquidity_usd=500.0),
    )
    result = check_killswitch(tfb)
    assert result.triggered is True
    assert result.primary.rule == "INSUFFICIENT_LIQUIDITY"
    assert result.primary.evidence["liquidity_usd"] == 500.0


@pytest.mark.unit
def test_killswitch_ignores_zero_liquidity_to_avoid_false_positive() -> None:
    # liquidity 0 means "unknown", not "< floor"
    tfb = _make_factbook(
        market=MarketFactBook(has_data=True, liquidity_usd=0.0),
        rug=RugFactBook(has_data=True, liquidity_usd=0.0),
    )
    result = check_killswitch(tfb)
    # Unknown liquidity should not fire the liquidity rule
    rules = [r.rule for r in result.reasons]
    assert "INSUFFICIENT_LIQUIDITY" not in rules


@pytest.mark.unit
def test_killswitch_fires_on_sybil_concentration() -> None:
    tfb = _make_factbook(
        rug=RugFactBook(
            has_data=True,
            liquidity_usd=100_000,
            top_10_holder_pct=MAX_TOP10_CONCENTRATION_PCT + 1,
        )
    )
    result = check_killswitch(tfb)
    assert any(r.rule == "SYBIL_CONCENTRATION" for r in result.reasons)


@pytest.mark.unit
def test_killswitch_does_not_fire_at_concentration_threshold() -> None:
    # Equal to threshold → NOT fired (rule is strict >)
    tfb = _make_factbook(
        rug=RugFactBook(
            has_data=True,
            liquidity_usd=100_000,
            top_10_holder_pct=MAX_TOP10_CONCENTRATION_PCT,
        )
    )
    result = check_killswitch(tfb)
    assert not any(r.rule == "SYBIL_CONCENTRATION" for r in result.reasons)


@pytest.mark.unit
def test_killswitch_fires_on_unbounded_mint() -> None:
    tfb = _make_factbook(
        rug=RugFactBook(
            has_data=True,
            liquidity_usd=100_000,
            is_mintable=True,
            ownership_renounced=False,
            unbounded_mint_flag=True,
        )
    )
    result = check_killswitch(tfb)
    assert any(r.rule == "UNBOUNDED_MINT" for r in result.reasons)


@pytest.mark.unit
def test_killswitch_skips_mint_rule_when_renounced() -> None:
    tfb = _make_factbook(
        rug=RugFactBook(
            has_data=True,
            liquidity_usd=100_000,
            is_mintable=True,
            ownership_renounced=True,
            unbounded_mint_flag=False,
        )
    )
    result = check_killswitch(tfb)
    assert not any(r.rule == "UNBOUNDED_MINT" for r in result.reasons)


@pytest.mark.unit
def test_killswitch_fires_on_dev_wallet_dominance() -> None:
    tfb = _make_factbook(
        rug=RugFactBook(
            has_data=True,
            liquidity_usd=100_000,
            dev_wallet_pct=MAX_DEV_WALLET_PCT + 5,
        )
    )
    result = check_killswitch(tfb)
    assert any(r.rule == "DEV_WALLET_DOMINANT" for r in result.reasons)


# ---------------------------------------------------------------------------
# Multi-rule firing — ensure all matching rules are surfaced
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_killswitch_collects_multiple_reasons() -> None:
    tfb = _make_factbook(
        market=MarketFactBook(has_data=True, liquidity_usd=500.0),
        rug=RugFactBook(
            has_data=True,
            is_honeypot=True,
            liquidity_usd=500.0,
            top_10_holder_pct=95,
            dev_wallet_pct=60,
        ),
    )
    result = check_killswitch(tfb)
    rules = {r.rule for r in result.reasons}
    assert "HONEYPOT_DETECTED" in rules
    assert "INSUFFICIENT_LIQUIDITY" in rules
    assert "SYBIL_CONCENTRATION" in rules
    assert "DEV_WALLET_DOMINANT" in rules
    # Honeypot should be first (highest certainty rule)
    assert result.primary.rule == "HONEYPOT_DETECTED"


@pytest.mark.unit
def test_killswitch_result_to_dict_is_serializable() -> None:
    tfb = _make_factbook(
        rug=RugFactBook(has_data=True, is_honeypot=True, liquidity_usd=100_000)
    )
    d = check_killswitch(tfb).to_dict()
    assert d["triggered"] is True
    assert d["action"] == "AVOID"
    assert d["reasons"][0]["rule"] == "HONEYPOT_DETECTED"
    assert d["reasons"][0]["severity"] == "CRITICAL"
