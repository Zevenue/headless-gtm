# Provider Reference — AI Ark · Prospeo · Blitz · Findymail · ZeroBounce

Every key is read from an **environment variable** — never hardcode a key in a script. The skill runs with as few as one key set; any rung whose key is unset is skipped, not an error (log which rungs were skipped and why).

```python
import os
AIARK_API_KEY      = os.environ.get("AIARK_API_KEY")
PROSPEO_API_KEY    = os.environ.get("PROSPEO_API_KEY")
BLITZ_API_KEY      = os.environ.get("BLITZ_API_KEY")
FINDYMAIL_API_KEY  = os.environ.get("FINDYMAIL_API_KEY")
ZEROBOUNCE_API_KEY = os.environ.get("ZEROBOUNCE_API_KEY")
# A rung is available only if its key is truthy. Skip the rest.
```

Load them however your host provides env vars (shell export, `.env` loader, secrets manager) — the skill only cares that they're present in the environment.

---

## AI Ark — finder + pre-verified passthrough (rung 0, conditional)

- **Base URL:** `https://api.ai-ark.com/api/developer-portal/v1/`
- **Auth:** `X-TOKEN: <AIARK_API_KEY>` header (not Bearer, not `x-api-key`)
- **Key endpoints:** `POST /companies` (search), `POST /people` (search), `POST /people/export/single` (the email finder), and `GET /payments/credits` (remaining balance).
- **Email finder (docs-verified):** `POST /people/export/single` — body `{ "url": "<linkedin profile url>" }` **or** `{ "id": "<person id from People Search>" }` (exactly one of the two; both empty → 400; person or email not found → 404). Response carries the full profile plus `email.output[]` with `address`, `status` (`VALID`), `domainType`. **Billing: 1 credit per valid email (0.5 profile + 0.5 email), 0 when no valid email is found — pay-for-valid applies to THIS endpoint,** not to search. A Clay-compatible `POST /people/export/single/v2` variant returns HTTP 200 for found and unfound alike.
- **Rate limits:** ~5 req/sec, 300/min, 18,000/hour; ≤500 in-flight requests per token.
- **Advertised billing:** 1 credit per person exported *with a valid email* (0.5 profile + 0.5 email); 0 credits when no valid email is found (pay-for-valid). Auto-refund up to 10h on stuck jobs.
- **Search billing:** `POST /people` bills ~0.5 credit per returned profile; "pay-for-valid" applies to the email-export step only. Pin every search tight (domain + full name — never broad discovery), check `GET /payments/credits` before and after, and cap spend per run (default 5 credits).
- **Verification:** every returned email (SMTP + catch-all) is verified in real time by **BounceBan** — this is why passthrough emails need no re-verify.
- **Two modes:** *passthrough* (row already carries an AI Ark-verified email → accept, spend nothing) and *finder* (resolve a LinkedIn URL or person id via `/people/export/single`). Skip the whole rung if `AIARK_API_KEY` is unset.

---

## Prospeo — title-first finder (rung 1)

- **Endpoint:** `POST https://api.prospeo.io/search-person`
- **Auth:** `X-KEY` header
- **Rate limit:** ~2–2.5 req/sec (token bucket recommended)
- **Paging:** 25 results/page, up to 1000 pages
- **Billing:** **1 credit per request that *returns results*.** A request that returns nothing costs nothing — so trying extra title variants that miss is free. The cost lands only when a query returns people.

This skill uses the connected **Prospeo MCP** tools (`search_person`, `bulk_enrich_person`, `get_account_info`, `search_suggestions`) rather than raw HTTP — they wrap the same API with typed filters.

### Request shape (verified live)

```json
{
  "page": 1,
  "filters": {
    "company": { "websites": { "include": ["acme.com"] } },
    "person_job_title": {
      "include": ["Marketing Director", "Director of Marketing"],
      "match_mode": "EXACT"
    },
    "person_seniority": { "include": ["Director"] },
    "max_person_per_company": 1
  }
}
```

- **Domain scope:** `company.websites.include` (NOT `company_domain`). Falls back to `company.names.include`.
- **Title:** `person_job_title.include` is an **array** — bundle every spelling of one logical title in a single call. `match_mode` controls breadth:
  - Attempt 1 → `"EXACT"` (optionally `smart_intensity: "STRICT"`)
  - Attempt 2 → `"SIMILAR"`
  - Attempt 3 → `"CONTAINS"` (optionally `smart_intensity: "LOOSE"`) + a wider title array
