#!/usr/bin/env python3
"""
email_builder.py — draft a buy-box submission email in Pace's required format.

Every Pace buy box card ends with the same REMINDER: include the property
address, photos, purchase price, financing terms, and a brief explanation of
why the deal fits the buy box. This module produces exactly that — ready to
paste into the "Email Us" form. It does NOT send anything.
"""

from buy_boxes import all_buy_boxes


def _fmt_money(value):
    try:
        return f"${float(str(value).replace('$','').replace(',','')):,.0f}"
    except (ValueError, TypeError):
        return str(value) if value else "TBD"


def _underwriting_lines(uw):
    """Optional numbers block built from an underwriting dict."""
    if not uw:
        return []
    lines = []
    m = uw.get("model")
    if m == "fix_flip":
        if uw.get("rehab") is not None:
            lines.append(f"  Est. Rehab       : {_fmt_money(uw['rehab'])}"
                         f" ({uw.get('rehab_basis','')})")
        if uw.get("projected_profit") is not None:
            roi = f" ({uw['roi_pct']}% ROI)" if uw.get("roi_pct") is not None else ""
            lines.append(f"  Projected Profit : {_fmt_money(uw['projected_profit'])}{roi}")
    elif m == "income":
        if uw.get("noi") is not None:
            lines.append(f"  Est. NOI         : {_fmt_money(uw['noi'])}")
        if uw.get("cap_rate_pct") is not None:
            lines.append(f"  Cap Rate         : {uw['cap_rate_pct']}%")
    return lines


def build_email(deal, box_id, result, underwriting=None):
    box = all_buy_boxes()[box_id]

    address = deal.get("address") or "[ADDRESS NEEDED]"
    price = _fmt_money(deal.get("purchase_price") or deal.get("list_price"))
    arv = _fmt_money(deal.get("arv") or deal.get("zillow_value"))
    financing = (deal.get("financing_terms") or deal.get("financing")
                 or deal.get("financing_type") or "[FINANCING TERMS NEEDED]")
    photos = deal.get("photos_url") or deal.get("photos") or "[ATTACH/LINK PHOTOS]"

    # Brief explanation built from the matcher's PASS reasons.
    why = "; ".join(result.get("reasons", [])) or box["blurb"]

    subject = f"Deal Submission — {box['name']} — {address}"

    body_lines = [
        f"Hi Pace's team,",
        "",
        f"Submitting the following for the {box['name']}:",
        "",
        f"  Property Address : {address}",
        f"  Purchase Price   : {price}",
        f"  ARV / Value      : {arv}",
        f"  Financing Terms  : {financing}",
        f"  Photos           : {photos}",
    ]

    # Buy-box-specific facts worth calling out.
    extras = []
    if deal.get("asset_type"):
        extras.append(f"  Asset Type       : {deal.get('asset_type')}")
    loc = ", ".join(p for p in [deal.get("county"), deal.get("state")] if p)
    if loc:
        extras.append(f"  Location         : {loc}")
    if box.get("max_arv_pct") and (deal.get("arv") or deal.get("zillow_value")):
        extras.append(
            f"  Rule Check       : offered at/under {int(box['max_arv_pct']*100)}% of ARV"
        )
    if box.get("exclude_flood_zone"):
        extras.append(f"  Flood Zone       : {deal.get('flood_zone') or 'No'}")
    if box.get("require_existing"):
        extras.append(f"  Existing Op      : {deal.get('existing_operation') or 'Yes'}")
    body_lines.extend(extras)
    body_lines.extend(_underwriting_lines(underwriting))

    body_lines += [
        "",
        f"Why it fits: {why}.",
        "",
    ]

    notes = deal.get("notes")
    if notes:
        body_lines += [f"Additional info: {notes}", ""]

    if result.get("missing"):
        body_lines += [
            f"NOTE (internal): before sending, fill in: {', '.join(result['missing'])}.",
            "",
        ]

    body_lines += ["Thank you,", "[YOUR NAME / CONTACT]"]

    return {"subject": subject, "body": "\n".join(body_lines)}
