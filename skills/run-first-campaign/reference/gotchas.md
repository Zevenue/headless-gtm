# Cold-start gotchas

Failure patterns from real first-campaign runs, as wrong/right pairs. Read this
when a step misbehaves rather than improvising around the workflow.

## The registry fights scraping

✗ Retry the same registry with different settings until credits are gone, or
tell the owner the workflow is blocked.
✓ Registries and professional colleges are the best sources and the most
defended ones. If extraction returns empty or blocked pages, fall through the
candidate list proposed in Step 2 - second registry, association directory,
marketplace - and land on 02-apify-maps-discover as the general fallback. One
clean source is enough; name the switch and the reason when it happens.

## Listings without websites

✗ Drop rows with no website, or treat a missing domain as a failed extraction.
✓ Many registry rows list a business with no site. They enter the chain on the
`name|city` dedup key (`headless-gtm-shared/schema.py:dedup_key`) and stay
rankable on listing fields alone. Keep them; a website can be resolved later,
and the campaign sheet degrades gracefully on the missing column.

## The owner's ICP is everyone

✗ Loosen the qualification brief so more of the extraction survives, or ask the
owner to narrow their ICP before anything runs.
✓ "Anyone with a truck" is a normal first answer. Run the gate as written - a
high disqualification count is the finding, not a failure. Show the owner what
got demoted and why; two rounds of corrections turn a vague ICP into a real
brief faster than any up-front interview.

## The owner asks you to send

✗ Promise sends later, offer to "set up sending", or quietly draft into a
connected mail tool.
✓ Nothing in this repo sends. Say so plainly at the moment it comes up, and
point at what the workflow does produce: approved drafts and an import-ready
sheet. Where the owner takes them - a CRM import, a sending tool, manual
one-by-one - is their call, after the on-screen approval.
