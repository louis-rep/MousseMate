from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, field_serializer

MapScope = Literal["me", "mates"]


class VenueDrinker(BaseModel):
    username: str
    entry_count: int
    liters: float


class VenueMapPoint(BaseModel):
    bar_id: int
    name: str
    latitude: float
    longitude: float
    address: str | None
    postcode: str | None
    is_closed: bool
    entry_count: int
    total_liters: float
    last_visit: datetime
    drinkers: tuple[VenueDrinker, ...]  # sorted by liters desc

    # JSON only: tag the naive-UTC value with +00:00 so browsers convert to local time
    @field_serializer("last_visit", when_used="json")
    def serialize_as_utc(self, v: datetime) -> datetime:
        return v.replace(tzinfo=UTC)


class VenueMapResponse(BaseModel):
    scope: MapScope
    venues: tuple[VenueMapPoint, ...]
