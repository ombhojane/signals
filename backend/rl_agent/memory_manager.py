"""
Memory Manager - Handles reading/writing markdown-based trading memories.

Manages two memory files:
1. trading_journal.md - Chronological trade history
2. trading_rules.md - Learned trading rules
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
import re


@dataclass
class TradeRecord:
    """Record of a single trade."""
    trade_id: int
    timestamp: str
    token_name: str
    token_symbol: str
    action: str  # BUY, SELL
    entry_price: float
    exit_price: Optional[float]
    amount_usd: float
    quantity: float
    pnl: Optional[float]
    pnl_pct: Optional[float]
    reasoning: str
    risk_assessment: str
    outcome: Optional[str]  # SUCCESS, FAILURE, NEUTRAL, PENDING
    lesson: Optional[str]


@dataclass
class TradingRule:
    """A learned trading rule."""
    rule_id: str
    rule_type: str  # ENTRY, EXIT, AVOID
    name: str
    description: str
    conditions: str
    success_count: int = 0
    failure_count: int = 0
    total_pnl: float = 0.0
    source_trades: List[int] = None
    created_at: str = None
    
    def __post_init__(self):
        if self.source_trades is None:
            self.source_trades = []
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.0


class MemoryManager:
    """
    Manages trading memory via markdown files.
    
    Provides clean read/write interface for:
    - Trade journal entries
    - Trading rules (learned over time)
    """
    
    def __init__(self, memory_dir: str = None):
        if memory_dir is None:
            memory_dir = Path(__file__).parent / "memory"
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.journal_path = self.memory_dir / "trading_journal.md"
        self.rules_path = self.memory_dir / "trading_rules.md"
        
        # In-memory state
        self.trades: List[TradeRecord] = []
        self.rules: List[TradingRule] = []
        self.next_trade_id = 1
        self.next_rule_id = 1
        
        # Initialize files if they don't exist
        self._init_files()
    
    def _init_files(self):
        """Initialize empty memory files."""
        if not self.journal_path.exists():
            self._write_journal_header()
        
        if not self.rules_path.exists():
            self._write_rules_header()
    
    def _write_journal_header(self):
        """Write initial journal header."""
        header = """# Trading Journal

> Autonomous Trading Agent - Trade History
> Started: {timestamp}

---

## Trade Log

""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.journal_path.write_text(header)
    
    def _write_rules_header(self):
        """Write initial rules header."""
        header = """# Trading Rules

> Autonomous Trading Agent - Learned Rules
> Last Updated: {timestamp}

---

## Entry Rules (When to BUY)

*No rules learned yet*

---

## Exit Rules (When to SELL)

*No rules learned yet*

---

## Avoid Rules (When to HOLD)

*No rules learned yet*

""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.rules_path.write_text(header)
    
    def reset(self):
        """Reset all memories."""
        self.trades = []
        self.rules = []
        self.next_trade_id = 1
        self.next_rule_id = 1
        self._write_journal_header()
        self._write_rules_header()
    
    # ===== TRADE JOURNAL =====
    
    def add_trade_entry(
        self,
        token_name: str,
        token_symbol: str,
        action: str,
        price: float,
        amount_usd: float,
        quantity: float,
        reasoning: str,
        risk_assessment: str = ""
    ) -> TradeRecord:
        """Record a new trade entry (BUY)."""
        trade = TradeRecord(
            trade_id=self.next_trade_id,
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"),
            token_name=token_name,
            token_symbol=token_symbol,
            action=action,
            entry_price=price,
            exit_price=None,
            amount_usd=amount_usd,
            quantity=quantity,
            pnl=None,
            pnl_pct=None,
            reasoning=reasoning,
            risk_assessment=risk_assessment,
            outcome="PENDING",
            lesson=None
        )
        
        self.trades.append(trade)
        self.next_trade_id += 1
        self._append_trade_to_journal(trade)
        
        return trade
    
    def close_trade(
        self,
        trade_id: int,
        exit_price: float,
        reasoning: str,
        lesson: Optional[str] = None
    ) -> Optional[TradeRecord]:
        """Close an open trade (SELL)."""
        trade = self.get_trade(trade_id)
        if trade is None:
            return None
        
        trade.exit_price = exit_price
        trade.pnl = (exit_price - trade.entry_price) * trade.quantity
        trade.pnl_pct = ((exit_price / trade.entry_price) - 1) * 100
        trade.outcome = "SUCCESS" if trade.pnl > 0 else "FAILURE" if trade.pnl < 0 else "NEUTRAL"
        trade.lesson = lesson
        
        self._append_trade_close_to_journal(trade, reasoning)
        
        return trade
    
    def get_trade(self, trade_id: int) -> Optional[TradeRecord]:
        """Get trade by ID."""
        for trade in self.trades:
            if trade.trade_id == trade_id:
                return trade
        return None
    
    def get_open_trade(self) -> Optional[TradeRecord]:
        """Get the currently open trade (if any)."""
        for trade in reversed(self.trades):
            if trade.action == "BUY" and trade.exit_price is None:
                return trade
        return None
    
    def get_recent_trades(self, n: int = 10) -> List[TradeRecord]:
        """Get N most recent trades."""
        return self.trades[-n:] if self.trades else []
    
    def get_trade_summary(self) -> str:
        """Get summary for LLM context."""
        if not self.trades:
            return "No trades yet."
        
        completed = [t for t in self.trades if t.outcome != "PENDING"]
        pending = [t for t in self.trades if t.outcome == "PENDING"]
        
        if not completed:
            summary = "No completed trades yet."
        else:
            wins = len([t for t in completed if t.outcome == "SUCCESS"])
            losses = len([t for t in completed if t.outcome == "FAILURE"])
            total_pnl = sum(t.pnl for t in completed if t.pnl is not None)
            
            summary = f"""Completed: {len(completed)} trades
