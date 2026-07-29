# 04-crustdata-signals

The "what already happened" signal layer (step 04) of the API-first GTM chain.
Enriches company domains with structured signals from
[CrustData](https://crustdata.com): funding rounds, headcount growth,
department growth, and recent hires.

Feed it a domain list, a Google Sheet, or an upstream `records.jsonl`, and it
returns records with signal fields attached plus auto-generated signal text
("Series A $20M raised 45d ago - FRESH CAPITAL"), ready for judgment and copy.

## What it does

- Takes domains from a raw list, a Google Sheet column, or an upstream
  `records.jsonl` (discovery/qualification/extraction output); with `--records`,
  every upstream field is inherited so the chain record keeps evolving instead
  of restarting here
- Pulls funding rounds, headcount growth, department growth, and recent hires
  over a configurable window (90/180/365 days back, default 180)
- Computes fresh growth from timeseries data instead of trusting CrustData's
  pre-computed growth fields, which lag by 3-10 months
- Treats credits like money: ~2 credits per enrich plus 0.03 per hire returned,
  budgeted by the ICP's hiring velocity rather than a flat per-domain rate
- Caches every API response as a per-domain JSON in `runs/<run-id>/` and reuses
  cached JSONs from prior runs before spending credits again
- Resumes mid-run from a tracker file if a batch fails partway
- Writes `records.jsonl` with the stage-04 fields: `funding[]`,
  `headcount_growth`, `dept_growth[]`, and `recent_hires[]` (capped at 25 per
  record; the per-domain JSONs keep the full list)
- Optional Google Sheets writer with 5 tabs (Signal Summary, Recent Hires,
  Funding, Company Growth, Dept Growth) that can combine multiple run folders
  and dedupes by domain

Example record (fictional company):

```jsonl
{"company": "Acme Robotics", "domain": "acmerobotics.com", "funding": [{"round_type": "Series B", "money_raised_formatted": "$56M", "date": "2026-03-02"}], "headcount_growth": {"current_employee_count": 350, "employee_count_yoy_growth_rate_percentage": 42}, "recent_hires": [{"name": "J. Doe", "title": "VP Sales", "start_date": "2026-05-01", "seniority": "vp"}], "filters_matched": ["Series B $56M", "42% YoY growth", "18 recent hires"]}
```

## Setup

Auth comes from environment variables - no keys are stored in the skill.

```bash
export CRUSTDATA_API_KEY="your-crustdata-key"   # from the CrustData dashboard
```

Only needed for the optional Google Sheets writer: an OAuth2 token at
`~/.google/token.json` plus the `gspread`/`google-auth` extras from
`../headless-gtm-shared/requirements.txt`.

## Layout

```
04-crustdata-signals/
├── SKILL.md                      workflow, credit rules, output spec
├── references/
│   ├── enrich-api.md             company enrich endpoint docs
│   └── person-search-api.md      person search endpoint docs
├── scripts/
│   ├── crustdata_signals.py      enrichment -> runs/<run-id>/ (JSONs + records.jsonl)
│   └── sheets_writer.py          run folder(s) -> 5-tab Google Sheet
└── runs/                         (created at runtime) per-run JSONs, records, summary
```

Evals for this skill are maintained in Zevenue's private source repo and run
before every release - skill folders ship without them.

## Position in the chain

Step 04 (signals) has two sibling skills:
[`04-theirstack-jobs`](../04-theirstack-jobs/) covers what's open right now
(job postings); this one covers what already happened (funding rounds, people
who joined, headcount trends). Upstream, it accepts `records.jsonl` from any
discovery or extraction step. Downstream, its records feed
[`05-signal-builder`](../05-signal-builder/), where signals get scored and
turned into campaign angles.

Built at [Zevenue](https://zevenue.com), a GTM engineering firm.
