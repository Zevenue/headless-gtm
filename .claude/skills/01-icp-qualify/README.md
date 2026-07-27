# 01-icp-qualify

The free qualification gate of the API-first GTM chain. Judges every discovered
company against the client's ICP before any paid enrichment, so credits are only
spent on companies that could actually buy.

Discovery filters match labels - industry codes, size bands, locations as a
database recorded them. This skill judges fit: would this specific company
plausibly buy from this specific client? Acquisitions, competitors, stale
headcounts, and shell listings all pass label filters and then waste enrichment
spend downstream. The gate catches them first, and it costs nothing to run.

## What it does

- Studies the client before judging anyone: inherits the client profile when
  running inside the chain, works from whatever the user provides standalone,
  and falls back to a bounded read of the client's own website (~5 pages max)
- Compiles a client-specific qualification brief - business-nature check,
  firmographic bounds, a universal independence-and-liveness check, and 1-3
  dynamic checks derived from the client's reality - shows it for approval
  before judging, then saves and reuses it on later runs
- Returns one of three verdicts per company: `qualified`, `disqualified`, or
  `uncertain` - asymmetric on purpose, because wrongly qualifying wastes a few
  credits while wrongly disqualifying throws away a real buyer
- Never disqualifies without quotable evidence: every rejection names a DQ
  category and the sentence, redirect, number, or list entry that proves it;
  uncertainty and missing data are never disqualifications
- Applies a wide-tolerance rule to firmographics, since discovery data lies
  about size and location: near-misses become `uncertain`, not rejections
- Fetches a homepage title and meta-description with a plain HTTP request when
  a record has no description - free, no scraping service
- Runs two passes: pass 1 pre-spend on discovery fields, pass 2 after scrape
  and signal skills add evidence - re-judging every `uncertain` and confirming
  (or demoting) every `qualified`
- Calibrates on the first run per client: judges in batches of 10, takes
  corrections, writes each one into the brief as a rule, and goes hands-off
  after two consecutive clean rounds
- Splits output into three files - forwarded records, an uncertain review
  queue, and a disqualified audit trail - so downstream skills read the
  forwarded file unchanged, and asks before forwarding uncertain rows
- Closes every run with a summary that includes downstream spend avoided:
  disqualified count times the per-company cost of the chain's paid steps

## Setup

None by default. Judgment runs in-session - no API key, no per-company cost.

For large lists, an external model can do the judging via any OpenAI-compatible
endpoint:

```bash
export QUALIFY_LLM_BASE_URL="https://api.example.com/v1"
export QUALIFY_LLM_API_KEY="your-key"
export QUALIFY_LLM_MODEL="model-name"
```

If these are unset, judgment stays in-session. A newly configured model must
pass an acceptance check before judging a real list; one that fails falls back
to in-session judgment.

## Layout

```
01-icp-qualify/
├── SKILL.md                    phases, verdict rules, output contract
├── references/
│   ├── brief-template.md       the qualification brief format
│   └── dq-catalog.md           every DQ category and the evidence it requires
└── runs/                       (created at runtime) records + uncertain + disqualified per run
```

Evals for this skill are maintained in Zevenue's private source repo and run
before every release - skill folders ship without them.

## Position in the chain

```
01-prospeo-discover / 01-prospeo-lookalike /
02-apify-maps-discover / an imported list  ──►  01-icp-qualify  ──►  first paid step
```

Every router chain routes through this gate: it follows whichever discovery ran
(or an imported list) and precedes the first credit-spending step, so downstream
volume - and downstream cost - is post-qualify volume.

Built at [Zevenue](https://zevenue.com), a GTM engineering firm.
