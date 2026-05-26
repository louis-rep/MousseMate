from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator


class EntryBase(BaseModel):
    name: str | None = None
    type: str
    volume: float
    drink_datetime: datetime
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
    pass


class EntryUpdate(BaseModel):
    name: str | None = None
    type: str | None = None
    volume: float | None = None
    drink_datetime: datetime | None = None
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
    id: int
    username: str | None = None
    like_count: int = 0
    liked_by_me: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VenueRead(BaseModel):
    date: date
    bar: str | None
    entries: tuple[EntryRead, ...]


class DailyLiters(BaseModel):
    date: date
    liters: float


class TypeDailyLiters(BaseModel):
    type: str
    daily: tuple[DailyLiters, ...]


class TypeLiters(BaseModel):
    type: str
    liters: float


class BarTypeLiters(BaseModel):
    bar: str | None
    values: tuple[TypeLiters, ...]


class StatsSummary(BaseModel):
    weekly_count: int
    monthly_count: int
    top_types: list[str]
    top_names: list[str]
    total_liters: float
    daily_liters: tuple[TypeDailyLiters, ...]
    liters_by_type: tuple[BarTypeLiters, ...]
