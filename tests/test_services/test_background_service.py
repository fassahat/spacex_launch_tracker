"""Tests for background service."""
import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from app.services.background_service import (
    check_new_launches,
    _send_webhook_notifications,
)


@pytest.fixture
def temp_data_dir(tmp_path, monkeypatch):
    """Create temporary data directory for testing."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Mock the DATA_DIR in webhook_manager
    import app.services.webhook_manager as wm
    monkeypatch.setattr(wm, "DATA_DIR", data_dir)
    monkeypatch.setattr(wm, "WEBHOOKS_FILE", data_dir / "webhooks.json")
    monkeypatch.setattr(wm, "LAUNCHES_CACHE", data_dir / "launches_cache.json")

    return data_dir


@pytest.fixture
def mock_spacex_api():
    """Mock SpaceX API client."""
    with patch("app.services.background_service.SpaceXAPIClient") as mock:
        yield mock


@pytest.fixture
def mock_requests():
    """Mock requests library."""
    with patch("app.services.background_service.requests") as mock:
        yield mock


def test_check_new_launches_no_api_data(temp_data_dir, mock_spacex_api):
    """Test check_new_launches when API returns no data."""
    # Mock API to return empty list
    mock_api_instance = Mock()
    mock_api_instance.get_all_launches = AsyncMock(return_value=[])
    mock_spacex_api.return_value = mock_api_instance

    # Should not raise an error
    check_new_launches()


def test_check_new_launches_with_new_launch(temp_data_dir, mock_spacex_api, mock_requests):
    """Test check_new_launches detects new launches."""
    from app.models.launch import Launch
    from app.services.webhook_manager import add_webhook

    # Create a test launch
    now = datetime.now(timezone.utc)
    test_launch = Launch(
        id="test-launch-1",
        name="Test Launch",
        date_utc=now.isoformat(),
        date_local=now.isoformat(),
        success=True,
        flight_number=1,
        upcoming=False,
        rocket="test-rocket",
        launchpad="test-pad"
    )

    # Mock API to return the test launch
    mock_api_instance = Mock()
    mock_api_instance.get_all_launches = AsyncMock(return_value=[test_launch])
    mock_spacex_api.return_value = mock_api_instance

    # Add a webhook
    add_webhook("https://example.com/webhook", "Test webhook")

    # Mock requests.post
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_requests.post.return_value = mock_response

    # Run check
    check_new_launches()

    # Verify webhook was called
    assert mock_requests.post.called
    call_args = mock_requests.post.call_args

    # Verify URL
    assert call_args[0][0] == "https://example.com/webhook"

    # Verify payload structure
    payload = call_args[1]["json"]
    assert payload["event"] == "new_launch"
    assert "timestamp" in payload
    assert payload["launch"]["id"] == "test-launch-1"
    assert payload["launch"]["name"] == "Test Launch"


def test_check_new_launches_no_new_launches(temp_data_dir, mock_spacex_api, mock_requests):
    """Test check_new_launches when no new launches."""
    from app.models.launch import Launch
    from app.services.webhook_manager import save_cached_launch_ids

    # Create a test launch
    now = datetime.now(timezone.utc)
    test_launch = Launch(
        id="test-launch-1",
        name="Test Launch",
        date_utc=now.isoformat(),
        date_local=now.isoformat(),
        success=True,
        flight_number=1,
        upcoming=False,
        rocket="test-rocket",
        launchpad="test-pad"
    )

    # Cache the launch ID (simulate it was already seen)
    save_cached_launch_ids(["test-launch-1"])

    # Mock API to return the same launch
    mock_api_instance = Mock()
    mock_api_instance.get_all_launches = AsyncMock(return_value=[test_launch])
    mock_spacex_api.return_value = mock_api_instance

    # Run check
    check_new_launches()

    # Verify webhook was NOT called
    assert not mock_requests.post.called


def test_send_webhook_notifications(mock_requests):
    """Test sending webhook notifications."""
    launch = {
        "id": "test-launch-1",
        "name": "Test Launch",
        "date_utc": "2026-01-05T12:00:00Z",
        "success": True,
        "upcoming": False,
        "details": "Test details",
        "flight_number": 1
    }

    webhooks = [
        {"url": "https://example.com/webhook1"},
        {"url": "https://example.com/webhook2"}
    ]

    # Mock successful response
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_requests.post.return_value = mock_response

    # Send notifications
    _send_webhook_notifications(launch, webhooks)

    # Verify both webhooks were called
    assert mock_requests.post.call_count == 2


def test_send_webhook_notifications_with_datetime(mock_requests):
    """Test sending webhook with datetime objects."""
    launch = {
        "id": "test-launch-1",
        "name": "Test Launch",
        "date_utc": datetime(2026, 1, 5, 12, 0, 0),  # datetime object
        "success": True,
        "upcoming": False,
        "details": "Test details",
        "flight_number": 1
    }

    webhooks = [{"url": "https://example.com/webhook"}]

    # Mock successful response
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_requests.post.return_value = mock_response

    # Should not raise an error
    _send_webhook_notifications(launch, webhooks)

    # Verify datetime was serialized
    call_args = mock_requests.post.call_args
    payload = call_args[1]["json"]
    assert isinstance(payload["launch"]["date_utc"], str)


def test_send_webhook_notifications_failure(mock_requests, caplog):
    """Test webhook notification failure handling."""
    launch = {
        "id": "test-launch-1",
        "name": "Test Launch",
        "date_utc": "2026-01-05T12:00:00Z",
        "success": True,
        "upcoming": False,
        "details": "Test",
        "flight_number": 1
    }

    webhooks = [{"url": "https://example.com/webhook"}]

    # Mock failed response
    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 500
    mock_requests.post.return_value = mock_response

    # Should not raise an error, just log
    _send_webhook_notifications(launch, webhooks)

    # Verify warning was logged
    assert "Webhook failed" in caplog.text


def test_send_webhook_notifications_exception(mock_requests, caplog):
    """Test webhook notification with exception."""
    launch = {
        "id": "test-launch-1",
        "name": "Test Launch",
        "date_utc": "2026-01-05T12:00:00Z",
        "success": True,
        "upcoming": False,
        "details": "Test",
        "flight_number": 1
    }

    webhooks = [{"url": "https://example.com/webhook"}]

    # Mock exception
    mock_requests.post.side_effect = Exception("Network error")

    # Should not raise an error, just log
    _send_webhook_notifications(launch, webhooks)

    # Verify error was logged
    assert "Error sending webhook" in caplog.text


def test_check_new_launches_api_error(temp_data_dir, mock_spacex_api, caplog):
    """Test check_new_launches handles API errors."""
    # Mock API to raise an error
    mock_api_instance = Mock()
    mock_api_instance.get_all_launches.side_effect = Exception("API Error")
    mock_spacex_api.return_value = mock_api_instance

    # Should not raise an error
    check_new_launches()

    # Verify error was logged
    assert "Error checking new launches" in caplog.text


def test_check_new_launches_multiple_new_launches(temp_data_dir, mock_spacex_api, mock_requests):
    """Test check_new_launches with multiple new launches."""
    from app.models.launch import Launch
    from app.services.webhook_manager import add_webhook

    # Create multiple test launches
    now = datetime.now(timezone.utc)
    launches = [
        Launch(
            id=f"test-launch-{i}",
            name=f"Test Launch {i}",
            date_utc=now.isoformat(),
            date_local=now.isoformat(),
            success=True,
            flight_number=i,
            upcoming=False,
            rocket="test-rocket",
            launchpad="test-pad"
        )
        for i in range(3)
    ]

    # Mock API
    mock_api_instance = Mock()
    mock_api_instance.get_all_launches = AsyncMock(return_value=launches)
    mock_spacex_api.return_value = mock_api_instance

    # Add a webhook
    add_webhook("https://example.com/webhook")

    # Mock requests
    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_requests.post.return_value = mock_response

    # Run check
    check_new_launches()

    # Verify webhook was called 3 times (once per launch)
    assert mock_requests.post.call_count == 3
