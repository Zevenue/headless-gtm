# signal-builder

The judgment layer (step 05) of the API-first GTM chain. Takes scraped website
markdown (03-firecrawl-research), structured vendor signals (04-crustdata-signals),
or a bare URL, and emits ranked, provenance-backed outbound signals: the exact
quotable sentence, source URL, a 1-10 score, and a recommended campaign approach
(Pain-led / Value-led / Segment fallback) per signal.

This is the one skill in the chain with no vendor behind it - the model is the
engine. No API key, no credits.

## What it does

- Judges evidence against your client's ICP: which findings are triggers, which are noise
- Scores 1-10 against fixed anchors, with per-shape calibration (`b2b-saas` | `vertical-smb`)
- Maps every signal to a campaign approach with the email shape it implies
- Enforces provenance: web signals quote the page verbatim; structured signals cite `vendor:section:domain`
- Batch mode composes with the chain: merges upstream `records.jsonl`, judges per domain, emits validated records for 06-resolution and the router
- Always produces a fallback approach for the prospects where nothing lands

## Setup

None. `scripts/signal_io.py` is stdlib-only Python. The optional standalone-URL mode
uses the 03-firecrawl-research skill if installed, or any plain fetch tool otherwise.

## Layout

```
05-signal-builder/
├── SKILL.md                              method, scoring anchors, output contracts
├── references/
│   ├── signal-types-b2b-saas.md          B2B SaaS calibration catalog
│   ├── signal-types-vertical-smb.md      vertical SMB calibration catalog
│   └── calibration-guide.md              reply-gym format for calibrating new verticals
└── scripts/
    └── signal_io.py                      collect / emit / status - batch chain I/O
```

Evals live outside the skill, at `_evals/05-signal-builder/` - see
[`_evals/README.md`](../_evals/README.md) for why.

Calibration target: (A) Opus-optimized (see the repo's authoring standard).

Built at [Zevenue](https://zevenue.com), a GTM engineering firm.
