"""Overpass API client — network only, no DB access (reconciliation lives in services/bar.py)."""

from __future__ import annotations

import re

import httpx

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Overpass blocks generic client user agents (406) — OSM etiquette is to identify yourself
_HEADERS = {"User-Agent": "MousseMate/0.1 (beer-tracking app; OSM bar referential sync script)"}

# TODO(scale): widening scope is a one-line change here — top candidates: cafe
# (many Parisian café-bars are tagged amenity=cafe), nightclub, biergarten.
SYNC_AMENITIES: tuple[str, ...] = ("bar", "pub", "restaurant")

# TODO(scale): area is resolved by city name; for France-wide coverage, switch to
# per-département queries or Geofabrik extracts instead of one giant Overpass call.
_QUERY_TEMPLATE = """
[out:json][timeout:180];
area["name"="{city}"]["admin_level"="8"]["boundary"="administrative"]->.searcharea;
nwr["amenity"~"^({amenities})$"]["name"](area.searcharea);
out center tags;
"""


def fetch_bars(city: str = "Paris") -> list[dict]:
    """Fetch all named in-scope venues inside the city's admin boundary.

    Returns dicts whose keys match Bar columns, ready for reconciliation.
    """
    query = _QUERY_TEMPLATE.format(city=city, amenities="|".join(SYNC_AMENITIES))
    # HTTP timeout slightly above the query's server-side [timeout:180]
    resp = httpx.post(OVERPASS_URL, data={"data": query}, headers=_HEADERS, timeout=200.0)
    resp.raise_for_status()
    elements = resp.json()["elements"]
    return [bar for el in elements if (bar := _normalize(el, city)) is not None]


def _normalize(element: dict, city: str) -> dict | None:
    tags = element.get("tags", {})
    name = tags.get("name")
    # nodes carry lat/lon directly; ways/relations carry a computed centroid under "center"
    coords = element if element["type"] == "node" else element.get("center", {})
    lat, lon = coords.get("lat"), coords.get("lon")
    if not name or lat is None or lon is None:
        return None
    return {
        "osm_id": element["id"],
        "osm_type": element["type"],
        "name": name[:255],  # OSM tags are free-form — clamp to column sizes
        "amenity": tags["amenity"],
        "latitude": lat,
        "longitude": lon,
        "address": _build_address(tags),
        "postcode": _extract_postcode(tags),
        "city": city,
    }


def _extract_postcode(tags: dict) -> str | None:
    # addr:postcode is free-form (multi-values like "75001;75002" occur) — keep the first 5-digit code
    match = re.search(r"\d{5}", tags.get("addr:postcode", ""))
    return match.group() if match else None


def _build_address(tags: dict) -> str | None:
    address = " ".join(p for p in (tags.get("addr:housenumber"), tags.get("addr:street")) if p)
    return address[:500] or None
