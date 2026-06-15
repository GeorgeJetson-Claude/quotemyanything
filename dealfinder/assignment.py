#!/usr/bin/env python3
"""
assignment.py — generate the wholesale exit paperwork.

Your revenue model is the **assignment**: you put the property under contract
with the seller, then assign that contract to Pace (the end buyer) for an
assignment fee. This module produces two things per deal:

  1. A wholesale math sheet — what to tie the property up at so there's room for
     your fee under Pace's 50%-of-ARV ceiling.
  2. An Assignment of Real Estate Purchase & Sale Contract — a fill-in-the-blank
     template for assigning your contract to Pace's entity for the fee.

IMPORTANT: this is a template, not legal advice. Assignment rules and required
disclosures vary by state (Arizona among them). Have a local real estate
attorney or title company review before you use it on a live deal.
"""

from underwriting import underwrite, TARGET_ASSIGNMENT_FEE


def _money(v):
    try:
        return f"${float(v):,.0f}"
    except (ValueError, TypeError):
        return "$________"


def wholesale_math(deal, uw=None):
    """Plain-language breakdown of the assignment economics for one deal."""
    uw = uw or underwrite(deal)
    if uw.get("model") != "fix_flip":
        return ("Assignment math sheet applies to SFH fix & flip deals; "
                f"this deal is '{uw.get('model')}'.")
    arv = uw.get("arv")
    lines = [
        "WHOLESALE ASSIGNMENT MATH",
        "=" * 40,
        f"ARV (from your comps)............ {_money(arv)}",
        f"Pace's ceiling (50% of ARV)...... {_money(uw.get('pace_max_offer'))}",
        f"Target assignment fee............ {_money(TARGET_ASSIGNMENT_FEE)}",
        f"=> Tie property up at (max)....... {_money(uw.get('max_contract_price'))}",
    ]
    if uw.get("assignment_fee") is not None:
        viable = "VIABLE" if uw.get("wholesale_viable") else "TOO THIN"
        lines += [
            "-" * 40,
            f"Your contract price.............. {_money(uw.get('purchase_price'))}",
            f"Your assignment fee.............. {_money(uw.get('assignment_fee'))}  [{viable}]",
        ]
    return "\n".join(lines)


def assignment_agreement(deal, fee=None, uw=None):
    """Fill-in-the-blank Assignment of Contract for assigning to Pace's entity."""
    uw = uw or underwrite(deal)
    fee = fee if fee is not None else uw.get("assignment_fee")
    address = deal.get("address", "____________________")
    apn = deal.get("apn", "____________")

    return "\n".join([
        "ASSIGNMENT OF REAL ESTATE PURCHASE & SALE CONTRACT",
        "",
        "(TEMPLATE — have a licensed attorney / title company review before use)",
        "",
        f"This Assignment is made on ____________, 20____, between:",
        "",
        "  ASSIGNOR (you):  ______________________________________",
        "  ASSIGNEE (end buyer): _________________________________",
        "      [Pace's acquiring entity, per the buy box submission]",
        "",
        "1. UNDERLYING CONTRACT. Assignor is the buyer under that certain Real",
        f"   Estate Purchase & Sale Contract dated ____________ for the property",
        f"   located at:",
        f"       {address}",
        f"       APN: {apn}",
        f"       (the \"Property\"), with the seller named therein (the \"Contract\").",
        "",
        "2. ASSIGNMENT. Assignor assigns and transfers all of Assignor's right,",
        "   title, and interest in the Contract to Assignee.",
        "",
        f"3. ASSIGNMENT FEE. In consideration, Assignee shall pay Assignor a",
        f"   non-refundable assignment fee of {_money(fee)}, due at closing through",
        "   escrow, as a separate line item on the closing statement.",
        "",
        "4. ASSUMPTION. Assignee assumes and agrees to perform all of Assignor's",
        "   obligations under the Contract arising on or after the date hereof.",
        "",
        "5. CLOSING. Assignee shall close per the terms and timeline of the",
        "   Contract. Earnest money: ____________________.",
        "",
        "6. REPRESENTATIONS. Assignor represents the Contract is valid, in full",
        "   force, and not in default, and Assignor has authority to assign it.",
        "",
        "7. GOVERNING LAW. This Assignment is governed by the laws of the State",
        "   of Arizona.",
        "",
        "ASSIGNOR: ______________________   Date: __________",
        "ASSIGNEE: ______________________   Date: __________",
        "",
        "Disclosure: Assignor holds an equitable interest in the Property by",
        "virtue of the Contract and is assigning that interest; Assignor is not",
        "the title owner. Marketing/assignment of contracts may be regulated in",
        "your state — confirm compliance before proceeding.",
    ])
