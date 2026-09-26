# Web Pattern Library

A curated composition vocabulary for realizing locked content. Patterns are **options chosen by reasoning**, never defaults. Selection happens in the [Pattern Selection Engine](../../skills/design-inspiration/pattern-selection.md); this library describes each option's requirements and failure modes.

Boundary: Phase 1 (`PAGE-SPEC`, `WIREFRAME-SPEC`) owns which blocks exist and their responsibility. Patterns decide composition, pacing and interaction presentation within that. A pattern that needs new content or changes meaning triggers a Phase 1 rollback request.

## Groups

| Group | File | Load when |
|---|---|---|
| Hero | [hero/hero-patterns.md](hero/hero-patterns.md) | Landing, marketing, product pages |
| Grid | [grid/grid-patterns.md](grid/grid-patterns.md) | Bento, masonry, editorial, broken, magazine, dashboard, card matrix, asymmetric, dense data |
| Storytelling layouts | [storytelling/story-layouts.md](storytelling/story-layouts.md) | Sticky, scroll, pinned demo, alternating, layered, feature explorer, timeline, comparison, before/after |
| Application | [application/application-layouts.md](application/application-layouts.md) | Sidebar, three-panel, master-detail, canvas, command-driven, dashboard shell, editor, inbox, split inspector |
| Sections | [sections/section-patterns.md](sections/section-patterns.md) | Any multi-section marketing/content page |
| Storytelling | [storytelling/storytelling-patterns.md](storytelling/storytelling-patterns.md) | Product narratives, launches, showcases |
| Navigation | [navigation/navigation-patterns.md](navigation/navigation-patterns.md) | Header/nav presentation choices |
| Product showcase & interaction | [product-showcase/interaction-patterns.md](product-showcase/interaction-patterns.md) | Tabs, carousels, galleries, sliders, configurators, demos |
| Conversion | [conversion/conversion-patterns.md](conversion/conversion-patterns.md) | CTA, pricing, sign-up, trust near action |
| Content | [content/content-patterns.md](content/content-patterns.md) | Reading, docs, listings, dense product views |
| Composition | [composition/composition-patterns.md](composition/composition-patterns.md) | Choosing page-level visual composition |
| Motion composition | [motion-composition/motion-composition.md](motion-composition/motion-composition.md) | Distributing motion budget across selected patterns |

## Progressive disclosure

| Task | Load | Do not load |
|---|---|---|
| Landing / marketing / product showcase | composition, hero, sections, storytelling, conversion, motion-composition | content (unless reading-heavy) |
| Editorial / docs / blog | composition, content, navigation | hero (except editorial-split), storytelling |
| Marketplace / travel | composition, content (listing), navigation, interaction (gallery/filters), conversion | cinematic hero, sticky storytelling |
| Dashboard / app | content (high-density product) only if layout changes | hero, sections, storytelling, motion-composition |
| Small form / component | none | everything here |

## Library rules

- Each pattern lists content requirements; unmet requirements make it ineligible (`PATTERN_MISUSE`).
- Adjacent sections vary pattern or density only for a narrative reason; uniform repetition of interchangeable blocks is `GENERIC_TEMPLATE_COMPOSITION`.
- Floating pill navigation, bento grids, and three-card rows are allowed only with a recorded reason; none is a default.
- Keep this library small. Add a pattern only when a real project needs one that no existing entry covers.

Hero, grid, storytelling-layout and application entries are structured catalog entries of the [Design Knowledge System](../domains/README.md) (schema `layout`). They are ranked by the [Capability Resolver](../../skills/capability-resolver/README.md) from style compatibility, content requirements, density and motion cost.