- **Same-seniority guard (native!):** add `person_seniority.include` with the requested band — enum: `Founder/Owner, C-Suite, Partner, Vice President, Head, Director, Manager, Senior, Entry, Intern`. This enforces the guard *at query time*, so a broadened search can't return a different seniority (CTO vs Director). Use it on the broaden attempts especially.
- **Count:** `max_person_per_company` (1–100) = how many people per company the user asked for.

### Estimation (verified live)

- The search response includes `pagination.total_count` → the number of matching people. That powers estimation fields 1 (found), 8 (coverage %).
- Each result carries `email.status` (`VERIFIED` / `UNVERIFIED` / `UNAVAILABLE`) and `revealed: false` — an **obfuscated preview**. Count `VERIFIED` statuses for field 4 (how many have emails) **without revealing anything** (no reveal credit). `linkedin_url` is present for field 5.
- So: **`search_person` = the estimation/preview step** (1 credit/page that returns results). The **actual reveal** runs only after Gate 1 (the estimation gate) returns "yes" — via `POST /bulk-enrich-person` (below).

### Reveal — raw HTTP (verified live 2026-07)

Reveal via **`POST https://api.prospeo.io/bulk-enrich-person`** (`X-KEY` header). The body is a `data` array, one object per contact, each with an `identifier` (any string — used to match the response back) plus a resolver: a `linkedin_url` (verified working) or a `person_id` from the preview. Up to 50 per call.

```json
{ "data": [
  { "identifier": "1", "linkedin_url": "https://www.linkedin.com/in/janedoe/" },
  { "identifier": "2", "linkedin_url": "https://www.linkedin.com/in/johnroe/" }
] }
```

Response: `{ "error": false, "total_cost": <credits>, "matched": [ … ], "not_matched": [] }`. Each `matched` entry is `{ identifier, person, company }`; the revealed email is at **`matched[].person.email`** → `{ "email", "status" (VERIFIED/…), "revealed": true, "verification_method" }`. **Cost: ~1 credit per newly revealed contact; 0 for misses and for contacts already revealed on the account (Prospeo dedups).**

> ⚠️ Do **not** use `POST /enrich-person` with a bare `{ "linkedin_url": … }` — it returns `400 "Field required"`. The working reveal is `/bulk-enrich-person` with the `data` array above. The `search_person` / `bulk_enrich_person` names in this section are the **MCP** abstraction; against the raw Prospeo API, use these exact request shapes.

---

## Blitz — domain-first finder (rung 2)

- **Base:** `https://api.blitz-api.ai/v2` · **Auth:** `x-api-key` header
- **Billing:** enrichment + search are **free on Blitz's Unlimited plan** — verify your own plan before a big run; on other plans, budget per call. When free, Blitz is the cheap middle rung.
- **Two-step flow — Blitz keys on the company LinkedIn URL, not the bare domain:**
  1. `POST /enrichment/domain-to-linkedin` — body `{ "domain": "acme.com" }` → `{ found, company_linkedin_url, company_name }`
  2. `POST /search/employee-finder` — body `{ company_linkedin_url, job_level, job_function, max_results, page }` → `{ results: [...], total_pages, results_length }`
- **Native server-side filters (use these — don't filter only locally):**
  - `job_level` (seniority): `C-Team`, `VP`, `Director`, … → Blitz's same-seniority lever (parallel to Prospeo's `person_seniority`).
  - `job_function` (department) — the API ENFORCES this enum; the repo's old script used **stale** values. Current valid set: `Advertising & Marketing` · `Sales & Business Development` · `Engineering` · `Finance & Accounting` · `Human Resources` · `Information Technology` · `Legal` · `Operations` · `Manufacturing & Production` · `Purchasing` · `Research & Development` · `Customer/Client Service` · `General Business & Management` · `Healthcare & Human Services` · `Education` · `Science` · `Construction` · `Supply Chain & Logistics` · `Public Administration & Safety` · `Art, Culture and Creative Professionals` · `Other`.
- **`employee-finder` returns the person + profile but NOT the email.** Each result: `first_name, last_name, full_name, headline, linkedin_url, experiences[], education, skills, …`. Current title lives in `headline` / `experiences[0]` — there is no flat `title`/`job_title`/`email`.
- **Email step:** `POST /enrichment/email` — body `{ "person_linkedin_url": "<profile url>" }` → `{ found, email }`. Free. (The required field is **`person_linkedin_url`** — not `linkedin_url`/`profile_url`, which 422.)
- **Notes:** resolve `domain → company_linkedin_url` first. Profile data can be stale (→ LinkedIn freshness check).

