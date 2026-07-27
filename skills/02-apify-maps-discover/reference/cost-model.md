# Reference · Cost model & the $10 gate

## Constants (top of `discover.py`)
```python
COST_PER_1K_PLACES = 2.10   # Step-2 doc figure (Apify page sometimes shows ~$1.50)
COST_PER_1K_EMAILS = 2.00   # add-on when --include-emails
```
Edit these to match your actual Apify account/usage tier. The doc and the public
actor page disagree on the base rate, so treat these as planning defaults.

## How the estimate is computed
```
places = (max_results / 1000) * COST_PER_1K_PLACES
emails = (max_results / 1000) * COST_PER_1K_EMAILS   # only if --include-emails
estimate = places + emails
```
`--with-review-dates` (detail-page scraping) adds real cost on Apify but isn't
modeled as a separate line yet - treat it as a meaningful multiplier on latency
and spend, and confirm against your dashboard after the first run.

## The gate
- The estimate is **always printed** before any API call.
- `--estimate-only` prints it and exits (no spend) - use it to sanity-check.
- If `estimate > $10` and you didn't pass `--yes`:
  - interactive terminal → asks `Proceed? [y/N]`
  - non-interactive (no TTY) → hard-stops with an error telling you to add `--yes`.
- Never script around the gate silently; pass `--yes` deliberately.

## Worked examples
| Run | Flags | Estimate |
|---|---|---|
| 200 places | default | ~$0.42 |
| 200 + emails | `--include-emails` | ~$0.82 |
| 500 places | default | ~$1.05 |
| 2,000 places | default | ~$4.20 |
| 2,000 + emails | `--include-emails` | ~$8.20 |
| 5,000 places | default | ~$10.50 → **gate triggers** |

## Rules of thumb
- A full Step-2 deliverable (≈2,000 rows + emails) lands around **$4–8**.
- Keep `--with-review-dates` off unless review recency is actually needed.
- Big geos: prefer one larger `max_results` run over many tiny ones (less
  per-run overhead, same per-record price).
