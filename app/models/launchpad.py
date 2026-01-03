"""Pydantic models for SpaceX launchpads."""

from typing import Optional
from pydantic import BaseModel, Field


class Launchpad(BaseModel):
    """Represents a SpaceX launchpad."""

    id: str = Field(..., description="Launchpad unique identifier")
    name: str = Field(..., description="Launchpad name")
    full_name: Optional[str] = Field(None, description="Full launchpad name")
    locality: Optional[str] = Field(None, description="City/locality")
    region: Optional[str] = Field(None, description="State/region")
    latitude: Optional[float] = Field(None, description="Latitude coordinate")
    longitude: Optional[float] = Field(None, description="Longitude coordinate")
    launch_attempts: Optional[int] = Field(None, description="Total launch attempts")
    launch_successes: Optional[int] = Field(None, description="Successful launches")
    rockets: Optional[list[str]] = Field(None, description="Compatible rocket IDs")
    status: Optional[str] = Field(None, description="Operational status")
    details: Optional[str] = Field(None, description="Additional details")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": "5e9e4502f509094188566f88",
                "name": "VAFB SLC 4E",
                "full_name": "Vandenberg Air Force Base Space Launch Complex 4E",
                "locality": "Vandenberg Air Force Base",
                "region": "California",
                "status": "active",
                "launch_attempts": 15,
                "launch_successes": 15
            }
        }
