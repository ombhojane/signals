"""
Agentic Trader - LLM-powered autonomous trading agent (adaptive).

Loop: OBSERVE → THINK (LLM, with rules + journal) → ACT (sized by confidence,
volatility-aware stop) → REFLECT (rule add / weight update).

Improvements over the original:
- Configurable model via env (GEMINI_MODEL), with safe default and fallback.
- Confidence-scaled position sizing (Kelly-lite).
- Volatility-aware adaptive stop loss + take profit.
- ε-greedy exploration to avoid getting stuck on HOLD.
- Heuristic policy fallback when the LLM is unavailable, so the loop never stalls.
- Rule weight updates after each closed trade (success/failure counters).
"""

import os
import json
import math
import random
from typing import Optional, Dict, Any
from dataclasses import dataclass

from dotenv import load_dotenv

from .synthetic_market import TokenSnapshot
from .memory_manager import MemoryManager
from .wallet_manager import WalletManager

load_dotenv()

# Model: prefer env override; fall back to project default; secondary fallback to a known-stable Gemini.
PRIMARY_MODEL = os.getenv("GEMINI_MODEL", "gemma-3-27b-it")
FALLBACK_MODEL = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-2.5-flash")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")


@dataclass
class TradeDecision:
    action: str  # BUY, SELL, HOLD
    confidence: int  # 0-100
    reasoning: str
    risk_assessment: str
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None
    source: str = "llm"  # llm | heuristic | explore


@dataclass
class Reflection:
    trade_assessment: str  # SUCCESS, FAILURE, NEUTRAL
    key_learnings: list
    rule_updates: list
    confidence_adjustment: float


