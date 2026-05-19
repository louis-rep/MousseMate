from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class EntryBase(BaseModel):
    brewery: str
    style: str | None = None
    volume: float | None = None
    datetime: datetime
    bar: str | None = None
    rating: float | None = None
    notes: str | None = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: float | None) -> float | None:
        if v is not None and not (0.0 <= v <= 5.0):
            raise ValueError("rating must be between 0.0 and 5.0")
        return v


class EntryCreate(EntryBase):
    """Schema for creating a new entry (POST)."""

    pass


class EntryUpdate(BaseModel):
    """Schema for partially updating an entry (PATCH) — all fields optional."""

    brewery: str | None = None
    style: str | None = None
    volume: float | None = None
    datetime: datetime | None = None
    bar: str | None = None
    rating: float | None = None
    notes: str | None = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: float | None) -> float | None:
        if v is not None and not (0.0 <= v <= 5.0):
            raise ValueError("rating must be between 0.0 and 5.0")
        return v


class EntryRead(EntryBase):
    """Schema returned from the API (includes DB-generated fields)."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatsSummary(BaseModel):
    """Aggregated stats for all entries."""

    weekly_count: int
    monthly_count: int
    top_styles: list[str]
    top_breweries: list[str]
    current_streak_days: int
