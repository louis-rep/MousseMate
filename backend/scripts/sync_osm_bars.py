"""Sync the bar referential from OpenStreetMap (Overpass API).

Usage (from backend/):
    uv run python scripts/sync_osm_bars.py [--dry-run]

TODO(scale): accept --city/--country args and loop over cities for France-wide sync.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.session import SessionLocal  # noqa: E402
from app.models.bar import Bar  # noqa: E402
from app.services import bar as bar_service  # noqa: E402
from app.services import osm  # noqa: E402

CITY = "Paris"

# Abort threshold: protects against a partial Overpass response mass-closing bars
MIN_OSM_RATIO = 0.7


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync bars from OpenStreetMap into the local DB")
    parser.add_argument("--dry-run", action="store_true", help="compute and print the diff without writing")
    args = parser.parse_args()

    print(f"Fetching {CITY} venues from Overpass ({', '.join(osm.SYNC_AMENITIES)})...")
    elements = osm.fetch_bars(city=CITY)
    print(f"  {len(elements)} named venues fetched")

    db = SessionLocal()
    try:
        open_count = db.query(Bar).filter(Bar.city == CITY, Bar.is_closed.is_(False)).count()
        if open_count and len(elements) < MIN_OSM_RATIO * open_count:
            print(
                f"ABORT: OSM returned {len(elements)} venues but DB has {open_count} open bars "
                f"(below the {MIN_OSM_RATIO:.0%} guard). Likely a partial Overpass response — nothing written."
            )
            return 1

        counts = bar_service.sync_bars(db, elements, city=CITY, dry_run=args.dry_run)
    finally:
        db.close()

    label = "DRY RUN (nothing written)" if args.dry_run else "Done"
    print(f"{label}: " + ", ".join(f"{k}={v}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
