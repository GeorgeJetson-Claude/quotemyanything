#!/usr/bin/env python3
"""
Daily QMA workflow: lead capture + routing + content generation.
One command runs: fetch leads → route to contractors → generate posts.

Usage: python3 daily_workflow.py [--service roofing] [--dry-run]
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Import local agents
from zap_sim_organic import fetch_organic_leads, format_lead_reply
from lead_router import route_lead, normalize_service

def run_workflow(service="roofing", dry_run=False):
    """Execute daily lead capture and routing workflow."""

    timestamp = datetime.now().isoformat()
    print(f"\n{'='*60}")
    print(f"QMA Daily Workflow | {timestamp}")
    print(f"{'='*60}\n")

    # Step 1: Fetch organic leads (Reddit)
    print("STEP 1: Fetching organic leads from Reddit...")
    try:
        leads = fetch_organic_leads(service)
        print(f"✓ Found {len(leads)} potential leads\n")
    except Exception as e:
        print(f"✗ Error fetching leads: {e}\n")
        leads = []

    if not leads:
        print("No leads found. Workflow complete.\n")
        return

    # Step 2: Route leads to contractors
    print("STEP 2: Routing leads to contractors...")
    routed = []
    for lead in leads:
        result = route_lead({
            "service_details": lead.get("title", lead.get("body", "")),
            "zip": "78704",  # Could extract from post if available
            "email": "leads@quotemyanything.com",
            "name": lead.get("author", "Homeowner"),
        })
        if result["status"] == "routed":
            routed.append(result)
            print(f"  ✓ Routed: {result['assigned_to']}")
        else:
            print(f"  ⚠ No match: {result['reason']}")

    print(f"\nRouted {len(routed)} of {len(leads)} leads\n")

    # Step 3: Generate reply drafts
    print("STEP 3: Generating reply drafts for Reddit/Discord...")
    replies = []
    for lead in leads:
        reply = format_lead_reply(
            service=service,
            title=lead.get("title", ""),
            url=lead.get("url", ""),
        )
        replies.append({
            "subreddit": lead.get("subreddit", "r/Austin"),
            "post_url": lead.get("url", ""),
            "draft_reply": reply,
        })
        print(f"  ✓ Draft for r/{lead.get('subreddit', 'Austin')}")

    print(f"\nGenerated {len(replies)} draft replies\n")

    # Step 4: Output checklist
    print("STEP 4: Daily Checklist (15 min work)")
    print("-" * 60)
    print(f"Leads to follow up:     {len(routed)}")
    print(f"Replies to post:        {len(replies)}")
    print(f"\nTODO:")
    print(f"  [ ] Email routed leads to contractors")
    print(f"  [ ] Review and post {len(replies)} replies on Reddit/Discord")
    print(f"  [ ] Log results in Google Sheet")
    print(f"  [ ] Check for contractor responses")
    print("\nLinks:")
    for reply in replies[:3]:  # Show first 3
        print(f"  • {reply['post_url']}")
    if len(replies) > 3:
        print(f"  ... and {len(replies)-3} more")

    # Step 5: Save to log
    log_entry = {
        "timestamp": timestamp,
        "service": service,
        "leads_found": len(leads),
        "leads_routed": len(routed),
        "replies_generated": len(replies),
        "routed_leads": routed,
        "draft_replies": replies,
    }

    log_file = Path("leads_log.jsonl")
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    print(f"\n✓ Logged to {log_file}")
    print("\n" + "="*60 + "\n")

def main():
    service = "roofing"
    dry_run = False

    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--service" and i+2 < len(sys.argv):
            service = sys.argv[i+2]
        elif arg == "--dry-run":
            dry_run = True

    try:
        run_workflow(service=service, dry_run=dry_run)
    except Exception as e:
        print(f"\n✗ Workflow failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
