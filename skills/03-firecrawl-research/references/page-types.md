# Page Types Reference

Full classification of GTM-relevant pages with URL patterns and tier assignments.

## Tier 1 - Always scraped (all modes)

### Homepage
- URL: base domain `/`
- Always included, no pattern matching needed
- Contains: value prop, positioning, customer logos, social proof

### About / Company
- Patterns: `about`, `about-us`, `company`, `who-we-are`, `our-story`, `team`, `overview`
- TR: `hakkimizda`, `hakkinda`, `hikayemiz`, `kurumsal`, `biz-kimiz`
- BG: `za-nas`, `za-kompaniyata`, `ekip`
- RO: `despre`, `despre-noi`, `companie`
- GR: `sxetika`, `etairia`, `poioi-eimaste`
- DE: `ueber-uns`, `uber-uns`, `unternehmen`, `wir-ueber-uns`
- Contains: founding story, team size, mission, leadership names, locations

### Careers / Jobs
- Patterns: `careers`, `jobs`, `work-with-us`, `join-us`, `hiring`, `join`, `opportunities`, `vacancies`
- TR: `kariyer`, `is-ilanlari`, `pozisyon`, `calisan`
- BG: `karieri`, `rabota`, `svobodni-pozitsii`
- RO: `cariere`, `joburi`, `locuri-de-munca`
- GR: `karieres`, `theseis-ergasias`
- DE: `karriere`, `stellenangebote`
- Contains: open roles, departments, growth signals
- Depth rule: main page only (1 credit). TheirStack handles deep JD analysis.

### Blog / News
- Patterns: `blog`, `news`, `insights`, `resources`, `articles`, `updates`, `press`, `media`
- TR: `haberler`, `blogliste`, `bloglar`, `makale`, `basin`
- BG: `novini`, `stati`
- RO: `noutati`, `stiri`, `articole`
- GR: `nea`, `arthra`
- DE: `neuigkeiten`, `nachrichten`, `aktuelles`, `presse`
- Contains: funding announcements, product launches, partnerships

## Tier 2 - Standard + Deep modes

### Customers / Case Studies
- Patterns: `customers`, `case-studies`, `success-stories`, `testimonials`, `case-study`, `stories`, `results`
- TR: `musteriler`, `basari-hikayeleri`
- BG: `klienti`, `uspeshni-istorii`
- RO: `clienti`, `studii-de-caz`
- GR: `pelates`, `periptoseis`
- DE: `kunden`, `erfolgsgeschichten`, `referenzen`
- Contains: customer names, verticals, deal size clues

### Pricing
- Patterns: `pricing`, `plans`, `price`, `packages`
- TR: `fiyat`, `fiyatlar`, `paketler`
- BG: `tseni`, `planove`
- RO: `pret`, `tarife`, `preturi`
- GR: `times`, `paketa`
- DE: `preise`, `kosten`, `tarife`
- Contains: business model (self-serve vs enterprise), price points

### Integrations / Partners
- Patterns: `integrations`, `ecosystem`, `partners`, `apps`, `marketplace`
- TR: `entegrasyonlar`, `ortaklar`, `is-ortaklari`
- BG: `integratsii`, `partnyor`
- RO: `integrari`, `parteneri`
- DE: `integrationen`, `partner`
- Contains: tech ecosystem, partnership signals

### Product / Platform / Technology
- Patterns: `product`, `platform`, `features`, `solutions`, `how-it-works`, `technology`, `tech`
- TR: `urun`, `platform`, `ozellikler`, `cozumler`, `teknoloji`
- DE: `produkt`, `funktionen`, `loesungen`, `technologie`
- Contains: what they build, feature set, use cases, tech stack

## Tier 3 - Deep mode only

### Changelog / Release Notes
- Patterns: `changelog`, `release-notes`, `whats-new`, `releases`, `updates-log`
- Contains: product velocity signal

### Leadership / Executives
- Patterns: `leadership`, `management`, `executives`, `founders`
- TR: `yonetim`, `kurucular`
- DE: `fuehrungsteam`, `geschaeftsfuehrung`
- Contains: decision-maker names (separate from /about team page)

## Pages we skip

- `/terms`, `/privacy`, `/cookie-policy`, `/legal` - no GTM value
- `/docs`, `/documentation`, `/api` - developer reference
- `/support`, `/help`, `/faq` - customer support
- Subdomains (`docs.company.com`, `support.company.com`) - different sites

## URL scoring

When multiple URLs match the same page type, the script picks the best one:
1. Non-locale URLs preferred (penalize `/en-us/about`, `/zh-cn/careers`)
2. Fewer path segments preferred (`/about` beats `/company/about-us/overview`)
3. Shorter path preferred as tiebreaker

File extensions (`.aspx`, `.html`, `.php`) are stripped before matching.
