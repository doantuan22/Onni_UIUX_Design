# Phase 2 — frontend design engine

## Responsibility

Turn the active locked structure into a complete, rendered frontend delivery without changing protected structural decisions. Phase 2 owns how the experience looks, feels, responds, adapts, and realizes components; it does not own what the product does, why it exists, who can use it, or its business rules.

## Entry condition

The workflow is `STRUCTURE_LOCKED`, the lock is valid and current, and Phase 2 receives the locked Phase 1 artifacts it needs.

## Inputs

- Active `STRUCTURE-LOCK.md` and its referenced versions
- `DESIGN-BRIEF.md`, `PAGE-MAP.md`, `PAGE-SPEC.md`, `WIREFRAME-SPEC.md`, `COMPONENT-MAP.md`, `STATE-MAP.md`, and `NAVIGATION-MAP.md`, or their explicit merged equivalents
- Existing frontend stack, design system, and implementation constraints

## Outputs

- Router-selected Phase 2 artifacts, including a design system and implementation map when in scope
- Rendered frontend delivery suitable for browser, responsive, accessibility, and quality review

## Exit condition

Phase 2 review and the final quality gate pass with no unresolved blocker. A structural discovery stops the affected visual decision, creates a rollback request, and returns to Phase 1.

## Start and loading

Read [router.md](router.md) first. It validates the lock, classifies the task, selects the minimum artifact set, identifies the frontend stack, and chooses only needed references. Then follow [workflow.md](workflow.md) and the selected engine modules.

Never start CSS or frontend implementation before a `DESIGN-DIRECTION.md` exists for work that changes visual realization. Before tokens, select design DNA with [Design Inspiration](../design-inspiration/README.md) and type character with [Typography Intelligence](../typography/README.md) when the router selects them. After tokens, use [Visual Language](../visual-language/README.md) to make rendered behavior explicit, [Motion](../../knowledge/motion/README.md) for temporal behavior, and the [Web Pattern Library](../../knowledge/web-patterns/README.md) for composition options, then hand the result to Component Specs. The active `STRUCTURE-LOCK.md` is immutable in Phase 2: do not change business flows, actors, permissions, use cases, required data, route semantics, API contracts, or backend logic. Do not replace frameworks or add major dependencies without need and authorization.

## Source of truth

| Owner | Owns |
|---|---|
| Design Knowledge System (`knowledge/`, motion, web-patterns catalogs) | design vocabulary: styles, layouts, screens, motion, interactions, effects, recipes, technologies |
| Capability Resolver (`CAPABILITY-PLAN.md`) | ranked capability selection with why / why not |
| Design Direction | desired experience |
| Design Inspiration (`DESIGN-INSPIRATION.md`) | archetype, reference/design DNA, pattern selection |
| Typography Intelligence (`DESIGN-SYSTEM.md` › Typography system) | type character, families, pairing, rhythm |
| Design System / Tokens | token values |
| Visual Grammar | rendered visual behavior and exceptions |
| Motion System (`MOTION-SYSTEM.md` or grammar block) | temporal behavior |
| Web Patterns | composition vocabulary (not which content exists) |
| Component Spec | implementation contract |
| Technology Resolver + Performance Budget | implementation technology and effect/motion/interaction budgets |
| Design quality evals E65–E80 (`DESIGN-QUALITY-REPORT.md`) | runtime/visual/interaction evaluation of the outcome |
