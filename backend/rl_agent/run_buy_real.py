"""
Run the agentic trader on a fast synthetic market and, the moment a BUY
decision fires, execute a real 1 USDC transfer on Base Sepolia.

Loads AGENT_PRIVATE_KEY from backend/.env. Forces the public Base Sepolia
RPC (https://sepolia.base.org) — ignores BASE_RPC_URL if it points at a
local fork.

Usage:
    cd backend
    ./venv/bin/python rl_agent/run_buy_real.py
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from web3 import Web3

HERE = Path(__file__).resolve().parent
BACKEND_DIR = HERE.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

load_dotenv(BACKEND_DIR / ".env")

from rl_agent.agentic_trader import AgenticTrader, TradeDecision  # noqa: E402
from rl_agent.synthetic_market import SyntheticMarket  # noqa: E402
from rl_agent.strategies import seed_memory  # noqa: E402

BASE_SEPOLIA_RPC = "https://sepolia.base.org"
USDC_BASE_SEPOLIA = Web3.to_checksum_address("0x036CbD53842c5426634e7929541eC2318f3dCF7e")
AMOUNT_USDC = 1_000_000  # 1 USDC (6 decimals)

ERC20_ABI = [
    {"inputs": [{"name": "to", "type": "address"}, {"name": "value", "type": "uint256"}],
     "name": "transfer", "outputs": [{"name": "", "type": "bool"}],
     "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "account", "type": "address"}],
     "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}],
     "stateMutability": "view", "type": "function"},
]


def execute_real_buy(decision: TradeDecision, snap) -> dict:
    key = os.getenv("AGENT_PRIVATE_KEY")
    if not key:
        raise SystemExit("AGENT_PRIVATE_KEY missing in backend/.env")

    w3 = Web3(Web3.HTTPProvider(BASE_SEPOLIA_RPC))
    if not w3.is_connected():
        raise SystemExit(f"cannot reach {BASE_SEPOLIA_RPC}")

    account = w3.eth.account.from_key(key)
    me = account.address
    usdc = w3.eth.contract(address=USDC_BASE_SEPOLIA, abi=ERC20_ABI)

    bal = usdc.functions.balanceOf(me).call()
    print(f"\n  wallet:        {me}")
    print(f"  chain_id:      {w3.eth.chain_id}")
    print(f"  USDC balance:  {bal / 1e6:.6f} USDC")
    if bal < AMOUNT_USDC:
        raise SystemExit(f"insufficient USDC ({bal/1e6} < 1.0). Fund {me} with Base Sepolia USDC.")

    nonce = w3.eth.get_transaction_count(me)
    tx = usdc.functions.transfer(me, AMOUNT_USDC).build_transaction({
        "from": me,
        "nonce": nonce,
        "gas": 100_000,
        "maxFeePerGas": w3.eth.gas_price * 2,
        "maxPriorityFeePerGas": w3.to_wei(0.001, "gwei"),
        "chainId": w3.eth.chain_id,
    })
    signed = w3.eth.account.sign_transaction(tx, key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    h = "0x" + tx_hash.hex().removeprefix("0x")
    print(f"\n  📡 broadcast:   {h}")
    print(f"  waiting for confirmation…")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    return {
        "tx_hash": h,
        "status": "success" if receipt["status"] == 1 else "failed",
        "block": receipt["blockNumber"],
        "gas_used": receipt["gasUsed"],
        "from": me,
        "to": me,  # self-transfer demo
        "token": "USDC (Base Sepolia)",
        "token_address": USDC_BASE_SEPOLIA,
        "amount": "1.000000 USDC",
        "explorer": f"https://sepolia.basescan.org/tx/{h}",
        "decision": {
            "action": decision.action,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "source": decision.source,
            "target_symbol": snap.symbol,
            "target_price": snap.price,
        },
    }


async def main():
    print("\033[1;36m" + "═" * 78 + "\033[0m")
    print("\033[1;36m  RL AGENT  ·  REAL BASE SEPOLIA BUY EXECUTION  \033[0m")
    print("\033[1;36m" + "═" * 78 + "\033[0m")

    agent = AgenticTrader(initial_balance=100.0, verbose=True, use_llm=False)  # heuristic = fast & deterministic
    seeded = seed_memory(agent.memory)
    print(f"  agent ready  ·  {seeded} seed rules  ·  policy: heuristic")

    market = SyntheticMarket()
    print(f"  market: synthetic {market.symbol} ({market.chain})\n")

    max_steps = 200
    for step in range(max_steps):
        snap = market.step_market()
        decision: TradeDecision = await agent.think(snap)
        tag = {"BUY": "\033[32m", "SELL": "\033[31m", "HOLD": "\033[2m"}[decision.action]
        print(f"  t={step:>3}  px=${snap.price:.6f}  rsi={snap.rsi:>5.1f}  vol×{snap.volume_ratio:>4.2f}  →  "
              f"{tag}{decision.action:<4}\033[0m  ({decision.confidence}%)  {decision.reasoning[:90]}")

        if decision.action == "BUY":
            print(f"\n  🚀 BUY signal received — executing real on-chain trade…")
            result = execute_real_buy(decision, snap)

            print("\n\033[1;32m" + "═" * 78 + "\033[0m")
            print("\033[1;32m  TRANSACTION DETAILS\033[0m")
            print("\033[1;32m" + "═" * 78 + "\033[0m")
            print(f"  status:        {result['status']}")
            print(f"  tx hash:       {result['tx_hash']}")
            print(f"  block:         {result['block']}")
            print(f"  gas used:      {result['gas_used']}")
            print(f"  from:          {result['from']}")
            print(f"  to:            {result['to']}")
            print(f"  token:         {result['token']}")
            print(f"  token addr:    {result['token_address']}")
            print(f"  amount:        {result['amount']}")
            print(f"  explorer:      {result['explorer']}")
            print()
            print(f"  agent decision:")
            print(f"    action:      {result['decision']['action']}")
            print(f"    confidence:  {result['decision']['confidence']}%")
            print(f"    source:      {result['decision']['source']}")
            print(f"    target:      {result['decision']['target_symbol']} @ ${result['decision']['target_price']:.6f}")
            print(f"    reasoning:   {result['decision']['reasoning']}")
            print()
            return

    print(f"\n  no BUY signal in {max_steps} steps — try again.")


if __name__ == "__main__":
    asyncio.run(main())
