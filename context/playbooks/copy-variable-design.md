# Copy Variable Design Playbook

## Purpose
When writing outbound email copy for a client campaign, identify where hardcoded language should be replaced with dynamic variables to improve relevance across segments - and where it should stay hardcoded for readability.

## When to use
- Drafting or reviewing cold email copy that will be sent to multiple segments (different titles, industries, pain points)
- Anytime a line in the email references a specific pain, task, outcome, or persona attribute that doesn't apply uniformly across the prospect list

## Process

### Step 1: Audit the copy against the data
For each line in the email, ask:
- Does this statement apply to >80% of the list? If yes, it can stay hardcoded.
- Does it apply to 40-80%? Flag it - it either needs a variable or a safer generalization.
- Does it apply to <40%? It must be variablized or removed.

### Step 2: Check variable grammar fit
Before creating a variable, test it in-sentence with 3-4 real values from the data:
- Does it read naturally when substituted? (e.g., "40% of their week will be {{manual_task}}" - works if manual_task is an action phrase like "chasing suppliers for ETAs")
- Does it break grammatically with some values? If yes, either rewrite the sentence structure or normalize the variable values to a consistent grammatical form.

**Variable value rules:**
- Action variables (what someone does): use gerund form - "chasing X", "confirming Y", "reconciling Z"
- Responsibility variables (what the JD says): use infinitive form - "validate X", "coordinate Y"
- Noun variables (a thing): use noun phrase - "supplier exceptions", "pricing discrepancies"
- Outcome variables (what they should be doing instead): use noun phrase - "strategic sourcing", "demand planning"

### Step 3: Design the variable
For each new variable, define:
1. **Name**: snake_case, descriptive (e.g., `high_value_task`, `inbox_risk`, `manual_task`)
2. **Description**: What it represents in one sentence
3. **Grammar form**: gerund / infinitive / noun phrase
4. **Source**: Where the value comes from (JD text, enrichment, manual mapping, Clay formula)
5. **Fallback**: A safe default if the value is missing or unresolvable
6. **Coverage**: What % of the list it applies to and which segments

### Step 4: Build the mapping table
Create a CSV or table mapping the variable values to segments. Include:
- The variable name
- The segment or condition (title, pain point flag, etc.)
- The value for that segment
- A fallback value

### Step 5: Validate with rendered examples
Render 3-5 full emails with real data substituted. Read them aloud. Check for:
- Grammatical breaks
- Lines that feel generic when variablized (sometimes hardcoded is better)
- Values that are too long and break email scanning rhythm

## Decision framework: variable vs. hardcode vs. remove

| Condition | Action |
|---|---|
| Applies to >80% of list, reads naturally | Keep hardcoded |
| Applies to 40-80%, easy to variablize | Create variable |
| Applies to 40-80%, awkward as variable | Generalize the language |
| Applies to <40% | Remove or create a segment-specific version |
| Critical for the hook/emotional punch | Keep hardcoded even if imperfect - test it |

## Anti-patterns
- Over-variablizing: every other word is a {{variable}} - kills readability and feels like a mail merge
- Under-variablizing: referencing "price discrepancies" when only 25% of the list deals with pricing
- Grammar mismatch: variable values don't fit the sentence structure
- Missing fallbacks: blank variables = broken emails in production

## Output format
When suggesting variables, provide:
1. The variable name and definition
2. A mapping table (segment → value)
3. The updated copy with variables inserted
4. 3 rendered examples with real data
5. Flags for any lines where hardcoding is the better call
