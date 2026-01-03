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


class TestStatsController:
    """Test suite for statistics controller endpoints."""

    def test_get_success_rate_success(self, client):
        """Test successfully retrieving success rates."""
        mock_data = {
            "Falcon 9": {
                "total_launches": 100,
                "successful_launches": 98,
                "failed_launches": 2,
                "success_rate_percentage": 98.0
            }
        }

        with patch("app.controllers.stats_controller.StatsService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_success_rate_by_rocket = AsyncMock(return_value=mock_data)
            mock_service.return_value = mock_instance

            with patch("app.controllers.stats_controller.SpaceXAPIClient"):
                response = client.get("/stats/success-rate")

                assert response.status_code == 200
                data = response.json()
                assert "Falcon 9" in data
                assert data["Falcon 9"]["success_rate_percentage"] == 98.0

    def test_get_launchpads_success(self, client):
        """Test successfully retrieving launchpad statistics."""
        mock_data = {
            "LC-39A": {"total": 50, "successful": 48}
        }

        with patch("app.controllers.stats_controller.StatsService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_launches_by_launchpad = AsyncMock(return_value=mock_data)
            mock_service.return_value = mock_instance

            with patch("app.controllers.stats_controller.SpaceXAPIClient"):
                response = client.get("/stats/launchpads")

                assert response.status_code == 200
                data = response.json()
                assert "LC-39A" in data

    def test_get_frequency_success(self, client):
        """Test successfully retrieving launch frequency."""
        mock_data = {
            "by_year": {"2020": 26, "2021": 31},
            "by_month": {"2020-01": 3, "2020-02": 2}
        }

        with patch("app.controllers.stats_controller.StatsService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_launch_frequency = AsyncMock(return_value=mock_data)
            mock_service.return_value = mock_instance

            with patch("app.controllers.stats_controller.SpaceXAPIClient"):
                response = client.get("/stats/frequency")

                assert response.status_code == 200
                data = response.json()
                assert "by_year" in data
                assert "by_month" in data

    def test_get_overall_statistics_success(self, client):
        """Test successfully retrieving overall statistics."""
        mock_data = {
            "total_launches": 150,
            "successful_launches": 145,
            "failed_launches": 5,
            "upcoming_launches": 10,
            "overall_success_rate_percentage": 96.67
        }

        with patch("app.controllers.stats_controller.StatsService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_overall_statistics = AsyncMock(return_value=mock_data)
            mock_service.return_value = mock_instance

            with patch("app.controllers.stats_controller.SpaceXAPIClient"):
                response = client.get("/stats/overall")

                assert response.status_code == 200
                data = response.json()
                assert data["total_launches"] == 150
                assert data["overall_success_rate_percentage"] == 96.67

    def test_stats_api_error(self, client):
        """Test API error handling returns 503."""
        with patch("app.controllers.stats_controller.StatsService") as mock_service:
            mock_instance = MagicMock()
            mock_instance.get_success_rate_by_rocket = AsyncMock(
                side_effect=SpaceXAPIError("API unavailable")
            )
            mock_service.return_value = mock_instance

            with patch("app.controllers.stats_controller.SpaceXAPIClient"):
                response = client.get("/stats/success-rate")

                assert response.status_code == 503
