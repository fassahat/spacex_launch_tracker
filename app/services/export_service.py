"""Service for exporting launch data to various formats."""

import csv
import io
import json
from typing import List, Dict, Optional, Iterator
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

        # Fetch all launches with filters (no pagination for export)
        launch_filters = LaunchFilter(
            rocket_name=rocket_name if rocket_name else None,
            launchpad_name=launchpad_name if launchpad_name else None,
            success=(
                success.lower() == 'true'
                if success and success.lower() in ('true', 'false')
                else None
            ),
            date_from=date_from_utc,
            date_to=date_to_utc,
            limit=None,
            offset=0,
        )

        launches = await self.launch_service.get_filtered_launches(
            launch_filters,
            rocket_id_map=rocket_map,
            launchpad_id_map=launchpad_map
        )

        return launches, rocket_map, launchpad_map

    def generate_csv_stream(
        self,
        launches: List[Launch],
        rocket_map: Dict[str, str],
        launchpad_map: Dict[str, str]
    ) -> Iterator[str]:
        """
        Generate CSV content as an iterator for memory-efficient streaming.
        Yields CSV rows one at a time instead of building entire file in memory.
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write and yield header
        writer.writerow([
            'Mission Name', 'Date (UTC)', 'Rocket', 'Launchpad',
            'Success', 'Flight Number', 'Details'
        ])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        # Write and yield data rows
        for launch in launches:
            writer.writerow([
                launch.name,
                launch.date_utc.isoformat() if launch.date_utc else 'TBD',
                rocket_map.get(launch.rocket, launch.rocket or 'Unknown'),
                launchpad_map.get(launch.launchpad, launch.launchpad or 'Unknown'),
                (
                    'Success' if launch.success is True
                    else 'Failed' if launch.success is False
                    else 'Upcoming'
                ),
                launch.flight_number or '-',
                launch.details or ''
            ])
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    def generate_csv(
        self,
        launches: List[Launch],
        rocket_map: Dict[str, str],
        launchpad_map: Dict[str, str]
    ) -> str:
        """Generate CSV content from launch data (non-streaming, for compatibility)."""
        return ''.join(self.generate_csv_stream(launches, rocket_map, launchpad_map))

    def _serialize_launch(
        self,
        launch: Launch,
        rocket_map: Dict[str, str],
        launchpad_map: Dict[str, str]
    ) -> dict:
        """Convert a launch object to a dictionary for JSON serialization."""
        return {
            "mission_name": launch.name,
            "date_utc": launch.date_utc.isoformat() if launch.date_utc else None,
            "rocket": rocket_map.get(launch.rocket, launch.rocket or 'Unknown'),
            "launchpad": launchpad_map.get(launch.launchpad, launch.launchpad or 'Unknown'),
            "success": launch.success,
            "flight_number": launch.flight_number,
            "details": launch.details,
            "upcoming": launch.upcoming
        }

    def generate_json_stream(
        self,
        launches: List[Launch],
        rocket_map: Dict[str, str],
        launchpad_map: Dict[str, str]
    ) -> Iterator[str]:
        """
        Generate JSON content as an iterator for memory-efficient streaming.
        Yields JSON in chunks instead of building entire array in memory.
        """
        # Yield opening bracket
        yield "[\n"

        # Yield each launch object
        for i, launch in enumerate(launches):
            launch_dict = self._serialize_launch(launch, rocket_map, launchpad_map)
            # Add proper indentation and comma handling
            json_str = json.dumps(launch_dict, indent=2)
            # Indent each line by 2 spaces to match array formatting
            indented = '\n'.join('  ' + line for line in json_str.split('\n'))

            if i < len(launches) - 1:
                yield indented + ',\n'
            else:
                yield indented + '\n'

        # Yield closing bracket
        yield "]"

    def generate_json(
        self,
        launches: List[Launch],
        rocket_map: Dict[str, str],
        launchpad_map: Dict[str, str]
    ) -> str:
        """Generate JSON content from launch data (non-streaming, for compatibility)."""
        return ''.join(self.generate_json_stream(launches, rocket_map, launchpad_map))
