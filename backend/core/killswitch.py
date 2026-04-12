"""
Deterministic kill-switch — Stage 1 of the enhanced AI pipeline.

Before any LLM is called, we apply a small set of hard rules that reliably
identify tokens so dangerous that no amount of LLM reasoning would rescue
them. If any rule fires, the pipeline short-circuits to AVOID with the
triggering rule cited as evidence. This saves money (no LLM calls on obvious
scams) and removes a hallucination surface (LLM cannot "talk itself into"
a HOLD on a honeypot).

The rules are intentionally conservative — false negatives (letting a scam
through) are acceptable here because the LLM pipeline still runs behind them
and can catch subtler signals. False positives (blocking a legit token) are
the real risk, so every rule must fire only on strong, numerically verifiable
evidence.

Reference: RPHunter (arxiv 2506.18398) shows hybrid rule + ML pipelines
achieve 94.5 F1 on rug detection — significantly beating either approach
alone.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from core.factbook import RugFactBook, MarketFactBook, TokenFactBook


class KillSeverity(str, Enum):
    """How severe a kill-switch trigger is."""

    CRITICAL = "CRITICAL"  # immediate AVOID, no further analysis
    HIGH = "HIGH"  # AVOID with caveat, still log features


@dataclass(frozen=True)
class KillReason:
    """A single fired kill-switch rule with its evidence."""

    rule: str  # short rule id (e.g., "HONEYPOT_DETECTED")
    severity: KillSeverity
    message: str  # human-readable explanation
    evidence: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule": self.rule,
            "severity": self.severity.value,
            "message": self.message,
            "evidence": dict(self.evidence),
        }


@dataclass(frozen=True)
class KillSwitchResult:
    """Result of running the kill-switch against a FactBook."""

    triggered: bool
    action: str  # "AVOID" if triggered, "PROCEED" otherwise
    reasons: tuple  # tuple[KillReason, ...]

    @property
    def primary(self) -> Optional[KillReason]:
        return self.reasons[0] if self.reasons else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "triggered": self.triggered,
            "action": self.action,
            "reasons": [r.to_dict() for r in self.reasons],
        }


# ---------------------------------------------------------------------------
# Thresholds — tuned conservative. Tune against the eval harness in Step 13.
# ---------------------------------------------------------------------------

MIN_LIQUIDITY_USD = 1_000.0
MAX_TOP10_CONCENTRATION_PCT = 90.0
MAX_DEV_WALLET_PCT = 50.0


# ---------------------------------------------------------------------------
# Individual rules — each takes the relevant FactBook slice and returns an
# Optional[KillReason]. Rules are pure functions and independently unit-tested.
# ---------------------------------------------------------------------------


def _rule_honeypot(rug: RugFactBook) -> Optional[KillReason]:
    if rug.is_honeypot is True:
        return KillReason(
            rule="HONEYPOT_DETECTED",
            severity=KillSeverity.CRITICAL,
            message=(
                "Token is flagged as a honeypot by upstream safety providers. "
                "Buys succeed but sells revert — do not engage."
            ),
            evidence={"is_honeypot": True},
        )
    return None


def _rule_insufficient_liquidity(
    rug: RugFactBook, market: MarketFactBook
) -> Optional[KillReason]:
    # Prefer DEX-reported liquidity (fresher), fall back to safety-report liquidity.
    liq = market.liquidity_usd if market.liquidity_usd > 0 else rug.liquidity_usd
    if liq > 0 and liq < MIN_LIQUIDITY_USD:
        return KillReason(
            rule="INSUFFICIENT_LIQUIDITY",
            severity=KillSeverity.CRITICAL,
            message=(
                f"Liquidity is ${liq:,.0f}, below the minimum safe floor of "
                f"${MIN_LIQUIDITY_USD:,.0f}. Slippage on exit will be catastrophic."
            ),
            evidence={"liquidity_usd": liq, "floor_usd": MIN_LIQUIDITY_USD},
        )
    return None


def _rule_sybil_concentration(rug: RugFactBook) -> Optional[KillReason]:
    if rug.top_10_holder_pct > MAX_TOP10_CONCENTRATION_PCT:
        return KillReason(
            rule="SYBIL_CONCENTRATION",
            severity=KillSeverity.CRITICAL,
            message=(
                f"Top 10 holders control {rug.top_10_holder_pct:.1f}% of supply "
                f"(threshold: {MAX_TOP10_CONCENTRATION_PCT:.0f}%). "
                "Any one of them can rug at will."
            ),
            evidence={
                "top_10_holder_pct": rug.top_10_holder_pct,
                "threshold": MAX_TOP10_CONCENTRATION_PCT,
            },
        )
    return None


def _rule_unbounded_mint(rug: RugFactBook) -> Optional[KillReason]:
    if rug.unbounded_mint_flag:
        return KillReason(
            rule="UNBOUNDED_MINT",
            severity=KillSeverity.CRITICAL,
            message=(
                "Contract is mintable AND ownership has not been renounced. "
                "Creator can print arbitrary supply — dilution rug is always possible."
            ),
            evidence={
                "is_mintable": rug.is_mintable,
                "ownership_renounced": rug.ownership_renounced,
            },
        )
    return None


def _rule_dev_wallet_dominant(rug: RugFactBook) -> Optional[KillReason]:
    if rug.dev_wallet_pct > MAX_DEV_WALLET_PCT:
        return KillReason(
            rule="DEV_WALLET_DOMINANT",
            severity=KillSeverity.CRITICAL,
            message=(
                f"Dev wallet holds {rug.dev_wallet_pct:.1f}% of supply "
                f"(threshold: {MAX_DEV_WALLET_PCT:.0f}%). "
                "Deployer can single-handedly dump the market."
            ),
            evidence={
                "dev_wallet_pct": rug.dev_wallet_pct,
                "threshold": MAX_DEV_WALLET_PCT,
            },
        )
    return None


# Ordered by severity / certainty. Honeypot is most decisive, so it runs first.
_RULES = (
    ("honeypot", _rule_honeypot),
    ("liquidity", _rule_insufficient_liquidity),
    ("sybil", _rule_sybil_concentration),
    ("mint", _rule_unbounded_mint),
    ("dev_wallet", _rule_dev_wallet_dominant),
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_killswitch(factbook: TokenFactBook) -> KillSwitchResult:
    """Run all kill-switch rules against a TokenFactBook.

    Returns a KillSwitchResult with all triggered reasons (not just the first).
    Callers can short-circuit on result.triggered and use result.primary for
    a single explanation to return to the user.
    """
    rug = factbook.rug
    market = factbook.market

    reasons: List[KillReason] = []

    # Run each rule; skip rules that need arguments we can't satisfy.
    for name, rule in _RULES:
        if name == "liquidity":
            hit = rule(rug, market)
        else:
            hit = rule(rug)
        if hit is not None:
            reasons.append(hit)

    triggered = len(reasons) > 0
    return KillSwitchResult(
        triggered=triggered,
        action="AVOID" if triggered else "PROCEED",
        reasons=tuple(reasons),
    )
