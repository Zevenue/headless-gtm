# Unit costs, rate limits, and estimation

The numbers the router uses to build a cost line per step. Prices marked *plan-dependent*
vary with the vendor plan - treat them as ranges and say which plan the estimate assumes.
**Update this file after any run where actuals diverged from the estimate** - the
estimate-vs-actual gap at each checkpoint is the calibration data.

Every component skill has its own spend gate; the router's estimate never replaces those
confirmations, it just makes the total visible before step one.

## Per-step costs

| Step | Skill | Unit cost | Rate limit | Notes |
|---|---|---|---|---|
| 01 | prospeo-discover | 1 credit per search page (25 companies/page) | ~2-2.5 req/s | Account info + suggestions are free. Export cost = `ceil(target / 25)` credits. Credit price is plan-dependent. |
| 01 | prospeo-lookalike | 1 credit per search page (25/page), same as discover; + 1 credit per seed domain resolved to a company ID (multi-seed only) | ~2-2.5 req/s | Lookalike filter needs a **Starter+** plan (unavailable on Free). Single-domain and `icp_text` seeds skip the resolution credits. Mode 2 adds one 25-result page (1 credit) to read the pattern, then the discover search costs apply. |
| 01 | icp-qualify | $0 API - in-session model judgment (optional external engine bills your own LLM tokens) | n/a | The free gate between discovery and every paid step. Its effect on the estimate: every line below it prices on post-qualify volume. Description-less rows get a plain-HTTP homepage title/meta fetch - also free. |
| 02 | apify-maps-discover | ~$2.10 / 1K places; +$2.00 / 1K with `--include-emails` | 300s sync cap per call | Script hard-gates any run estimated over $10. Actor page has shown ~$1.50/1K; the script budgets the conservative figure. |
| 03 | firecrawl-research | minimal 3 · standard 5-8 · deep 5-11 · extract ~20+ credits per domain | plan-dependent | $0.001/credit (Standard plan) or $0.0004 (Growth). Stealth proxy silently charges 5 credits/page on blocked sites - budget batches assuming some 5x pages. |
| 03 | firecrawl-research (registry) | /extract is token-billed: 1 credit = 15 tokens, so cost scales with page size - no flat per-page number (extract mode on a directory, not a company site) | plan-dependent | Pilot page 1, read the actual charge, multiply by page count. Rows without websites still count. This is discovery, not enrichment - the source replaces an 01/02 pull, so it isn't spent on top of one. |
| 04 | crustdata-signals | 2 credits per company enrich + 0.03 per person result (~2.6 credits/domain with a typical hire pull) | 15 RPM enrich · 30 RPM person search | Credit price is plan-dependent. Cached JSONs are free - the skill reuses prior runs before spending. |
| 04 | theirstack-jobs | 1 credit per job returned, exactly. Sizing counts: free without company filters (discover); ~1 credit against a domain list (blur disables on company identifiers) | none published (script spaces ~0.4s/call) | The sizing count returns exact job AND company totals - use it as the estimate, not a guess. No charge dedup on re-pulls; per-domain cache reused across runs. Check-mode cap defaults to 10 jobs/domain. |
| 05 | signal-builder | $0 API - model judgment only | n/a | The cost is session time, not credits. |
| 06 | resolution-email-person | Prospeo: 1 credit/page that returns results (misses free) + reveal credits per contact · Blitz: free on its Unlimited plan · Findymail: pay-per-valid · ZeroBounce: 1 credit/check, `unknown` results free | Prospeo ~2-2.5 req/s | The Step 3 estimation gate shows exact credit cost before anything is revealed - use its preview as the real number. |

## Estimation formulas

- **01 discover**: `credits = ceil(target_companies / 25)` - e.g. 1,000 companies = 40 credits.
- **01 lookalike**: `credits = ceil(matches / 25) + seed_domains_resolved` (seed resolution
  only on multi-domain seeds; single-domain and `icp_text` skip it). Mode 2 adds 1 credit for
  the pattern-read page, then the discover formula applies to the broadened search.
- **01 qualify**: `cost = $0`; `post_qualify_volume = discovered x pass_rate`. The pass
  rate is a labeled assumption (it depends on the client and the discovery source - Maps
  and directory pulls shed more than database pulls) until the pilot trues it. Report
  `spend_avoided = disqualified x per-company cost of the chain's paid steps` at every
  run close - that figure comes from this file.
