"""Webhook management service using JSON file storage."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional


# Data directory for storing webhook and cache files
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

WEBHOOKS_FILE = DATA_DIR / "webhooks.json"
LAUNCHES_CACHE = DATA_DIR / "launches_cache.json"


def load_webhooks() -> List[dict]:
    """Load webhooks from JSON file."""
    if not WEBHOOKS_FILE.exists():
        return []

    try:
        with open(WEBHOOKS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def save_webhooks(webhooks: List[dict]) -> None:
    """Save webhooks to JSON file."""
    with open(WEBHOOKS_FILE, "w") as f:
        json.dump(webhooks, f, indent=2)


def add_webhook(url: str, description: Optional[str] = None) -> dict:
    """Add a new webhook subscription."""
    webhooks = load_webhooks()

    webhook = {
        "id": len(webhooks) + 1,
        "url": url,
        "description": description,
        "active": True,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    webhooks.append(webhook)
    save_webhooks(webhooks)

    return webhook


def get_webhooks(active_only: bool = False) -> List[dict]:
    """Get all webhook subscriptions."""
    webhooks = load_webhooks()

    if active_only:
        return [w for w in webhooks if w.get("active", True)]

    return webhooks


def delete_webhook(webhook_id: int) -> bool:
    """Delete a webhook subscription."""
    webhooks = load_webhooks()
    initial_count = len(webhooks)

    webhooks = [w for w in webhooks if w["id"] != webhook_id]
    save_webhooks(webhooks)

    return len(webhooks) < initial_count


def get_cached_launch_ids() -> set:
    """Get previously seen launch IDs from cache."""
    if not LAUNCHES_CACHE.exists():
        return set()

    try:
        with open(LAUNCHES_CACHE, "r") as f:
            data = json.load(f)
            return set(data.get("launch_ids", []))
    except (json.JSONDecodeError, FileNotFoundError):
        return set()


def save_cached_launch_ids(launch_ids: List[str]) -> None:
    """Save launch IDs to cache."""
    with open(LAUNCHES_CACHE, "w") as f:
        json.dump({
            "launch_ids": list(launch_ids),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }, f, indent=2)
