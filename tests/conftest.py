"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def disable_cache_for_tests(request):
    """
    Automatically disable cache for controller/integration tests.

    This prevents test data from polluting the production cache.
    Skips disabling for tests in test_cache_service.py and test_spacex_api.py
    since those specifically test caching behavior.
    """
    # Skip disabling cache for tests that explicitly test cache functionality
    test_file = request.node.fspath.basename
    if test_file in ["test_cache_service.py", "test_spacex_api.py"]:
        yield
        return

    # Disable cache for all other tests
    with patch("app.config.settings.cache_enabled", False):
        yield