- **02**: `usd = (max_results / 1000) x (2.10 + 2.00 if emails)` - e.g. 2,000 with emails
  = $8.20.
- **03**: `usd = domains x credits_per_mode x usd_per_credit` - e.g. 200 domains, standard
  (~7), Standard plan = 200 x 7 x $0.001 = $1.40.
- **03 registry extract**: token-billed (1 credit = 15 tokens), so there is no flat
  per-page number. Extract page 1 only, read the actual charge from the run tracker (or
  the Firecrawl dashboard when the API omits usage), then `credits ~= pages x page-1
  actual`. Count pages from the registry's own pagination and state the pilot figure in
  the estimate before extracting the rest. This is the discovery layer, so price it in
  place of an 01/02 line, not in addition to one.
- **04 crustdata**: `credits = domains x ~2.6` - e.g. 1,000 domains = ~2,600 credits.
- **04 theirstack**: check: `credits = min(total_jobs, domains x per_domain_cap) + ~1`
  (the domain-scoped sizing count bills ~1); discover: `credits = min(total_jobs,
  max_jobs)` with a genuinely free sizing count. `total_jobs` is exact either way.
- **06**: `cost = found_contacts x (search + reveal credits) + validations`. Coverage is
  the unknown - assume 50-70% title-match coverage for planning, then replace with the
  Step 3 preview's real count.

State every assumption in the plan (coverage %, credit price, scrape mode) so a wrong
input is correctable before it compounds.

## Wall-clock time

Enrichment RPM, not scraping, is usually the bottleneck on large runs:

- **04 crustdata** at 15 RPM enrich: 1,000 domains = ~67 min of enrich calls, plus ~34 min
  of person searches at 30 RPM. Budget ~1.5-2h per 1,000 domains.
- **04 theirstack**: never the bottleneck - the script spaces calls ~0.4s apart, so a
  1,000-domain check is under 10 min.
- **01** at ~2 req/s: a 40-page export is minutes, not hours.
- **01 qualify**: no rate limit - judgment passes like 05's, batches of 10 during
  calibration then bulk; minutes per hundred rows. Never the bottleneck.
- **03**: minutes per hundred domains in minimal/standard mode; extract mode is slower per
  page. The script batches and resumes, so interruptions don't lose progress.
- **06**: dominated by per-contact waterfall calls at Prospeo's ~2 req/s; the validation
  pass is fast.

For a same-day deadline, the levers are: minimal scrape mode, a tighter superset, and
running 04 only on the pilot slice.

## Worked examples

**b2b-saas, 2,000-domain TAM, pilot 150.**

| Step | Volume | Est. |
|---|---|---|
| 01 discover | 2,000 companies = 80 pages | 80 Prospeo credits |
| 01 qualify | all 2,000, pass 1 | $0 - assume ~80% pass (labeled); ~400 DQs skip every line below |
| 04 signals | pilot 150 first, then top ~1,000 qualified | 150 x 2.6 = ~390 credits (pilot) |
| 03 selective | top decile ~100 domains, standard | ~$0.70 (Standard plan) |
| 05 judge | 150 records | $0 |
| 06 resolve | ~90 found at 60% coverage | ~90 search + reveal credits + validations |

The pilot proves the per-unit numbers - including the pass rate - before the remaining
domains spend anything. At the assumed rate the gate's spend-avoided line is ~400 x 2.6
= ~1,040 CrustData credits before counting scrape and resolution.

**vertical-smb, 2,000 Maps records.**

| Step | Volume | Est. |
|---|---|---|
| 02 discover | 2,000 places, with emails | ~$8.20 |
| 01 qualify | all 2,000, pass 1 (free homepage-meta fetches for description-less rows) | $0 - Maps pulls shed hard; assume ~70-80% pass (labeled) |
| 03 scrape | qualified ~1,500, minimal mode | 1,500 x 3 x $0.001 = ~$4.50 |
| 05 judge | in passes of 25 | $0 |
| 06 resolve | owner/manager, domain-first | mostly free rung + validations |

Under $20 in tool spend end-to-end - the real cost of the vertical-smb chain is judgment
time in the gate and in 05, which is why both run in batched passes.
