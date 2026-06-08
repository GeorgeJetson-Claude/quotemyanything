#!/usr/bin/env python3
"""
matcher.py — score a candidate deal against every Pace Morby buy box.

A "deal" is a plain dict (one row from a CSV / API feed). The matcher returns,
for each buy box, a verdict:

    fit   : "yes" | "maybe" | "no"
    score : 0-100 (higher = stronger fit)
    reasons   : list of human-readable PASS reasons
    failures  : list of human-readable disqualifiers (empty when fit != "no")

Design: HARD rules disqualify (fit="no"). When all hard rules pass we score the
SOFT preferences and the deal economics. A "maybe" means it qualifies but is
missing data we'd want before submitting (e.g. no ARV, no photos).
"""

from buy_boxes import all_buy_boxes


def _norm(value):
    return (value or "").strip().lower()


def _to_float(value):
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def _to_bool(value):
    """Loose truthiness for CSV strings. Returns None if unknown/blank."""
    s = _norm(value)
    if s in ("", "unknown", "n/a", "na"):
        return None
    return s in ("1", "true", "yes", "y", "t")


def _financing_tokens(deal):
    """All financing-ish signals on the deal, lowercased."""
    tokens = set()
    for key in ("financing", "financing_type", "financing_terms"):
        val = _norm(deal.get(key))
        if val:
            for piece in val.replace("/", " ").replace(",", " ").split():
                tokens.add(piece)
    return tokens


def _max_offer(deal, box):
    """Max purchase price this buy box would accept, or None if N/A."""
    pct = box.get("max_arv_pct")
    if not pct:
        return None
    arv = _to_float(deal.get("arv")) or _to_float(deal.get("zillow_value"))
    if arv is None:
        return None
    return arv * pct


def score_deal_against_box(deal, box_id, box):
    reasons = []
    failures = []

    asset = _norm(deal.get("asset_type"))
    state = (deal.get("state") or "").strip().upper()
    county = _norm(deal.get("county")).replace(" county", "")

    # ---- HARD: asset type ----
    if box["asset_types"] and asset not in box["asset_types"]:
        failures.append(f"asset_type '{asset or '?'}' not in buy box")

    # ---- HARD: geography ----
    geo = box["geo"]
    if geo.get("states_required"):
        if state not in {s.upper() for s in geo["states"]}:
            failures.append(f"state '{state or '?'}' outside {sorted(geo['states'])}")
    if geo.get("counties_required"):
        if county not in geo["counties"]:
            failures.append(f"county '{county or '?'}' not in {sorted(geo['counties'])}")

    # ---- HARD: financing ----
    tokens = _financing_tokens(deal)
    if box["financing"]:
        if tokens and not (tokens & box["financing"]):
            failures.append(f"financing {sorted(tokens)} not creative/cash as required")

    # ---- HARD: existing operation only (RV/campground) ----
    if box.get("require_existing"):
        is_land = _to_bool(deal.get("is_land"))
        existing = _to_bool(deal.get("existing_operation"))
        if is_land is True or existing is False:
            failures.append("development land / not an existing operation")

    # ---- HARD: flood zone ----
    if box.get("exclude_flood_zone"):
        if _to_bool(deal.get("flood_zone")) is True:
            failures.append("located in a flood zone")

    # ---- HARD: economics (50% of ARV rule) ----
    max_offer = _max_offer(deal, box)
    price = _to_float(deal.get("purchase_price")) or _to_float(deal.get("list_price"))
    if box.get("max_arv_pct") and max_offer is not None and price is not None:
        if price > max_offer:
            failures.append(
                f"price ${price:,.0f} > {int(box['max_arv_pct']*100)}% ARV "
                f"(max ${max_offer:,.0f})"
            )

    if failures:
        return {"fit": "no", "score": 0, "reasons": reasons, "failures": failures}

    # ---------- Passed all hard rules: score it ----------
    score = 60  # baseline for a qualifying deal
    reasons.append(f"asset/geo/financing match {box['name']}")

    # Economics bonus: deeper than the cap is better.
    if box.get("max_arv_pct") and max_offer is not None and price is not None:
        margin = (max_offer - price) / max_offer  # 0 at the cap, ->1 the cheaper
        score += int(min(margin, 0.5) * 60)  # up to +30
        reasons.append(
            f"price ${price:,.0f} is {int((1-price/max_offer)*100)}% under the cap"
        )

    # Soft geo preference.
    pref_states = {s.upper() for s in box.get("preferred", {}).get("states", set())}
    if pref_states and state in pref_states:
        score += 10
        reasons.append(f"in preferred state {state}")

    # Data completeness — needed before we can submit to Pace.
    incomplete = []
    if not (deal.get("photos") or deal.get("photos_url")):
        incomplete.append("photos")
    # ARV only matters for boxes priced off ARV (the SFH 50% rule).
    if box.get("max_arv_pct") and not (
        _to_float(deal.get("arv")) or _to_float(deal.get("zillow_value"))
    ):
        incomplete.append("ARV/value")
    if price is None:
        incomplete.append("purchase_price")
    if not _financing_tokens(deal):
        incomplete.append("financing_terms")

    score = max(0, min(score, 100))

    if incomplete:
        return {
            "fit": "maybe",
            "score": score,
            "reasons": reasons,
            "failures": [],
            "missing": incomplete,
        }
    return {"fit": "yes", "score": score, "reasons": reasons, "failures": []}


def match_deal(deal):
    """Score a deal against ALL buy boxes. Returns dict keyed by buy box id."""
    results = {}
    for box_id, box in all_buy_boxes().items():
        results[box_id] = score_deal_against_box(deal, box_id, box)
    return results


def best_match(deal):
    """Return (box_id, result) of the strongest qualifying buy box, or None."""
    ranked = []
    for box_id, res in match_deal(deal).items():
        if res["fit"] in ("yes", "maybe"):
            # yes beats maybe at equal score
            tier = 1 if res["fit"] == "yes" else 0
            ranked.append((tier, res["score"], box_id, res))
    if not ranked:
        return None
    ranked.sort(reverse=True)
    _, _, box_id, res = ranked[0]
    return box_id, res
