"""FastAPI controller for launch endpoints."""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends

from app.models.launch import Launch, LaunchFilter
from app.lib.spacex_api import SpaceXAPIClient, SpaceXAPIError
from app.services.launch_service import LaunchService


router = APIRouter(prefix="/launches", tags=["launches"])


def get_api_client() -> SpaceXAPIClient:
    """Dependency to get API client instance."""
    return SpaceXAPIClient()


def get_launch_service(
    api_client: SpaceXAPIClient = Depends(get_api_client)
) -> LaunchService:
    """Dependency to get launch service instance."""
    return LaunchService(api_client)


@router.get("/", response_model=list[Launch])
async def get_launches(
    date_from: Optional[datetime] = Query(None, description="Start date filter"),
    date_to: Optional[datetime] = Query(None, description="End date filter"),
    rocket_name: Optional[str] = Query(None, description="Filter by rocket name"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    launchpad_name: Optional[str] = Query(None, description="Filter by launchpad name"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    launch_service: LaunchService = Depends(get_launch_service),
    api_client: SpaceXAPIClient = Depends(get_api_client)
) -> list[Launch]:
    """
    Get filtered list of SpaceX launches.

    Supports filtering by date range, rocket, success status, and launchpad.
    """
    try:
        # Build filter object
        filters = LaunchFilter(
            date_from=date_from,
            date_to=date_to,
            rocket_name=rocket_name,
            success=success,
            launchpad_name=launchpad_name,
            limit=limit,
            offset=offset
        )

        # Get mappings for filtering
        rocket_map = None
        launchpad_map = None

        if rocket_name:
            rockets = await api_client.get_all_rockets()
            rocket_map = {r.id: r.name for r in rockets}

        if launchpad_name:
            launchpads = await api_client.get_all_launchpads()
            launchpad_map = {lp.id: lp.name for lp in launchpads}

        # Get filtered launches
        launches = await launch_service.get_filtered_launches(
            filters, rocket_map, launchpad_map
        )

        return launches

    except SpaceXAPIError as e:
        raise HTTPException(status_code=503, detail=f"SpaceX API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/{launch_id}", response_model=Launch)
async def get_launch_by_id(
    launch_id: str,
    launch_service: LaunchService = Depends(get_launch_service)
) -> Launch:
    """
    Get a specific launch by ID.

    Args:
        launch_id: The unique identifier of the launch
    """
    try:
        launch = await launch_service.get_launch_by_id(launch_id)

        if not launch:
            raise HTTPException(status_code=404, detail="Launch not found")

        return launch

    except HTTPException:
        raise
    except SpaceXAPIError as e:
        raise HTTPException(status_code=503, detail=f"SpaceX API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
