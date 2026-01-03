"""Tests for launch service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from app.services.launch_service import LaunchService
from app.models.launch import Launch, LaunchFilter


@pytest.fixture
def mock_api_client():
    """Create mock API client."""
    return MagicMock()


@pytest.fixture
def launch_service(mock_api_client):
    """Create launch service with mock API."""
    return LaunchService(mock_api_client)


@pytest.fixture
def sample_launches():
    """Create sample launch data."""
    return [
        Launch(
            id="1",
            name="Launch 1",
            date_utc=datetime(2020, 1, 15),
            success=True,
            rocket="rocket1",
            launchpad="pad1"
        ),
        Launch(
            id="2",
            name="Launch 2",
            date_utc=datetime(2020, 6, 20),
            success=False,
            rocket="rocket2",
            launchpad="pad2"
        ),
        Launch(
            id="3",
            name="Launch 3",
            date_utc=datetime(2021, 3, 10),
            success=True,
            rocket="rocket1",
            launchpad="pad1"
        ),
    ]


class TestLaunchService:
    """Test suite for LaunchService."""

    @pytest.mark.asyncio
    async def test_filter_by_date_range(self, launch_service, mock_api_client, sample_launches):
        """Test filtering launches by date range."""
        mock_api_client.get_all_launches = AsyncMock(return_value=sample_launches)

        filters = LaunchFilter(
            date_from=datetime(2020, 6, 1),
            date_to=datetime(2020, 12, 31)
        )

        results = await launch_service.get_filtered_launches(filters)

        assert len(results) == 1
        assert results[0].id == "2"

    @pytest.mark.asyncio
    async def test_filter_by_success(self, launch_service, mock_api_client, sample_launches):
        """Test filtering launches by success status."""
        mock_api_client.get_all_launches = AsyncMock(return_value=sample_launches)

        filters = LaunchFilter(success=True)
        results = await launch_service.get_filtered_launches(filters)

        assert len(results) == 2
        assert all(launch.success is True for launch in results)

    @pytest.mark.asyncio
    async def test_filter_by_rocket_name(self, launch_service, mock_api_client, sample_launches):
        """Test filtering launches by rocket name."""
        mock_api_client.get_all_launches = AsyncMock(return_value=sample_launches)

        rocket_map = {"rocket1": "Falcon 9", "rocket2": "Falcon Heavy"}
        filters = LaunchFilter(rocket_name="Falcon 9")

        results = await launch_service.get_filtered_launches(filters, rocket_id_map=rocket_map)

        assert len(results) == 2
        assert all(launch.rocket == "rocket1" for launch in results)

    @pytest.mark.asyncio
    async def test_pagination(self, launch_service, mock_api_client, sample_launches):
        """Test pagination with limit and offset."""
        mock_api_client.get_all_launches = AsyncMock(return_value=sample_launches)

        filters = LaunchFilter(limit=1, offset=1)
        results = await launch_service.get_filtered_launches(filters)

        assert len(results) == 1
        assert results[0].id == "2"

    @pytest.mark.asyncio
    async def test_get_launch_by_id(self, launch_service, mock_api_client, sample_launches):
        """Test retrieving specific launch by ID."""
        mock_api_client.get_all_launches = AsyncMock(return_value=sample_launches)

        result = await launch_service.get_launch_by_id("2")

        assert result is not None
        assert result.id == "2"
        assert result.name == "Launch 2"

    @pytest.mark.asyncio
    async def test_get_launch_by_id_not_found(self, launch_service, mock_api_client, sample_launches):
        """Test retrieving non-existent launch returns None."""
        mock_api_client.get_all_launches = AsyncMock(return_value=sample_launches)

        result = await launch_service.get_launch_by_id("999")

        assert result is None
