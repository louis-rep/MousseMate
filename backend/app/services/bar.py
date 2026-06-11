from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.bar import Bar
from app.schemas.bar import BarRead

# Fields overwritten from OSM on every sync
_SYNCED_FIELDS = ("name", "amenity", "latitude", "longitude", "address", "postcode", "city")


def search_bars(db: Session, q: str, city: str = "Paris", limit: int = 20) -> tuple[BarRead, ...]:
    bars = (
        db.query(Bar)
        .filter(Bar.city == city, Bar.is_closed.is_(False), Bar.name.ilike(f"%{q}%"))
        .order_by(Bar.name)
        .limit(limit)
        .all()
    )
    return tuple(BarRead.model_validate(b) for b in bars)


def sync_bars(db: Session, osm_elements: list[dict], city: str = "Paris", dry_run: bool = False) -> dict[str, int]:
    """Reconcile DB state against an OSM fetch.

    - in OSM, not in DB  -> insert
    - in both            -> update synced fields if changed; reopen if it was closed
    - in DB, not in OSM  -> is_closed = True (never delete — entries may reference the bar)
    """
    osm_by_key = {(el["osm_type"], el["osm_id"]): el for el in osm_elements}
    # OSM ids are globally unique, so match across all cities — a boundary element
    # picked up by two city syncs must update, not violate uq_bar_osm_type_osm_id.
    # TODO(scale): revisit loading the full table once the referential goes France-wide.
    db_by_key = {(b.osm_type, b.osm_id): b for b in db.query(Bar).all()}

    counts = {"inserted": 0, "updated": 0, "closed": 0, "reopened": 0, "unchanged": 0}

    for key, element in osm_by_key.items():
        bar = db_by_key.get(key)
        if bar is None:
            db.add(Bar(**element))
            counts["inserted"] += 1
            continue
        changed = False
        for field in _SYNCED_FIELDS:
            if getattr(bar, field) != element[field]:
                setattr(bar, field, element[field])
                changed = True
        if bar.is_closed:
            bar.is_closed = False
            counts["reopened"] += 1
        elif changed:
            counts["updated"] += 1
        else:
            counts["unchanged"] += 1

    # Closing is city-scoped: a Paris sync says nothing about Lyon bars
    for key, bar in db_by_key.items():
        if bar.city != city or key in osm_by_key:
            continue
        if bar.is_closed:
            counts["unchanged"] += 1
        else:
            bar.is_closed = True
            counts["closed"] += 1

    if dry_run:
        db.rollback()
    else:
        db.commit()
    return counts
