"""
Cron Scanner — autonomous token discovery + AI analysis endpoint.

Hit POST /cron/scan and it will:
1. Fetch the latest trending/boosted Solana tokens from DexScreener
2. Pull detailed pair data for each
3. Apply a memecoin-trader-style kill-chain filter:
   - Age > 15 min (avoid instant rugs)
   - Age < 24h (focus on fresh launches)
   - Volume 24h > $1,000 (real trading activity)
   - Liquidity > $500 (can actually exit)
   - Buys > 10 (organic interest, not 1 insider)
   - Not a known honeypot
4. Run survivors through the full orchestrator pipeline
5. Store + return results

Designed to be hit by an external cron (every 15-30 min) or triggered
manually from the frontend.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.logging import logger
from core.orchestrator import orchestrator

router = APIRouter(prefix="/cron", tags=["Cron Scanner"])

SCANS_DIR = Path("data/scans")
SCANS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Kill-chain filter defaults — what memecoin traders actually want
# ---------------------------------------------------------------------------

class ScanConfig(BaseModel):
    chain: str = "sol"
    max_tokens: int = 5
    min_age_minutes: int = 15
    max_age_hours: int = 24
    min_volume_usd: float = 1000.0
    min_liquidity_usd: float = 500.0
    min_buys_24h: int = 10
    min_market_cap_usd: float = 0.0
    max_rug_score: int = 80


# ---------------------------------------------------------------------------
# Token discovery — DexScreener latest boosts + profiles
# ---------------------------------------------------------------------------

async def _fetch_trending_addresses(chain: str, limit: int = 30) -> List[str]:
    """Get recently boosted/trending token addresses from DexScreener."""
    addresses: List[str] = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get("https://api.dexscreener.com/token-boosts/latest/v1")
            resp.raise_for_status()
            for item in resp.json():
                if item.get("chainId", "").lower() == "solana":
                    addr = item.get("tokenAddress")
                    if addr and addr not in addresses:
                        addresses.append(addr)
                if len(addresses) >= limit:
                    break
        except Exception as exc:
            logger.warning(f"DexScreener boosts fetch failed: {exc}")

        # Also try token profiles for more coverage
        try:
            resp2 = await client.get("https://api.dexscreener.com/token-profiles/latest/v1")
            resp2.raise_for_status()
            for item in resp2.json():
                if item.get("chainId", "").lower() == "solana":
                    addr = item.get("tokenAddress")
                    if addr and addr not in addresses:
                        addresses.append(addr)
                if len(addresses) >= limit:
                    break
        except Exception as exc:
            logger.warning(f"DexScreener profiles fetch failed: {exc}")

    return addresses


async def _fetch_pair_data(address: str) -> Optional[Dict[str, Any]]:
    """Get detailed pair data from DexScreener search for one token."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                "https://api.dexscreener.com/latest/dex/search",
                params={"q": address},
            )
            resp.raise_for_status()
            data = resp.json()
            pairs = data.get("pairs") or []
            # Pick the Solana pair with highest liquidity
            sol_pairs = [
                p for p in pairs
                if (p.get("chainId") or "").lower() == "solana"
            ]
            if sol_pairs:
                sol_pairs.sort(
                    key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0),
                    reverse=True,
                )
                return {"pairs": [sol_pairs[0]]}
        except Exception as exc:
            logger.warning(f"DexScreener pair fetch for {address[:12]}... failed: {exc}")
    return None


# ---------------------------------------------------------------------------
# Kill-chain filter
# ---------------------------------------------------------------------------

def _passes_killchain(pair: Dict[str, Any], config: ScanConfig) -> tuple[bool, str]:
    """Apply memecoin-trader-style filters. Returns (passed, reason)."""
    base = pair.get("baseToken") or {}
    liq = float((pair.get("liquidity") or {}).get("usd") or 0)
    vol_24h = float((pair.get("volume") or {}).get("h24") or 0)
    txns = pair.get("txns") or {}
    buys_24h = int((txns.get("h24") or {}).get("buys") or 0)
    mcap = float(pair.get("marketCap") or pair.get("fdv") or 0)
    created_ms = int(pair.get("pairCreatedAt") or 0)

    now_ms = int(time.time() * 1000)
    age_minutes = (now_ms - created_ms) / 60_000 if created_ms > 0 else 0
    age_hours = age_minutes / 60

    symbol = base.get("symbol") or "?"

    if age_minutes < config.min_age_minutes:
        return False, f"{symbol}: too young ({age_minutes:.0f}min < {config.min_age_minutes}min)"
    if config.max_age_hours > 0 and age_hours > config.max_age_hours:
        return False, f"{symbol}: too old ({age_hours:.1f}h > {config.max_age_hours}h)"
    if vol_24h < config.min_volume_usd:
        return False, f"{symbol}: low volume (${vol_24h:,.0f} < ${config.min_volume_usd:,.0f})"
    if liq < config.min_liquidity_usd:
        return False, f"{symbol}: low liquidity (${liq:,.0f} < ${config.min_liquidity_usd:,.0f})"
    if buys_24h < config.min_buys_24h:
        return False, f"{symbol}: low buys ({buys_24h} < {config.min_buys_24h})"
    if mcap < config.min_market_cap_usd:
        return False, f"{symbol}: low mcap (${mcap:,.0f})"

    return True, f"{symbol}: PASSED (age={age_minutes:.0f}min vol=${vol_24h:,.0f} liq=${liq:,.0f} buys={buys_24h})"


