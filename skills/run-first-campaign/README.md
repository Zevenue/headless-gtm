# run-first-campaign

The packaged cold-start workflow. Where 00-gtm-router plans a chain for an
operator who can describe an ICP and a budget, this skill runs a fixed,
supervised sequence for the other starting point: an owner with no list, no
CRM, and no outbound history - just a business.

One pass takes them from a plain-English description to an approved campaign
sheet: context (preset or interview) -> a proposed source of record (registry,
professional college, association directory, marketplace, Maps fallback) ->
free qualification -> signal ranking -> a drafted 3-email sequence -> an
owner-readable sheet plus a HubSpot-import-shaped CSV. Every step ends at an
explicit owner approval, every paid step is cost-approved before it runs, and
nothing sends - the sheet and drafts are the deliverable.

## What it does

- Establishes business context from `context/offer.md` + `context/icp.md`, a
  vertical preset in `reference/presets/`, or the `gtm-context` interview
- Proposes the source of record by name instead of asking the owner for URLs,
  and extracts it with 03-firecrawl-research's listing-row schema after
  confirmation
- Gates the extracted list with 01-icp-qualify (free) before anything else is
  spent, and surfaces the uncertain-row question instead of deciding silently
- Ranks the qualified set with 05-signal-builder (vertical-smb calibration) and
  drafts a 3-email sequence with email-writer for the approved segment
- Closes with 07-campaign-sheet: who to contact first and why, plus a CSV in
  HubSpot's default import headers, approved on screen
- Offers 06-resolution-email-person as an explicit, cost-gated branch when the
  owner wants send-ready addresses

## Setup

None for the workflow itself. The extraction step needs `FIRECRAWL_API_KEY`;
without it the workflow still establishes context, qualifies, ranks, and writes
on whatever data exists - it names the skipped layer instead of failing.

## Layout

```
run-first-campaign/
├── SKILL.md                     the workflow: six steps, gates, output spec
└── reference/
    ├── presets/                 vertical context presets (offer.md + icp.md)
    ├── gotchas.md               failure patterns from real cold-start runs
    └── examples/happy-path.md   one full worked run, from preset to sheet
```

## Position in the chain

Sits above the chain like the writing skills, not inside it: it sequences
03 -> 01-icp-qualify -> 05 -> email-writer -> 07 for one specific situation.
The router's entry-point table hands "nothing yet - no list, no CRM" here; a
user with any existing data belongs in 00-gtm-router instead.

## Calibration target

Written to the (A) Opus-optimized standard - thin body, explicit gates only
where money or sends are at stake, depth in `reference/`.
