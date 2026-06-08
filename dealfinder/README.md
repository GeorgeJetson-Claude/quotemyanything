# Pace Morby Deal Finder

An automated deal-sourcing / qualification engine for **Pace Morby's published
buy boxes** (pacemorby.com). Feed it candidate properties; it scores each one
against every buy box, ranks the matches, and drafts the submission email in the
exact format Pace's team asks for — so the deals you send actually fit and
actually get read.

> It **qualifies and drafts**. It does **not** send anything and does **not**
> scrape any site against its Terms of Service. You review the drafts and hit
> send (the buy-box "Email Us" form) when you're ready.

## The buy boxes (encoded in `buy_boxes.py`)

| Buy box | Geo | Asset | Financing | Rule |
|---|---|---|---|---|
| **SFH Fix & Flip** | Maricopa County, AZ **only** | Single-family | Cash or creative | Price ≤ **50% of ARV** (Zillow ÷ 2), 10–15/yr |
| **Mobile Home Park** | Nationwide (prefers AZ/TX/GA) | MHP | **Creative only** | Existing parks |
| **RV Parks / Campgrounds / Resorts** | Nationwide (CA/NY ok) | RV park / campground / resort | **Creative only** | **Existing** only, **no flood zones**, no dev land, 15–20/yr |
| **Private Lending** | n/a | any | private / hard money | Capital for flips & refis |

## Usage

```bash
cd dealfinder

# Score the sample deals and print a ranked report
python3 dealfinder.py --input sample_deals.csv

# Only show strong fits, and write submission drafts to outbox/
python3 dealfinder.py --input sample_deals.csv --min-score 65 --write-drafts

# Machine-readable output (for piping into another tool / Zapier)
python3 dealfinder.py --input sample_deals.csv --json
```

Stdlib only — no pip install needed. Python 3.8+.

## Input format

A CSV with these columns (only `address` is strictly required; more data = a
stronger, submittable match):

```
address, county, state, asset_type, purchase_price, arv (or zillow_value),
financing_terms, flood_zone, existing_operation, is_land, photos_url, notes
```

`asset_type` values: `single_family`, `mhp`, `rv_park`, `campground`, `resort`.
`financing_terms` keywords: `cash`, `creative`, `subto`, `seller finance`, etc.

See `sample_deals.csv` for worked examples (including deals that *should* fail —
wrong county, over the 50% cap, flood zone, raw land, cash-only on a
creative-only box).

## How scoring works (`matcher.py`)

1. **Hard rules disqualify** (`fit = "no"`): wrong asset type, outside the geo,
   wrong financing, over the 50%-of-ARV cap, flood zone, or development land.
2. Survivors get a **0–100 score**: baseline 60, +up to 30 for buying further
   under the ARV cap, +10 for a preferred state.
3. `fit = "maybe"` means it qualifies but is missing something you need before
   submitting (photos, purchase price, financing terms — or ARV for the SFH box).

## Automating ingestion (the "automate it" part)

`sources.py` is a pluggable adapter registry. CSV ships today. To run this on a
schedule against live data, add an adapter that returns the same normalized dict
shape and register it — using **licensed / public** feeds only:

- County assessor / GIS open-data exports (public records)
- Your MLS feed via a licensed RESO Web API account
- A paid list/data provider API you already license
- FEMA flood map API to auto-fill `flood_zone`

Then schedule `dealfinder.py --write-drafts` (cron / GitHub Action) and review
the `outbox/` each morning.

## Files

```
buy_boxes.py     buy box definitions (single source of truth)
matcher.py       scoring engine (hard rules + soft preferences)
email_builder.py drafts the submission email in Pace's required format
sources.py       pluggable ingestion adapters (CSV today)
dealfinder.py    CLI entry point
test_dealfinder.py  smoke tests
sample_deals.csv example input
outbox/          drafted submission emails land here (git-ignored)
```
