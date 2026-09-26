# Phase 2 router

Before any visual decision, verify that `STRUCTURE-LOCK.md` is active, lists the artifacts it protects, and covers the requested work. Read the locked Phase 1 artifacts or their declared merged equivalents. A semantic mismatch is a structural issue: create a rollback request and return to Phase 1; never edit the lock here.

## Task modes

| Mode | Route | Minimum outputs |
|---|---|---|
| `NEW_BUILD` | Direction → intelligence → system/tokens → visual grammar → components → implementation → craft/QA | Direction, system/tokens, visual grammar, component/implementation map, review |
| `VISUAL_REDESIGN` | Extract current system → compare → direction → grammar → normalize/redesign → craft/QA | Current system, direction, grammar, migration decision, review |
| `EXTEND_EXISTING` | Read lock/current system → classify pattern → targeted grammar/component extension → QA | Impacted grammar/component/implementation notes, review |
| `MIGRATE_EXISTING` | Extract → target system → representative page → groups → cross-page QA | Current system, system/tokens, migration plan, quality report |
| `POLISH` | Preserve system → targeted visual/QA loop | Review and documented exceptions |
| `AUDIT` | Inspect rendered UI/system → review/report | Visual/accessibility/quality report; no unsolicited rewrite |

## Reference selection

Load only references signalled by the selected pages and task: `typography`, `color`, `spacing`, `layout`, `imagery`, or `motion` for system decisions; `forms`, `tables`, or `dashboard` for the relevant component type; `accessibility` for interaction/QA; and Visual Language references for rendered behavior/craft. Button work loads `visual-language/components/buttons.md`; toast/feedback work loads `components/feedback.md` and `color-character.md`; icon work loads `components/iconography.md`; generic-page craft or AI-tell concerns load `anti-slop/global.md`, `ai-tell-density.md`, and `craft-review.md`; a full visual redesign also loads `visual-grammar.md`, `surface-profile.md`, `typography-character.md`, and `motion-character.md`. Read the relevant `references/design-intelligence/` file for product, style, industry, density, or layout choices—never the full directory by default.

### Inspiration, typography, motion and patterns

| Trigger in task | Load | Never load for this trigger |
|---|---|---|
| "landing page", "marketing", "product showcase", "launch", new marketing site | `design-inspiration/workflow.md`, `archetypes.md`, `pattern-selection.md`; `web-patterns/` composition + hero + sections + storytelling + conversion + motion-composition; `typography/` archetypes/selection/display; `motion/` principles/character/scroll/reduced-motion | dashboard/table references unless content has them |
| "make it premium", "more distinctive", "looks generic" | `archetypes.md`, typography archetypes + display, composition patterns, motion character + principles, plus the Visual Language craft set | full reference-profile list unless a name is given |
| "font", "typography", "type", readability | `typography/README.md` → only the role files needed + `typography-review.md` | motion, web-patterns |
| "animation", "interaction", "motion", "transition" | `motion/README.md`, `motion-principles.md`, `motion-character.md`, the relevant family file, `reduced-motion.md`, `performance-safety.md` for scroll/continuous | hero/storytelling patterns unless a marketing page |
| "reference X", "like X", screenshot/URL | `reference-extraction.md`, `anti-copying.md`, the matching `reference-profiles.md` entry | cloning; fetching the site as a hard dependency |
| Dashboard / app screens | typography (dense/neutral), `content/content-patterns.md` (high-density) only if layout changes, `motion/microinteractions.md` + `spatial-motion.md` + `reduced-motion.md` | hero, storytelling, scroll motion, cinematic profiles |
| Small form / single component | typography body/technical as needed, `microinteractions.md`, `reduced-motion.md` | inspiration engine, web patterns |
| Editorial / docs / content | archetypes (editorial), typography (editorial/body/composition), `content/content-patterns.md`, navigation patterns | cinematic hero, sticky storytelling |
| Marketplace / travel | archetypes (marketplace/travel-commerce), `content/` listing/detail, `interaction-patterns.md`, conversion | cinematic/luxury patterns |

### Design Knowledge System

| Trigger in task | Load | Never load for this trigger |
|---|---|---|
| New build, visual redesign, landing/product site, "make it premium/distinctive", benchmark tasks | [capability-resolver](../capability-resolver/README.md) + `resolver.md`; then **only** the files in the plan's retrieval list ([retrieval.md](../../knowledge/domains/retrieval.md)) and the composition anchor in `knowledge/composition/recipes.md` | whole catalog folders |
| Style/"look" questions, generic or homogenized output | the resolved `knowledge/styles/` entries, `knowledge/composition/anti-homogenization.md`, `premium-quality-model.md` | unrelated style families |
| Screen types (dashboard, settings, AI chat, kanban, …) | the matching `knowledge/screens/` entry (structure stays locked) | marketing hero/storytelling layouts |
| Application shells or grids | `web-patterns/application/application-layouts.md` or `grid/grid-patterns.md` entries | cinematic layouts |
| Motion tiers | `motion/motion-principles.md` (grammar) + only the needed tier file: M1 `microinteractions.md`, M2 `spatial-motion.md`, M3 `layout-motion.md`, M4 `scroll-motion.md`/`text-motion.md`, M5 `cinematic-motion.md`; `responsive-motion.md` for M3+ | M4/M5 for apps, dashboards, forms |
| Interactions (drag, command palette, inline edit, gestures) | the matching `knowledge/interactions/` entry | pointer-play entries for productivity tools |
| Visual effects (glass, glow, gradient, noise, shader…) | the matching `knowledge/effects/` entry + `05-frontend-implementation/performance-budget.md` | effects from a style's `avoid_effects` |
| Advanced graphics (WebGL, Three.js, Rive, Lottie, canvas) | `05-frontend-implementation/technology-resolver.md` + `knowledge/graphics/techniques.md` + `knowledge/advanced-accessibility.md` | — |
| Before implementation of any motion/effect/graphic | `technology-resolver.md`, `performance-budget.md` | new packages without authorization |
| Design quality evaluation / benchmark | `evals/quality/README.md`, `scripts/analyze_design_quality.py`, `templates/DESIGN-QUALITY-REPORT.md` | — |

Existing coherent typography/motion is classified `KEEP` before any of these modules proposes change.

Router output records: task mode, selected inspiration/typography/motion/pattern modules (or `none`), project/page types, frontend stack, existing-system state (`none`/`keep`/`refine`/`replace`/`migrate`), lock version, selected artifact set, selected references, viewport targets, assumptions, and blockers.
