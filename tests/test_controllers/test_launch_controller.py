"""Tests for launch controller."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app
from app.models.launch import Launch
from app.lib.spacex_api import SpaceXAPIError
from app.controllers import launch_controller


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def sample_launches():
    """Create sample launch data."""
    return [
        Launch(
            id="1",
            name="Launch 1",
            date_utc=datetime(2020, 1, 1),
            success=True,
            rocket="r1",
            launchpad="p1"
        ),
        Launch(
            id="2",
            name="Launch 2",
            date_utc=datetime(2020, 6, 1),
            success=False,
            rocket="r2",
            launchpad="p2"
        ),
    ]


class TestLaunchController:
    """Test suite for launch controller endpoints."""

    def test_get_launches_success(self, client, sample_launches):
        """Test successfully retrieving launches."""
        mock_service = MagicMock()
        mock_service.get_filtered_launches = AsyncMock(return_value=sample_launches)

        mock_api_client = MagicMock()

        # Override dependencies
        app.dependency_overrides[launch_controller.get_launch_service] = lambda: mock_service
        app.dependency_overrides[launch_controller.get_api_client] = lambda: mock_api_client

        try:
            response = client.get("/launches/")

            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
        finally:
            app.dependency_overrides.clear()

    def test_get_launches_with_filters(self, client):
        """Test retrieving launches with query filters."""
        mock_service = MagicMock()
        mock_service.get_filtered_launches = AsyncMock(return_value=[])

        mock_api_client = MagicMock()
        mock_api_client.get_all_rockets = AsyncMock(return_value=[])

        # Override dependencies
        app.dependency_overrides[launch_controller.get_launch_service] = lambda: mock_service
        app.dependency_overrides[launch_controller.get_api_client] = lambda: mock_api_client

        try:
            response = client.get(
                "/launches/",
                params={"success": True, "rocket_name": "Falcon 9", "limit": 10}
            )

            assert response.status_code == 200
        finally:
            app.dependency_overrides.clear()

    def test_get_launch_by_id_success(self, client, sample_launches):
        """Test successfully retrieving a specific launch."""
        mock_service = MagicMock()
        mock_service.get_launch_by_id = AsyncMock(return_value=sample_launches[0])

        # Override dependencies
        app.dependency_overrides[launch_controller.get_launch_service] = lambda: mock_service

        try:
            response = client.get("/launches/1")

            assert response.status_code == 200
            data = response.json()
            assert data["id"] == "1"
            assert data["name"] == "Launch 1"
        finally:
            app.dependency_overrides.clear()

    def test_get_launch_by_id_not_found(self, client):
        """Test retrieving non-existent launch returns 404."""
        mock_service = MagicMock()
        mock_service.get_launch_by_id = AsyncMock(return_value=None)

        # Override dependencies
        app.dependency_overrides[launch_controller.get_launch_service] = lambda: mock_service

        try:
            response = client.get("/launches/999")

            assert response.status_code == 404
        finally:
            app.dependency_overrides.clear()

    def test_get_launches_api_error(self, client):
        """Test API error handling returns 503."""
        mock_service = MagicMock()
        mock_service.get_filtered_launches = AsyncMock(
            side_effect=SpaceXAPIError("API unavailable")
        )

        mock_api_client = MagicMock()

        # Override dependencies
        app.dependency_overrides[launch_controller.get_launch_service] = lambda: mock_service
        app.dependency_overrides[launch_controller.get_api_client] = lambda: mock_api_client

        try:
            response = client.get("/launches/")

            assert response.status_code == 503
        finally:
            app.dependency_overrides.clear()
