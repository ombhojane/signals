"""
Wallet Manager - Handles virtual wallet for simulation.

Tracks balance, positions, and P&L calculations.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
import json


@dataclass
class Trade:
    """Represents a single trade."""
    timestamp: datetime
    action: str  # "buy" or "sell"
    price: float
    amount: float
    value: float
    balance_after: float
    pnl: float = 0.0
    reason: str = ""


@dataclass
class WalletManager:
    """
    Virtual wallet for trading simulation.
    
    Attributes:
        initial_balance: Starting balance (default $100)
        max_position_pct: Maximum position size as percentage (default 25%)
        stop_loss_pct: Stop-loss percentage (default 10%)
    """
    initial_balance: float = 100.0
    max_position_pct: float = 0.25
    stop_loss_pct: float = 0.10
    
    # Internal state
    balance: float = field(init=False)
    position: float = field(init=False)  # Number of tokens held
    avg_entry_price: float = field(init=False)
    trades: List[Trade] = field(default_factory=list, init=False)
    realized_pnl: float = field(init=False)
    
    def __post_init__(self):
        self.reset()
    
    def reset(self):
        """Reset wallet to initial state."""
        self.balance = self.initial_balance
        self.position = 0.0
        self.avg_entry_price = 0.0
        self.trades = []
        self.realized_pnl = 0.0
    
    @property
    def max_trade_value(self) -> float:
        """Maximum value allowed for a single trade."""
        return self.balance * self.max_position_pct
    
    @property
    def total_equity(self) -> float:
        """Total equity including unrealized P&L."""
        return self.balance + self.position_value
    
    @property
    def position_value(self) -> float:
        """Current value of position (needs current price)."""
        # This is updated externally when calculating portfolio value
        return 0.0
    
    def get_position_value(self, current_price: float) -> float:
        """Get current value of position."""
        return self.position * current_price
    
    def get_unrealized_pnl(self, current_price: float) -> float:
        """Calculate unrealized P&L."""
        if self.position <= 0:
            return 0.0
        return (current_price - self.avg_entry_price) * self.position
    
    def get_total_equity(self, current_price: float) -> float:
        """Get total equity at current price."""
        return self.balance + self.get_position_value(current_price)
    
    def should_stop_loss(self, current_price: float) -> bool:
        """Check if stop-loss should be triggered."""
        if self.position <= 0 or self.avg_entry_price <= 0:
            return False
        
        loss_pct = (self.avg_entry_price - current_price) / self.avg_entry_price
        return loss_pct >= self.stop_loss_pct
    
    def buy(self, price: float, amount: Optional[float] = None, reason: str = "") -> Optional[Trade]:
        """
        Execute a buy order.
        
        Args:
            price: Current token price
            amount: Amount of tokens to buy (default: max allowed)
            reason: Reason for the trade
            
        Returns:
            Trade object if successful, None otherwise
        """
        max_amount = self.max_trade_value / price
        
        if amount is None:
            amount = max_amount
        else:
            amount = min(amount, max_amount)
        
        value = amount * price
        
        if value > self.balance or value <= 0:
            return None
        
        # Update position with weighted average entry price
        total_value = (self.position * self.avg_entry_price) + value
        self.position += amount
        self.avg_entry_price = total_value / self.position if self.position > 0 else 0
        
        self.balance -= value
        
        trade = Trade(
            timestamp=datetime.now(),
            action="buy",
            price=price,
            amount=amount,
            value=value,
            balance_after=self.balance,
            reason=reason
        )
        self.trades.append(trade)
        return trade
    
    def sell(self, price: float, amount: Optional[float] = None, reason: str = "") -> Optional[Trade]:
        """
        Execute a sell order.
        
        Args:
            price: Current token price
            amount: Amount of tokens to sell (default: all)
            reason: Reason for the trade
            
        Returns:
            Trade object if successful, None otherwise
        """
        if self.position <= 0:
            return None
        
        if amount is None:
            amount = self.position
        else:
            amount = min(amount, self.position)
        
        value = amount * price
        pnl = (price - self.avg_entry_price) * amount
        
        self.position -= amount
        self.balance += value
        self.realized_pnl += pnl
        
        # Reset avg entry if position closed
        if self.position <= 0:
            self.position = 0.0
            self.avg_entry_price = 0.0
        
        trade = Trade(
            timestamp=datetime.now(),
            action="sell",
            price=price,
            amount=amount,
            value=value,
            balance_after=self.balance,
            pnl=pnl,
            reason=reason
        )
        self.trades.append(trade)
        return trade
    
    def get_stats(self, current_price: float) -> dict:
        """Get wallet statistics."""
        total_trades = len(self.trades)
        winning_trades = sum(1 for t in self.trades if t.pnl > 0)
        losing_trades = sum(1 for t in self.trades if t.pnl < 0)
        
        return {
            "balance": self.balance,
            "position": self.position,
            "position_value": self.get_position_value(current_price),
            "total_equity": self.get_total_equity(current_price),
            "unrealized_pnl": self.get_unrealized_pnl(current_price),
            "realized_pnl": self.realized_pnl,
            "total_pnl": self.realized_pnl + self.get_unrealized_pnl(current_price),
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": winning_trades / total_trades if total_trades > 0 else 0.0,
            "return_pct": ((self.get_total_equity(current_price) / self.initial_balance) - 1) * 100
        }
    
    def to_dict(self) -> dict:
        """Convert wallet state to dictionary."""
        return {
            "balance": self.balance,
            "position": self.position,
            "avg_entry_price": self.avg_entry_price,
            "realized_pnl": self.realized_pnl,
            "trades": [
                {
                    "timestamp": t.timestamp.isoformat(),
                    "action": t.action,
                    "price": t.price,
                    "amount": t.amount,
                    "value": t.value,
                    "pnl": t.pnl,
                    "reason": t.reason
                }
                for t in self.trades
            ]
        }
    
    def save(self, filepath: str):
        """Save wallet state to JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
