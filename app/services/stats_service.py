"""Service for calculating launch statistics."""

from typing import Dict
from collections import defaultdict
from datetime import datetime

from app.models.launch import Launch
from app.models.rocket import Rocket
from app.models.launchpad import Launchpad
from app.lib.spacex_api import SpaceXAPIClient


class StatsService:
    """Handles statistical calculations for launch data."""

    def __init__(self, api_client: SpaceXAPIClient):
        """
        Initialize statistics service.

        Args:
            api_client: SpaceX API client instance
        """
        self.api_client = api_client

    async def get_success_rate_by_rocket(self) -> Dict[str, dict]:
        """
        Calculate success rate for each rocket.

        Returns:
            Dictionary mapping rocket names to their statistics
        """
        launches = await self.api_client.get_all_launches()
        rockets = await self.api_client.get_all_rockets()

        # Create rocket ID to name mapping
        rocket_map = {r.id: r.name for r in rockets}

        # Count launches per rocket
        rocket_stats = defaultdict(lambda: {"total": 0, "successful": 0})

        for launch in launches:
            if launch.rocket and launch.success is not None:
                rocket_name = rocket_map.get(launch.rocket, "Unknown")
                rocket_stats[rocket_name]["total"] += 1
                if launch.success:
                    rocket_stats[rocket_name]["successful"] += 1

        # Calculate success rates
        result = {}
        for rocket_name, stats in rocket_stats.items():
            total = stats["total"]
            successful = stats["successful"]
            success_rate = (successful / total * 100) if total > 0 else 0

            result[rocket_name] = {
                "total_launches": total,
                "successful_launches": successful,
                "failed_launches": total - successful,
                "success_rate_percentage": round(success_rate, 2)
            }

        return result

    async def get_launches_by_launchpad(self) -> Dict[str, dict]:
        """
        Count total launches for each launchpad.

        Returns:
            Dictionary mapping launchpad names to launch counts
        """
        launches = await self.api_client.get_all_launches()
        launchpads = await self.api_client.get_all_launchpads()

        # Create launchpad ID to name mapping
        launchpad_map = {lp.id: lp.name for lp in launchpads}

        # Count launches per launchpad
        launchpad_counts = defaultdict(lambda: {"total": 0, "successful": 0})

        for launch in launches:
            if launch.launchpad:
                launchpad_name = launchpad_map.get(launch.launchpad, "Unknown")
                launchpad_counts[launchpad_name]["total"] += 1
                if launch.success:
                    launchpad_counts[launchpad_name]["successful"] += 1

        return dict(launchpad_counts)

    async def get_launch_frequency(self) -> Dict[str, dict]:
        """
        Calculate launch frequency by month and year.

        Returns:
            Dictionary with monthly and yearly launch frequencies
        """
        launches = await self.api_client.get_all_launches()

        monthly_counts = defaultdict(int)
        yearly_counts = defaultdict(int)

        for launch in launches:
            if launch.date_utc:
                year = launch.date_utc.year
                month = launch.date_utc.strftime("%Y-%m")

                yearly_counts[str(year)] += 1
                monthly_counts[month] += 1

        return {
            "by_month": dict(sorted(monthly_counts.items())),
            "by_year": dict(sorted(yearly_counts.items()))
        }

    async def get_overall_statistics(self) -> dict:
        """
        Get overall launch statistics summary.

        Returns:
            Dictionary with overall statistics
        """
        launches = await self.api_client.get_all_launches()

        total_launches = len(launches)
        successful = sum(1 for l in launches if l.success is True)
        failed = sum(1 for l in launches if l.success is False)
        upcoming = sum(1 for l in launches if l.upcoming is True)

        success_rate = (successful / (successful + failed) * 100) if (successful + failed) > 0 else 0

        return {
            "total_launches": total_launches,
            "successful_launches": successful,
            "failed_launches": failed,
            "upcoming_launches": upcoming,
            "overall_success_rate_percentage": round(success_rate, 2)
        }
