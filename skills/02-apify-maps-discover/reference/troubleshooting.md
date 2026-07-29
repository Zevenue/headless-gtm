# Reference · Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ERROR: environment variable APIFY_API_TOKEN is not set` | token not exported | `export APIFY_API_TOKEN=...` (Apify Console → Settings → Integrations) |
| `ModuleNotFoundError: requests` | deps not installed | `pip install -r ../headless-gtm-shared/requirements.txt` (use a venv) |
| `Apify error 401` | bad/expired token | regenerate the token; check you copied it whole |
| `Apify error 402` / insufficient credit | account out of credit | top up, or lower `--max-results` |
| `Apify error 429` | rate limited | wait and retry; reduce concurrency / run size |
| Run hangs then fails ~300s | sync endpoint timeout on a big pull | reduce `--max-results`, or use the async pattern in [compass-actor.md](compass-actor.md) |
| Zero / very few rows | geo too narrow or term too specific | broaden `--geo`, simplify `--search-term`, lower `--min-rating` - see [verticals-and-geo.md](verticals-and-geo.md) |
| Lots of rows, missing websites/emails | many SMBs simply have no site | expected; `domain` will be blank - dedup falls back to name+city |
| `last_review_date` always blank | `--with-review-dates` not set, or field name differs | pass the flag; if still blank, verify the actor's review field name and update `_extract_last_review_date` in `discover.py` |
| Estimate looks wrong | pricing constants stale | edit `COST_PER_1K_*` at the top of `discover.py` - see [cost-model.md](cost-model.md) |
| Gate blocks a non-interactive run | estimate > $10 and no TTY | re-run with `--yes` (deliberately) |

## Sanity checklist before a big run
1. `--estimate-only` first - confirm the number.
2. Token set, deps installed, venv active.
3. Start with a 25-row smoke test on the same query.
4. Then scale `--max-results` up.

## Field-shape caveat
The raw→normalized mapping (see [output-schema.md](output-schema.md)) targets the
Compass output as documented. Actors evolve - if a column comes back empty that
shouldn't, dump one raw item and confirm the source field name, then adjust the
adapter in `discover.py`.
