# Context Schema

The schemas below are what `gtm-context` writes and what every other skill reads. Keep them tight - these files reload every session.

---

## `context/offer.md`

```markdown
# Offer

## What we sell
One sentence. The outcome, not the feature.

## Who we sell to
- Titles: VP Sales, Head of RevOps, Founder
- Company stage: Series A through Series C
- Size: 30-300 people
- Vertical: B2B SaaS (or "any" if cross-vertical)

## The problem we solve
2-4 sentences. What the prospect is doing today that this replaces or makes 10x better.

## Trigger event
The specific moment a prospect realizes they need this. Examples:
- They just hired their first SDR
- Their previous tool got acquired and is being shut down
- They closed a Series B and outbound is now the bottleneck

## Most common objection
The #1 reason prospects don't buy. One sentence.

## Proof
One or two named customers + outcome. Or a statistic. Real proof, not "we've helped many companies."
```

### Example - filled in

```markdown
# Offer

## What we sell
We build the outbound system that turns a Series A team's first SDR into a pipeline machine in 90 days.

## Who we sell to
- Titles: VP Sales, Head of GTM, Founder/CEO at < $5M ARR
- Stage: Series A to Series B
- Size: 20-150 people
- Vertical: B2B SaaS (vertical-agnostic, but lean toward dev tools / RevOps / vertical SaaS)

## The problem we solve
Founders raise a Series A, hire one SDR, and watch them flounder for 6 months because there's no playbook, no signals, and no system. We build the outbound engine - signals, sequences, deliverability, reporting - and hand it off so the SDR ramps in weeks instead of quarters.

## Trigger event
Just hired their first SDR (or first sales lead) post-Series-A. The clock is ticking on the SDR's ramp window.

## Most common objection
"We're going to hire a head of sales who will figure this out." (Reality: they won't, for 6 months. The system needs to exist before the leader arrives.)

## Proof
Built the outbound engine for Sweatpals (Series A, $16M raised) - went from 0 to 200 booked meetings in 90 days. Mandel AI (YC) is running on the same playbook now.
```

---

## `context/icp.md`

```markdown
# ICP

## Engagement signals
What makes a prospect a great fit. 3-7 bullets.
- Has tried outbound before and it stalled
- Just raised a Series A or B
- Hiring an SDR or RevOps lead
- Founder is hands-on with sales
- Has a defined ICP and is willing to iterate

## Anti-signals
What makes you walk away. 3-5 bullets.
- Demanding "guaranteed meetings" before any iteration
- Wants the cheapest possible execution, no interest in systems
- Refuses to change internal workflow or adopt new tools
- Pushing for vague, undefined scope ("just fix our GTM")
- Pre-Series A with no funding signal

## Disqualifying conditions
Hard exclusions. The deal does not happen if any of these are true.
- Less than $1M ARR
- No existing GTM lead (founder-only sales)
- Buyer doesn't have budget authority

## Buying committee
Who actually signs off + who blocks.
- Decision maker: Founder/CEO (early stage), VP Sales (later stage)
- Champion: Head of GTM, RevOps lead
- Blocker: Often a marketing leader who wants to own messaging
```

---

## `context/offer.md` invariants the other skills depend on

- `## What we sell` is the one-liner that `email-writer` uses for value-prop framing.
- `## Trigger event` is what `signal-builder` looks for when scoring prospects 8+.
- `## Most common objection` shapes the second email in every sequence.
- `## Proof` populates the proof line in `email-writer` outputs.

---

## `context/icp.md` invariants

- `## Engagement signals` are what `signal-builder` weights positively.
- `## Anti-signals` are what `signal-builder` flags as deal-killers.
- `## Buying committee` is what `prospect-posts` and `job-search` use to filter who's worth scraping.

---

## Editing rules

- Keep both files under 600 words combined. They reload every session - bigger files cost tokens and make agents slower.
- One file per concept. Don't merge offer.md and icp.md. Don't split offer.md into 5 sub-files.
- Update at most quarterly. If the offer is changing every week, the offer isn't ready to outbound on yet.
