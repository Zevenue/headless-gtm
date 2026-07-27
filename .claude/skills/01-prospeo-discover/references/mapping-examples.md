# Plain English → Prospeo Filter Mapping Examples

20+ examples showing how to convert user input to Prospeo filter JSON.

## Location Mappings

| User says | Filter JSON |
|-----------|-------------|
| "US" / "America" / "United States" | `"company_location_search": {"include": ["United States"]}` |
| "US and UK" | `"company_location_search": {"include": ["United States", "United Kingdom"]}` |
| "Europe except France" | `"company_location_search": {"include": ["Germany", "United Kingdom", ...], "exclude": ["France"]}` |
| "Bay Area" / "SF" | `"company_location_search": {"include": ["San Francisco Bay Area"]}` - resolve via search_suggestions |
| "DACH region" | `"company_location_search": {"include": ["Germany", "Austria", "Switzerland"]}` |

> Always resolve location values via `POST /search-suggestions` with `{"location_search": "..."}` - see SKILL.md for exact curl format.

## Company Size Mappings

| User says | Filter JSON |
|-----------|-------------|
| "small companies" / "startups" | `"company_headcount_range": ["1-10", "11-20", "21-50"]` |
| "50-200 employees" | `"company_headcount_range": ["51-100", "101-200"]` |
| "mid-market" | `"company_headcount_range": ["101-200", "201-500", "501-1000"]` |
| "enterprise" | `"company_headcount_range": ["1001-2000", "2001-5000", "5001-10000", "10000+"]` |
| "exactly 75-300 employees" | `"company_headcount_custom": {"min": 75, "max": 300}` |

## Industry & Type Mappings

| User says | Filter JSON |
|-----------|-------------|
| "tech companies" | Show matching options: Industries (Software Development, IT Services, Technology Information and Internet, etc.) + Subtypes (SaaS, Platform, AI/ML, etc.). Let user pick. |
| "SaaS" | `"company_type": {"subtypes": {"include": ["SaaS"]}}` |
| "B2B SaaS" | `"company_type": {"business_model": "b2b", "subtypes": {"include": ["SaaS"]}}` |
| "AI company" | `"company_type": {"is_mainly_ai": true}` |
| "healthcare" | `"company_industry": {"include": ["Hospitals and Health Care", "Medical Practices", "Mental Health Care", "Medical Equipment Manufacturing"]}` - show options, let user pick |
| "fintech" | `"company_type": {"subtypes": {"include": ["FinTech"]}}` or `"company_industry": {"include": ["Financial Services"]}` + `"company_type": {"subtypes": {"include": ["SaaS", "Platform"]}}` |
| "exclude consulting" | `"company_industry": {"exclude": ["Business Consulting and Services", "Management Consulting"]}` |
| "software development only" | `"company_industry": {"include": ["Software Development"]}` |

## Funding Mappings

| User says | Filter JSON |
|-----------|-------------|
| "Series A" | `"company_funding": {"stage": ["Series A"]}` |
| "Series A or B" | `"company_funding": {"stage": ["Series A", "Series B"]}` |
| "raised recently" / "recently funded" | `"company_funding": {"funding_date": 365}` |
| "raised in last 6 months" | `"company_funding": {"funding_date": 180}` |
| "raised $5M-$50M total" | `"company_funding": {"total_funding": {"min": "5M", "max": "50M"}}` |
| "YC companies" | `"company_funding": {"was_in_accelerator": true, "accelerator_name": "Y Combinator"}` |
| "VC-backed" | `"company_attributes": {"is_venture_backed": true}` |

## Revenue Mappings

| User says | Filter JSON |
|-----------|-------------|
| "$1M-$10M revenue" | `"company_revenue": {"min": "1M", "max": "10M"}` |
| "pre-revenue" / "early stage" | `"company_revenue": {"min": "<100K", "max": "500K"}` |
| "over $100M" | `"company_revenue": {"min": "100M"}` |

## Growth & Signals

