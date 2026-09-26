# Pattern Selection Engine

Selects hero, section, storytelling, navigation, interaction, composition and motion-composition patterns from the [Web Pattern Library](../../knowledge/web-patterns/README.md). Patterns are never chosen at random, by popularity, or because a category "usually has" them.

## Boundary with Phase 1

The locked `PAGE-SPEC.md`/`WIREFRAME-SPEC.md` own **which content blocks exist, their responsibilities, and required order**. Pattern selection owns **how each block is composed and paced**. If the best narrative needs a block that is not locked (or removal/reordering that changes meaning), write a rollback request to Phase 1; do not silently add or delete sections. Pure visual pacing (e.g., split vs stacked, sticky vs static) stays in Phase 2.

## Inputs

```text
content inventory   what actually exists: product imagery? UI? code? metrics? testimonials? long copy?
product / archetype from DESIGN-INSPIRATION
audience            expert vs general; evaluating vs returning
page goal           convert / inform / operate / read / browse / transact
density             from direction
visual direction    composition line
motion character    from motion system (if decided) or direction
```

## Procedure

1. **Map each locked block to its narrative job**: orient, prove, explain, compare, reassure, convert, navigate, reference.
2. **List candidates** per block from the library whose *content requirement* is met. A pattern whose required content does not exist is ineligible (e.g., `cinematic-product` without high-quality product media).
3. **Score** each candidate quickly: fit to job (0–2), fit to archetype (0–2), content availability (0–2), responsive risk (0 to −2), motion budget cost (0 to −2). Pick the highest; ties go to the simpler pattern.
4. **Check rhythm across the page**: adjacent blocks should not repeat the same pattern and density unless repetition is the point (e.g., a spec list). Aim for a deliberate cadence (e.g., open → dense → open → proof → close).
5. **Check the motion budget** with [motion-intensity-budget](../../knowledge/motion/motion-principles.md#intensity-budget): at most one high-intensity block per page (two on long storytelling pages with separation).
6. **Record** selected, candidates, and rejected patterns with a one-line reason in `DESIGN-INSPIRATION.md`.

## Archetype → typical candidates

| Archetype | Hero candidates | Section/story candidates | Avoid by default |
|---|---|---|---|
| premium-product | `layout.hero-product`, `layout.hero-cinematic` | sticky-storytelling, progressive product reveal, metric-story, technical-detail | feature-grid of equal cards |
| modern-saas | `layout.hero-dashboard`, `layout.hero-split` | feature-alternating, feature-switcher, capability → evidence, social-proof | immersive-fullscreen |
| developer-tool | `layout.hero-centered`, `layout.hero-dashboard` (code/CLI) | technical-detail, capability → evidence, comparison, FAQ | cinematic-product, parallax |
| technical-platform | `layout.hero-dashboard`, `layout.hero-centered` | technical deep-dive, metric-story, comparison, section navigation | playful hovers |
| editorial-product | `layout.hero-editorial`, `layout.hero-centered` | editorial-sections, asymmetric editorial | card grids |
| creative-portfolio | `layout.hero-full-bleed`, `layout.hero-asymmetric` | full-bleed media, case-study narrative | feature-grid, pricing tables |
| marketplace | `layout.hero-media-led` | high-density grid/list, filters, social-proof | cinematic storytelling |
| travel-commerce | `layout.hero-media-led` | gallery, comparison, reassurance (policies/reviews) | sticky-storytelling |
| luxury | `layout.hero-full-bleed`, `layout.hero-editorial` | editorial-sections, full-bleed media | metric-story, dense grids |
| consumer-tech | `layout.hero-product`, `layout.hero-interactive` | feature → benefit, visual demonstration, testimonial | technical deep-dive-first |
| data-heavy-product | (app — no hero) | high-density product composition | all landing patterns |
| minimal-product | `layout.hero-centered` | short feature list, single CTA | multi-section storytelling |

## Anti-template rule

Flag `GENERIC_TEMPLATE_COMPOSITION` when the output reduces to

```text
navbar → centered hero → 3 equal cards → 3 equal cards → testimonials → CTA → footer
```

(or an equivalent sequence of interchangeable blocks) **and** no recorded reasoning ties each block's pattern to content and page goal. The fix is not "add variety" but re-running steps 1–4: assign narrative jobs, pick patterns by content, vary density by job. Keep the sequence only if the reasoning genuinely supports it (e.g., a tiny service site with exactly three equal services) and record why.

## Related failures

| Code | Signal |
|---|---|
| `PATTERN_MISUSE` | Pattern chosen without its content requirement (sticky storytelling with one sentence; carousel hiding critical content; comparison slider without before/after pairs). |
| `VISUAL_STORYTELLING_WEAK` | Sections are independent claims with no progression (problem→solution, claim→evidence); proof never follows claims. |
| `GENERIC_TEMPLATE_COMPOSITION` | See above. |

Hero, grid, storytelling and application layouts are structured catalog entries (`layout.*` ids; earlier names are kept as `aliases`). When a `CAPABILITY-PLAN.md` exists, start from its ranked layouts and record here only the mapping to locked blocks and any override.
