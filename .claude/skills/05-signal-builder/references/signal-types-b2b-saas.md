# Signal Types — `b2b-saas` calibration

Catalog for prospects that are funded or funding-track companies with title-based
org charts: SaaS, marketplaces, tech-enabled services, enterprise software buyers.
Calibrated against classified enterprise B2B reply data. Each type lists what to
look for, what it implies, the score band, and the default approach - the anchors
in SKILL.md still govern; this file adjusts within them.

Contents: 1. Tech stack · 2. Hiring · 3. Funding & growth · 4. Operational & review
· 5. Content & awareness · 6. Structured-data judgment · 7. Combinations

---

## 1. Tech stack signals

### Direct competitor in place
**Look for:** a product that competes head-on with the client's offering. Shows up in
integrations pages, footers, careers JDs ("experience with [tool]"), case studies,
review sites.
**Implies:** they've bought into the problem space; the open question is whether the
incumbent still earns its seat.
**Sharpeners:** negative reviews of the incumbent, several tools duct-taped to do what
the client does in one, incumbent sunsetting or repricing, JDs demanding incumbent
experience (deep investment - harder switch, but validated pain).
**Score:** 8-10 with friction evidence; 5-7 for bare usage.
**Approach:** PQS - "Noticed you run [competitor]. Teams on it usually hit [pain]. You?"

### Adjacent tools, no direct solution
**Look for:** same-ecosystem tools that solve neighboring problems.
**Implies:** the problem exists and is being patched around.
**Score:** 5-7 · **Approach:** Pain-led, using the adjacent stack as the evidence the
problem persists.

### No tooling / visibly manual
**Look for:** no category tool anywhere; JDs describing manual workflows; process
pages that read like spreadsheets.
**Implies:** pain not yet acute, unaware, or resource-constrained - stage decides which.
**Score:** 4-6 (a Series B running manual scores the top of the band; pre-seed the bottom).
**Approach:** PVP - show them what automated looks like for a company their shape.

## 2. Hiring signals

### Role the product replaces or augments
**Look for:** open roles whose core responsibilities overlap what the client's product
does. Careers pages, job boards, postings data.
**Implies:** pain acute enough to fund headcount; product-vs-salary ROI writes itself.
**Score:** 8-10, higher with multiple identical openings.
**Approach:** PQS - "Hiring a [role]? Most of that job is [task the product automates]."

### Hiring around the function
**Look for:** growth in the department the client serves, without the exact role.
**Implies:** the underlying operational load is about to grow with the team.
**Score:** 5-7 · **Approach:** Pain-led on the coordination cost of the growth.

### Leadership hire in the function
**Look for:** new VP / Head / Director in the relevant function - careers page
announcements, blog, structured people-move data.
**Implies:** new leaders audit their systems in the first 90 days and buy quick wins.
**Score:** 7-9 · **Approach:** PQS - "New [title]s usually audit [area] in the first
quarter - what's the plan for [pain]?"

### JD language describing the exact pain
**Look for:** posting copy that narrates the problem - "manage escalations across
email and phone", "reduce manual reconciliation", "wrangle multiple tools".
**Implies:** the pain is written into how they describe their own operations.
**Score:** 6-8 · **Approach:** PQS, quoting the JD line back (this is the single most
quotable signal type - the verbatim sentence is already written for you).

## 3. Funding & growth signals

### Fresh raise (≤ 6 months)
**Look for:** seed through C announced recently - blog, press, structured funding data.
**Implies:** capital plus milestone pressure equals willingness to buy acceleration.
**Score:** 6-8; top of band when the stated use of funds touches the client's area.
**Approach:** Pain-led on the scaling challenge the raise creates.

### Expansion moves
**Look for:** new offices or markets, product-line launches, headcount surging in a
region or department.
**Implies:** processes that worked at the old size are breaking.
**Score:** 6-7 · **Approach:** Pain-led or PVP tied to the specific expansion.

## 4. Operational & review signals

### Their customers complain about the gap
**Look for:** review-site or app-store complaints tracing to an operational gap the
client fills (slow onboarding, weak integrations, manual steps, support lag).
**Implies:** the prospect's own customers are feeling the pain.
**Score:** 7-9 when complaints name the problem area.
**Approach:** PVP - "Read your recent reviews; the pattern is [X]. Here's how teams
fix it."

### Public complaints or visible gaps
**Look for:** forum threads, social posts, community chatter about their operational
problems.
**Implies:** pain real enough to be discussed in public.
**Score:** 7-9 · **Approach:** PQS referencing the pattern (not the individual post).

### Pricing / business-model reads
**Look for:** pricing page structure, fee models, who they monetize.
**Implies:** context for tailoring economics - rarely a standalone trigger.
**Score:** 4-6 · **Approach:** feed as context into another signal's campaign.

## 5. Content & awareness signals

### They write about the problem
**Look for:** blog or changelog posts about the challenge the client solves.
**Implies:** problem-aware; possibly evaluating or building in-house.
**Score:** 6-8, higher when recent.
**Approach:** PVP - reference their post, add the insight it stopped short of.

### Conference presence
**Look for:** speaking slots or attendance at events in the client's space.
**Implies:** investing time in the problem space; often actively evaluating.
**Score:** 5-7 · **Approach:** PQS with the event as the hook.

## 6. Structured-data judgment (04-crustdata-signals input)

Structured blocks arrive as facts. Judge them against icp_context before they count:

| Fact in the bundle | Counts as a signal when | Type to use |
|---|---|---|
| Funding round (type, amount, date) | ≤ 6 months old, or stated use of funds touches the client's area | `funding-fresh-raise` |
| Headcount growth % | growth concentrates load on the function the client serves (pair with dept data or hiring evidence) | `growth-headcount` |
| Department growth | the growing department is the one the client sells into | `growth-department` |
| Recent hires list | a hire's title is the role the product replaces (8-10) or leads the function (7-9); bulk junior hires alone stay 5-6 | `hiring-people-move` |
| Open job postings | title or JD maps to the pain (see section 2) | `hiring-role-replaced` / `hiring-jd-language` |

Cite structured facts as `vendor:section:domain` (e.g. `crustdata:recent_hires:acme.com`)
and state them exactly - round, amount, date, name, title. A 14-month-old funding
round or a 3% growth wobble is context, not a signal; leave it out of the top 5.

## 7. Combinations (lead with these when present)

| Combination | Score | Why it outranks the parts |
|---|---|---|
| Hiring the role + competitor in place with friction | 9-10 | budgeted pain plus switching intent |
| Fresh raise + no tooling | 8-9 | budget plus urgency, no incumbent to displace |
| Hiring + writing about the problem | 7-9 | active evaluation in progress |
| Competitor + their customers complaining | 8-10 | the incumbent is failing publicly |
| Expansion + visibly manual process | 7-8 | the break point is scheduled |

Write a combination as one signal: strongest evidence carries `signal_sentence` and
`source_url`; the supporting fact goes in `notes`.