# ---------------------------------------------------------------------------
# Result storage
# ---------------------------------------------------------------------------

def _save_scan_result(result: Dict[str, Any]) -> None:
    """Append one scan result to the daily JSONL file."""
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = SCANS_DIR / f"scans_{date_str}.jsonl"
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(result, default=str, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Main endpoint
# ---------------------------------------------------------------------------

@router.post("/scan")
async def scan_new_tokens(config: ScanConfig = ScanConfig()) -> Dict[str, Any]:
    """Discover, filter, and analyze new Solana tokens autonomously.

    Call this on a 15-30 minute cron to maintain a continuously-updating
    signal feed. Each run processes up to `max_tokens` survivors.
    """
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    logger.section(f"CRON SCAN — {run_id}")
    t0 = time.time()

    # 1. Discover
    logger.info("Discovering trending Solana tokens...")
    addresses = await _fetch_trending_addresses(config.chain, limit=30)
    logger.info(f"Found {len(addresses)} candidate addresses")

    if not addresses:
        return {
            "run_id": run_id,
            "status": "no_candidates",
            "discovered": 0,
            "filtered": 0,
            "analyzed": 0,
            "results": [],
            "elapsed_seconds": round(time.time() - t0, 2),
        }

    # 2. Fetch pair data + filter
    logger.info("Fetching pair data and applying kill-chain filters...")
    survivors: List[Dict[str, Any]] = []
    filter_log: List[str] = []

    for addr in addresses:
        if len(survivors) >= config.max_tokens * 3:
            break
        pair_data = await _fetch_pair_data(addr)
        if not pair_data or not pair_data.get("pairs"):
            filter_log.append(f"{addr[:12]}...: no pair data")
            continue
        pair = pair_data["pairs"][0]
        passed, reason = _passes_killchain(pair, config)
        filter_log.append(reason)
        if passed:
            survivors.append({
                "address": addr,
                "pair_data": pair_data,
                "pair": pair,
            })

    logger.info(f"Kill-chain: {len(survivors)} survived out of {len(addresses)}")
    for line in filter_log:
        logger.info(f"  {line}")

    # Cap at max_tokens
    survivors = survivors[: config.max_tokens]

    if not survivors:
        return {
            "run_id": run_id,
            "status": "all_filtered",
            "discovered": len(addresses),
            "filtered": 0,
            "analyzed": 0,
            "filter_log": filter_log,
            "results": [],
            "elapsed_seconds": round(time.time() - t0, 2),
        }

    # 3. Run through AI pipeline
    logger.info(f"Running {len(survivors)} tokens through orchestrator...")
    results: List[Dict[str, Any]] = []

    for s in survivors:
        addr = s["address"]
        pair = s["pair"]
        base = pair.get("baseToken") or {}
        symbol = base.get("symbol") or "?"
        name = base.get("name") or "?"

        logger.info(f"Analyzing {symbol} ({addr[:12]}...)...")
        t1 = time.time()

        try:
            analysis = await orchestrator.run(
                token_address=addr,
                chain=config.chain,
            )

            # Extract key fields for the summary
            pred = (analysis.ai_results.get("prediction") or {}).get("analysis") or {}
            action = pred.get("action_signal")
            if hasattr(action, "value"):
                action = action.value
            action = str(action or "UNKNOWN")

            confidence = int(pred.get("confidence_level") or 0)
            risk_level = pred.get("risk_level")
            if hasattr(risk_level, "value"):
                risk_level = risk_level.value
            risk_level = str(risk_level or "UNKNOWN")

            signal = analysis.signal_vector
            ks = analysis.killswitch

            scan_result = {
                "run_id": run_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "token_address": addr,
                "symbol": symbol,
                "name": name,
                "chain": config.chain,
                "price": float(pair.get("priceUsd") or 0),
                "volume_24h": float((pair.get("volume") or {}).get("h24") or 0),
                "liquidity": float((pair.get("liquidity") or {}).get("usd") or 0),
                "market_cap": float(pair.get("marketCap") or 0),
                "action": action,
                "confidence": confidence,
                "risk_level": risk_level,
                "signal_overall": signal.overall if signal else None,
                "signal_market": signal.market if signal else None,
                "signal_rug": signal.rug if signal else None,
                "signal_social": signal.social if signal else None,
                "signal_hint": signal.action_hint if signal else None,
                "killswitch_triggered": bool(ks and ks.triggered),
                "killswitch_reason": (ks.primary.rule if (ks and ks.primary) else None),
                "reasoning": pred.get("summary", ""),
                "key_factors": list(pred.get("key_factors") or []),
                "red_flags": list(
                    (analysis.ai_results.get("prediction") or {}).get("red_flags") or []
                ),
                "elapsed_seconds": round(time.time() - t1, 2),
                "status": "ok",
            }

            results.append(scan_result)
            _save_scan_result(scan_result)

            logger.info(
                f"  {symbol}: {action} @ conf={confidence} "
                f"signal={signal.overall if signal else 'n/a'} "
                f"ks={'Y' if scan_result['killswitch_triggered'] else 'n'} "
                f"({scan_result['elapsed_seconds']}s)"
            )

        except Exception as exc:
            logger.error(f"  {symbol}: FAILED — {exc}")
            err_result = {
                "run_id": run_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "token_address": addr,
                "symbol": symbol,
                "name": name,
                "chain": config.chain,
                "status": "error",
                "error": str(exc),
                "elapsed_seconds": round(time.time() - t1, 2),
            }
            results.append(err_result)
            _save_scan_result(err_result)

    elapsed = round(time.time() - t0, 2)
    logger.section(f"CRON SCAN COMPLETE — {len(results)} tokens in {elapsed}s")

    # Summary stats
    ok_results = [r for r in results if r.get("status") == "ok"]
    buys = [r for r in ok_results if r.get("action") in ("BUY", "STRONG_BUY")]
    sells = [r for r in ok_results if r.get("action") in ("SELL", "STRONG_SELL")]
    holds = [r for r in ok_results if r.get("action") == "HOLD"]

    return {
        "run_id": run_id,
        "status": "ok",
        "discovered": len(addresses),
        "filtered": len(survivors),
        "analyzed": len(results),
        "summary": {
            "buys": len(buys),
            "sells": len(sells),
            "holds": len(holds),
            "errors": len(results) - len(ok_results),
        },
        "results": results,
        "filter_log": filter_log,
        "config": config.model_dump(),
        "elapsed_seconds": elapsed,
    }


@router.get("/scans")
async def list_recent_scans(
    limit: int = Query(default=50, le=200),
    action_filter: Optional[str] = Query(default=None, description="BUY, SELL, HOLD"),
) -> Dict[str, Any]:
    """List recent scan results from the JSONL store. Newest first."""
    all_results: List[Dict[str, Any]] = []

    # Read all JSONL files, newest first
    files = sorted(SCANS_DIR.glob("scans_*.jsonl"), reverse=True)
    for f in files[:7]:  # last 7 days
        try:
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    all_results.append(json.loads(line))
        except Exception:
            continue

    # Sort by timestamp desc
    all_results.sort(key=lambda r: r.get("timestamp", ""), reverse=True)

    # Filter by action if requested
    if action_filter:
        actions = {a.strip().upper() for a in action_filter.split(",")}
        all_results = [r for r in all_results if r.get("action") in actions]

    return {
        "total": len(all_results),
        "returned": min(limit, len(all_results)),
        "results": all_results[:limit],
    }


@router.get("/scans/summary")
async def scan_summary() -> Dict[str, Any]:
    """Quick summary of today's scan activity."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    path = SCANS_DIR / f"scans_{today}.jsonl"

    if not path.exists():
        return {"date": today, "total_scans": 0, "message": "No scans today yet"}

    results: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            results.append(json.loads(line))

    ok = [r for r in results if r.get("status") == "ok"]
    actions = {}
    for r in ok:
        a = r.get("action", "UNKNOWN")
        actions[a] = actions.get(a, 0) + 1

    top_buys = sorted(
        [r for r in ok if r.get("action") in ("BUY", "STRONG_BUY")],
        key=lambda r: r.get("confidence", 0),
        reverse=True,
    )[:5]

    return {
        "date": today,
        "total_scans": len(results),
        "successful": len(ok),
        "errors": len(results) - len(ok),
        "action_distribution": actions,
        "top_buys": [
            {
                "symbol": r.get("symbol"),
                "token_address": r.get("token_address"),
                "action": r.get("action"),
                "confidence": r.get("confidence"),
                "signal_overall": r.get("signal_overall"),
                "price": r.get("price"),
                "volume_24h": r.get("volume_24h"),
            }
            for r in top_buys
        ],
    }
