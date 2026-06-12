"""Point-in-polygon lookup: Paris coordinates -> arrondissement postcode.

Pure geometry — no DB, no network. Polygons come from Paris Open Data (ODbL),
the same asset the frontend choropleth uses (frontend/public/).
TODO(scale): France-wide coverage means commune polygons instead — same lookup, bigger asset.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_GEOJSON_PATH = Path(__file__).resolve().parent.parent / "data" / "paris-arrondissements.geojson"

# one entry per arrondissement: ("75011", rings) — rings in GeoJSON (lng, lat) order
_Ring = tuple[tuple[float, float], ...]


@lru_cache(maxsize=1)
def _load_areas() -> tuple[tuple[str, tuple[_Ring, ...]], ...]:
    data = json.loads(_GEOJSON_PATH.read_text())
    areas = []
    for feature in data["features"]:
        postcode = f"750{feature['properties']['c_ar']:02d}"
        geometry = feature["geometry"]
        polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
        rings = tuple(tuple((x, y) for x, y in ring) for polygon in polygons for ring in polygon)
        areas.append((postcode, rings))
    return tuple(areas)


def _in_rings(lng: float, lat: float, rings: tuple[_Ring, ...]) -> bool:
    # even-odd ray casting over all rings: crossing a hole's boundary flips the parity back out
    inside = False
    for ring in rings:
        for i in range(len(ring)):
            x1, y1 = ring[i - 1]
            x2, y2 = ring[i]
            if (y1 > lat) != (y2 > lat) and lng < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
                inside = not inside
    return inside


def postcode_for_point(latitude: float, longitude: float) -> str | None:
    """The arrondissement postcode containing the point, or None outside Paris."""
    for postcode, rings in _load_areas():
        if _in_rings(longitude, latitude, rings):
            return postcode
    return None
