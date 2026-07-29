# Company Enrich API Reference

## Endpoint

```
POST https://api.crustdata.com/company/enrich
```

## Auth

```
Authorization: Bearer {CRUSTDATA_API_KEY}
Content-Type: application/json
x-api-version: 2025-11-01
```

Both headers required - requests fail without `x-api-version`.

## Cost & Limits

- **2 credits per company** (regardless of how many field groups requested - always request all)
- **Rate limit**: 15 requests per minute
- **Timeout**: Use 90s - responses are large JSON blobs

## Request

One identifier type per request. Multiple values of the same type supported.

```json
{
  "domains": ["serverobotics.com", "prenosis.com"],
  "fields": [
    "basic_info", "headcount", "funding", "hiring", "revenue",
    "locations", "taxonomy", "followers", "people", "web_traffic",
    "seo", "employee_reviews", "competitors", "social_profiles",
    "news", "software_reviews", "reviews", "public_launches", "market_intel"
  ]
}
```

### Identifier options (use exactly one)

| Parameter | Type | Example |
|---|---|---|
| `domains` | string[] | `["serverobotics.com"]` |
| `names` | string[] | `["Serve Robotics"]` |
| `crustdata_company_ids` | int[] | `[628895]` |
| `professional_network_profile_urls` | string[] | `["https://linkedin.com/company/serverobotics"]` |

### Optional parameters

| Parameter | Type | Default | Notes |
|---|---|---|---|
| `fields` | string[] | `["crustdata_company_id", "basic_info"]` | Omitting returns only basic_info. Always pass all 19 fields since cost is the same. |
| `exact_match` | bool/null | null | Enforce strict matching. Null = auto-detection. |

## Response

```json
[
  {
    "matched_on": "serverobotics.com",
    "match_type": "domain",
    "matches": [
      {
        "confidence_score": 1,
        "company_data": {
          "crustdata_company_id": 628895,
          "updated_at": "2026-06-15T...",
          "indexed_at": "2026-06-15T...",
          "basic_info": { ... },
          "headcount": { ... },
          "funding": { ... },
          "hiring": { ... },
          "revenue": { ... },
          ...
        }
      }
    ]
  }
]
```

- No match: HTTP 200 with empty `matches` array
- Domain/ID matches: confidence_score = 1
- Name matches: confidence_score varies (higher = better match)

## Field Groups (what each returns)

### basic_info
- `name`, `primary_domain`, `all_domains`, `website`
- `professional_network_url`, `professional_network_id`, `profile_name`
- `logo_permalink`, `description`, `company_type`, `year_founded`
- `employee_count_range`, `markets`, `industries`

### headcount
- `total` (int) - current employee count
- `largest_headcount_country` (string)
- `timeseries` - array of `{date, employee_count}` (weekly, back to 2021)
- `growth_percent` - `{mom, qoq, six_months, yoy, two_years}` (NOTE: pre-computed, can be stale - compute fresh from timeseries)
- `growth_absolute` - `{mom, qoq, six_months, yoy, two_years}`
- `by_role_absolute`, `by_role_percent` - per-department headcount
- `by_region_absolute`, `by_region_percent` - per-region headcount
- `by_skill_absolute`, `by_skill_percent` - per-skill headcount
- `by_function_timeseries` - `{CURRENT_FUNCTION, GEO_REGION}` with per-dept monthly timeseries

Available departments: engineering, sales, operations, marketing, human_resources, finance, product, business_development, information_technology, support, legal, administrative, consulting, data_science, arts_and_design

### funding
- `total_investment_usd` (number)
- `last_round_amount_usd` (number)
- `last_fundraise_date` (date)
- `last_round_type` (string) - seed, series_a, series_b, venture, private_equity, post_ipo_equity, etc.
- `milestones` - array of `{date, funding_date, amount_usd, round_type, investors, lead_investors}`
- `investors` - array of investor name strings
- `investors_detailed` - array of `{name, uuid, type, categories, permalink, crunchbase_profile_url}`
- `acquisitions` - array of acquisition records
- `acquired_by` - array of `{name, crustdata_company_id, date, amount_usd}`

### hiring
- `recent_titles_csv` (string) - comma-separated recent job titles
- `openings_count` (int) - number of open job postings
- `openings_growth_percent` - `{mom, qoq, six_months, yoy}`
- `by_function_qoq_pct`, `by_function_6m_pct` - per-function hiring growth
- `open_jobs_timeseries` - array of `{date, open_jobs}`
- `recent_openings` - array of `{title, url, number_of_openings, category, description, date_added, date_updated, location_text}`

### revenue
- `estimated` - `{lower_bound_usd, upper_bound_usd, timeseries}`
- `public_markets` - `{ipo_date, stock_symbols, fiscal_year_end}`
- `acquisition_status` (string)

### people
- `decision_makers` - array of PersonProfile objects
- `founders` - array of PersonProfile objects
- `cxos` - array of PersonProfile objects
- Each PersonProfile has: basic_profile (name, headline, title, summary, location), experience (current + past employers), education, social_handles

### Other field groups
- `locations` - country, headquarters, street_address, all_office_addresses
- `taxonomy` - professional_network_industry, specialities, categories, naics_detail, sic_detail_list
- `followers` - count, timeseries, growth percentages
- `web_traffic` - monthly_visitors, traffic sources, timeseries per domain
- `seo` - organic results, ad budget, keyword rankings
- `competitors` - all_domains, paid_seo, organic_seo
- `employee_reviews` - overall_rating, culture, management, work_life_balance, ceo_rating
- `news` - array of {source, article_url, article_title, article_publish_date, confidence_score}
- `social_profiles` - crunchbase, twitter_url, professional_network
- `software_reviews` - review_count, average_rating, growth percentages
- `public_launches` - product launch data
- `market_intel` - market intelligence data

## Error Responses

| Code | Type | When |
|---|---|---|
| 400 | invalid_request | Missing identifier or invalid fields |
| 401 | unauthorized | Invalid/missing API key |
| 403 | forbidden | Enrich not permitted for this account |
| 404 | not_found | No data found |
| 500 | internal_error | Server error |

## Staleness Warning

Pre-computed growth fields (`growth_percent.yoy`, `six_months`, etc.) can be stale by 3-10+ months. Always compute fresh growth from the `timeseries` data:

```python
# Fresh YoY growth from timeseries
ts = company_data["headcount"]["timeseries"]
latest = ts[-1]["employee_count"]
year_ago = ts[-52]["employee_count"]  # 52 weeks back
yoy_pct = ((latest - year_ago) / year_ago) * 100
```
