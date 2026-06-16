#!/usr/bin/env python3
"""
dealfinder.py — the end-to-end system: ingest -> enrich -> match -> underwrite
-> rank -> draft -> track.

Commands:
    scan      score candidates, underwrite, draft emails, record to pipeline
    pipeline  list tracked deals + running P&L
    status    move a deal through its lifecycle and record a fee
    boxes     print the buy box definitions

Examples:
    python3 dealfinder.py scan --input sample_deals.csv --write-drafts
    python3 dealfinder.py scan --input sample_deals.csv --min-score 65 --flood
    python3 dealfinder.py pipeline
    python3 dealfinder.py status "1423 W Roosevelt" --set submitted
    python3 dealfinder.py status 1a2b3c --set accepted --fee 12000

Nothing is ever auto-sent. Qualifying deals are drafted to outbox/ for you to
review and submit via each buy box's "Email Us" form.
"""

import argparse
import json
import os
import re

import sources
import pipeline
import arv as arv_mod
from matcher import match_deal, best_match
from email_builder import build_email
from underwriting import underwrite, summary_line
from assignment import wholesale_math, assignment_agreement
from buy_boxes import all_buy_boxes

OUTBOX = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outbox")


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", (text or "deal").lower()).strip("-")[:50]


def cmd_scan(args):
    deals = sources.load(args.source, path=args.input, query=args.query)

    if args.comps or args.arv_from_fcv:
        comps = arv_mod.load_comps_csv(args.comps) if args.comps else {}
        arv_mod.enrich_arv(deals, comps_by_key=comps,
                           use_fcv_fallback=args.arv_from_fcv)

    if args.flood:
        sources.enrich_flood_zone(deals)

    rows = []
    for deal in deals:
        results = match_deal(deal)
        bm = best_match(deal)
        uw = underwrite(deal) if bm else None
        rows.append({"deal": deal, "results": results, "best": bm, "uw": uw})

    def sort_key(r):
        if not r["best"]:
            return (-1, 0)
        _, res = r["best"]
        return (1 if res["fit"] == "yes" else 0, res["score"])

    rows.sort(key=sort_key, reverse=True)
    qualifying = [r for r in rows
                  if r["best"] and r["best"][1]["score"] >= args.min_score]

    # Record qualifying deals to the pipeline ledger (dedup + tracking).
    ledger = pipeline.load()
    recorded_new = 0
    for r in qualifying:
        box_id, res = r["best"]
        _, is_new = pipeline.upsert(ledger, r["deal"], box_id, res, r["uw"])
        recorded_new += 1 if is_new else 0

    if args.json:
        print(json.dumps([{
            "id": pipeline.deal_id(r["deal"]),
            "address": r["deal"].get("address"),
            "best_box": r["best"][0] if r["best"] else None,
            "fit": r["best"][1]["fit"] if r["best"] else "no",
            "score": r["best"][1]["score"] if r["best"] else 0,
            "reasons": r["best"][1]["reasons"] if r["best"] else [],
            "underwriting": r["uw"] or {},
        } for r in rows], indent=2))
        pipeline.save(ledger)
        return

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
            for box_id, res in r["results"].items():
                if res["failures"]:
                    print(f"            {boxes[box_id]['name']}: {res['failures'][0]}")
            continue

        box_id, res = r["best"]
        if res["score"] < args.min_score:
            continue

        did = pipeline.deal_id(deal)
        mark = "✓ FIT  " if res["fit"] == "yes" else "~ MAYBE"
        print(f"\n{mark}  [{res['score']:>3}]  {addr}   ({did})")
        print(f"            → {boxes[box_id]['name']}")
        for reason in res["reasons"]:
            print(f"              • {reason}")
        if deal.get("arv_confidence"):
            print(f"              ~ ARV ${arv_mod._f(deal['arv']):,.0f} "
                  f"[{deal['arv_confidence']} confidence — {deal.get('arv_basis','')}]")
        if r["uw"]:
            uw_line = summary_line(r["uw"])
            if uw_line:
                print(f"              $ {uw_line}")
        if res.get("missing"):
            print(f"              ! need before sending: {', '.join(res['missing'])}")

        if args.write_drafts:
            email = build_email(deal, box_id, res, underwriting=r["uw"])
            fname = f"{res['score']:03d}_{box_id}_{_slug(addr)}.txt"
            os.makedirs(OUTBOX, exist_ok=True)
            with open(os.path.join(OUTBOX, fname), "w") as f:
                f.write("To: (buy box 'Email Us' form on pacemorby.com)\n")
                f.write(f"Subject: {email['subject']}\n\n")
                f.write(email["body"] + "\n")
            drafted += 1
            # advance status new -> drafted (won't downgrade a later stage)
            entry = ledger[did]
            if entry["status"] == "new":
                pipeline.set_status(ledger, did, "drafted")
            print(f"              ✎ draft: outbox/{fname}")

            # Wholesale paperwork for viable SFH assignment deals.
            if args.paperwork and r["uw"] and r["uw"].get("model") == "fix_flip":
                pw = (f"{wholesale_math(deal, r['uw'])}\n\n\n"
                      f"{assignment_agreement(deal, uw=r['uw'])}\n")
                pwname = f"{res['score']:03d}_{_slug(addr)}_ASSIGNMENT.txt"
                with open(os.path.join(OUTBOX, pwname), "w") as f:
                    f.write(pw)
                print(f"              ✎ paperwork: outbox/{pwname}")

    pipeline.save(ledger)

    print("\n" + "-" * 72)
    print(f"Qualifying deals (score >= {args.min_score}): "
          f"{len(qualifying)} / {len(deals)}   (new to pipeline: {recorded_new})")
    if args.write_drafts:
        print(f"Drafts written to outbox/: {drafted}  (review, then submit manually)")
    print("-" * 72)


