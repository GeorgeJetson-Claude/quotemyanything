#!/usr/bin/env python3
"""
pipeline.py — persistent deal ledger: dedup, status lifecycle, and the money.

Sourcing is worthless if you spam the same address twice or lose track of what
you sent. This keeps a JSON ledger (pipeline.json) keyed by a stable deal id so:

  - the same property is never re-drafted/re-submitted by accident,
  - each deal moves through a status lifecycle, and
  - accepted deals record an assignment / referral FEE, giving you a running P&L.

Status lifecycle:
    new -> drafted -> submitted -> {accepted, dead}

Stdlib only. The ledger is a plain JSON file you can read, edit, or commit.
"""

import hashlib
import json
import os
import re
from datetime import datetime, timezone

LEDGER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "pipeline.json")

# Lifecycle for a wholesale-assignment deal: you draft -> submit to Pace ->
# tie the property up (under_contract) -> assign & close (accepted) | dead.
STATUSES = ["new", "drafted", "submitted", "under_contract", "accepted", "dead"]


def deal_id(deal):
    """Stable id from normalized address (dedup key)."""
    norm = re.sub(r"[^a-z0-9]+", "", (deal.get("address") or "").lower())
    return hashlib.sha1(norm.encode()).hexdigest()[:12]


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def load(path=LEDGER_PATH):
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return json.load(f)


def save(ledger, path=LEDGER_PATH):
    with open(path, "w") as f:
        json.dump(ledger, f, indent=2, sort_keys=True)


def upsert(ledger, deal, box_id, result, underwriting=None):
    """Insert a newly-matched deal, or refresh score/underwriting if it exists.
    Returns (entry, is_new). Never downgrades a human-set status."""
    did = deal_id(deal)
    existing = ledger.get(did)
    base = {
        "id": did,
        "address": deal.get("address"),
        "buy_box": box_id,
        "fit": result["fit"],
        "score": result["score"],
        "asset_type": deal.get("asset_type"),
        "state": deal.get("state"),
        "underwriting": underwriting or {},
        "updated": _now(),
    }
    if existing:
        existing.update(base)  # keep status, fee, history, first_seen
        return existing, False
    base.update({"status": "new", "fee": 0, "first_seen": _now(),
                 "history": [{"at": _now(), "status": "new"}]})
    ledger[did] = base
    return base, True


def set_status(ledger, did, status, fee=None, note=None):
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    entry = ledger.get(did)
    if not entry:
        raise KeyError(f"no deal with id {did}")
    entry["status"] = status
    entry["updated"] = _now()
    if fee is not None:
        entry["fee"] = float(fee)
    entry.setdefault("history", []).append(
        {"at": _now(), "status": status, **({"fee": fee} if fee else {}),
         **({"note": note} if note else {})})
    return entry


def find(ledger, prefix):
    """Resolve a short id prefix or address substring to a single id."""
    if prefix in ledger:
        return prefix
    hits = [k for k in ledger if k.startswith(prefix)]
    if not hits:
        p = prefix.lower()
        hits = [k for k, v in ledger.items()
                if p in (v.get("address") or "").lower()]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise KeyError(f"no deal matches '{prefix}'")
    raise KeyError(f"'{prefix}' is ambiguous: {hits}")


def pnl(ledger):
    """Revenue summary across the pipeline."""
    by_status = {s: 0 for s in STATUSES}
    revenue = 0.0
    pending_fee = 0.0
    for e in ledger.values():
        by_status[e.get("status", "new")] += 1
        if e.get("status") == "accepted":
            revenue += float(e.get("fee") or 0)
        elif e.get("status") in ("drafted", "submitted", "under_contract"):
            pending_fee += float(e.get("fee") or 0)
    return {"by_status": by_status, "realized_revenue": revenue,
            "pipeline_fee_potential": pending_fee, "total_deals": len(ledger)}
