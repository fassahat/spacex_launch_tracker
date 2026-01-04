"""Web interface controller for HTML pages."""

from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse

from app.lib.spacex_api import SpaceXAPIClient
from app.services.launch_service import LaunchService
from app.services.stats_service import StatsService
from app.services.export_service import ExportService
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


def get_export_service(
    launch_service: LaunchService = Depends(get_launch_service)
) -> ExportService:
    """Dependency to get export service instance."""
    return ExportService(launch_service)


def build_filter_dict(
    rocket_name: Optional[str],
    launchpad_name: Optional[str],
    success: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str]
) -> dict:
    """Build filter dictionary for templates."""
    return {
        "rocket_name": rocket_name or '',
        "launchpad_name": launchpad_name or '',
        "success": success or '',
        "date_from": date_from or '',
        "date_to": date_to or ''
    }


async def get_launches_with_maps(
    launch_service: LaunchService,
    rocket_name: Optional[str],
    launchpad_name: Optional[str],
    success: Optional[str],
    date_from: Optional[str],
    date_to: Optional[str],
    limit: int = 1000
):
    """Helper to get launches with rocket and launchpad mappings."""
    # Get rockets and launchpads for name mapping
    rockets = await launch_service.api_client.get_all_rockets()
    launchpads = await launch_service.api_client.get_all_launchpads()

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

    # Build filters
    launch_filters = LaunchFilter(
        rocket_name=rocket_name if rocket_name else None,
        launchpad_name=launchpad_name if launchpad_name else None,
        success=success.lower() == 'true' if success and success != '' else None,
        date_from=date_from_utc,
        date_to=date_to_utc,
        limit=limit
    )

    # Get launches
    launches = await launch_service.get_filtered_launches(
        launch_filters,
        rocket_id_map=rocket_map,
        launchpad_id_map=launchpad_map
    )

    return launches, rocket_map, launchpad_map


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
        launches, rocket_map, launchpad_map = await get_launches_with_maps(
            launch_service, rocket_name, launchpad_name, success, date_from, date_to
        )

        return templates.TemplateResponse(
            "launches.html",
            {
                "request": request,
                "launches": launches,
                "rocket_map": rocket_map,
                "launchpad_map": launchpad_map,
                "filters": build_filter_dict(rocket_name, launchpad_name, success, date_from, date_to)
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "launches.html",
            {
                "request": request,
                "launches": [],
                "rocket_map": {},
                "launchpad_map": {},
                "filters": build_filter_dict(rocket_name, launchpad_name, success, date_from, date_to),
                "error": f"Error loading launches: {str(e)}"
            }
        )


@router.get("/statistics", response_class=HTMLResponse)
async def statistics_page(
    request: Request,
    stats_service: StatsService = Depends(get_stats_service)
):
    """Display statistics page."""
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


@router.get("/export/launches/csv")
async def export_launches_csv(
    rocket_name: Optional[str] = None,
    launchpad_name: Optional[str] = None,
    success: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    export_service: ExportService = Depends(get_export_service)
):
    """Export launches to CSV format."""
    try:
        launches, rocket_map, launchpad_map = await export_service.prepare_launch_data(
            rocket_name, launchpad_name, success, date_from, date_to
        )

        # Use streaming generator for memory efficiency
        csv_stream = export_service.generate_csv_stream(launches, rocket_map, launchpad_map)

        return StreamingResponse(
            csv_stream,
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=spacex_launches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error exporting launches: {str(e)}"}
        )


@router.get("/export/launches/json")
async def export_launches_json(
    rocket_name: Optional[str] = None,
    launchpad_name: Optional[str] = None,
    success: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    export_service: ExportService = Depends(get_export_service)
):
    """Export launches to JSON format."""
    try:
        launches, rocket_map, launchpad_map = await export_service.prepare_launch_data(
            rocket_name, launchpad_name, success, date_from, date_to
        )

        # Use streaming generator for memory efficiency
        json_stream = export_service.generate_json_stream(launches, rocket_map, launchpad_map)

        return StreamingResponse(
            json_stream,
            media_type="application/json",
            headers={
                "Content-Disposition": f"attachment; filename=spacex_launches_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Error exporting launches: {str(e)}"}
        )
