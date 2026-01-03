"""Tests for SpaceX API client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.lib.spacex_api import SpaceXAPIClient, SpaceXAPIError
from app.services.cache_service import CacheService


@pytest.fixture
def mock_cache():
    """Create mock cache service."""
    cache = MagicMock(spec=CacheService)
    cache.get.return_value = None
    return cache


@pytest.fixture
def api_client(mock_cache):
    """Create API client with mock cache."""
    return SpaceXAPIClient(cache_service=mock_cache)


class TestSpaceXAPIClient:
    """Test suite for SpaceXAPIClient."""

    @pytest.mark.asyncio
    async def test_get_all_launches_success(self, api_client, mock_cache):
        """Test successfully fetching all launches."""
        mock_response_data = [
            {
                "id": "1",
                "name": "Test Launch",
                "date_utc": "2020-01-01T00:00:00.000Z",
                "success": True,
                "rocket": "rocket1",
                "launchpad": "pad1"
            }
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            launches = await api_client.get_all_launches()

            assert len(launches) == 1
            assert launches[0].id == "1"
            assert launches[0].name == "Test Launch"

    @pytest.mark.asyncio
    async def test_get_all_rockets_success(self, api_client):
        """Test successfully fetching all rockets."""
        mock_response_data = [
            {
                "id": "rocket1",
                "name": "Falcon 9",
                "active": True,
                "stages": 2
            }
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_response_data
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            rockets = await api_client.get_all_rockets()

            assert len(rockets) == 1
            assert rockets[0].name == "Falcon 9"

    @pytest.mark.asyncio
    async def test_cache_hit(self, api_client, mock_cache):
        """Test cache returns cached data."""
        cached_data = [{"id": "1", "name": "Cached Launch"}]
        mock_cache.get.return_value = cached_data

        with patch("httpx.AsyncClient") as mock_client:
            # Should not make HTTP request
            launches_data = await api_client._fetch_data("launches")

            assert launches_data == cached_data
            mock_client.assert_not_called()

    @pytest.mark.asyncio
    async def test_api_error_handling(self, api_client):
        """Test API error handling."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Server Error", request=MagicMock(), response=mock_response
            )

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            with pytest.raises(SpaceXAPIError):
                await api_client.get_all_launches()

    @pytest.mark.asyncio
    async def test_network_error_handling(self, api_client):
        """Test network error handling."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.RequestError("Network error", request=MagicMock())
            )

            with pytest.raises(SpaceXAPIError):
                await api_client.get_all_launches()

    def test_clear_cache(self, api_client, mock_cache):
        """Test cache clearing."""
        api_client.clear_cache()
        mock_cache.clear.assert_called_once()
