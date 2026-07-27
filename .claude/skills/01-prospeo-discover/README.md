# prospeo-discover

B2B company discovery and list building via the [Prospeo](https://prospeo.io) search API. Turns a plain-English ICP into Prospeo filter JSON, searches the 30M+ company database across 33 filters, and exports large lists to Google Sheets.

## What it does

- Maps plain-English ICP language to exact Prospeo filter values
- Detects the account plan and only offers filters that plan supports
- Covers 5 mandatory filters with smart defaults (location, size, industry, status, revenue)
- Handles seed-based "similar to X" input by finding the pattern in the seeds and building an ICP (the lookalike filter is dropped before the search, since stacking it collapses results); the sibling [`01-prospeo-lookalike`](../01-prospeo-lookalike/) skill goes deeper when you want the matches themselves returned and ranked
- Recommends high-impact optional filters from the search context, capped at 5
- Tracks credits and confirms cost before any export
- Python export script with batching and retries for 3,000-5,000+ company lists

## Setup

Auth comes from environment variables - no keys are stored in the skill.

```bash
export PROSPEO_API_KEY="your-prospeo-key"

# Only needed for Google Sheets export:
export GOOGLE_TOKEN_PATH="$HOME/.google/token.json"          # default if unset
export GOOGLE_CREDENTIALS_PATH="$HOME/.google/credentials.json"  # default if unset
```

Export dependencies:

```bash
pip install requests gspread google-auth
```

## Export usage

```bash
# Preview the count for free (no export credits spent)
python3 scripts/sheets_export.py --filters filters.json --dry-run

# Standard chain export - writes runs/<run-id>/ (records.jsonl + tracker + meta)
python3 scripts/sheets_export.py --filters filters.json

# Also export to Google Sheets (opt-in)
python3 scripts/sheets_export.py --filters filters.json --sheets
python3 scripts/sheets_export.py --filters filters.json --spreadsheet-id SHEET_ID --tab-name "my-search"
```

## Layout

```
prospeo-discover/
├── SKILL.md                      workflow and instructions
├── references/
│   ├── api-curl.md               exact curl formats + search-suggestions keys
│   ├── filters-full.md           all 33 filters with accepted values
│   ├── plan-filter-map.md        which filters each plan supports
│   ├── mapping-examples.md       plain-English → filter JSON examples
│   ├── enum-refresh.md           enum cache refresh procedure
│   └── prospeo-enums.json        cached enum values
└── scripts/
    └── sheets_export.py          paginated fetch -> runs/<run-id>/ (Sheets opt-in)
```

Evals for this skill are maintained in Zevenue's private source repo and run
before every release - skill folders ship without them.

Built at [Zevenue](https://zevenue.com), a GTM engineering firm.
