"""Unit tests for core.scoring — the weighted scoring module."""

from __future__ import annotations

from typing import Tuple

import pytest

from core.killswitch import (
    KillReason,
    KillSeverity,
    KillSwitchResult,
)
from core.scoring import (
    DEFAULT_WEIGHTS,
    SignalVector,
    _action_from_signal,
    _collect_warnings,
    compute_signal_vector,
)
from services.agents.base import AgentOutcome, ScoredResponse


# ---------------------------------------------------------------------------
# Test fixtures
# ---------------------------------------------------------------------------


def _outcome(
    agent_type: str,
    score: float,
    confidence: float,
    red_flags: Tuple[str, ...] = (),
) -> AgentOutcome:
    return AgentOutcome(
        agent_type=agent_type,
        status="success",
        scored=ScoredResponse(score=score, confidence=confidence, red_flags=red_flags),
        raw={"score": score, "confidence": confidence},
        error=None,
    )


def _killswitch(triggered: bool = False, rule: str = "") -> KillSwitchResult:
    reasons = ()
    if triggered:
        reasons = (
            KillReason(
                rule=rule or "TEST_RULE",
                severity=KillSeverity.CRITICAL,
                message="test",
                evidence={},
            ),
        )
    return KillSwitchResult(
        triggered=triggered,
        action="AVOID" if triggered else "PROCEED",
        reasons=reasons,
    )


# ---------------------------------------------------------------------------
# Weight invariants
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_default_weights_sum_to_one() -> None:
    assert abs(sum(DEFAULT_WEIGHTS) - 1.0) < 1e-9


@pytest.mark.unit
def test_rug_weight_is_highest_of_the_three() -> None:
    # Rug should dominate because false-negatives on safety are catastrophic
    assert DEFAULT_WEIGHTS[1] > DEFAULT_WEIGHTS[0]
    assert DEFAULT_WEIGHTS[1] > DEFAULT_WEIGHTS[2]


# ---------------------------------------------------------------------------
# Happy-path scoring
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_compute_signal_vector_clean_token() -> None:
    sv = compute_signal_vector(
        market=_outcome("market", score=0.80, confidence=0.90),
        rug=_outcome("rug", score=0.90, confidence=0.80),
        social=_outcome("social", score=0.70, confidence=0.70),
    )
    assert isinstance(sv, SignalVector)
    # Combined overall should be a weighted blend close to rug (highest weight)
    assert 0.75 <= sv.overall <= 0.90
    # Combined confidence is the mean
    assert abs(sv.confidence - (0.9 + 0.8 + 0.7) / 3) < 0.01
    assert sv.killswitch_triggered is False
    assert sv.action_hint in {"BUY", "STRONG_BUY"}


@pytest.mark.unit
def test_compute_signal_vector_scam_token() -> None:
    sv = compute_signal_vector(
        market=_outcome("market", score=0.20, confidence=0.80),
        rug=_outcome("rug", score=0.05, confidence=0.90),
        social=_outcome("social", score=0.10, confidence=0.70),
    )
    assert sv.overall < 0.20
    # Rug veto should fire — score < 0.30 with confidence ≥ 0.50
    assert sv.action_hint == "STRONG_SELL"


# ---------------------------------------------------------------------------
# Confidence-adjusted weighting
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_low_confidence_agent_contributes_less() -> None:
    # Rug agent is very negative but low confidence — effective weight should shrink
    sv_low_conf = compute_signal_vector(
        market=_outcome("market", score=0.80, confidence=0.90),
        rug=_outcome("rug", score=0.10, confidence=0.10),  # low confidence
        social=_outcome("social", score=0.70, confidence=0.80),
    )
    sv_high_conf = compute_signal_vector(
        market=_outcome("market", score=0.80, confidence=0.90),
        rug=_outcome("rug", score=0.10, confidence=0.90),  # high confidence
        social=_outcome("social", score=0.70, confidence=0.80),
    )
    # High-confidence rug should pull overall down much more than low-confidence
    assert sv_high_conf.overall < sv_low_conf.overall


@pytest.mark.unit
def test_zero_confidence_all_agents_degenerate_case() -> None:
    sv = compute_signal_vector(
        market=_outcome("market", score=0.8, confidence=0.0),
        rug=_outcome("rug", score=0.2, confidence=0.0),
        social=_outcome("social", score=0.5, confidence=0.0),
    )
    # Combined confidence should be exactly 0
    assert sv.confidence == 0.0
    # Action must be HOLD (insufficient data)
    assert sv.action_hint == "HOLD"


@pytest.mark.unit
def test_effective_weights_sum_to_one() -> None:
    sv = compute_signal_vector(
        market=_outcome("market", score=0.5, confidence=0.6),
        rug=_outcome("rug", score=0.5, confidence=0.8),
        social=_outcome("social", score=0.5, confidence=0.4),
    )
    assert abs(sum(sv.effective_weights) - 1.0) < 1e-9


# ---------------------------------------------------------------------------
# Kill-switch dominance
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_killswitch_forces_strong_sell_regardless_of_scores() -> None:
    sv = compute_signal_vector(
        # Even with all agents saying "great!"
        market=_outcome("market", score=0.95, confidence=0.95),
        rug=_outcome("rug", score=0.95, confidence=0.95),
        social=_outcome("social", score=0.95, confidence=0.95),
        killswitch=_killswitch(triggered=True, rule="HONEYPOT_DETECTED"),
    )
    assert sv.killswitch_triggered is True
    assert sv.overall == 0.0
    assert sv.action_hint == "STRONG_SELL"
    assert sv.confidence >= 0.95


