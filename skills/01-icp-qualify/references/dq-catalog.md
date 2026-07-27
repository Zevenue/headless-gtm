# Disqualification Catalog

Every category a company can be disqualified under, with the evidence that
justifies it. A DQ always cites its category and quotable evidence; if the
evidence isn't there, the verdict is `uncertain`, not `disqualified`.

## Hard disqualifications

| Category | Definition | Detection evidence |
|---|---|---|
| `competitor` | The company sells in the client's own product category | Their site/description describes the same offering the client sells; product pages in the category; category keywords in the client's exclusion list |
| `acquired` | Acquired, merged, or absorbed - no longer an independent buyer | "Now part of / acquired by" language; domain redirects to the acquirer; vendor `acquired_by` field; acquirer branding on the site |
| `size-out-of-band` | Headcount outside the ICP's hard band | A stated or vendor-reported headcount outside the band; trust the freshest source when discovery data and enrichment disagree |
| `geo-mismatch` | Operating base outside the ICP's geographies | HQ/team location evidence contradicting the target geo; a registration-only entity in the target country with the real team elsewhere counts as a mismatch when the ICP requires local presence |
| `not-a-company` | The domain isn't an operating business | Directory or listicle site, SEO blog, template/placeholder page, personal page, dormant site with years-old content |
| `wrong-business` | A real business, but not in the ICP's category at all | What they actually sell has no overlap with the ICP definition (e.g. a training school or marketing agency surfacing in a software-company search) |
| `existing-relationship` | Already a customer, partner, or named exclusion | Present on the client's exclusion list |

## Flags - record, don't disqualify

| Flag | Meaning | Why it's not a DQ |
|---|---|---|
| `rebrand` | Company recently renamed; discovery data carries the old name | Same buyer, wrong label - fix the name before copywriting |
| `stale-data` | Discovery fields contradict fresher evidence (size, title, status) | Re-judge on the fresh evidence; the company may still fit |
| `distributed-team` | Legal HQ in the target geo, team split across others | Qualify if the ICP cares about the market served; flag for sending-time and copy |
| `weak-signal` | Fits the ICP but nothing suggests urgency | Fit is this skill's question; urgency belongs to the signal layer |

## Judgment guidance

- **Hybrids qualify.** A company doing the ICP's activity *plus* something else
  (a product company that also does services, a manufacturer that also
  integrates) is qualified when the ICP-relevant side is real - look for named
  products, dedicated pages, a team. Don't disqualify a hybrid by its weaker
  half.
- **Category edges take the client's view.** When "competitor vs. adjacent tool"
  is genuinely arguable, mark `uncertain` and let the calibration loop decide -
  the client knows their competitive map better than any heuristic.
- **One category per DQ.** Pick the strongest, best-evidenced category; put the
  rest in `flags`. Multi-category DQs read as pile-ons and hide the real reason.
- **Expected base rates.** On raw discovery output it is normal for a third to
  half of records to fail qualification - acquisitions and stale size data alone
  account for a large share. A 0% DQ rate on a raw list usually means the gate
  isn't looking; a 90% rate usually means the ICP bounds are wrong. Either
  extreme is a prompt to re-check before proceeding.
