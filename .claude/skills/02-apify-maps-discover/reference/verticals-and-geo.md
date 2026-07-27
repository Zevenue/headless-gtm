# Reference · Verticals & geo tuning

How to phrase `search_term` and `geo` so Compass returns the right businesses.

## Search-term phrasing
Use the term a customer would type into Google Maps — singular service noun, no
filler. Add a qualifier only when the plain term is too broad.

| Vertical | Good `search_term` | Avoid |
|---|---|---|
| Laundromats | `laundromat` | "laundry services near me" |
| Hair / beauty | `hair salon`, `nail salon`, `barber shop` | "beauty" |
| HVAC | `hvac contractor`, `air conditioning repair` | "heating and cooling solutions" |
| Fitness | `yoga studio`, `pilates studio`, `gym` | "wellness center" |
| Dental / clinics | `dental clinic`, `physiotherapy clinic` | "healthcare" |
| Auto | `auto repair shop`, `car detailing` | "automotive" |
| Food service | `coffee shop`, `pizza restaurant` | "food" |
| Pet | `pet grooming`, `veterinary clinic` | "pet services" |

Tip: run two narrow terms rather than one vague one (e.g. `nail salon` +
`hair salon`) — recall is usually higher and cleaner than `beauty salon`.

## Geo formatting
`geo` is free-text passed to `locationQuery`. Granularity controls coverage:
- **City** — `"Toronto, ON"`, `"San Diego, CA"` → tight, high-precision.
- **Region/State** — `"California"`, `"Ontario"` → broad; expect more rows, more
  noise, higher cost.
- **Neighborhood** — `"Scarborough, Toronto"` → very tight; good for dense sweeps.
- Include the province/state to avoid ambiguous city names ("London, ON" vs UK).

## Sizing `max_results`
| Goal | `max_results` |
|---|---|
| Quick smoke test | 25–50 |
| Single city list | 150–300 |
| Region / full deliverable | 1,000–2,000 |

Returning far fewer rows than asked usually means the geo is too narrow or the
term too specific — broaden one of them.

## `min_rating`
- `4.0` (default) matches the Step-2 eval and filters obvious low-quality places.
- Drop to `0`/omit when you want **full coverage** (e.g. building a TAM count)
  rather than only well-rated prospects.
- Raising to `4.5` tightens to premium operators but can miss newer businesses
  with few reviews.
