# Quote Me Anything — *Buy it. Sell it. Get paid fast.*

A fast marketplace for **anything** — sneakers to supercars. Buy it, sell it, or **name your price**.
Free to list. Pay only when it sells. **Buyer and seller deal direct — we never touch the money.**

**Live:** quotemeanything.com · **Stack:** static front-end + [Supabase](https://supabase.com) · **License:** MIT

---

## Why it's different
- **Free to list**, pay only when it sells — a small fee that *drops* as the price climbs.
- **Name your price** — built-in offers/negotiation on everything.
- **Deal direct** — we connect buyer and seller and never hold funds (no middleman, no money-transmitter risk).
- **Vetted sellers** — apply, get approved, list. No scammers, no spam.
- **Reseller links** — every seller gets a share code; earn on what you refer.
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

## Files
- `index.html` — marketplace storefront (vanilla JS, Supabase via CDN, no build step).
- `dashboard.html` — seller dashboard (Client ID + PIN login → offers pipeline, listings, payouts).
- `vercel.json` — clean URLs + security headers.

## Backend (Supabase)
- Tables: `listings`, `offers`, `seller_applications`, `sellers`, `orders` (auto fee/payout trigger),
  `categories`, `settings`, `referral_hits`.
- Edge function `seller-portal` — validates Client ID + PIN (service role), returns only that seller's
  data, masks buyer contact until an offer is accepted.

## Run / deploy
Static site — deploy the folder to any static host (Vercel recommended). Set your own Supabase URL +
publishable key at the top of the `<script>` in `index.html` and `dashboard.html`.

## License
[MIT](./LICENSE) — free to use, modify, and build on.
