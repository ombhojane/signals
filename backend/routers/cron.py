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

GET /cron/scan/stream does the same but returns Server-Sent Events so
the frontend can render each pipeline stage + agent interaction live.

Designed to be hit by an external cron (every 15-30 min) or triggered
manually from the frontend.
"""

from __future__ import annotations

import asyncio
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

import httpx
from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from core.factbook import build_token_factbook
from core.killswitch import check_killswitch
from core.logging import logger
from core.orchestrator import AnalysisPlan, orchestrator
from core.scoring import compute_signal_vector
from services.agents import empty_outcome, to_legacy_envelope
from services.social_preprocessor import preprocess_twitter_payload

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


# Emit callback — receives a dict, returns an awaitable. Default is a no-op.
Emit = Callable[[Dict[str, Any]], Awaitable[None]]


async def _noop_emit(_event: Dict[str, Any]) -> None:  # pragma: no cover
    return None


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
# Per-token orchestrator run with live event emission.
#
# Mirrors orchestrator._run_from_raw() but calls each stage explicitly so
# we can emit phase + agent events between them. Keeps the result shape
# identical to the non-streaming path.
# ---------------------------------------------------------------------------

def _outcome_event(outcome, status: str, duration_ms: float) -> Dict[str, Any]:
    return {
        "type": "agent",
        "name": outcome.agent_type,
        "status": status,
        "duration_ms": round(duration_ms, 1),
        "score": round(outcome.scored.score, 3),
        "confidence": round(outcome.scored.confidence, 3),
        "red_flags": list(outcome.scored.red_flags),
        "error": outcome.error,
        "analysis": outcome.raw,
    }


async def _analyze_token_with_events(
    *,
    token_address: str,
    chain: str,
    pair_data: Dict[str, Any],
    emit: Emit,
) -> Dict[str, Any]:
    """Run one token through the orchestrator and emit events at each stage."""
    pair = (pair_data.get("pairs") or [{}])[0]
    base = pair.get("baseToken") or {}
    symbol = base.get("symbol") or "?"
    t1 = time.time()

    try:
        # PLAN
        plan: AnalysisPlan = orchestrator.think(token_address, chain)
        await emit({"type": "phase", "name": "plan", "status": "done",
                    "reasoning": plan.reasoning,
                    "data_sources": [s.value for s in plan.data_sources]})

        # FETCH
        await emit({"type": "phase", "name": "fetch", "status": "start"})
        fetch_t0 = time.time()
        dex_data, gmgn_data, safety_data, twitter_data = await orchestrator.fetch_data(plan)
        await emit({
            "type": "phase", "name": "fetch", "status": "done",
            "duration_ms": round((time.time() - fetch_t0) * 1000, 1),
            "sources": {
                "dex": bool(dex_data),
                "gmgn": bool(gmgn_data),
                "safety": bool(safety_data),
                "twitter": bool(twitter_data and not twitter_data.get("error")),
            },
        })

        # PREPROCESS
        await emit({"type": "phase", "name": "preprocess", "status": "start"})
        clean_twitter = preprocess_twitter_payload(twitter_data)
        await emit({"type": "phase", "name": "preprocess", "status": "done",
                    "tweets": len(clean_twitter.get("tweets") or [])})

        # FACTBOOK + KILLSWITCH
        factbook = build_token_factbook(
            token_address=token_address,
            chain=chain,
            dex_data=dex_data,
            gmgn_data=gmgn_data,
            safety_data=safety_data,
            twitter_data=clean_twitter,
        )
        killswitch = check_killswitch(factbook)
        await emit({
            "type": "killswitch",
            "triggered": killswitch.triggered,
            "action": killswitch.action,
            "rule": killswitch.primary.rule if killswitch.primary else None,
            "message": killswitch.primary.message if killswitch.primary else None,
            "reasons": [
                {"rule": r.rule, "severity": r.severity.value, "message": r.message}
                for r in killswitch.reasons
            ],
        })

        # AI WORKERS (parallel)
        await emit({
            "type": "phase", "name": "ai", "status": "start",
            "agents": [
                a for a, has in (
                    ("market_agent", factbook.market.has_data),
                    ("rug_check_agent", factbook.rug.has_data),
                    ("social_agent", factbook.social.has_data),
                ) if has
            ],
        })
        for agent_name in ("market_agent", "rug_check_agent", "social_agent"):
            await emit({"type": "agent", "name": agent_name, "status": "start"})

        ai_t0 = time.time()
        market_outcome, rug_outcome, social_outcome = await orchestrator.run_workers(
            factbook, killswitch.triggered
        )
        ai_ms = (time.time() - ai_t0) * 1000

        for outcome in (market_outcome, rug_outcome, social_outcome):
            await emit(_outcome_event(
                outcome,
                status="ok" if outcome.status == "success" else "error",
                duration_ms=ai_ms,
            ))
        await emit({"type": "phase", "name": "ai", "status": "done",
                    "duration_ms": round(ai_ms, 1)})

        # SCORING
        await emit({"type": "phase", "name": "scoring", "status": "start"})
        signal_vector = compute_signal_vector(
            market=market_outcome,
            rug=rug_outcome,
            social=social_outcome,
            killswitch=killswitch,
        )
        sv_dict = signal_vector.to_dict()
        await emit({"type": "signal_vector", **sv_dict})
        await emit({"type": "phase", "name": "scoring", "status": "done"})

        # PREDICTION
        await emit({"type": "phase", "name": "predict", "status": "start"})
        await emit({"type": "agent", "name": "predictor", "status": "start"})
        pred_t0 = time.time()
        prediction_outcome = await orchestrator.prediction_agent.predict(
            factbook=factbook,
            killswitch=killswitch,
            market=market_outcome,
            rug=rug_outcome,
            social=social_outcome,
            signal_vector=sv_dict,
        )
        pred_ms = (time.time() - pred_t0) * 1000
        await emit(_outcome_event(
            prediction_outcome,
            status="ok" if prediction_outcome.status == "success" else "error",
            duration_ms=pred_ms,
        ))
        await emit({"type": "phase", "name": "predict", "status": "done",
                    "duration_ms": round(pred_ms, 1)})

        # Build the scan-result shape (identical to the POST /cron/scan response)
        pred_analysis = (prediction_outcome.raw or {}) if prediction_outcome else {}
        action = pred_analysis.get("action_signal")
        if hasattr(action, "value"):
            action = action.value
        action = str(action or "UNKNOWN")

        confidence = int(pred_analysis.get("confidence_level") or 0)
        risk_level = pred_analysis.get("risk_level")
        if hasattr(risk_level, "value"):
            risk_level = risk_level.value
        risk_level = str(risk_level or "UNKNOWN")

        scan_result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "token_address": token_address,
            "symbol": symbol,
            "name": base.get("name") or "?",
            "chain": chain,
            "price": float(pair.get("priceUsd") or 0),
            "volume_24h": float((pair.get("volume") or {}).get("h24") or 0),
            "liquidity": float((pair.get("liquidity") or {}).get("usd") or 0),
            "market_cap": float(pair.get("marketCap") or 0),
            "action": action,
            "confidence": confidence,
            "risk_level": risk_level,
            "signal_overall": sv_dict.get("overall"),
            "signal_market": sv_dict.get("market"),
            "signal_rug": sv_dict.get("rug"),
            "signal_social": sv_dict.get("social"),
            "signal_hint": sv_dict.get("action_hint"),
            "killswitch_triggered": bool(killswitch and killswitch.triggered),
            "killswitch_reason": (killswitch.primary.rule if (killswitch and killswitch.primary) else None),
            "reasoning": pred_analysis.get("summary", ""),
            "key_factors": list(pred_analysis.get("key_factors") or []),
            "red_flags": list(pred_analysis.get("red_flags") or []),
            "elapsed_seconds": round(time.time() - t1, 2),
            "status": "ok",
        }
        return scan_result

    except Exception as exc:
        logger.error(f"  {symbol}: FAILED — {exc}")
        await emit({"type": "token.error", "symbol": symbol, "error": str(exc)})
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "token_address": token_address,
            "symbol": symbol,
            "name": base.get("name") or "?",
            "chain": chain,
            "status": "error",
            "error": str(exc),
            "elapsed_seconds": round(time.time() - t1, 2),
        }


# ---------------------------------------------------------------------------
# Main scan runner — emits events; used by both POST and SSE paths.
# ---------------------------------------------------------------------------

def _check_ai_auth() -> Optional[str]:
    """Cheap shape-check on GOOGLE_API_KEY — returns a warning message if
    the key is clearly unusable, else None. Real Gemini keys start with 'AIza'.
    """
    key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not key:
        return "GOOGLE_API_KEY is empty — all 4 AI agents will fail and every token will fall back to HOLD. Add a real Gemini key from https://aistudio.google.com/apikey to backend/.env and restart."
    if key.startswith("placeholder") or key.startswith("your_") or len(key) < 20:
        return "GOOGLE_API_KEY looks like a placeholder — AI agents will fail and every token will fall back to HOLD. Replace it in backend/.env with a real Gemini key from https://aistudio.google.com/apikey."
    if not key.startswith("AIza"):
        return "GOOGLE_API_KEY does not look like a Gemini API key (should start with 'AIza'). AI agents may fail."
    return None


async def _run_scan(config: ScanConfig, emit: Emit) -> Dict[str, Any]:
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    logger.section(f"CRON SCAN — {run_id}")
    t0 = time.time()

    await emit({"type": "scan.start", "run_id": run_id,
                "config": config.model_dump(), "started_at": datetime.now(timezone.utc).isoformat()})

    # Preflight — warn up front if the AI stack is unauthenticated so the UI
    # can make it obvious that HOLD is a fallback, not a real recommendation.
    auth_warning = _check_ai_auth()
    if auth_warning:
        logger.warning(auth_warning)
        await emit({
            "type": "scan.warning",
            "code": "ai_unauthenticated",
            "message": auth_warning,
        })

    # 1. DISCOVER
    await emit({"type": "phase", "name": "discover", "status": "start"})
    logger.info("Discovering trending Solana tokens...")
    disc_t0 = time.time()
    addresses = await _fetch_trending_addresses(config.chain, limit=30)
    await emit({
        "type": "discover.done",
        "count": len(addresses),
        "duration_ms": round((time.time() - disc_t0) * 1000, 1),
    })
    logger.info(f"Found {len(addresses)} candidate addresses")

    if not addresses:
        result = {
            "run_id": run_id, "status": "no_candidates",
            "discovered": 0, "filtered": 0, "analyzed": 0,
            "results": [], "elapsed_seconds": round(time.time() - t0, 2),
        }
        await emit({"type": "scan.done", **result})
        return result

    # 2. FILTER
    await emit({"type": "phase", "name": "filter", "status": "start"})
    logger.info("Fetching pair data and applying kill-chain filters...")
    survivors: List[Dict[str, Any]] = []
    filter_log: List[str] = []
    evaluated = 0

    for addr in addresses:
        if len(survivors) >= config.max_tokens * 3:
            break
        pair_data = await _fetch_pair_data(addr)
        evaluated += 1
        if not pair_data or not pair_data.get("pairs"):
            reason = f"{addr[:12]}...: no pair data"
            filter_log.append(reason)
            await emit({"type": "filter", "address": addr, "symbol": None,
                        "passed": False, "reason": reason})
            continue
        pair = pair_data["pairs"][0]
        base = pair.get("baseToken") or {}
        passed, reason = _passes_killchain(pair, config)
        filter_log.append(reason)
        await emit({
            "type": "filter", "address": addr,
            "symbol": base.get("symbol"),
            "passed": passed, "reason": reason,
            "price": float(pair.get("priceUsd") or 0),
            "volume_24h": float((pair.get("volume") or {}).get("h24") or 0),
            "liquidity": float((pair.get("liquidity") or {}).get("usd") or 0),
            "market_cap": float(pair.get("marketCap") or 0),
        })
        if passed:
            survivors.append({"address": addr, "pair_data": pair_data, "pair": pair})

    survivors = survivors[: config.max_tokens]
    await emit({
        "type": "filter.done",
        "evaluated": evaluated, "survived": len(survivors),
        "rejected": evaluated - len(survivors),
    })
    logger.info(f"Kill-chain: {len(survivors)} survived out of {len(addresses)}")

    if not survivors:
        result = {
            "run_id": run_id, "status": "all_filtered",
            "discovered": len(addresses), "filtered": 0, "analyzed": 0,
            "filter_log": filter_log, "results": [],
            "elapsed_seconds": round(time.time() - t0, 2),
        }
        await emit({"type": "scan.done", **result})
        return result

    # 3. ANALYZE
    logger.info(f"Running {len(survivors)} tokens through orchestrator...")
    results: List[Dict[str, Any]] = []

    for idx, s in enumerate(survivors):
        addr = s["address"]
        pair = s["pair"]
        base = pair.get("baseToken") or {}
        symbol = base.get("symbol") or "?"

        await emit({
            "type": "token.start",
            "index": idx, "total": len(survivors),
            "address": addr, "symbol": symbol, "name": base.get("name"),
            "price": float(pair.get("priceUsd") or 0),
            "volume_24h": float((pair.get("volume") or {}).get("h24") or 0),
            "liquidity": float((pair.get("liquidity") or {}).get("usd") or 0),
            "market_cap": float(pair.get("marketCap") or 0),
        })
        logger.info(f"Analyzing {symbol} ({addr[:12]}...)...")

        scan_result = await _analyze_token_with_events(
            token_address=addr, chain=config.chain,
            pair_data=s["pair_data"], emit=emit,
        )
        scan_result["run_id"] = run_id
        results.append(scan_result)
        _save_scan_result(scan_result)

        await emit({"type": "token.done", "index": idx, "result": scan_result})

    elapsed = round(time.time() - t0, 2)
    logger.section(f"CRON SCAN COMPLETE — {len(results)} tokens in {elapsed}s")

    ok_results = [r for r in results if r.get("status") == "ok"]
    buys = [r for r in ok_results if r.get("action") in ("BUY", "STRONG_BUY")]
    sells = [r for r in ok_results if r.get("action") in ("SELL", "STRONG_SELL")]
    holds = [r for r in ok_results if r.get("action") == "HOLD"]

    summary = {
        "run_id": run_id, "status": "ok",
        "discovered": len(addresses), "filtered": len(survivors),
        "analyzed": len(results),
        "summary": {
            "buys": len(buys), "sells": len(sells),
            "holds": len(holds), "errors": len(results) - len(ok_results),
        },
        "results": results, "filter_log": filter_log,
        "config": config.model_dump(), "elapsed_seconds": elapsed,
    }
    await emit({"type": "scan.done", **summary})
    return summary


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------

@router.post("/scan")
async def scan_new_tokens(config: ScanConfig = ScanConfig()) -> Dict[str, Any]:
    """Discover, filter, and analyze new Solana tokens autonomously."""
    return await _run_scan(config, emit=_noop_emit)


@router.get("/scan/stream")
async def scan_stream(
    request: Request,
    chain: str = "sol",
    max_tokens: int = 5,
    min_age_minutes: int = 15,
    max_age_hours: int = 24,
    min_volume_usd: float = 1000.0,
    min_liquidity_usd: float = 500.0,
    min_buys_24h: int = 10,
    min_market_cap_usd: float = 0.0,
    max_rug_score: int = 80,
) -> StreamingResponse:
    """Run the scan and stream pipeline events as Server-Sent Events.

    Each event is a JSON payload with a `type` field. See _run_scan for the
    full vocabulary (scan.start, phase, filter, agent, signal_vector, token.*,
    scan.done, error).
    """
    config = ScanConfig(
        chain=chain, max_tokens=max_tokens,
        min_age_minutes=min_age_minutes, max_age_hours=max_age_hours,
        min_volume_usd=min_volume_usd, min_liquidity_usd=min_liquidity_usd,
        min_buys_24h=min_buys_24h, min_market_cap_usd=min_market_cap_usd,
        max_rug_score=max_rug_score,
    )

    queue: asyncio.Queue[Optional[Dict[str, Any]]] = asyncio.Queue()

    async def emit(event: Dict[str, Any]) -> None:
        await queue.put(event)

    async def runner() -> None:
        try:
            await _run_scan(config, emit)
        except Exception as exc:  # noqa: BLE001
            logger.error(f"scan.stream failed: {exc}")
            await queue.put({"type": "error", "message": str(exc)})
        finally:
            await queue.put(None)  # sentinel

    async def generator():
        task = asyncio.create_task(runner())
        try:
            while True:
                if await request.is_disconnected():
                    task.cancel()
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=10.0)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
                    continue
                if event is None:
                    break
                yield f"data: {json.dumps(event, default=str)}\n\n"
        finally:
            if not task.done():
                task.cancel()

    return StreamingResponse(
        generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/scans")
async def list_recent_scans(
    limit: int = Query(default=50, le=200),
    action_filter: Optional[str] = Query(default=None, description="BUY, SELL, HOLD"),
) -> Dict[str, Any]:
    """List recent scan results from the JSONL store. Newest first."""
    all_results: List[Dict[str, Any]] = []

    files = sorted(SCANS_DIR.glob("scans_*.jsonl"), reverse=True)
    for f in files[:7]:
        try:
            for line in f.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line:
                    all_results.append(json.loads(line))
        except Exception:
            continue

    all_results.sort(key=lambda r: r.get("timestamp", ""), reverse=True)

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
    actions: Dict[str, int] = {}
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
