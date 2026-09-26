# Design archetypes

Twelve curated visual families. Each describes **intent and DNA**, not a look to reproduce. Values are relative (`low`/`medium`/`high`) so they adapt to any token system. Adapt, combine within [compatibility](#compatibility), and override any trait when product evidence disagrees.

Field meanings: *perception* = what the audience should feel in the first seconds; *CTA* = how conversion actions behave; *poor fit* = where the archetype actively harms the product.

---

## premium-product

```yaml
visual_intent: the product is the hero; confidence through restraint and scale
perception: considered, expensive, trustworthy, calm
composition: centered or product-staged; generous whitespace; one idea per viewport-height section
density: low
typography: large display with tight tracking; restrained body; few weights; strong size contrast
color: near-neutral base (light or dark); color comes from the product/imagery, accent used sparingly
surfaces: few cards; tonal full-width bands instead of boxes; minimal borders; restrained elevation
imagery: large, high-fidelity product renders/photos; product-first; consistent lighting and crop
navigation: quiet, thin, secondary to content; product sub-nav may appear on scroll
motion: expressive hero and scroll storytelling; subtle controls; one high-intensity moment per page
cta: few, calm, repeated at decision points; text-link secondary actions
good_for: hardware, flagship software, launch pages, premium subscriptions
poor_fit: catalogs, admin tools, content with little imagery, price-comparison shopping
```

## modern-saas

```yaml
visual_intent: clarity of value and credibility of the product UI
perception: capable, organized, current, trustworthy
composition: strict grid; product UI screenshots/previews carry the story; alternating feature rhythm
density: medium
typography: neutral sans; medium display contrast; very readable body; numerals for metrics
color: neutral base with one brand accent; semantic colors only in UI previews
surfaces: light cards or framed UI previews; hairline borders; low elevation
imagery: real product UI (cropped, annotated), diagrams; not stock photography
navigation: product header with clear sign-in/primary action; mega menu only for large product suites
motion: soft entrances, UI preview transitions, feature switchers; medium budget
cta: one primary (trial/demo) + one secondary; consistent across page
good_for: B2B software marketing, product sites, onboarding surfaces
poor_fit: luxury goods, editorial publishing, portfolios needing personality
```

## developer-tool

```yaml
visual_intent: show the tool working; respect the reader's time and expertise
perception: precise, fast, honest, engineered
composition: code/terminal/UI evidence near the top; tight grid; documentation-like rhythm
density: medium-high
typography: neutral or grotesk sans + monospace for code, commands, identifiers, metadata; modest display scale
color: often dark or high-contrast neutral; accent is functional (links, status, syntax); little decoration
surfaces: code blocks, bordered panels, terminal frames; flat; borders over shadows
imagery: code, CLI output, diagrams, real interface; no lifestyle photography
navigation: product header with Docs/Pricing/GitHub-style links; persistent docs sidebar in docs areas
motion: snappy and minimal; typed/stepped code reveal only if it teaches; no cinematic scroll
cta: install command or "start" + docs link; copy-to-clipboard as a first-class action
good_for: CLIs, SDKs, APIs, frameworks, devops products, open-source projects
poor_fit: consumer lifestyle, luxury, emotional brand storytelling
```

## technical-platform

```yaml
visual_intent: communicate depth, scale and reliability of a system
perception: serious, robust, enterprise-ready, precise
composition: structured grid; architecture diagrams; capability → evidence sections; comparison tables
density: medium-high
typography: grotesk or humanist sans; mono accent for specs/metrics; strong heading hierarchy
color: restrained neutral with a controlled accent family; diagrams use a limited functional palette
surfaces: diagrams, spec panels, bordered tables; low elevation
imagery: system diagrams, data visualizations, UI; abstract visuals only when explaining architecture
navigation: product header with mega menu for platform breadth; section navigation on long pages
motion: technical: precise, linear-ish, diagram build-ups, metric counters with purpose; low-medium budget
cta: "talk to sales"/docs/trial; specs and compliance evidence near CTA
good_for: infrastructure, security, data platforms, cloud, B2B enterprise
poor_fit: casual consumer apps, fashion, single-feature tools
```

## editorial-product

```yaml
visual_intent: typography and content hierarchy lead; the product feels like a publication
perception: thoughtful, authored, calm, intelligent
composition: asymmetric columns, strong headlines, text-led sections, generous reading measure
density: medium (text-rich but well spaced)
typography: serif or characterful display + highly readable body; typographic hierarchy replaces boxes
color: paper-like or ink-like neutrals; accent rare (links, marks)
surfaces: almost no cards; rules, whitespace and typographic scale define groups
imagery: editorial photography or illustration with captions; purposeful crops
navigation: minimal header; section/category navigation; table of contents on long reads
motion: minimal-soft; reading is sacred; line/word reveal only for rare headline moments
cta: typographic (underlined links, text buttons); subscription prompts placed after value
good_for: publishing, knowledge products, newsletters, documentation brands, journals
poor_fit: operational dashboards, dense e-commerce, products without substantive content
```

## creative-portfolio

```yaml
visual_intent: the work is the argument; the frame expresses authorship
perception: distinctive, crafted, confident, memorable
composition: asymmetric, full-bleed media, unexpected grids, case-study narratives
density: low-medium
typography: expressive display (may be oversized, condensed, or serif), quiet body
color: author-defined; often monochrome base so work carries color
surfaces: minimal; media edges define structure
imagery: the work itself at large scale; video and interaction allowed
navigation: minimal/hidden until needed; project index; clear return path
motion: expressive-controlled; page/project transitions; cursor/hover reveals only when discoverable
cta: contact, view project; rarely more than one
good_for: studios, agencies, designers, photographers, personal sites
poor_fit: task-heavy apps, compliance-driven products, marketplaces
```

## marketplace

```yaml
visual_intent: help people find, compare and trust quickly
perception: abundant, reliable, easy, fair
composition: search-first; filterable grids/lists; listing cards are justified here; strong result hierarchy
density: high
typography: neutral, highly legible sans; tabular numerals for prices/ratings; compact titles
color: neutral base; one brand accent for primary actions; semantic colors for price/availability
surfaces: listing cards with consistent media ratio; subtle borders; sticky filter/search bars
imagery: user/seller photography; consistent aspect ratio; graceful fallback
navigation: persistent search, category navigation, account/cart; mega menu for large catalogs
motion: minimal-snappy; feedback on filter/favorite/add; skeletons over spinners
cta: per-item actions + one clear transaction path; urgency only when truthful
good_for: listings, e-commerce catalogs, booking platforms, classifieds
poor_fit: single-product launches, editorial content, portfolios
```

## travel-commerce

```yaml
visual_intent: inspire, then transact with confidence
perception: aspirational yet trustworthy; price-clear; reassuring
composition: media-led inspiration above a search/booking entry; then dense comparable results
density: low at entry, high in results and checkout
typography: friendly or neutral sans; strong price typography; clear date/guest inputs
color: warm neutrals; destination imagery provides color; semantic for deals/availability
surfaces: search panel as the hero object; result cards; map + list split
imagery: destination/property photography; galleries; maps
navigation: product header with search persistence; trip/booking account areas
motion: soft for inspiration (gallery, image scale), snappy for booking controls; low in checkout
cta: search/book; price and cancellation policy adjacent to CTA
good_for: hotels, flights, tours, rentals, travel agencies
poor_fit: developer tools, B2B infrastructure
```

## luxury

```yaml
visual_intent: rarity, craft and restraint; nothing hurried
perception: exclusive, refined, timeless
composition: very low density; asymmetric editorial layouts; long pauses of whitespace
density: very low
typography: refined serif or high-contrast display; wide tracking for small caps/labels; light weights used carefully (contrast-checked)
color: monochrome or deep neutrals with a single material-inspired accent; no bright semantic color outside commerce feedback
surfaces: none/near-none; hairlines; full-bleed imagery
imagery: art-directed photography; texture and material detail
navigation: sparse, often centered brand mark; menu may be hidden behind a clear control
motion: slow-soft cinematic transitions; long ease-out; very few moments
cta: understated text actions; appointment/enquiry over "buy now"
good_for: fashion, jewelry, hospitality, premium real estate, fine goods
poor_fit: anything needing speed, density or price comparison
```

## consumer-tech

```yaml
visual_intent: approachable delight around a useful product
perception: friendly, modern, optimistic, easy
composition: product/app shots in context; playful but gridded; bento-like groupings only when content is truly modular
density: low-medium
typography: rounded/geometric or friendly humanist sans; bold headlines; short copy
color: brighter brand palette used in blocks; still one primary action color
surfaces: rounded containers, soft tonal backgrounds; moderate elevation
imagery: device/app screens, lifestyle photography, illustration with a consistent style
navigation: simple product header, app-store/download actions
motion: playful-soft microinteractions; springy but short; medium budget
cta: download/sign up; app badges; one primary
good_for: mobile apps, consumer devices, personal productivity, fintech for consumers
poor_fit: enterprise infrastructure, luxury, long-form editorial
```

## data-heavy-product

```yaml
visual_intent: make large amounts of data scannable and actionable
perception: efficient, reliable, in-control
composition: app shell; sidebars; tables, charts and panels; information hierarchy by type and alignment
density: high
typography: neutral sans with tabular numerals; compact scale; mono for IDs/code only
color: neutral UI; color reserved for data encoding and status
surfaces: panels and tables; borders/dividers; minimal elevation except overlays
imagery: none decorative; charts and data visualizations only
navigation: persistent sidebar or top bar; breadcrumbs; section tabs
motion: minimal, fast; state change, loading, expand/collapse; no entrance animation
cta: contextual actions per object; one primary per view
good_for: dashboards, admin, analytics, monitoring, CRM, internal tools
poor_fit: marketing storytelling, brand launches
```

## minimal-product

```yaml
visual_intent: a single clear job with almost no chrome
perception: calm, focused, honest
composition: single column or simple split; few sections; strong alignment
density: low
typography: one family; hierarchy through size and weight only; excellent body readability
color: near-monochrome; one accent
surfaces: whitespace and dividers; almost no cards
imagery: optional; small product UI or none
navigation: minimal header, few links
motion: minimal; feedback only
cta: one action repeated at most twice
good_for: utilities, single-feature tools, waitlists, personal apps, documentation-light products
poor_fit: broad platforms needing breadth, catalogs, content-heavy brands
```

---

## Compatibility

Mix at most one primary + one secondary (+ one scoped accent trait). `✓` compatible, `~` only with a scoped rule (e.g., "secondary affects hero only"), `✗` reject.

| primary ↓ / secondary → | premium | saas | dev | tech-plat | editorial | portfolio | market | travel | luxury | consumer | data | minimal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| premium-product | — | ~ | ~ | ✓ | ✓ | ~ | ✗ | ~ | ✓ | ✓ | ✗ | ✓ |
| modern-saas | ~ | — | ✓ | ✓ | ~ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ | ✓ |
| developer-tool | ~ | ✓ | — | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ~ | ✓ | ✓ |
| technical-platform | ✓ | ✓ | ✓ | — | ~ | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ | ✓ |
| editorial-product | ✓ | ~ | ✓ | ~ | — | ✓ | ✗ | ~ | ✓ | ~ | ✗ | ✓ |
| creative-portfolio | ~ | ✗ | ✗ | ✗ | ✓ | — | ✗ | ✗ | ✓ | ~ | ✗ | ✓ |
| marketplace | ✗ | ~ | ✗ | ✗ | ~ | ✗ | — | ✓ | ✗ | ✓ | ~ | ~ |
| travel-commerce | ~ | ✗ | ✗ | ✗ | ✓ | ✗ | ✓ | — | ~ | ✓ | ✗ | ~ |
| luxury | ✓ | ✗ | ✗ | ✗ | ✓ | ✓ | ✗ | ~ | — | ✗ | ✗ | ✓ |
| consumer-tech | ✓ | ✓ | ~ | ✗ | ~ | ~ | ✓ | ✓ | ✗ | — | ✗ | ✓ |
| data-heavy-product | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ~ | ✗ | ✗ | ✗ | — | ✓ |
| minimal-product | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ~ | ~ | ✓ | ✓ | ✓ | — |

Common coherent mixes: `premium-product + technical-platform` (premium hardware/silicon, "technical minimalism"), `developer-tool + editorial-product` (docs-first developer brands), `marketplace + travel-commerce` (booking platforms), `modern-saas + data-heavy-product` (product site → app continuity), `editorial-product + luxury` (fashion journals).

Archetypes are product-level families; visual languages that realize them are in the [style catalog](../../knowledge/domains/styles/README.md) (e.g., premium-product → `style.calm-futurism`, `style.cinematic`, `style.minimal`; developer-tool → `style.developer-tool`, `style.monochrome`; editorial-product → `style.editorial`, `style.swiss`).

A mix is rejected (`INCOMPATIBLE_REFERENCE_MIX`) when the two sources disagree on **density** by two levels *in the same region*, on **motion character** (cinematic vs snappy for the same element type), or on **surface philosophy** (card-driven vs card-free) without a scoped rule.
