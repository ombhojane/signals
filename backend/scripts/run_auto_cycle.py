"""
Autonomous trading cycle client.

Hits POST /rl-trade/auto-cycle on the local backend, which:
  1. Asks Gemini to analyze WETH/USDC and approve the entry.
  2. Vault buys WETH with `amount_usdc` USDC on Base Sepolia.
  3. Polls live WETH→USDC quote; exits on take-profit, stop-loss,
     timeout, or Gemini SELL.
  4. Vault swaps the WETH back to USDC.
  5. Returns a P&L summary with every reasoning step.

Prereqs:
  - Backend running:  cd backend && ./venv/bin/python main.py
  - backend/.env has BASE_RPC_URL=https://sepolia.base.org,
    VAULT_ADDRESS, AGENT_PRIVATE_KEY, GOOGLE_API_KEY

Usage:
  ./venv/bin/python scripts/run_auto_cycle.py
  ./venv/bin/python scripts/run_auto_cycle.py --take 1.5 --stop 1.0 --window 90 --poll 8 --usdc 1
"""
from __future__ import annotations
import argparse, json, sys, urllib.error, urllib.parse, urllib.request


def hit(url, params, timeout):
    qs = urllib.parse.urlencode(params)
    full = f"{url.rstrip('/')}/rl-trade/auto-cycle?{qs}"
    print(f"POST {full}\n(this can take up to {params['max_monitor_seconds']}s while monitoring)…\n")
    req = urllib.request.Request(full, method="POST", headers={"accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def fmt(d):
    B, GR, RD, CY, YL, MG, D, R = "\033[1m", "\033[32m", "\033[31m", "\033[36m", "\033[33m", "\033[35m", "\033[2m", "\033[0m"
    print(f"\n{B}{CY}{'═'*78}{R}")
    print(f"{B}{CY}  AUTONOMOUS CYCLE  ·  {d['asset']}  ·  Base Sepolia  ·  Gemini-driven{R}")
    print(f"{B}{CY}{'═'*78}{R}")
    print(f"  vault:           {d['vault']}")
    print(f"  agent:           {d['agent']}")
    print(f"  chain_id:        {d['chain_id']}")
    print(f"  gemini model:    {d.get('gemini_model') or 'OFFLINE'}")
    print(f"  duration:        {d['duration_sec']}s")

    e = d["entry"]
    if e.get("skipped"):
        print(f"\n  {YL}Gemini declined entry:{R} {e.get('gemini', {}).get('reasoning', '?')}")
        return
    print(f"\n{B}{GR}── ENTRY  (USDC → WETH) ───────────────────────────────────{R}")
    print(f"  status:        {e['status']}")
    print(f"  tx:            {e['tx_hash']}")
    print(f"  block / gas:   {e['block']}  /  {e['gas_used']}")
    print(f"  spent:         {e['amount_in']/1e6:.6f} USDC")
    print(f"  received:      {e['weth_acquired']:.10f} WETH  (rate: {e['entry_rate_usdc_per_weth']:.2f} USDC/WETH)")
    print(f"  reasoningHash: {e['reasoning_hash']}")
    print(f"  gemini conf:   {e['gemini_confidence']}%")
    print(f"  reasoning:     {D}{e['gemini_reasoning']}{R}")
    print(f"  explorer:      {e['explorer']}")

    print(f"\n{B}── MONITOR  (poll-by-poll) ────────────────────────────────{R}")
    if not d["monitor"]:
        print(f"  {D}no polls before exit{R}")
    for m in d["monitor"]:
        if m.get("error"):
            print(f"  poll {m['poll']:>2}: {YL}error: {m['error']}{R}")
            continue
        sign_color = GR if m["pnl_pct"] >= 0 else RD
        dec_color = {"SELL": RD, "HOLD": D}.get(m.get("decision", "HOLD"), R)
        print(f"  poll {m['poll']:>2}  t={m['elapsed_sec']:>5.1f}s  "
              f"value={m['current_value_usdc']:.6f} USDC  "
              f"P&L={sign_color}{m['pnl_pct']:+.3f}%{R}  →  "
              f"{dec_color}{m.get('decision', '?')}{R} ({m.get('source', '?')})  "
              f"{D}{m.get('reason', '')[:80]}{R}")

    x = d["exit"]
    print(f"\n{B}{MG}── EXIT  (WETH → USDC) ────────────────────────────────────{R}")
    print(f"  reason:        {x['exit_reason']}")
    print(f"  tx:            {x['tx_hash']}")
    print(f"  block / gas:   {x['block']}  /  {x['gas_used']}")
    print(f"  sold:          {x['weth_sold']:.10f} WETH")
    print(f"  realized:      {x['realized_usdc']:.6f} USDC")
    print(f"  reasoningHash: {x['reasoning_hash']}")
    print(f"  reasoning:     {D}{x['reasoning']}{R}")
    print(f"  explorer:      {x['explorer']}")

    color = GR if d["pnl_usdc"] >= 0 else RD
    print(f"\n{B}{color}── RESULT ─────────────────────────────────────────────────{R}")
    print(f"  {color}P&L:    {d['pnl_usdc']:+.6f} USDC  ({d['pnl_pct']:+.4f}%){R}")
    print(f"  duration: {d['duration_sec']}s   ·   exit: {d['exit_reason']}")
    print(f"  vault:    {d['explorer_vault']}\n")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--url", default="http://127.0.0.1:8000")
    p.add_argument("--usdc", type=float, default=1.0)
    p.add_argument("--take", type=float, default=1.5, help="take-profit %%")
    p.add_argument("--stop", type=float, default=1.0, help="stop-loss %%")
    p.add_argument("--window", type=int, default=90, help="max monitor seconds")
    p.add_argument("--poll", type=int, default=8, help="poll interval seconds")
    args = p.parse_args()

    params = {
        "amount_usdc": args.usdc,
        "take_profit_pct": args.take,
        "stop_loss_pct": args.stop,
        "max_monitor_seconds": args.window,
        "poll_seconds": args.poll,
    }
    try:
        data = hit(args.url, params, args.window + 120)
    except urllib.error.HTTPError as e:
        sys.exit(f"\n❌ {e.code}: {e.read().decode(errors='replace')}")
    except urllib.error.URLError as e:
        sys.exit(f"\n❌ cannot reach backend at {args.url}: {e}\n   Start it: cd backend && ./venv/bin/python main.py")
    fmt(data)


if __name__ == "__main__":
    main()
