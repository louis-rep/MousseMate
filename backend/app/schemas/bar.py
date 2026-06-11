from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BarRead(BaseModel):
    id: int
    osm_id: int
    osm_type: str
    name: str
    amenity: str
    latitude: float
    longitude: float
    address: str | None
    postcode: str | None
    city: str
    is_closed: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
