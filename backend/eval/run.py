"""
Eval harness — replays the enhanced pipeline against hand-picked cases and
reports aggregate metrics.

Usage (from D:\\elonmusk\\hackx\\backend):

    # First run: fetches live data for each case and caches to eval/snapshots/
    venv/Scripts/python.exe eval/run.py --refresh

    # Subsequent runs: replays from snapshots (deterministic, free, fast)
    venv/Scripts/python.exe eval/run.py

    # Refresh a single case
    venv/Scripts/python.exe eval/run.py --refresh --only hawk_tuah

    # Run a subset
    venv/Scripts/python.exe eval/run.py --only usdc_sol,bonk,hawk_tuah

Metrics computed:
    - Rug detection rate: fraction of rug/pump_and_dump cases where the
      pipeline returned SELL/STRONG_SELL or triggered the kill-switch
    - Legit pass rate: fraction of legit cases where the pipeline did NOT
      return SELL/STRONG_SELL
    - Kill-switch precision: of all kill-switch triggers, fraction that are
      actually rugs (higher is better; 1.0 = no false positives)
    - Per-label action distribution
    - Avg latency and avg LLM confidence per label
    - Brier-style score on the rug probability proxy (1 - signal.rug)

Outputs:
    - eval/reports/report_<timestamp>.md  — human-readable summary
    - eval/reports/latest.jsonl           — machine-readable per-case results
"""

from __future__ import annotations

import argparse
import asyncio
import io
import json
import sys
import time
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Make the backend package importable when running from eval/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from core.orchestrator import AnalysisResult, orchestrator  # noqa: E402
from services.dex_api import get_dex_data  # noqa: E402
from services.token_data_service import get_token_analysis  # noqa: E402
from services.token_safety_service import get_safety_report  # noqa: E402
from services.twitter_api_v2 import fetch_token_tweets  # noqa: E402
from core.constants import get_chain_id  # noqa: E402


EVAL_DIR = Path(__file__).resolve().parent
CASES_PATH = EVAL_DIR / "cases.jsonl"
SNAPSHOTS_DIR = EVAL_DIR / "snapshots"
REPORTS_DIR = EVAL_DIR / "reports"
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Case / result types
# ---------------------------------------------------------------------------


@dataclass
class EvalCase:
    id: str
    token_address: str
    chain: str
    label: str  # legit | pump_and_dump | rug
    category: str
    notes: str


@dataclass
class EvalResult:
    case_id: str
    label: str
    category: str
    token_address: str
    action: str
    confidence: int
    risk_level: str
    killswitch_triggered: bool
    killswitch_primary: Optional[str]
    signal_overall: float
    signal_confidence: float
    signal_market: float
    signal_rug: float
    signal_social: float
    signal_hint: str
    elapsed_seconds: float
    status: str  # "ok" | "error"
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# Actions that constitute a "negative" verdict on the token.
SELL_ACTIONS = {"SELL", "STRONG_SELL"}
BUY_ACTIONS = {"BUY", "STRONG_BUY"}


# ---------------------------------------------------------------------------
# Snapshot I/O
# ---------------------------------------------------------------------------


def _snapshot_path(case: EvalCase) -> Path:
    return SNAPSHOTS_DIR / f"{case.id}.json"


def load_snapshot(case: EvalCase) -> Optional[Dict[str, Any]]:
    path = _snapshot_path(case)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def save_snapshot(case: EvalCase, data: Dict[str, Any]) -> None:
    path = _snapshot_path(case)
    path.write_text(
        json.dumps(data, indent=2, default=str, ensure_ascii=False),
        encoding="utf-8",
    )


