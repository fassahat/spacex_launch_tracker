"""Web interface controller for HTML pages."""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from app.lib.spacex_api import SpaceXAPIClient
from app.services.launch_service import LaunchService
from app.services.stats_service import StatsService
from app.models.launch import LaunchFilter


router = APIRouter(prefix="/web", tags=["web"])
templates = Jinja2Templates(directory="app/templates")


def get_api_client() -> SpaceXAPIClient:
    """Dependency to get API client instance."""
    return SpaceXAPIClient()


def get_launch_service(
    api_client: SpaceXAPIClient = Depends(get_api_client)
) -> LaunchService:
    """Dependency to get launch service instance."""
    return LaunchService(api_client)


def get_stats_service(
    api_client: SpaceXAPIClient = Depends(get_api_client)
) -> StatsService:
    """Dependency to get statistics service instance."""
    return StatsService(api_client)


@router.get("/launches", response_class=HTMLResponse)
async def launches_page(
    request: Request,
    rocket_name: Optional[str] = None,
    launchpad_name: Optional[str] = None,
    success: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    launch_service: LaunchService = Depends(get_launch_service)
):
    """Display launches page with filters."""
    try:
        # Get rockets and launchpads for name mapping
        rockets = await launch_service.api_client.get_all_rockets()
        launchpads = await launch_service.api_client.get_all_launchpads()

        rocket_map = {r.id: r.name for r in rockets}
        launchpad_map = {lp.id: lp.name for lp in launchpads}

        # Build filters - convert dates to timezone-aware UTC
        from datetime import timezone
        date_from_utc = None
        date_to_utc = None
        if date_from:
            # Parse and make timezone-aware UTC
            date_from_utc = datetime.fromisoformat(date_from).replace(tzinfo=timezone.utc)
        if date_to:
            # Parse, set to end of day, and make timezone-aware UTC
            date_to_utc = datetime.fromisoformat(date_to).replace(hour=23, minute=59, second=59, tzinfo=timezone.utc)

        launch_filters = LaunchFilter(
            rocket_name=rocket_name if rocket_name else None,
            launchpad_name=launchpad_name if launchpad_name else None,
            success=success.lower() == 'true' if success and success != '' else None,
            date_from=date_from_utc,
            date_to=date_to_utc,
            limit=1000
        )

        # Get launches
        launches = await launch_service.get_filtered_launches(
            launch_filters,
            rocket_id_map=rocket_map,
            launchpad_id_map=launchpad_map
        )

        return templates.TemplateResponse(
            "launches.html",
            {
                "request": request,
                "launches": launches,
                "rocket_map": rocket_map,
                "launchpad_map": launchpad_map,
                "filters": {
                    "rocket_name": rocket_name or '',
                    "launchpad_name": launchpad_name or '',
                    "success": success or '',
                    "date_from": date_from or '',
                    "date_to": date_to or ''
                }
            }
        )
    except Exception as e:
        # Return error page with details
        return templates.TemplateResponse(
            "launches.html",
            {
                "request": request,
                "launches": [],
                "rocket_map": {},
                "launchpad_map": {},
                "filters": {
                    "rocket_name": rocket_name or '',
                    "launchpad_name": launchpad_name or '',
                    "success": success or '',
                    "date_from": date_from or '',
                    "date_to": date_to or ''
                },
                "error": f"Error loading launches: {str(e)}"
            }
        )


@router.get("/statistics", response_class=HTMLResponse)
async def statistics_page(
    request: Request,
    stats_service: StatsService = Depends(get_stats_service)
):
    """Display statistics page."""
    # Get all statistics
    overall = await stats_service.get_overall_statistics()
    success_rate = await stats_service.get_success_rate_by_rocket()
    launchpads = await stats_service.get_launches_by_launchpad()
    frequency = await stats_service.get_launch_frequency()

    return templates.TemplateResponse(
        "statistics.html",
        {
            "request": request,
            "overall": overall,
            "success_rate": success_rate,
            "launchpads": launchpads,
            "frequency": frequency
        }
    )
