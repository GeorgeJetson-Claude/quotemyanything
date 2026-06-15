#!/usr/bin/env python3
"""
underwriting.py — put a number on each deal.

The matcher decides IF a deal fits a buy box. Underwriting decides WHAT IT'S
WORTH, so you submit deals with real numbers instead of "looks good." Two
models, picked by asset type:

  Fix & flip (SFH):  MAO, rehab estimate, projected profit, ROI, spread vs the
                     50%-of-ARV cap.
  Income property (MHP / RV / campground / resort):  NOI, cap rate, and a
                     value estimate from NOI / target cap.

Everything degrades gracefully: if a field is missing we say so rather than
inventing it. Stdlib only.
"""

# --- Fix & flip assumptions (override per-deal via CSV columns) ---
DEFAULT_HOLDING_PCT = 0.08   # holding + closing + selling, as % of ARV
DEFAULT_FLIP_FORMULA = 0.70  # classic 70% rule, for comparison vs Pace's 50%
DEFAULT_WHOLESALE_FEE = 10000

# Rehab $/sqft by level when no explicit rehab_cost is given.
REHAB_PSF = {"light": 20, "medium": 35, "heavy": 55, "gut": 80}

# --- Income property assumptions ---
DEFAULT_EXPENSE_RATIO = 0.40  # opex as % of gross when expenses not given
DEFAULT_TARGET_CAP = 0.08     # cap rate used to back into a value estimate

SFH_TYPES = {"sfh", "single_family", "single-family", "house"}
INCOME_TYPES = {"mhp", "mobile_home_park", "rv_park", "rv-park", "campground",
                "resort", "rv_resort", "multifamily"}


def _f(deal, *keys):
    """First parseable float among keys, else None."""
    for k in keys:
        v = deal.get(k)
        if v in (None, ""):
            continue
        try:
            return float(str(v).replace("$", "").replace(",", "").replace("%", "").strip())
        except (ValueError, TypeError):
            continue
    return None


def estimate_rehab(deal):
    """Explicit rehab_cost wins; else sqft x level $/sqft; else None."""
    explicit = _f(deal, "rehab_cost", "rehab")
    if explicit is not None:
        return explicit, "provided"
    sqft = _f(deal, "sqft", "square_feet")
    level = (deal.get("rehab_level") or "").strip().lower()
    if sqft and level in REHAB_PSF:
        return sqft * REHAB_PSF[level], f"{level} @ ${REHAB_PSF[level]}/sqft x {int(sqft)}sqft"
    if sqft:
        return sqft * REHAB_PSF["medium"], f"assumed medium @ ${REHAB_PSF['medium']}/sqft"
    return None, "no rehab data"


def underwrite_flip(deal):
    arv = _f(deal, "arv", "zillow_value")
    price = _f(deal, "purchase_price", "list_price")
    rehab, rehab_basis = estimate_rehab(deal)
    out = {"model": "fix_flip", "arv": arv, "purchase_price": price,
           "rehab": rehab, "rehab_basis": rehab_basis, "notes": []}

    if arv is None:
        out["notes"].append("no ARV — cannot underwrite")
        return out

    holding = arv * DEFAULT_HOLDING_PCT
    out["holding_selling_costs"] = round(holding)
    out["pace_max_offer"] = round(arv * 0.50)           # the buy box rule
    if rehab is not None:
        fee = DEFAULT_WHOLESALE_FEE
        out["mao_70_rule"] = round(arv * DEFAULT_FLIP_FORMULA - rehab - fee)

    if price is not None and rehab is not None:
        profit = arv - price - rehab - holding
        invested = price + rehab
        out["projected_profit"] = round(profit)
        out["roi_pct"] = round(profit / invested * 100, 1) if invested else None
        out["spread_vs_pace_cap"] = round(out["pace_max_offer"] - price)
        if profit < 0:
            out["notes"].append("projected loss at this price")
    else:
        out["notes"].append("need purchase_price + rehab for profit/ROI")
    return out


def underwrite_income(deal):
    """NOI / cap rate for parks. Works from explicit NOI, or builds gross from
    pads x rent x occupancy and applies an expense ratio."""
    price = _f(deal, "purchase_price", "list_price")
    out = {"model": "income", "purchase_price": price, "notes": []}

    noi = _f(deal, "noi")
    if noi is None:
        gross = _f(deal, "gross_income", "annual_income")
        if gross is None:
            pads = _f(deal, "pads", "sites", "units")
            rent = _f(deal, "lot_rent", "monthly_rent", "site_rent")
            occ = _f(deal, "occupancy")
            occ = (occ / 100 if occ and occ > 1 else occ) if occ is not None else 0.90
            if pads and rent:
                gross = pads * rent * 12 * occ
                out["gross_basis"] = f"{int(pads)} pads x ${rent:.0f}/mo x {occ:.0%} occ"
        if gross is not None:
            exp_ratio = _f(deal, "expense_ratio")
            exp_ratio = (exp_ratio / 100 if exp_ratio and exp_ratio > 1
                         else exp_ratio) if exp_ratio is not None else DEFAULT_EXPENSE_RATIO
            noi = gross * (1 - exp_ratio)
            out["gross_income"] = round(gross)
            out["expense_ratio"] = exp_ratio

    if noi is None:
        out["notes"].append("need NOI, or pads+lot_rent, to value this park")
        return out

    out["noi"] = round(noi)
    if price:
        out["cap_rate_pct"] = round(noi / price * 100, 2)
    out["value_at_target_cap"] = round(noi / DEFAULT_TARGET_CAP)
    if price:
        out["value_vs_price"] = round(out["value_at_target_cap"] - price)
        if out["value_at_target_cap"] < price:
            out["notes"].append(
                f"priced above an {DEFAULT_TARGET_CAP:.0%}-cap value")
    return out


def underwrite(deal):
    """Pick the right model for the asset type."""
    asset = (deal.get("asset_type") or "").strip().lower()
    if asset in SFH_TYPES:
        return underwrite_flip(deal)
    if asset in INCOME_TYPES:
        return underwrite_income(deal)
    return {"model": "none", "notes": [f"no underwriting model for '{asset}'"]}


def summary_line(uw):
    """One-line human summary for the report."""
    m = uw.get("model")
    if m == "fix_flip":
        bits = []
        if uw.get("projected_profit") is not None:
            bits.append(f"profit ~${uw['projected_profit']:,}")
        if uw.get("roi_pct") is not None:
            bits.append(f"ROI {uw['roi_pct']}%")
        if uw.get("rehab") is not None:
            bits.append(f"rehab ~${int(uw['rehab']):,}")
        if uw.get("spread_vs_pace_cap") is not None:
            bits.append(f"${uw['spread_vs_pace_cap']:,} under 50% cap")
        return " | ".join(bits) or "needs ARV/price/rehab"
    if m == "income":
        bits = []
        if uw.get("noi") is not None:
            bits.append(f"NOI ~${uw['noi']:,}")
        if uw.get("cap_rate_pct") is not None:
            bits.append(f"cap {uw['cap_rate_pct']}%")
        if uw.get("value_vs_price") is not None:
            sign = "+" if uw["value_vs_price"] >= 0 else ""
            bits.append(f"value vs price {sign}${uw['value_vs_price']:,}")
        return " | ".join(bits) or "needs NOI or pads+rent"
    return uw.get("notes", [""])[0]
