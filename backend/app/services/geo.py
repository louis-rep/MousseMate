from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from app.models.bar import Bar
from app.models.entry import Entry
from app.models.user import User
from app.schemas.geo import MapScope, VenueDrinker, VenueMapPoint, VenueMapResponse
from app.services import follow as follow_service


def get_venue_map(db: Session, current_user_id: int, scope: MapScope) -> VenueMapResponse:
    if scope == "mates":
        mates = follow_service.list_following(db, current_user_id)
        user_ids = [current_user_id, *(m.id for m in mates)]
    else:
        user_ids = [current_user_id]

    rows = (
        db.query(
            Entry.bar_id,
            Entry.volume,
            Entry.drink_datetime,
            User.username,
            Bar.name,
            Bar.latitude,
            Bar.longitude,
            Bar.address,
            Bar.postcode,
            Bar.is_closed,
        )
        .join(User, Entry.user_id == User.id)
        .join(Bar, Entry.bar_id == Bar.id)
        # manual rows (the "Unknown bar" placeholder) have no real location — never pin them
        .filter(Entry.user_id.in_(user_ids), Bar.osm_type != "manual")
        .all()
    )
    if not rows:
        return VenueMapResponse(scope=scope, venues=())

    entries_df = pd.DataFrame(
        rows,
        columns=[
            "bar_id",
            "volume",
            "drink_datetime",
            "username",
            "name",
            "latitude",
            "longitude",
            "address",
            "postcode",
            "is_closed",
        ],
    )
    entries_df["liters"] = entries_df.volume / 1000

    drinkers_df = (
        entries_df.groupby(["bar_id", "username"])
        .agg(entry_count=("liters", "size"), liters=("liters", "sum"))
        .reset_index()
        .sort_values("liters", ascending=False)
    )
    drinkers_by_bar = {
        bar_id: tuple(
            VenueDrinker(username=r["username"], entry_count=r["entry_count"], liters=round(r["liters"], 3))
            for r in group.to_dict("records")
        )
        for bar_id, group in drinkers_df.groupby("bar_id", sort=False)
    }

    venues_df = (
        entries_df.groupby("bar_id")
        .agg(
            name=("name", "first"),
            latitude=("latitude", "first"),
            longitude=("longitude", "first"),
            address=("address", "first"),
            postcode=("postcode", "first"),
            is_closed=("is_closed", "first"),
            entry_count=("liters", "size"),
            total_liters=("liters", "sum"),
            last_visit=("drink_datetime", "max"),
        )
        .reset_index()
    )
    venues_df = venues_df.astype(object).where(pd.notna(venues_df), other=None)

    venues = [
        VenueMapPoint(
            **{**r, "total_liters": round(r["total_liters"], 2)},
            drinkers=drinkers_by_bar[r["bar_id"]],
        )
        for r in venues_df.to_dict("records")
    ]
    return VenueMapResponse(scope=scope, venues=tuple(venues))
