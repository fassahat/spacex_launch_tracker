"""Pydantic models for SpaceX rockets."""

from typing import Optional
from pydantic import BaseModel, Field


class Rocket(BaseModel):
    """Represents a SpaceX rocket."""

    id: str = Field(..., description="Rocket unique identifier")
    name: str = Field(..., description="Rocket name")
    type: Optional[str] = Field(None, description="Rocket type")
    active: bool = Field(..., description="Whether rocket is active")
    stages: Optional[int] = Field(None, description="Number of stages")
    boosters: Optional[int] = Field(None, description="Number of boosters")
    cost_per_launch: Optional[int] = Field(None, description="Launch cost in USD")
    success_rate_pct: Optional[float] = Field(None, description="Success rate percentage")
    first_flight: Optional[str] = Field(None, description="Date of first flight")
    country: Optional[str] = Field(None, description="Country of origin")
    company: Optional[str] = Field(None, description="Manufacturing company")
    wikipedia: Optional[str] = Field(None, description="Wikipedia URL")
    description: Optional[str] = Field(None, description="Rocket description")

    class Config:
        """Pydantic config."""
        json_schema_extra = {
            "example": {
                "id": "5e9d0d95eda69973a809d1ec",
                "name": "Falcon 9",
                "type": "rocket",
                "active": True,
                "stages": 2,
                "cost_per_launch": 50000000,
                "success_rate_pct": 98.0,
                "country": "United States",
                "company": "SpaceX"
            }
        }
