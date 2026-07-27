# 04-theirstack-jobs

The hiring-signal layer (step 04) of the API-first GTM chain. Pulls open job
postings from the [TheirStack](https://theirstack.com) API and turns them into
structured hiring signals: open roles per domain, titles, seniority, posting
dates, and the hiring team where the posting exposes it, plus free
firmographics (headcount, funding stage, industry) on the side.

Open reqs are the "what they're about to do" signal - a company hiring its
first SDRs is building outbound, a VP Sales req is a strategy shift. Every
pull is bounded by a sizing count before any credits are spent.

## What it does

- **check mode**: takes a domain list (or an upstream `records.jsonl`) and
  returns hiring evidence per company - the standard step-04 position in
  the chain, with upstream fields passing through untouched
- **discover mode**: takes filters only (title/seniority/tech plus
  geo/size/funding) and finds companies currently hiring for a role - the
  direct discovery entry when the ICP is defined by the req itself
- Sizes before it spends: counts without company filters are free (exact
  job and company totals), counts against a domain list cost ~1 credit,
  and `--count-only` answers "how many / what would it cost" without a pull
- Job fetches cost exactly 1 credit per job returned; caps (`--per-domain`,
  `--max-jobs`, `--days`, `--title`) keep a 50-req company from costing 50
- Caches every fetched domain keyed by a query hash, because TheirStack
  charges full price for re-pulls - re-running the same query costs 0
- Stops for confirmation when the estimate crosses the credit gate
  (default 500, `--credit-gate` to change), and runs are resumable without
  double spend
- Writes a `runs/<run-id>/` folder with `records.jsonl` per the chain
  contract; domains checked with zero matches still get a record, so
  downstream can tell checked-and-quiet from never-checked

## Setup

Auth comes from the environment - no keys are stored in the skill.

```bash
export THEIRSTACK_API_KEY="your-theirstack-key"
```

No Python packages required (stdlib only; `python-dotenv` is optional).

```bash
# Free sizing in discover mode, ~1 credit against a domain list
python3 scripts/theirstack_jobs.py count --domains acme.com,globex.com \
  --title "SDR,BDR" --days 30

# Check a domain list (cached, resumable)
python3 scripts/theirstack_jobs.py check --domains acme.com,globex.com \
  --title "SDR,BDR" --days 30 --per-domain 10
```

## Layout

```
04-theirstack-jobs/
├── SKILL.md                    modes, credit rules, filters, output contract
├── references/
│   └── jobs-api.md             full filter list, response fields, credit mechanics
└── scripts/
    └── theirstack_jobs.py      count / check / discover / credits CLI
```

Evals for this skill are maintained in Zevenue's private source repo and run
before every release - skill folders ship without them.

## Position in the chain

Sibling of [`04-crustdata-signals`](../04-crustdata-signals/): this skill
covers what's open right now (job reqs), that one covers what already
happened (funding, joins, headcount). Run both when the play needs both -
same `records.jsonl` in, additive fields out.

Discover mode doubles as the discovery entry for hiring-defined ICPs, so
the chain can start here instead of at step 01. Either way the output feeds
[`05-signal-builder`](../05-signal-builder/), which owns the scoring and the
approach call; `hiring_team` entries give 06 a head start on resolution.

Built at [Zevenue](https://zevenue.com), a GTM engineering firm.
