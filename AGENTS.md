# Headless GTM - agent notes

This repo is an outbound GTM pipeline packaged as agent skills (the SKILL.md standard). It works in Claude Code and Codex.

## Where things are

- Skills live in `skills/` - one folder per skill, each with a `SKILL.md` spec. `.claude/skills` and `.agents/skills` are symlinks to it, so both Claude Code and Codex discover the skills when run from this repo.
- The chain skills are numbered `00`-`06` by layer: router, discovery + qualification, extraction, signals, judgment, email resolution. `headless-gtm-shared/CONVENTIONS.md` defines the record contract every chain skill reads and writes (`records.jsonl`, additive fields, run folders, resume).
- The writing skills (`email-writer`, `creative-variable`, `prospect-posts`, `gtm-context`) sit downstream of the chain.

## Operating rules

- For any multi-step ask (a full list build, a campaign, "what would this cost"), start with `00-gtm-router` - it plans the chain and prices it before anything runs.
- Never spend API credits without presenting the estimate and getting a go-ahead. Every chain skill documents its own spend gate; respect them.
- API keys come from the environment or a `.env` file (`cp .env.example .env`). The Python scripts load `.env` themselves; **curl does not** - when calling a vendor API directly, load it in the same command (`set -a; [ -f .env ] && . ./.env; set +a`), or you'll send an empty auth header and get a misleading provider error. Every key is optional - skip layers whose key is missing and say so, never crash and never hardcode a key.
- Output goes to `./runs/<run-id>/` in the working directory, never inside a skill folder. Run-ids are prefixed with the producing step (`2026-07-27-01-prospeo-saas-us`) because every step of a chain shares that one `runs/` root. Pass records between steps by explicit path.
- Each skill's `SKILL.md` is the authoritative spec for inputs, outputs, and cost rules. Read it before running the skill.
