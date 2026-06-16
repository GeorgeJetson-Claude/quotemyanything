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

## The full loop

```
ingest → enrich (FEMA flood) → match (buy box) → underwrite ($) → rank →
draft email → track in pipeline → record fee → P&L
```

## Usage

```bash
cd dealfinder

# Score + underwrite candidates, draft submission emails, record to pipeline
python3 dealfinder.py scan --input sample_deals.csv --write-drafts

# Same, plus wholesale math + assignment agreement for SFH deals
python3 dealfinder.py scan --input sample_deals.csv --write-drafts --paperwork

# Pull candidates straight from Maricopa County public records (offline sample)
python3 dealfinder.py scan --source maricopa_fixture
# ...or live (needs a free token; see County feed below)
MARICOPA_API_TOKEN=xxx python3 dealfinder.py scan --source maricopa --query "Phoenix 85007"

# The full automated chain: county parcels -> ARV from comps -> underwrite ->
# draft + assignment paperwork, all tracked in the pipeline
python3 dealfinder.py scan --source maricopa_fixture \
    --comps fixtures/comps_sample.csv --arv-from-fcv \
    --write-drafts --paperwork

# Only strong fits; auto-fill flood zone from FEMA for rows that have lat/lon
python3 dealfinder.py scan --input sample_deals.csv --min-score 65 --flood

# See everything you're tracking + running P&L
python3 dealfinder.py pipeline

# Move a deal through its lifecycle and record the fee when it closes
python3 dealfinder.py status "1423 W Roosevelt" --set submitted
python3 dealfinder.py status 1a2b3c --set accepted --fee 12000

# Machine-readable output (pipe into Zapier / a sheet)
python3 dealfinder.py scan --input sample_deals.csv --json

# Print the buy box definitions
python3 dealfinder.py boxes
```

Stdlib only — no pip install needed. Python 3.8+.

## Input format

A CSV with these columns (only `address` is strictly required; more data = a
stronger, submittable match):

```
address, county, state, asset_type, purchase_price, arv (or zillow_value),
financing_terms, flood_zone, existing_operation, is_land, photos_url, notes
```

Optional columns that unlock underwriting numbers:

