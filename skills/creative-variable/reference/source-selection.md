# Source Selection - Mental Model

The core question: **given a campaign angle, where's the right place to look for the raw data that feeds the variable?**

## The sources we actually use

| Source | Best for | Weakness |
|---|---|---|
| **Job descriptions** (via Clay "find jobs" or TheirStack webhook) | Role-level pain, responsibilities, tools mentioned, hiring intent | Only exists when they're hiring; JDs sometimes list tools the hire *will use*, not what's in place |
| **Company website** (WebFetch / Claygent scrape) | Positioning, size/stage signals, fleet/physical presence, front-end tech stack | Marketing-polished - filter out jargon |
| **BuiltWith** | Front-end tech (analytics, CRM widgets, marketing pixels, anything installed on the site) | Misses back-end/operational tools (Samsara, Verizon Connect, internal ERPs) |
| **TheirStack** | Back-end / operational tech stacks mentioned in JDs; recent (last 60-90 day) hiring signals | Noisy - always qualify the company after the scrape |
| **Crunchbase** | VC funding, investor lists, funding rounds, ownership type | Weak integration with Clay; often need to export-then-import. Some investor data has to be scraped via reverse-engineered Crunchbase URLs |
| **Clay "enrich company"** (LinkedIn data) | Industry tags, employee headcount, description keywords | LinkedIn industry tags sometimes disagree with Crunchbase tags - qualify both |
| **Phantombuster** (LinkedIn activity scraper) | Whether a prospect is active on LinkedIn (like/comment/post frequency); connection count | Activity data is messy (multiple rows per prospect); qualify with a second-layer Claygent pass |
| **Apollo / Prospeo / Findymail** (waterfall) | Work emails, titles, seniority | Coverage varies by segment; always run a waterfall, not a single provider |

## Decision rules

### Rule 1: Front-end vs back-end tech
BuiltWith is excellent for scraping tech stacks that are front-end facing (CRM widgets, analytics, marketing pixels). For back-end/operational stacks (Samsara, Verizon Connect, internal ERPs, fleet software), reach for TheirStack instead - it pulls from JDs and surfaces what teams actually run internally.

**Apply when**: the campaign angle depends on knowing what tool the prospect uses internally.

### Rule 2: If Clay's data is suspicious, go to the original source
Crunchbase has materially better coverage for funding rounds, investors, and VC-backed companies than Clay's enrichment layer. If you need investor lists or precise round data, query Crunchbase directly.

**Apply when**: Clay enrichment returns sparse or contradictory data - check if there's a specialist source (Crunchbase for funding, TheirStack for recent jobs, Phantombuster for LinkedIn behavior).

### Rule 3: Qualify at the level you're targeting
Use two-layer qualification when the campaign has both a firmographic filter and a behavioral signal: **company eligibility** first (is this the kind of company we can sell to?), then **per-row eligibility** (does this specific JD / post / event contain the signal we need?). Variables extract only from rows that passed both layers.

**Apply when**: the campaign has both a firmographic filter *and* a behavioral signal - always qualify the firmo first, then the behavior.

### Rule 4: Walk the manual workflow before you automate it
Before writing a Claygent prompt, do the task by hand on 2-3 prospects and narrate the steps. Those steps become the prompt. If you can't do the task manually, you can't prompt for it.

## When to reach for unusual sources

Most campaigns don't need anything beyond the table above. When the standard sources don't reveal the signal the angle needs, consult **`extended-sources.md`** - it catalogs 40+ additional sources organized by pipeline readiness (pipeline-ready / ABM-only / opportunistic) and by research category (public-company filings, person-level content, operational/regulatory).

Common extensions:
- **Trigger feeds** (8-K RSS, PR Newswire, GDELT, Product Hunt, OSHA incidents, SAM.gov expiring contracts) - for event-driven campaigns rather than persona-driven
- **Public-company filings** (SEC EDGAR Risk Factors, UK Companies House, Quartr earnings transcripts) - for F500 / recently-IPO'd / mid-market+ ICPs
- **Person-level content** (GitHub, podcast transcripts, Substack, conference talks, X/Twitter) - for campaigns targeting individual executives in their own voice
- **Customer sentiment** (G2, Glassdoor, Reddit, HN hiring) - for pain/switching-signal mining

**Never propose an unusual source without confirmation.** These sources are expensive to scrape, often inconsistent, and the payoff depends on whether the specific angle needs what they reveal. Flag the opportunity, tier it (pipeline-ready / ABM-only / opportunistic), explain the reasoning, let the campaign owner decide.

## Source × archetype heuristic

| Variable archetype | Default source |
|---|---|
| Verbatim-pain | JD text (it's the only place pain is written in the prospect's own voice) |
| Manual-task | JD text (inferred via Claygent) |
| Strategic-alternative | Domain knowledge / manual mapping (not scraped) |
| Failure-mode | Domain knowledge / manual mapping, sometimes JD context |
| Novel (anything else) | Reason from first principles; often an unusual source |
