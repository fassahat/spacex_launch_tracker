"""Service for launch data operations and filtering."""

from typing import Optional
from datetime import datetime

from app.models.launch import Launch, LaunchFilter
from app.lib.spacex_api import SpaceXAPIClient


class LaunchService:
    """Handles launch data retrieval and filtering."""

    def __init__(self, api_client: SpaceXAPIClient):
        """
        Initialize launch service.

        Args:
            api_client: SpaceX API client instance
        """
        self.api_client = api_client

    async def get_filtered_launches(
        self,
        filters: LaunchFilter,
        rocket_id_map: Optional[dict[str, str]] = None,
        launchpad_id_map: Optional[dict[str, str]] = None
    ) -> list[Launch]:
        """
        Get launches with applied filters.

        Args:
            filters: Filter parameters
            rocket_id_map: Optional mapping of rocket IDs to names
            launchpad_id_map: Optional mapping of launchpad IDs to names

        Returns:
            Filtered list of launches
        """
        launches = await self.api_client.get_all_launches()

        # Pre-compute ID sets for efficient filtering
        rocket_ids = None
        if filters.rocket_name and rocket_id_map:
            rocket_ids = {
                rocket_id for rocket_id, name in rocket_id_map.items()
                if filters.rocket_name.lower() in name.lower()
            }

        launchpad_ids = None
        if filters.launchpad_name and launchpad_id_map:
            launchpad_ids = {
                lp_id for lp_id, name in launchpad_id_map.items()
                if filters.launchpad_name.lower() in name.lower()
            }

        # Apply all filters in a single pass
        filtered_launches = [
            launch for launch in launches
            if self._matches_filters(launch, filters, rocket_ids, launchpad_ids)
        ]

        # Apply pagination
        if filters.limit is not None:
            start_idx = filters.offset
            end_idx = start_idx + filters.limit
            return filtered_launches[start_idx:end_idx]

        return filtered_launches

    def _matches_filters(
        self,
        launch: Launch,
        filters: LaunchFilter,
        rocket_ids: Optional[set[str]],
        launchpad_ids: Optional[set[str]]
    ) -> bool:
        """Check if a launch matches all filter criteria."""
        if filters.date_from and (not launch.date_utc or launch.date_utc < filters.date_from):
            return False

        if filters.date_to and (not launch.date_utc or launch.date_utc > filters.date_to):
            return False

        if filters.success is not None and launch.success != filters.success:
            return False

        if rocket_ids is not None and launch.rocket not in rocket_ids:
            return False

        if launchpad_ids is not None and launch.launchpad not in launchpad_ids:
            return False

        return True

    async def get_launch_by_id(self, launch_id: str) -> Optional[Launch]:
        """
        Get a specific launch by ID.

        Args:
            launch_id: Launch identifier

        Returns:
            Launch object if found, None otherwise
        """
        launches = await self.api_client.get_all_launches()
        return next((l for l in launches if l.id == launch_id), None)
