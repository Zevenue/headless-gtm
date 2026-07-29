# Happy path - one full cold-start run

Two ICPs through the same workflow. The first is a full worked run on the
`local-services` preset: company names are neutralized (house rule: no real
prospect names in the repo), but the counts, timings, and costs are the actual
figures from that run. The second, at the end, shows the two steps that change
when the ICP is firmographic B2B rather than local businesses, anchored on a
real 01-prospeo-discover pull - so the workflow does not read as
main-street-only.

**Setup.** An owner runs a booking-and-follow-up service for home-services
contractors. No CRM, no list, no outbound history - just the business.

## Step 1 - Business context

No `context/offer.md` existed, so the workflow offered the `local-services`
preset. The owner adopted it and adjusted one line (their sweet spot is 5-20
techs, not 5-50). Context confirmed in about a minute. No spend.

## Step 2 - Source of record

The workflow proposed three named sources, in order: the provincial
trade-licensing registry, a trade-association "find a contractor" directory, and
a metro HVAC directory listing. The owner picked the registry first.

The registry's public search page returned **zero** extractable rows - it is a
search form that renders nothing without a query (registries are the best source
and the most defended, exactly the case `reference/gotchas.md` covers). The
workflow named the block and fell through to the metro HVAC directory listing,
confirmed it with the owner, and ran `03-firecrawl-research` directory
extraction on the confirmed URL.

- **Result:** 26 contractor rows - name, city, website (where listed), category.
- **Cost:** one extract call on a single listing page, about 70 seconds.
  Firecrawl bills extraction by tokens (1 credit = 15 tokens), so the workflow
  stated the token-based estimate and got approval before running.
- Several rows carried **no website**; they entered the chain on the `name|city`
  dedup key rather than being dropped, keeping their phone and listing link as
  the contact channel.

## Step 3 - Qualify (free)

`01-icp-qualify` ran on the 26 against the confirmed context:

| Outcome | N | Why |
|---|---|---|
| Qualified | 22 | Owner-operated local HVAC / mechanical contractors |
| Uncertain | 1 | A duct-cleaning-only shop - narrower than the ICP; gate asked whether to include |
| Disqualified | 3 | National home-services brands (the preset's "national franchise with corporate marketing" anti-signal); one shared a domain with another and was merged |

The gate earned its keep here: the three national brands are the ones a
cold-start owner would waste the first week chasing. No spend - this step is
model judgment only.

## Step 4 - Rank

The offer is "modernize online booking and follow-up," so each row's **digital
maturity is itself the signal - and it is already in the listing.**
`05-signal-builder` (vertical-smb calibration) scored on it, provenance = the
directory row:

- **No website listed** -> sharpest Pain-led fit (phone-only booking is the
  exact gap the offer closes). Top of the sheet.
- **Social page only** -> Pain-led, one notch down.
- **Has an owned site** -> Value-led (modernize an existing basic site).

The phone-only contractors ranked first. A per-company `03` scrape is the
optional next pass that would add hiring/expansion signals on top; the first
pass ranks on what the directory already gave.

## Step 5 - Write

`email-writer` drafted a 3-email Pain-led sequence for the top segment (the
"no online presence" contractors) - built on the digital-gap signal, with the
preset's objection ("we get all our work from referrals") shaping email two.
**Drafts only**, presented for edits.

## Step 6 - Campaign sheet + approval

`07-campaign-sheet` wrote the sheet on the 22 qualified records:

- `campaign-sheet.md` - 22 targets ranked, the phone-only shops first, each with
  its digital-gap reason and Pain-led approach.
- `campaign-sheet.csv` - HubSpot default import headers, every row Lifecycle
  Stage = Lead. Contacts were unresolved (06 had not run), so the sheet degraded
  to five columns (no First/Last/Email) rather than shipping empty ones.

Presented for on-screen approval. Nothing was sent.

Neutralized excerpt of the top of the sheet:

```
### 1. [Contractor A] - North York, ON
- Why now: digital-gap - no website listed in the directory, phone-only booking
- Approach: Pain-led
- Contact: not resolved - run 06-resolution-email-person for send-ready addresses

### 2. [Contractor B] - Brampton, ON
- Why now: digital-gap - no website listed in the directory, phone-only booking
- Approach: Pain-led
```

## Recap

- **Source:** one directory listing (after the registry form returned nothing).
- **26 found -> 22 qualified**, 1 uncertain, 3 disqualified.
- **Spend:** one token-billed extract call on one listing page - the run's only
  paid step (the free gate, rank, and sheet cost nothing).
- **Data path** - extraction to finished sheet - ran in a few minutes, extraction
  (~70s) the dominant cost. Wall-clock of a supervised run tracks how fast the
  owner approves each gate.
- **Deliverable:** a ranked sheet + a HubSpot-import CSV, approved on screen.
  Nothing sent.

## The same workflow, a B2B ICP

The run above sourced from a scraped directory because its buyers - local
contractors - live in one. A firmographic B2B ICP - say a RevOps or GTM tool
sold to funded B2B SaaS companies - has no directory to scrape: the buyers are
defined by what the company is and what it is doing, not by a listing. Two steps
change; the gates, the approvals, and the no-send rule are identical. The
figures below are from a real 01-prospeo-discover call (company names
neutralized, per the same house rule).

**Step 2 forks to a pull, not a scrape.** Instead of a registry, the workflow
proposes a firmographic source: 01-prospeo-discover for an ICP-filtered pull,
01-prospeo-lookalike from a few seed companies, or 04-theirstack-jobs when a
hiring signal defines the buyer. Here the plain-English ICP mapped to funded
(Series A-C), US, private B2B SaaS at 51-500 employees.

- **Result:** 2,304 matching companies; page one returned the first 25 with full
  firmographics. A full export is 93 pages.
- **Cost:** 1 Prospeo credit for the total count and the 25-row preview (one
  credit per 25-result page), 93 credits to export every row. The estimate
  was stated before the call - and page one is already enough to qualify and
  rank a first campaign.
- Every record came back with far more than a directory row would carry:
  employee count, founded year, revenue range, funding history, an
  active-job-postings count, and the technology stack.

**Step 4 ranks on the pulled signal, not a listing column.** The local-services
run had its signal - digital maturity - sitting in the directory row. The B2B
pull is richer: because each record already carries funding, hiring, and tech,
05-signal-builder ranks on what the pull returned, with no separate paid signal
pass needed for a first cut. A later 04-theirstack-jobs or 04-crustdata-signals
pass deepens it only if the owner approves the spend. Provenance still cites the
source record.

Everything else is the same path: 01-icp-qualify runs free on the pulled list,
email-writer drafts the sequence, and 07-campaign-sheet writes the same
HubSpot-shaped sheet. The deliverable and the approval gate are identical - the
only difference is where the first list came from.
