from __future__ import annotations

from datetime import UTC, date, datetime

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator


def _to_naive_utc(v: datetime) -> datetime:
    """Datetimes are stored timezone-unaware in UTC; aware inputs are converted, naive ones trusted as UTC."""
    if v.tzinfo is not None:
        return v.astimezone(UTC).replace(tzinfo=None)
    return v


class EntryBase(BaseModel):
    name: str | None = None
    type: str
    volume: float
    drink_datetime: datetime
    bar_id: int
    rating: float | None = None
    notes: str | None = None

    @field_validator("drink_datetime")
    @classmethod
    def normalize_drink_datetime(cls, v: datetime) -> datetime:
        return _to_naive_utc(v)

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
    bar_id: int | None = None
    rating: float | None = None
    notes: str | None = None

    @field_validator("drink_datetime")
    @classmethod
    def normalize_drink_datetime(cls, v: datetime | None) -> datetime | None:
        return None if v is None else _to_naive_utc(v)

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

    # JSON only: tag the naive-UTC values with +00:00 so browsers convert to local
    # time; python-mode dumps (the pandas pipeline) keep them naive.
    @field_serializer("drink_datetime", "created_at", "updated_at", when_used="json")
    def serialize_as_utc(self, v: datetime) -> datetime:
        return v.replace(tzinfo=UTC)


class VenueRead(BaseModel):
    date: date
    bar: str  # bar name, joined from the bar referential
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
    bar: str  # bar name, joined from the bar referential
    values: tuple[TypeLiters, ...]


class StatsSummary(BaseModel):
    weekly_count: int
    monthly_count: int
    top_types: list[str]
    top_names: list[str]
    total_liters: float
    daily_liters: tuple[TypeDailyLiters, ...]
    liters_by_type: tuple[BarTypeLiters, ...]
