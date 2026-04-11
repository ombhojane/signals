"""
In-Memory TTL Cache - Simple caching layer for API responses.
"""

import time
from typing import Any, Optional, Dict, Tuple


class TTLCache:
    """
    Simple in-memory cache with per-key TTL expiration.

    Usage:
        cache = TTLCache(default_ttl=300)  # 5 minutes
        cache.set("key", data)
        result = cache.get("key")  # Returns None if expired
    """

    def __init__(self, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self._store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        """Get a cached value, or None if expired/missing."""
        if key not in self._store:
            return None

        expires_at, value = self._store[key]
        if time.time() > expires_at:
            del self._store[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set a cached value with optional custom TTL."""
        ttl = ttl if ttl is not None else self.default_ttl
        self._store[key] = (time.time() + ttl, value)

    def invalidate(self, key: str):
        """Remove a specific key."""
        self._store.pop(key, None)

    def clear(self):
        """Clear all cached entries."""
        self._store.clear()

    def cleanup(self):
        """Remove all expired entries."""
        now = time.time()
        expired = [k for k, (exp, _) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]


# Global cache instances for different services
token_data_cache = TTLCache(default_ttl=60)      # 1 minute for price data
safety_cache = TTLCache(default_ttl=300)          # 5 minutes for safety data
twitter_cache = TTLCache(default_ttl=300)         # 5 minutes for tweets
