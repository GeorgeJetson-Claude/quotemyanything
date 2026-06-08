#!/usr/bin/env python3
"""
dealfinder.py — match candidate properties to Pace Morby's buy boxes, rank the
hits, and draft a submission email for each one.

Usage:
    python3 dealfinder.py --input sample_deals.csv
    python3 dealfinder.py --input sample_deals.csv --min-score 70
    python3 dealfinder.py --input sample_deals.csv --write-drafts

Output:
    - Console report ranked by score (best deals first).
    - With --write-drafts: one .txt submission email per qualifying deal into
      outbox/, ready to paste into the buy box "Email Us" form. NOTHING is sent.

This is a sourcing/qualification tool. You review the drafts and submit. It
makes money by surfacing only deals that actually fit a buy box, formatted the
way Pace's team asks, so submissions convert instead of getting ignored.
"""

import argparse
import json
import os
import re

import sources
from matcher import match_deal, best_match
from email_builder import build_email
from buy_boxes import all_buy_boxes

OUTBOX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outbox")


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "deal").lower()).strip("-")[:50]


def run(input_path, source="csv", min_score=0, write_drafts=False, as_json=False):
    deals = sources.load(source, path=input_path)

    rows = []
    for deal in deals:
        results = match_deal(deal)
        bm = best_match(deal)
        rows.append({"deal": deal, "results": results, "best": bm})

    # Rank: qualifying deals by best score desc; non-matches last.
    def sort_key(r):
        if not r["best"]:
            return (-1, 0)
        _, res = r["best"]
        tier = 1 if res["fit"] == "yes" else 0
        return (tier, res["score"])

    rows.sort(key=sort_key, reverse=True)

    qualifying = [r for r in rows if r["best"] and r["best"][1]["score"] >= min_score]

    if as_json:
        print(json.dumps([{
            "address": r["deal"].get("address"),
            "best_box": r["best"][0] if r["best"] else None,
            "fit": r["best"][1]["fit"] if r["best"] else "no",
            "score": r["best"][1]["score"] if r["best"] else 0,
            "reasons": r["best"][1]["reasons"] if r["best"] else [],
        } for r in rows], indent=2))
        return rows

    boxes = all_buy_boxes()
    print("=" * 72)
    print(f"PACE MORBY DEAL FINDER — {len(deals)} candidates scanned")
    print("=" * 72)

    drafted = 0
    for r in rows:
        deal = r["deal"]
        addr = deal.get("address", "(no address)")
        if not r["best"]:
            print(f"\n✗ NO FIT   {addr}")
            # show why the closest box failed (first failure of each box)
            for box_id, res in r["results"].items():
                if res["failures"]:
                    print(f"            {boxes[box_id]['name']}: {res['failures'][0]}")
            continue

        box_id, res = r["best"]
        if res["score"] < min_score:
            continue

        mark = "✓ FIT  " if res["fit"] == "yes" else "~ MAYBE"
        print(f"\n{mark}  [{res['score']:>3}]  {addr}")
        print(f"            → {boxes[box_id]['name']}")
        for reason in res["reasons"]:
            print(f"              • {reason}")
        if res.get("missing"):
            print(f"              ! need before sending: {', '.join(res['missing'])}")

        if write_drafts:
            email = build_email(deal, box_id, res)
            fname = f"{res['score']:03d}_{box_id}_{_slug(addr)}.txt"
            path = os.path.join(OUTBOX, fname)
            os.makedirs(OUTBOX, exist_ok=True)
            with open(path, "w") as f:
                f.write(f"To: (buy box 'Email Us' form on pacemorby.com)\n")
                f.write(f"Subject: {email['subject']}\n\n")
                f.write(email["body"] + "\n")
            drafted += 1
            print(f"              ✎ draft: outbox/{fname}")

    print("\n" + "-" * 72)
    print(f"Qualifying deals (score >= {min_score}): {len(qualifying)} / {len(deals)}")
    if write_drafts:
        print(f"Drafts written to outbox/: {drafted}  (review, then submit manually)")
    print("-" * 72)
    return rows


def main():
    ap = argparse.ArgumentParser(description="Match deals to Pace Morby buy boxes.")
    ap.add_argument("--input", required=True, help="path to deals CSV")
    ap.add_argument("--source", default="csv", help="ingestion adapter (default: csv)")
    ap.add_argument("--min-score", type=int, default=0, help="only show deals >= score")
    ap.add_argument("--write-drafts", action="store_true",
                    help="write submission email drafts to outbox/")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args()

    run(args.input, source=args.source, min_score=args.min_score,
        write_drafts=args.write_drafts, as_json=args.json)


if __name__ == "__main__":
    main()