async def fetch_raw_data(case: EvalCase) -> Dict[str, Any]:
    """Fetch raw data from all sources for one case (used by --refresh)."""
    dex_chain = get_chain_id(case.chain, "dex")

    # Kick off all fetches in parallel.
    dex_task = asyncio.to_thread(get_dex_data, dex_chain, case.token_address)
    gmgn_task = get_token_analysis(case.token_address, case.chain)
    safety_task = get_safety_report(case.token_address, case.chain)

    dex_data, gmgn_data, safety_raw = await asyncio.gather(
        dex_task, gmgn_task, safety_task, return_exceptions=True
    )

    dex_data = dex_data if not isinstance(dex_data, Exception) else {}
    gmgn_data = gmgn_data if not isinstance(gmgn_data, Exception) else {}
    if isinstance(safety_raw, Exception):
        safety_dict: Dict[str, Any] = {}
    else:
        safety_dict = safety_raw.to_dict() if hasattr(safety_raw, "to_dict") else (
            safety_raw or {}
        )

    # Try to derive symbol for twitter search
    symbol = None
    name = None
    pairs = (dex_data or {}).get("pairs") or []
    if pairs:
        base = pairs[0].get("baseToken") or {}
        symbol = base.get("symbol")
        name = base.get("name")

    twitter_data: Dict[str, Any] = {}
    if symbol:
        try:
            twitter_data = await fetch_token_tweets(
                token_symbol=symbol,
                token_name=name,
                token_address=case.token_address,
                max_tweets=20,
            )
        except Exception as exc:  # noqa: BLE001
            twitter_data = {"error": str(exc), "tweets": [], "status": "error"}

    return {
        "token_address": case.token_address,
        "chain": case.chain,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "dex_data": dex_data,
        "gmgn_data": gmgn_data,
        "safety_data": safety_dict,
        "twitter_data": twitter_data,
    }


# ---------------------------------------------------------------------------
# Case execution
# ---------------------------------------------------------------------------


def load_cases() -> List[EvalCase]:
    cases: List[EvalCase] = []
    for line in CASES_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        row = json.loads(line)
        cases.append(EvalCase(**row))
    return cases


async def run_case(case: EvalCase, refresh: bool) -> EvalResult:
    """Run one eval case. Fetches + saves snapshot if needed."""
    snapshot = None if refresh else load_snapshot(case)
    if snapshot is None:
        print(f"  [fetch] {case.id} ({case.token_address[:12]}...)")
        snapshot = await fetch_raw_data(case)
        save_snapshot(case, snapshot)
    else:
        print(f"  [replay] {case.id}")

    t0 = time.time()
    try:
        result: AnalysisResult = await orchestrator.run_from_snapshot(
            token_address=case.token_address,
            chain=case.chain,
            dex_data=snapshot.get("dex_data") or {},
            gmgn_data=snapshot.get("gmgn_data") or {},
            safety_data=snapshot.get("safety_data") or {},
            twitter_data=snapshot.get("twitter_data") or {},
        )
    except Exception as exc:  # noqa: BLE001
        elapsed = time.time() - t0
        print(f"    ERROR: {type(exc).__name__}: {exc}")
        return EvalResult(
            case_id=case.id,
            label=case.label,
            category=case.category,
            token_address=case.token_address,
            action="ERROR",
            confidence=0,
            risk_level="UNKNOWN",
            killswitch_triggered=False,
            killswitch_primary=None,
            signal_overall=0.0,
            signal_confidence=0.0,
            signal_market=0.0,
            signal_rug=0.0,
            signal_social=0.0,
            signal_hint="ERROR",
            elapsed_seconds=elapsed,
            status="error",
            error=str(exc),
        )

    elapsed = time.time() - t0

    pred = result.ai_results.get("prediction", {}).get("analysis") or {}
    action = pred.get("action_signal") or "UNKNOWN"
    if hasattr(action, "value"):
        action = action.value
    risk_level = pred.get("risk_level") or "UNKNOWN"
    if hasattr(risk_level, "value"):
        risk_level = risk_level.value
    confidence = int(pred.get("confidence_level") or 0)

    sv = result.signal_vector
    ks = result.killswitch

    return EvalResult(
        case_id=case.id,
        label=case.label,
        category=case.category,
        token_address=case.token_address,
        action=str(action),
        confidence=confidence,
        risk_level=str(risk_level),
        killswitch_triggered=bool(ks and ks.triggered),
        killswitch_primary=(ks.primary.rule if (ks and ks.primary) else None),
        signal_overall=float(sv.overall) if sv else 0.0,
        signal_confidence=float(sv.confidence) if sv else 0.0,
        signal_market=float(sv.market) if sv else 0.0,
        signal_rug=float(sv.rug) if sv else 0.0,
        signal_social=float(sv.social) if sv else 0.0,
        signal_hint=str(sv.action_hint) if sv else "NONE",
        elapsed_seconds=round(elapsed, 2),
        status="ok",
        error=None,
    )


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


