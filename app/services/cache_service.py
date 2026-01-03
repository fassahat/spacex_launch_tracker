"""Caching service for API responses."""

import json
import time
from typing import Optional, Any
from pathlib import Path


class CacheService:
    """Simple file-based cache implementation."""

    def __init__(self, cache_dir: str = ".cache", ttl_seconds: int = 3600):
        """
        Initialize cache service.

        Args:
            cache_dir: Directory to store cache files
            ttl_seconds: Time-to-live for cached data in seconds
        """
        self.cache_dir = Path(cache_dir)
        self.ttl_seconds = ttl_seconds
        self.cache_dir.mkdir(exist_ok=True)

    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key."""
        safe_key = key.replace("/", "_").replace(":", "_")
        return self.cache_dir / f"{safe_key}.json"

    def _is_expired(self, cache_path: Path) -> bool:
        """Check if cached data has expired."""
        if not cache_path.exists():
            return True

        file_age = time.time() - cache_path.stat().st_mtime
        return file_age > self.ttl_seconds

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve data from cache.

        Args:
            key: Cache key

        Returns:
            Cached data if exists and not expired, None otherwise
        """
        cache_path = self._get_cache_path(key)

        if self._is_expired(cache_path):
            # Clean up expired cache file
            cache_path.unlink(missing_ok=True)
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            # Clean up corrupted cache file
            cache_path.unlink(missing_ok=True)
            return None

    def set(self, key: str, data: Any) -> None:
        """
        Store data in cache.

        Args:
            key: Cache key
            data: Data to cache (must be JSON serializable)
        """
        cache_path = self._get_cache_path(key)

        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except (TypeError, IOError) as e:
            # Log error but don't fail the application
            print(f"Cache write failed for key {key}: {e}")

    def clear(self) -> None:
        """Clear all cached data."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()

    def delete(self, key: str) -> None:
        """
        Delete specific cache entry.

        Args:
            key: Cache key to delete
        """
        cache_path = self._get_cache_path(key)
        if cache_path.exists():
            cache_path.unlink()
