# Quote Me Anything 🚀 — *Where deals take off*

A fast, negotiation-first marketplace for **anything** — sneakers to supercars.
Buy it, sell it, or **name your price**. Free to list. Pay only when it sells.

**Live:** quotemeanything.com · **Stack:** static front-end + [Supabase](https://supabase.com) · **License:** MIT (open source, free to build on)

---

## Why it's different
- **Free to list**, pay only when it sells — a small fee that *drops* as the price climbs.
- **Make an offer on anything** — built-in haggle/negotiation, souk-style.
- **Vetted sellers** — apply, get approved, list. No scammers, no spam.
- **Reseller links** — every seller gets a share code; drive traffic, earn on what you refer.
- **Fast.** Single-page, edge-cached, instant search/sort/filter.

## Fee ladder (enforced in the database)
| Sale price | Fee |
|---|---|
| under $1,000 | 5% |
| $1,000 – $20,000 | 12.5% |
| $20,000 – $100,000 | 5% |
| $100,000 – $1,000,000 | 2.5% |
| over $1,000,000 | custom / negotiable |

Plus: **no listing fee**, optional **$5 Enhance Listing** boost.

## Architecture
- `index.html` — the whole front-end (vanilla JS, no build step). Supabase JS via CDN.
- `vercel.json` — clean URLs + security headers.
- **Supabase** backend: `listings`, `offers`, `seller_applications`, `sellers`,
  `orders` (auto fee/payout via trigger), `categories`, `settings`, `referral_hits`.

## Run / deploy
It's a static site — open `index.html`, or deploy the folder to any static host (Vercel recommended).
Set your own Supabase project URL + publishable key at the top of the `<script>` in `index.html`.

## License
[MIT](./LICENSE) — free to use, modify, and build on.
