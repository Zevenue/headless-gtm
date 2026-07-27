# Prospeo API — Exact Curl Formats

Read this when you need the precise request shapes, the full search-suggestions key table, or the wrong formats to avoid. All calls use direct HTTP via curl with the `X-KEY: $PROSPEO_API_KEY` header. Don't use MCP tools for Prospeo - the MCP abstraction uses different field names that fail against the raw API (see "Formats to avoid" below).

## Table of contents

1. [account-information](#1-get-account-information-free)
2. [search-company](#2-post-search-company-1-creditpage)
3. [search-suggestions](#3-post-search-suggestions-free)
4. [Search-suggestions key table](#search-suggestions-key-table)
5. [Formats to avoid](#formats-to-avoid)
6. [API docs](#api-docs)

---

## 1. GET /account-information (free)

```bash
curl -s -H "X-KEY: $PROSPEO_API_KEY" "https://api.prospeo.io/account-information"
```

Response (read `current_plan` and `remaining_credits` from `response`):

```json
{"error": false, "response": {"current_plan": "PRO", "remaining_credits": 64523}}
```

## 2. POST /search-company (1 credit/page)

Filters go inside a `"filters": {}` wrapper. `"page"` is a sibling of `"filters"`, not inside it.

```bash
curl -s -X POST "https://api.prospeo.io/search-company" \
  -H "X-KEY: $PROSPEO_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "company_location_search": {"include": ["United States"]},
      "company_headcount_range": ["11-20", "21-50"],
      "company_industry": {"include": ["Software Development"]},
      "company_type": {"status": "Private", "business_model": "b2b"}
    },
    "page": 1
  }'
```

Response shape:

```json
{"results": [...], "pagination": {"current_page": 1, "total_page": 80, "total_count": 1991}}
```

## 3. POST /search-suggestions (free)

Rate limit 15 req/sec. Send exactly ONE search key per request, minimum 2 characters. This is how you resolve any value you're unsure of - especially locations and technologies, which are too large to cache.

```bash
# Location
curl -s -X POST "https://api.prospeo.io/search-suggestions" \
  -H "X-KEY: $PROSPEO_API_KEY" -H "Content-Type: application/json" \
  -d '{"location_search": "united states"}'

# Technology
curl -s -X POST "https://api.prospeo.io/search-suggestions" \
  -H "X-KEY: $PROSPEO_API_KEY" -H "Content-Type: application/json" \
  -d '{"technology_search": "hubspot"}'

# Industry
curl -s -X POST "https://api.prospeo.io/search-suggestions" \
  -H "X-KEY: $PROSPEO_API_KEY" -H "Content-Type: application/json" \
  -d '{"industry_search": "software"}'

# Job title
curl -s -X POST "https://api.prospeo.io/search-suggestions" \
  -H "X-KEY: $PROSPEO_API_KEY" -H "Content-Type: application/json" \
  -d '{"job_title_search": "sales development"}'

# NAICS (by code prefix or label text)
curl -s -X POST "https://api.prospeo.io/search-suggestions" \
  -H "X-KEY: $PROSPEO_API_KEY" -H "Content-Type: application/json" \
  -d '{"naics_search": "5132"}'

# Company filter field (investors, integrations, awards, etc.)
curl -s -X POST "https://api.prospeo.io/search-suggestions" \
  -H "X-KEY: $PROSPEO_API_KEY" -H "Content-Type: application/json" \
  -d '{"company_funding_investors_search": "sequoia"}'
```

### Search-suggestions key table

Each value type uses its own body key and returns its own response key.

| To resolve | Body key | Response key |
|-----------|----------|-------------|
| Locations | `location_search` | `location_suggestions` → `[{"name": "...", "type": "COUNTRY/STATE/CITY/ZONE"}]` |
| Technologies | `technology_search` | `technology_suggestions` → `["HubSpot", ...]` |
| Industries | `industry_search` | `industry_suggestions` → `["Software Development", ...]` |
| Job titles | `job_title_search` | `job_title_suggestions` |
| NAICS codes | `naics_search` | `naics_suggestions` → `[{"code": "5132", "label": "..."}]` |
| SIC codes | `sic_search` | `sic_suggestions` → `[{"code": "7371", "label": "..."}]` |
| Integrations | `company_integrations_search` | `company_integrations_suggestions` |
| Awards | `company_awards_search` | `company_awards_suggestions` |
| Compliance | `company_awards_compliance_search` | `company_awards_compliance_suggestions` |
| Key customers | `company_key_customers_search` | `company_key_customers_suggestions` |
| Investors | `company_funding_investors_search` | `company_funding_investors_suggestions` |
| Accelerators | `company_funding_accelerator_search` | `company_funding_accelerator_suggestions` |
| Operating languages | `company_operating_languages_search` | `company_operating_languages_suggestions` |
| SEO keywords | `company_google_discovery_search` | `company_google_discovery_suggestions` |
| Products | `company_products_services_products_search` | `company_products_services_products_suggestions` |
| Services | `company_products_services_services_search` | `company_products_services_services_suggestions` |
| ICP titles | `company_icp_titles_search` | `company_icp_titles_suggestions` |
| ICP industries | `company_icp_industries_search` | `company_icp_industries_suggestions` |
| ICP geo markets | `company_icp_geographic_markets_search` | `company_icp_geographic_markets_suggestions` |
| ICP departments | `company_icp_other_departments_search` | `company_icp_other_departments_suggestions` |
| Headcount by location | `company_headcount_by_location_search` | `company_headcount_by_location_suggestions` |
| Traffic countries | `company_website_traffic_countries_search` | `company_website_traffic_countries_suggestions` |

## Formats to avoid

These are MCP-server shapes that don't work against the raw API:

- `{"type": "location", "query": "..."}` - wrong, MCP abstraction
- `{"filter_id": "company_location_search", "query": "..."}` - wrong, local MCP server format
- `{"filter": "location", "query": "..."}` - wrong field names

Send exactly one search key per request, minimum 2 characters.

## API docs

- Search suggestions: https://prospeo.io/api-docs/search-suggestions
- Search company: https://prospeo.io/api-docs/search-company
- Filters documentation: https://prospeo.io/api-docs/filters-documentation
- Enum values: https://prospeo.io/api-docs/enum
