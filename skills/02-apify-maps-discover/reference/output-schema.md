# Reference · Output schema (normalized ProspectRecord)

Every tool in the Step-2 stack normalizes to this one record so outputs are
comparable and dedup-able. Defined in [`../../_shared/schema.py`](../../_shared/schema.py).

## The 15 fields
| Field | Type | Source (Compass) | Notes |
|---|---|---|---|
| `name` | str | `title` | trimmed |
| `domain` | str | derived from `website` | bare host, no scheme/www - **dedup key** |
| `website` | str | `website` | original URL |
| `phone` | str | `phone` | as returned |
| `full_address` | str | `address` | single-line |
| `city` | str | `city` | |
| `region` | str | `state` | province/state |
| `rating` | float\|null | `totalScore` | 0–5 |
| `reviews_count` | int\|null | `reviewsCount` | |
| `latitude` | float\|null | `location.lat` | |
| `longitude` | float\|null | `location.lng` | |
| `place_id` | str | `placeId` | tool-specific id |
| `category` | str | `categoryName` / `categories[0]` | |
| `last_review_date` | str | detail page only | blank unless `--with-review-dates` |
| `source` | str | constant `"apify"` | which tool produced the row |

## Derivation rules
- **domain** = `domain_from_url(website)` → lowercased host, strips scheme,
  `www.`, port, and any `user@`. Empty string when there's no website.
- **dedup_key** (cross-tool) = `domain` → else `name+city` (normalized) →
  else `place_id`. `place_id` is last on purpose: each tool mints its own, so
  keying on it would stop the same business merging across tools.
- **type coercion**: ratings/lat/lng → float, reviews_count → int; bad/empty
  values become `null` rather than throwing.

## Sample row (JSON)
```json
{
  "name": "Sunrise Yoga",
  "domain": "sunriseyoga.com",
  "website": "https://www.sunriseyoga.com",
  "phone": "+1 213-555-0148",
  "full_address": "144 5th St, Los Angeles, CA 90013",
  "city": "Los Angeles",
  "region": "CA",
  "rating": 4.8,
  "reviews_count": 312,
  "latitude": 34.0407,
  "longitude": -118.2468,
  "place_id": "ChIJ....",
  "category": "Yoga studio",
  "last_review_date": "",
  "source": "apify"
}
```

## CSV
Same 15 columns in the order above, header row included. Written next to the JSON
as `runs/<slug>.csv`. Empty optional values render as blank cells.
