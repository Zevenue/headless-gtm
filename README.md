# Headless GTM

GTM without the SaaS layer. This repo is the full outbound data chain - discover -> qualify -> extract -> signal -> judge -> resolve - run as Claude Code skills against raw vendor APIs. No orchestration platform, no per-seat tools, no UI between you and the data. Claude Code is the operator, the vendor APIs are the backend, and the skills encode the methodology.

Built and used in production at [Zevenue](https://zevenue.com), a GTM engineering firm. An ICP description goes in one end; qualified companies with ranked signals and verified emails come out the other, with a cost estimate approved before any credit is spent.

## The chain

```
            00-gtm-router          plans the chain, prices it, runs it step by step
            │
discover    01-prospeo-discover · 01-prospeo-lookalike · 02-apify-maps-discover
            │                     (04-theirstack-jobs discover mode for hiring-defined ICPs)
qualify     01-icp-qualify        free gate - no credit is spent on a company that can't buy
            │
extract     03-firecrawl-research
            │
signal      04-crustdata-signals · 04-theirstack-jobs
            │
judge       05-signal-builder     every signal scored, sourced, and mapped to an approach
            │
resolve     06-resolution-email-person
            │
write       email-writer · creative-variable
```

| Step | Skill | What it does |
|---|---|---|
| 00 | [`00-gtm-router`](.claude/skills/00-gtm-router/) | The orchestrator. Classifies your ICP's shape, assembles the right chain, estimates per-step cost, and executes skill-by-skill after an explicit go-ahead. |
| 01 | [`01-prospeo-discover`](.claude/skills/01-prospeo-discover/) | Company discovery from firmographic filters (industry, location, headcount, funding) via Prospeo. |
| 01 | [`01-prospeo-lookalike`](.claude/skills/01-prospeo-lookalike/) | Discovery from seed companies - "we closed these logos, find more like them." |
| 01 | [`01-icp-qualify`](.claude/skills/01-icp-qualify/) | The free qualification gate. Judges every discovered company against the ICP before any paid step. No API key, no per-company cost. |
| 02 | [`02-apify-maps-discover`](.claude/skills/02-apify-maps-discover/) | Local-business discovery via Google Maps for ICPs that title-based databases can't reach - laundromats, salons, HVAC, clinics. |
| 03 | [`03-firecrawl-research`](.claude/skills/03-firecrawl-research/) | Scrapes company websites into clean, page-typed markdown - the evidence bundle the judgment layer scores. |
| 04 | [`04-crustdata-signals`](.claude/skills/04-crustdata-signals/) | What already happened: funding rounds, headcount growth, department growth, recent hires. |
| 04 | [`04-theirstack-jobs`](.claude/skills/04-theirstack-jobs/) | What's open right now: job postings as hiring signals, with free sizing counts before any spend. |
| 05 | [`05-signal-builder`](.claude/skills/05-signal-builder/) | The judgment layer. Ranks provenance-backed signals 1-10 and picks the campaign approach per account. |
| 06 | [`06-resolution-email-person`](.claude/skills/06-resolution-email-person/) | Verified, send-safe email addresses via a cost-ordered provider waterfall with validation. |

Plus the methodology layer the chain hands off to:

| Skill | What it does |
|---|---|
| [`gtm-context`](.claude/skills/gtm-context/) | **Run this first.** Captures your offer, ICP, and engagement signals into context files every other skill reads. |
| [`creative-variable`](.claude/skills/creative-variable/) | Specs the personalization variables for a campaign - names, grammar, sources, extraction prompts, fallbacks. |
| [`email-writer`](.claude/skills/email-writer/) | 3-email cold sequences using the Situation -> Insight -> Inquisition methodology, with deliverability rules and a QA checklist. |
| [`prospect-posts`](.claude/skills/prospect-posts/) | Scans prospects' recent LinkedIn posts for a theme. Account intelligence input. |

## How the chain thinks

The component skills are interchangeable - swap Prospeo for another database and the chain still works. The routing is the product:

- **Plan before spend.** The router presents a costed plan and stops. Execution starts only on go-ahead, and approval covers only the spends listed in the plan.
- **Qualify before credits.** Every discovered or imported list passes the free qualification gate before the first paid step. Downstream steps are priced on post-qualify volume.
- **Judge before copy.** Nothing goes to a copywriter without a scored, provenance-backed signal - the exact quotable sentence and its source URL.
- **One record contract.** Every skill reads and writes the same `records.jsonl` shape (see [`_shared/CONVENTIONS.md`](.claude/skills/_shared/CONVENTIONS.md)), so any step can hand off to any later step, and an interrupted run resumes without re-spending.
- **Degrade honestly.** A missing API key turns a step manual in the plan - it never silently reroutes the methodology.

In our internal benchmark (4 scenarios, 27 assertions), chains run through the router scored 100% with zero variance vs 84% (±19) for the same setup without it, at equal time and token cost. The edge isn't tool knowledge - it's the enforced operating contract: selective scraping, pilot-first sizing, stop gates, key degradation.

## Install

1. **Clone:**
   ```bash
   git clone https://github.com/Zevenue/headless-gtm.git
   cd headless-gtm
   ```
2. **Install the skills.** Either copy `.claude/skills/*` into `~/.claude/skills/` (available in every Claude Code session), copy them into your project's `.claude/skills/`, or run Claude Code from this directory directly.
3. **Copy `utils/` and `context/` into your project root** if you use the methodology skills - they reference `context/outreach/` and `context/playbooks/`.
4. **Environment:**
   ```bash
   cp .env.example .env
   pip install -r requirements.txt
   ```
   Python 3.10+. Every key is optional: each skill uses only the keys it needs and logs what it skips. The router (00), the qualify gate (01), the judgment layer (05), and the writing skills need no keys at all. `.env.example` documents every variable and where to get each key.

## Use

In Claude Code, describe what you want and the right skill triggers - or invoke by name:

```
/00-gtm-router          new client ICP: B2B SaaS, US, 50-500 headcount, budget $200
/01-icp-qualify         qualify this list against the ICP before we enrich it
/02-apify-maps-discover laundromats in Texas metros
/05-signal-builder      rank these accounts - who do we email first, and with what angle
/06-resolution-email-person  find the owner's email for these 40 domains
```

Each skill's `SKILL.md` is the authoritative spec for what it expects and returns. The router's [`references/decision-tree.md`](.claude/skills/00-gtm-router/references/decision-tree.md) is the full routing logic as a standalone read.

## How to think about these

These skills are opinionated. They encode judgments like:

- **The message is only as good as the list.** If you need heavy personalization to make copy work, your targeting is wrong.
- **Three emails per sequence (max).** If three well-targeted emails don't land, more won't help - the signal or the angle was wrong.
- **Every signal has a score.** A 4/10 is fine - it tells the email writer how confident to sound.
- **Failures are data.** Outbound is a system of experiments, not a single campaign.

See [`context/outreach/outreach-principles.md`](context/outreach/outreach-principles.md) for the full framework.

## v2.0

This repo was previously `Zevenue/gtm-skills` (v1: the methodology skills only). v2.0 renames it to Headless GTM and adds the numbered API chain:

- New: `00-gtm-router`, `01-prospeo-discover`, `01-prospeo-lookalike`, `01-icp-qualify`, `02-apify-maps-discover`, `03-firecrawl-research`, `04-crustdata-signals`, `04-theirstack-jobs`, `06-resolution-email-person`, and the shared record contract in `_shared/`
- Replaced: `signal-builder` -> `05-signal-builder` (chain-native, record contract in and out), `job-search` -> `04-theirstack-jobs` (sizing counts before spend, discover mode, caching)
- Kept: `gtm-context`, `email-writer`, `creative-variable`, `prospect-posts`

Old links redirect. Evals for every skill are maintained in Zevenue's private source repo and run before each release.

## License

MIT. See [LICENSE](LICENSE).

## About Zevenue

[Zevenue](https://zevenue.com) is a Toronto-based GTM engineering firm. We build custom outbound + RevOps systems for GTM teams. Reach me at: yusuf@zevenue.com
