"""Tests for launch controller."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.lib.spacex_api import SpaceXAPIError


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_launches_data():
    """Mock SpaceX API launch data."""
    return [
        {
            "id": "1",
            "name": "Falcon 9 Launch",
            "date_utc": "2020-01-01T00:00:00.000Z",
            "success": True,
            "rocket": "r1",
            "launchpad": "p1"
        },
        {
            "id": "2",
            "name": "Falcon Heavy Launch",
            "date_utc": "2020-06-01T00:00:00.000Z",
            "success": False,
            "rocket": "r2",
            "launchpad": "p2"
        },
        {
            "id": "3",
            "name": "Starship Launch",
            "date_utc": "2021-01-01T00:00:00.000Z",
            "success": True,
            "rocket": "r1",
            "launchpad": "p1"
        },
    ]


@pytest.fixture
def mock_rockets_data():
    """Mock SpaceX API rocket data."""
    return [
        {"id": "r1", "name": "Falcon 9", "active": True, "stages": 2},
        {"id": "r2", "name": "Falcon Heavy", "active": True, "stages": 2},
    ]


@pytest.fixture
def mock_launchpads_data():
    """Mock SpaceX API launchpad data."""
    return [
        {"id": "p1", "name": "LC-39A", "locality": "Cape Canaveral", "region": "Florida"},
        {"id": "p2", "name": "SLC-40", "locality": "Cape Canaveral", "region": "Florida"},
    ]


class TestLaunchController:
    """Test suite for launch controller endpoints."""

    def test_get_launches_success(self, client, mock_launches_data):
        """Test successfully retrieving launches."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_launches_data
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            response = client.get("/launches/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 3
            assert data[0]["id"] == "1"
            assert data[0]["name"] == "Falcon 9 Launch"
            assert data[1]["id"] == "2"
            assert data[1]["name"] == "Falcon Heavy Launch"
            assert data[2]["id"] == "3"
            assert data[2]["name"] == "Starship Launch"

    def test_get_launches_with_success_filter(self, client, mock_launches_data, mock_rockets_data):
        """Test retrieving launches with success filter."""
        with patch("httpx.AsyncClient") as mock_client:
            # Mock the API to return all launches
            mock_response = MagicMock()
            mock_response.json.return_value = mock_launches_data
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            response = client.get("/launches/", params={"success": True})

            assert response.status_code == 200
            data = response.json()
            # Service should filter to only successful launches (id 1 and 3)
            assert len(data) == 2
            assert all(launch["success"] is True for launch in data)
            assert data[0]["id"] == "1"
            assert data[1]["id"] == "3"

    def test_get_launches_with_rocket_name_filter(self, client, mock_launches_data, mock_rockets_data):
        """Test retrieving launches with rocket name filter."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()

            # Return different data based on endpoint
            def get_mock_data(url):
                if "rockets" in url:
                    mock_response.json.return_value = mock_rockets_data
                else:
                    mock_response.json.return_value = mock_launches_data
                return mock_response

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=lambda url: get_mock_data(url)
            )
            mock_response.raise_for_status = MagicMock()

            response = client.get("/launches/", params={"rocket_name": "Falcon 9"})

            assert response.status_code == 200
            data = response.json()
            # Service should filter to Falcon 9 launches (rocket r1: id 1 and 3)
            assert len(data) == 2
            assert data[0]["id"] == "1"
            assert data[1]["id"] == "3"

    def test_get_launches_with_multiple_filters(self, client, mock_launches_data, mock_rockets_data):
        """Test retrieving launches with multiple filters."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()

            def get_mock_data(url):
                if "rockets" in url:
                    mock_response.json.return_value = mock_rockets_data
                else:
                    mock_response.json.return_value = mock_launches_data
                return mock_response

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=lambda url: get_mock_data(url)
            )
            mock_response.raise_for_status = MagicMock()

            response = client.get(
                "/launches/",
                params={
                    "success": True,
                    "rocket_name": "Falcon 9",
                    "limit": 10,
                    "offset": 0
                }
            )

            assert response.status_code == 200
            data = response.json()
            # Filter: successful AND Falcon 9 (rocket r1) = id 1 and 3
            assert len(data) == 2
            assert all(launch["success"] is True for launch in data)
            assert data[0]["id"] == "1"
            assert data[1]["id"] == "3"

    def test_get_launches_with_limit_and_offset(self, client, mock_launches_data):
        """Test pagination with limit and offset."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_launches_data
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            response = client.get("/launches/", params={"limit": 1, "offset": 1})

            assert response.status_code == 200
            data = response.json()
            # Should return only the second launch (offset 1, limit 1)
            assert len(data) == 1
            assert data[0]["id"] == "2"

    def test_get_launch_by_id_success(self, client, mock_launches_data):
        """Test successfully retrieving a specific launch."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_launches_data
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            response = client.get("/launches/1")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "1"
            assert data["name"] == "Falcon 9 Launch"
            assert data["success"] is True

    def test_get_launch_by_id_not_found(self, client, mock_launches_data):
        """Test retrieving non-existent launch returns 404."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_launches_data
            mock_response.raise_for_status = MagicMock()

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            response = client.get("/launches/999")

            assert response.status_code == 404
            assert "not found" in response.json()["detail"].lower()

    def test_get_launches_api_error(self, client):
        """Test API error handling returns 503."""
        # Disable cache to ensure we hit the API error
        with patch("app.config.settings.cache_enabled", False):
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.raise_for_status.side_effect = Exception("Server Error")

                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                response = client.get("/launches/")

                assert response.status_code == 503
                assert "SpaceX API error" in response.json()["detail"]

    def test_get_launch_by_id_api_error(self, client):
        """Test API error when fetching single launch."""
        # Disable cache to ensure we hit the API error
        with patch("app.config.settings.cache_enabled", False):
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.status_code = 500
                mock_response.raise_for_status.side_effect = Exception("Server Error")

                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                response = client.get("/launches/1")

                assert response.status_code == 503
                assert "SpaceX API error" in response.json()["detail"]
