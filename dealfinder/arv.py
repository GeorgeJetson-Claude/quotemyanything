#!/usr/bin/env python3
"""
arv.py — estimate After-Repair Value, the one number the pipeline can't fake.

The 50%-of-ARV rule is only as good as the ARV. This estimates it transparently
from comparable sales (no black box, no paid API required):

  Comps method (preferred): median $/sqft of nearby retail/renovated sales,
  outliers trimmed, applied to the subject's square footage. Confidence scales
  with how many comps you have and how tight they cluster.

  Assessor fallback: county Full Cash Value x a market factor. Clearly labeled
  LOW confidence — FCV is a tax figure, use it only to triage, never to submit.

Comps come from a CSV you control (your MLS pull, a data export, or hand-built),
keyed to each subject by APN or address. Stdlib only.
"""

import csv
import statistics

DEFAULT_FCV_MARKET_FACTOR = 1.15  # rough FCV -> market; AZ FCV often lags market
MIN_COMPS_GOOD = 3
TIGHT_SPREAD = 0.25  # (p75-p25)/median below this = tight cluster


def _f(v):
    try:
        return float(str(v).replace("$", "").replace(",", "").strip())
    except (ValueError, TypeError):
        return None


def estimate_from_comps(subject_sqft, comps):
    """comps: list of dicts with sold_price + sqft. Returns an estimate dict or
    None if there isn't enough to work with."""
    sqft = _f(subject_sqft)
    if not sqft:
        return None
    ppsf = []
    for c in comps:
        price, csqft = _f(c.get("sold_price")), _f(c.get("sqft"))
        if price and csqft and csqft > 0:
            ppsf.append(price / csqft)
    if not ppsf:
        return None

    ppsf.sort()
    n = len(ppsf)  # how many comps you actually have -> drives confidence
    # Spread measured on the full set, before any trimming.
    if n >= 2:
        q = statistics.quantiles(ppsf, n=4)
        spread = (q[2] - q[0]) / statistics.median(ppsf) if ppsf else 1
    else:
        spread = 1
    # Trim one outlier per end only when it still leaves >=3 for the median.
    trimmed = ppsf[1:-1] if n >= 5 else ppsf
    median_ppsf = statistics.median(trimmed)
    arv = round(median_ppsf * sqft / 1000) * 1000
    if n >= MIN_COMPS_GOOD and spread <= TIGHT_SPREAD:
        conf = "high"
    elif n >= 2:
        conf = "medium"
    else:
        conf = "low"

    return {
        "arv": arv,
        "method": "comps",
        "confidence": conf,
        "comp_count": n,
        "median_ppsf": round(median_ppsf, 2),
        "basis": f"{n} comps, median ${round(median_ppsf)}/sqft x {int(sqft)}sqft",
    }


def estimate_from_fcv(fcv, factor=DEFAULT_FCV_MARKET_FACTOR):
    fcv = _f(fcv)
    if not fcv:
        return None
    return {
        "arv": round(fcv * factor / 1000) * 1000,
        "method": "fcv_factor",
        "confidence": "low",
        "basis": f"assessor FCV ${int(fcv):,} x {factor} (triage only — verify with comps)",
    }


def load_comps_csv(path):
    """Group comps by subject key. CSV columns:
       subject_apn (or subject_address), comp_address, sold_price, sqft, sold_date
    Returns {key: [comp, ...]} keyed by both apn and lowercased address."""
    by_key = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            key = (row.get("subject_apn") or row.get("subject_address") or "").strip()
            if not key:
                continue
            by_key.setdefault(key.lower(), []).append(row)
    return by_key


def enrich_arv(deals, comps_by_key=None, use_fcv_fallback=False,
               overwrite=False):
    """Fill arv (+ arv_confidence, arv_basis) on deals that lack it. Prefers
    comps matched by APN or address; optional FCV fallback. Mutates + returns."""
    comps_by_key = comps_by_key or {}
    for d in deals:
        if d.get("arv") and not overwrite:
            continue
        est = None
        # Match comps by APN first, then address.
        for key in (str(d.get("apn") or "").lower(),
                    str(d.get("address") or "").lower()):
            if key and key in comps_by_key:
                est = estimate_from_comps(d.get("sqft"), comps_by_key[key])
                if est:
                    break
        if not est and use_fcv_fallback:
            est = estimate_from_fcv(d.get("assessor_value"))
        if est:
            d["arv"] = est["arv"]
            d["arv_confidence"] = est["confidence"]
            d["arv_basis"] = est["basis"]
    return deals