def _is_rug_label(label: str) -> bool:
    return label in ("rug", "pump_and_dump")


def compute_metrics(results: List[EvalResult]) -> Dict[str, Any]:
    ok = [r for r in results if r.status == "ok"]
    errored = [r for r in results if r.status == "error"]

    rugs = [r for r in ok if _is_rug_label(r.label)]
    legits = [r for r in ok if r.label == "legit"]

    def _caught_as_negative(r: EvalResult) -> bool:
        return r.action in SELL_ACTIONS or r.killswitch_triggered

    rug_caught = sum(1 for r in rugs if _caught_as_negative(r))
    legit_passed = sum(1 for r in legits if not _caught_as_negative(r))

    # Killswitch precision: of all ks triggers, how many are actually rugs
    ks_triggered = [r for r in ok if r.killswitch_triggered]
    ks_on_rug = sum(1 for r in ks_triggered if _is_rug_label(r.label))
    ks_on_legit = sum(1 for r in ks_triggered if r.label == "legit")

    # Brier-style on rug probability (using 1 - signal.rug as P(rug))
    brier_rugs = 0.0
    brier_legits = 0.0
    for r in rugs:
        p_rug = 1.0 - r.signal_rug
        brier_rugs += (1.0 - p_rug) ** 2  # true label = 1
    for r in legits:
        p_rug = 1.0 - r.signal_rug
        brier_legits += (0.0 - p_rug) ** 2  # true label = 0

    action_by_label: Dict[str, Counter] = defaultdict(Counter)
    for r in ok:
        action_by_label[r.label][r.action] += 1

    confidence_by_label: Dict[str, List[int]] = defaultdict(list)
    for r in ok:
        confidence_by_label[r.label].append(r.confidence)

    latencies = [r.elapsed_seconds for r in ok]

    def _safe_div(n: float, d: float) -> float:
        return n / d if d > 0 else 0.0

    return {
        "total_cases": len(results),
        "ok": len(ok),
        "errored": len(errored),
        "rug_count": len(rugs),
        "legit_count": len(legits),
        "rug_detection_rate": round(_safe_div(rug_caught, len(rugs)), 3),
        "legit_pass_rate": round(_safe_div(legit_passed, len(legits)), 3),
        "killswitch_triggers": len(ks_triggered),
        "killswitch_on_rugs": ks_on_rug,
        "killswitch_on_legits": ks_on_legit,
        "killswitch_precision": round(_safe_div(ks_on_rug, len(ks_triggered)), 3),
        "brier_rugs": round(_safe_div(brier_rugs, len(rugs)), 4),
        "brier_legits": round(_safe_div(brier_legits, len(legits)), 4),
        "action_distribution": {k: dict(v) for k, v in action_by_label.items()},
        "avg_confidence": {
            k: round(sum(v) / len(v), 1) if v else 0.0
            for k, v in confidence_by_label.items()
        },
        "avg_latency_sec": round(sum(latencies) / len(latencies), 2) if latencies else 0.0,
        "total_latency_sec": round(sum(latencies), 2),
    }


