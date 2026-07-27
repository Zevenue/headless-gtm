# Extended Source Catalog

Sources beyond the baseline set in `source-selection.md` (JDs / website / BuiltWith / TheirStack / Crunchbase / Clay LinkedIn / Phantombuster / Apollo waterfall). Organized by (1) access readiness for a weekly Clay/Claygent pipeline and (2) research category. Use this after `source-selection.md` - that file is the mental model; this file expands the menu.

## The operating split

Every source in this catalog falls into one of three pipeline tiers. Pick the tier before you pick the source.

| Tier | Definition | Use for |
|---|---|---|
| **Pipeline-ready** | Returns structured text via a single API call or scrape; can run per-row in Clay at weekly cadence | Mass outbound, automated triggers, continuous enrichment |
| **ABM-only** | Valuable signal but requires manual research or fragile scraping; doesn't scale past ~50 accounts | Top-tier ABM, executive 1:1s, high-ACV campaigns |
| **Opportunistic** | Coverage too thin (<5% of prospects have it) to pipe dedicated extraction, but rich when present | Check-if-exists fallback layer, never the primary source |

---

## A. Public-company & financial disclosures

### Pipeline-ready

- **SEC EDGAR 8-K filings (RSS)** - real-time trigger feed for material events (exec departures = Item 5.02, restructuring = Item 2.05, material contracts = Item 1.01). Free. Pipe via RSS → Clay webhook. **Archetypes**: novel (trigger), failure-mode. Best trigger source on this list for US public companies.
- **SEC EDGAR 10-K Risk Factors section** - most candid pain-language a public company publishes. Free full-text API. Claygent-parseable per company. **Archetypes**: verbatim-pain, failure-mode. Example: "we rely on manual consolidation across 14 ERP instances" → FP&A outreach opener.
- **Form 4 (insider trading)** - exec stock buys/sells, co-sold trades. Cluster of exec exits = org destabilization trigger. Free EDGAR. **Archetypes**: novel, failure-mode.
- **UK Companies House API** - cleanest non-US equivalent. Director appointments (new-CFO trigger), PSC changes, filed accounts. Free, structured JSON. **Archetypes**: novel, failure-mode (late filings, qualified audits).
- **last10k.com / stockanalysis.com** - pre-parsed 10-K sections (Risk Factors isolated). Scrapeable. Faster than raw EDGAR for bulk Risk Factors extraction.
- **Quartr API** - aggregated earnings calls and investor-day transcripts, cleaner than Seeking Alpha. ~$500–2K/mo. **Archetypes**: verbatim-pain, strategic-alternative.
- **Sedar+** - Canadian EDGAR equivalent. Free, clunky but scrapeable. Use for Canadian ICP slice.

### ABM-only

- **S-1 filings** - IPO prospectuses have the most candid unit economics and failure-mode narrative a company ever publishes. Free via EDGAR but the parse-and-extract work is heavy. Use for recently-IPO'd targets (6–18mo window).
- **Investor-day decks & shareholder letters** - 3-year strategic narrative, named transformation initiatives ("Project Lighthouse"). Manual PDF download, inconsistent URLs. Batch-parse for top 50 accounts.
- **Earnings call transcripts via Seeking Alpha / IR pages** - unscripted Q&A language. Seeking Alpha fights scrapers hard; IR pages are inconsistent. Better via Quartr if you're paying.
- **Proxy statements (DEF 14A)** - exec comp structure reveals real priorities (what the CRO is bonused on = where to pitch). Parsing is noisy.
- **Tegus / AlphaSense expert transcripts** - ex-employee interviews, the candid "what actually broke" content. $25K+/yr seats, no API. Manual research only.

### Opportunistic / regional

- **EU national registers (BaFin, AMF, ESMA)** - fragmentation kills operationality. Skip unless EU-listed is core ICP.

---

## B. Person-level unstructured content

### Pipeline-ready (when prospect qualifies)