---

## Findymail — email finder (rung 3) + verify

> If `FINDYMAIL_API_KEY` is missing or empty, the skill must **skip Findymail and warn the user** (don't silently drop) — never crash.

- **Base:** `https://app.findymail.com` · **Auth:** `Authorization: Bearer <FINDYMAIL_API_KEY>`
- **Find email:** `POST /api/search/name` — body `{ "name": "...", "domain": "..." }` → `{ "contact": { "email", "name", "domain", "linkedin_url", "company", "job_title", ... } }`. The email is nested under `contact` — not top-level.
  - The find route is `/api/search/name`; `POST /api/find` is not a valid route (accepts only GET/HEAD, returns 405).
- **Credits check:** `GET /api/credits` → `{ "credits", "verifier_credits", "email", "id", "pricing" }`. Use to confirm the key + remaining quota before a bulk run.
- **Verify:** `POST /api/verify` (email → status) — spends `verifier_credits` (separate pool from find credits).
- **Billing:** pay-per-valid. Find credits and verifier credits are **separate pools** — check `GET /api/credits` and top up before any large run.

---

## ZeroBounce — independent validation

- **Single validate:** `GET https://api.zerobounce.net/v2/validate?api_key=<ZEROBOUNCE_API_KEY>&email=<email>&ip_address=` (regional hosts `api-us.` / `api-eu.` also exist). Optional: `timeout` (3–60s; returns `unknown` if exceeded), `verify_plus` (deeper validation), `activity_data`.
- **Batch validate:** `POST https://api.zerobounce.net/v2/validatebatch` — JSON body `{ "api_key": "...", "email_batch": [{ "email_address": "...", "ip_address": null }] }`. Can take up to ~70s to return; **beyond ~200 emails use the Bulk File endpoints instead** (per ZeroBounce's own guidance).
- **Credits check:** `GET https://api.zerobounce.net/v2/getcredits?api_key=<key>` → `{ "Credits": N }` (`-1` = bad key). Confirm the key + quota before a bulk run.
- **Response fields:** `status`, `sub_status`, `catchall_domain`, `free_email`, `did_you_mean`, `domain_age_days`, `smtp_provider`, `mx_found`, `mx_record`, `firstname`/`lastname`, `processed_at`.
- **Verdict mapping for this skill:**
  - `status: "valid"` → `valid`
  - `status: "catch-all"` → `catch_all` (accept + flag) — an explicit status: no false "ok" on catch-all domains. `catchall_domain: true` on a `valid` result also powers the pattern-inference booster.
  - `status: "invalid"` → `invalid` (hard invalid — triggers provider retry if the gate was enabled)
  - `status: "spamtrap"` / `"abuse"` / `"do_not_mail"` → **never email** — treat as hard invalid, record `sub_status` in `note`
  - `status: "unknown"` → unverifiable (costs **0 credits**); treat as hard invalid for send-safety, optionally retry once with a longer `timeout`
- **Billing:** 1 credit per validation; **`unknown` results never consume a credit.**
- **Rate limits:** 80,000 requests per 10s (far above this skill's volume); 200+ bad-key requests in an hour → temporary block.
- **Catch-all depth:** explicit catch-all status + `verify_plus` mode for deeper Google-Workspace/O365 catch-all resolution.

---

## Billing summary (the cost model that drives the waterfall)

| Action | Cost | Confirmed? |
|--------|------|-----------|
| AI Ark search (`POST /people`) | ~0.5 credit per returned profile | bills per profile — prefer `/people/export/single` |
| AI Ark `/people/export/single` | 1 credit per valid email, 0 on a miss | ✅ |
| Prospeo search that **misses** | free | ✅ |
| Prospeo search that **returns results** | 1 credit/page | ✅ |
| Prospeo reveal (`bulk_enrich_person`) | credits | ✅ |
| Blitz domain-to-linkedin / employee-finder | free on the Unlimited plan (verify your plan) | ✅ |
| Findymail `/api/search/name` | pay-per-valid | ✅ |
| ZeroBounce validate | 1 credit/check; `unknown` free | ✅ |

Because misses are free on Prospeo, broadening via extra title variants is cheap; the rare wasted credit is a broaden attempt that *returns* an off-target person — contained by the same-seniority guard.
