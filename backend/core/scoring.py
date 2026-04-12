"""
Scoring module — Stage 3 of the enhanced AI pipeline.

Takes the three worker agent outcomes (Market / RugCheck / Social) plus the
kill-switch result and produces a single calibrated `SignalVector` that the
Prediction agent consumes.

Design decisions (confirmed by the user):

1. **Static prior weights** for the three agents:
       market = 0.35
       rug    = 0.40   ← highest, because false positives on safety are catastrophic
       social = 0.25

2. **Confidence-adjusted effective weights.** An agent that reports low
   confidence should contribute less to the final signal than one that is
   sure. We multiply the static weight by the agent's self-reported
   confidence and re-normalize. This is a proper soft-weighting scheme —
   see "Revisiting Ensemble Methods for Crypto Trading" (arxiv 2501.10709)
   for the same pattern applied to validation precision.

3. **No PCA.** The arch diagram labels this module "PCA" but with only three
   inputs, PCA would just be a rotated basis of the same space — it doesn't
   compress anything. A weighted soft-vote is simpler, more interpretable,
   and preserves the dimensions for downstream explainability.

4. **Kill-switch dominates.** If the kill-switch triggered, `overall` is
   forced to 0.0 and `action_hint = STRONG_SELL` regardless of LLM outputs.

5. **Calibration hook.** `DEFAULT_WEIGHTS` is a module constant; Step 12's
   isotonic calibrator can overwrite it at runtime by rewriting
   `data/scoring_weights.json`, which `load_weights()` picks up.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from core.killswitch import KillSwitchResult
from core.logging import logger
from services.agents.base import AgentOutcome


# Prior weights confirmed in the v1 plan. Rug is highest because safety
# false-negatives are catastrophic; social is lowest because the data is
# noisy and easily gamed.
DEFAULT_WEIGHTS: Tuple[float, float, float] = (0.35, 0.40, 0.25)
assert abs(sum(DEFAULT_WEIGHTS) - 1.0) < 1e-9, "weights must sum to 1.0"

# Where persisted (calibrator-updated) weights live.
_WEIGHTS_PATH = Path(os.getenv("SCORING_WEIGHTS_PATH", "data/scoring_weights.json"))


# ---------------------------------------------------------------------------
# SignalVector — the compact output the Prediction agent consumes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SignalVector:
    """Calibrated 3-component score vector + combined signal.

    All score fields are in [0, 1] where 1 = best. For `rug` that means
    "safest" (not "riskiest") — consistent with how the agents report.
    """

    # Raw per-agent scores (after LLM clamping, before weight combination)
    market: float
    rug: float
    social: float

    # Per-agent self-reported confidences
    market_confidence: float
    rug_confidence: float
    social_confidence: float

    # Combined signal
    overall: float          # weighted combination in [0, 1]
    confidence: float       # combined confidence in [0, 1]

    # Weights actually used this call (static prior, not confidence-adjusted)
    weights: Tuple[float, float, float]
    # Confidence-adjusted normalized weights that produced `overall`
    effective_weights: Tuple[float, float, float]

    # Synthesis
    warnings: Tuple[str, ...]
    action_hint: str        # STRONG_BUY / BUY / HOLD / SELL / STRONG_SELL
    killswitch_triggered: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "market": round(self.market, 4),
            "rug": round(self.rug, 4),
            "social": round(self.social, 4),
            "market_confidence": round(self.market_confidence, 4),
            "rug_confidence": round(self.rug_confidence, 4),
            "social_confidence": round(self.social_confidence, 4),
            "overall": round(self.overall, 4),
            "confidence": round(self.confidence, 4),
            "weights": list(self.weights),
            "effective_weights": [round(w, 4) for w in self.effective_weights],
            "warnings": list(self.warnings),
            "action_hint": self.action_hint,
            "killswitch_triggered": self.killswitch_triggered,
        }


# ---------------------------------------------------------------------------
# Weights persistence — Step 12 calibrator writes to this file
# ---------------------------------------------------------------------------


def load_weights() -> Tuple[float, float, float]:
    """Load the scoring weights. Falls back to `DEFAULT_WEIGHTS`.

    The calibrator (Step 12) can overwrite `data/scoring_weights.json` to
    replace these at runtime without redeploying code. We re-read on every
    call because hackathon scope; production would cache + hot-reload.
    """
    if not _WEIGHTS_PATH.exists():
        return DEFAULT_WEIGHTS
    try:
        raw = json.loads(_WEIGHTS_PATH.read_text(encoding="utf-8"))
        w = (
            float(raw["market"]),
            float(raw["rug"]),
            float(raw["social"]),
        )
        total = sum(w)
        if total <= 0:
            return DEFAULT_WEIGHTS
        # Renormalize in case the calibrator wrote unnormalized values
        return (w[0] / total, w[1] / total, w[2] / total)
    except (json.JSONDecodeError, KeyError, ValueError, OSError) as exc:
        logger.warning(f"Failed to load scoring weights: {exc}. Using defaults.")
        return DEFAULT_WEIGHTS


def save_weights(weights: Tuple[float, float, float]) -> None:
    """Persist learned weights. Called by the Step 12 calibrator."""
    _WEIGHTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "market": float(weights[0]),
        "rug": float(weights[1]),
        "social": float(weights[2]),
    }
    _WEIGHTS_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Core scoring function
# ---------------------------------------------------------------------------


def compute_signal_vector(
    *,
    market: AgentOutcome,
    rug: AgentOutcome,
    social: AgentOutcome,
    killswitch: Optional[KillSwitchResult] = None,
    weights: Optional[Tuple[float, float, float]] = None,
) -> SignalVector:
    """Combine three agent outcomes into a SignalVector.

    Confidence-adjusted soft-weighting:
        eff_i = w_i * conf_i
        norm_i = eff_i / sum(eff)
        overall = sum(score_i * norm_i)

    If all three effective weights are zero (all agents failed / unknown),
    we fall back to the uniform prior `weights` and report neutral 0.5
    with confidence 0.0 — the Prediction agent's INSUFFICIENT DATA rule
    will then dominate.
    """
    w = weights if weights is not None else load_weights()
    w_m, w_r, w_s = w

    s_m = market.scored.score
    s_r = rug.scored.score
    s_s = social.scored.score

    c_m = market.scored.confidence
    c_r = rug.scored.confidence
    c_s = social.scored.confidence

    eff_m = w_m * c_m
    eff_r = w_r * c_r
    eff_s = w_s * c_s
    total_eff = eff_m + eff_r + eff_s

    if total_eff <= 0:
        # Degenerate: every agent reported zero confidence. Fall back to raw
        # priors on the scores and report near-zero combined confidence so
        # the Prediction agent defaults to HOLD.
        norm = w
        overall = w_m * s_m + w_r * s_r + w_s * s_s
        combined_conf = 0.0
    else:
        norm = (eff_m / total_eff, eff_r / total_eff, eff_s / total_eff)
        overall = norm[0] * s_m + norm[1] * s_r + norm[2] * s_s
        # Combined confidence = mean of individual confidences (not a weighted
        # metric — it represents how sure we are overall, not how sure any
        # single agent is). This is what the prediction agent uses for its
        # INSUFFICIENT DATA rule.
        combined_conf = (c_m + c_r + c_s) / 3.0

    # Kill-switch dominates everything.
    ks_triggered = bool(killswitch and killswitch.triggered)
    if ks_triggered:
        overall = 0.0
        combined_conf = 0.99

    warnings = _collect_warnings(
        s_m=s_m,
        s_r=s_r,
        s_s=s_s,
        c_m=c_m,
        c_r=c_r,
        c_s=c_s,
        killswitch=killswitch,
    )

    action = _action_from_signal(
        overall=overall,
        combined_conf=combined_conf,
        s_r=s_r,
        c_r=c_r,
        ks_triggered=ks_triggered,
    )

    return SignalVector(
        market=s_m,
        rug=s_r,
        social=s_s,
        market_confidence=c_m,
        rug_confidence=c_r,
        social_confidence=c_s,
        overall=round(overall, 4),
        confidence=round(combined_conf, 4),
        weights=w,
        effective_weights=norm,
        warnings=tuple(warnings),
        action_hint=action,
        killswitch_triggered=ks_triggered,
    )


# ---------------------------------------------------------------------------
# Helpers — warnings and action derivation
# ---------------------------------------------------------------------------


def _collect_warnings(
    *,
    s_m: float,
    s_r: float,
    s_s: float,
    c_m: float,
    c_r: float,
    c_s: float,
    killswitch: Optional[KillSwitchResult],
) -> list:
    """Cross-pattern warnings that aren't visible to any single agent.

    These are not punitive penalties on the score — the prediction agent
    reads them as contextual hints. Calibration (Step 12) learns their
    real predictive weight from outcomes.
    """
    warnings = []

    # Pattern: market looks great but safety is questionable
    if s_m >= 0.70 and s_r <= 0.50 and c_r >= 0.50:
        warnings.append("MARKET_MASKING_SAFETY_RISK")

    # Pattern: strong negative social with confidence = coordinated FUD or real red flag
    if s_s <= 0.30 and c_s >= 0.60:
        warnings.append("NEGATIVE_SOCIAL_HIGH_CONFIDENCE")

    # Pattern: all three agents have low confidence — we genuinely don't know
    if c_m < 0.40 and c_r < 0.40 and c_s < 0.40:
        warnings.append("LOW_CONFIDENCE_ALL_AGENTS")

    # Pattern: safety is borderline — neither clean nor dirty
    if 0.40 <= s_r <= 0.60 and c_r < 0.50:
        warnings.append("SAFETY_INCONCLUSIVE")

    # Kill-switch primary reason — expose it to prediction for explanation
    if killswitch and killswitch.triggered and killswitch.primary:
        warnings.append(f"KILLSWITCH_{killswitch.primary.rule}")

    return warnings


def _action_from_signal(
    *,
    overall: float,
    combined_conf: float,
    s_r: float,
    c_r: float,
    ks_triggered: bool,
) -> str:
    """Deterministic mapping from the combined signal to an action hint.

    This is just a *hint* — the LLM Prediction agent makes the final call
    and may override based on the full worker outputs. The hint keeps the
    mapping explainable and lets the eval harness (Step 13) measure the
    pure-math decision quality separately from the LLM decision quality.
    """
    if ks_triggered:
        return "STRONG_SELL"

    # Insufficient data: don't take a position
    if combined_conf < 0.40:
        return "HOLD"

    # Safety veto — below 0.30 with confidence is always SELL
    if s_r < 0.30 and c_r >= 0.50:
        return "STRONG_SELL"
    if s_r < 0.50 and c_r >= 0.60 and overall < 0.50:
        return "SELL"

    if overall >= 0.75:
        return "STRONG_BUY"
    if overall >= 0.60:
        return "BUY"
    if overall <= 0.25:
        return "STRONG_SELL"
    if overall <= 0.40:
        return "SELL"
    return "HOLD"