- **GitHub (REST/GraphQL API)** - commits, READMEs, repo structure, signed commit messages. Free (5K req/hr authed). HIGH authorship confidence (ghostwriting impossible). Best for CTOs, VP Eng, staff engineers. **Archetypes**: manual-task, novel, failure-mode.
- **LinkedIn long-form post text** (not like/comment counts) - via Phantombuster or Clay LinkedIn enrichment. Weekly cadence common. **Archetypes**: verbatim-pain, strategic-alternative. **Ghostwriting flag**: high for CMO/VP Marketing; low for founders.
- **Substack / personal newsletter RSS** - per-publication RSS is free. Coverage ~5%. When present, extremely rich. Discovery is the hard part (find URL via LinkedIn bio / Google). **Archetypes**: novel, strategic-alternative.
- **arXiv API** - free, clean. Use only for ML/AI/research buyers.
- **YouTube Data API + `youtube-transcript-api`** - free. For founder-creators and exec channels. Use Whisper/AssemblyAI (~$0.36/hr) for un-captioned videos.

### ABM-only

- **Podcast appearances** (Listen Notes $180/mo Pro + Podchaser) - highest-density verbatim source when present. Coverage 15–25% at VP+ level, thin below. Transcribe missing pods with AssemblyAI. **Archetypes**: verbatim-pain, strategic-alternative, novel.
- **Conference talk recordings** (YouTube org channels, Sessionize, Vimeo) - prepared positions + named failure modes. No aggregator; discovery via manual search. Stale (12–24mo typical).
- **X/Twitter** - Basic API $200/mo (10K tweets). Rich for technical-founder ICPs, sparse elsewhere. Cost-per-prospect brutal at scale.
- **Google Scholar (via SerpAPI $75/mo)** - research papers. Only relevant for deep-technical buyers.

### Opportunistic

