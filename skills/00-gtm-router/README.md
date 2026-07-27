# gtm-router

The orchestrator (step 00) of the API-first GTM chain. Takes an ICP description
plus optional budget, volume, and urgency, classifies the ICP's shape, and produces
the right discovery -> qualification -> extraction -> signals -> judgment ->
resolution chain with per-step cost estimates and rationale. Executes the chain
skill-by-skill only after an explicit go-ahead, checkpointing actuals against
estimates between steps.

Per-tool wrappers route tools ("use Firecrawl to scrape"). This skill routes
methodology: the ICP shape picks the discovery path, volume picks extraction depth,
evidence type picks the signal source, every discovered list passes the
qualification gate (01-icp-qualify) before credits touch it, and everything passes
through judgment (05) before copy gets written. That decision logic is the product -
the component skills are interchangeable; the routing isn't.

## What it does

- Classifies an ICP into one of four shapes (b2b-saas, vertical-smb,
  hiring-defined, web-scattered), asking at most one clarifying question
- Picks the entry point from what the user already has - a bare ICP, seed
  companies to expand, a target domain list, an evidence bundle, or contacts
  missing emails
- Routes every discovered or imported list through the free qualification gate
  (01-icp-qualify) before the first paid step, and prices downstream steps on
  post-qualify volume with the pass rate as a labeled assumption
- Assembles the default chain per shape and adjusts for volume, budget, and
  urgency, with the reason for every deviation stated in the plan
- Estimates per-step and total cost from `references/unit-costs.md` (real unit
  prices and rate limits, not guesses), plus wall-clock time
- Presents a plan and stops - execution starts only on go-ahead, and plan approval
  covers only the spends listed in the plan
- Executes via the component skills' own SKILL.md flows, threading `records.jsonl`
  per the chain contract, tracking estimate-vs-actual in a run manifest, and
  stopping to re-plan when actuals blow past estimates
- Degrades honestly: a missing key or skill turns a step manual, it doesn't
  silently reroute the methodology

## Setup

None for the router itself - it spends no credits and needs no keys. Each
component skill carries its own auth (see `_shared/CONVENTIONS.md`); a missing key
downgrades that step to manual in the plan rather than blocking it.

## Layout

```
00-gtm-router/
├── SKILL.md                    routing logic, plan template, execution rules
├── references/
│   ├── decision-tree.md        the full routing logic as a standalone readable doc
│   └── unit-costs.md           per-step unit costs, rate limits, estimation formulas
└── runs/                       (created at runtime) plan.md + manifest.json per run
```

Evals for this skill are maintained in Zevenue's private source repo and run
before every release - skill folders ship without them.

`references/decision-tree.md` reads standalone - the full routing logic as a
document, no skill required.

## Position in the chain

```
00 gtm-router  ──orchestrates──►  01/02 discover -> 01 icp-qualify -> 04 signals
                                   -> 03 extract -> 05 judge -> 06 resolve
                                   -> email-writer
```

Two chain slots are each two sibling skills, and 01 holds a third. Step 01:
01-prospeo-discover (list from firmographic filters), 01-prospeo-lookalike (list
from seed companies), and 01-icp-qualify (the free gate that judges fit before
any paid step - it follows whichever discovery ran, or an imported list). Step
04: 04-crustdata-signals (what already happened - funding, joins, headcount) and
04-theirstack-jobs (what's open right now - job reqs). Theirstack's discover
mode doubles as the discovery entry for hiring-defined ICPs, and lookalike is
the discovery entry when the client starts from example logos instead of
filters - so the chain doesn't always start at 01-discover/02.

Upstream of everything; downstream of nothing. The router is also the natural
kickoff surface: a new-client brief goes in, a costed pilot plan comes out.

