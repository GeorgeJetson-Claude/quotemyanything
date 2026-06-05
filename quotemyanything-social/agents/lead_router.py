#!/usr/bin/env python3
"""
Lead router: Process homeowner leads from Formspree and route to contractors.
Usage: python3 lead_router.py --input leads.csv --output routed_leads.csv
"""

import json
import sys
import csv
from pathlib import Path
from datetime import datetime

CONTRACTOR_DB = {
    "roofing": [
        {"name": "Austin Roofing Pro", "zip": ["78704", "78703", "78702"], "email": "quotes@austinroofing.local"},
        {"name": "Central TX Roofing", "zip": ["78701", "78704", "78723"], "email": "leads@centraltxroofing.local"},
    ],
    "hvac": [
        {"name": "AC Experts Austin", "zip": ["78704", "78702", "78723"], "email": "quotes@acexperts.local"},
    ],
    "plumbing": [
        {"name": "24/7 Plumbing", "zip": ["78704", "78702", "78703"], "email": "leads@247plumbing.local"},
    ],
    "solar": [
        {"name": "Solar Austin", "zip": ["78704", "78702", "78723"], "email": "quotes@solaraustin.local"},
    ],
}

SERVICE_MAP = {
    "roof": "roofing", "roofing": "roofing", "hail": "roofing", "shingle": "roofing",
    "hvac": "hvac", "ac": "hvac", "air condition": "hvac", "furnace": "hvac",
    "plumb": "plumbing", "leak": "plumbing", "water heater": "plumbing",
    "solar": "solar",
    "lawn": "lawn-care", "landscap": "lawn-care",
    "paint": "painting", "electric": "electrical", "outlet": "electrical",
    "pest": "pest-control", "tree": "tree-service", "moving": "moving", "clean": "house-cleaning",
}

def normalize_service(service_text):
    """Map service text to service category."""
    text = service_text.lower()
    for keyword, category in SERVICE_MAP.items():
        if keyword in text:
            return category
    return None

def find_contractors(service, zip_code):
    """Find contractors for a service and ZIP."""
    if service not in CONTRACTOR_DB:
        return []

    contractors = []
    for contractor in CONTRACTOR_DB[service]:
        if zip_code in contractor["zip"]:
            contractors.append(contractor)
    return contractors

def route_lead(lead):
    """
    Route a lead to contractors.
    lead: dict with keys: name, email, phone, zip, service_details
    """
    service = normalize_service(lead.get("service_details", ""))
    zip_code = lead.get("zip", "").strip()

    if not service:
        return {"status": "error", "reason": "service_not_recognized", "lead": lead}

    contractors = find_contractors(service, zip_code)

    if not contractors:
        return {
            "status": "no_match",
            "reason": f"no_contractors_{service}_{zip_code}",
            "lead": lead,
            "service": service,
            "zip": zip_code,
        }

    # Round-robin: assign to first contractor (production would track rotation)
    contractor = contractors[0]

    return {
        "status": "routed",
        "lead": lead,
        "service": service,
        "zip": zip_code,
        "assigned_to": contractor["name"],
        "contractor_email": contractor["email"],
        "timestamp": datetime.now().isoformat(),
    }

def process_leads(input_file, output_file):
    """Process all leads from CSV and write routed results."""
    results = []

    try:
        with open(input_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                routed = route_lead(row)
                results.append(routed)
    except FileNotFoundError:
        print(f"Error: {input_file} not found")
        return

    # Write output
    with open(output_file, "w") as f:
        for result in results:
            f.write(json.dumps(result) + "\n")

    # Summary
    routed = sum(1 for r in results if r["status"] == "routed")
    no_match = sum(1 for r in results if r["status"] == "no_match")
    error = sum(1 for r in results if r["status"] == "error")

    print(f"\n✓ Processed {len(results)} leads")
    print(f"  Routed: {routed}")
    print(f"  No match: {no_match}")
    print(f"  Errors: {error}")
    print(f"  Output: {output_file}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 lead_router.py [--input leads.csv] [--output routed_leads.json]")
        print("\nExample leads CSV:")
        print("name,email,phone,zip,service_details")
        print("John Doe,john@example.com,512-xxx-xxxx,78704,Need roof repair")
        return

    input_file = "leads.csv"
    output_file = "routed_leads.json"

    for i, arg in enumerate(sys.argv[1:]):
        if arg == "--input" and i+2 < len(sys.argv):
            input_file = sys.argv[i+2]
        elif arg == "--output" and i+2 < len(sys.argv):
            output_file = sys.argv[i+2]

    process_leads(input_file, output_file)

if __name__ == "__main__":
    main()
