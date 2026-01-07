"""Background service to check for new launches and send webhooks."""
import asyncio
import logging
import threading
import time
from datetime import datetime, timezone

import requests
import schedule

from app.lib.spacex_api import SpaceXAPIClient
from app.services.webhook_manager import (
    get_webhooks,
    get_cached_launch_ids,
    save_cached_launch_ids
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def check_new_launches():
    """
    Check for new launches and send webhook notifications.

    Runs periodically to detect new SpaceX launches.
    """
    logger.info("Checking for new launches...")

    try:
        # Fetch launches from SpaceX API
        api = SpaceXAPIClient()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        launch_objects = loop.run_until_complete(api.get_all_launches())
        loop.close()

        if not launch_objects:
            logger.warning("No launches fetched from SpaceX API")
            return

        # Convert Launch objects to dicts
        launches = [launch.model_dump() for launch in launch_objects]

        # Get cached launch IDs
        cached_ids = get_cached_launch_ids()

        # Find new launches
        current_ids = {launch["id"] for launch in launches}
        new_launch_ids = current_ids - cached_ids

        if new_launch_ids:
            logger.info("Found %d new launches!", len(new_launch_ids))

            # Get new launch data
            new_launches = [l for l in launches if l["id"] in new_launch_ids]

            # Get active webhooks
            webhooks = get_webhooks(active_only=True)

            if webhooks:
                # Send webhooks for each new launch
                for launch in new_launches:
                    _send_webhook_notifications(launch, webhooks)
            else:
                logger.info("No active webhooks configured")

            # Update cache
            save_cached_launch_ids(list(current_ids))
        else:
            logger.info("No new launches found")
            # Still update cache
            save_cached_launch_ids(list(current_ids))

    except Exception as e:
        logger.error("Error checking new launches: %s", e, exc_info=True)


def _send_webhook_notifications(launch: dict, webhooks: list):
    """
    Send webhook notifications for a new launch.

    Args:
        launch: Launch data
        webhooks: List of webhook subscriptions
    """
    # Convert datetime objects to strings for JSON serialization
    def serialize_value(value):
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    payload = {
        "event": "new_launch",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "launch": {
            "id": launch.get("id"),
            "name": launch.get("name"),
            "date_utc": serialize_value(launch.get("date_utc")),
            "success": launch.get("success"),
            "upcoming": launch.get("upcoming"),
            "details": launch.get("details"),
            "flight_number": launch.get("flight_number"),
        }
    }

    for webhook in webhooks:
        try:
            logger.info(
                "Sending webhook to %s for launch '%s'",
                webhook['url'], launch.get('name')
            )

            response = requests.post(
                webhook["url"],
                json=payload,
                timeout=10,
                headers={"Content-Type": "application/json"}
            )

            if response.ok:
                logger.info("✓ Webhook sent successfully: %s", response.status_code)
            else:
                logger.warning("✗ Webhook failed: %s", response.status_code)

        except Exception as e:
            logger.error("✗ Error sending webhook to %s: %s", webhook['url'], e)


def _run_scheduler():
    """Run the background scheduler in a separate thread."""
    # Schedule the task to run every 5 seconds
    schedule.every(5).seconds.do(check_new_launches)

    # Run immediately on startup
    check_new_launches()

    logger.info("Background scheduler started - checking for new launches every 5 seconds")

    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


def start_background_service():
    """Start the background service in a daemon thread."""
    thread = threading.Thread(target=_run_scheduler, daemon=True)
    thread.start()
    logger.info("Background service started")
