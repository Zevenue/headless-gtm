# TheirStack Jobs API - verified reference

Everything the script uses, plus the filter surface it doesn't expose as
flags (available via direct curl when a run needs them). Verified against the
live API on 2026-07-24 unless marked doc-only.

Contents: [Auth](#auth-and-endpoint) · [Credits](#credit-mechanics-verified) ·
[Free count](#the-free-count-recipe) · [Filters](#request-filters) ·
[Response](#response-fields) · [Curl examples](#curl-examples)

## Auth and endpoint

```
POST https://api.theirstack.com/v1/jobs/search
Authorization: Bearer $THEIRSTACK_API_KEY
Content-Type: application/json
```

Balance (undocumented but live): `GET /v0/billing/credit-balance` returns
`{ui_credits, used_ui_credits, api_credits, used_api_credits,
earliest_expiration}`.

The request fails unless it includes at least one of:
`posted_at_max_age_days`, `posted_at_gte`, `posted_at_lte`,
`company_domain_or`, `company_linkedin_url_or`, `company_name_or`.

## Credit mechanics (verified)

- **1 credit per job returned.** Verified exactly: a 2-job fetch moved
  `used_api_credits` by 2. A `limit: 25` page returning 25 jobs costs 25.
- **Blur is free ONLY without company-identifier filters.** Per the OpenAPI
  spec, blur is "not available when filtering by company identifiers"
  (`company_domain_or`, LinkedIn URL, name). The failure mode is silent:
  HTTP 200, unblurred data, billed per returned job. Verified live both
  ways - filter-only counts moved the ledger 0 across repeated 100+ -job
  totals; domain-filtered limit-1 counts billed 1 when matches existed and
  0 when the domain was quiet. `limit` has a hard minimum of 1, so a
  domain-scoped count costs ~1 credit, never 0.
- **No charge dedup.** Re-requesting jobs you already paid for charges
  again - this is why the script caches per-domain JSONs and why you never
  re-run a query "just to refresh" without intending to pay.
- **Ledger lag.** `used_api_credits` postings can land minutes late, which
  makes mid-session reads misleading. Measure spend as the settled balance
  delta in `meta.json`, taken before and after the run.
- Company Search endpoint (not used here) is 3 credits/company;
  technographics is 3 credits per company's full tech list.

## The sizing-count recipe

Exact totals for any filter set:

```json
{"...your filters...": "...",
 "blur_company_data": true,
 "include_total_results": true,
 "limit": 1, "page": 0}
```

The response `metadata` block carries `total_results` (jobs) and
`total_companies` - both, which is what makes discover-mode estimation
honest: you know the company yield before paying for a single job.

Cost of the count itself: **0 credits when no company-identifier filter is
present** (discover-style sizing). **~1 credit when `company_domain_or` is
in the body** - blur silently disables and the single limit-1 job is billed
(0 if the domains have no matches). See Credit mechanics above.

## Request filters

Flags marked ✦ are exposed by `scripts/theirstack_jobs.py`; the rest are
curl-only. All `_or` filters take arrays.

**Company scoping**
| Param | Notes |
|---|---|
| `company_domain_or` ✦ | Exact domain match - the reliable one |
| `company_domain_not` | Exclusion list |
| `company_name_or` / `company_name_partial_match_or` | Fuzzy - false-positive prone, prefer domains |
| `company_linkedin_url_or` | Alternative exact key |
| `company_country_code_or` ✦ | ISO2, company HQ |
| `min_employee_count` / `max_employee_count` ✦ | Also `_or_null` variants that keep unknown-size companies |
| `funding_stage_or` ✦ | Observed values: `seed`, `series_a`, `series_b`, `series_c`, `secondary_market` |
| `min_funding_usd` / `max_funding_usd` | Total raised bounds |
| `last_funding_round_date_gte/lte` | Date-bounded raises |

**Job scoping**
| Param | Notes |
|---|---|
| `job_title_or` ✦ | Keyword match on title, case-insensitive |
| `job_title_pattern_or/_not/_and` | Regex variants when keywords over-match |
| `job_description_contains_or` / `job_description_pattern_*` | Description text - powerful but slow queries |
| `job_seniority_or` ✦ | Observed: `junior`, `mid_level`, `senior`, `c_level` |
| `job_country_code_or` ✦ | ISO2, job location |
| `job_location_or` | Structured location objects |
| `remote` ✦ | Boolean |
| `employment_statuses_or` | Full-time / contract etc. |
| `min_salary_usd` / `max_salary_usd` | Annualized USD |
| `easy_apply`, `is_closed` | Booleans |

**Technology scoping**
| Param | Notes |
|---|---|
| `company_technology_slug_or` ✦ | Company uses the tech (e.g. `salesforce`, `hubspot`) |
| `job_technology_slug_or` | Tech named in the posting itself |
| `_not` / `_and` variants of both | |

**Freshness + paging**
| Param | Notes |
|---|---|
| `posted_at_max_age_days` ✦ | The script always sends this (default 30) |
| `posted_at_gte` / `posted_at_lte` | Absolute date bounds |
| `discovered_at_*` | When TheirStack first saw it - useful for "new since last run" |
| `limit` (default 25) / `page` (0-indexed) | Each returned job on each page is charged |
| `order_by` | Script sends `[{"field": "date_posted", "desc": true}]` |

## Response fields

Per job (the ones that matter; the payload carries more):

| Field | Notes |
|---|---|
| `job_title`, `url`, `final_url`, `source_url` | Prefer `url`, fall back `final_url` then `source_url` |
| `date_posted`, `discovered_at`, `date_reposted` | ISO dates |
| `location`, `short_location`, `countries` | `short_location` is the clean one |
| `remote`, `hybrid` | Booleans |
| `seniority` | See observed enum above |
| `employment_statuses` | Array, first entry is the main one |
| `min/max_annual_salary_usd`, `salary_string` | `salary_string` is display-ready |
| `description` | Full markdown, large - the script stores a 400-char snippet |
| `hiring_team` | Array of {name, role/title, linkedin_url} when available - a 06-resolution shortcut |
| `technology_slugs` | Tech detected for the company |
| `company_object` | Free firmographics: `name`, `employee_count`, `funding_stage`, `total_funding_usd`, `industry`, `city`, `country` |
| `has_blurred_data` | True on preview rows |

Metadata block (with `include_total_results: true`): `total_results`,
`total_companies`, `truncated_results`, `truncated_companies`.

## Curl examples

Free count - companies 50-500 hiring RevOps in the US, last 14 days:

```bash
curl -s -X POST https://api.theirstack.com/v1/jobs/search \
  -H "Authorization: Bearer $THEIRSTACK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"posted_at_max_age_days": 14,
       "job_title_or": ["Revenue Operations", "RevOps"],
       "job_country_code_or": ["US"],
       "min_employee_count": 50, "max_employee_count": 500,
       "blur_company_data": true, "include_total_results": true,
       "limit": 1}' | python3 -m json.tool | grep -A2 total
```

Paid pull - open SDR reqs at one domain (each returned job = 1 credit):

```bash
curl -s -X POST https://api.theirstack.com/v1/jobs/search \
  -H "Authorization: Bearer $THEIRSTACK_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"company_domain_or": ["stripe.com"],
       "posted_at_max_age_days": 30,
       "job_title_or": ["SDR", "BDR", "Sales Development"],
       "limit": 10,
       "order_by": [{"field": "date_posted", "desc": true}]}'
```
