"""Tests for webhook manager service."""
import json
import pytest
from pathlib import Path

from app.services.webhook_manager import (
    add_webhook,
    get_webhooks,
    delete_webhook,
    get_cached_launch_ids,
    save_cached_launch_ids,
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


def test_add_webhook(temp_data_dir):
    """Test adding a webhook."""
    webhook = add_webhook("https://example.com/webhook", "Test webhook")

    assert webhook["id"] == 1
    assert webhook["url"] == "https://example.com/webhook"
    assert webhook["description"] == "Test webhook"
    assert webhook["active"] is True
    assert "created_at" in webhook


def test_add_multiple_webhooks(temp_data_dir):
    """Test adding multiple webhooks."""
    webhook1 = add_webhook("https://example.com/webhook1")
    webhook2 = add_webhook("https://example.com/webhook2", "Second webhook")

    assert webhook1["id"] == 1
    assert webhook2["id"] == 2

    webhooks = get_webhooks()
    assert len(webhooks) == 2


def test_get_webhooks_empty(temp_data_dir):
    """Test getting webhooks when none exist."""
    webhooks = get_webhooks()
    assert webhooks == []


def test_get_webhooks_active_only(temp_data_dir):
    """Test getting only active webhooks."""
    # Add webhooks
    add_webhook("https://example.com/webhook1")
    add_webhook("https://example.com/webhook2")

    # Manually deactivate one
    import app.services.webhook_manager as wm
    webhooks_file = wm.WEBHOOKS_FILE
    with open(webhooks_file, "r") as f:
        webhooks = json.load(f)
    webhooks[0]["active"] = False
    with open(webhooks_file, "w") as f:
        json.dump(webhooks, f)

    # Get active only
    active_webhooks = get_webhooks(active_only=True)
    assert len(active_webhooks) == 1
    assert active_webhooks[0]["url"] == "https://example.com/webhook2"

    # Get all
    all_webhooks = get_webhooks(active_only=False)
    assert len(all_webhooks) == 2


def test_delete_webhook(temp_data_dir):
    """Test deleting a webhook."""
    webhook = add_webhook("https://example.com/webhook")

    # Delete webhook
    result = delete_webhook(webhook["id"])
    assert result is True

    # Verify it's deleted
    webhooks = get_webhooks()
    assert len(webhooks) == 0


def test_delete_nonexistent_webhook(temp_data_dir):
    """Test deleting a webhook that doesn't exist."""
    result = delete_webhook(999)
    # Should return False when webhook doesn't exist
    assert result is False


def test_get_cached_launch_ids_empty(temp_data_dir):
    """Test getting cached launch IDs when cache is empty."""
    launch_ids = get_cached_launch_ids()
    assert launch_ids == set()


def test_save_and_get_cached_launch_ids(temp_data_dir):
    """Test saving and retrieving cached launch IDs."""
    test_ids = ["launch1", "launch2", "launch3"]

    save_cached_launch_ids(test_ids)

    cached_ids = get_cached_launch_ids()
    assert cached_ids == set(test_ids)


def test_cached_launch_ids_persistence(temp_data_dir):
    """Test that cached launch IDs persist to file."""
    test_ids = ["launch1", "launch2"]
    save_cached_launch_ids(test_ids)

    # Read directly from file
    import app.services.webhook_manager as wm
    cache_file = wm.LAUNCHES_CACHE

    with open(cache_file, "r") as f:
        data = json.load(f)

    assert set(data["launch_ids"]) == set(test_ids)
    assert "updated_at" in data


def test_webhook_persistence(temp_data_dir):
    """Test that webhooks persist to file."""
    webhook = add_webhook("https://example.com/webhook", "Test")

    # Read directly from file
    import app.services.webhook_manager as wm
    webhooks_file = wm.WEBHOOKS_FILE

    with open(webhooks_file, "r") as f:
        webhooks = json.load(f)

    assert len(webhooks) == 1
    assert webhooks[0]["url"] == "https://example.com/webhook"
    assert webhooks[0]["description"] == "Test"


def test_add_webhook_without_description(temp_data_dir):
    """Test adding webhook without description."""
    webhook = add_webhook("https://example.com/webhook")

    assert webhook["url"] == "https://example.com/webhook"
    assert webhook["description"] is None


def test_concurrent_webhook_operations(temp_data_dir):
    """Test multiple webhook operations."""
    # Add multiple webhooks
    for i in range(5):
        add_webhook(f"https://example.com/webhook{i}", f"Webhook {i}")

    # Get all
    all_webhooks = get_webhooks()
    assert len(all_webhooks) == 5

    # Delete some
    delete_webhook(2)
    delete_webhook(4)

    # Verify
    remaining = get_webhooks()
    assert len(remaining) == 3

    # Verify correct ones remain (webhook1 and webhook3 were deleted since they had IDs 2 and 4)
    urls = [w["url"] for w in remaining]
    assert "https://example.com/webhook0" in urls
    assert "https://example.com/webhook1" not in urls  # ID 2 was deleted
    assert "https://example.com/webhook2" in urls
    assert "https://example.com/webhook3" not in urls  # ID 4 was deleted
    assert "https://example.com/webhook4" in urls
