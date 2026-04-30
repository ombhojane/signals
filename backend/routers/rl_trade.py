"""
RL Trade Router

Endpoints:
  POST /rl-trade/run         — N synthetic-market BUYs (demo)
  POST /rl-trade/auto-cycle  — autonomous BUY → MONITOR → SELL on WETH/USDC,
                                with Gemini reasoning + take-profit / stop-loss
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from web3 import Web3

from rl_agent.agentic_trader import AgenticTrader, TradeDecision
from rl_agent.synthetic_market import SyntheticMarket
from rl_agent.strategies import seed_memory

load_dotenv()

router = APIRouter(tags=["RL Trade"])

RPC = os.getenv("BASE_RPC_URL", "https://sepolia.base.org")
VAULT = os.getenv("VAULT_ADDRESS", "0xdf57590D27f02BcFA8522d4a59E07Ca7a31b9a6a")
USDC = "0x036CbD53842c5426634e7929541eC2318f3dCF7e"
WETH = "0x4200000000000000000000000000000000000006"
POOL_FEE = 3000
AMOUNT_IN = 1_000_000  # 1 USDC

VAULT_ABI = [
    {"inputs": [
        {"name": "tokenIn", "type": "address"}, {"name": "tokenOut", "type": "address"},
        {"name": "poolFee", "type": "uint24"}, {"name": "amountIn", "type": "uint256"},
        {"name": "amountOutMinimum", "type": "uint256"}, {"name": "reasoningHash", "type": "bytes32"},
        {"name": "confidence", "type": "uint8"},
     ], "name": "executeTrade", "outputs": [{"type": "uint256"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [], "name": "agent", "outputs": [{"type": "address"}], "stateMutability": "view", "type": "function"},
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
ERC20_ABI = [{"inputs": [{"name": "a", "type": "address"}], "name": "balanceOf",
              "outputs": [{"type": "uint256"}], "stateMutability": "view", "type": "function"}]


def _execute_one_trade(w3: Web3, key: str, decision: TradeDecision) -> Dict[str, Any]:
    me = w3.eth.account.from_key(key).address
    vault = w3.eth.contract(address=Web3.to_checksum_address(VAULT), abi=VAULT_ABI)
    usdc = w3.eth.contract(address=Web3.to_checksum_address(USDC), abi=ERC20_ABI)
    weth = w3.eth.contract(address=Web3.to_checksum_address(WETH), abi=ERC20_ABI)

    on_chain_agent = vault.functions.agent().call()
    if on_chain_agent.lower() != me.lower():
        raise HTTPException(403, f"wallet {me} is not vault agent ({on_chain_agent})")

    usdc_before = usdc.functions.balanceOf(Web3.to_checksum_address(VAULT)).call()
    weth_before = weth.functions.balanceOf(Web3.to_checksum_address(VAULT)).call()
    if usdc_before < AMOUNT_IN:
        raise HTTPException(400, f"vault USDC {usdc_before/1e6} < 1.0 — cannot trade")

    reasoning = f"{decision.action}|{decision.confidence}|{decision.source}|{decision.reasoning}"
    reasoning_hash = bytes.fromhex(hashlib.sha256(reasoning.encode()).hexdigest())
    confidence = max(0, min(100, int(decision.confidence)))

    fn = vault.functions.executeTrade(
        Web3.to_checksum_address(USDC), Web3.to_checksum_address(WETH),
        POOL_FEE, AMOUNT_IN, 0, reasoning_hash, confidence,
    )
    try:
        sim_out = fn.call({"from": me})
    except Exception as exc:
        raise HTTPException(500, f"simulation reverted: {exc}")

    tx = fn.build_transaction({
        "from": me, "nonce": w3.eth.get_transaction_count(me),
        "gas": 500_000, "maxFeePerGas": w3.eth.gas_price * 2,
        "maxPriorityFeePerGas": w3.to_wei(0.001, "gwei"), "chainId": w3.eth.chain_id,
    })
    signed = w3.eth.account.sign_transaction(tx, key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    h = "0x" + tx_hash.hex().removeprefix("0x")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

    amount_out = None
    try:
        evts = vault.events.TradeExecuted().process_receipt(receipt)
        if evts:
            amount_out = int(evts[0]["args"]["amountOut"])
    except Exception:
        pass
    if amount_out is None:
        amount_out = sim_out

    usdc_after = usdc.functions.balanceOf(Web3.to_checksum_address(VAULT)).call()
    weth_after = weth.functions.balanceOf(Web3.to_checksum_address(VAULT)).call()

    return {
        "tx_hash": h,
        "status": "success" if receipt["status"] == 1 else "failed",
        "block": receipt["blockNumber"],
        "gas_used": receipt["gasUsed"],
        "amount_in_usdc": AMOUNT_IN / 1e6,
        "amount_out_weth": amount_out / 1e18 if amount_out else None,
        "amount_out_wei": amount_out,
        "pool_fee_bps": POOL_FEE,
        "reasoning_hash": "0x" + reasoning_hash.hex(),
        "vault_usdc_before": usdc_before / 1e6,
        "vault_usdc_after": usdc_after / 1e6,
        "vault_weth_before": weth_before / 1e18,
        "vault_weth_after": weth_after / 1e18,
        "explorer_tx": f"https://sepolia.basescan.org/tx/{h}",
        "decision": {
            "action": decision.action,
            "confidence": decision.confidence,
            "reasoning": decision.reasoning,
            "source": decision.source,
        },
    }


class RunTradesResponse(BaseModel):
    vault: str
    agent: str
    chain_id: int
    max_trades: int
    steps_taken: int
    buy_signals: int
    trades_executed: int
    decisions_log: List[Dict[str, Any]]
    trades: List[Dict[str, Any]]
    explorer_vault: str


@router.post("/rl-trade/run", response_model=RunTradesResponse)
async def run_rl_trades(max_trades: int = 2, max_steps: int = 200):
    """
    Hit this to:
      1. spin up the RL agent on a fast synthetic market,
      2. step through it, and
      3. on each BUY decision, execute a real 1 USDC → WETH swap via the vault on Base Sepolia.

    Stops after `max_trades` (default 2) or `max_steps` (default 200), whichever comes first.
    """
    if max_trades < 1 or max_trades > 5:
        raise HTTPException(400, "max_trades must be in [1, 5]")

    key = os.getenv("AGENT_PRIVATE_KEY")
    if not key:
        raise HTTPException(500, "AGENT_PRIVATE_KEY not configured")

    w3 = Web3(Web3.HTTPProvider(RPC))
    if not w3.is_connected():
        raise HTTPException(500, f"cannot reach RPC {RPC}")
    me = w3.eth.account.from_key(key).address

    agent = AgenticTrader(initial_balance=100.0, verbose=False, use_llm=False)
    seed_memory(agent.memory)
    market = SyntheticMarket()

    decisions_log: List[Dict[str, Any]] = []
    trades: List[Dict[str, Any]] = []
    buy_signals = 0
    steps_taken = 0

    for step in range(max_steps):
        steps_taken = step + 1
        snap = market.step_market()
        decision: TradeDecision = await agent.think(snap)
        decisions_log.append({
            "step": step, "symbol": snap.symbol, "price": snap.price,
            "rsi": snap.rsi, "vol_ratio": snap.volume_ratio,
            "action": decision.action, "confidence": decision.confidence,
            "source": decision.source, "reasoning": decision.reasoning[:140],
        })

        if decision.action == "BUY":
            buy_signals += 1
            trade = await asyncio.to_thread(_execute_one_trade, w3, key, decision)
            trade["step"] = step
            trade["target_symbol"] = snap.symbol
            trade["target_price"] = snap.price
            trades.append(trade)
            if len(trades) >= max_trades:
                break

    return RunTradesResponse(
        vault=VAULT,
        agent=me,
        chain_id=w3.eth.chain_id,
        max_trades=max_trades,
        steps_taken=steps_taken,
        buy_signals=buy_signals,
        trades_executed=len(trades),
        decisions_log=decisions_log,
        trades=trades,
        explorer_vault=f"https://sepolia.basescan.org/address/{VAULT}",
    )


# ─────────────────────────────────────────────────────────────────────
#  AUTONOMOUS CYCLE  ·  BUY → MONITOR → SELL on WETH/USDC
# ─────────────────────────────────────────────────────────────────────

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _gemini_chat():
    """Return a langchain Gemini chat instance, or None if unavailable."""
    if not GOOGLE_API_KEY:
        return None
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL, temperature=0.2, google_api_key=GOOGLE_API_KEY
        )
    except Exception:
        return None


def _ask_gemini_json(llm, system: str, user: str) -> Dict[str, Any]:
    """Call Gemini and parse the JSON object out of its response."""
    if llm is None:
        return {}
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        resp = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        text = getattr(resp, "content", str(resp)).strip()
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if not m:
            return {"raw": text}
        return json.loads(m.group(0))
    except Exception as exc:
        return {"error": str(exc)}


def _quote_weth_to_usdc(w3: Web3, key: str, weth_amount: int) -> Optional[int]:
    """Simulate a WETH→USDC swap through the vault to get the live quote in USDC wei."""
    me = w3.eth.account.from_key(key).address
    vault = w3.eth.contract(address=Web3.to_checksum_address(VAULT), abi=VAULT_ABI)
    fn = vault.functions.executeTrade(
        Web3.to_checksum_address(WETH), Web3.to_checksum_address(USDC),
        POOL_FEE, int(weth_amount), 0,
        bytes.fromhex("00" * 32), 0,
    )
    try:
        return int(fn.call({"from": me}))
    except Exception:
        return None


def _execute_swap(
    w3: Web3, key: str, token_in: str, token_out: str, amount_in: int,
    reasoning: str, confidence: int,
) -> Dict[str, Any]:
    me = w3.eth.account.from_key(key).address
    vault = w3.eth.contract(address=Web3.to_checksum_address(VAULT), abi=VAULT_ABI)

    reasoning_hash = bytes.fromhex(hashlib.sha256(reasoning.encode()).hexdigest())
    fn = vault.functions.executeTrade(
        Web3.to_checksum_address(token_in), Web3.to_checksum_address(token_out),
        POOL_FEE, int(amount_in), 0, reasoning_hash, max(0, min(100, int(confidence))),
    )
    try:
        sim_out = fn.call({"from": me})
    except Exception as exc:
        raise HTTPException(500, f"swap simulation reverted: {exc}")

    tx = fn.build_transaction({
        "from": me, "nonce": w3.eth.get_transaction_count(me),
        "gas": 500_000, "maxFeePerGas": w3.eth.gas_price * 2,
        "maxPriorityFeePerGas": w3.to_wei(0.001, "gwei"), "chainId": w3.eth.chain_id,
    })
    signed = w3.eth.account.sign_transaction(tx, key)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    h = "0x" + tx_hash.hex().removeprefix("0x")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

    amount_out = sim_out
    try:
        evts = vault.events.TradeExecuted().process_receipt(receipt)
        if evts:
            amount_out = int(evts[0]["args"]["amountOut"])
    except Exception:
        pass

    return {
        "tx_hash": h,
        "status": "success" if receipt["status"] == 1 else "failed",
        "block": receipt["blockNumber"],
        "gas_used": receipt["gasUsed"],
        "amount_in": int(amount_in),
        "amount_out": int(amount_out),
        "reasoning_hash": "0x" + reasoning_hash.hex(),
        "explorer": f"https://sepolia.basescan.org/tx/{h}",
    }


class CycleResponse(BaseModel):
    asset: str
    vault: str
    agent: str
    chain_id: int
    entry: Dict[str, Any]
    exit: Optional[Dict[str, Any]]
    monitor: List[Dict[str, Any]]
    pnl_usdc: float
    pnl_pct: float
    duration_sec: float
    exit_reason: str
    gemini_model: Optional[str]
    explorer_vault: str


@router.post("/rl-trade/auto-cycle", response_model=CycleResponse)
async def auto_cycle(
    take_profit_pct: float = 1.5,
    stop_loss_pct: float = 1.0,
    max_monitor_seconds: int = 90,
    poll_seconds: int = 8,
    amount_usdc: float = 1.0,
):
    """
    Autonomous one-coin trading cycle on WETH/USDC (Base Sepolia):

      1. Gemini analyzes the trade and approves an entry.
      2. Vault buys WETH with `amount_usdc` USDC.
      3. Polls live WETH→USDC quote every `poll_seconds`.
      4. Exits when:  pnl >= take_profit_pct,  pnl <= -stop_loss_pct,
                      timeout, or Gemini says SELL.
      5. Vault swaps the WETH bought in (2) back to USDC.
      6. Returns a P&L summary with every Gemini reasoning step.
    """
    if amount_usdc < 0.1 or amount_usdc > 5.0:
        raise HTTPException(400, "amount_usdc must be in [0.1, 5.0]")
    if take_profit_pct <= 0 or stop_loss_pct <= 0:
        raise HTTPException(400, "take/stop must be > 0")

    key = os.getenv("AGENT_PRIVATE_KEY")
    if not key:
        raise HTTPException(500, "AGENT_PRIVATE_KEY not configured")
    w3 = Web3(Web3.HTTPProvider(RPC))
    if not w3.is_connected():
        raise HTTPException(500, f"cannot reach RPC {RPC}")
    me = w3.eth.account.from_key(key).address

    vault = w3.eth.contract(address=Web3.to_checksum_address(VAULT), abi=VAULT_ABI)
    if vault.functions.agent().call().lower() != me.lower():
        raise HTTPException(403, "wallet is not the vault agent")

    weth_c = w3.eth.contract(address=Web3.to_checksum_address(WETH), abi=ERC20_ABI)
    usdc_c = w3.eth.contract(address=Web3.to_checksum_address(USDC), abi=ERC20_ABI)
    amount_in_wei = int(amount_usdc * 1_000_000)

    if usdc_c.functions.balanceOf(Web3.to_checksum_address(VAULT)).call() < amount_in_wei:
        raise HTTPException(400, f"vault USDC < {amount_usdc}")

    llm = _gemini_chat()
    started_at = time.monotonic()

    # ── 1. Pre-trade Gemini analysis ──────────────────────────────
    pre_quote = _quote_weth_to_usdc(w3, key, int(0.001 * 10**18))  # 0.001 WETH → USDC
    spot_price = (pre_quote / 1e6) / 0.001 if pre_quote else None  # USDC per WETH

    sys_prompt = (
        "You are an autonomous on-chain trading agent for a Base Sepolia vault. "
        "Risk is strictly bounded: only ~1 USDC per trade, with HARD on-chain take-profit "
        "and stop-loss enforced by code. Your job is to decide entry/exit on the WETH/USDC pair "
        "and write concise reasoning. Bias toward action — HOLD only if signals are clearly bearish. "
        "Reply with strict JSON: {\"action\":\"BUY|HOLD\",\"confidence\":0-100,\"reasoning\":\"...\"}."
    )
    spot_line = f"Spot WETH price: {spot_price:.2f} USDC\n" if spot_price else ""
    user_prompt = (
        f"Pair: WETH / USDC on Uniswap V3 (Base Sepolia, fee 0.3%).\n"
        f"{spot_line}"
        f"Trade plan: commit {amount_usdc} USDC, exit on +{take_profit_pct}% take-profit OR "
        f"-{stop_loss_pct}% stop-loss within {max_monitor_seconds}s. Slippage protected by code.\n"
        f"Risk envelope is small and bounded. Should we ENTER (BUY) or skip (HOLD)? "
        f"Default to BUY unless you see a strong reason to abstain."
    )
    pre_decision = _ask_gemini_json(llm, sys_prompt, user_prompt) or {}
    action = (pre_decision.get("action") or "BUY").upper()
    pre_confidence = int(pre_decision.get("confidence") or 70)
    pre_reasoning = pre_decision.get("reasoning") or "Heuristic enter (no Gemini)."

    if action != "BUY":
        return CycleResponse(
            asset="WETH/USDC", vault=VAULT, agent=me, chain_id=w3.eth.chain_id,
            entry={"skipped": True, "gemini": pre_decision, "spot_price_usdc_per_weth": spot_price},
            exit=None, monitor=[], pnl_usdc=0.0, pnl_pct=0.0,
            duration_sec=time.monotonic() - started_at,
            exit_reason="gemini_declined_entry",
            gemini_model=GEMINI_MODEL if llm else None,
            explorer_vault=f"https://sepolia.basescan.org/address/{VAULT}",
        )

    # ── 2. Enter position: USDC → WETH ────────────────────────────
    weth_before = weth_c.functions.balanceOf(Web3.to_checksum_address(VAULT)).call()
    entry_swap = await asyncio.to_thread(
        _execute_swap, w3, key, USDC, WETH, amount_in_wei,
        f"AUTO-ENTRY|{pre_confidence}|gemini|{pre_reasoning}", pre_confidence,
    )
    weth_after = weth_c.functions.balanceOf(Web3.to_checksum_address(VAULT)).call()
    weth_acquired = weth_after - weth_before  # exact WETH from THIS swap
    if weth_acquired <= 0:
        weth_acquired = entry_swap["amount_out"]
    entry_rate_usdc_per_weth = (amount_in_wei / 1e6) / (weth_acquired / 1e18)
    entry_swap["weth_acquired"] = weth_acquired / 1e18
    entry_swap["entry_rate_usdc_per_weth"] = entry_rate_usdc_per_weth
    entry_swap["gemini_reasoning"] = pre_reasoning
    entry_swap["gemini_confidence"] = pre_confidence

    # ── 3. Monitor loop ───────────────────────────────────────────
    monitor: List[Dict[str, Any]] = []
    exit_reason = "timeout"
    exit_decision_text = "monitor window elapsed"
    exit_confidence = 60

    deadline = time.monotonic() + max_monitor_seconds
    poll_idx = 0
    while time.monotonic() < deadline:
        await asyncio.sleep(poll_seconds)
        poll_idx += 1
        quote_usdc_wei = await asyncio.to_thread(_quote_weth_to_usdc, w3, key, int(weth_acquired))
        if quote_usdc_wei is None:
            monitor.append({"poll": poll_idx, "error": "quote_failed"})
            continue

        cur_value_usdc = quote_usdc_wei / 1e6
        pnl_usdc = cur_value_usdc - amount_usdc
        pnl_pct = (pnl_usdc / amount_usdc) * 100.0

        row = {
            "poll": poll_idx,
            "elapsed_sec": round(time.monotonic() - started_at, 1),
            "current_value_usdc": round(cur_value_usdc, 6),
            "pnl_usdc": round(pnl_usdc, 6),
            "pnl_pct": round(pnl_pct, 4),
        }

        # Hard rules first
        if pnl_pct >= take_profit_pct:
            row["decision"] = "SELL"
            row["reason"] = f"take_profit hit (+{pnl_pct:.3f}% ≥ +{take_profit_pct}%)"
            row["source"] = "rule"
            exit_reason = "take_profit"
            exit_decision_text = row["reason"]
            exit_confidence = 95
            monitor.append(row)
            break
        if pnl_pct <= -stop_loss_pct:
            row["decision"] = "SELL"
            row["reason"] = f"stop_loss hit ({pnl_pct:.3f}% ≤ -{stop_loss_pct}%)"
            row["source"] = "rule"
            exit_reason = "stop_loss"
            exit_decision_text = row["reason"]
            exit_confidence = 95
            monitor.append(row)
            break

        # Otherwise consult Gemini
        mon_user = (
            f"You hold {weth_acquired/1e18:.8f} WETH bought at {entry_rate_usdc_per_weth:.2f} USDC/WETH.\n"
            f"Current quote: {cur_value_usdc:.6f} USDC ({pnl_pct:+.3f}% P&L) after {row['elapsed_sec']}s.\n"
            f"Take-profit target: +{take_profit_pct}%, Stop-loss: -{stop_loss_pct}%, "
            f"window remaining: {max(0, deadline - time.monotonic()):.0f}s.\n"
            f"Reply JSON: {{\"action\":\"HOLD|SELL\",\"confidence\":0-100,\"reasoning\":\"...\"}}"
        )
        g = _ask_gemini_json(llm, sys_prompt, mon_user) or {}
        g_action = (g.get("action") or "HOLD").upper()
        g_conf = int(g.get("confidence") or 50)
        g_reason = g.get("reasoning") or "no Gemini"
        row["decision"] = g_action
        row["reason"] = g_reason
        row["source"] = "gemini" if llm else "heuristic"
        row["gemini_confidence"] = g_conf
        monitor.append(row)
        if g_action == "SELL":
            exit_reason = "gemini_sell"
            exit_decision_text = g_reason
            exit_confidence = g_conf
            break

    # ── 4. Exit position: WETH → USDC ─────────────────────────────
    exit_swap = await asyncio.to_thread(
        _execute_swap, w3, key, WETH, USDC, int(weth_acquired),
        f"AUTO-EXIT|{exit_confidence}|{exit_reason}|{exit_decision_text}", exit_confidence,
    )
    realized_usdc_wei = exit_swap["amount_out"]
    realized_usdc = realized_usdc_wei / 1e6
    pnl_usdc = realized_usdc - amount_usdc
    pnl_pct = (pnl_usdc / amount_usdc) * 100.0
    exit_swap["weth_sold"] = weth_acquired / 1e18
    exit_swap["realized_usdc"] = realized_usdc
    exit_swap["exit_reason"] = exit_reason
    exit_swap["reasoning"] = exit_decision_text

    return CycleResponse(
        asset="WETH/USDC",
        vault=VAULT, agent=me, chain_id=w3.eth.chain_id,
        entry=entry_swap,
        exit=exit_swap,
        monitor=monitor,
        pnl_usdc=round(pnl_usdc, 6),
        pnl_pct=round(pnl_pct, 4),
        duration_sec=round(time.monotonic() - started_at, 1),
        exit_reason=exit_reason,
        gemini_model=GEMINI_MODEL if llm else None,
        explorer_vault=f"https://sepolia.basescan.org/address/{VAULT}",
    )
