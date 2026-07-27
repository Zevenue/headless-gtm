# Prospeo Lookalike — Modes, Resolution, and Pattern Analysis

Everything about the `company_lookalike` filter (filter #22) in one place. Read this before running a
lookalike search for the first time in a session.

## Table of contents

1. [Filter shape](#filter-shape)
2. [The three input modes](#the-three-input-modes)
3. [Resolving domains to company IDs](#resolving-domains-to-company-ids)
4. [Tiers and match_all](#tiers-and-match_all)
5. [Mode 1 — lookalike list](#mode-1--lookalike-list)
6. [Mode 2 — seed → ICP pattern analysis](#mode-2--seed--icp-pattern-analysis)
7. [Why not stack lookalike with a full ICP](#why-not-stack-lookalike-with-a-full-icp)

---

## Filter shape

`company_lookalike` is a Starter+ filter. It goes inside the standard `"filters": {}` wrapper:

```json
{
  "filters": {
    "company_lookalike": {
      "domain": "hubspot.com",
      "minimum_tier": "T2"
    }
  },
  "page": 1
}
```

Constraints:

- **Exactly ONE input mode per call** - `domain`, `company_oids`, or `icp_text`. Never combine them.
- `minimum_tier`: `"T1"` (most similar) / `"T2"` / `"T3"` (broadest, default).
- `match_all`: boolean - only meaningful with `company_oids` (multi-seed). `false` (default) = union,
  `true` = intersection.
- `same_language`: boolean - restrict to companies operating in the same language as the seed(s).

## The three input modes

| Mode | Key | Value | When |
|---|---|---|---|
| **A — domain** | `domain` | single domain string, e.g. `"stripe.com"` | one seed company |
| **B — company_oids** | `company_oids` | array of Prospeo company IDs, max 10 | multiple seeds / named companies |
| **D — icp_text** | `icp_text` | free-text description, max 5,000 chars | no seed domain, just a description of the ideal company |

> Modes are labelled A/B/D to match Prospeo's own docs (there is no public "C"). Use exactly one.

### Mode A — domain (single seed)

```json
{"company_lookalike": {"domain": "hubspot.com", "minimum_tier": "T2"}}
```

Fastest path - no lookup, no credit spent resolving. Use whenever there's exactly one seed domain.

### Mode B — company_oids (multiple seeds)

```json
{"company_lookalike": {"company_oids": ["<id1>", "<id2>"], "match_all": false, "minimum_tier": "T2"}}
```

Resolve each domain/name to a company ID first (see below). Max 10 IDs. `match_all: false` unions each
seed's lookalikes (broader, usually what you want); `true` intersects (companies similar to *all* seeds).

### Mode D — icp_text (no seed domain)

```json
{"company_lookalike": {"icp_text": "Series A robotics companies building autonomous vehicle perception stacks, US-based, 50-200 employees", "minimum_tier": "T2"}}
```

Use when the user describes the ideal company in prose instead of pointing at examples. Prospeo's semantic
search interprets the text. Keep it concrete - industry, what they build, size, geo, stage.

## Resolving domains to company IDs

Mode B needs Prospeo company IDs, not domains. Resolve each seed by searching the `company` filter on its
website (1 credit per search page):

```bash
curl -s -X POST "https://api.prospeo.io/search-company" \
  -H "X-KEY: $PROSPEO_API_KEY" -H "Content-Type: application/json" \
  -d '{"filters": {"company": {"websites": {"include": ["torc.ai"]}}}, "page": 1}'
```

Read the company ID off the first result in `results` (the identifier field on the company object - commonly
`id` / `oid`; inspect the response object and use the ID Prospeo returns). Collect one ID per seed, then run
the lookalike in Mode B.

Tip: a single domain never needs this - use Mode A directly and skip the credit.

## Tiers and match_all

| Setting | Effect | Use when |
|---|---|---|
| `minimum_tier: "T1"` | tightest similarity, fewest results | you want only near-identical companies |
| `minimum_tier: "T2"` | balanced | default for a usable list |
| `minimum_tier: "T3"` | broadest, most results | seeds are niche and T1/T2 return too few |
| `match_all: false` | union of every seed's lookalikes | most multi-seed runs (broader net) |
| `match_all: true` | only companies similar to ALL seeds | seeds share a tight profile and you want the overlap |

Start at T2 / `match_all: false`. Tighten to T1 or `match_all: true` if the list is too broad; loosen to T3
if it's too thin.

## Mode 1 — lookalike list

The lookalike matches ARE the deliverable. Run `company_lookalike` as the only filter (or plus a single
light constraint the user explicitly asked for, e.g. a location), page through, export. Results come back
most-similar-first, so the tier + row order is the ranking. This is the direct answer to "find companies
like X" and is exactly what `01-prospeo-discover` avoids doing - here it's the point.

You may layer a **light** constraint (one of: `company_location_search`, `company_headcount_range`) when the
user is explicit ("similar to Stripe, but only in the US"). Do NOT layer a full ICP stack - see the last
section for why.

## Mode 2 — seed → ICP pattern analysis

When the user wants *who to target* rather than *this exact list*, mine the 25 closest matches for an ICP:

1. Fetch page 1 only (25 results, 1 credit). Each result already carries industry, headcount, location,
   funding, revenue, and keywords.
2. Tally patterns across the mandatory ICP filters:
   - **Industries** - the 2-4 dominant `company_industry` values
   - **Size** - the typical `company_headcount_range` band(s)
   - **Location** - country / region concentration
   - **Funding** - common stages, whether most are funded at all
   - **Revenue** - the rough band
   - **Keywords** - recurring specialty / description terms
3. Present the pattern-built ICP as a filter set and let the user confirm or adjust.
4. Hand the confirmed ICP to `01-prospeo-discover` for the real search.

**Broad-industry overshoot.** If the seeds are niche (robotics, autonomy) but sit under a huge parent
industry like `Software Development`, an industry + size + geo ICP can balloon to six figures - the
keywords carried the specificity and the plain firmographic ICP drops them. Sanity-check the page-1 count:
if it's tens of thousands, add the 1-2 dominant recurring keywords as a `company_keywords` constraint, or
keep only the niche industry. Observed: robotics seeds → `Software Development + Robotics Engineering`
(US/Canada) ≈ 138K; `Robotics Engineering` alone ≈ 980; `+ keyword "robotics"` ≈ 1,491. Aim for the low
thousands.

Example presentation:

> From the 25 closest matches to torc.ai + field.ai:
> - **Industry:** Software Development (14), Automation Machinery Mfg (6)
> - **Size:** mostly 51-200 employees
> - **Location:** 80% United States
> - **Funding:** Series A-C; only 3 had no funding data
> - **Keywords:** "autonomous", "perception", "robotics", "AI"
>
> ICP I'd build from this: US · 51-200 employees · Software Development + Automation · Series A-C · private.
> Confirm and I'll hand it to prospeo-discover for the full list.

## Why not stack lookalike with a full ICP

Stacking `company_lookalike` on top of a full ICP filter set (industry + size + geo + funding + revenue)
intersects two already-narrow sets and collapses the count to single digits. That's why `01-prospeo-discover`
runs lookalike only for pattern discovery and then drops it.

In THIS skill:

- **Mode 1** keeps lookalike as the primary filter and only ever adds one light constraint - so the list
  stays large enough to be useful.
- **Mode 2** doesn't stack at all - it converts the lookalike patterns into an ICP and lets discovery run
  that ICP without any lookalike filter.

If a user insists on stacking lookalike with a full ICP, allow it but restate the trade-off: expect very few
results.
