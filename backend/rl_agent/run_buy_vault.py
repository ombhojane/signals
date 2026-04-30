"""
Run the agentic trader on a fast synthetic market and, the moment a BUY
decision fires, execute a real Uniswap V3 swap THROUGH the HypeScanVault on
Base Sepolia (1 USDC → WETH).

Loads AGENT_PRIVATE_KEY from backend/.env. Uses public Base Sepolia RPC.
"""
from __future__ import annotations

import asyncio
import hashlib
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

RPC = "https://sepolia.base.org"
VAULT = Web3.to_checksum_address("0xdf57590D27f02BcFA8522d4a59E07Ca7a31b9a6a")
USDC = Web3.to_checksum_address("0x036CbD53842c5426634e7929541eC2318f3dCF7e")
WETH = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")
POOL_FEE = 3000   # 0.3% — deepest liquidity on Base Sepolia
AMOUNT_IN = 1_000_000  # 1 USDC

VAULT_ABI = [
    {"inputs": [
        {"name": "tokenIn", "type": "address"},
        {"name": "tokenOut", "type": "address"},
        {"name": "poolFee", "type": "uint24"},
        {"name": "amountIn", "type": "uint256"},
        {"name": "amountOutMinimum", "type": "uint256"},
        {"name": "reasoningHash", "type": "bytes32"},
        {"name": "confidence", "type": "uint8"},
     ], "name": "executeTrade", "outputs": [{"type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [], "name": "agent", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "asset", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "positionOpen", "outputs": [{"type": "bool"}], "stateMutability": "view", "type": "function"},
    {"anonymous": False, "inputs": [
        {"indexed": True, "name": "tokenIn", "type": "address"},
        {"indexed": True, "name": "tokenOut", "type": "address"},
        {"indexed": False, "name": "amountIn", "type": "uint256"},
        {"indexed": False, "name": "amountOut", "type": "uint256"},
        {"indexed": True, "name": "reasoningHash", "type": "bytes32"},
        {"indexed": False, "name": "confidence", "type": "uint8"},
        {"indexed": False, "name": "timestamp", "type": "uint256"},
     ], "name": "TradeExecuted", "type": "event"},
]
ERC20_ABI = [
    {"inputs": [{"name": "a", "type": "address"}], "name": "balanceOf",
     "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"},
]


def execute_vault_trade(decision: TradeDecision, snap) -> dict:
    key = os.getenv("AGENT_PRIVATE_KEY")
    if not key:
        raise SystemExit("AGENT_PRIVATE_KEY missing in backend/.env")

    w3 = Web3(Web3.HTTPProvider(RPC))
    if not w3.is_connected():
        raise SystemExit(f"cannot reach {RPC}")

    me = w3.eth.account.from_key(key).address
    vault = w3.eth.contract(address=VAULT, abi=VAULT_ABI)
    usdc = w3.eth.contract(address=USDC, abi=ERC20_ABI)
    weth = w3.eth.contract(address=WETH, abi=ERC20_ABI)

    on_chain_agent = vault.functions.agent().call()
    if on_chain_agent.lower() != me.lower():
        raise SystemExit(f"wallet {me} is not the vault's agent ({on_chain_agent})")

    vault_usdc_before = usdc.functions.balanceOf(VAULT).call()
    vault_weth_before = weth.functions.balanceOf(VAULT).call()
    print(f"\n  vault:           {VAULT}")
    print(f"  agent (us):      {me}")
    print(f"  vault USDC:      {vault_usdc_before / 1e6:.6f}")
    print(f"  vault WETH:      {vault_weth_before / 1e18:.8f}")
    print(f"  positionOpen:    {vault.functions.positionOpen().call()}")
    if vault_usdc_before < AMOUNT_IN:
        raise SystemExit(f"vault has insufficient USDC: {vault_usdc_before/1e6} < 1")

    reasoning_str = f"{decision.action}|{decision.confidence}|{decision.source}|{decision.reasoning}"
    reasoning_hash = bytes.fromhex(hashlib.sha256(reasoning_str.encode()).hexdigest())
    confidence = max(0, min(100, int(decision.confidence)))

    # eth_call simulation first (cheap revert check)
    fn = vault.functions.executeTrade(USDC, WETH, POOL_FEE, AMOUNT_IN, 0, reasoning_hash, confidence)
    try:
        sim_out = fn.call({"from": me})
        print(f"  simulation:      OK — would receive {sim_out} wei WETH ({sim_out/1e18:.8f} WETH)")
    except Exception as exc:
        raise SystemExit(f"simulation reverted: {exc}")

    nonce = w3.eth.get_transaction_count(me)
    tx = fn.build_transaction({
        "from": me,
        "nonce": nonce,
        "gas": 500_000,
        "maxFeePerGas": w3.eth.gas_price * 2,
        "maxPriorityFeePerGas": w3.to_wei(0.001, "gwei"),
        "chainId": w3.eth.chain_id,
    })
    signed = w3.eth.account.sign_transaction(tx, key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    h = "0x" + tx_hash.hex().removeprefix("0x")
    print(f"\n  📡 broadcast:     {h}")
    print(f"  awaiting confirmation…")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

    # Decode TradeExecuted event for amountOut
    amount_out = None
    try:
        evts = vault.events.TradeExecuted().process_receipt(receipt)
        if evts:
            amount_out = evts[0]["args"]["amountOut"]
    except Exception:
        pass

    vault_usdc_after = usdc.functions.balanceOf(VAULT).call()
    vault_weth_after = weth.functions.balanceOf(VAULT).call()

    return {
        "tx_hash": h,
        "status": "success" if receipt["status"] == 1 else "failed",
        "block": receipt["blockNumber"],
        "gas_used": receipt["gasUsed"],
        "vault": VAULT,
        "agent": me,
        "token_in": "USDC",
        "token_in_addr": USDC,
        "token_out": "WETH",
        "token_out_addr": WETH,
        "pool_fee": f"{POOL_FEE/10000:.2f}%",
        "amount_in": "1.000000 USDC",
        "amount_out_wei": amount_out,
        "amount_out_eth": (amount_out / 1e18) if amount_out else None,
        "vault_usdc_before": vault_usdc_before / 1e6,
        "vault_usdc_after": vault_usdc_after / 1e6,
        "vault_weth_before": vault_weth_before / 1e18,
        "vault_weth_after": vault_weth_after / 1e18,
        "reasoning_hash": "0x" + reasoning_hash.hex(),
        "explorer_tx": f"https://sepolia.basescan.org/tx/{h}",
        "explorer_vault": f"https://sepolia.basescan.org/address/{VAULT}",
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
    print("\033[1;36m  RL AGENT  ·  REAL VAULT TRADE  ·  BASE SEPOLIA  \033[0m")
    print("\033[1;36m" + "═" * 78 + "\033[0m")

    agent = AgenticTrader(initial_balance=100.0, verbose=True, use_llm=False)
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
            print(f"\n  🚀 BUY signal — calling vault.executeTrade(USDC → WETH, 1 USDC) on Base Sepolia…")
            r = execute_vault_trade(decision, snap)

            print("\n\033[1;32m" + "═" * 78 + "\033[0m")
            print("\033[1;32m  VAULT TRADE  ·  TRANSACTION DETAILS\033[0m")
            print("\033[1;32m" + "═" * 78 + "\033[0m")
            print(f"  status:           {r['status']}")
            print(f"  tx hash:          {r['tx_hash']}")
            print(f"  block:            {r['block']}")
            print(f"  gas used:         {r['gas_used']}")
            print(f"  vault:            {r['vault']}")
            print(f"  agent (caller):   {r['agent']}")
            print(f"  swap:             {r['amount_in']}  →  "
                  f"{r['amount_out_eth']:.10f} {r['token_out']}" if r['amount_out_eth'] else
                  f"  swap:             {r['amount_in']}  →  ?")
            print(f"  pool fee:         {r['pool_fee']}")
            print(f"  reasoningHash:    {r['reasoning_hash']}")
            print()
            print(f"  vault USDC:       {r['vault_usdc_before']:.6f}  →  {r['vault_usdc_after']:.6f}")
            print(f"  vault WETH:       {r['vault_weth_before']:.8f}  →  {r['vault_weth_after']:.8f}")
            print()
            print(f"  explorer tx:      {r['explorer_tx']}")
            print(f"  explorer vault:   {r['explorer_vault']}")
            print()
            print(f"  agent decision:")
            print(f"    action:         {r['decision']['action']}")
            print(f"    confidence:     {r['decision']['confidence']}%")
            print(f"    source:         {r['decision']['source']}")
            print(f"    target:         {r['decision']['target_symbol']} @ ${r['decision']['target_price']:.6f}")
            print(f"    reasoning:      {r['decision']['reasoning']}")
            print()
            return

    print(f"\n  no BUY signal in {max_steps} steps — try again.")


if __name__ == "__main__":
    asyncio.run(main())
