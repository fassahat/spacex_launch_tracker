"""Service for exporting launch data to various formats."""

import csv
import io
import json
from typing import List, Dict, Optional
from datetime import datetime, timezone

from app.models.launch import Launch, LaunchFilter
from app.services.launch_service import LaunchService


class ExportService:
    """Handles data export operations."""

    def __init__(self, launch_service: LaunchService):
        self.launch_service = launch_service

    async def prepare_launch_data(
        self,
        rocket_name: Optional[str] = None,
        launchpad_name: Optional[str] = None,
        success: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> tuple[List[Launch], Dict[str, str], Dict[str, str]]:
        """
        Prepare launch data with filters and mappings.

        Returns tuple of (launches, rocket_map, launchpad_map)
        """
        # Get rockets and launchpads for name mapping
        rockets = await self.launch_service.api_client.get_all_rockets()
        launchpads = await self.launch_service.api_client.get_all_launchpads()

        rocket_map = {r.id: r.name for r in rockets}
        launchpad_map = {lp.id: lp.name for lp in launchpads}

        # Convert dates to timezone-aware UTC
        date_from_utc = None
        date_to_utc = None
        if date_from:
            date_from_utc = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
        if date_to:
            date_to_utc = datetime.fromisoformat(date_to).replace(
                hour=23, minute=59, second=59, tzinfo=timezone.utc
            )

        # Fetch all launches with pagination (max limit is 1000)
        all_launches = []
        offset = 0
        limit = 1000

        while True:
            launch_filters = LaunchFilter(
                rocket_name=rocket_name if rocket_name else None,
                launchpad_name=launchpad_name if launchpad_name else None,
                success=success.lower() == 'true' if success and success != '' else None,
                date_from=date_from_utc,
                date_to=date_to_utc,
                limit=limit,
                offset=offset
            )

            launches = await self.launch_service.get_filtered_launches(
                launch_filters,
                rocket_id_map=rocket_map,
                launchpad_id_map=launchpad_map
            )

            if not launches:
                break

            all_launches.extend(launches)

            if len(launches) < limit:
                break

            offset += limit

        return all_launches, rocket_map, launchpad_map

    def generate_csv(
        self,
        launches: List[Launch],
        rocket_map: Dict[str, str],
        launchpad_map: Dict[str, str]
    ) -> str:
        """Generate CSV content from launch data."""
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            'Mission Name', 'Date (UTC)', 'Rocket', 'Launchpad',
            'Success', 'Flight Number', 'Details'
        ])

        # Write data
        for launch in launches:
            writer.writerow([
                launch.name,
                launch.date_utc.isoformat() if launch.date_utc else 'TBD',
                rocket_map.get(launch.rocket, launch.rocket or 'Unknown'),
                launchpad_map.get(launch.launchpad, launch.launchpad or 'Unknown'),
                'Success' if launch.success is True else 'Failed' if launch.success is False else 'Upcoming',
                launch.flight_number or '-',
                launch.details or ''
            ])

        output.seek(0)
        return output.getvalue()

    def generate_json(
        self,
        launches: List[Launch],
        rocket_map: Dict[str, str],
        launchpad_map: Dict[str, str]
    ) -> str:
        """Generate JSON content from launch data."""
        export_data = []
        for launch in launches:
            export_data.append({
                "mission_name": launch.name,
                "date_utc": launch.date_utc.isoformat() if launch.date_utc else None,
                "rocket": rocket_map.get(launch.rocket, launch.rocket or 'Unknown'),
                "launchpad": launchpad_map.get(launch.launchpad, launch.launchpad or 'Unknown'),
                "success": launch.success,
                "flight_number": launch.flight_number,
                "details": launch.details,
                "upcoming": launch.upcoming
            })

        return json.dumps(export_data, indent=2)
