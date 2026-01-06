"""Tests for webhook controller endpoints."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


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


def test_create_webhook(client, temp_data_dir):
    """Test creating a webhook via API."""
    response = client.post(
        "/webhooks",
        json={
            "url": "https://example.com/webhook",
            "description": "Test webhook"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["url"] == "https://example.com/webhook"
    assert data["description"] == "Test webhook"
    assert data["active"] is True
    assert "id" in data
    assert "created_at" in data


def test_create_webhook_minimal(client, temp_data_dir):
    """Test creating webhook with minimal data."""
    response = client.post(
        "/webhooks",
        json={"url": "https://example.com/webhook"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["url"] == "https://example.com/webhook"
    assert data["description"] is None


def test_create_webhook_invalid_url(client, temp_data_dir):
    """Test creating webhook with invalid URL."""
    response = client.post(
        "/webhooks",
        json={"url": "not-a-valid-url"}
    )

    assert response.status_code == 422  # Validation error


def test_list_webhooks_empty(client, temp_data_dir):
    """Test listing webhooks when none exist."""
    response = client.get("/webhooks")

    assert response.status_code == 200
    data = response.json()
    assert data == []


def test_list_webhooks(client, temp_data_dir):
    """Test listing webhooks."""
    # Create some webhooks
    client.post("/webhooks", json={"url": "https://example.com/webhook1"})
    client.post("/webhooks", json={"url": "https://example.com/webhook2"})

    # List all
    response = client.get("/webhooks")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["url"] == "https://example.com/webhook1"
    assert data[1]["url"] == "https://example.com/webhook2"


def test_list_webhooks_active_only(client, temp_data_dir):
    """Test listing only active webhooks."""
    # Create webhooks
    client.post("/webhooks", json={"url": "https://example.com/webhook1"})
    client.post("/webhooks", json={"url": "https://example.com/webhook2"})

    # Manually deactivate one (in real scenario, would use update endpoint)
    import json
    import app.services.webhook_manager as wm
    with open(wm.WEBHOOKS_FILE, "r") as f:
        webhooks = json.load(f)
    webhooks[0]["active"] = False
    with open(wm.WEBHOOKS_FILE, "w") as f:
        json.dump(webhooks, f)

    # List active only
    response = client.get("/webhooks?active_only=true")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["active"] is True


def test_delete_webhook(client, temp_data_dir):
    """Test deleting a webhook."""
    # Create webhook
    create_response = client.post(
        "/webhooks",
        json={"url": "https://example.com/webhook"}
    )
    webhook_id = create_response.json()["id"]

    # Delete webhook
    delete_response = client.delete(f"/webhooks/{webhook_id}")

    assert delete_response.status_code == 200
    assert "deleted successfully" in delete_response.json()["message"]

    # Verify it's deleted
    list_response = client.get("/webhooks")
    assert len(list_response.json()) == 0


def test_delete_nonexistent_webhook(client, temp_data_dir):
    """Test deleting a webhook that doesn't exist."""
    response = client.delete("/webhooks/999")

    # Should return 404 when webhook doesn't exist
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_multiple_webhooks(client, temp_data_dir):
    """Test creating multiple webhooks."""
    urls = [
        "https://example.com/webhook1",
        "https://example.com/webhook2",
        "https://example.com/webhook3"
    ]

    for url in urls:
        response = client.post("/webhooks", json={"url": url})
        assert response.status_code == 201

    # Verify all created
    list_response = client.get("/webhooks")
    data = list_response.json()
    assert len(data) == 3

    # Verify IDs are sequential
    assert data[0]["id"] == 1
    assert data[1]["id"] == 2
    assert data[2]["id"] == 3


def test_webhook_response_format(client, temp_data_dir):
    """Test that webhook response has correct format."""
    response = client.post(
        "/webhooks",
        json={
            "url": "https://example.com/webhook",
            "description": "Test"
        }
    )

    data = response.json()

    # Check all required fields are present
    required_fields = ["id", "url", "description", "active", "created_at"]
    for field in required_fields:
        assert field in data

    # Check types
    assert isinstance(data["id"], int)
    assert isinstance(data["url"], str)
    assert isinstance(data["active"], bool)
    assert isinstance(data["created_at"], str)


def test_create_webhook_with_long_description(client, temp_data_dir):
    """Test creating webhook with long description."""
    long_description = "A" * 500  # Very long description

    response = client.post(
        "/webhooks",
        json={
            "url": "https://example.com/webhook",
            "description": long_description
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["description"] == long_description


def test_webhook_url_formats(client, temp_data_dir):
    """Test various URL formats."""
    valid_urls = [
        "https://example.com/webhook",
        "https://example.com:8080/webhook",
        "https://sub.example.com/webhook",
        "https://example.com/path/to/webhook"
    ]

    for url in valid_urls:
        response = client.post("/webhooks", json={"url": url})
        assert response.status_code == 201, f"Failed for URL: {url}"


def test_concurrent_webhook_creation(client, temp_data_dir):
    """Test creating webhooks rapidly."""
    responses = []

    for i in range(10):
        response = client.post(
            "/webhooks",
            json={"url": f"https://example.com/webhook{i}"}
        )
        responses.append(response)

    # All should succeed
    assert all(r.status_code == 201 for r in responses)

    # Verify all created
    list_response = client.get("/webhooks")
    assert len(list_response.json()) == 10
