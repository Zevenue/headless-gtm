# Signal Types — `vertical-smb` calibration

Catalog for prospects that are local or owner-operated businesses reached through
Maps-style discovery rather than firmographic databases: fitness studios, event
venues and organizers, salons, clinics, restaurants, laundromats, home-service
trades. Calibrated against classified reply data from fitness and events outbound.

The register differs from B2B SaaS in three ways that change scoring:

1. **The owner reads the email.** Signals about their day-to-day (reviews, staffing,
   bookings) land harder than industry abstractions.
2. **Data is thinner.** No funding feeds, few JDs. Websites, review platforms, and
   marketplace listings do the work - so platform and review evidence scores a band
   higher here than equivalent-strength evidence would in b2b-saas.
3. **Seasonality is real.** The same signal can be a 7 in the ramp-up months and a 3
   mid-season. Note timing in `evidence_date`.

Contents: 1. Location & expansion · 2. Reviews & reputation · 3. Platform &
marketplace · 4. Staffing · 5. Website & digital state · 6. Community & social ·
7. Combinations

---

## 1. Location & expansion signals

### Second-location moment (or third, or fourth)
**Look for:** "opening soon", new address on the site, a second Maps listing, press in
local outlets, hiring posts naming a new neighborhood.
**Implies:** whatever ran on the owner's phone and memory now has to run twice.
Systems pain arrives with the lease.
**Score:** 8-10 within ~6 months of the opening; 6-7 after it settles.
**Approach:** PQS - "Saw the [neighborhood] opening. Most owners tell us the second
location is where [manual process] stops working."

### Multi-location operator
**Look for:** 3+ locations listed; "our locations" page.
**Implies:** past the breaking point; either they built systems or they're bleeding.
**Score:** 6-8 · **Approach:** Pain-led on cross-location consistency.

## 2. Reviews & reputation signals

### Review velocity spike or stall
**Look for:** review counts and recency across Maps-type listings (02's records carry
rating and reviews_count). A busy business collecting no fresh reviews, or a sudden
influx after years of quiet.
**Implies:** stall - nobody owns the ask; spike - growth or a push that needs follow-through.
**Score:** 6-8 · **Approach:** PVP - a quick read of their review pattern vs. nearby
competitors is a real artifact.

### Rating slipping on an operational theme
**Look for:** recent reviews clustering on a fixable operational gripe - booking
friction, no-shows, waitlists, response time.
**Implies:** the pain has reached their customers; the owner likely knows.
**Score:** 7-9 when the theme maps to what the client fixes.
**Approach:** PQS on the pattern ("last month's reviews mention booking three times"),
never quoting one reviewer.

## 3. Platform & marketplace signals

### Platform in place (booking / ticketing / POS / scheduling)
**Look for:** "book via [platform]" buttons, ticketing links, embedded widgets,
marketplace listings, footer badges.
**Implies:** same as the B2B competitor/adjacent read: bought into the problem space.
Fee-heavy or feature-capped platforms carry visible friction.
**Score:** 8-10 when the platform is the client's direct competitor and friction is
visible (fee complaints, workarounds, "DM to book" next to a booking tool); 5-7 bare.
**Approach:** PQS on the known friction of that specific platform.

### Scattered stack
**Look for:** one tool for booking, another for payments, a newsletter service, DMs
for changes - visible as four different embeds and links.
**Implies:** the owner is the integration layer.
**Score:** 6-8 · **Approach:** Pain-led on the stitching cost.

### Marketplace-dependent revenue
**Look for:** most traffic routed through a marketplace listing (class packs, ticket
platforms, aggregator pages) rather than their own site.
**Implies:** margin and customer-relationship pain; platform fee sensitivity.
**Score:** 6-8 · **Approach:** PVP - show what direct revenue would look like.

## 4. Staffing signals

### Now-hiring for the front of house
**Look for:** "we're hiring" pages or posts for desk staff, coordinators, managers.
**Implies:** throughput pain; admin load outgrew the current team.
**Score:** 6-8 (8 when the posting describes the exact task the client automates).
**Approach:** PQS quoting the posting's own words.

### Owner doing everything
**Look for:** the owner is the named contact for booking, events, complaints, and
press; "text me directly" language.
**Implies:** no slack in the system; pitch time-back, not features.
**Score:** 5-7 · **Approach:** Pain-led, short email, time framing.

## 5. Website & digital state signals

### Stale or broken digital presence
**Look for:** copyright year 2+ years old, dead links, last blog post years back,
no booking path at all, unclaimed or inconsistent Maps data.
**Implies:** either nobody owns digital, or it's owned by someone with no time.
**Score:** 5-7 for clients selling web/digital services; 3-4 as context otherwise.
**Approach:** PVP - a specific list of what's broken is a genuine artifact.

### Fresh relaunch or rebrand
**Look for:** "new site", redesign announcements, renovation posts, "under new
management".
**Implies:** investment mood; open to changing tools while everything's in motion.
**Score:** 6-8 within ~3 months · **Approach:** PQS on what the relaunch usually
surfaces next.

### Seasonal ramp
**Look for:** season-dependent businesses approaching their ramp (registration
opens, summer schedule, holiday bookings).
**Implies:** a hard deadline for fixing the operational gap.
**Score:** +1 to any related signal during ramp-up; -2 mid-peak (no bandwidth to
switch anything) · **Approach:** keep whatever the base signal recommends, anchored
to the season date.

## 6. Community & social signals

### Audience without monetization rails
**Look for:** strong social following or engaged community next to a thin
booking/payment path.
**Implies:** demand exists; capture doesn't.
**Score:** 6-8 for clients that monetize community · **Approach:** PVP with a
concrete "here's what [their audience size] usually converts to" read.

### Event cadence
**Look for:** regular events, workshops, pop-ups listed anywhere.
**Implies:** recurring coordination load; every event is the pain repeating.
**Score:** 5-7 · **Approach:** Pain-led on the per-event overhead.

## 7. Combinations (lead with these when present)

| Combination | Score | Why it outranks the parts |
|---|---|---|
| Second location + hiring front-of-house | 9-10 | scaling moment with budgeted admin pain |
| Competitor platform + fee/friction evidence | 8-10 | switching intent, SMB edition |
| Review theme + the platform that causes it | 8-9 | customer-visible pain with a named cause |
| Relaunch + scattered stack | 7-8 | investment mood meets integration pain |
| Seasonal ramp + any 6+ signal | +1 band | deadline attached to existing pain |

Write a combination as one signal: strongest evidence carries `signal_sentence` and
`source_url`; the supporting fact goes in `notes`.