```
# fix & flip:   sqft, rehab_level (light|medium|heavy|gut), rehab_cost
# parks:        pads (or sites/units), lot_rent, occupancy, noi, expense_ratio
# flood enrich: lat, lon   (used by --flood to query FEMA)
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

## Underwriting (`underwriting.py`) — putting a number on each deal

- **Fix & flip:** estimates rehab ($/sqft by level, or your explicit number),
  then projected profit = ARV − price − rehab − holding/selling, plus ROI and
  spread vs Pace's 50%-of-ARV cap.
- **Parks (MHP / RV):** NOI (from an explicit figure, or pads × lot_rent ×
  occupancy with an expense ratio), cap rate, and a value estimate at a target
  cap so you can see value-vs-price.

These numbers are printed in the report and embedded in the submission email.

## ARV from comps (`arv.py`) — the number that drives everything

The 50%-of-ARV rule is only as good as the ARV, so this estimates it
transparently instead of guessing:

- **Comps method (preferred):** median $/sqft of nearby sold/renovated comps,
  outliers trimmed, applied to the subject's sqft. Confidence (`high`/`medium`/
  `low`) scales with comp count and how tightly they cluster.
- **Assessor fallback (`--arv-from-fcv`):** county Full Cash Value × market
  factor. Always `low` confidence — triage only, never submit on it.

Feed comps with `--comps comps.csv`:

```
subject_apn, subject_address, comp_address, sold_price, sqft, sold_date
```

(match each comp to a subject by APN or address). See
`fixtures/comps_sample.csv`. The report prints the ARV, its confidence, and the
exact basis (e.g. `4 comps, median $221/sqft x 1450sqft`).

## Scheduling (`.github/workflows/dealfinder.yml`) — the "automate it" part

A GitHub Action runs the scan daily (and on demand), estimates ARV from comps,
drafts emails + assignment paperwork, and commits the updated `pipeline.json`.
Set the `MARICOPA_API_TOKEN` repo secret + a `query` input to use the live
county feed; without them it runs the offline fixture so the workflow is always
green. It never emails anything — you still review `outbox/` and submit.

## Revenue model: wholesale assignment (`assignment.py`)

The exit is an **assignment**: you tie the property up under contract with the
seller, then assign that contract to Pace's entity for an **assignment fee**.
The underwriter does the math so there's room for your fee under Pace's 50% cap:

```
ARV (your comps) → Pace's ceiling = 50% × ARV
Tie property up at ≤ ceiling − target fee   ($15k default)
Your assignment fee = ceiling − your contract price   (min $5k to be "viable")
```

With `--paperwork`, each viable SFH deal also gets a **wholesale math sheet**
and a fill-in-the-blank **Assignment of Contract** written to `outbox/`.

> The assignment agreement is a template, **not legal advice**. Assignment rules
> and disclosures vary by state — have a local attorney or title company review
> before using it on a live deal.

## County feed (`sources.py`, source=`maricopa`)

Because the SFH box is **Maricopa County only**, the county assessor is the
public-records feed. The API issues a **free token** (request at
mcassessor.maricopa.gov); set `MARICOPA_API_TOKEN` and use `--source maricopa
--query "..."`. An offline fixture (`--source maricopa_fixture`) lets you run it
with no network/token.

County data gives you address, asset type, sqft, year built, and the assessor's
Full Cash Value — but **FCV is a tax value, not ARV**, so deals come in as
"maybe" until you add real comps (ARV), your offer price, and financing. That's
intentional: it won't let you submit an un-comped number to Pace.

> Egress note: in a sandboxed/allowlisted environment, add
> `mcassessor.maricopa.gov` (and `hazards.fema.gov` for `--flood`) to the
> network egress allowlist, or live calls return 403.

## Pipeline + money (`pipeline.py`)

Every qualifying deal is recorded to `pipeline.json` keyed by a stable id from
the address, so the same property is **never re-submitted by accident**. Deals
move `new → drafted → submitted → under_contract → accepted | dead`. Accepted
deals carry the assignment **fee**, and `dealfinder.py pipeline` rolls it into a
P&L (realized revenue + pipeline fee potential). This is the "make us money"
ledger — it tracks what you sent and what it earned.

## Automating ingestion (the "automate it" part)

`sources.py` is a pluggable adapter registry. CSV ships today; `--flood`
auto-fills the flood-zone field from FEMA's free public NFHL API (no key) for
any row with `lat`/`lon`. To run on a schedule against live data, add an adapter
that returns the same normalized dict shape — using **licensed / public** feeds
only:

- County assessor / GIS open-data exports (public records)
- Your MLS feed via a licensed RESO Web API account
- A paid list/data provider API you already license

Then schedule `dealfinder.py scan --write-drafts` (cron / GitHub Action) and
review `outbox/` each morning. Deals already in the pipeline won't be
re-created.

## Files

```
buy_boxes.py     buy box definitions (single source of truth)
matcher.py       scoring engine (hard rules + soft preferences)
arv.py           ARV estimation from comps (+ assessor fallback)
underwriting.py  flip + park valuation + wholesale assignment economics
assignment.py    wholesale math sheet + Assignment of Contract template
email_builder.py drafts the submission email in Pace's required format
pipeline.py      persistent ledger: dedup, status lifecycle, fee/P&L
sources.py       pluggable ingestion (CSV, Maricopa assessor) + FEMA flood
dealfinder.py    CLI (scan / pipeline / status / boxes)
test_dealfinder.py  smoke tests (34)
sample_deals.csv example input
fixtures/        offline county + comps samples (test without network)
outbox/          drafted emails + paperwork land here (git-ignored)
pipeline.json    the ledger (git-ignored; created on first scan)
../.github/workflows/dealfinder.yml   daily scheduled scan
```
