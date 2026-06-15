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

# ---- underwriting ----
from underwriting import underwrite

flip = underwrite({"asset_type": "single_family", "arv": "310000",
                   "purchase_price": "135000", "sqft": "1450",
                   "rehab_level": "medium"})
check("flip computes positive profit", flip["projected_profit"] > 0)
check("flip computes ROI", flip["roi_pct"] is not None)
check("flip pace_max_offer = 50% ARV", flip["pace_max_offer"] == 155000)

park = underwrite({"asset_type": "rv_park", "purchase_price": "3100000",
                   "noi": "290000"})
check("park computes cap rate", park["cap_rate_pct"] is not None)
check("park cap rate ~9.4%", abs(park["cap_rate_pct"] - 9.35) < 0.2)

mhp_uw = underwrite({"asset_type": "mhp", "purchase_price": "1200000",
                     "pads": "42", "lot_rent": "375", "occupancy": "0.90"})
check("mhp builds NOI from pads x rent", mhp_uw["noi"] > 0)

# ---- pipeline ----
import pipeline as pl

led = {}
d = {"address": "1423 W Roosevelt St, Phoenix, AZ"}
entry, is_new = pl.upsert(led, d, "sfh_fix_flip", {"fit": "yes", "score": 67})
check("pipeline insert is new", is_new and entry["status"] == "new")
_, is_new2 = pl.upsert(led, d, "sfh_fix_flip", {"fit": "yes", "score": 70})
check("pipeline dedup on same address", not is_new2 and len(led) == 1)
did = pl.find(led, "1423")
pl.set_status(led, did, "accepted", fee=12000)
check("pipeline records fee", led[did]["fee"] == 12000)
check("pipeline pnl realizes revenue", pl.pnl(led)["realized_revenue"] == 12000)

print("\nAll smoke tests passed.")
