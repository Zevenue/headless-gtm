# Variable Archetypes

Four recurring patterns that cover most outbound personalization variables. Most campaigns can be expressed using these four; anything that doesn't fit is a candidate for a **novel** variable and needs explicit reasoning from first principles.

## 1. Verbatim-pain

**What it captures**: the pain in the prospect's own voice, pulled directly from a source they wrote or published.

**Why it works**: prospects recognize their own words. Reduces "marketing pitch" feel.

**Grammar**: infinitive phrase ("validate X", "coordinate Y").

**Source**: almost always JD text. Occasionally website careers-page copy or About-us language.

**Example**: `JD_Pain_Point` → "validate transactional data accuracy prior to submission"

**Target-sentence pattern**: "I saw your team is hiring someone to {{JD_Pain_Point}}..."

**When to use**: any time you can get the prospect's own role description. Almost universal for outbound targeting hiring-based signals.

---

## 2. Manual-task

**What it captures**: the day-to-day grind inferred from the verbatim pain. The action that fills their week.

**Why it works**: creates a vivid Monday-morning picture. Makes the prospect feel seen.

**Grammar**: gerund, lowercase, no leading article ("chasing suppliers", "reconciling invoices").

**Source**: inferred via Claygent from the same JD that produced the verbatim pain.

**Example**: `Manual_Task` → "chasing suppliers for ETAs and clarifications"

**Target-sentence pattern**: "40% of your week is {{manual_task}}..."

**When to use**: when the copy needs a concrete day-to-day hook. Pairs with verbatim-pain: the pain is what the JD says, the manual-task is what it actually looks like.

---

## 3. Strategic-alternative

**What it captures**: what the prospect *should* be doing if the manual grind were removed. The aspirational frame.

**Why it works**: creates the contrast. Positions the solution without pitching it.

**Grammar**: noun phrase ("strategic sourcing", "demand planning", "supplier performance management").

**Source**: domain-mapped (manual table), not scraped. Values come from the campaign owner's knowledge of what strategic work looks like in the prospect's role.

**Example**: `high_value_task` → "strategic sourcing"

**Target-sentence pattern**: "...instead of {{high_value_task}}."

**When to use**: when the campaign's emotional move is "you're doing the wrong thing with your time." Most pain-based outbound can use it.

**Note on sourcing**: because values are domain-mapped, the mapping table itself is the artifact. The variable's "extraction" is a Clay formula or VLOOKUP against the segment, not a Claygent call.

---

## 4. Failure-mode

**What it captures**: the specific thing that breaks and lands in their inbox. The concrete failure.

**Why it works**: specificity beats generality. "A mismatched PO" is stickier than "supply chain issues."

**Grammar**: noun phrase with article ("a mismatched PO", "an unconfirmed material receipt", "a late shipment with no ETA").

**Source**: domain-mapped, sometimes with JD-derived context.

**Example**: `inbox_risk` → "a mismatched PO"

**Target-sentence pattern**: "One {{inbox_risk}} and you're stuck reconciling for hours."

**When to use**: when the campaign leans on fear-of-failure or reactive firefighting. Strong for ops/procurement/finance roles where things do break regularly.

---

## When the angle doesn't fit an archetype

Sometimes the campaign needs a variable that's not pain-based at all. Examples:
- A competitor/tool name they're using (→ TheirStack or JD-derived)
- A recent event (funding, launch, acquisition - → Crunchbase or press)
- A person's recent LinkedIn post topic (→ Phantombuster + Claygent)
- A specific metric they publish (→ website scrape)
- A conference they spoke at or panel they joined (→ manual research + Claygent)

These are **novel variables**. For each, spec it like the four archetypes above but add a **justification** field: why this variable, why this source, why it fits the target sentence. Don't default to novel - it's more work and higher failure rate. Exhaust the four archetypes first.

## Archetype checklist

Before finalizing a variable spec, confirm:
- [ ] Does the variable name match its archetype? (e.g., `*_task` for manual-task, `*_risk` for failure-mode)
- [ ] Does the grammar form match the target sentence?
- [ ] Is the source the right one for this archetype? (see `source-selection.md`)
- [ ] Does the Claygent prompt (or mapping table) enforce the grammar - not a downstream step?
- [ ] Is there a fallback value?
- [ ] Does coverage pass the threshold in `context/playbooks/copy-variable-design.md` for this segment?
