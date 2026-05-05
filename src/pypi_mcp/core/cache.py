"""TTL cache for pypi-mcp."""

import time
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    """Simple in-memory cache with TTL."""

    def __init__(self, default_ttl: float = 300.0) -> None:
        """Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds.
        """
        self._store: dict[str, dict[str, Any]] = {}
        self.default_ttl = default_ttl

    def get(self, key: str) -> T | None:
        """Get cached value if not expired."""
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.time() - entry["timestamp"] > entry["ttl"]:
            del self._store[key]
            return None
        return entry["data"]

    def set(self, key: str, value: T, ttl: float | None = None) -> None:
        """Set cached value with optional custom TTL."""
        self._store[key] = {
            "data": value,
            "timestamp": time.time(),
            "ttl": ttl if ttl is not None else self.default_ttl,
        }

    def delete(self, key: str) -> None:
        """Delete a cached entry."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()

    def keys(self) -> list[str]:
        """Return all valid (non-expired) keys."""
        now = time.time()
        valid_keys = []
        for key, entry in list(self._store.items()):
            if now - entry["timestamp"] <= entry["ttl"]:
                valid_keys.append(key)
            else:
                del self._store[key]
        return valid_keys

    def __len__(self) -> int:
        """Return number of valid entries."""
        return len(self.keys())
