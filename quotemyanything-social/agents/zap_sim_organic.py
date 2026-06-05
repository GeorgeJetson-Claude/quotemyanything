#!/usr/bin/env python3
"""
Organic Lead Finder for QuoteMyAnything (free, no API keys, stdlib only).

Monitors Reddit /new.json across home-service subreddits for people actively
asking for quotes/recommendations, then writes drafted, compliant replies you
can post by hand. Human-in-the-loop on purpose: no auto-posting (keeps your
accounts safe and within platform rules).

Run:   python3 zap_sim_organic.py
Daily: add to cron, e.g.  0 9,17 * * *  python3 /path/zap_sim_organic.py
"""
import json
import urllib.request
from datetime import datetime
from pathlib import Path

# --- Portable paths (relative to this file; works in any environment) ---
BASE = Path(__file__).resolve().parent
LEADS_LOG = BASE / "leads_log.txt"
SITE = "https://quotemyanything.com"

# Optional external alert hook (5LUV/Zapier). Stays silent if not present.
TRIGGER = Path.home() / "5LUVINC" / "scripts" / "trigger_qma.py"

# Subreddits where Austin/Central-TX homeowners ask for service quotes.
SUBS = "Austin+HomeImprovement+lawncare+HVAC+Roofing+Plumbing+Moving+solar+pestcontrol+electricians"
REDDIT_URL = f"https://www.reddit.com/r/{SUBS}/new.json?limit=50"

# Service routing: keyword -> (service label, landing page) for a tailored reply.
SERVICE_MAP = {
    "roof": ("roofing", "/roofing.html"),
    "hail": ("roofing", "/roofing.html"),
    "shingle": ("roofing", "/roofing.html"),
    "hvac": ("HVAC", "/hvac.html"),
    "ac ": ("HVAC", "/hvac.html"),
    "air condition": ("HVAC", "/hvac.html"),
    "furnace": ("HVAC", "/hvac.html"),
    "plumb": ("plumbing", "/plumbing.html"),
    "water heater": ("plumbing", "/plumbing.html"),
    "leak": ("plumbing", "/plumbing.html"),
    "solar": ("solar", "/solar.html"),
    "lawn": ("lawn care", "/lawn-care.html"),
    "landscap": ("lawn care", "/lawn-care.html"),
    "paint": ("painting", "/painting.html"),
    "electric": ("electrical", "/electrical.html"),
    "pest": ("pest control", "/pest-control.html"),
    "roach": ("pest control", "/pest-control.html"),
    "tree": ("tree service", "/tree-service.html"),
    "stump": ("tree service", "/tree-service.html"),
    "moving": ("moving", "/moving.html"),
    "movers": ("moving", "/moving.html"),
    "clean": ("house cleaning", "/house-cleaning.html"),
}

# Intent signals: a post only counts as a lead if it shows buying intent.
INTENT = [
    "quote", "recommend", "looking for", "anyone know a good", "need a",
    "how much", "cost", "estimate", "cheapest", "suggestions", "who do you use",
    "referral", "hire", "best company",
]


def fetch():
    try:
        req = urllib.request.Request(REDDIT_URL, headers={"User-Agent": "QMA-LeadFinder/2.0"})
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode()).get("data", {}).get("children", [])
    except Exception as e:
        print(f"[fetch error] {e}")
        return []


def match_service(text):
    for kw, (label, page) in SERVICE_MAP.items():
        if kw in text:
            return label, page
    return None, None


def draft_reply(service, page):
    return (
        f"If you want to compare options fast, {SITE}{page} matches you with up to 3 "
        f"local licensed {service} pros who compete for the job — free for homeowners, "
        f"takes about 60 seconds, no spam. Worth a look before you commit to one bid."
    )


def find_opportunities(posts):
    opps = []
    for p in posts:
        d = p.get("data", {})
        text = (d.get("title", "") + " " + d.get("selftext", "")).lower()
        if not any(sig in text for sig in INTENT):
            continue
        service, page = match_service(text)
        if not service:
            continue
        opps.append({
            "service": service,
            "title": d.get("title", "")[:140],
            "url": "https://reddit.com" + d.get("permalink", ""),
            "sub": d.get("subreddit", ""),
            "reply": draft_reply(service, page),
        })
    return opps


def report(opps):
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    if not opps:
        print(f"[{stamp}] No new buying-intent posts in feed this run.")
        return
    print(f"\n=== {len(opps)} LEAD OPPORTUNITIES — {stamp} ===\n")
    with open(LEADS_LOG, "a") as f:
        f.write(f"\n===== RUN {stamp} — {len(opps)} opportunities =====\n")
        for i, o in enumerate(opps, 1):
            block = (
                f"[{i}] r/{o['sub']} — {o['service'].upper()}\n"
                f"    Post : {o['title']}\n"
                f"    Link : {o['url']}\n"
                f"    Reply: {o['reply']}\n"
            )
            print(block)
            f.write(block + "\n")
            if TRIGGER.exists():
                import subprocess
                try:
                    subprocess.call(["python3", str(TRIGGER), "LEAD_OPP", o["sub"], o["title"][:50]])
                except Exception:
                    pass
    print(f"Saved drafts to {LEADS_LOG}. Review, then reply by hand on Reddit.")


def main():
    print(f"=== QMA Organic Lead Finder — {datetime.now().strftime('%Y-%m-%d %H:%M')} ===")
    report(find_opportunities(fetch()))


if __name__ == "__main__":
    main()
