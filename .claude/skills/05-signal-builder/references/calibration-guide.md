# Calibration Guide — tuning signal-builder for a new vertical

The two shipped catalogs (`b2b-saas`, `vertical-smb`) cover most outbound. When a
vertical behaves differently enough that their score bands feel wrong - agencies,
public sector, healthcare providers, franchise networks - build a calibration file
for it. This guide defines the format and the data bar.

The core idea: **calibration comes from replies, not intuition.** A signal type
earns a higher band because prospects who were contacted on it replied positively
more often - not because it sounds compelling. We call the classified reply dataset
a *reply gym*.

## 1. The reply gym format

One row per reply received, joined back to the signal that drove the email:

```jsonl
{"domain": "acme.com", "signal_type": "hiring-role-replaced", "signal_score": 9,
 "approach": "PQS", "reply_class": "positive-meeting", "reply_excerpt": "...",
 "campaign": "2026-05-supply-chain", "sent_date": "2026-05-14"}
```

`reply_class` values (keep these five - comparability across verticals depends on it):

| Class | Means |
|---|---|
| `positive-meeting` | agreed to or asked about a call |
| `positive-interest` | engaged with the substance, no call yet |
| `neutral-info` | factual response, no stance ("we use X, why?") |
| `objection` | pushed back on premise, timing, or fit |
| `negative` | opt-out, annoyance, wrong person |

If replies weren't tracked per signal, you can start from campaign-level joins
(every reply in a campaign inherits the campaign's lead signal type) - noisier, but
enough to seed a first calibration.

## 2. The data bar

- **25+ classified replies** in the vertical before shifting any score band. Below
  that, use the closest shipped catalog and note the low-confidence calibration in
  your reports.
- **3+ replies on a specific signal type** before moving that type's band.
- Re-derive quarterly or every ~500 sends, whichever comes first - platform shifts
  (a tool repricing, a hiring freeze) move bands within a quarter.

## 3. Deriving band adjustments

For each signal type with enough data:

```
positive rate = (positive-meeting + positive-interest) / total replies for that type
```

Compare against the vertical's overall positive rate:

| Signal type's positive rate vs. vertical average | Adjustment |
|---|---|
| ≥ 2x average | raise the band by 1 (cap at 10) |
| 1.25x - 2x | keep the catalog band, note "validated" |
| 0.5x - 1.25x | keep, note "unproven" |
| < 0.5x average with 5+ replies | lower the band by 1-2 |

Objection content matters as much as the rate: if objections cluster on the premise
("we already have someone for that"), the signal is misread - fix the *implies*
text, not the band.

## 4. Writing the calibration file

Copy the structure of a shipped catalog into
`references/signal-types-<shape>.md`:

1. Header: who the shape covers, what data calibrated it, reply count and date.
2. A "register" note: what changes about how this audience reads email (see the
   vertical-smb file's three-point register block for the pattern).
3. Signal types grouped by category. Every type carries: **Look for / Implies /
   Score / Approach**. Keep score bands inside the SKILL.md anchors - calibration
   moves types within bands, it doesn't redefine what an 8 means.
4. A combinations table - combinations are usually where a new vertical differs
   most.
5. A contents line at the top once the file passes ~100 lines.

Then invoke the skill with `icp_shape=<shape>`. Nothing else changes - the method,
output contract, and scripts are shape-independent.

## 5. Without any reply data

Starting a brand-new vertical cold: pick the nearer shipped catalog (`b2b-saas` if
prospects have org charts, `vertical-smb` if they have storefronts), run the first
campaign wave, classify every reply into the five classes from day one, and
recalibrate at 25 replies. The first wave is the gym membership fee.
