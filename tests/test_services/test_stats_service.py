"""Tests for statistics service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.stats_service import StatsService
from app.models.launch import Launch
from app.models.rocket import Rocket
from app.models.launchpad import Launchpad


@pytest.fixture
def mock_api_client():
    """Create mock API service."""
    return MagicMock()


@pytest.fixture
def stats_service(mock_api_client):
    """Create statistics service with mock API."""
    return StatsService(mock_api_client)


@pytest.fixture
def sample_data():
    """Create sample launches, rockets, and launchpads."""
    launches = [
        Launch(id="1", name="L1", date_utc=datetime(2020, 1, 1), success=True, rocket="r1", launchpad="p1"),
        Launch(id="2", name="L2", date_utc=datetime(2020, 2, 1), success=True, rocket="r1", launchpad="p1"),
        Launch(id="3", name="L3", date_utc=datetime(2020, 3, 1), success=False, rocket="r1", launchpad="p2"),
        Launch(id="4", name="L4", date_utc=datetime(2021, 1, 1), success=True, rocket="r2", launchpad="p1"),
    ]

    rockets = [
        Rocket(id="r1", name="Falcon 9", active=True),
        Rocket(id="r2", name="Falcon Heavy", active=True),
    ]

    launchpads = [
        Launchpad(id="p1", name="LC-39A"),
        Launchpad(id="p2", name="SLC-40"),
    ]

    return launches, rockets, launchpads


class TestStatsService:
    """Test suite for StatsService."""

    @pytest.mark.asyncio
    async def test_success_rate_by_rocket(self, stats_service, mock_api_client, sample_data):
        """Test calculating success rates by rocket."""
        launches, rockets, launchpads = sample_data

        mock_api_client.get_all_launches = AsyncMock(return_value=launches)
        mock_api_client.get_all_rockets = AsyncMock(return_value=rockets)

        result = await stats_service.get_success_rate_by_rocket()

        assert "Falcon 9" in result
        assert result["Falcon 9"]["total_launches"] == 3
        assert result["Falcon 9"]["successful_launches"] == 2
        assert result["Falcon 9"]["failed_launches"] == 1
        assert result["Falcon 9"]["success_rate_percentage"] == 66.67

        assert "Falcon Heavy" in result
        assert result["Falcon Heavy"]["total_launches"] == 1
        assert result["Falcon Heavy"]["successful_launches"] == 1
        assert result["Falcon Heavy"]["success_rate_percentage"] == 100.0

    @pytest.mark.asyncio
    async def test_launches_by_launchpad(self, stats_service, mock_api_client, sample_data):
        """Test counting launches by launchpad."""
        launches, rockets, launchpads = sample_data

        mock_api_client.get_all_launches = AsyncMock(return_value=launches)
        mock_api_client.get_all_launchpads = AsyncMock(return_value=launchpads)

        result = await stats_service.get_launches_by_launchpad()

        assert "LC-39A" in result
        assert result["LC-39A"]["total"] == 3
        assert result["LC-39A"]["successful"] == 3

        assert "SLC-40" in result
        assert result["SLC-40"]["total"] == 1
        assert result["SLC-40"]["successful"] == 0

    @pytest.mark.asyncio
    async def test_launch_frequency(self, stats_service, mock_api_client, sample_data):
        """Test calculating launch frequency by month and year."""
        launches, rockets, launchpads = sample_data

        mock_api_client.get_all_launches = AsyncMock(return_value=launches)

        result = await stats_service.get_launch_frequency()

        assert "by_year" in result
        assert result["by_year"]["2020"] == 3
        assert result["by_year"]["2021"] == 1

        assert "by_month" in result
        assert result["by_month"]["2020-01"] == 1
        assert result["by_month"]["2020-02"] == 1
        assert result["by_month"]["2020-03"] == 1

    @pytest.mark.asyncio
    async def test_overall_statistics(self, stats_service, mock_api_client, sample_data):
        """Test calculating overall statistics."""
        launches, rockets, launchpads = sample_data

        # Add upcoming launch
        launches.append(
            Launch(id="5", name="L5", upcoming=True, rocket="r1", launchpad="p1")
        )

        mock_api_client.get_all_launches = AsyncMock(return_value=launches)

        result = await stats_service.get_overall_statistics()

        assert result["total_launches"] == 5
        assert result["successful_launches"] == 3
        assert result["failed_launches"] == 1
        assert result["upcoming_launches"] == 1
        assert result["overall_success_rate_percentage"] == 75.0

    @pytest.mark.asyncio
    async def test_zero_division_handling(self, stats_service, mock_api_client):
        """Test handling of zero launches."""
        mock_api_client.get_all_launches = AsyncMock(return_value=[])
        mock_api_client.get_all_rockets = AsyncMock(return_value=[])

        result = await stats_service.get_success_rate_by_rocket()

        assert result == {}
