# Headless GTM - agent notes

This repo is an outbound GTM pipeline packaged as agent skills (the SKILL.md standard). It works in Claude Code and Codex.

## Where things are

- Skills live in `.claude/skills/` - one folder per skill, each with a `SKILL.md` spec. `.agents/skills` points at the same directory so Codex discovers them at repo level.
- The chain skills are numbered `00`-`06` by layer: router, discovery + qualification, extraction, signals, judgment, email resolution. `_shared/CONVENTIONS.md` defines the record contract every chain skill reads and writes (`records.jsonl`, additive fields, run folders, resume).
- The writing skills (`email-writer`, `creative-variable`, `prospect-posts`, `gtm-context`) sit downstream of the chain.

## Operating rules

- For any multi-step ask (a full list build, a campaign, "what would this cost"), start with `00-gtm-router` - it plans the chain and prices it before anything runs.
- Never spend API credits without presenting the estimate and getting a go-ahead. Every chain skill documents its own spend gate; respect them.
- API keys come from the environment (`cp .env.example .env`). Every key is optional - skip layers whose key is missing and say so, never crash and never hardcode a key.
- Each skill's `SKILL.md` is the authoritative spec for inputs, outputs, and cost rules. Read it before running the skill.
