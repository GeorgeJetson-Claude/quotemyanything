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
