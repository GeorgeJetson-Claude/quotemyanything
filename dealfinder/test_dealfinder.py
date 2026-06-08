#!/usr/bin/env python3
"""Smoke tests for the deal matcher. Run: python3 test_dealfinder.py"""

from matcher import match_deal, best_match


def check(name, cond):
    print(("PASS" if cond else "FAIL") + f"  {name}")
    assert cond, name


# SFH in Maricopa at 50% of ARV -> fits SFH box
sfh = {"address": "x", "county": "Maricopa", "state": "AZ",
       "asset_type": "single_family", "purchase_price": "135000",
       "arv": "310000", "financing_terms": "cash", "photos_url": "u"}
r = match_deal(sfh)["sfh_fix_flip"]
check("SFH under 50% ARV fits", r["fit"] == "yes")

# Same SFH but over the cap -> disqualified
over = dict(sfh, purchase_price="200000")
check("SFH over 50% ARV fails", match_deal(over)["sfh_fix_flip"]["fit"] == "no")

# SFH in wrong county -> disqualified
pima = dict(sfh, county="Pima")
check("SFH wrong county fails", match_deal(pima)["sfh_fix_flip"]["fit"] == "no")

# MHP creative finance, no ARV needed -> fits
mhp = {"address": "x", "county": "Travis", "state": "TX", "asset_type": "mhp",
       "purchase_price": "1200000", "financing_terms": "seller finance",
       "existing_operation": "Yes", "photos_url": "u"}
check("MHP creative fits", match_deal(mhp)["mobile_home_park"]["fit"] == "yes")

# MHP cash-only -> fails creative-only rule
mhp_cash = dict(mhp, financing_terms="cash")
check("MHP cash-only fails", match_deal(mhp_cash)["mobile_home_park"]["fit"] == "no")

# RV park in flood zone -> fails
rv_flood = {"address": "x", "state": "LA", "asset_type": "rv_park",
            "purchase_price": "900000", "financing_terms": "creative",
            "flood_zone": "Yes", "existing_operation": "Yes"}
check("RV flood zone fails", match_deal(rv_flood)["rv_park"]["fit"] == "no")

# RV raw land -> fails (must be existing)
rv_land = {"address": "x", "state": "AZ", "asset_type": "rv_park",
           "purchase_price": "500000", "financing_terms": "creative",
           "is_land": "Yes", "existing_operation": "No"}
check("RV raw land fails", match_deal(rv_land)["rv_park"]["fit"] == "no")

# Existing RV park, creative, no flood -> fits + is best match
rv_ok = {"address": "x", "state": "CA", "asset_type": "rv_park",
         "purchase_price": "3100000", "financing_terms": "creative",
         "flood_zone": "No", "existing_operation": "Yes", "photos_url": "u"}
bm = best_match(rv_ok)
check("RV existing fits as best match", bm and bm[0] == "rv_park")

print("\nAll smoke tests passed.")
