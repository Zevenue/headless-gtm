# Plain English → Prospeo Lookalike Filter Mapping

How to convert seed-based requests into `company_lookalike` filter JSON. For the full mode reference (oid
resolution, tiers, pattern analysis) see `lookalike-modes.md`. For non-lookalike ICP filters you might layer
on or build in Mode 2, see `mapping-examples` patterns in the sibling `01-prospeo-discover` skill and
`filters-full.md`.

## Seed → mode selection

| User says | Mode | Filter JSON |
|-----------|------|-------------|
| "similar to hubspot.com" | domain | `"company_lookalike": {"domain": "hubspot.com", "minimum_tier": "T2"}` |
| "companies like Stripe" (one name) | domain | Resolve the name's domain, then `{"domain": "stripe.com", "minimum_tier": "T2"}` |
| "companies like Stripe and HubSpot" | company_oids | Resolve both to IDs, then `{"company_oids": ["<id1>", "<id2>"], "match_all": false, "minimum_tier": "T2"}` |
| "lookalikes of torc.ai, field.ai, waymo.com" | company_oids | Resolve all three to IDs, then oid mode, `match_all: false` |
| "find companies like our closed-won list" (domains pasted) | company_oids | Resolve each (max 10) to IDs, oid mode |
| "companies that look like [prose description]" | icp_text | `{"icp_text": "<description>", "minimum_tier": "T2"}` |

## Tier tuning

| User says | Setting |
|-----------|---------|
| "very similar only" / "closest matches" | `"minimum_tier": "T1"` |
| (default, balanced) | `"minimum_tier": "T2"` |
| "broad matches" / "cast a wide net" | `"minimum_tier": "T3"` |

## match_all (multi-seed only)

| User says | Setting |
|-----------|---------|
| "similar to any of these" (default) | `"match_all": false` |
| "similar to ALL of these at once" / "the overlap" | `"match_all": true` |

## Same-language restriction

| User says | Setting |
|-----------|---------|
| "keep it English-speaking / same language as the seeds" | `"same_language": true` |

## Light constraints you MAY layer (Mode 1 only)

Only when the user is explicit, and only ONE of these - never a full ICP stack (it collapses the count).

| User says | Add alongside company_lookalike |
|-----------|--------------------------------|
| "similar to Stripe but US only" | `"company_location_search": {"include": ["United States"]}` - resolve via search_suggestions |
| "like HubSpot, but 50-200 employees" | `"company_headcount_range": ["51-100", "101-200"]` |

## Worked examples

### Single seed, direct list (Mode 1)
User: "Find companies similar to hubspot.com"

```json
{
  "company_lookalike": {"domain": "hubspot.com", "minimum_tier": "T2"}
}
```
Run page 1, present the ranked list, offer export.

### Multiple seeds, direct list (Mode 1)
User: "Find companies like torc.ai and field.ai"

1. Resolve `torc.ai` → id1, `field.ai` → id2 (1 credit each via `company.websites.include`).
2. Assemble:
```json
{
  "company_lookalike": {"company_oids": ["<id1>", "<id2>"], "match_all": false, "minimum_tier": "T2"}
}
```
3. Run page 1, present the ranked list, offer export.

### Multiple seeds + one explicit constraint (Mode 1)
User: "Companies like torc.ai and field.ai, US only"

```json
{
  "company_lookalike": {"company_oids": ["<id1>", "<id2>"], "match_all": false, "minimum_tier": "T2"},
  "company_location_search": {"include": ["United States"]}
}
```

### Prose seed, no domain (Mode 1, icp_text)
User: "Find companies like Series A autonomous-vehicle perception startups in the US"

```json
{
  "company_lookalike": {
    "icp_text": "Series A autonomous vehicle perception startups building self-driving stacks, US-based, 50-200 employees",
    "minimum_tier": "T2"
  }
}
```

### Closed-won seeds → ICP (Mode 2)
User: "We closed torc.ai, field.ai, and aurora.tech - find more like them"

1. Resolve the three domains to IDs, run lookalike page 1 (`match_all: false`, `T2`).
2. Analyze the 25 matches for patterns (industries, size, geo, funding, keywords).
3. Present the pattern-built ICP, confirm with the user.
4. Hand the confirmed ICP to `01-prospeo-discover` (no `company_lookalike` in that final search):
```json
{
  "company_location_search": {"include": ["United States"]},
  "company_headcount_range": ["51-100", "101-200", "201-500"],
  "company_industry": {"include": ["Software Development", "Automation Machinery Manufacturing"]},
  "company_type": {"status": "Private", "is_mainly_ai": true},
  "company_funding": {"stage": ["Series A", "Series B", "Series C"]}
}
```
