# Shared Conventions - gtm-skills chain

Every skill in this repo follows the same output and directory rules so the chain
composes cleanly and the router (00) can hand one skill's output to the next
without manual reformatting.

---

## Canonical interchange format: JSONL

**The standard is JSONL** (one JSON object per line), not CSV. CSV is a *derived,
human-facing export only* - never the format skills read from each other.

### Why JSONL, not CSV

The records passed between skills have **nested and variable-length fields** that
flatten badly to CSV:

- a company has *N* funding rounds, *M* recent hires, a list of technologies
- a contact carries a verdict object, a match_type, a confidence score, notes
- signal records carry a source URL + verbatim source sentence per signal

In CSV these become either lossy (drop the nesting) or unreadable (JSON stuffed
into a cell, comma-escaping hell). JSONL keeps the structure, is **appendable**
(write records as they resolve - critical for resumable long runs), streams
row-by-row without loading the whole file, and diffs cleanly in git.

**Rule of thumb:** skills read and write `.jsonl`. A skill may *additionally*
write a `.csv` for the human, and the Sheets writers stay as an *opt-in* export.
Nothing downstream should ever depend on the CSV.

---

## The `runs/` directory convention

Every skill that produces output writes it under its **own** `runs/` folder,
resolved relative to the skill directory (never a hardcoded absolute path):

```
<skill-dir>/runs/<run-id>/
├── records.jsonl        # canonical output - the chain reads this
├── tracker.json         # progress + resume state (in-progress / done / failed per item)
├── meta.json            # run metadata: date, inputs, credits/$ spent, counts
└── records.csv          # OPTIONAL human export (derived from records.jsonl)
```

- **`<run-id>`** is a timestamp+slug (e.g. `2026-07-07-salons-toronto`). Do not
  use `Date.now()`-style values that break resume; a stable slug is fine.
- **`records.jsonl`** is the one file the next skill in the chain consumes.
- **`tracker.json`** lets an interrupted run resume without re-spending credits.
  For single-call skills (02) it's a completion marker - present so every run
  folder has the same three files.
- **`meta.json` carries a `deviations[]` list.** Any run that can't follow the
  documented contract appends `{skill, what, why, at}` - via
  `05-signal-builder/scripts/signal_io.py deviation --run <folder> --skill …
  --what … --why …` - instead of silently working around it. The build-time
  complement is the chain's offline contract eval.
- A skill that received an upstream `records.jsonl` saves it as
  **`upstream.jsonl`** in its own run folder, so the writer can inherit fields
  and a resume doesn't lose them.
- Skills that enrich (04, 06) should **check prior run folders for an existing
  record before spending credits** on the same domain/person.

`runs/` is git-ignored - it holds generated data, not source.

---

## The shared record shape (minimum fields)

Records evolve down the chain - each skill *adds* fields, never overwrites an
upstream field. The chain key is **`domain`** (normalized: lowercase, no scheme,
no `www.`, no trailing slash).

| Stage | Skill | Adds to the record |
|-------|-------|--------------------|
| 01 | prospeo-discover | `company, domain, industry, size, location, funding, revenue, keywords, description` |
| 02 | apify-maps-discover | `company, domain, phone, full_address, city, region, rating, reviews_count, place_id, category` |
| 03 | firecrawl-research | `scraped_markdown` (by page type), `pages_scraped`, `scrape_status` |
| 04 | crustdata-signals | `funding[], headcount_growth, dept_growth[], recent_hires[]` |
| 04 | theirstack-jobs | `open_roles_count, roles_window_days, jobs[] {title, url, date_posted, seniority, hiring_team}`, plus free firmographics (`employee_count, funding_stage, industry`) when present |
| 05 | signal-builder | `signals[] {signal_type, signal_sentence, source_url, score, approach}`, `fallback_approach {approach, angle}` |
| 06 | resolution-email-person | `person_name, matched_title, email, email_source, verification_status, confidence` |

A skill inherits any field already present (e.g. 06 inherits `domain` +
`person?` from upstream) and only asks the user for genuine gaps.

Two shape notes:

- 03's `scraped_markdown` is keyed by page type and capped at **15K chars per
  page** (matching 05's bundle cap) - the run's `scans/*.json` keep the full
  text.
- 04's `recent_hires[]` caps at 25 entries - the per-domain JSONs keep the
  full list.

**This contract is enforced, not aspirational:** an offline contract eval
validates every writer's output against these shapes before anything ships.

---

## Auth conventions

- API keys load from environment / a `.env` file via `python-dotenv`. **Never
  hardcode a key.**
- **Google OAuth (`~/.google/token.json`) is only needed for the optional Google
  Sheets export in 01, 03, and 04.** The core discover → extract → signal →
  resolve chain runs entirely on local JSONL/CSV with no Google account.
- Each skill reads only the keys it needs and **degrades gracefully** when an
  optional key is missing - it logs `"skipping <layer>: <KEY> not set"` and
  continues, rather than crashing.

---

## Where evals live

Eval suites are maintained in Zevenue's private source repo, never inside a
skill folder. A skill directory holds only what ships: `SKILL.md`, `references/`,
`scripts/`, and its runtime `runs/`. Chain-level evals - including the contract
eval that asserts every writer matches the shared record shape - run before
every release.
