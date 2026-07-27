# Claygent Prompt Design

Methodology for writing Claygent (and Claude API) extraction prompts that produce values ready to drop into email copy.

## The workflow-first principle

Before writing the prompt, do the task by hand on 2-3 real prospects. Narrate each step out loud. Those steps become the prompt.

The reason: the AI will follow the same workflow you would. If you can't articulate the steps manually, the AI can't either - it just hides the failure behind plausible-sounding output.

## The four-part prompt structure

### Part 1: Describe the task
One sentence. What is the AI doing, and what does the output feed into?

> "Extract the primary supply-chain pain point mentioned in this job description. This phrase will be inserted into an outbound email sentence."

### Part 2: Break it into steps
Numbered steps the AI must follow in order. Match the manual workflow you just walked.

> 1. Read the full job description.
> 2. Identify responsibilities related to supplier coordination, PO management, or data validation.
> 3. Select the single responsibility that reads as most painful (manual, repetitive, reactive).
> 4. Rewrite it as an infinitive phrase starting with a verb (e.g., "validate...", "coordinate...", "verify...").

### Part 3: Constrain
Explicit don'ts. This is where most prompts fail silently - the AI produces something plausible but wrong.

> - Do not paraphrase the pain as marketing language.
> - Do not return more than one responsibility.
> - Do not include the word "responsible" or "will be."
> - If no clear supply-chain pain exists in the JD, return the literal string "NO_FIT" (do not guess).

### Part 4: Give input → output examples
2-3 concrete pairs. Examples teach grammar and tone faster than instructions.

> **Example 1**
> Input: "You will manage supplier communications and confirm purchase orders with vendors daily..."
> Output: "coordinate supplier communication for material quality assurance"
>
> **Example 2**
> Input: "Responsible for reconciling packing slips against received goods and flagging discrepancies..."
> Output: "verify purchase orders against received goods documentation"

## The grammar-fit instruction (critical)

Always include a line specifying the grammatical form by embedding the target sentence:

> "Return a phrase that fits naturally into this sentence: `Your week is spent {{manual_task}} instead of {{high_value_task}}.`"

Specifying the target sentence is what makes the output grammatically usable. Without it, the AI returns a full sentence, a noun, or marketing-speak randomly - and you end up cleaning it up downstream.

Grammar forms by archetype:
- **Verbatim-pain** → infinitive ("validate X", "coordinate Y")
- **Manual-task** → gerund, lowercase, no leading article ("chasing suppliers", "reconciling invoices")
- **Strategic-alternative** → noun phrase ("strategic sourcing", "vendor strategy")
- **Failure-mode** → noun phrase with article ("a mismatched PO", "an unconfirmed receipt")

## Fallbacks - always include

Every prompt needs a safe default when extraction fails. Two patterns:

**Sentinel pattern**: Return a literal string like `NO_FIT` or `NULL` that downstream formulas filter out. Good when missing data should disqualify the row.

**Safe-default pattern**: Return a generic-but-true value that still reads naturally. Good when the row should proceed regardless.

Example safe-default for `Manual_Task`:
> "If no specific manual task is identifiable, return: 'coordinating across suppliers'"

## Claygent vs Claude API - which to use

- **Claygent** (in-Clay): most extraction from per-row sources (JD text, website scrape, LinkedIn activity). Lives inside the table, re-runs automatically.
- **Claude API / ChatGPT in a separate chat**: campaign-level thinking - ICP research, angle brainstorming, prompt authoring, deep research on a sector. Not per-row.
- **Sculptor** (Clay's experimental AI): good for *analyzing* an existing Clay build (finding loopholes); careful when using it to build.

## Anti-patterns

- **Missing examples**: prompt without input→output examples returns variable quality.
- **Implicit grammar**: "extract a pain point" with no target sentence → AI returns a full sentence, a noun, or marketing-speak randomly.
- **Over-broad constraint**: "don't use jargon" without examples of what jargon looks like.
- **No fallback**: blank cell → broken email in production.
- **Prompting for multiple things at once**: one prompt per variable. Extracting `Manual_Task` and `inbox_risk` in a single call produces noisy output for both.