class AgenticTrader:
    """LLM-powered autonomous trading agent. Adaptive sizing + exploration + reflection."""

    def __init__(
        self,
        initial_balance: float = 100.0,
        max_position_pct: float = 0.25,
        stop_loss_pct: float = 0.10,
        memory_dir: str = None,
        verbose: bool = True,
        explore_eps: float = 0.05,
        use_llm: bool = True,
    ):
        self.verbose = verbose
        self.max_position_pct = max_position_pct
        self.stop_loss_pct = stop_loss_pct
        self.explore_eps = explore_eps
        self.use_llm = use_llm and bool(GOOGLE_API_KEY)

        self.llm = None
        self._llm_model_name = None
        if self.use_llm:
            self.llm, self._llm_model_name = self._init_llm()

        # Components
        self.wallet = WalletManager(initial_balance, max_position_pct, stop_loss_pct)
        self.memory = MemoryManager(memory_dir)

        # State
        self.current_token: Optional[TokenSnapshot] = None
        self.current_trade_id: Optional[int] = None
        self.entry_volatility: float = 0.0
        self.entry_take_profit: Optional[float] = None
        self.total_decisions = 0
        self.action_counts = {"BUY": 0, "SELL": 0, "HOLD": 0}

    # ---------- LLM init with fallback ----------
    def _init_llm(self):
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(
                model=PRIMARY_MODEL, temperature=0.3, google_api_key=GOOGLE_API_KEY
            )
            return llm, PRIMARY_MODEL
        except Exception as exc:
            if self.verbose:
                print(f"  [llm] primary {PRIMARY_MODEL} init failed: {exc}; trying {FALLBACK_MODEL}")
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model=FALLBACK_MODEL, temperature=0.3, google_api_key=GOOGLE_API_KEY
                )
                return llm, FALLBACK_MODEL
            except Exception as exc2:
                if self.verbose:
                    print(f"  [llm] fallback init failed too: {exc2}; running heuristic-only")
                return None, None

    def reset(self, keep_memory: bool = False):
        self.wallet = WalletManager(
            self.wallet.initial_balance, self.max_position_pct, self.stop_loss_pct
        )
        self.current_trade_id = None
        self.entry_volatility = 0.0
        self.entry_take_profit = None
        self.total_decisions = 0
        self.action_counts = {"BUY": 0, "SELL": 0, "HOLD": 0}
        if not keep_memory:
            self.memory.reset()

    # ---------- THINK ----------
    async def think(self, market: TokenSnapshot) -> TradeDecision:
        self.current_token = market

        # ε-greedy exploration: occasionally force BUY/SELL to break HOLD bias
        if random.random() < self.explore_eps:
            forced = random.choice(["BUY", "SELL", "HOLD"])
            return TradeDecision(
                action=forced,
                confidence=20,
                reasoning="Exploration step (ε-greedy) — sampling uncommon action for learning.",
                risk_assessment="Random exploration carries elevated risk.",
                source="explore",
            )

        # If no LLM available, fall through to heuristic
        if not self.llm:
            return self._heuristic_decision(market)

        position_info = self._get_position_context()
        trade_history = self.memory.get_last_n_trades_text(5)
        rules = self.memory.get_rules_summary()

        prompt = self._build_prompt(market, position_info, trade_history, rules)

        try:
            from langchain_core.messages import HumanMessage
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            return self._parse_decision(response.content, source="llm")
        except Exception as e:
            if self.verbose:
                print(f"  [llm] error → heuristic fallback: {str(e)[:100]}")
            return self._heuristic_decision(market)

    def _build_prompt(self, market, position_info, trade_history, rules) -> str:
        return f"""You are an autonomous on-chain memecoin trading agent managing a ${self.wallet.initial_balance} portfolio.

Goal: maximize risk-adjusted return. Survive bad tokens, ride good ones.

## Current Market Data
{market.to_market_summary()}

## Your Current Position
{position_info}

## Recent Trading History
{trade_history}

## Your Learned Rules (apply only if conditions match)
{rules}

## Risk Parameters
- Max position size: {self.max_position_pct * 100:.0f}% of equity
- Base stop loss: {self.stop_loss_pct * 100:.0f}% (will be widened by volatility)

## Decision Heuristics (memecoin meta, 2025)
1. AVOID if rug_score > 75, or top_10_holder_pct > 80, or liquidity_locked is False with rug_score > 50.
2. STRONG BUY signal: smart_money=buying + volume_ratio > 2 + rsi 35-65 + sentiment > 60 + influencer_mentions ≥ 1.
3. EXIT signal: rsi > 80 + bollinger_position > 0.85, OR price_change_1h < -8% with volume spike (dump), OR smart_money flipping to selling while you're long.
4. HOLD if signal is mixed; don't trade on noise (volume_ratio < 0.6).
5. After +30% unrealized gain, tighten stop to entry to lock in.

## Output (JSON only — no prose, no markdown)
{{
    "action": "BUY" | "SELL" | "HOLD",
    "confidence": 0-100,
    "reasoning": "1-2 sentence why",
    "risk_assessment": "what could go wrong",
    "price_target": <number or null>,
    "stop_loss": <number or null>
}}"""

    # ---------- ACT ----------
    def act(self, decision: TradeDecision) -> Dict[str, Any]:
        self.total_decisions += 1
        self.action_counts[decision.action] = self.action_counts.get(decision.action, 0) + 1

        result = {"action": decision.action, "executed": False, "details": {}}

        # BUY
        if decision.action == "BUY" and self.current_token:
            if self.wallet.position > 0:
                result["details"]["reason"] = "Already holding position"
                return result

            # Confidence-scaled sizing: 0.3..1.0 of max_position_pct
            conf = max(0, min(100, decision.confidence)) / 100.0
            size_scale = 0.3 + 0.7 * conf
            target_value = self.wallet.balance * self.max_position_pct * size_scale
            target_amount = target_value / max(self.current_token.price, 1e-12)

            trade = self.wallet.buy(price=self.current_token.price, amount=target_amount, reason=decision.reasoning)
            if trade:
                # Volatility-aware stop loss + take profit memo
                vol = max(self.current_token.volatility or 0.0, 0.005)
                self.entry_volatility = vol
                self.entry_take_profit = self.current_token.price * (1.0 + max(0.15, 4.0 * vol))

                result["executed"] = True
                result["details"] = {
                    "price": trade.price, "amount": trade.amount,
                    "cost": trade.amount * trade.price,
                    "size_scale": round(size_scale, 2),
                    "take_profit": self.entry_take_profit,
                    "vol": round(vol, 4),
                }

                record = self.memory.add_trade_entry(
                    token_name=self.current_token.name,
                    token_symbol=self.current_token.symbol,
                    action="BUY",
                    price=trade.price,
                    amount_usd=trade.amount * trade.price,
                    quantity=trade.amount,
                    reasoning=f"[{decision.source}] {decision.reasoning}",
                    risk_assessment=decision.risk_assessment,
                )
                self.current_trade_id = record.trade_id
                if self.verbose:
                    print(f"  ▶ BUY {trade.amount:.4f} @ ${trade.price:.8f} (conf={decision.confidence}, scale={size_scale:.2f}, TP=${self.entry_take_profit:.8f})")

        # SELL
        elif decision.action == "SELL" and self.current_token:
            if self.wallet.position <= 0:
                result["details"]["reason"] = "No position to sell"
                return result

            trade = self.wallet.sell(price=self.current_token.price, reason=decision.reasoning)
            if trade:
                result["executed"] = True
                result["details"] = {"price": trade.price, "amount": trade.amount, "pnl": trade.pnl}
                if self.current_trade_id:
                    self.memory.close_trade(
                        trade_id=self.current_trade_id,
                        exit_price=trade.price,
                        reasoning=f"[{decision.source}] {decision.reasoning}",
                    )
                    self.current_trade_id = None
                self.entry_take_profit = None
                self.entry_volatility = 0.0
                if self.verbose:
                    print(f"  ▶ SELL @ ${trade.price:.8f}  P&L: ${trade.pnl:+.2f}")

        else:
            result["details"]["reason"] = "Hold — no action"

        # Volatility-adaptive stop loss
        if self.wallet.position > 0 and self.current_token:
            vol = max(self.entry_volatility, 0.005)
            adaptive_stop = max(self.stop_loss_pct, min(0.35, 3.0 * vol))
            entry = self.wallet.avg_entry_price
            current = self.current_token.price
            loss_pct = (entry - current) / entry if entry > 0 else 0
            tp_hit = self.entry_take_profit is not None and current >= self.entry_take_profit

            if loss_pct >= adaptive_stop or tp_hit:
                reason = "Take profit" if tp_hit else f"Adaptive stop ({adaptive_stop*100:.1f}%)"
                trade = self.wallet.sell(price=current, reason=reason)
                if trade:
                    result["risk_exit"] = reason
                    if self.current_trade_id:
                        self.memory.close_trade(
                            trade_id=self.current_trade_id,
                            exit_price=current,
                            reasoning=reason,
                            lesson=("Position locked profit." if tp_hit else "Stopped out — re-evaluate entry rule."),
                        )
                        self.current_trade_id = None
                    self.entry_take_profit = None
                    self.entry_volatility = 0.0
                    if self.verbose:
                        tag = "TP" if tp_hit else "SL"
                        print(f"  ▶ {tag} @ ${current:.8f}  P&L: ${trade.pnl:+.2f}")

        return result

    # ---------- REFLECT ----------
    async def reflect(self, trade_result: Dict, outcome_pnl: float) -> Optional[Reflection]:
        last_closed = None
        for t in reversed(self.memory.trades):
            if t.outcome and t.outcome != "PENDING":
                last_closed = t
                break
        if not last_closed:
            return None

        # Update rule weights based on outcome (for any rule referenced in entry reasoning)
        for rule in self.memory.rules:
            if rule.name.lower() in (last_closed.reasoning or "").lower():
                self.memory.update_rule_stats(
                    rule.rule_id,
                    success=(last_closed.outcome == "SUCCESS"),
                    pnl=last_closed.pnl or 0.0,
                )

        # If no LLM, do a lightweight rule-add heuristic and exit
        if not self.llm:
            return self._heuristic_reflection(last_closed)

        prompt = f"""You just completed a trade. Analyze and learn (briefly).

## Trade
- Token: {last_closed.token_name} ({last_closed.token_symbol})
- Entry: ${last_closed.entry_price:.8f}
- Exit: ${last_closed.exit_price:.8f}
- P&L: ${last_closed.pnl:+.2f} ({last_closed.pnl_pct:+.1f}%)
- Outcome: {last_closed.outcome}
- Original Reasoning: {last_closed.reasoning}

## Current Rules
{self.memory.get_rules_summary()}

Add a NEW rule ONLY if this trade reveals a pattern the current rules don't capture.
Do NOT add a rule for every trade.

## Output (JSON only)
{{
    "trade_assessment": "SUCCESS" | "FAILURE" | "NEUTRAL",
    "key_learnings": ["..."],
    "rule_updates": [
        {{"action": "ADD", "type": "ENTRY|EXIT|AVOID", "name": "Rule Name",
          "conditions": "concrete condition (use indicator names)", "description": "why"}}
    ],
    "confidence_adjustment": 0.0
}}"""

        try:
            from langchain_core.messages import HumanMessage
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            reflection = self._parse_reflection(response.content)
            for upd in reflection.rule_updates:
                if upd.get("action") == "ADD":
                    self.memory.add_rule(
                        rule_type=upd.get("type", "ENTRY"),
                        name=upd.get("name", "Unnamed Rule"),
                        description=upd.get("description", ""),
                        conditions=upd.get("conditions", ""),
                        source_trade_id=last_closed.trade_id,
                    )
                    if self.verbose:
                        print(f"  ✚ rule learned: [{upd.get('type')}] {upd.get('name')}")
            return reflection
        except Exception as e:
            if self.verbose:
                print(f"  [reflect] LLM error → heuristic: {str(e)[:80]}")
            return self._heuristic_reflection(last_closed)

    # ---------- Heuristic fallback policy ----------
    def _heuristic_decision(self, m: TokenSnapshot) -> TradeDecision:
        score = 0
        notes = []
        # Hard avoid gates
        if m.rug_score >= 75:
            return TradeDecision("HOLD", 10, f"Rug score too high ({m.rug_score})",
                                 "Rug pattern; do not enter.", source="heuristic")
        if m.top_10_holder_pct >= 80:
            score -= 30; notes.append(f"top10 {m.top_10_holder_pct:.0f}%")
        # Only penalize unlocked LP if we actually have a confirmed signal of risk
        if not m.liquidity_locked and m.rug_score >= 50:
            score -= 15; notes.append("unlocked LP + rug risk")

        # Smart money
        if m.smart_money_flow == "buying":
            score += 25; notes.append("smart $ buying")
        elif m.smart_money_flow == "selling":
            score -= 20; notes.append("smart $ selling")

        # RSI
        if m.rsi >= 80:
            score -= 25; notes.append(f"RSI {m.rsi:.0f} hot")
        elif 40 <= m.rsi <= 65:
            score += 8
        elif m.rsi <= 28:
            score += 12; notes.append(f"oversold {m.rsi:.0f}")

        # Bollinger
        if m.bollinger_position > 0.9:
            score -= 12; notes.append("upper band")
        elif m.bollinger_position < -0.85:
            score += 12; notes.append("lower band")

        # Momentum (the big one we were missing)
        if m.price_change_1h >= 15:
            score += 20; notes.append(f"+{m.price_change_1h:.0f}% 1h pump")
        elif m.price_change_1h >= 5:
            score += 12; notes.append(f"+{m.price_change_1h:.0f}% 1h")
        elif m.price_change_1h <= -10 and m.volume_ratio > 1.5:
            score -= 25; notes.append(f"{m.price_change_1h:.0f}% dump on vol")
        elif m.price_change_1h <= -5:
            score -= 10
        if m.price_change_24h >= 30:
            score += 8
        if m.price_change_24h <= -30:
            score -= 10

        # Volume confirmation
        if m.volume_ratio >= 2.5:
            score += 15; notes.append(f"vol×{m.volume_ratio:.1f}")
        elif m.volume_ratio >= 1.5:
            score += 8
        elif m.volume_ratio < 0.5:
            score -= 8

        # Social
        if m.sentiment_score > 65:
            score += 8
        elif m.sentiment_score < 35:
            score -= 8
        if m.trending:
            score += 4
        if m.influencer_mentions >= 2:
            score += 6

        # Position-aware exits
        if self.wallet.position > 0:
            if m.rsi > 80 and m.bollinger_position > 0.85:
                return TradeDecision("SELL", 75, f"Blow-off top: {'; '.join(notes)}",
                                     "Reversal risk", source="heuristic")
            if m.smart_money_flow == "selling":
                return TradeDecision("SELL", 70, f"Smart money rotating out ({'; '.join(notes)})",
                                     "Distribution risk", source="heuristic")
            if m.price_change_1h <= -10 and m.volume_ratio > 1.5:
                return TradeDecision("SELL", 75, f"Capitulation dump: {'; '.join(notes)}",
                                     "Cut and reassess", source="heuristic")

        # Entry threshold (lowered from 30 → 22, so the agent actually trades)
        if score >= 22 and self.wallet.position == 0:
            return TradeDecision("BUY", min(95, 45 + score),
                                 f"Composite + ({score}): {'; '.join(notes)}",
                                 "Memecoin volatility / dump risk", source="heuristic")
        if score <= -25 and self.wallet.position > 0:
            return TradeDecision("SELL", min(95, 45 - score),
                                 f"Composite − ({score}): {'; '.join(notes)}",
                                 "Cutting losses", source="heuristic")
        return TradeDecision("HOLD", max(20, 50 - abs(score)),
                             f"No edge ({score}): {'; '.join(notes) or 'neutral'}",
                             "Wait for better setup", source="heuristic")

    def _heuristic_reflection(self, trade) -> Reflection:
        return Reflection(
            trade_assessment=trade.outcome or "NEUTRAL",
            key_learnings=[f"PnL {trade.pnl_pct:+.1f}% on {trade.token_symbol}"],
            rule_updates=[],
            confidence_adjustment=0.0,
        )

    # ---------- Helpers ----------
    def _get_position_context(self) -> str:
        if self.wallet.position <= 0:
            return f"- Balance: ${self.wallet.balance:.2f}\n- Position: None\n- Realized P&L: ${self.wallet.realized_pnl:.2f}"
        current_price = self.current_token.price if self.current_token else self.wallet.avg_entry_price
        unrealized = (current_price - self.wallet.avg_entry_price) * self.wallet.position
        unrealized_pct = ((current_price / self.wallet.avg_entry_price) - 1) * 100
        return (f"- Balance: ${self.wallet.balance:.2f}\n"
                f"- Position: {self.wallet.position:.4f} @ ${self.wallet.avg_entry_price:.8f}\n"
                f"- Current: ${current_price:.8f}\n"
                f"- Unrealized: ${unrealized:+.2f} ({unrealized_pct:+.1f}%)\n"
                f"- Realized: ${self.wallet.realized_pnl:.2f}")

    def _parse_decision(self, response: str, source: str = "llm") -> TradeDecision:
        text = response.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()
        try:
            data = json.loads(text)
            return TradeDecision(
                action=str(data.get("action", "HOLD")).upper(),
                confidence=int(data.get("confidence", 50)),
                reasoning=str(data.get("reasoning", "No reasoning provided"))[:300],
                risk_assessment=str(data.get("risk_assessment", ""))[:300],
                price_target=data.get("price_target"),
                stop_loss=data.get("stop_loss"),
                source=source,
            )
        except Exception:
            # Try to find JSON in the response
            try:
                start = text.find("{")
                end = text.rfind("}")
                if start >= 0 and end > start:
                    data = json.loads(text[start:end + 1])
                    return TradeDecision(
                        action=str(data.get("action", "HOLD")).upper(),
                        confidence=int(data.get("confidence", 50)),
                        reasoning=str(data.get("reasoning", "No reasoning"))[:300],
                        risk_assessment=str(data.get("risk_assessment", ""))[:300],
                        source=source,
                    )
            except Exception:
                pass
        return TradeDecision("HOLD", 0, "Parse error in LLM output", "Parsing error", source=source)

    def _parse_reflection(self, response: str) -> Reflection:
        text = response.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()
        try:
            data = json.loads(text)
        except Exception:
            try:
                s, e = text.find("{"), text.rfind("}")
                data = json.loads(text[s:e + 1]) if s >= 0 else {}
            except Exception:
                data = {}
        return Reflection(
            trade_assessment=data.get("trade_assessment", "NEUTRAL"),
            key_learnings=data.get("key_learnings", []),
            rule_updates=data.get("rule_updates", []),
            confidence_adjustment=float(data.get("confidence_adjustment", 0.0) or 0.0),
        )

    def get_summary(self) -> Dict[str, Any]:
        return {
            "balance": self.wallet.balance,
            "position": self.wallet.position,
            "realized_pnl": self.wallet.realized_pnl,
            "total_decisions": self.total_decisions,
            "action_distribution": self.action_counts,
            "trades": len(self.memory.trades),
            "rules": len(self.memory.rules),
            "llm_model": self._llm_model_name,
        }
