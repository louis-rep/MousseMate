from __future__ import annotations

import pandas as pd
from sqlalchemy.orm import Session

from app.models.bar import Bar
from app.models.entry import Entry
from app.models.user import User
from app.schemas.geo import (
    ArrondissementMapResponse,
    ArrondissementStat,
    MapScope,
    VenueDrinker,
    VenueMapPoint,
    VenueMapResponse,
)
from app.services import follow as follow_service


def _visible_user_ids(db: Session, current_user_id: int, scope: MapScope) -> list[int]:
    if scope == "mates":
        mates = follow_service.list_following(db, current_user_id)
        return [current_user_id, *(m.id for m in mates)]
    return [current_user_id]


def _postcode_to_arrondissement(postcode: str | None) -> int | None:
    """75001-75020 -> 1-20; 75116 is Passy, part of the 16th. Anything else is unmappable."""
    if postcode == "75116":
        return 16
    if postcode is None or len(postcode) != 5 or not postcode.startswith("750") or not postcode.isdigit():
        return None
    arrondissement = int(postcode[3:])
    return arrondissement if 1 <= arrondissement <= 20 else None


def get_venue_map(db: Session, current_user_id: int, scope: MapScope) -> VenueMapResponse:
    user_ids = _visible_user_ids(db, current_user_id, scope)

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


def get_arrondissement_map(db: Session, current_user_id: int, scope: MapScope) -> ArrondissementMapResponse:
    user_ids = _visible_user_ids(db, current_user_id, scope)

    rows = (
        db.query(Entry.volume, Bar.postcode).join(Bar, Entry.bar_id == Bar.id).filter(Entry.user_id.in_(user_ids)).all()
    )
    if not rows:
        return ArrondissementMapResponse(scope=scope, arrondissements=())

    entries_df = pd.DataFrame(rows, columns=["volume", "postcode"])
    # na_action: null postcodes arrive as NaN floats, keep them out of the str-typed helper
    entries_df["arrondissement"] = entries_df.postcode.map(_postcode_to_arrondissement, na_action="ignore")
    entries_df = entries_df[entries_df.arrondissement.notna()]
    if entries_df.empty:
        return ArrondissementMapResponse(scope=scope, arrondissements=())

    stats_df = (
        entries_df.groupby("arrondissement")
        .agg(entry_count=("volume", "size"), total_liters=("volume", "sum"))
        .reset_index()
    )
    stats = tuple(
        ArrondissementStat(
            arrondissement=int(r["arrondissement"]),
            entry_count=r["entry_count"],
            total_liters=round(r["total_liters"] / 1000, 2),
        )
        for r in stats_df.to_dict("records")
    )
    return ArrondissementMapResponse(scope=scope, arrondissements=stats)