def render_markdown_report(
    results: List[EvalResult], metrics: Dict[str, Any]
) -> str:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines: List[str] = []
    lines.append(f"# Eval Report — {ts}\n")
    lines.append("## Headline metrics\n")
    lines.append(
        f"- **Rug detection rate**: {metrics['rug_detection_rate']*100:.0f}% "
        f"({metrics['rug_count']} rugs evaluated)"
    )
    lines.append(
        f"- **Legit pass rate**: {metrics['legit_pass_rate']*100:.0f}% "
        f"({metrics['legit_count']} legits evaluated)"
    )
    lines.append(
        f"- **Kill-switch precision**: {metrics['killswitch_precision']*100:.0f}% "
        f"({metrics['killswitch_on_rugs']}/{metrics['killswitch_triggers']} triggers on actual rugs)"
    )
    if metrics["killswitch_on_legits"] > 0:
        lines.append(
            f"- **⚠ Kill-switch false positives**: "
            f"{metrics['killswitch_on_legits']} legit token(s) were killswitched"
        )
    lines.append(
        f"- **Brier score (rugs)**: {metrics['brier_rugs']:.3f} "
        f"— **Brier score (legits)**: {metrics['brier_legits']:.3f}"
    )
    lines.append(
        f"- **Avg latency**: {metrics['avg_latency_sec']:.1f}s per case, "
        f"total {metrics['total_latency_sec']:.0f}s"
    )
    if metrics["errored"] > 0:
        lines.append(f"- **⚠ Errored cases**: {metrics['errored']}")
    lines.append("")

    lines.append("## Per-case results\n")
    lines.append(
        "| Case | Label | Action | Conf | Risk | KS | signal.overall | rug | mkt | social | hint | t(s) |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for r in results:
        ks_mark = (
            f"🛑 {r.killswitch_primary}"
            if r.killswitch_triggered
            else "—"
        )
        lines.append(
            f"| `{r.case_id}` | {r.label} | **{r.action}** | {r.confidence} | "
            f"{r.risk_level} | {ks_mark} | {r.signal_overall:.2f} | "
            f"{r.signal_rug:.2f} | {r.signal_market:.2f} | {r.signal_social:.2f} | "
            f"{r.signal_hint} | {r.elapsed_seconds:.1f} |"
        )
    lines.append("")

    lines.append("## Action distribution by label\n")
    for label, counts in metrics["action_distribution"].items():
        lines.append(f"- **{label}** ({sum(counts.values())}): {dict(counts)}")
    lines.append("")

    lines.append("## Average confidence by label\n")
    for label, avg in metrics["avg_confidence"].items():
        lines.append(f"- **{label}**: {avg}")
    lines.append("")

    # Per-case notes at the end for traceability
    lines.append("## Errors\n")
    errs = [r for r in results if r.status == "error"]
    if not errs:
        lines.append("None.")
    else:
        for r in errs:
            lines.append(f"- `{r.case_id}`: {r.error}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


async def main() -> int:
    parser = argparse.ArgumentParser(description="Eval harness runner")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-fetch raw data for all cases (or those named with --only)",
    )
    parser.add_argument(
        "--only",
        type=str,
        default="",
        help="Comma-separated case ids to run (default: all)",
    )
    args = parser.parse_args()

    cases = load_cases()
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        cases = [c for c in cases if c.id in wanted]
        if not cases:
            print(f"No cases matched --only {args.only}")
            return 1

    print(f"Running {len(cases)} case(s)...")
    results: List[EvalResult] = []
    for case in cases:
        print(f"\n— {case.id} ({case.label}/{case.category})")
        res = await run_case(case, refresh=args.refresh)
        results.append(res)
        print(
            f"    action={res.action} conf={res.confidence} "
            f"ks={'Y' if res.killswitch_triggered else 'n'} "
            f"overall={res.signal_overall:.2f}"
        )

    metrics = compute_metrics(results)
    report_md = render_markdown_report(results, metrics)

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    (REPORTS_DIR / f"report_{ts}.md").write_text(report_md, encoding="utf-8")
    (REPORTS_DIR / "latest.md").write_text(report_md, encoding="utf-8")

    # Machine-readable
    (REPORTS_DIR / "latest.jsonl").write_text(
        "\n".join(json.dumps(r.to_dict(), default=str) for r in results)
        + "\n",
        encoding="utf-8",
    )

    print("\n" + "=" * 72)
    print(f"Rug detection rate: {metrics['rug_detection_rate']*100:.0f}%")
    print(f"Legit pass rate:    {metrics['legit_pass_rate']*100:.0f}%")
    print(
        f"Killswitch: {metrics['killswitch_triggers']} triggered "
        f"({metrics['killswitch_on_rugs']} on rugs, "
        f"{metrics['killswitch_on_legits']} on legits)"
    )
    print(f"Avg latency: {metrics['avg_latency_sec']:.1f}s")
    print(f"Report:      eval/reports/report_{ts}.md (also latest.md)")
    print("=" * 72)

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
