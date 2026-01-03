"""Tests for cache service."""

import pytest
import json
import time
from pathlib import Path

from app.services.cache_service import CacheService


@pytest.fixture
def cache_service(tmp_path):
    """Create cache service with temporary directory."""
    return CacheService(cache_dir=str(tmp_path / ".cache"), ttl_seconds=1)


class TestCacheService:
    """Test suite for CacheService."""

    def test_cache_set_and_get(self, cache_service):
        """Test setting and retrieving cached data."""
        test_data = {"key": "value", "number": 42}
        cache_service.set("test_key", test_data)

        result = cache_service.get("test_key")
        assert result == test_data

    def test_cache_miss(self, cache_service):
        """Test cache miss returns None."""
        result = cache_service.get("nonexistent_key")
        assert result is None

    def test_cache_expiration(self, cache_service):
        """Test cache data expires after TTL."""
        test_data = {"expired": True}
        cache_service.set("expire_key", test_data)

        # Data should be available immediately
        assert cache_service.get("expire_key") == test_data

        # Wait for expiration
        time.sleep(1.5)

        # Data should be expired
        assert cache_service.get("expire_key") is None

    def test_cache_clear(self, cache_service):
        """Test clearing all cached data."""
        cache_service.set("key1", {"data": 1})
        cache_service.set("key2", {"data": 2})

        cache_service.clear()

        assert cache_service.get("key1") is None
        assert cache_service.get("key2") is None

    def test_cache_delete(self, cache_service):
        """Test deleting specific cache entry."""
        cache_service.set("key1", {"data": 1})
        cache_service.set("key2", {"data": 2})

        cache_service.delete("key1")

        assert cache_service.get("key1") is None
        assert cache_service.get("key2") == {"data": 2}

    def test_cache_safe_key_conversion(self, cache_service):
        """Test cache handles special characters in keys."""
        test_data = {"special": "chars"}
        special_key = "api/v4/launches:filter"

        cache_service.set(special_key, test_data)
        result = cache_service.get(special_key)

        assert result == test_data

    def test_expired_cache_file_cleanup(self, cache_service):
        """Test expired cache files are deleted on read."""
        test_data = {"cleanup": True}
        cache_service.set("cleanup_key", test_data)

        # Get cache file path
        cache_path = cache_service._get_cache_path("cleanup_key")
        assert cache_path.exists()

        # Wait for expiration
        time.sleep(1.5)

        # Get should return None and delete the file
        result = cache_service.get("cleanup_key")
        assert result is None
        assert not cache_path.exists()

    def test_corrupted_cache_file_cleanup(self, cache_service):
        """Test corrupted cache files are deleted on read."""
        # Create a corrupted cache file
        cache_path = cache_service._get_cache_path("corrupted_key")
        cache_path.parent.mkdir(exist_ok=True)

        with open(cache_path, "w") as f:
            f.write("invalid json {{{")

        assert cache_path.exists()

        # Get should return None and delete corrupted file
        result = cache_service.get("corrupted_key")
        assert result is None
        assert not cache_path.exists()

    def test_cleanup_missing_file_no_error(self, cache_service):
        """Test cleanup doesn't error if file already deleted."""
        # Try to get non-existent key (should not raise error)
        result = cache_service.get("never_existed")
        assert result is None
