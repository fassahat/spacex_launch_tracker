"""Pydantic models for SpaceX launches."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class LaunchCore(BaseModel):
    """Represents a launch core/booster."""

    core: Optional[str] = Field(None, description="Core ID")
    flight: Optional[int] = Field(None, description="Flight number for this core")
    landing_success: Optional[bool] = Field(None, description="Landing success status")
    reused: Optional[bool] = Field(None, description="Whether core was reused")


class LaunchFailure(BaseModel):
    """Represents launch failure details."""

    time: Optional[int] = Field(None, description="Time of failure in seconds")
    altitude: Optional[float] = Field(None, description="Altitude at failure")
    reason: Optional[str] = Field(None, description="Failure reason")


class Launch(BaseModel):
    """Represents a SpaceX launch."""

    id: str = Field(..., description="Launch unique identifier")
    name: str = Field(..., description="Launch mission name")
    date_utc: Optional[datetime] = Field(None, description="Launch date in UTC")
    date_local: Optional[str] = Field(None, description="Launch date in local time")
    success: Optional[bool] = Field(None, description="Launch success status")
    rocket: Optional[str] = Field(None, description="Rocket ID")
    launchpad: Optional[str] = Field(None, description="Launchpad ID")
    flight_number: Optional[int] = Field(None, description="Flight number")
    details: Optional[str] = Field(None, description="Launch details")
    upcoming: Optional[bool] = Field(None, description="Whether launch is upcoming")
    cores: Optional[list[LaunchCore]] = Field(None, description="Launch cores/boosters")
    failures: Optional[list[LaunchFailure]] = Field(None, description="Failure details")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": "5eb87cd9ffd86e000604b32a",
                "name": "FalconSat",
                "date_utc": "2006-03-24T22:30:00.000Z",
                "success": False,
                "rocket": "5e9d0d95eda69973a809d1ec",
                "launchpad": "5e9e4502f509094188566f88",
                "flight_number": 1
            }
        }


class LaunchFilter(BaseModel):
    """Query parameters for filtering launches."""

    date_from: Optional[datetime] = Field(None, description="Start date for filtering")
    date_to: Optional[datetime] = Field(None, description="End date for filtering")
    rocket_name: Optional[str] = Field(None, description="Filter by rocket name")
    success: Optional[bool] = Field(None, description="Filter by success status")
    launchpad_name: Optional[str] = Field(None, description="Filter by launchpad name")
    limit: Optional[int] = Field(100, description="Maximum results to return", ge=1, le=1000)
    offset: Optional[int] = Field(0, description="Number of results to skip", ge=0)
