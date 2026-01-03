"""Tests for statistics controller."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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
            "name": "Falcon 9 Launch 1",
            "date_utc": "2020-01-15T00:00:00.000Z",
            "success": True,
            "rocket": "r1",
            "launchpad": "p1"
        },
        {
            "id": "2",
            "name": "Falcon 9 Launch 2",
            "date_utc": "2020-02-10T00:00:00.000Z",
            "success": True,
            "rocket": "r1",
            "launchpad": "p1"
        },
        {
            "id": "3",
            "name": "Falcon Heavy Launch",
            "date_utc": "2020-03-05T00:00:00.000Z",
            "success": False,
            "rocket": "r2",
            "launchpad": "p2"
        },
        {
            "id": "4",
            "name": "Falcon 9 Launch 3",
            "date_utc": "2021-01-20T00:00:00.000Z",
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


class TestStatsController:
    """Test suite for statistics controller endpoints."""

    def test_get_success_rate_success(self, client, mock_launches_data, mock_rockets_data):
        """Test successfully retrieving success rates."""
        # Disable cache to ensure we use fresh data
        with patch("app.config.settings.cache_enabled", False):
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

                response = client.get("/stats/success-rate")

                assert response.status_code == 200
                data = response.json()
                assert "Falcon 9" in data
                assert "Falcon Heavy" in data
                # Falcon 9: 3 launches, 3 successful = 100%
                assert data["Falcon 9"]["total_launches"] == 3
                assert data["Falcon 9"]["successful_launches"] == 3
                assert data["Falcon 9"]["success_rate_percentage"] == 100.0
                # Falcon Heavy: 1 launch, 0 successful = 0%
                assert data["Falcon Heavy"]["total_launches"] == 1
                assert data["Falcon Heavy"]["successful_launches"] == 0
                assert data["Falcon Heavy"]["success_rate_percentage"] == 0.0

    def test_get_launchpads_success(self, client, mock_launches_data, mock_launchpads_data):
        """Test successfully retrieving launchpad statistics."""
        # Disable cache to ensure we use fresh data
        with patch("app.config.settings.cache_enabled", False):
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()

                def get_mock_data(url):
                    if "launchpads" in url:
                        mock_response.json.return_value = mock_launchpads_data
                    else:
                        mock_response.json.return_value = mock_launches_data
                    return mock_response

                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    side_effect=lambda url: get_mock_data(url)
                )
                mock_response.raise_for_status = MagicMock()

                response = client.get("/stats/launchpads")

                assert response.status_code == 200
                data = response.json()
                assert "LC-39A" in data
                assert "SLC-40" in data
                # LC-39A (p1): 3 launches, 3 successful
                assert data["LC-39A"]["total"] == 3
                assert data["LC-39A"]["successful"] == 3
                # SLC-40 (p2): 1 launch, 0 successful
                assert data["SLC-40"]["total"] == 1
                assert data["SLC-40"]["successful"] == 0

    def test_get_frequency_success(self, client, mock_launches_data):
        """Test successfully retrieving launch frequency."""
        # Disable cache to ensure we use fresh data
        with patch("app.config.settings.cache_enabled", False):
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_launches_data
                mock_response.raise_for_status = MagicMock()

                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                response = client.get("/stats/frequency")

                assert response.status_code == 200
                data = response.json()
                assert "by_year" in data
                assert "by_month" in data
                # 2020: 3 launches, 2021: 1 launch
                assert data["by_year"]["2020"] == 3
                assert data["by_year"]["2021"] == 1
                # Monthly breakdown
                assert data["by_month"]["2020-01"] == 1
                assert data["by_month"]["2020-02"] == 1
                assert data["by_month"]["2020-03"] == 1
                assert data["by_month"]["2021-01"] == 1

    def test_get_overall_statistics_success(self, client, mock_launches_data):
        """Test successfully retrieving overall statistics."""
        # Disable cache to ensure we use fresh data
        with patch("app.config.settings.cache_enabled", False):
            with patch("httpx.AsyncClient") as mock_client:
                mock_response = MagicMock()
                mock_response.json.return_value = mock_launches_data
                mock_response.raise_for_status = MagicMock()

                mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                    return_value=mock_response
                )

                response = client.get("/stats/overall")

                assert response.status_code == 200
                data = response.json()
                # Total 4 launches: 3 successful, 1 failed, 0 upcoming
                assert data["total_launches"] == 4
                assert data["successful_launches"] == 3
                assert data["failed_launches"] == 1
                assert data["upcoming_launches"] == 0
                # Success rate: 3/4 = 75%
                assert data["overall_success_rate_percentage"] == 75.0

    def test_stats_api_error(self, client):
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

                response = client.get("/stats/success-rate")

                assert response.status_code == 503
                assert "SpaceX API error" in response.json()["detail"]
