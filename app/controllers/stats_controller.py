"""FastAPI controller for statistics endpoints."""

from typing import Dict
from fastapi import APIRouter, HTTPException, Depends

from app.lib.spacex_api import SpaceXAPIClient, SpaceXAPIError
from app.services.stats_service import StatsService


router = APIRouter(prefix="/stats", tags=["statistics"])


def get_api_client() -> SpaceXAPIClient:
    """Dependency to get API client instance."""
    return SpaceXAPIClient()


def get_stats_service(
    api_client: SpaceXAPIClient = Depends(get_api_client)
) -> StatsService:
    """Dependency to get statistics service instance."""
    return StatsService(api_client)


@router.get("/success-rate", response_model=Dict[str, dict])
async def get_success_rate_by_rocket(
    stats_service: StatsService = Depends(get_stats_service)
) -> Dict[str, dict]:
    """
    Get success rate statistics for each rocket.

    Returns launch counts and success rates grouped by rocket name.
    """
    try:
        return await stats_service.get_success_rate_by_rocket()
    except SpaceXAPIError as e:
        raise HTTPException(status_code=503, detail=f"SpaceX API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/launchpads", response_model=Dict[str, dict])
async def get_launches_by_launchpad(
    stats_service: StatsService = Depends(get_stats_service)
) -> Dict[str, dict]:
    """
    Get launch counts for each launchpad.

    Returns total and successful launch counts grouped by launchpad.
    """
    try:
        return await stats_service.get_launches_by_launchpad()
    except SpaceXAPIError as e:
        raise HTTPException(status_code=503, detail=f"SpaceX API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/frequency", response_model=Dict[str, dict])
async def get_launch_frequency(
    stats_service: StatsService = Depends(get_stats_service)
) -> Dict[str, dict]:
    """
    Get launch frequency statistics.

    Returns launch counts grouped by month and year.
    """
    try:
        return await stats_service.get_launch_frequency()
    except SpaceXAPIError as e:
        raise HTTPException(status_code=503, detail=f"SpaceX API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/overall", response_model=dict)
async def get_overall_statistics(
    stats_service: StatsService = Depends(get_stats_service)
) -> dict:
    """
    Get overall launch statistics summary.

    Returns total counts and overall success rate.
    """
    try:
        return await stats_service.get_overall_statistics()
    except SpaceXAPIError as e:
        raise HTTPException(status_code=503, detail=f"SpaceX API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