Win/Loss: {wins}/{losses}
Total P&L: ${total_pnl:+.2f}"""
        
        if pending:
            summary += f"\nOpen Position: {pending[-1].token_symbol} @ ${pending[-1].entry_price:.6f}"
        
        return summary
    
    def get_last_n_trades_text(self, n: int = 5) -> str:
        """Get last N trades as readable text."""
        recent = self.get_recent_trades(n)
        if not recent:
            return "No previous trades."
        
        lines = []
        for t in recent:
            if t.outcome == "PENDING":
                lines.append(f"- [{t.trade_id}] {t.action} {t.token_symbol} @ ${t.entry_price:.6f} - OPEN")
            else:
                lines.append(f"- [{t.trade_id}] {t.token_symbol}: {t.outcome} ({t.pnl_pct:+.1f}%)")
        
        return "\n".join(lines)
    
    def _append_trade_to_journal(self, trade: TradeRecord):
        """Append trade entry to journal file."""
        entry = f"""
### Trade #{trade.trade_id:03d} - {trade.action}
**{trade.timestamp}** | {trade.token_name} ({trade.token_symbol})

- **Action**: {trade.action} ${trade.amount_usd:.2f}
- **Price**: ${trade.entry_price:.8f}
- **Quantity**: {trade.quantity:.4f}
- **Reasoning**: {trade.reasoning}
- **Risk**: {trade.risk_assessment or 'N/A'}
- **Status**: PENDING

"""
        with open(self.journal_path, "a") as f:
            f.write(entry)
    
    def _append_trade_close_to_journal(self, trade: TradeRecord, reasoning: str):
        """Append trade close to journal file."""
        emoji = "OK" if trade.outcome == "SUCCESS" else "X" if trade.outcome == "FAILURE" else "-"
        
        entry = f"""
### Trade #{trade.trade_id:03d} - CLOSED {emoji}
**{datetime.now().strftime('%Y-%m-%d %H:%M')}** | {trade.token_symbol}

- **Exit Price**: ${trade.exit_price:.8f}
- **P&L**: ${trade.pnl:+.2f} ({trade.pnl_pct:+.1f}%)
- **Outcome**: {trade.outcome}
- **Reasoning**: {reasoning}
- **Lesson**: {trade.lesson or 'N/A'}

---

