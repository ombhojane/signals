"""
Agentic Trader - LLM-powered autonomous trading agent.

Uses LLM for reasoning about trades based on:
- Market data from synthetic market
- Trading memory (journal + rules)
- Risk parameters

Implements THINK → ACT → OBSERVE → REFLECT loop.
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from .synthetic_market import TokenSnapshot
from .memory_manager import MemoryManager
from .wallet_manager import WalletManager

# Load environment variables
load_dotenv()

# Get API key
google_api_key = os.getenv("GOOGLE_API_KEY")


@dataclass
class TradeDecision:
    """Agent's trading decision."""
    action: str  # BUY, SELL, HOLD
    confidence: int  # 0-100
    reasoning: str
    risk_assessment: str
    price_target: Optional[float] = None
    stop_loss: Optional[float] = None


@dataclass
class Reflection:
    """Post-trade reflection."""
    trade_assessment: str  # SUCCESS, FAILURE, NEUTRAL
    key_learnings: list
    rule_updates: list
    confidence_adjustment: float


class AgenticTrader:
    """
    LLM-powered autonomous trading agent.
    
    Makes trading decisions through reasoning, not rule matching.
    Learns from experience via reflection.
    """
    
    def __init__(
        self,
        initial_balance: float = 100.0,
        max_position_pct: float = 0.25,
        stop_loss_pct: float = 0.10,
        memory_dir: str = None,
        verbose: bool = True
    ):
        self.verbose = verbose
        self.max_position_pct = max_position_pct
        self.stop_loss_pct = stop_loss_pct
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.3,
            google_api_key=google_api_key
        )
        
        # Initialize components
        self.wallet = WalletManager(initial_balance, max_position_pct, stop_loss_pct)
        self.memory = MemoryManager(memory_dir)
        
        # State
        self.current_token: Optional[TokenSnapshot] = None
        self.current_trade_id: Optional[int] = None
        self.total_decisions = 0
        self.action_counts = {"BUY": 0, "SELL": 0, "HOLD": 0}
    
    def reset(self, keep_memory: bool = False):
        """Reset agent state."""
        self.wallet = WalletManager(
            self.wallet.initial_balance,
            self.max_position_pct,
            self.stop_loss_pct
        )
        self.current_trade_id = None
        self.total_decisions = 0
        self.action_counts = {"BUY": 0, "SELL": 0, "HOLD": 0}
        
        if not keep_memory:
            self.memory.reset()
    
    async def think(self, market: TokenSnapshot) -> TradeDecision:
        """
        THINK: Analyze market and decide action using LLM.
        """
        self.current_token = market
        
        # Build context
        position_info = self._get_position_context()
        trade_history = self.memory.get_last_n_trades_text(5)
        rules = self.memory.get_rules_summary()
        
        prompt = f"""You are an autonomous crypto trading agent managing a ${self.wallet.initial_balance} portfolio.

## Current Market Data
{market.to_market_summary()}

## Your Current Position
{position_info}

## Recent Trading History
{trade_history}

## Your Learned Rules
{rules}

## Risk Parameters
- Maximum position size: {self.max_position_pct * 100}% of balance
- Stop loss: {self.stop_loss_pct * 100}%

## Task
Analyze the market and decide your next action.

Consider:
1. Technical indicators (RSI, MACD, Bollinger)
2. On-chain safety (rug score, liquidity lock)
3. Social sentiment
4. Your position and P&L
5. Your learned rules

## Output Format
Return ONLY a valid JSON object (no markdown):
{{
    "action": "BUY" or "SELL" or "HOLD",
    "confidence": 0-100,
    "reasoning": "Brief explanation of why this action",
    "risk_assessment": "What could go wrong",
    "price_target": null or target price if buying,
    "stop_loss": null or stop loss price if buying
}}"""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            decision = self._parse_decision(response.content)
        except Exception as e:
            if self.verbose:
                print(f"  LLM error: {e}")
            decision = TradeDecision(
                action="HOLD",
                confidence=0,
                reasoning=f"LLM error: {str(e)[:50]}",
                risk_assessment="Error occurred"
            )
        
        return decision
    
    def act(self, decision: TradeDecision) -> Dict[str, Any]:
        """
        ACT: Execute the trading decision.
        
        Returns trade result.
        """
        self.total_decisions += 1
        self.action_counts[decision.action] = self.action_counts.get(decision.action, 0) + 1
        
        result = {
            "action": decision.action,
            "executed": False,
            "details": {}
        }
        
        if decision.action == "BUY" and self.current_token:
            # Check if already holding
            if self.wallet.position > 0:
                result["details"]["reason"] = "Already holding position"
                return result
            
            # Execute buy (use default max position from wallet)
            trade = self.wallet.buy(
                price=self.current_token.price,
                reason=decision.reasoning
            )
            
            if trade:
                result["executed"] = True
                result["details"] = {
                    "price": trade.price,
                    "amount": trade.amount,
                    "cost": trade.amount * trade.price
                }
                
                # Record in memory
                record = self.memory.add_trade_entry(
                    token_name=self.current_token.name,
                    token_symbol=self.current_token.symbol,
                    action="BUY",
                    price=trade.price,
                    amount_usd=trade.amount * trade.price,
                    quantity=trade.amount,
                    reasoning=decision.reasoning,
                    risk_assessment=decision.risk_assessment
                )
                self.current_trade_id = record.trade_id
                
                if self.verbose:
                    print(f"  → BUY {trade.amount:.4f} @ ${trade.price:.8f}")
        
        elif decision.action == "SELL" and self.current_token:
            # Check if holding
            if self.wallet.position <= 0:
                result["details"]["reason"] = "No position to sell"
                return result
            
            # Execute sell (sell all by default)
            trade = self.wallet.sell(
                price=self.current_token.price,
                reason=decision.reasoning
            )
            
            if trade:
                result["executed"] = True
                result["details"] = {
                    "price": trade.price,
                    "amount": trade.amount,
                    "pnl": trade.pnl
                }
                
                # Close trade in memory
                if self.current_trade_id:
                    self.memory.close_trade(
                        trade_id=self.current_trade_id,
                        exit_price=trade.price,
                        reasoning=decision.reasoning
                    )
                    self.current_trade_id = None
                
                if self.verbose:
                    print(f"  → SELL @ ${trade.price:.8f} (P&L: ${trade.pnl:+.2f})")
        
        else:  # HOLD
            result["details"]["reason"] = "Waiting for better opportunity"
        
        # Check stop loss
        if self.wallet.position > 0 and self.current_token:
            if self.wallet.should_stop_loss(self.current_token.price):
                # Execute stop loss sell
                trade = self.wallet.sell(
                    price=self.current_token.price,
                    reason="Stop loss triggered"
                )
                if trade:
                    result["stop_loss_triggered"] = True
                    if self.current_trade_id:
                        self.memory.close_trade(
                            trade_id=self.current_trade_id,
                            exit_price=self.current_token.price,
                            reasoning="Stop loss triggered",
                            lesson="Need better entry points or wider stops"
                        )
                        self.current_trade_id = None
                    if self.verbose:
                        print(f"  STOP LOSS triggered!")
        
        return result
    
    async def reflect(self, trade_result: Dict, outcome_pnl: float) -> Optional[Reflection]:
        """
        REFLECT: Learn from completed trade.
        
        Only called after a trade closes.
        """
        if not trade_result.get("executed"):
            return None
        
        trade = self.memory.get_trade(self.current_trade_id - 1 if self.current_trade_id else len(self.memory.trades))
        if not trade or trade.outcome == "PENDING":
            return None
        
        prompt = f"""You just completed a trade. Analyze and learn from it.

## Trade Details
- Token: {trade.token_name} ({trade.token_symbol})
- Entry: ${trade.entry_price:.8f}
- Exit: ${trade.exit_price:.8f}
- P&L: ${trade.pnl:+.2f} ({trade.pnl_pct:+.1f}%)
- Outcome: {trade.outcome}
- Original Reasoning: {trade.reasoning}

## Current Rules
{self.memory.get_rules_summary()}

## Questions
1. What signals did you read correctly?
2. What did you miss?
3. Should you add or modify any rules?

## Output Format
Return ONLY a valid JSON object:
{{
    "trade_assessment": "SUCCESS" or "FAILURE" or "NEUTRAL",
    "key_learnings": ["learning1", "learning2"],
    "rule_updates": [
        {{"action": "ADD", "type": "ENTRY/EXIT/AVOID", "name": "Rule Name", "conditions": "condition description", "description": "why this rule"}}
    ],
    "confidence_adjustment": 0.0
}}

Only add rules for significant patterns. Don't add a rule for every trade."""

        try:
            response = await self.llm.ainvoke([HumanMessage(content=prompt)])
            reflection = self._parse_reflection(response.content)
            
            # Apply rule updates
            for update in reflection.rule_updates:
                if update.get("action") == "ADD":
                    self.memory.add_rule(
                        rule_type=update.get("type", "ENTRY"),
                        name=update.get("name", "Unnamed Rule"),
                        description=update.get("description", ""),
                        conditions=update.get("conditions", ""),
                        source_trade_id=trade.trade_id
                    )
                    if self.verbose:
                        print(f"  New rule: {update.get('name')}")
            
            return reflection
        
        except Exception as e:
            if self.verbose:
                print(f"  Reflection error: {e}")
            return None
    
    def _get_position_context(self) -> str:
        """Get current position as text."""
        if self.wallet.position <= 0:
            return f"""- Balance: ${self.wallet.balance:.2f}
- Position: None
- Realized P&L: ${self.wallet.realized_pnl:.2f}"""
        
        current_price = self.current_token.price if self.current_token else self.wallet.avg_entry_price
        unrealized = (current_price - self.wallet.avg_entry_price) * self.wallet.position
        unrealized_pct = ((current_price / self.wallet.avg_entry_price) - 1) * 100
        
        return f"""- Balance: ${self.wallet.balance:.2f}
- Position: {self.wallet.position:.4f} tokens @ ${self.wallet.avg_entry_price:.8f}
- Current Price: ${current_price:.8f}
- Unrealized P&L: ${unrealized:+.2f} ({unrealized_pct:+.1f}%)
- Realized P&L: ${self.wallet.realized_pnl:.2f}"""
    
    def _parse_decision(self, response: str) -> TradeDecision:
        """Parse LLM response into TradeDecision."""
        # Clean up response
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        response = response.strip()
        
        try:
            data = json.loads(response)
            return TradeDecision(
                action=data.get("action", "HOLD").upper(),
                confidence=int(data.get("confidence", 50)),
                reasoning=data.get("reasoning", "No reasoning provided"),
                risk_assessment=data.get("risk_assessment", ""),
                price_target=data.get("price_target"),
                stop_loss=data.get("stop_loss")
            )
        except Exception:
            # Default to HOLD if parsing fails
            return TradeDecision(
                action="HOLD",
                confidence=0,
                reasoning="Failed to parse LLM response",
                risk_assessment="Parsing error"
            )
    
    def _parse_reflection(self, response: str) -> Reflection:
        """Parse LLM response into Reflection."""
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        response = response.strip()
        
        try:
            data = json.loads(response)
            return Reflection(
                trade_assessment=data.get("trade_assessment", "NEUTRAL"),
                key_learnings=data.get("key_learnings", []),
                rule_updates=data.get("rule_updates", []),
                confidence_adjustment=data.get("confidence_adjustment", 0.0)
            )
        except Exception:
            return Reflection(
                trade_assessment="NEUTRAL",
                key_learnings=[],
                rule_updates=[],
                confidence_adjustment=0.0
            )
    
    def get_summary(self) -> Dict[str, Any]:
        """Get agent summary."""
        return {
            "balance": self.wallet.balance,
            "position": self.wallet.position,
            "realized_pnl": self.wallet.realized_pnl,
            "total_decisions": self.total_decisions,
            "action_distribution": self.action_counts,
            "trades": len(self.memory.trades),
            "rules": len(self.memory.rules)
        }
