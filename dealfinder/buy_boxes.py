#!/usr/bin/env python3
"""
buy_boxes.py — Pace Morby buy box definitions.

Encoded directly from the public buy box cards on pacemorby.com. Each buy box
is a set of HARD rules (disqualify if violated) and SOFT preferences (boost the
score but don't disqualify). The matcher in matcher.py consumes these.

Keep this file as the single source of truth. If Pace updates a buy box, edit
the dict here and every downstream score/email updates automatically.
"""

# Submission contact shown on every card ("Email Us" button).
# We do NOT auto-send. Drafts are written to outbox/ for manual send.
SUBMISSION_NOTE = (
    "Please include the property address, photos, purchase price, financing "
    "terms, and a brief explanation of why you believe the deal fits Pace's "
    "buy box. Any additional information is also appreciated."
)

# Two-letter states Pace treats as "creative finance only" markets where he
# already operates mobile home parks.
MHP_PREFERRED_STATES = {"AZ", "TX", "GA"}

BUY_BOXES = {
    "sfh_fix_flip": {
        "name": "SFH Fix & Flip Buy Box",
        "asset_types": {"sfh", "single_family", "single-family", "house"},
        # Hard geo: Maricopa County, AZ ONLY.
        "geo": {
            "states": {"AZ"},
            "counties": {"maricopa"},
            "states_required": True,
            "counties_required": True,
        },
        # Cash OR creative both acceptable here.
        "financing": {"cash", "creative", "seller", "subto", "sub2", "subject-to"},
        # Core formula: max offer = 50% of ARV (Zillow value / 2).
        "max_arv_pct": 0.50,
        "volume_per_year": (10, 15),
        "preferred": {},
        "blurb": "Single-family fix & flip in Maricopa County, AZ at 50% of ARV or better.",
    },
    "private_lending": {
        "name": "Private Lending Buy Box",
        # Capital box, not an acquisition box: a deal that NEEDS funding for a
        # flip or refinance. Matched when financing_need is set.
        "asset_types": {"sfh", "single_family", "single-family", "house",
                        "multifamily", "commercial", "mhp", "rv_park"},
        "geo": {"states": set(), "counties": set(),
                "states_required": False, "counties_required": False},
        "financing": {"private", "private_lending", "hard_money", "refi",
                     "refinance", "flip"},
        "max_arv_pct": None,
        "volume_per_year": None,
        "lending_purposes": {"flip", "refinance", "refi"},
        "preferred": {},
        "blurb": "Private lending for flips and refinances.",
    },
    "mobile_home_park": {
        "name": "Mobile Home Park Buy Box",
        "asset_types": {"mhp", "mobile_home_park", "mobile-home-park",
                        "mobilehomepark"},
        # Nationwide.
        "geo": {"states": set(), "counties": set(),
                "states_required": False, "counties_required": False},
        # Creative finance ONLY.
        "financing": {"creative", "seller", "subto", "sub2", "subject-to",
                     "seller_finance", "seller-finance"},
        "max_arv_pct": None,
        "volume_per_year": None,
        # Prefers AZ/TX/GA but open nationwide if the deal makes sense.
        "preferred": {"states": MHP_PREFERRED_STATES},
        "blurb": "Mobile home parks nationwide (prefers AZ/TX/GA), creative finance only.",
    },
    "rv_park": {
        "name": "RV Parks, Campgrounds & Resorts Buy Box",
        "asset_types": {"rv_park", "rv-park", "rvpark", "campground",
                        "resort", "rv_resort"},
        # Nationwide; CA and NY explicitly okay.
        "geo": {"states": set(), "counties": set(),
                "states_required": False, "counties_required": False},
        # Creative finance ONLY.
        "financing": {"creative", "seller", "subto", "sub2", "subject-to",
                     "seller_finance", "seller-finance"},
        "max_arv_pct": None,
        "volume_per_year": (15, 20),
        # Existing parks only — NO raw land for development. NO flood zones.
        "require_existing": True,
        "exclude_flood_zone": True,
        "preferred": {"states": {"CA", "NY"}},
        "blurb": ("Existing RV parks / campgrounds / resorts nationwide, creative "
                  "finance only, no flood zones, no development land."),
    },
}


def all_buy_boxes():
    """Return the buy box dict (id -> definition)."""
    return BUY_BOXES


def get(buy_box_id):
    return BUY_BOXES[buy_box_id]
