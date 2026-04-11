"""
RL Trading Agent Module

A self-learning agentic trading system using Google Gemini.
"""

# Use lazy imports to avoid import issues
__all__ = [
    "AgenticTrader",
    "SyntheticMarket",
    "TokenSnapshot",
    "MemoryManager",
    "WalletManager",
]


def __getattr__(name):
    """Lazy import of modules."""
    if name == "WalletManager":
        from .wallet_manager import WalletManager
        return WalletManager
    elif name == "AgenticTrader":
        from .agentic_trader import AgenticTrader
        return AgenticTrader
    elif name == "SyntheticMarket":
        from .synthetic_market import SyntheticMarket
        return SyntheticMarket
    elif name == "TokenSnapshot":
        from .synthetic_market import TokenSnapshot
        return TokenSnapshot
    elif name == "MemoryManager":
        from .memory_manager import MemoryManager
        return MemoryManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

