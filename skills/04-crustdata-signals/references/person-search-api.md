# Person Search API Reference

## Endpoint

```
POST https://api.crustdata.com/person/search
```

## Auth

```
Authorization: Bearer {CRUSTDATA_API_KEY}
Content-Type: application/json
x-api-version: 2025-11-01
```

## Cost & Limits

- **0.03 credits per result returned** (e.g. 20 results = 0.6 credits)
- **Rate limit**: 30 requests per minute
- **Max limit per request**: 1000

## Primary Use Case: Recent Hires by Domain

Find people who joined a specific company in the last N days.

### Key Filters

| Filter field | What it does |
|---|---|
| `experience.employment_details.current.company_website_domain` | Scope to a specific company domain |
| `experience.employment_details.current.start_date` | Filter by when they started current role |
| `experience.employment_details.current.title` | Filter by current job title |
| `experience.employment_details.current.seniority_level` | Filter by seniority |
| `recently_changed_jobs` | Boolean - recently switched jobs |

### Example: People who joined example.com in last 180 days

```json
{
  "filters": {
    "op": "and",
    "conditions": [
      {
        "field": "experience.employment_details.current.company_website_domain",
        "type": "=",
        "value": "example.com"
      },
      {
        "field": "experience.employment_details.current.start_date",
        "type": ">",
        "value": "2026-01-04"
      }
    ]
  },
  "fields": [
    "basic_profile.name",
    "basic_profile.headline",
    "basic_profile.location",
    "experience.employment_details.current.title",
    "experience.employment_details.current.start_date",
    "experience.employment_details.current.seniority_level",
    "experience.employment_details.current.name",
    "experience.employment_details.current.function_category"
  ],
  "sorts": [
    {"field": "experience.employment_details.start_date", "order": "desc"}
  ],
  "limit": 100
}
```

## Request Schema

```json
{
  "filters": { },
  "fields": ["string"],
  "sorts": [{"field": "string", "order": "asc|desc"}],
  "limit": 1-1000,
  "cursor": "string",
  "post_processing": {
    "exclude_profiles": ["url"],
    "exclude_names": ["string"]
  }
}
```

### Filter operators

| Operator | Value type | Purpose |
|---|---|---|
| `=` | scalar | Exact match |
| `!=` | scalar | Not equal |
| `<` | number/date | Less than |
| `>` | number/date | Greater than |
| `=<` | number/date | Less than or equal |
| `=>` | number/date | Greater than or equal |
| `in` | array | Value in list |
| `not_in` | array | Value not in list |
| `(.)` | string | Regex/contains (case-insensitive) |
| `[.]` | string | Substring match |

### Filter groups (AND/OR)

```json
{
  "op": "and",
  "conditions": [
    {"field": "...", "type": "=", "value": "..."},
    {"field": "...", "type": ">", "value": "..."}
  ]
}
```

## All Filterable Fields

### Current employer fields (most relevant for this skill)
- `experience.employment_details.current.company_name`
- `experience.employment_details.current.company_website_domain`
- `experience.employment_details.current.company_id`
- `experience.employment_details.current.title`
- `experience.employment_details.current.seniority_level`
- `experience.employment_details.current.function_category`
- `experience.employment_details.current.start_date`
- `experience.employment_details.current.company_headcount_latest`
- `experience.employment_details.current.company_headcount_range`
- `experience.employment_details.current.company_industries`
- `experience.employment_details.current.company_type`
- `experience.employment_details.current.company_headquarters_country`
- `experience.employment_details.current.company_hq_location`
- `experience.employment_details.current.employment_type`
- `experience.employment_details.current.years_at_company_raw`

### Basic profile fields
- `basic_profile.name`, `basic_profile.first_name`, `basic_profile.last_name`
- `basic_profile.headline`, `basic_profile.summary`
- `basic_profile.location` (sub-fields: city, state, country, continent, full_location)
- `basic_profile.normalized_title.department`, `.sub_department`, `.matched_title`

### Other useful fields
- `recently_changed_jobs` - boolean, recently switched jobs
- `years_of_experience`, `years_of_experience_raw`
- `professional_network.connections`, `professional_network.followers`

## Response Schema

```json
{
  "profiles": [
    {
      "crustdata_person_id": 12345,
      "basic_profile": {
        "name": "Jane Smith",
        "first_name": "Jane",
        "last_name": "Smith",
        "headline": "VP Engineering at ExampleCo",
        "location": {"city": "San Francisco", "state": "California", "country": "US"}
      },
      "experience": {
        "employment_details": {
          "current": [
            {
              "company_name": "ExampleCo",
              "title": "VP Engineering",
              "start_date": "2026-03-15",
              "seniority_level": "VP",
              "function_category": "Engineering",
              "company_website_domain": "example.com"
            }
          ]
        }
      }
    }
  ],
  "next_cursor": "...",
  "total_count": 42
}
```

## Sortable Fields

- `crustdata_person_id`
- `metadata.updated_at`
- `basic_profile.name`, `basic_profile.location.*`
- `professional_network.connections`, `professional_network.followers`
- `experience.employment_details.start_date`
- `experience.employment_details.company_headcount_latest`
- `experience.employment_details.years_at_company_raw`
- `recently_changed_jobs`
- `years_of_experience_raw`

## Pagination

Cursor-based. Use `next_cursor` from response in next request.

```python
cursor = None
all_profiles = []
while True:
    payload["cursor"] = cursor
    resp = requests.post(URL, headers=HEADERS, json=payload)
    data = resp.json()
    profiles = data.get("profiles", [])
    all_profiles.extend(profiles)
    cursor = data.get("next_cursor")
    if not cursor or not profiles:
        break
```

## Error Responses

| Code | Type | When |
|---|---|---|
| 400 | invalid_request | Unsupported field, wrong operator, malformed filters |
| 401 | unauthorized | Invalid/missing API key |
| 403 | forbidden | Permission denied or insufficient credits |
| 500 | internal_error | Server error (retry with backoff) |
