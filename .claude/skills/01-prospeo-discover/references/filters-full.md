# Prospeo Company Search — Complete 33-Filter Reference

All filters for `/search-company`. Read this when mapping user input to filter JSON.

## Table of Contents

1. [Global Constraints](#global-constraints)
2. [Filters 1-18: Free Plan](#free-plan-filters)
3. [Filters 19-24: Starter Plan](#starter-plan-filters)
4. [Filters 25-29: Growth Plan](#growth-plan-filters)
5. [Filters 30-33: Pro Plan](#pro-plan-filters)

---

## Global Constraints

| Constraint | Value |
|------------|-------|
| Max total filter values across all filters | 20,000 |
| Max include/exclude items per filter | 500 (unless noted) |
| Max page number | 1,000 |
| Results per page | 25 (fixed) |
| Must have at least one positive (include) filter | Cannot search with only exclude filters |

---

## Free Plan Filters

### 1. `company`
- `names.include` / `names.exclude`: array of strings, max 500
- `websites.include` / `websites.exclude`: array of strings (root domains, no www.)
- Combined names + websites include <= 500

### 2. `company_location_search`
- `include` / `exclude`: array of strings, max 100, 1-200 chars
- **Values MUST come from `/search-suggestions` API**

### 3. `company_headcount_range`
- Array of strings: `"1-10"`, `"11-20"`, `"21-50"`, `"51-100"`, `"101-200"`, `"201-500"`, `"501-1000"`, `"1001-2000"`, `"2001-5000"`, `"5001-10000"`, `"10000+"`
- Cannot combine with `company_headcount_custom`

### 4. `company_headcount_custom`
- `min`: 1–999,998 | `max`: 1–999,999 (must be >= min)
- Cannot combine with `company_headcount_range`

### 5. `company_industry`
- `include` / `exclude`: array of strings, max 500
- 256 valid values — check `prospeo-enums.json`

### 6. `company_keywords`
- `include` / `exclude`: array of strings, max 20, 3-100 chars each
- `include_all`: boolean — `true` = AND, `false` (default) = OR
- `search_everywhere`: boolean — `true` (default) = all sources
- `sources`: array — `"specialties"`, `"social_media_description"`, `"seo_description"`, `"ai_description"`, `"products_services"`, `"website_pages"`

### 7. `company_attributes`
- **General**: `b2b`, `demo`, `freetrial`, `downloadable`, `mobileapps`, `onlinereviews`, `pricing`, `uses_ai` — all boolean/null
- **Platform**: `has_api`, `has_chrome_extension`, `has_sso`, `has_uptime_guarantee`, `has_open_source`, `has_marketplace`
- **Content**: `has_blog`, `has_podcast`, `has_community_forum`, `has_knowledge_base`, `has_academy`, `has_affiliate_program`, `has_case_studies`, `has_testimonials`
- **Support**: `has_phone_support`, `has_email_support`, `has_chat_support`, `has_ticket_support`, `has_social_support`
- **Compliance**: `has_soc2`, `has_iso27001`, `has_gdpr`, `has_hipaa`, `has_ccpa`, `has_pci_dss`, `other_compliance` (array, max 50), `compliance_match_mode` (`"EXACT"`/`"CONTAINS"`), `has_esg_reports`
- **Presence**: `data_residency` (`"EU"`/`"US"`), `has_physical_offices`, `is_venture_backed`, `is_publicly_traded`

### 8. `company_naics`
- `include` / `exclude`: array of integers, max 100, range 1-1,000,000

### 9. `company_sics`
- `include` / `exclude`: array of integers, max 100, range 1-1,000,000

### 10. `company_type`
- `status`: `"Private"`, `"Public"`, `"Non Profit"`, `"Other"`
- `subtypes.include` / `subtypes.exclude`: 27 values — SaaS, Platform, AI/ML, FinTech, HealthTech, Marketplace, E-commerce, Agency, Consulting, Manufacturing, Media/Publisher, Education, Non-Profit, Government, Hardware, Professional Services, Data/Analytics, Franchise, Logistics, Real Estate, Legal, Insurance, Retail, Hospitality, Food & Beverage, Construction, Telecommunications
- `business_model`: `"b2b"`, `"b2c"`, `"b2b2c"`, `"d2c"`, `"marketplace"`, `"franchise"`, `"non_profit"`, `"government"`
- Boolean flags: `is_retail`, `is_marketplace`, `is_mainly_ai`, `is_mainly_crypto`, `multi_product`, `has_free_tier`, `is_self_serve`, `is_sales_led`, `has_usage_pricing`, `has_subscription`, `has_enterprise_plan`, `has_public_pricing`

### 11. `company_founded`
- `min` / `max`: 1900–current year
- `include_unknown_founded`: boolean

### 12. `company_headcount_growth`
- `timeframe_month`: `3`, `6`, `12`, or `24`
- `min` / `max`: -100 to 10,000 (percentage)
- `departments`: array of strings, max 10 — Administrative, Consulting, Customer service, Design / UI / UX, Education, Finance, General management, HR, Legal, Marketing, Medical, Operations, Product, Project management, Real estate, Research, Sales, Technical, Trades

### 13. `company_email_provider`
- Array of strings: `"Google"`, `"Microsoft"`, `"Proofpoint"`, `"Mimecast"`, `"Other"`

### 14. `company_operating_languages`
- `include`: array of strings, max 10, 50 chars each

### 15. `company_products_services`
- `products_include` / `products_exclude`: max 20/10 items, 100 chars each
- `products_match_all`: boolean (AND/OR)
- `service_tags_include` / `service_tags_exclude`: max 20/10
- `service_tags_match_all`: boolean (AND/OR)

### 16. `company_headcount_by_department`
- Array of objects, max 10
- Each: `department` (one of 14 department values), `min` (0-100,000), `max` (0-100,000)

### 17. `company_news`
- `keywords`: array, max 20, 100 chars each
- `categories`: array, max 10 — Funding & Investment, Mergers & Acquisitions, Product Launch, Partnership, Expansion, Layoffs & Restructuring, IPO, Leadership Change, Legal & Regulatory, Awards & Recognition
- `timeframe_days`: 60, 90 (default), 180, 365
- At least one of keywords or categories required

### 18. `company_intent`
- `topic_ids`: array, 1-30 items (configured in Prospeo UI)
- `in_depth_research` / `active_research` / `early_research`: boolean

---

## Starter Plan Filters

### 19. `company_revenue`
- `min` / `max`: `"<100K"`, `"100K"`, `"500K"`, `"1M"`, `"5M"`, `"10M"`, `"25M"`, `"50M"`, `"100M"`, `"250M"`, `"500M"`, `"1B"`, `"5B"`, `"10B+"`
- `include_unknown_revenue`: boolean

### 20. `company_funding`
- `stage`: array — 23 values (Angel through Undisclosed)
- `funding_date`: 30, 60, 90, 180, 270, 365 (days since last funding)
- `last_funding.min` / `last_funding.max`: revenue range values
- `total_funding.min` / `total_funding.max`: revenue range values
- `investors`: array, max 10, 100 chars each
- `was_in_accelerator`: boolean
- `accelerator_name`: string, max 100 chars (only when was_in_accelerator is true)

### 21. `company_technology`
- `include` / `exclude`: array, max 20 each
- 4,946 valid values — **resolve via `/search-suggestions`**

### 22. `company_lookalike`
- **Mode A — company_oids**: array of Prospeo company IDs, max 10
- **Mode B — icp_text**: string, max 5,000 chars
- **Mode D — domain**: string (single domain)
- `match_all`: boolean — true = intersection, false (default) = union
- `same_language`: boolean
- `minimum_tier`: `"T1"` (most similar), `"T2"`, `"T3"` (broadest, default)
- Use exactly ONE mode per call

### 23. `company_job_posting_hiring_for`
- `include` / `exclude`: array, max 500, 1-200 chars
- `match_type`: `"contains"` (default) or `"exact"`
- `boolean_search`: string, max 500 terms — cannot combine with include/exclude

### 24. `company_job_posting_quantity`
- `min` / `max`: 0–5,000

---

## Growth Plan Filters

### 25. `company_icp`
- `titles_include` / `titles_exclude`: array, max 20, 100 chars
- `company_sizes`: array — `"micro"`, `"smb"`, `"midmarket"`, `"enterprise"`, `"large_enterprise"`
- `industries`: array, max 10, 100 chars
- `geographic_markets`: array, max 10 (country name or ISO2)
- `geographic_scope`: `"single_country"` or `"multi_country"`
- `departments.include`: array, max 15 — Engineering, Sales, Marketing, Finance, HR, Operations, IT, Legal, Customer Success, Procurement, Data, Security, Design, SMB Owners, Consumers
- `departments.match_mode`: `"any"` or `"all"`
- `departments.other`: array, max 5, 100 chars

### 26. `company_key_customers`
- `include`: array, max 100, 100 chars each (include only, no exclude)

### 27. `company_integrations`
- `include` / `exclude`: array, max 20/10, 100 chars

### 28. `company_awards`
- `include`: array, max 50, 100 chars
- `match_mode`: `"EXACT"` (default) or `"CONTAINS"`

### 29. `company_headcount_by_location`
- Array of 1-10 entries
- Each: `country` (string), `min_headcount` / `max_headcount` (0-1,000,000)

---

## Pro Plan Filters

### 30. `company_key_execs`
- `event_types`: array, max 10 — CEO/CTO/CFO/COO/CMO/CRO Departed/Appointed, VP of Sales/Marketing/Engineering Departed/Appointed, Any C-Level/VP/Director Departed/Appointed
- `timeframe_days`: 60, 90 (default), 180, 365

### 31. `company_website_traffic`
- `min_monthly_visits` / `max_monthly_visits`: 0–100,000,000
- `visit_change.period`: `"monthly"`, `"quarterly"`, `"yearly"`
- `visit_change.min_change` / `max_change`: -100 to 10,000 (%)
- `top_countries`: array, max 5
- `min_country_pct` / `max_country_pct`: 0–100
- At least one criterion required

### 32. `company_website_search`
- `include_keywords` / `exclude_keywords`: array, max 10, 200 chars
- `match_mode`: `"any"` (default) or `"all"`
- `search_in`: `page_body`, `page_titles`, `urls_only`, `headings_only`, `seo_description` — all boolean
- `page_scope`: array — `"homepage"`, `"product"`, `"blog"`, `"careers"`, `"about"`
- `url_contains`: string, max 200
- Page type booleans: `has_persona_pages`, `has_industry_pages`, `has_solution_pages`, `has_careers_page`, `has_status_page`, `has_sla_page`, `has_developer_docs_page`, `has_investor_page`, `has_security_page`, `has_comparison_pages`

### 33. `company_google_discovery`
- `seo_keywords`: array, 1-100 items, 100 chars each
