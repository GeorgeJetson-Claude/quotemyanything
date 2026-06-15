#!/usr/bin/env python3
"""
sources.py — pluggable deal ingestion adapters.

The matcher only cares about a normalized deal dict. Where deals come from is
swappable. Ship with a CSV adapter; add API adapters later WITHOUT touching the
matching/email code.

A normalized deal dict uses these keys (all optional except address):
    address, county, state, asset_type, purchase_price (or list_price),
    arv (or zillow_value), financing_terms (or financing/financing_type),
    flood_zone, existing_operation, is_land, photos_url (or photos), notes

Adding an automated source later (the "automate it" part):
    Write a function that returns a list[dict] in the shape above and register
    it in SOURCES. Examples that respect each provider's Terms of Service:
      - County assessor / GIS open-data exports (public records, usually CSV/API)
      - Your MLS feed via a licensed RETS/RESO Web API account
      - A paid data provider API (e.g. lists you already license)
      - FEMA flood map API to auto-populate the flood_zone field
    Do NOT scrape sites that forbid it (e.g. Zillow's ToS). Use licensed feeds.
"""

import csv
import json
import urllib.parse
import urllib.request

# FEMA National Flood Hazard Layer (NFHL) — free, public, no key required.
# We query the flood hazard zones layer by lat/lon and report whether the point
# falls in a Special Flood Hazard Area (SFHA). This is the same data the RV buy
# box's "NO FLOOD ZONES" rule cares about.
FEMA_NFHL_URL = (
    "https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query"
)
# Zones starting with A or V are Special Flood Hazard Areas (high risk).
SFHA_PREFIXES = ("A", "V")


def fema_flood_zone(lat, lon, timeout=8):
    """Return ("Yes"/"No"/None, zone_code). None means lookup unavailable
    (offline / API error) — caller should fall back to existing data."""
    params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": "4326",
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "FLD_ZONE,SFHA_TF",
        "returnGeometry": "false",
        "f": "json",
    }
    url = FEMA_NFHL_URL + "?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
    except Exception:
        return None, None
    features = data.get("features") or []
    if not features:
        return "No", "X"  # not in any mapped SFHA polygon -> outside flood zone
    attrs = features[0].get("attributes", {})
    zone = attrs.get("FLD_ZONE") or ""
    sfha = attrs.get("SFHA_TF")
    in_sfha = (sfha == "T") or zone.startswith(SFHA_PREFIXES)
    return ("Yes" if in_sfha else "No"), zone


def enrich_flood_zone(deals, only_missing=True):
    """Fill the flood_zone field on deals that have lat/lon. Mutates and returns
    the list. Skips deals already carrying flood_zone unless only_missing=False.
    Never raises on network failure — it just leaves the field as-is."""
    for d in deals:
        if only_missing and d.get("flood_zone"):
            continue
        lat, lon = d.get("lat") or d.get("latitude"), d.get("lon") or d.get("longitude")
        if not (lat and lon):
            continue
        try:
            zone_yn, zone_code = fema_flood_zone(float(lat), float(lon))
        except (ValueError, TypeError):
            continue
        if zone_yn is not None:
            d["flood_zone"] = zone_yn
            d["flood_zone_code"] = zone_code
    return deals


def from_csv(path):
    """Load deals from a CSV whose headers match the normalized keys."""
    deals = []
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            deals.append({k.strip(): (v.strip() if isinstance(v, str) else v)
                          for k, v in row.items()})
    return deals


# Registry of named sources. CLI uses --source <name> --path <file>.
SOURCES = {
    "csv": from_csv,
}


def load(source_name, **kwargs):
    if source_name not in SOURCES:
        raise ValueError(f"unknown source '{source_name}'; have {list(SOURCES)}")
    return SOURCES[source_name](**kwargs)