@pytest.mark.unit
def test_killswitch_warning_includes_primary_rule() -> None:
    sv = compute_signal_vector(
        market=_outcome("market", score=0.5, confidence=0.5),
        rug=_outcome("rug", score=0.5, confidence=0.5),
        social=_outcome("social", score=0.5, confidence=0.5),
        killswitch=_killswitch(triggered=True, rule="HONEYPOT_DETECTED"),
    )
    assert any("HONEYPOT_DETECTED" in w for w in sv.warnings)


# ---------------------------------------------------------------------------
# Action hint rules
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_insufficient_confidence_returns_hold() -> None:
    sv = compute_signal_vector(
        market=_outcome("market", score=0.90, confidence=0.20),
        rug=_outcome("rug", score=0.90, confidence=0.20),
        social=_outcome("social", score=0.90, confidence=0.20),
    )
    # Combined confidence = 0.20 < 0.40 → HOLD regardless of scores
    assert sv.action_hint == "HOLD"


@pytest.mark.unit
def test_safety_veto_fires_even_with_strong_market() -> None:
    sv = compute_signal_vector(
        market=_outcome("market", score=0.95, confidence=0.95),
        rug=_outcome("rug", score=0.10, confidence=0.80),
        social=_outcome("social", score=0.95, confidence=0.95),
    )
    # Rug < 0.30 with confidence ≥ 0.50 → STRONG_SELL
    assert sv.action_hint == "STRONG_SELL"


@pytest.mark.unit
def test_borderline_safety_goes_to_sell_not_strong_sell() -> None:
    sv = compute_signal_vector(
        market=_outcome("market", score=0.40, confidence=0.80),
        rug=_outcome("rug", score=0.35, confidence=0.80),
        social=_outcome("social", score=0.40, confidence=0.80),
    )
    # Rug < 0.50 with conf ≥ 0.60 AND overall < 0.50 → SELL
    assert sv.action_hint == "SELL"


@pytest.mark.unit
def test_strong_buy_requires_high_overall() -> None:
    sv = compute_signal_vector(
        market=_outcome("market", score=0.85, confidence=0.90),
        rug=_outcome("rug", score=0.85, confidence=0.90),
        social=_outcome("social", score=0.85, confidence=0.90),
    )
    assert sv.action_hint == "STRONG_BUY"


# ---------------------------------------------------------------------------
# Warnings
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_market_masking_safety_warning() -> None:
    sv = compute_signal_vector(
        market=_outcome("market", score=0.85, confidence=0.90),
        rug=_outcome("rug", score=0.40, confidence=0.80),  # low safety, high conf
        social=_outcome("social", score=0.60, confidence=0.60),
    )
    assert "MARKET_MASKING_SAFETY_RISK" in sv.warnings


@pytest.mark.unit
def test_low_confidence_all_agents_warning() -> None:
    sv = compute_signal_vector(
        market=_outcome("market", score=0.5, confidence=0.20),
        rug=_outcome("rug", score=0.5, confidence=0.30),
        social=_outcome("social", score=0.5, confidence=0.10),
    )
    assert "LOW_CONFIDENCE_ALL_AGENTS" in sv.warnings


@pytest.mark.unit
def test_safety_inconclusive_warning() -> None:
    sv = compute_signal_vector(
        market=_outcome("market", score=0.6, confidence=0.8),
        rug=_outcome("rug", score=0.55, confidence=0.40),  # borderline + low conf
        social=_outcome("social", score=0.6, confidence=0.8),
    )
    assert "SAFETY_INCONCLUSIVE" in sv.warnings


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_signal_vector_to_dict_is_serializable() -> None:
    import json

    sv = compute_signal_vector(
        market=_outcome("market", score=0.6, confidence=0.7),
        rug=_outcome("rug", score=0.5, confidence=0.6),
        social=_outcome("social", score=0.4, confidence=0.5),
    )
    d = sv.to_dict()
    # Round-trip through JSON
    json.dumps(d)
    assert "overall" in d
    assert "action_hint" in d
    assert "warnings" in d


@pytest.mark.unit
def test_load_weights_falls_back_to_defaults_when_file_missing(tmp_path, monkeypatch) -> None:
    """load_weights should degrade gracefully if the weights file doesn't exist."""
    from core import scoring

    monkeypatch.setattr(scoring, "_WEIGHTS_PATH", tmp_path / "nonexistent.json")
    assert scoring.load_weights() == scoring.DEFAULT_WEIGHTS


@pytest.mark.unit
def test_save_and_load_weights_round_trip(tmp_path, monkeypatch) -> None:
    from core import scoring

    monkeypatch.setattr(scoring, "_WEIGHTS_PATH", tmp_path / "weights.json")
    scoring.save_weights((0.30, 0.50, 0.20))
    loaded = scoring.load_weights()
    assert abs(loaded[0] - 0.30) < 1e-9
    assert abs(loaded[1] - 0.50) < 1e-9
    assert abs(loaded[2] - 0.20) < 1e-9


@pytest.mark.unit
def test_load_weights_renormalizes_unnormalized_values(tmp_path, monkeypatch) -> None:
    """Calibrator may write unnormalized weights; load_weights should normalize them."""
    import json as _json
    from core import scoring

    path = tmp_path / "weights.json"
    path.write_text(_json.dumps({"market": 2.0, "rug": 4.0, "social": 2.0}))
    monkeypatch.setattr(scoring, "_WEIGHTS_PATH", path)
    loaded = scoring.load_weights()
    assert abs(sum(loaded) - 1.0) < 1e-9
    assert abs(loaded[0] - 0.25) < 1e-9
    assert abs(loaded[1] - 0.50) < 1e-9
    assert abs(loaded[2] - 0.25) < 1e-9
