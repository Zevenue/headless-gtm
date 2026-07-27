# 03-firecrawl-research

The extraction step (03) of the API-first GTM chain. Given a company domain, it
scrapes the website into clean markdown organized by page type using
[Firecrawl](https://firecrawl.dev) map + scrape + extract, and writes the
evidence bundle the judgment layer ([`05-signal-builder`](../05-signal-builder/))
scores. It fetches only - scoring and interpretation happen downstream.

## What it does

- Maps the domain first, then scrapes only the page types that matter -
  blind scraping wastes credits on wrong URLs
- Four modes with known credit ranges: standard (Homepage, About, Careers,
  Blog, Pricing, Customers, Integrations, Product; 5-8 credits), deep
  (+ Changelog, Leadership), minimal (Homepage + About; 3 credits), and
  extract (structured JSON via LLM extraction; ~20+ credits)
- Batch mode over a domains file or an upstream `records.jsonl` from earlier
  chain steps - it reads the domains and carries every upstream field through,
  so the chain record keeps evolving instead of restarting here
- Extract mode pulls structured fields (founder, customers, partners,
  investors, funding clues, and more) with a default schema the user can
  override - the best way to get customer/partner/investor data
- Writes `records.jsonl` + `meta.json` per the chain contract: markdown keyed
  by page type (capped at 15K chars/page, full text kept in per-domain scan
  files), plus `pages_scraped`, `scrape_status`, and `has_<page>` labels
- Cost guardrails: warns past 10 credits on a single domain, confirms batches
  over 50 domains, hard-stops any batch estimated over $10, and reads actual
  credits from the API response - Firecrawl's stealth proxy can silently 5x
  the expected cost on blocked sites
- Resumable batches via a per-run `tracker.json`
- Optional Google Sheets export of a run via `scripts/sheets_writer.py`

## Setup

```bash
export FIRECRAWL_API_KEY="your-firecrawl-key"   # or put it in .env
```

Google Sheets export is opt-in and only needs auth if you use it: an OAuth2
token at `~/.google/token.json`.

## Layout

```
03-firecrawl-research/
├── SKILL.md                      workflow, modes, credit rules
├── references/
│   ├── page-types.md             page-type classification + multilingual patterns
│   ├── firecrawl-endpoints.md    map / scrape / extract API details
│   └── cost-guide.md             credit math and cost triggers
├── scripts/
│   ├── firecrawl_scrape.py       map -> scrape -> records.jsonl (single or batch)
│   └── sheets_writer.py          optional run -> Google Sheet export
└── runs/                         (created at runtime) tracker + scans + records per run
```

Evals for this skill are maintained in Zevenue's private source repo and run
before every release - skill folders ship without them.

## Position in the chain

```
01/02 discover -> 01 icp-qualify -> [03 firecrawl-research] -> 05 signal-builder
```

Runs after discovery and the qualification gate, so credits are only spent
scraping companies that already fit the ICP. Its output is the website-evidence
half of what `05-signal-builder` judges (the other half is vendor signals from
step 04). For scoring use signal-builder, for finding emails use resolution
(06), for building the domain list use the discovery skills.

Built at [Zevenue](https://zevenue.com), a GTM engineering firm.
