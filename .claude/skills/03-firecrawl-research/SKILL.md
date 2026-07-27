---
name: 03-firecrawl-research
description: >
  Scrapes a company website into clean, page-typed markdown using Firecrawl
  map + scrape + extract. Triggers on: "scrape this company", "read their
  website", "extract pages from", "research this domain", "fetch their
  careers page", or any URL + "scrape/extract/read". Covers single domain,
  batch processing, structured LLM extraction, and Google Sheets output.
---

# Firecrawl Research

Given a company domain, scrape its website and return clean markdown organized
by page type. Downstream skills (signal-builder, email-writer) consume this
output. This skill fetches only — scoring and interpretation belong to
signal-builder.

## Quick start

The user provides domain(s) and optionally a mode. Default to standard.

| Mode | Credits | Pages |
|------|---------|-------|
| standard | 5-8 | Homepage, About, Careers, Blog, Pricing, Customers, Integrations, Product |
| deep | 5-11 | Standard + Changelog, Leadership |
| minimal | 3 | Homepage, About only |
| extract | ~20+ | Structured JSON via LLM extraction |

If the user doesn't specify a mode, use standard. Confirm mode before running
only when the choice is ambiguous or the batch is large (>50 domains).

## Running the scraper

```bash
# Single domain
python3 scripts/firecrawl_scrape.py --domain "acme.com" --mode standard

# Batch (one domain per line in file)
python3 scripts/firecrawl_scrape.py --batch domains.txt --mode standard

# Resume interrupted batch
python3 scripts/firecrawl_scrape.py --resume runs/<run-folder-name>
```

All paths are relative to the skill folder (`firecrawl-research/`).

The script creates a timestamped run folder under `runs/` with a `tracker.json`
for progress and per-domain JSON scan files under `runs/<name>/scans/`.

After a scrape completes, read the tracker and show the user a summary
(completed/failed count, total credits).

## Writing to Google Sheet

Use `scripts/sheets_writer.py` — the Google Sheets MCP fails on large content.

```bash
python3 scripts/sheets_writer.py \
  --run-dir runs/<run-folder> \
  --spreadsheet-id <SHEET_ID>
```

Options: `--summary` (char counts instead of full content), `--tab-name "name"`.

### Output columns

| Column | Content |
|--------|---------|
| Domain | acme.com |
| Status | success / partial / blocked |
| Mode | standard / deep / minimal / extract |
| Date | 2026-06-18 |
| URLs Found | 47 |
| Pages Scraped | 6 |
| Credits Used | 7 |
| Homepage…Product | Page content (or empty if not found) |

## Page types

See `references/page-types.md` for full classification and multilingual patterns.

| Tier | Pages | Modes |
|------|-------|-------|
| 1 | Homepage, About, Careers, Blog | All |
| 2 | Customers, Pricing, Integrations, Product | Standard + Deep |
| 3 | Changelog, Leadership | Deep only |

Careers scrapes the main `/careers` page only (1 credit).

## Extract mode

When the user picks extract without a custom schema, the script uses:

```json
{
  "founder": "string", "headcount_clues": "string",
  "tech_mentions": "array", "funding_clues": "string",
  "product_category": "string", "customers_mentioned": "array",
  "partners": "array", "investors": "array",
  "year_founded": "string", "locations": "array"
}
```

Extract mode is the best way to get customer/partner/investor data — it uses
LLM-powered extraction that understands context better than HTML parsing.
The user can override with a custom schema.

## Cost and credit rules

| Trigger | Action |
|---------|--------|
| Single domain > 10 credits | Warn before proceeding |
| Batch > 50 domains | Show estimated total, ask confirmation |
| Batch > 500 domains | Suggest minimal mode, require confirmation |
| Estimated batch > $10 | Hard stop, require user approval |

Credit math: credits x $0.001 (Standard plan) or credits x $0.0004 (Growth).

Credit tracking rules — these prevent silent cost overruns:
- Read actual credits from `response.metadata.credits_used`, not hardcoded counts. Firecrawl's stealth proxy charges 5 credits instead of 1 and activates automatically on blocked sites.
- Always map before scraping — blind scraping wastes credits on wrong URLs.
- Check the Firecrawl dashboard credit balance before large batches. Stealth proxy can silently 5x expected cost.
- Running scrape + extract together on the same domain has no benefit over running them separately and costs more.

## Shared output (records.jsonl)

After each run (single or batch), the script writes `records.jsonl` and `meta.json`
to the run folder alongside `tracker.json` and `scans/`. Each record carries the
stage-03 fields per `_shared/CONVENTIONS.md` - `scraped_markdown` keyed by page
type (capped at 15K chars/page; `scans/*.json` keep the full text),
`pages_scraped`, and `scrape_status` - plus `has_<page>` labels in
`filters_matched`:

```jsonl
{"company": "Acme Corp", "domain": "acme.com", "person": null, "scraped_markdown": {"homepage": "# Acme...", "about": "## Our story..."}, "pages_scraped": 2, "scrape_status": "success", "filters_matched": ["has_homepage", "has_about"]}
```

`--batch` also accepts an upstream `records.jsonl` (from 01/02/04) directly: it
reads the domains from it and carries every upstream field through into the
output records, so the chain record keeps evolving instead of restarting here.

## Scope boundaries

| Not this skill | Use instead |
|----------------|-------------|
| Score or rank signals | signal-builder |
| Find email addresses | prospeo-resolve |
| Discover domains | prospeo-discover |

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `FIRECRAWL_API_KEY not found` | Add to `.env` file |
| Map returns 0 URLs | Script falls back to homepage-only scrape |
| All pages thin_content | Site is JS-heavy or blocked |
| Credits running low | Switch to minimal mode |
| Sheet writer auth fails | Re-auth: `rm ~/.google/token.json` then re-run |
| Interrupted batch | Resume with `--resume <run-folder-path>` |
| Script import error | `pip install -r ../_shared/requirements.txt` |

## Auth

- Firecrawl: `FIRECRAWL_API_KEY` in `.env`
- Google Sheets: OAuth2 token at `~/.google/token.json`