"""
        with open(self.journal_path, "a") as f:
            f.write(entry)
    
    # ===== TRADING RULES =====
    
    def add_rule(
        self,
        rule_type: str,
        name: str,
        description: str,
        conditions: str,
        source_trade_id: Optional[int] = None
    ) -> TradingRule:
        """Add a new trading rule."""
        rule = TradingRule(
            rule_id=f"RULE_{self.next_rule_id:03d}",
            rule_type=rule_type.upper(),
            name=name,
            description=description,
            conditions=conditions,
            source_trades=[source_trade_id] if source_trade_id else []
        )
        
        self.rules.append(rule)
        self.next_rule_id += 1
        self._rewrite_rules_file()
        
        return rule
    
    def update_rule_stats(self, rule_id: str, success: bool, pnl: float):
        """Update rule performance stats."""
        for rule in self.rules:
            if rule.rule_id == rule_id:
                if success:
                    rule.success_count += 1
                else:
                    rule.failure_count += 1
                rule.total_pnl += pnl
                break
        
        self._rewrite_rules_file()
    
    def get_rules_summary(self) -> str:
        """Get rules summary for LLM context."""
        if not self.rules:
            return "No trading rules learned yet."
        
        lines = []
        for rule in self.rules:
            rate = f"{rule.success_rate*100:.0f}%" if (rule.success_count + rule.failure_count) > 0 else "N/A"
            lines.append(f"- [{rule.rule_type}] {rule.name}: {rule.conditions} (Success: {rate})")
        
        return "\n".join(lines)
    
    def _rewrite_rules_file(self):
        """Rewrite entire rules file."""
        entry_rules = [r for r in self.rules if r.rule_type == "ENTRY"]
        exit_rules = [r for r in self.rules if r.rule_type == "EXIT"]
        avoid_rules = [r for r in self.rules if r.rule_type == "AVOID"]
        
        content = f"""# Trading Rules

> Autonomous Trading Agent - Learned Rules
> Last Updated: {datetime.now().strftime("%Y-%m-%d %H:%M")}
> Total Rules: {len(self.rules)}

---

## Entry Rules (When to BUY)

"""
        if entry_rules:
            for r in entry_rules:
                content += self._format_rule(r)
        else:
            content += "*No entry rules learned yet*\n"
        
        content += "\n---\n\n## Exit Rules (When to SELL)\n\n"
        if exit_rules:
            for r in exit_rules:
                content += self._format_rule(r)
        else:
            content += "*No exit rules learned yet*\n"
        
        content += "\n---\n\n## Avoid Rules (When to HOLD)\n\n"
        if avoid_rules:
            for r in avoid_rules:
                content += self._format_rule(r)
        else:
            content += "*No avoid rules learned yet*\n"
        
        self.rules_path.write_text(content)
    
    def _format_rule(self, rule: TradingRule) -> str:
        """Format a single rule for markdown."""
        total = rule.success_count + rule.failure_count
        rate = f"{rule.success_rate*100:.0f}%" if total > 0 else "N/A"
        
        return f"""### {rule.name}
**ID**: {rule.rule_id} | **Created**: {rule.created_at[:10]}

- **Conditions**: {rule.conditions}
- **Description**: {rule.description}
- **Performance**: {rule.success_count}W / {rule.failure_count}L ({rate})
- **Total P&L**: ${rule.total_pnl:+.2f}

"""
    
    # ===== PERSISTENCE =====
    
    def save_state(self, path: Optional[str] = None):
        """Save full state to JSON for resuming."""
        if path is None:
            path = self.memory_dir / "memory_state.json"
        
        state = {
            "trades": [asdict(t) for t in self.trades],
            "rules": [asdict(r) for r in self.rules],
            "next_trade_id": self.next_trade_id,
            "next_rule_id": self.next_rule_id
        }
        
        Path(path).write_text(json.dumps(state, indent=2))
    
    def load_state(self, path: Optional[str] = None):
        """Load state from JSON."""
        if path is None:
            path = self.memory_dir / "memory_state.json"
        
        if not Path(path).exists():
            return
        
        state = json.loads(Path(path).read_text())
        
        self.trades = [TradeRecord(**t) for t in state.get("trades", [])]
        self.rules = [TradingRule(**r) for r in state.get("rules", [])]
        self.next_trade_id = state.get("next_trade_id", 1)
        self.next_rule_id = state.get("next_rule_id", 1)
