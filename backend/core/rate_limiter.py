"""
Async Rate Limiter - Token bucket pattern for free API tier management.
"""

import asyncio
import time
from typing import Dict


class AsyncRateLimiter:
    """
    Simple async token-bucket rate limiter.

    Usage:
        limiter = AsyncRateLimiter(max_requests=30, window_seconds=60)
        await limiter.acquire()  # blocks if rate limit exceeded
    """

    def __init__(self, max_requests: int, window_seconds: float):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: list[float] = []
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Wait until a request slot is available."""
        async with self._lock:
            now = time.time()
            cutoff = now - self.window_seconds

            # Remove expired timestamps
            self._timestamps = [t for t in self._timestamps if t > cutoff]

            if len(self._timestamps) >= self.max_requests:
                # Wait until the oldest request expires
                wait_time = self._timestamps[0] - cutoff
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                self._timestamps = [t for t in self._timestamps if t > time.time() - self.window_seconds]

            self._timestamps.append(time.time())


# Pre-configured rate limiters for free API tiers
_limiters: Dict[str, AsyncRateLimiter] = {}


def get_rate_limiter(name: str, max_requests: int = 30, window_seconds: float = 60.0) -> AsyncRateLimiter:
    """Get or create a named rate limiter."""
    if name not in _limiters:
        _limiters[name] = AsyncRateLimiter(max_requests, window_seconds)
    return _limiters[name]
