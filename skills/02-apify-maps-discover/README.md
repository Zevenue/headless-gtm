# 02-apify-maps-discover

The local-business (SMB) discovery step of the API-first GTM chain. Turns a
vertical plus a place ("yoga studios" + "California") into a clean prospect
list scraped from Google Maps via the maintained Apify Compass actor
(`compass~crawler-google-places`). Built for ICPs that title-based contact
databases can't reach - laundromat owners, salons, HVAC operators, studios,
gyms, clinics - where the business exists on Maps but not in a B2B database.

It wraps the best existing actor rather than running its own scraper: Compass
already handles proxies, anti-bot, and layout drift, and offers optional
email/contact enrichment.

## What it does

- Takes a `search_term` (the vertical) and a `geo` (the area), with sane
  defaults (`max_results=200`, `min_rating=4.0`), and asks only when inputs
  are missing or ambiguous
- Prints a cost estimate before any API call, and requires explicit
  confirmation (`--yes` or an interactive prompt) for any run over $10 -
  never bypassed silently; `--estimate-only` does a dry run with no spend
- Normalizes every raw place into a shared 15-field ProspectRecord: name,
  domain, website, phone, full address, city, region, rating, review count,
  coordinates, place ID, category, last review date, source
- Writes a `runs/<run-id>/` folder per the chain conventions: `records.jsonl`
  (the shared format downstream skills consume), `tracker.json`, `meta.json`
  (count + spend estimate), `prospects.json`, and `records.csv` for humans
- Keeps output usable for outreach: every row has at least a name plus a
  domain or phone, domains are bare hosts so they dedup cleanly, and closed
  businesses are skipped
- Optional flags add contact emails (`--include-emails`, ~$2/1K extra) or
  per-place review dates (`--with-review-dates`, extra cost and latency)

Typical pricing: ~$2.10/1K records for discovery, ~$4.10/1K with emails - a
typical 2K-record run lands around $4-8.

## Setup

Auth comes from an environment variable - no keys are stored in the skill.

```bash
export APIFY_API_TOKEN="your-apify-token"   # console.apify.com -> Settings -> Integrations
pip install -r ../headless-gtm-shared/requirements.txt
```

## Layout

```
02-apify-maps-discover/
├── SKILL.md                        workflow, flags, cost gate, output contract
├── discover.py                     estimate -> gate -> run actor -> normalize -> runs/<run-id>/
└── reference/
    ├── compass-actor.md            actor ID, endpoints, full input schema, limits
    ├── output-schema.md            15-field ProspectRecord + raw-to-normalized map
    ├── cost-model.md               pricing per mode and how the $10 gate is computed
    ├── verticals-and-geo.md        search-term phrasings, geo formats, sizing
    ├── examples.md                 copy-paste recipes for common jobs
    └── troubleshooting.md          empty results, auth errors, timeouts, rate limits
```

Evals for this skill are maintained in Zevenue's private source repo and run
before every release - skill folders ship without them.

## Position in the chain

Step 02 is the vertical-SMB discovery entry - the sibling of
[`01-prospeo-discover`](../01-prospeo-discover/), which covers B2B SaaS ICPs
that live in company databases. When the ICP is Maps-addressable, the chain
starts here instead.

```
02 apify-maps-discover -> 01 icp-qualify -> signals -> extract -> judge -> resolve
```

Output flows to `01-icp-qualify` (the free gate that judges fit before any
paid step), then on to the downstream enrichment, judgment, and email
resolution skills - all of which read `runs/<run-id>/records.jsonl`.

Built at [Zevenue](https://zevenue.com), a GTM engineering firm.
