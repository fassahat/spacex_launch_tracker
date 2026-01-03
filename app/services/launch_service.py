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

        # Apply date range filter
        if filters.date_from:
            launches = [
                l for l in launches
                if l.date_utc and l.date_utc >= filters.date_from
            ]

        if filters.date_to:
            launches = [
                l for l in launches
                if l.date_utc and l.date_utc <= filters.date_to
            ]

        # Apply success filter
        if filters.success is not None:
            launches = [l for l in launches if l.success == filters.success]

        # Apply rocket name filter
        if filters.rocket_name and rocket_id_map:
            rocket_ids = [
                rocket_id for rocket_id, name in rocket_id_map.items()
                if filters.rocket_name.lower() in name.lower()
            ]
            launches = [l for l in launches if l.rocket in rocket_ids]

        # Apply launchpad name filter
        if filters.launchpad_name and launchpad_id_map:
            launchpad_ids = [
                lp_id for lp_id, name in launchpad_id_map.items()
                if filters.launchpad_name.lower() in name.lower()
            ]
            launches = [l for l in launches if l.launchpad in launchpad_ids]

        # Apply pagination
        start_idx = filters.offset
        end_idx = start_idx + filters.limit
        return launches[start_idx:end_idx]

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
