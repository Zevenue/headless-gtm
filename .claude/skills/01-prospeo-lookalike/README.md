# prospeo-lookalike

Seed-based B2B company discovery via the [Prospeo](https://prospeo.io) `company_lookalike` API. Turns seed
domains, named companies, or an ICP description into a ranked list of similar companies - and can distil the
closest matches into an ICP for [`01-prospeo-discover`](../01-prospeo-discover/) to run.

Sibling of `01-prospeo-discover`: use **this** skill when the user starts from *example companies*; use
discover when they start from *filters*.

## What it does

- Takes seeds as one domain, multiple domains/names, or a free-text ICP description
- Resolves multiple seeds to Prospeo company IDs, picks the right lookalike mode (domain / oids / icp_text)
- **Mode 1 — lookalike list:** runs `company_lookalike` alone and returns the similar companies, ranked by
  similarity tier (no ICP stacking, which would collapse the count to single digits)
- **Mode 2 — seed → ICP handoff:** analyzes the 25 closest matches for patterns, builds an ICP, and hands it
  to `01-prospeo-discover`
- Requires a **Starter+** plan (lookalike is filter #22); guards Free-plan accounts before spending a credit
- Tracks credits and confirms cost before any export
- Python export script with batching + retries, writes `records.jsonl` in the shared chain format

## Setup

Auth comes from environment variables - no keys are stored in the skill.

```bash
export PROSPEO_API_KEY="your-prospeo-key"

# Only needed for Google Sheets export:
export GOOGLE_TOKEN_PATH="$HOME/.google/token.json"              # default if unset
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

# Standard chain export — writes runs/<run-id>/ (records.jsonl + tracker + meta)
python3 scripts/sheets_export.py --filters filters.json

# Also export to Google Sheets (opt-in)
python3 scripts/sheets_export.py --filters filters.json --sheets
python3 scripts/sheets_export.py --filters filters.json --spreadsheet-id SHEET_ID --tab-name "lookalikes"
```

`filters.json` must contain a `company_lookalike` block (plus an optional single light constraint).

## Layout

```
prospeo-lookalike/
├── SKILL.md                      workflow and instructions (Mode 1 / Mode 2)
├── references/
│   ├── lookalike-modes.md        the three modes, oid resolution, tiers, pattern analysis
│   ├── mapping-examples.md       plain-English → lookalike filter JSON
│   ├── api-curl.md               exact curl formats + search-suggestions keys
│   ├── filters-full.md           all 33 filters (for constraints / Mode 2 ICP)
│   ├── plan-filter-map.md        which filters each plan supports (lookalike = Starter+)
│   ├── enum-refresh.md           enum cache refresh procedure
│   └── prospeo-enums.json        cached enum values
└── scripts/
    └── sheets_export.py          paginated fetch -> runs/<run-id>/ (Sheets opt-in)
```

Evals for this skill are maintained in Zevenue's private source repo and run
before every release - skill folders ship without them.

Built at [Zevenue](https://zevenue.com), a GTM engineering firm.
