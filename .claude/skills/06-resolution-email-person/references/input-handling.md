# Input Handling — the "thinking brain" before spending credit

The job here is to be smart about whatever shape the data arrives in. A mislabeled column or a disguised domain, if trusted blindly, wastes enrichment credit on garbage. So **inspect the data, don't just trust the headers**, and normalize before any paid call.

## Column mapping (bulk files)

A `records.jsonl` from an upstream skill (01–04) needs **no column mapping** — each line already carries `{company, domain, person?, filters_matched}`; trust the fields and route each record to a title search or a named-person lookup. The steps below are for CSV/Excel files that arrive from humans:

1. Read the header row.
2. Inspect a sample of actual cell values in each column.
3. Decide what each column *really* holds, based on the data — not the label. A column titled `Company` that holds `acme.com` is a domain; a `Name` column full of `x@y.com` is emails.
4. **Silently remap** mislabeled columns to their true role, and **report every remap** to the user (e.g., "Mapped 'Company' → domain; 'Contact' → full_name"). Auto-fix the obvious cases; only pause to ask when a column is genuinely ambiguous.

## Input-shape table

Handle each per-row. Anything you can't resolve, skip **with a reason** — never drop silently.

| Input reality | Action |
|---|---|
| **Mixed-mode file** — some rows have a name, some only a title, some only a domain | Classify each row independently as a title search or a named-person lookup |
| **Domain in disguise** — inside an email, a URL with `utm_`/path, or a LinkedIn *company* URL | Extract and normalize to the bare domain |
| **Name quirks** — `Last, First`, ALL CAPS, `Dr.`/`Jr.` suffixes, accents, nicknames (Bob↔Robert) | Normalize; expand nicknames before searching |
| **Personal-email domain as the "company"** — `gmail.com`, `yahoo.com`, `outlook.com` | Detect → can't role-pattern → skip with reason |
| **LinkedIn profile URL instead of a name** | Use it directly (Blitz/Findymail accept a LinkedIn URL) → skip the find step, save credit |
| **Parent vs subsidiary / rebranded / acquired domain** — old domain redirects | Resolve to the current live domain first |
| **Multiple domains or people in one cell** — comma-separated | Explode into separate rows |
| **Non-English titles** — e.g. `Geschäftsführer` = Managing Director | Translate to the searchable English title so the waterfall matches |
| **Garbled / empty rows** | Skip with reason; never crash the run |

## Domain normalization (used everywhere)

Lowercase → strip `https://` / `http://` → strip `www.` → strip path/query → strip sub-domain (`careers.acme.com` → `acme.com`). This same normalized form is the dedupe key.

## Auto-derive a missing domain

- From an email: take everything after `@` (100% reliable).
- From a website/URL: normalize as above (reliable).
- From a company name only: attempt a lookup, flag the result `derived` (can be wrong — let the user see it's a guess).

## Full-name rule (named-person lookups)

A named-person search needs a **complete** name (first + last). A lone first or last name is too ambiguous to resolve safely — ask for the full name before searching. If multiple people share the full name at the domain, return them all and note "found N people named X."
