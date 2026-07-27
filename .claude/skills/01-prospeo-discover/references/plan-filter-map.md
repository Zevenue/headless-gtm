# Plan → Filter Availability Map

Which Prospeo filters are available on each plan. The skill reads this to gate filter recommendations.

## Filter Table

| # | Filter | Free | Starter | Growth | Pro |
|---|--------|:----:|:-------:|:------:|:---:|
| 1 | `company` (names, websites) | Y | Y | Y | Y |
| 2 | `company_location_search` | Y | Y | Y | Y |
| 3 | `company_headcount_range` | Y | Y | Y | Y |
| 4 | `company_headcount_custom` | Y | Y | Y | Y |
| 5 | `company_industry` | Y | Y | Y | Y |
| 6 | `company_keywords` | Y | Y | Y | Y |
| 7 | `company_attributes` | Y | Y | Y | Y |
| 8 | `company_naics` | Y | Y | Y | Y |
| 9 | `company_sics` | Y | Y | Y | Y |
| 10 | `company_type` | Y | Y | Y | Y |
| 11 | `company_founded` | Y | Y | Y | Y |
| 12 | `company_headcount_growth` | Y | Y | Y | Y |
| 13 | `company_email_provider` | Y | Y | Y | Y |
| 14 | `company_operating_languages` | Y | Y | Y | Y |
| 15 | `company_products_services` | Y | Y | Y | Y |
| 16 | `company_headcount_by_department` | Y | Y | Y | Y |
| 17 | `company_news` | Y | Y | Y | Y |
| 18 | `company_intent` | Y | Y | Y | Y |
| 19 | `company_revenue` | - | Y | Y | Y |
| 20 | `company_funding` | - | Y | Y | Y |
| 21 | `company_technology` | - | Y | Y | Y |
| 22 | `company_job_posting_hiring_for` | - | Y | Y | Y |
| 23 | `company_job_posting_quantity` | - | Y | Y | Y |
| 24 | `company_lookalike` | - | Y | Y | Y |
| 25 | `company_icp` | - | - | Y | Y |
| 26 | `company_key_customers` | - | - | Y | Y |
| 27 | `company_integrations` | - | - | Y | Y |
| 28 | `company_awards` | - | - | Y | Y |
| 29 | `company_headcount_by_location` | - | - | Y | Y |
| 30 | `company_key_execs` | - | - | - | Y |
| 31 | `company_website_traffic` | - | - | - | Y |
| 32 | `company_website_search` | - | - | - | Y |
| 33 | `company_google_discovery` | - | - | - | Y |

## Summary

| Plan | Total Filters | Added Over Previous |
|------|:------------:|---------------------|
| **Free** | 18 | Base set |
| **Starter** | 24 | +revenue, funding, technology, lookalike, job postings (hiring_for, quantity) |
| **Growth** | 29 | +icp, key_customers, integrations, awards, headcount_by_location |
| **Pro** | 33 | +key_execs, website_traffic, website_search, google_discovery |

## Impact on Mandatory Filters

| Plan | Mandatory Filters | Notes |
|------|:-----------------:|-------|
| **Free** | 3 | Location, Company Size, Industry/Keywords/Subtype. Status defaults to Private. Revenue NOT available. |
| **Starter+** | 5 | Location, Company Size, Industry/Keywords/Subtype, Status, Revenue |

## Impact on User Types

- **Free plan**: Types 3, 4, 5 (lookalike modes) are NOT available. Only Types 1 and 2.
- **Starter+**: All 5 user types available.
