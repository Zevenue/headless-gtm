# Worked Example - Shopify Subscription Software Outbound

A canonical end-to-end walkthrough of a creative variable spec for a real-shape campaign. Use this as the template when you spec a new campaign.

## The campaign

A B2B software product helps Shopify DTC brands manage their subscription program - cancellation flows, dunning, subscriber data, replenishment forecasting. Outbound targets Director/VP of Ecommerce, Operations, or Growth at Shopify brands with $1M+ GMV running (or building) a subscription product.

## Campaign angles

- **Angle A - Hiring trigger**: "You're hiring an ecom/ops leader - they'll evaluate your subscription stack in 90 days"
- **Angle B - Stage value**: "You're building/scaling subscriptions - here's what brands at your stage choose"
- **Angle C - Pain-led switching**: "Your subscription tool is costing you revenue you can't see"

## Sources

- **Primary**: Company website (subscription page, product pages, pricing) - reveals subscription model and product catalog in the prospect's own words
- **Primary**: TheirStack / Prospeo (job postings, tech stack) - reveals hiring signals and current subscription tool
- **Secondary**: LinkedIn posts (via Phantombuster or similar) - reveals prospect's stated values, priorities, and language patterns
- **Secondary**: Prospeo enrichment (funding data, employee count) - firmographic context for "at your stage" framing
- **Unusual sources to consider**: Shopify App Store reviews for the major subscription tools - would reveal specific friction with the prospect's current setup. **Tier: ABM-only.** Worth doing for top accounts but not scalable. Confirm with the campaign owner before building.

## Variables

### 1. `{{subscription_model}}` - novel (product-context)

| Field | Value |
|---|---|
| Grammar | noun phrase, lowercase ("subscribe-and-save at 20% off", "monthly flavor drops", "a subscription program in development") |
| Source | Company website - `/pages/subscribe`, `/collections/subscribe`, or homepage subscription CTA |
| Extraction | Claygent on website URL |
| Fallback | "your subscription program" |
| Coverage | ~85% of Tier 1+2 companies; ~40% of Tier 3 (durable goods) - for Tier 3, hardcode "a membership or loyalty program" instead |
| Target sentence | "I saw you're running {{subscription_model}} on Shopify." |

**Claygent prompt:**
```
You are extracting a subscription product description from an ecommerce website. This phrase will be inserted into an outbound email.

Steps:
1. Visit the company's website and look for any subscription, subscribe-and-save, membership, or recurring purchase offering.
2. If found, describe what it is in 3-8 words: the discount, the frequency, or the key benefit they advertise.
3. Return the description as a lowercase noun phrase, no period, no leading article.

Constraints:
- Do not use marketing language like "amazing" or "revolutionary"
- Do not return the brand name
- Do not return more than 8 words
- If no subscription offering exists, return: NO_FIT

Return a phrase that fits naturally into this sentence: "I saw you're running {{subscription_model}} on Shopify."

Examples:
- Input: "Subscribe & Save 20% - Free shipping on every order"
  Output: subscribe-and-save at 20% off
- Input: "Join the club - monthly drops of our newest flavors, skip anytime"
  Output: monthly flavor drops with skip flexibility
- Input: "Subscribe page coming soon"
  Output: a subscription program in development
```

**Rendered examples:**
1. "I saw you're running **subscribe-and-save at 20% off** on Shopify."
2. "I saw you're running **monthly replenishment with subscriber-only perks** on Shopify."
3. "I saw you're running **a subscription program in development** on Shopify."

---

### 2. `{{current_sub_tool}}` - novel (tech-context)

| Field | Value |
|---|---|
| Grammar | proper noun or noun phrase ("Recharge", "native Shopify subscriptions", "your current setup") |
| Source | Prospeo technology data + BuiltWith for confirmation |
| Extraction | Clay formula against tech-stack field |
| Fallback | "your current setup" |
| Coverage | ~25% will have a detected tool, ~50% default to "native Shopify subscriptions", ~25% use fallback. Segment: only use in Angle C where the tool is known. |
| Target sentence | "Most teams running {{current_sub_tool}} at your scale hit a wall on cancellation flows and dunning." |

