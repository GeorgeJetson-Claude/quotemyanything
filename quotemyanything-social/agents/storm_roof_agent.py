#!/usr/bin/env python3
"""
QMA Daily Lead Agent — one command to run the whole organic lead workflow.

What it does each run (free, stdlib only, no auto-posting):
  1. Scans Reddit for live buying-intent posts and drafts compliant replies
     (via zap_sim_organic) -> agents/leads_log.txt
  2. Generates ready-to-post Facebook / X / YouTube copy for the day
     (via skills.content_gen) -> agents/Facebook_Posts_*.md
  3. Prints a clean checklist of what YOU post by hand today.

Usage:
  python3 storm_roof_agent.py                # defaults to roofing/storm focus
  python3 storm_roof_agent.py hvac           # focus a single service

Daily cron (twice a day):
  0 9,18 * * *  python3 /path/storm_roof_agent.py
"""
import sys
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

SITE = "https://quotemyanything.com"

SERVICE_PAGES = {
    "roofing": "/roofing.html", "hvac": "/hvac.html", "plumbing": "/plumbing.html",
    "solar": "/solar.html", "lawn-care": "/lawn-care.html", "painting": "/painting.html",
    "electrical": "/electrical.html", "pest-control": "/pest-control.html",
    "tree-service": "/tree-service.html", "moving": "/moving.html",
    "house-cleaning": "/house-cleaning.html",
}


def run_lead_scan():
    print("\n[1/3] Scanning Reddit for live lead opportunities...")
    try:
        import zap_sim_organic as z
        z.main()
    except Exception as e:
        print(f"  lead scan skipped: {e}")


def run_content(service):
    print("\n[2/3] Generating today's post copy...")
    try:
        from skills import content_gen
        out = content_gen.run({"platform": "all", "service": service})
        print(f"  content_gen: {out.get('status')} ({out.get('items')} blocks)")
    except Exception as e:
        print(f"  content_gen skipped: {e}")


def checklist(service):
    page = SERVICE_PAGES.get(service, "/roofing.html")
    print("\n[3/3] TODAY'S LEAD CHECKLIST (do these by hand -- ~15 min):")
    steps = [
        f"Open agents/leads_log.txt -> reply to any new Reddit posts (be helpful first, drop {SITE}{page} only if relevant).",
        "Post 1 Facebook post from the newest Facebook_Posts_*.md to local Austin groups + your page.",
        f"Post 1 X/Twitter reply or tweet targeting an Austin storm/{service} keyword, linking {SITE}{page}.",
        "Check Formspree inbox -> any lead that arrived, log it in the for-pros routing console.",
        "Optional: record a 30s phone video for YouTube/Shorts using the Gemini commercial as intro.",
    ]
    for i, s in enumerate(steps, 1):
        print(f"  {i}. {s}")


def main():
    service = sys.argv[1] if len(sys.argv) > 1 else "roofing"
    if service not in SERVICE_PAGES:
        print(f"Unknown service '{service}'. Options: {', '.join(SERVICE_PAGES)}")
        service = "roofing"
    print(f"===== QMA DAILY LEAD AGENT -- {datetime.now():%Y-%m-%d %H:%M} -- focus: {service} =====")
    run_lead_scan()
    run_content(service)
    checklist(service)
    print(f"\n===== Done. Consistency wins. Run this twice a day. {SITE} =====")


if __name__ == "__main__":
    main()
