# Enum Cache Refresh Procedure

How to refresh `prospeo-enums.json` when it's older than 21 days or missing.

## When to Refresh

- File `references/prospeo-enums.json` does not exist
- `last_updated` field is older than 21 days from today

## What Gets Refreshed

### Hardcoded values (from Prospeo API schema — rarely change)

Write these directly — no API call needed:

- `employee_ranges` — 11 values
- `revenue_ranges` — 14 values
- `funding_stages` — 23 values
- `subtypes` — 27 values
- `departments` — 14 values
- `headcount_growth_departments` — 19 values
- `seniorities` — 10 values
- `business_models` — 8 values
- `news_categories` — 10 values
- `exec_events` — 24 values
- `email_providers` — 5 values
- `icp_departments` — 15 values
- `icp_company_sizes` — 5 values
- `company_statuses` — 4 values

### Fetched via API (may grow over time)

Use curl to refresh industries — direct curl, not MCP tools.

**Procedure for industries** (target: 256 values):

**Option A — Scrape from API docs (preferred, fastest):**
Use WebFetch on `https://prospeo.io/api-docs/enum/industries` to get the full list in one call.

**Option B — Crawl via search-suggestions curl (fallback):**

1. Run search-suggestions with 2-char prefixes to maximize coverage:
   ```bash
   # Example for one prefix:
   curl -s -X POST "https://api.prospeo.io/search-suggestions" \
     -H "X-KEY: $PROSPEO_API_KEY" -H "Content-Type: application/json" \
     -d '{"industry_search": "ac"}'
   # Response key: industry_suggestions → ["Accommodation Services", "Accounting", ...]
   ```

   Prefixes to cover all 256:
   ```
   ac, ad, ae, ag, ai, al, am, an, ap, ar, as, au, av
   bi, bl, bo, br, bu
   ca, ch, ci, cl, co, cr, cu
   da, de, di, do
   ed, el, en, ev, ex
   fa, fi, fo, fr, fu
   ga, ge, gl, go, gr, gu
   he, hi, ho, hu
   in, it
   la, le, li, lo, lu
   ma, me, mi, mo, mu
   na, no, nu
   of, oi, op, ou
   pa, pe, ph, pl, po, pr, pu
   ra, re, ri, ro, ru
   sa, sc, se, si, so, sp, st, su
   te, th, to, tr, tu
   ut
   ve, vo
   wa, wh, wi, wo
   ```

2. Collect all unique values from all `industry_suggestions` responses
3. Sort alphabetically
4. Write to `industries` array in the JSON file

**Rate limit**: 15 requests/second. No credit cost.

### NOT cached (fetched at runtime)

These are too large to cache. Resolve via curl when the user mentions specific values:

- **Technologies** (4,946 values) → `curl -d '{"technology_search": "hubspot"}'` → `technology_suggestions`
- **Locations** → `curl -d '{"location_search": "new york"}'` → `location_suggestions`
- **Job titles** → `curl -d '{"job_title_search": "sales"}'` → `job_title_suggestions`
- **Company filter fields** (integrations, investors, awards, etc.) → `curl -d '{"company_integrations_search": "salesforce"}'` → `company_integrations_suggestions`

The full list of runtime search keys and response keys is in `references/api-curl.md`.

**For technologies specifically**: the full list (4,946 values) is at https://prospeo.io/api-docs/enum/technologies but is >10MB. Runtime search-suggestions is the practical approach — the user will always specify what tech they want (e.g., "companies using HubSpot"), so a targeted lookup is enough.

## After Refresh

Update `last_updated` to today's date in ISO format, e.g. `"2026-06-22"`.