**Formula logic (no Claygent needed):**
```
IF technology_names CONTAINS "Recharge" → "Recharge"
IF technology_names CONTAINS "Skio" → "Skio"
IF technology_names CONTAINS "Bold Subscriptions" → "Bold Subscriptions"
IF technology_names CONTAINS "Loop Subscriptions" → "Loop Subscriptions"
IF technology_names CONTAINS "Ordergroove" → "Ordergroove"
IF technology_names CONTAINS "Shopify" AND none of above → "native Shopify subscriptions"
ELSE → "your current setup"
```

**Rendered examples:**
1. "Most teams running **Recharge** at your scale hit a wall on cancellation flows and dunning."
2. "Most teams running **native Shopify subscriptions** at your scale hit a wall on cancellation flows and dunning."

---

### 3. `{{ops_grind}}` - manual-task

| Field | Value |
|---|---|
| Grammar | gerund, lowercase, no leading article ("reconciling subscription shipments with your 3PL", "manually adjusting forecasts for subscriber pauses and skips") |
| Source | JD text (TheirStack) for hiring companies; domain-mapped table for non-hiring |
| Extraction | Claygent on JD (when present); VLOOKUP against product category otherwise |
| Fallback | "manually tracking subscription metrics across multiple tools" |
| Coverage | ~30% from JDs, ~70% from domain mapping. Reliable because ops pain is predictable by product category (consumable CPG → inventory forecasting; beauty/skincare → SKU variant management; durables → order bundling). |
| Target sentence | "Your ops team is spending 10+ hours a week {{ops_grind}} instead of {{strategic_work}}." |

**Claygent prompt (for JD-sourced rows):**
```
You are extracting a manual operational task from a job description for an ecommerce company. This phrase will be inserted into an outbound email about subscription management.

Steps:
1. Read the full job description.
2. Identify responsibilities related to: subscription management, recurring order processing, inventory forecasting for subscriptions, payment reconciliation, dunning/failed payment handling, subscriber data management, or subscription-related customer support.
3. If found, select the single most tedious/manual responsibility.
4. Rewrite it as a gerund phrase (lowercase, no leading article) that describes what the person actually does day-to-day.

Constraints:
- Do not use the company name
- Do not include job title or seniority
- Do not return marketing language
- Maximum 10 words
- If no subscription-related operational task is identifiable, return: NO_FIT

Return a phrase that fits naturally into this sentence: "Your ops team is spending 10+ hours a week {{ops_grind}} instead of strategic work."

Examples:
- Input: "Manage subscription order fulfillment, coordinate with 3PL on recurring shipments, and reconcile subscription revenue against Shopify data"
  Output: reconciling subscription shipments against Shopify revenue data
- Input: "Handle failed payment retries, manage subscriber cancellation requests, and update customer billing information"
  Output: chasing failed payments and processing cancellation requests
- Input: "Forecast demand for subscription SKUs, adjusting for pauses, skips, and seasonal variation"
  Output: manually adjusting inventory forecasts for subscriber pauses and skips
```

**Domain mapping table (for non-JD rows):**

| Product category | `ops_grind` value |
|---|---|
| Consumable food/bev | reconciling subscription shipments against retail and DTC demand |
| Beauty/skincare | managing subscription SKU variants and replenishment cycles |
| Wellness/supplements | tracking subscriber churn and coordinating replacement shipments |
| Household/durables | manually bundling orders and managing gifting fulfillment |
| General DTC | pulling subscription performance data from multiple dashboards |

---

### 4. `{{strategic_work}}` - strategic-alternative

| Field | Value |
|---|---|
| Grammar | noun phrase, lowercase ("demand planning", "growth strategy", "product development") |
| Source | Domain-mapped by role title - the aspirational frame |
| Extraction | Clay formula / VLOOKUP against role title |
| Fallback | "strategic initiatives" |
| Coverage | 100% (always has a value) |
| Target sentence | "Your ops team is spending 10+ hours a week {{ops_grind}} instead of {{strategic_work}}." |

**Mapping table:**

| Role | `strategic_work` value |
|---|---|
| Director/VP of Operations | demand planning and vendor strategy |
| Director/VP of Ecommerce | conversion optimization and subscriber growth |
| Director/VP of Growth | retention strategy and LTV expansion |
| Director/VP of Supply Chain | supplier negotiations and cost reduction |
| Director/VP of Marketing | brand strategy and channel expansion |
| CEO/Founder | strategic roadmap and fundraising |

