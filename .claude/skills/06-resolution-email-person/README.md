# 06-resolution-email-person

The resolution layer (step 06) of the API-first GTM chain. Takes a company
domain plus an optional person name or job title and turns it into a verified,
send-safe email address - "who is the CFO at acme.com and what's their email."

The governing principle is deliverability-first: bounce rate, not find rate, is
the signal that matters. A found-but-undeliverable email is worse than no email
because it burns sender reputation, so the skill optimizes for deliverable
contacts at minimum credit cost and never returns an address as confirmed
without validation.

## What it does

- Runs a cost-ordered waterfall - AI Ark -> Prospeo -> Blitz -> Findymail -
  with ZeroBounce validation, stopping the moment a valid email lands
- Skips any rung whose API key is absent and logs which rungs were skipped
- Never spends enrichment credit without an explicit go-ahead: a mandatory
  estimation gate previews people found / not found, coverage %, and the
  credit + $ cost to enrich before anything is spent
- Tries the exact title strictly first, then broadens to similar titles,
  capped at 3 attempts per company, with a same-seniority guard so a looser
  match never swaps in a different-seniority person
- Dedupes by normalized domain before anything costly and checks prior runs
  so the same contact is never paid for twice
- Labels every result honestly: `valid`, `catch_all`, `invalid`, or
  `no_email` - it never invents a generic `info@` fallback, and an opt-in
  retry re-runs hard invalids through a different provider
- Infers a company's email pattern from one verified address, generates
  candidates for the people the providers missed, and validates them
  (labeled `pattern_inferred`)
- Works standalone on a single domain or in bulk - upstream `records.jsonl`
  from the chain, or CSV/Excel files with mislabeled columns remapped and
  reported before any spend
- Emits one record per contact (`match_type`, `email_source`,
  `verification_status`, confidence) plus an end-of-run summary

## Setup

Auth comes from environment variables - no keys are stored in the skill.

```bash
export AIARK_API_KEY="..."       # rung 0: LinkedIn URL / person id -> verified email
export PROSPEO_API_KEY="..."     # title-first finder (misses are free)
export BLITZ_API_KEY="..."       # domain-first finder (person + LinkedIn)
export FINDYMAIL_API_KEY="..."   # name+domain email finder
export ZEROBOUNCE_API_KEY="..."  # independent validation
```

The skill runs with as few as one key set. Rungs without a key are skipped,
and if ZeroBounce is absent, validation falls back to the finding provider's
bundled verdict.

## Layout

```
06-resolution-email-person/
├── SKILL.md                      waterfall logic, gates, validation, output contract
├── references/
│   ├── providers.md              endpoints, request shapes, billing rules, rate limits
│   └── input-handling.md         normalization rules for messy input files
└── runs/                         (created at runtime) records.jsonl per run
```

Evals for this skill are maintained in Zevenue's private source repo and run
before every release - skill folders ship without them.

## Position in the chain

```
05 signal-builder ──► 06 resolution ──► email-writer
```

The last chain step before copywriting. Consumes 05-signal-builder output or
any domain/contact list - a `records.jsonl` from upstream skills, a CSV of
domains, or a single ad-hoc ask. When running in the chain it adds
`verification_status` to each record without overwriting the upstream
confidence field.

Built at [Zevenue](https://zevenue.com), a GTM engineering firm.