| User says | Filter JSON |
|-----------|-------------|
| "growing fast" | `"company_headcount_growth": {"timeframe_month": 12, "min": 20}` |
| "growing engineering team" | `"company_headcount_growth": {"timeframe_month": 12, "min": 10, "departments": ["Technical"]}` |
| "hiring engineers" | `"company_job_posting_hiring_for": {"include": ["engineer"], "match_type": "contains"}` |
| "10+ open roles" | `"company_job_posting_quantity": {"min": 10}` |
| "recently in the news" | `"company_news": {"timeframe_days": 90}` - needs keywords or categories |
| "recently acquired someone" | `"company_news": {"categories": ["Mergers & Acquisitions"], "timeframe_days": 180}` |
| "new CTO" | `"company_key_execs": {"event_types": ["CTO Appointed"], "timeframe_days": 180}` (Pro plan) |

## Technology Mappings

| User says | Filter JSON |
|-----------|-------------|
| "uses Salesforce" | `"company_technology": {"include": ["Salesforce"]}` - resolve via search_suggestions |
| "uses HubSpot but not Salesforce" | `"company_technology": {"include": ["HubSpot"], "exclude": ["Salesforce"]}` |
| "AWS stack" | `"company_technology": {"include": ["Amazon Web Services"]}` - resolve exact name via search_suggestions |

## Company Status

| User says | Filter JSON |
|-----------|-------------|
| "private companies" | `"company_type": {"status": "Private"}` |
| "public companies" | `"company_type": {"status": "Public"}` |
| "nonprofits" | `"company_type": {"status": "Non Profit"}` |
| "exclude nonprofits" | Add `"Non Profit"` to any status exclusion logic, or only set status to `"Private"` |

## Lookalike Mappings (seed → ICP)

Seeds are used to *find an ICP*, then dropped before the search - see "Seed domains → build an ICP from the
pattern" in SKILL.md. Quick reference:

| User says | Filter JSON (page-1 discovery only, then drop) |
|-----------|-------------|
| "similar to hubspot.com" | `"company_lookalike": {"domain": "hubspot.com", "minimum_tier": "T2"}` |
| "companies like Stripe and HubSpot" | Get company_oids first, then `"company_lookalike": {"company_oids": ["<id1>", "<id2>"], "match_all": false, "minimum_tier": "T2"}` |
| "very similar only" / "broad matches" | `"minimum_tier": "T1"` / `"T3"` |

> The dedicated [`01-prospeo-lookalike`](../../01-prospeo-lookalike/SKILL.md) skill goes deeper on seeds
> (returns the matches themselves, ranked, with export). Use it when the user wants the similar companies as
> the deliverable rather than an ICP - it's optional, this skill covers seed → ICP on its own.

## Attributes & Compliance

| User says | Filter JSON |
|-----------|-------------|
| "has an API" | `"company_attributes": {"has_api": true}` |
| "SOC 2 compliant" | `"company_attributes": {"has_soc2": true}` |
| "GDPR compliant" | `"company_attributes": {"has_gdpr": true}` |
| "offers free trial" | `"company_attributes": {"freetrial": true}` |
| "has public pricing" | `"company_type": {"has_public_pricing": true}` |

## Combined Examples

### Full ICP (Type 1)
User: "Find private B2B SaaS companies in the US, 50-200 employees, Series A or B, software development"

```json
{
  "company_location_search": {"include": ["United States"]},
  "company_headcount_range": ["51-100", "101-200"],
  "company_industry": {"include": ["Software Development"]},
  "company_type": {"status": "Private", "business_model": "b2b", "subtypes": {"include": ["SaaS"]}},
  "company_funding": {"stage": ["Series A", "Series B"]},
  "company_revenue": {"min": "5M", "max": "50M"}
}
```

### ICP built from a seed lookalike - no `company_lookalike` in the search
User: "Find AI companies similar to scale.ai, US, 50-500 employees, Series A-C"

Use the seed (scale.ai) to find the pattern on page 1, build the ICP, then run the final search. The
lookalike filter is never part of that final search (stacking it with a full ICP narrows results to single
digits).

**Final search filters** (no `company_lookalike`):
```json
{
  "company_location_search": {"include": ["United States"]},
  "company_headcount_range": ["51-100", "101-200", "201-500"],
  "company_type": {"status": "Private", "is_mainly_ai": true},
  "company_funding": {"stage": ["Series A", "Series B", "Series C"]},
  "company_revenue": {"min": "5M", "max": "100M"}
}
```
