"""
Technical Indicators - Shared calculations used by both synthetic and real market adapters.
Extracted from synthetic_market.py for reuse.
"""

import numpy as np
from typing import List, Tuple


def calculate_rsi(prices: List[float], window: int = 14) -> float:
    """Calculate Relative Strength Index from price history."""
    if len(prices) < window + 1:
        return 50.0

    arr = np.array(prices[-window - 1:])
    deltas = np.diff(arr)

    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)

    avg_gain = np.mean(gains) if len(gains) > 0 else 0
    avg_loss = np.mean(losses) if len(losses) > 0 else 0.0001

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return float(np.clip(rsi, 0, 100))


def calculate_macd(prices: List[float]) -> Tuple[float, float]:
    """Calculate MACD and signal line from price history."""
    if len(prices) < 26:
        return 0.0, 0.0

    import pandas as pd
    series = pd.Series(prices)
    ema12 = series.ewm(span=12).mean().iloc[-1]
    ema26 = series.ewm(span=26).mean().iloc[-1]
    macd = ema12 - ema26

    # Signal line (simplified 9-period EMA of MACD)
    signal = macd * 0.8

    return float(macd), float(signal)


def calculate_bollinger(prices: List[float], current_price: float, window: int = 20) -> Tuple[float, float, float]:
    """
    Calculate Bollinger Bands position.

    Returns:
        (upper_band, lower_band, position) where position is -1 to 1
    """
    if len(prices) < window:
        return current_price * 1.1, current_price * 0.9, 0.0

    arr = np.array(prices[-window:])
    sma = np.mean(arr)
    std = np.std(arr)

    upper = sma + 2 * std
    lower = sma - 2 * std

    if std > 0:
        position = (current_price - sma) / (2 * std)
    else:
        position = 0

    return float(upper), float(lower), float(np.clip(position, -1, 1))


def calculate_volatility(prices: List[float], window: int = 20) -> float:
    """Calculate price volatility (standard deviation of returns)."""
    if len(prices) < 2:
        return 0.0

    arr = np.array(prices[-window:])
    returns = np.diff(arr) / arr[:-1]
    return float(np.std(returns)) if len(returns) > 0 else 0.0


def calculate_volume_ratio(volumes: List[float], window: int = 20) -> float:
    """Calculate current volume vs average volume ratio."""
    if not volumes:
        return 1.0

    arr = np.array(volumes[-window:])
    avg = np.mean(arr)
    if avg > 0:
        return float(volumes[-1] / avg)
    return 1.0