- **Medium RSS** - most content is stale (peak 2018–2020). Skip unless prospect is a known writer.
- **Personal blogs** - opportunistic scraping only. Coverage <3%.
- **Book authorship** (Amazon / Goodreads) - <2% coverage but massive signal when present. Cheap to check.
- **Op-eds in Forbes Council / Entrepreneur tier** - ~60% ghostwritten. Do not treat as verbatim. Genuine trade pubs (SaaStr blog, Lenny's guest posts, Chief Martec) are OK.

### Ghostwriting risk (high → low)
CMO LinkedIn > Forbes Council op-eds > Founder LinkedIn > Substack > Podcast appearances > X/Twitter > GitHub commits (impossible).

---

## C. Operational, customer-sentiment, and regulatory

### Pipeline-ready

- **Hacker News "Who's Hiring" + Ask HN (Algolia HN API)** - free, real-time. Founder-voice stack choices, team size, hiring urgency. **Archetypes**: manual-task, novel. Fully automatable.
- **Product Hunt launches (free GraphQL API)** - launch stage + category + founder positioning. Timing trigger. Fully Clay-compatible.
- **GDELT + Google News RSS** - free global news event feed (15-min freshness). Layoffs, exec moves, plant openings, lawsuits. **Archetypes**: novel, failure-mode.
- **PR Newswire / BusinessWire RSS** - real-time funding/launch/appointment news in company voice. Free baseline, paid enhanced feeds $500/mo.
- **SimilarWeb API** - monthly web traffic and referral split. $200–3K/mo. Clay-native integration exists. **Archetypes**: strategic-alternative, novel.
- **Wappalyzer API** ($250+/mo) - tech-stack detection beyond BuiltWith. Good for SaaS tool identification.
- **ImportGenius / Panjiva** - US customs bill-of-lading data ($200–2K/mo, 2–4 week lag). For selling into importers/manufacturers: "ships 40 containers/mo from Vietnam" = qualifier + pain hint.
- **USPTO + Google Patents BigQuery** - free. R&D direction, named inventors. For IP/pharma/deep-tech buyers.
- **SAM.gov API** - free. US federal procurement; expiring contracts = timing trigger for govtech outbound.
- **OSHA incident database** - free monthly. Recent recordable incidents at a facility = pain trigger for EHS software.
- **Form 990 via ProPublica Nonprofit Explorer** - free. Nonprofit budgets, exec comp, vendor relationships. 12–18mo lag.
- **Reddit API** (rate-limited post-2023) - r/sysadmin, r/devops, r/sales, r/accounting, industry-specific subs. "Anyone else dealing with X" threads = pain discovery. Account-matching is the hard part.

### ABM-only

- **G2 / Capterra / TrustRadius** - verbatim product complaints and switching language. Scrapeable but Cloudflare-aggressive; no official review API. $500+/mo via aggregators. Best as Claygent one-off per account, not per-row.
- **Glassdoor** - culture pain, CEO approval, tooling gripes. Aggressive anti-bot; partner-only API. $300–2K/mo via Apify actors. Legally grey at scale.
- **StackShare narratives** - team-voice "we chose X because Y" posts. Manual.
- **App Store / Play Store reviews** - for mobile-heavy ICPs. AppFollow API makes it pipeline-ready for that narrow use case.
- **Canadian provincial corporate registries** - fragmented, mostly manual scraping.

### Opportunistic

- **Blind** - anonymous employee posts; low verifiability. Treat as directional signal only.
- **Yelp / ZocDoc / vertical review sites** - only relevant for local services / healthcare ICPs.

---

## Trigger-based sources (often underweighted)

Triggers run on a **feed-first** model - you don't query per-row; you subscribe to an event stream and let matching rows flow into Clay. Set these up once and they feed the pipeline continuously.

| Trigger | Source | Archetype |
|---|---|---|
| Funding round | PR Newswire + Crunchbase webhook | novel |
| Exec appointment | 8-K Item 5.02 + UK Companies House + PR Newswire | novel |
| Restructuring / layoffs | 8-K Item 2.05 + GDELT | novel, failure-mode |
| Material contract win | 8-K Item 1.01 | novel |
| Insider stock activity cluster | SEC Form 4 | novel, failure-mode |
| Safety incident | OSHA recordable | failure-mode |
| Expiring gov contract | SAM.gov | novel (timing) |
| Product launch | Product Hunt | novel |
| Job post spike | TheirStack webhook | manual-task |
| Major news event | GDELT + Google News RSS | novel, failure-mode |

---

## Privacy & compliance flags

- **GDPR/PIPEDA-sensitive**: Glassdoor reviews (if joined to named employees), Reddit usernames (username→person linking is risky), any scraped personal data in EU/UK/Canada campaigns.
- **Low risk** (public by design): Companies House directors, Form 4 exec trades, USPTO inventor names, SAM.gov contracting officers.
- **Rule of thumb**: if joining a source to a named individual requires inferring identity (e.g., Blind post → LinkedIn profile), don't do it in EU/UK/Canada. In US, document the legal basis before productionizing.

---

## Choosing a source - updated decision rules

Extend the rules in `source-selection.md` with these:

### Rule 5: Trigger vs. enrichment
If the campaign is **trigger-driven** (reach out when X happens), use feed sources (8-K, PR Newswire, GDELT, Product Hunt, OSHA). If the campaign is **persona-driven** (reach out to everyone matching a profile), use enrichment sources (JDs, reviews, person-level content).

### Rule 6: Tier the source before picking it
Decide pipeline-ready / ABM-only / opportunistic first. Don't budget a weekly pipeline around a source that's actually ABM-only - you'll burn ops time fighting Cloudflare every Monday.

### Rule 7: Public-company depth scales inversely with company size
10-Ks and earnings calls are gold for F500 targets, empty for seed-stage. At Series B and below, default to JD/website/LinkedIn/GitHub. At IPO-stage and above, weight heavily toward EDGAR + earnings calls.

### Rule 8: For person-level sources, rank by ghostwriting risk
Prefer sources where authorship is verifiable (GitHub commits, podcast voice, X replies with personality) over sources where it's commonly delegated (CMO LinkedIn long-form, Forbes Council op-eds). Flag any extracted "quote" from a high-risk source.
