from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class CheckInBase(BaseModel):
    beer_name: str
    brewery: str | None = None
    style: str | None = None
    rating: float | None = None
    notes: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    venue: str | None = None
    city: str | None = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: float | None) -> float | None:
        if v is not None and not (0.0 <= v <= 5.0):
            raise ValueError("rating must be between 0.0 and 5.0")
        return v


class CheckInCreate(CheckInBase):
    """Schema for creating a new check-in (POST)."""

    pass


class CheckInUpdate(BaseModel):
    """Schema for partially updating a check-in (PATCH) — all fields optional."""

    beer_name: str | None = None
    brewery: str | None = None
    style: str | None = None
    rating: float | None = None
    notes: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    venue: str | None = None
    city: str | None = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: float | None) -> float | None:
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
