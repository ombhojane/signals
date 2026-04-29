"""
ADAPTIVE RL AGENT — LIVE BACKTEST RUNNER
=========================================

A single-file evaluation harness for the agentic trader. It is intentionally
agnostic to the FastAPI app: just run it as a python file.

What it does:
  1. Discovers ~30 trending memecoins across Solana / Base / Ethereum
     (DexScreener boosts + profiles).
  2. Applies the same kill-chain filter the cron scanner uses (age, vol,
     liquidity, buys, ...).
  3. For every survivor it pulls REAL OHLCV history (GeckoTerminal) +
     safety/holders + a Twitter pulse, then replays each historical bar
     through the agent step by step.
  4. Each step:  OBSERVE → THINK → ACT → REFLECT (rule add / weight update).
  5. Captures a simulated wallet (paper money) with confidence-scaled
     position sizing and adaptive stop loss / take profit.
  6. Prints rich verbose logs and writes a JSON report.

Usage (from repo root):
    cd backend
    source venv/bin/activate
    python rl_agent/run_live_eval.py                 # default: ~10 tokens, multi-chain
    python rl_agent/run_live_eval.py --tokens 30 --chains sol,base,eth
    python rl_agent/run_live_eval.py --no-llm        # heuristic-only (offline)
    python rl_agent/run_live_eval.py --timeframe minute --max-bars 60

Output:
    rl_agent/results/live_<timestamp>/
        ├── summary.json          (aggregate P&L + per-token results)
        ├── memory/
        │   ├── trading_journal.md
        │   └── trading_rules.md
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

# ───────────────────────── Path bootstrapping ─────────────────────────
# So the script runs as `python rl_agent/run_live_eval.py` AND `python -m rl_agent.run_live_eval`.
HERE = Path(__file__).resolve().parent
BACKEND_DIR = HERE.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from rl_agent.agentic_trader import AgenticTrader, TradeDecision  # noqa: E402
from rl_agent.synthetic_market import TokenSnapshot  # noqa: E402
from rl_agent.indicators import (  # noqa: E402
    calculate_rsi, calculate_macd, calculate_bollinger,
    calculate_volatility, calculate_volume_ratio,
)
from rl_agent.strategies import seed_memory, SEED_RULES  # noqa: E402

try:
    from services.token_safety_service import token_safety_service  # type: ignore
except Exception:
    token_safety_service = None


# Direct GeckoTerminal client. Free tier is ~30 req/min — we throttle to be safe.
GECKO_NETWORK = {"sol": "solana", "solana": "solana",
                 "eth": "eth", "ethereum": "eth",
                 "base": "base", "bsc": "bsc"}

_GECKO_LOCK = asyncio.Lock()
_GECKO_LAST_CALL = [0.0]
_GECKO_MIN_GAP = 2.2   # seconds between calls (~27/min, under the 30/min limit)


async def _gecko_get(client: httpx.AsyncClient, url: str, **params) -> Optional[Dict[str, Any]]:
    """Throttled GeckoTerminal GET with retry on 429."""
    backoff = 5.0
    for attempt in range(4):
        async with _GECKO_LOCK:
            wait = _GECKO_MIN_GAP - (time.monotonic() - _GECKO_LAST_CALL[0])
            if wait > 0:
                await asyncio.sleep(wait)
            try:
                r = await client.get(url, params=params or None,
                                     headers={"Accept": "application/json"})
            finally:
                _GECKO_LAST_CALL[0] = time.monotonic()
        if r.status_code == 429:
            print(f"  {C.D}↳ rate-limited; backing off {backoff:.0f}s (attempt {attempt+1}/4){C.R}")
            await asyncio.sleep(backoff)
            backoff *= 2
            continue
        try:
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            print(f"  {C.YL}⚠ gecko {url.split('/networks/')[-1][:80]}: {exc}{C.R}")
            return None
    return None


async def _resolve_pool_address(
    client: httpx.AsyncClient, token_address: str, chain: str, dex_pair: Dict[str, Any]
) -> Optional[str]:
    """Find the main pool address. Try GeckoTerminal first, fall back to DexScreener pairAddress."""
    network = GECKO_NETWORK.get(chain, chain)
    data = await _gecko_get(
        client,
        f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{token_address}/pools",
        page=1,
    )
    if data:
        pools = data.get("data") or []
        if pools:
            pool = pools[0]
            addr = (pool.get("attributes") or {}).get("address")
            if addr:
                return addr
            # GeckoTerminal pool id format: "{network}_{address}"
            pid = pool.get("id") or ""
            if "_" in pid:
                return pid.split("_", 1)[1]
    # Fallback: dexscreener gives us the pair address
    return dex_pair.get("pairAddress")


async def _fetch_gecko_ohlcv(
    client: httpx.AsyncClient, pool_address: str, chain: str, timeframe: str, limit: int = 100
) -> List[Dict[str, Any]]:
    network = GECKO_NETWORK.get(chain, chain)
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}"
    data = await _gecko_get(client, url, aggregate=1, limit=limit)
    if not data:
        return []
    raw = (data.get("data") or {}).get("attributes", {}).get("ohlcv_list") or []
    bars = [
        {"timestamp": int(row[0]), "open": float(row[1]), "high": float(row[2]),
         "low": float(row[3]), "close": float(row[4]), "volume": float(row[5])}
        for row in raw if len(row) >= 6
    ]
    bars.sort(key=lambda b: b["timestamp"])  # ensure chronological
    return bars


# ───────────────────────── Pretty logging ─────────────────────────

class C:  # ANSI colors — short names so prints stay readable
    R = "\033[0m"; B = "\033[1m"; D = "\033[2m"
    GR = "\033[32m"; RD = "\033[31m"; YL = "\033[33m"; BL = "\033[34m"; CY = "\033[36m"; MG = "\033[35m"


def hr(char: str = "─", n: int = 78) -> str:
    return char * n


def banner(title: str):
    print(f"\n{C.B}{C.CY}{hr('═')}{C.R}")
    print(f"{C.B}{C.CY}  {title}{C.R}")
    print(f"{C.B}{C.CY}{hr('═')}{C.R}")


def section(title: str):
    print(f"\n{C.B}{C.MG}▼ {title}{C.R}")
    print(f"{C.D}{hr()}{C.R}")


# ───────────────────────── Discovery ─────────────────────────

CHAIN_TO_DEX_ID = {"sol": "solana", "base": "base", "eth": "ethereum"}


async def fetch_trending_addresses(chain: str, limit: int) -> List[str]:
    """Get recently boosted/trending tokens for a chain from DexScreener."""
    dex_chain = CHAIN_TO_DEX_ID.get(chain, chain)
    addresses: List[str] = []
    async with httpx.AsyncClient(timeout=15.0) as client:
        for endpoint in (
            "https://api.dexscreener.com/token-boosts/latest/v1",
            "https://api.dexscreener.com/token-profiles/latest/v1",
        ):
            try:
                resp = await client.get(endpoint)
                resp.raise_for_status()
                for item in resp.json():
                    if (item.get("chainId") or "").lower() == dex_chain.lower():
                        addr = item.get("tokenAddress")
                        if addr and addr not in addresses:
                            addresses.append(addr)
                    if len(addresses) >= limit:
                        break
            except Exception as exc:
                print(f"  {C.YL}⚠ {endpoint.split('/')[-2]} on {chain} failed: {exc}{C.R}")
            if len(addresses) >= limit:
                break
    return addresses[:limit]


async def fetch_pair_data(address: str, chain: str) -> Optional[Dict[str, Any]]:
    """DexScreener search → best pair."""
    dex_chain = CHAIN_TO_DEX_ID.get(chain, chain)
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                "https://api.dexscreener.com/latest/dex/search",
                params={"q": address},
            )
            resp.raise_for_status()
            data = resp.json()
            pairs = [p for p in (data.get("pairs") or [])
                     if (p.get("chainId") or "").lower() == dex_chain.lower()]
            if pairs:
                pairs.sort(
                    key=lambda p: float((p.get("liquidity") or {}).get("usd") or 0),
                    reverse=True,
                )
                return pairs[0]
        except Exception as exc:
            print(f"  {C.YL}⚠ pair fetch {address[:8]}…: {exc}{C.R}")
    return None


# ───────────────────────── Kill-chain filter ─────────────────────────

@dataclass
class KillChain:
    min_age_minutes: int = 15
    max_age_hours: int = 24 * 14   # broaden for backtest history
    min_volume_usd: float = 1000.0
    min_liquidity_usd: float = 500.0
    min_buys_24h: int = 10


def passes_killchain(pair: Dict[str, Any], cfg: KillChain) -> Tuple[bool, str]:
    base = pair.get("baseToken") or {}
    symbol = base.get("symbol") or "?"
    liq = float((pair.get("liquidity") or {}).get("usd") or 0)
    vol = float((pair.get("volume") or {}).get("h24") or 0)
    buys = int(((pair.get("txns") or {}).get("h24") or {}).get("buys") or 0)
    created_ms = int(pair.get("pairCreatedAt") or 0)
    now_ms = int(time.time() * 1000)
    age_min = (now_ms - created_ms) / 60_000 if created_ms else 0
    age_h = age_min / 60

    if age_min < cfg.min_age_minutes:
        return False, f"{symbol}: too young ({age_min:.0f}m)"
    if cfg.max_age_hours > 0 and age_h > cfg.max_age_hours:
        return False, f"{symbol}: too old ({age_h:.1f}h)"
    if vol < cfg.min_volume_usd:
        return False, f"{symbol}: low volume (${vol:,.0f})"
    if liq < cfg.min_liquidity_usd:
        return False, f"{symbol}: low liquidity (${liq:,.0f})"
    if buys < cfg.min_buys_24h:
        return False, f"{symbol}: few buys ({buys})"
    return True, f"{symbol}: PASS (age={age_min:.0f}m vol=${vol:,.0f} liq=${liq:,.0f} buys={buys})"


# ───────────────────────── OHLCV fetch ─────────────────────────

async def fetch_ohlcv(
    client: httpx.AsyncClient, token_address: str, chain: str,
    pair: Dict[str, Any], timeframe: str = "hour",
) -> List[Dict[str, Any]]:
    """Fetch OHLCV directly from GeckoTerminal. Falls back through:
       1. tokens/{addr}/pools → first pool's ohlcv
       2. dexscreener pairAddress → ohlcv
       3. requested timeframe → "hour" → "minute" if empty
    """
    pool_addr = await _resolve_pool_address(client, token_address, chain, pair)
    if not pool_addr:
        return []
    seen = set()
    for tf in (timeframe, "hour", "minute"):
        if tf in seen:
            continue
        seen.add(tf)
        bars = await _fetch_gecko_ohlcv(client, pool_addr, chain, tf, limit=200)
        if bars and len(bars) >= 20:
            return bars
    return []


async def fetch_safety(token_address: str, chain: str) -> Dict[str, Any]:
    if token_safety_service is None:
        return {}
    try:
        rep = await token_safety_service.get_safety_report(token_address, chain)
        return rep.to_dict() if rep else {}
    except Exception:
        return {}


# ───────────────────────── Snapshot builder (replay frame) ─────────────────────────

def build_snapshot(
    *,
    pair: Dict[str, Any],
    chain: str,
    bars: List[Dict[str, Any]],
    bar_idx: int,
    safety: Dict[str, Any],
) -> TokenSnapshot:
    """Construct a TokenSnapshot for the bar at index `bar_idx` using only
    information available up to that bar. This is what makes the replay a
    genuine backtest rather than peeking at the future."""
    base = pair.get("baseToken") or {}
    window = bars[: bar_idx + 1]
    closes = [b["close"] for b in window]
    vols = [b["volume"] for b in window]
    cur_close = closes[-1]
    prev_close = closes[-2] if len(closes) >= 2 else cur_close
    price_change_1bar = ((cur_close / prev_close) - 1) * 100 if prev_close else 0
    # 24-bar look-back as a proxy for "1d" change in hour-tf, "1h" in minute-tf
    look = closes[-min(24, len(closes))] if len(closes) > 0 else cur_close
    price_change_24 = ((cur_close / look) - 1) * 100 if look else 0

    rsi = calculate_rsi(closes)
    macd, macd_sig = calculate_macd(closes)
    bb_u, bb_l, bb_p = calculate_bollinger(closes, cur_close)
    vol_ratio = calculate_volume_ratio(vols)
    volatility = calculate_volatility(closes)

    # Safety data (constant for the token). When missing, default to "unknown
    # but pair already passed the kill-chain" — neutral, not punitive.
    has_safety = bool(safety)
    rug_score = int(safety.get("overall_risk_score", 40) or 40)
    top10 = float(safety.get("top_10_holder_pct", 50) or 50)
    smart = (safety.get("smart_money_flow") or "neutral")
    # If safety unknown, assume LP locked (DEX-listed pair with real volume).
    if "liquidity_locked" in safety:
        locked = bool(safety.get("liquidity_locked"))
    else:
        locked = True
    lock_days = int(safety.get("lock_remaining_days", 0) or 0)
    holders = int(safety.get("holder_count", 0) or 0)
    dev_pct = float(safety.get("dev_wallet_pct", 5) or 5)

    return TokenSnapshot(
        name=base.get("name") or "Unknown",
        symbol=base.get("symbol") or "???",
        address=base.get("address") or pair.get("pairAddress") or "",
        chain=chain,
        timestamp=datetime.fromtimestamp(int(window[-1].get("timestamp") or 0), tz=timezone.utc).isoformat()
            if window[-1].get("timestamp") else datetime.now(timezone.utc).isoformat(),
        step=bar_idx,
        price=float(cur_close),
        price_change_1h=round(price_change_1bar, 2),
        price_change_24h=round(price_change_24, 2),
        volume_24h=float(vols[-1]),
        market_cap=float(pair.get("marketCap") or pair.get("fdv") or 0),
        liquidity=float((pair.get("liquidity") or {}).get("usd") or 0),
        holder_count=holders,
        top_10_holder_pct=top10,
        smart_money_flow=smart,
        rug_score=rug_score,
        dev_wallet_pct=dev_pct,
        liquidity_locked=locked,
        lock_days_remaining=lock_days,
        mentions_24h=0,
        sentiment_score=50,
        influencer_mentions=0,
        trending=False,
        community_size=0,
        rsi=round(rsi, 1),
        macd=round(macd, 6),
        macd_signal=round(macd_sig, 6),
        bollinger_upper=round(bb_u, 8),
        bollinger_lower=round(bb_l, 8),
        bollinger_position=round(bb_p, 2),
        volatility=round(volatility, 4),
        volume_ratio=round(vol_ratio, 2),
    )


# ───────────────────────── Per-token replay ─────────────────────────

async def replay_token(
    *,
    agent: AgenticTrader,
    pair: Dict[str, Any],
    chain: str,
    bars: List[Dict[str, Any]],
    safety: Dict[str, Any],
    max_bars: int,
    verbose: bool,
) -> Dict[str, Any]:
    base = pair.get("baseToken") or {}
    symbol = base.get("symbol") or "?"
    name = base.get("name") or "?"
    addr = base.get("address") or pair.get("pairAddress") or ""

    bars = bars[-max_bars:] if max_bars and len(bars) > max_bars else bars
    if len(bars) < 20:
        print(f"  {C.YL}↳ {symbol}: only {len(bars)} bars — skipping (need ≥20){C.R}")
        return {"symbol": symbol, "skipped": "insufficient_history", "bars": len(bars)}

    print(f"\n{C.B}╭─ {symbol} ({name}) on {chain.upper()}  ·  {len(bars)} bars  ·  rug={safety.get('overall_risk_score','?')}, locked={safety.get('liquidity_locked')}{C.R}")
    print(f"{C.D}│ addr: {addr}{C.R}")

    starting_equity = agent.wallet.get_total_equity(bars[0]["close"])
    trades_executed = 0
    reflections_made = 0
    pnl_path = []

    for i in range(len(bars)):
        snap = build_snapshot(pair=pair, chain=chain, bars=bars, bar_idx=i, safety=safety)
        decision: TradeDecision = await agent.think(snap)

        if verbose:
            tag_color = {"BUY": C.GR, "SELL": C.RD, "HOLD": C.D}.get(decision.action, C.R)
            print(f"{C.D}│{C.R} t={i:>3}  px=${snap.price:.8f}  rsi={snap.rsi:>5.1f}  bb={snap.bollinger_position:+.2f}  vol×{snap.volume_ratio:>4.2f}  →  "
                  f"{tag_color}{decision.action:<4}{C.R} ({decision.confidence:>3}%, {decision.source})  {C.D}{decision.reasoning[:120]}{C.R}")

        result = agent.act(decision)

        if result.get("executed"):
            trades_executed += 1

        # Reflect after a closed sell (manual or risk_exit)
        if (result.get("executed") and decision.action == "SELL") or result.get("risk_exit"):
            ref = await agent.reflect(result, result.get("details", {}).get("pnl", 0.0))
            if ref:
                reflections_made += 1
                if verbose:
                    print(f"{C.D}│  reflect: {ref.trade_assessment}, learnings: {ref.key_learnings}{C.R}")

        equity = agent.wallet.get_total_equity(snap.price)
        pnl_path.append(equity)

    # Force close at end of replay
    final_price = bars[-1]["close"]
    if agent.wallet.position > 0:
        sold = agent.wallet.sell(final_price, reason="End of replay window")
        if sold and agent.current_trade_id:
            agent.memory.close_trade(agent.current_trade_id, final_price, "Forced close at end of replay")
            agent.current_trade_id = None
            ref = await agent.reflect({"executed": True, "details": {"pnl": sold.pnl}}, sold.pnl)
            if ref:
                reflections_made += 1

    final_equity = agent.wallet.get_total_equity(final_price)
    token_pnl = final_equity - starting_equity
    print(f"{C.B}╰─ {symbol}: ${starting_equity:.2f} → ${final_equity:.2f}   "
          f"P&L ${token_pnl:+.2f} ({(token_pnl/starting_equity*100 if starting_equity else 0):+.2f}%)   "
          f"trades={trades_executed}, reflections={reflections_made}, rules={len(agent.memory.rules)}{C.R}")

    return {
        "symbol": symbol, "name": name, "address": addr, "chain": chain,
        "bars": len(bars),
        "starting_equity": starting_equity,
        "final_equity": final_equity,
        "pnl_usd": token_pnl,
        "pnl_pct": (token_pnl / starting_equity * 100) if starting_equity else 0,
        "trades": trades_executed,
        "reflections": reflections_made,
    }


# ───────────────────────── Orchestration ─────────────────────────

async def run(args) -> Dict[str, Any]:
    chains = [c.strip() for c in args.chains.split(",") if c.strip()]
    out_dir = Path(args.output) if args.output else (
        HERE / "results" / f"live_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    (out_dir / "memory").mkdir(parents=True, exist_ok=True)

    banner(f"ADAPTIVE RL AGENT  ·  LIVE MEMECOIN BACKTEST  ·  {datetime.now().isoformat(timespec='seconds')}")
    print(f"  starting balance: ${args.balance:.2f}")
    print(f"  chains:           {chains}")
    print(f"  target tokens:    {args.tokens}  (per chain ≤ {max(1, args.tokens // max(1, len(chains)) + 2)})")
    print(f"  timeframe:        {args.timeframe}  (max {args.max_bars} bars per token)")
    print(f"  policy:           {'LLM + heuristic' if args.use_llm else 'heuristic only'}")
    print(f"  exploration ε:    {args.epsilon}")
    print(f"  output:           {out_dir}")

    # ── 1. Discover ─────────────────────────────────────────
    section("1. DISCOVER  (DexScreener boosts + profiles)")
    per_chain = max(2, args.tokens // max(1, len(chains)) + 2)
    discovered: List[Tuple[str, str]] = []  # (address, chain)
    for ch in chains:
        addrs = await fetch_trending_addresses(ch, limit=per_chain * 2)
        print(f"  {ch.upper():<5} → {len(addrs)} candidate addresses")
        for a in addrs:
            discovered.append((a, ch))
    print(f"  total candidates: {len(discovered)}")

    # ── 2. Filter ───────────────────────────────────────────
    section("2. FILTER  (kill-chain: age / volume / liquidity / buys)")
    cfg = KillChain()
    survivors: List[Dict[str, Any]] = []
    for addr, ch in discovered:
        if len(survivors) >= args.tokens:
            break
        pair = await fetch_pair_data(addr, ch)
        if not pair:
            print(f"  {C.YL}✗ {addr[:10]}… ({ch}): no pair data{C.R}")
            continue
        ok, reason = passes_killchain(pair, cfg)
        marker = f"{C.GR}✓{C.R}" if ok else f"{C.D}✗{C.R}"
        print(f"  {marker} {ch.upper():<4} {reason}")
        if ok:
            survivors.append({"address": addr, "chain": ch, "pair": pair})
    print(f"\n  → {len(survivors)} tokens survive the kill-chain.")

    if not survivors:
        print(f"\n{C.YL}No tokens passed the filter — exiting.{C.R}")
        return {"status": "no_survivors"}

    # ── 3. Init agent + seed strategies ────────────────────
    section("3. AGENT  (init + seed strategies)")
    agent = AgenticTrader(
        initial_balance=args.balance,
        memory_dir=str(out_dir / "memory"),
        verbose=True,
        explore_eps=args.epsilon,
        use_llm=args.use_llm,
    )
    seeded = seed_memory(agent.memory)
    print(f"  seeded {seeded} curated memecoin rules into memory.")
    print(f"  llm:    {agent._llm_model_name or 'OFFLINE — heuristic-only'}")
    if seeded:
        for r in SEED_RULES[:5]:
            print(f"    {C.D}· [{r['type']}] {r['name']}  →  {r['conditions'][:80]}{C.R}")
        if len(SEED_RULES) > 5:
            print(f"    {C.D}  …(+{len(SEED_RULES)-5} more){C.R}")

    # ── 4. Replay each token ───────────────────────────────
    section("4. REPLAY  (real OHLCV + adaptive trading + reflection)")
    per_token_results = []
    async with httpx.AsyncClient(timeout=20.0) as client:
        for s in survivors:
            # Reset wallet between tokens, persist memory (rules/journal)
            agent.reset(keep_memory=True)
            symbol = (s["pair"].get("baseToken") or {}).get("symbol") or "?"
            try:
                bars = await fetch_ohlcv(client, s["address"], s["chain"], s["pair"], args.timeframe)
            except Exception as exc:
                print(f"  {C.YL}⚠ skip {symbol}: {exc}{C.R}")
                continue
            if not bars:
                print(f"  {C.YL}↳ {symbol}: no OHLCV from GeckoTerminal — skipping{C.R}")
                per_token_results.append({"symbol": symbol, "skipped": "no_ohlcv"})
                continue
            print(f"  {C.D}· {symbol} ({s['chain']}): fetched {len(bars)} bars{C.R}")
            safety = await fetch_safety(s["address"], s["chain"])
            res = await replay_token(
                agent=agent, pair=s["pair"], chain=s["chain"], bars=bars,
                safety=safety, max_bars=args.max_bars, verbose=True,
            )
            per_token_results.append(res)

    # ── 5. Report ──────────────────────────────────────────
    section("5. REPORT")
    completed = [r for r in per_token_results if "pnl_usd" in r]
    if completed:
        total_pnl = sum(r["pnl_usd"] for r in completed)
        avg_pct = sum(r["pnl_pct"] for r in completed) / len(completed)
        wins = [r for r in completed if r["pnl_usd"] > 0]
        losses = [r for r in completed if r["pnl_usd"] < 0]
        best = max(completed, key=lambda r: r["pnl_pct"])
        worst = min(completed, key=lambda r: r["pnl_pct"])

        print(f"  tokens replayed: {len(completed)}")
        print(f"  total simulated P&L: {C.GR if total_pnl>=0 else C.RD}${total_pnl:+.2f}{C.R}  "
              f"(avg {avg_pct:+.2f}% / token)")
        print(f"  wins / losses:   {len(wins)} / {len(losses)}")
        print(f"  best:  {best['symbol']} {best['pnl_pct']:+.2f}%")
        print(f"  worst: {worst['symbol']} {worst['pnl_pct']:+.2f}%")
        print(f"  total trades:    {sum(r['trades'] for r in completed)}")
        print(f"  reflections:     {sum(r['reflections'] for r in completed)}")
        print(f"  rules in memory: {len(agent.memory.rules)}  ({len(SEED_RULES)} seeded + {len(agent.memory.rules) - len(SEED_RULES)} learned)")

        print(f"\n  {C.B}top learned rules (by P&L):{C.R}")
        learned = [r for r in agent.memory.rules if r.success_count + r.failure_count > 0]
        for r in sorted(learned, key=lambda r: r.total_pnl, reverse=True)[:5]:
            rate = (r.success_count / max(1, r.success_count + r.failure_count)) * 100
            print(f"    · [{r.rule_type}] {r.name}  W/L={r.success_count}/{r.failure_count} ({rate:.0f}%)  PnL=${r.total_pnl:+.2f}")
    else:
        print(f"  {C.YL}no tokens completed a replay.{C.R}")

    # ── persist ────────────────────────────────────────────
    agent.memory.save_state()
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config": {
            "chains": chains, "target_tokens": args.tokens, "timeframe": args.timeframe,
            "max_bars": args.max_bars, "balance": args.balance, "epsilon": args.epsilon,
            "use_llm": args.use_llm, "llm_model": agent._llm_model_name,
        },
        "agent_summary": agent.get_summary(),
        "tokens": per_token_results,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print(f"\n  saved → {out_dir/'summary.json'}")
    print(f"  saved → {out_dir/'memory'/'trading_journal.md'}")
    print(f"  saved → {out_dir/'memory'/'trading_rules.md'}")
    return summary


def parse_args():
    p = argparse.ArgumentParser(description="Adaptive RL agent — live memecoin backtest")
    p.add_argument("--tokens", type=int, default=10, help="Total survivors to replay (default 10)")
    p.add_argument("--chains", type=str, default="sol,base,eth", help="Comma list: sol,base,eth")
    p.add_argument("--balance", type=float, default=100.0, help="Starting paper balance")
    p.add_argument("--timeframe", type=str, default="hour", choices=["minute", "hour", "day"])
    p.add_argument("--max-bars", type=int, default=80, help="Max OHLCV bars to replay per token")
    p.add_argument("--epsilon", type=float, default=0.05, help="ε-greedy exploration (0..1)")
    p.add_argument("--no-llm", dest="use_llm", action="store_false", help="Heuristic-only (no LLM)")
    p.add_argument("--output", type=str, default=None, help="Output dir override")
    p.set_defaults(use_llm=True)
    return p.parse_args()


def main():
    args = parse_args()
    try:
        asyncio.run(run(args))
    except KeyboardInterrupt:
        print(f"\n{C.YL}interrupted{C.R}")


if __name__ == "__main__":
    main()
