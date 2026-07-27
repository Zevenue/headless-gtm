# Reference · Apify Compass actor

Everything about the underlying actor this skill wraps.

## Identity
- **Actor:** `compass~crawler-google-places` (the "Compass" Google Maps scraper).
- **Auth:** `APIFY_API_TOKEN` — Apify Console → Settings → Integrations → API tokens.
- **Client SDKs (optional):** `apify-client` (Python / JS). This skill calls REST
  directly so no SDK is required.

## Endpoints
**Sync (used by the skill — returns dataset items in one call, ≤300s):**
```
POST https://api.apify.com/v2/acts/compass~crawler-google-places/run-sync-get-dataset-items?token=<APIFY_API_TOKEN>
Content-Type: application/json
<JSON input body>
```

**Async (for large/slow jobs that may exceed the 300s sync ceiling):**
```
POST https://api.apify.com/v2/acts/compass~crawler-google-places/runs?token=<TOKEN>
→ returns { data: { id, defaultDatasetId } }
GET  https://api.apify.com/v2/actor-runs/<id>?token=<TOKEN>           # poll status
GET  https://api.apify.com/v2/datasets/<defaultDatasetId>/items?token=<TOKEN>  # fetch
```
Prefer the header form `Authorization: Bearer <TOKEN>` over `?token=` in production
so the token doesn't land in logs.

## Input schema (fields the skill sets, plus useful extras)
| Field | Type | Used by skill | Notes |
|---|---|---|---|
| `searchStringsArray` | string[] | ✅ `--search-term` | one or more queries |
| `locationQuery` | string | ✅ `--geo` | free-text area ("California") |
| `maxCrawledPlacesPerSearch` | int | ✅ `--max-results` | per search term |
| `placeMinimumStars` | enum string | ✅ `--min-rating` | one of `""`, `two`, `twoAndHalf`, `three`, `threeAndHalf`, `four`, `fourAndHalf` - NOT a number (a float 400s the run). `build_input()` floor-maps the numeric `--min-rating` to the nearest step (4.2 → `four`); below 2.0 the filter is dropped. |
| `language` | string | ✅ ("en") | result language |
| `skipClosedPlaces` | bool | ✅ true | drop closed listings |
| `scrapeContacts` | bool | ✅ `--include-emails` | emails + socials, +cost |
| `scrapePlaceDetailPage` | bool | ✅ `--with-review-dates` | visits each detail page |
| `categoryFilterWords` | string[] | — | tighten by category |
| `website` | string | — | "withWebsite" / "withoutWebsite" filter |
| `maxImages` | int | — | leave 0 to skip images (cost) |
| `reviewsSort` | string | — | only relevant when scraping reviews |

## Raw output fields (per place)
`title`, `address` (+ `street`, `city`, `state`, `postalCode`, `countryCode`),
`phone`, `website`, `location{ lat, lng }`, `totalScore`, `reviewsCount`,
`categoryName` / `categories[]`, `placeId`, `cid`, `permanentlyClosed`,
`temporarilyClosed`, `openingHours`, `imageUrls`, `url` (Maps URL). With
`scrapeContacts`: `emails[]`, `phones[]`, social handles. With
`scrapePlaceDetailPage`: richer per-place data including review metadata.

## Limits & behaviour
- No fixed per-query result cap — you bound it with `maxCrawledPlacesPerSearch`.
- Real coverage is still limited by what Google actually lists for that query/geo.
- Sync endpoint times out at ~300s; switch to async for big pulls.
- Email/contacts and detail-page scraping each add cost and latency — keep off
  unless asked. See [cost-model.md](cost-model.md).
