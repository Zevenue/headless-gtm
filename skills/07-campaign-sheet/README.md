# 07-campaign-sheet

The exit door (step 07) of the API-first GTM chain. Takes the terminal
`records.jsonl` a run produced - qualified, signal-ranked, or fully resolved -
and turns it into what an owner actually uses: a ranked, owner-readable campaign
sheet and a CSV shaped for a one-click HubSpot import.

It is the only chain step whose output is *for a human, not the next skill*. It
adds no fields to the record and nothing downstream reads it - the CSV is a
derived export (`headless-gtm-shared/CONVENTIONS.md`), and `records.jsonl` stays
the source of truth.

## What it does

- Ranks records by their top 05 signal score - highest first is who to contact
  first - and keeps unscored rows in the sheet rather than dropping them
- Writes `campaign-sheet.md`: per-target cards (why now, verbatim signal +
  source, recommended approach, contact or "not resolved"), then a compact table
  for the rest
- Writes `campaign-sheet.csv` in HubSpot's default contact-import headers with
  every row set to Lifecycle Stage = Lead, so the mapping step is automatic
- Degrades with the data: no First/Last/Email columns until 06 has resolved
  contacts; rows without a website still ship on their listing fields
- Offers, only when a HubSpot connector is present, to stage the approved rows
  as `lifecyclestage = lead` contacts - approval-gated, batch size confirmed

## Setup

None. `scripts/campaign_sheet.py` is stdlib-only Python - no API key, no
network. It runs on a synthetic fixture, so the sheet can be demoed before any
real data or account exists.

## Layout

```
07-campaign-sheet/
├── SKILL.md                    what it reads, what it writes, the approval step
├── README.md                   this file
└── scripts/
    └── campaign_sheet.py       records.jsonl -> campaign-sheet.md + .csv (stdlib)
```

## Position in the chain

Runs last. `run-first-campaign` calls it as the final step after email-writer;
in a hand-built chain the router (00) points here once records are ranked (05)
and optionally resolved (06). Its two outputs are the deliverable an owner
approves on screen - nothing in this repo sends.

## Calibration target

Written to the (A) Opus-optimized standard - a thin SKILL.md with the approval
gate stated once, and a single stdlib script doing the flattening.
