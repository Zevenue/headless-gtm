# Contributing

These are the Zevenue GTM skills we use in production, published for anyone running outbound. Contributions from the Zevenue team and the community are welcome.

## The one rule that matters

**This repo is public. Treat everything in it as world-readable, forever.**

Nothing here may contain client or prospect names, staff names, pricing, margins, retainers, deal sizes, real call data, internal file paths, or secrets. A skill is only ready for this repo once it is fully generic - it should read like a framework, not like an account.

## Where to build (Zevenue team)

Build and iterate skills in the **private** workspace first, where real client context is safe to work with. Port a skill here only once it's sanitized - the public version should carry the *method*, not the *account it was tuned on*.

Practically: develop privately → strip everything account-specific → open a PR here with generic examples.

## What stays out of this repo

Keep these in the private workspace, not here:

- Anything with client/prospect names, logos, or identifying details
- Anything with pricing, margins, retainers, deal sizes, or GMV figures
- Reply/messaging skills tuned to one named account
- Sales collateral or proposal generators with embedded deal data
- Bookkeeping, finance, or compensation workflows
- Real call transcripts, prospect lists, or any PII

When in doubt, leave it out and ask Yusuf.

## How to contribute

1. **Branch** off `main` (`feat/skill-name` or `fix/...`).
2. **Build or edit** the skill under `.claude/skills/<name>/SKILL.md`. Keep the input/output contract explicit. Use generic, fabricated examples.
3. **Scan locally** before you push:
   ```bash
   python utils/leak_scan.py
   ```
   Fix anything it flags. If a flagged line is genuinely safe, add a trailing `# leakscan:ignore`.
4. **Open a PR.** Fill in the sanitization checklist in the PR template.
5. The **leak-scan** check runs automatically and must pass. **Yusuf reviews** every PR (CODEOWNERS) before it merges.

`main` is protected - changes land only through a reviewed PR. That review is the gate that keeps this repo clean.

## Skill conventions

- One skill per directory under `.claude/skills/<name>/`, defined in `SKILL.md`.
- State inputs and outputs explicitly; skills should be reproducible, not magic prompts.
- API-backed skills read credentials from environment variables (see `.env.example`) - never hardcode keys.
- If a skill needs a Python helper, put it in `utils/` and add deps to `requirements.txt`.

## Questions

Open an issue or reach Yusuf at yusuf@zevenue.com.