def cmd_pipeline(args):
    ledger = pipeline.load()
    if not ledger:
        print("Pipeline empty. Run: dealfinder.py scan --input <file>")
        return
    entries = sorted(ledger.values(),
                     key=lambda e: (e.get("status"), -e.get("score", 0)))
    print(f"{'ID':<13}{'STATUS':<11}{'SCORE':<6}{'FEE':<10}ADDRESS")
    print("-" * 72)
    for e in entries:
        fee = f"${e.get('fee', 0):,.0f}" if e.get("fee") else "-"
        print(f"{e['id']:<13}{e.get('status','new'):<11}"
              f"{e.get('score',0):<6}{fee:<10}{e.get('address','')[:34]}")
    p = pipeline.pnl(ledger)
    print("-" * 72)
    print(f"Deals: {p['total_deals']}  |  " +
          "  ".join(f"{k}:{v}" for k, v in p['by_status'].items() if v))
    print(f"Realized revenue (accepted): ${p['realized_revenue']:,.0f}   "
          f"Pipeline fee potential: ${p['pipeline_fee_potential']:,.0f}")


def cmd_status(args):
    ledger = pipeline.load()
    try:
        did = pipeline.find(ledger, args.deal)
    except KeyError as e:
        print(f"Error: {e}")
        return
    entry = pipeline.set_status(ledger, did, args.set, fee=args.fee, note=args.note)
    pipeline.save(ledger)
    fee = f" fee=${entry.get('fee',0):,.0f}" if entry.get("fee") else ""
    print(f"{did}  {entry.get('address','')}  ->  {entry['status']}{fee}")


def cmd_boxes(args):
    for box_id, box in all_buy_boxes().items():
        print(f"\n[{box_id}] {box['name']}")
        print(f"  {box['blurb']}")


def main():
    ap = argparse.ArgumentParser(description="Pace Morby buy box deal system.")
    sub = ap.add_subparsers(dest="cmd")

    s = sub.add_parser("scan", help="score, underwrite, draft, and track deals")
    s.add_argument("--input", help="path to deals CSV (source=csv)")
    s.add_argument("--source", default="csv",
                   help="ingestion adapter: csv | maricopa | maricopa_fixture")
    s.add_argument("--query", help="free-text search (source=maricopa)")
    s.add_argument("--min-score", type=int, default=0)
    s.add_argument("--write-drafts", action="store_true")
    s.add_argument("--paperwork", action="store_true",
                   help="also write wholesale math + assignment agreement (SFH)")
    s.add_argument("--comps", help="comps CSV to estimate ARV from sold sales")
    s.add_argument("--arv-from-fcv", action="store_true", dest="arv_from_fcv",
                   help="fallback: rough ARV from assessor value (low confidence)")
    s.add_argument("--flood", action="store_true",
                   help="auto-fill flood_zone from FEMA for deals with lat/lon")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_scan)

    p = sub.add_parser("pipeline", help="list tracked deals + P&L")
    p.set_defaults(func=cmd_pipeline)

    st = sub.add_parser("status", help="advance a deal's status / record a fee")
    st.add_argument("deal", help="deal id prefix or address substring")
    st.add_argument("--set", required=True, choices=pipeline.STATUSES)
    st.add_argument("--fee", type=float, default=None)
    st.add_argument("--note", default=None)
    st.set_defaults(func=cmd_status)

    b = sub.add_parser("boxes", help="print buy box definitions")
    b.set_defaults(func=cmd_boxes)

    args = ap.parse_args()
    if not getattr(args, "cmd", None):
        ap.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
