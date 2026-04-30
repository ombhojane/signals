"""
One-shot client for the RL-trade endpoint.

Hits POST /rl-trade/run on the local backend, runs the agent through a
synthetic market, executes up to `max_trades` real Uniswap V3 swaps
(1 USDC → WETH each) through the SignalsVault on Base Sepolia, and
prints a clean summary.

Prereqs:
  1. Backend running:   cd backend && ./venv/bin/python main.py
  2. backend/.env has   BASE_RPC_URL=https://sepolia.base.org
                        VAULT_ADDRESS=0xdf57590D27f02BcFA8522d4a59E07Ca7a31b9a6a
                        AGENT_PRIVATE_KEY=0x...   (funded vault agent)

Usage:
  ./venv/bin/python scripts/run_rl_trade.py
  ./venv/bin/python scripts/run_rl_trade.py --max-trades 2 --url http://127.0.0.1:8000
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request


def hit(url: str, max_trades: int, max_steps: int, timeout: int) -> dict:
    qs = urllib.parse.urlencode({"max_trades": max_trades, "max_steps": max_steps})
    full = f"{url.rstrip('/')}/rl-trade/run?{qs}"
    print(f"POST {full}")
    req = urllib.request.Request(full, method="POST", headers={"accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def fmt(d: dict) -> None:
    C_B, C_GR, C_CY, C_D, C_R = "\033[1m", "\033[32m", "\033[36m", "\033[2m", "\033[0m"

    print(f"\n{C_B}{C_CY}{'═'*78}{C_R}")
    print(f"{C_B}{C_CY}  RL AGENT  ·  REAL VAULT TRADES  ·  BASE SEPOLIA{C_R}")
    print(f"{C_B}{C_CY}{'═'*78}{C_R}")
    print(f"  vault:           {d['vault']}")
    print(f"  agent:           {d['agent']}")
    print(f"  chain_id:        {d['chain_id']}")
    print(f"  steps taken:     {d['steps_taken']}")
    print(f"  buy signals:     {d['buy_signals']}")
    print(f"  trades executed: {d['trades_executed']} / {d['max_trades']}")

    print(f"\n{C_B}Decision log (last 6):{C_R}")
    tail = d["decisions_log"][-6:]
    for row in tail:
        tag = {"BUY": C_GR, "SELL": "\033[31m", "HOLD": C_D}.get(row["action"], C_R)
        print(f"  t={row['step']:>3}  {row['symbol']:<6}  px=${row['price']:.6f}  "
              f"rsi={row['rsi']:>5.1f}  vol×{row['vol_ratio']:>4.2f}  →  "
              f"{tag}{row['action']:<4}{C_R} ({row['confidence']:>3}%)  "
              f"{C_D}{row['reasoning'][:80]}{C_R}")

    if not d["trades"]:
        print(f"\n  {C_D}no BUY signals — no trades executed{C_R}")
        return

    for i, t in enumerate(d["trades"], 1):
        print(f"\n{C_B}{C_GR}── TRADE #{i}  (step {t['step']}) ───────────────────────{C_R}")
        print(f"  status:           {t['status']}")
        print(f"  tx hash:          {t['tx_hash']}")
        print(f"  block:            {t['block']}")
        print(f"  gas used:         {t['gas_used']}")
        print(f"  swap:             {t['amount_in_usdc']:.6f} USDC  →  "
              f"{t['amount_out_weth']:.10f} WETH")
        print(f"  pool fee:         {t['pool_fee_bps']/10000:.2f}%")
        print(f"  reasoningHash:    {t['reasoning_hash']}")
        print(f"  explorer:         {t['explorer_tx']}")
        print(f"  decision:         {t['decision']['action']} "
              f"{t['decision']['confidence']}% [{t['decision']['source']}]")
        print(f"    reasoning:      {t['decision']['reasoning']}")
        print(f"    target:         {t['target_symbol']} @ ${t['target_price']:.6f}")

    print(f"\n  vault explorer:   {d['explorer_vault']}\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8000")
    p.add_argument("--max-trades", type=int, default=2)
    p.add_argument("--max-steps", type=int, default=200)
    p.add_argument("--timeout", type=int, default=300)
    args = p.parse_args()

    try:
        data = hit(args.url, args.max_trades, args.max_steps, args.timeout)
    except urllib.error.URLError as e:
        sys.exit(f"\n❌ cannot reach backend at {args.url}: {e}\n"
                 f"   Start it first:  cd backend && ./venv/bin/python main.py")
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        sys.exit(f"\n❌ {e.code} from backend: {body}")

    fmt(data)


if __name__ == "__main__":
    main()
