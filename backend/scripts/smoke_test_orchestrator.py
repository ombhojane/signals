"""
Smoke test for the enhanced orchestrator pipeline.

Runs the full pipeline against a real Solana token and prints:
- FactBook contents (per domain)
- Kill-switch result
- Each worker agent's score + confidence + red_flags
- Final prediction
- Synthesis summary
- Timing for each stage

Usage (from D:\\elonmusk\\hackx\\backend):
    venv/Scripts/python.exe scripts/smoke_test_orchestrator.py
    venv/Scripts/python.exe scripts/smoke_test_orchestrator.py <token> <chain> [pair]

Defaults: BONK on Solana (well-known safe token, should produce a non-triggered
kill-switch, coverage on DEX + safety, and a non-AVOID prediction).
"""

from __future__ import annotations

import asyncio
import io
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

# Force UTF-8 stdout on Windows so we don't crash on non-ASCII tweet content.
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Ensure project root is on path (so `core.` and `services.` imports work)
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

# Walk up from backend/scripts to find the project-root .env
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from core.orchestrator import orchestrator


DEFAULT_TOKEN = "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"  # BONK
DEFAULT_CHAIN = "sol"
DEFAULT_PAIR = None  # fall back to token address for DexScreener lookup


def _hr(label: str) -> None:
    print("\n" + "=" * 72)
    print(f"  {label}")
    print("=" * 72)


def _pretty(obj) -> str:
    def _default(v):
        # Unwrap enums to their value for readable output
        if hasattr(v, "value"):
            return v.value
        return str(v)

    try:
        return json.dumps(obj, indent=2, default=_default)
    except Exception:
        return str(obj)


def _enum_value(v):
    return v.value if hasattr(v, "value") else v


async def main() -> int:
    token = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TOKEN
    chain = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_CHAIN
    pair = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_PAIR

    print(f"Smoke test — token={token}  chain={chain}  pair={pair}")
    t0 = time.time()

    try:
        result = await orchestrator.run(
            token_address=token,
            chain=chain,
            pair_address=pair,
        )
    except Exception as exc:
        print(f"\nPIPELINE RAISED: {type(exc).__name__}: {exc}")
        import traceback
        traceback.print_exc()
        return 1

    elapsed = time.time() - t0
    print(f"\n[ok] pipeline finished in {elapsed:.2f}s")

    # Plan
    _hr("PLAN")
    print(f"Reasoning: {result.plan.reasoning}")
    print(f"Data sources: {[s.value for s in result.plan.data_sources]}")

    # FactBook
    _hr("FACTBOOK — market")
    if result.factbook:
        print(_pretty(asdict(result.factbook.market)))
    _hr("FACTBOOK — rug")
    if result.factbook:
        print(_pretty(asdict(result.factbook.rug)))
    _hr("FACTBOOK — social")
    if result.factbook:
        print(_pretty(asdict(result.factbook.social)))

    # Preprocessor stats (new — debugging dedup)
    _hr("TWITTER PREPROCESSING STATS")
    meta = (result.twitter_data or {}).get("meta") if isinstance(result.twitter_data, dict) else None
    if meta:
        print(_pretty(meta))
    else:
        print("no preprocessing meta available")
    # Dump the first raw tweet text from the cleaned payload so we can see
    # what the hash function actually saw.
    cleaned_tweets = (result.twitter_data or {}).get("tweets") if isinstance(result.twitter_data, dict) else None
    if cleaned_tweets:
        print(f"\nCLEANED TWEETS — {len(cleaned_tweets)} surviving:")
        for i, t in enumerate(cleaned_tweets[:10]):
            txt = (t.get("text") or "")[:120].replace("\n", " ")
            author = (t.get("author") or {}).get("userName", "?")
            print(f"  [{i}] @{author}: {txt}")

    # Kill-switch
    _hr("KILL-SWITCH")
    if result.killswitch:
        print(_pretty(result.killswitch.to_dict()))
    else:
        print("not run")

    # Worker outcomes (via legacy envelope)
    _hr("AGENT OUTCOMES")
    for key in ("market_analysis", "gmgn_analysis", "social_analysis", "prediction"):
        env = result.ai_results.get(key, {})
        print(f"\n--- {key} ---")
        print(f"  status      = {env.get('status')}")
        print(f"  score       = {env.get('score')}")
        print(f"  confidence  = {env.get('confidence')}")
        print(f"  red_flags   = {env.get('red_flags')}")
        if env.get("error"):
            print(f"  error       = {env['error']}")
        analysis = env.get("analysis")
        if isinstance(analysis, dict):
            # Only show the 3-4 most useful fields to keep output readable
            for field in ("summary", "recommendation", "action_signal", "confidence_level", "risk_level"):
                if field in analysis:
                    print(f"  {field:12}= {_enum_value(analysis[field])}")

    # Synthesis
    _hr("SYNTHESIS")
    if result.synthesis:
        print(_pretty(result.synthesis))

    # Final
    _hr("SUMMARY")
    pred = result.ai_results.get("prediction", {}).get("analysis") or {}
    print(f"Final action:     {_enum_value(pred.get('action_signal', 'N/A'))}")
    print(f"Final confidence: {pred.get('confidence_level', 'N/A')}")
    print(f"Risk level:       {_enum_value(pred.get('risk_level', 'N/A'))}")
    print(f"Killswitch:       {'TRIGGERED' if (result.killswitch and result.killswitch.triggered) else 'clear'}")
    print(f"Elapsed:          {elapsed:.2f}s")

    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