---

### 5. `{{revenue_leak}}` - failure-mode

| Field | Value |
|---|---|
| Grammar | noun phrase with article ("a failed payment that auto-cancels a loyal subscriber") |
| Source | Domain-mapped by product category |
| Extraction | Clay formula / VLOOKUP |
| Fallback | "a failed payment that silently churns a subscriber" |
| Coverage | 100% |
| Target sentence | "One {{revenue_leak}} and you've lost revenue you didn't even know was at risk." |

**Mapping table:**

| Product category | `revenue_leak` value |
|---|---|
| Consumable food/bev | a failed payment that auto-cancels a $50/month subscriber |
| Beauty/skincare | a botched subscription renewal that churns a high-LTV customer |
| Wellness/supplements | a declined card that silently drops a subscriber you spent $40 to acquire |
| Household/durables | a gifting order that gets double-charged and triggers a chargeback |
| General DTC | a failed payment that silently churns a subscriber |

---

### 6. `{{hiring_signal}}` - novel (trigger)

| Field | Value |
|---|---|
| Grammar | full clause, lowercase ("you're hiring a senior director of ecommerce") |
| Source | TheirStack API + Prospeo enrichment |
| Extraction | Clay formula against TheirStack data |
| Fallback | DO NOT USE - segment the list. Only Angle A uses this variable. |
| Coverage | ~30% of target list. Segment variable, not universal. |
| Target sentence | "I saw {{hiring_signal}} - new leaders in that role usually audit the subscription stack in their first quarter." |

**Formula logic:**
```
IF open_role EXISTS AND title MATCHES ecommerce/operations/growth/digital:
  "you're hiring " + LOWER(job_title)
IF recent_hire EXISTS (from LinkedIn new-position posts):
  "you just brought on a new " + LOWER(title)
ELSE → DO NOT USE (exclude row from Angle A segment)
```

## Variable × Campaign Angle Matrix

| Variable | Angle A (Hiring trigger) | Angle B (Building/scaling) | Angle C (Switching pain) |
|---|---|---|---|
| `subscription_model` | - | Required | Required |
| `current_sub_tool` | - | - | Required |
| `ops_grind` | Optional | Optional | Required |
| `strategic_work` | Optional | Optional | Required |
| `revenue_leak` | - | Optional | Required |
| `hiring_signal` | Required | - | - |

**Angle A** uses the fewest variables (the hiring signal is the hook - keep it clean).
**Angle B** is value-led, light on pain variables.
**Angle C** stacks the most (pain + grind + failure mode + tool name).

## Why this set of variables works

1. **Tight source mapping**: each variable has exactly one source of truth (website / tech stack / JD / domain table).
2. **Archetype reuse**: `ops_grind` is manual-task, `strategic_work` is strategic-alternative, `revenue_leak` is failure-mode. The remaining three (`subscription_model`, `current_sub_tool`, `hiring_signal`) are novel but justified by the angle.
3. **Sentence-driven design**: variables were designed backwards from target sentences, not forward from "what could we extract?"
4. **Grammar enforced at extraction**: gerund / noun-phrase / clause forms are specified in each Claygent prompt or formula, not normalized downstream.
5. **Coverage discipline**: variables with <40% coverage (`current_sub_tool`, `hiring_signal`) are gated to specific angles, not used universally.

## Adapting this template to a new campaign

When you spec a new campaign, walk the four archetype questions:

1. **Verbatim-pain** - is there a source (usually a JD) that contains the prospect's pain in their own words? What infinitive phrase would you extract?
2. **Manual-task** - what does that pain *look like* on a Tuesday afternoon? What gerund describes the day-to-day grind?
3. **Strategic-alternative** - what should they be doing instead? Build the noun-phrase mapping table by persona.
4. **Failure-mode** - what's the specific thing that breaks and lands in their inbox? Build the noun-phrase mapping table by category.

Then ask whether the angle implies any **novel** variables outside the four (a tech-stack name, a hiring trigger, a product-context anchor). For each novel variable, justify the source and tier the coverage. See "When the angle doesn't fit an archetype" in `variable-archetypes.md`.
