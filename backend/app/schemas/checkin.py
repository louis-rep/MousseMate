from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class CheckInBase(BaseModel):
    beer_name: str
    brewery: Optional[str] = None
    style: Optional[str] = None
    rating: Optional[float] = None
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    venue: Optional[str] = None
    city: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 5.0):
            raise ValueError("rating must be between 0.0 and 5.0")
        return v


class CheckInCreate(CheckInBase):
    """Schema for creating a new check-in (POST)."""
    pass


class CheckInUpdate(BaseModel):
    """Schema for partially updating a check-in (PATCH) — all fields optional."""
    beer_name: Optional[str] = None
    brewery: Optional[str] = None
    style: Optional[str] = None
    rating: Optional[float] = None
    notes: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    venue: Optional[str] = None
    city: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 5.0):
            raise ValueError("rating must be between 0.0 and 5.0")
        return v


class CheckInRead(CheckInBase):
    """Schema returned from the API (includes DB-generated fields)."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatsSummary(BaseModel):
    """Aggregated stats for the current user's check-ins."""
    weekly_count: int
    monthly_count: int
    top_styles: list[str]
    top_breweries: list[str]
    current_streak_days: int
