# Phase 2 workflow

```text
Structure Lock → frontend analysis → design direction → design intelligence + capability resolver
→ design inspiration → typography intelligence → design system/tokens
→ visual language → motion → web pattern selection → component realization → technology resolver → implementation
→ responsive/interactions/states → craft review → run application → visual QA
→ accessibility QA → design quality evals (E65–E80, when in scope) → final quality gate → final review
```

| Order | Module | Primary output / decision | Gate |
|---|---|---|---|
| 1 | [router.md](router.md) | Valid lock, mode, stack, selected references/artifacts | Missing or invalid lock → `BLOCKED` or Phase 1. |
| 2 | [01-design-direction](../design-direction/workflow.md) | `DESIGN-DIRECTION.md`; reference analysis if supplied | No CSS before direction exists. |
| 3 | [02-design-intelligence](../design-intelligence/workflow.md) + [Capability Resolver](../capability-resolver/README.md) | Deliberate strategy; `CAPABILITY-PLAN.md` with why / why not and retrieval list | Avoid a random default style; pre-design declaration first. |
| 3a | [Design Inspiration](../design-inspiration/workflow.md) | `DESIGN-INSPIRATION.md`: archetype, DNA, pattern candidates | Router-selected; references transformed, not copied. |
| 3b | [Typography Intelligence](../typography/README.md) | Typography system section of `DESIGN-SYSTEM.md` | Type character decided before type tokens. |
| 4 | [03-design-system](../design-system/workflow.md) | Design system and tokens | Tokens/system precede page-by-page styling for large work. |
| 5 | [Visual Language](../visual-language/workflow.md) | `VISUAL-GRAMMAR.md`, existing-pattern classification, behavior rules | Tokens alone are insufficient; preserve coherent patterns unless justified. |
| 5a | [Motion](../../knowledge/motion/README.md) | `MOTION-SYSTEM.md` or grammar motion block | Character + budget + reduced-motion before animating. |
| 5b | [Web Patterns](../../knowledge/web-patterns/README.md) via [pattern selection](../design-inspiration/pattern-selection.md) | Selected/rejected patterns per locked block | Content-driven; no default template composition. |
| 6 | [04-component-realization](../component-realization/workflow.md) | Component contracts and reuse plan | Search/extend existing components first. |
| 7 | [05-frontend-implementation](../frontend-implementation/workflow.md) + [technology resolver](../frontend-implementation/technology-resolver.md) + [performance budget](../frontend-implementation/performance-budget.md) | Stack-conforming rendered implementation map | Preserve stack and semantics; simplest sufficient technology; no unauthorized dependency. |
| 8 | [06-responsive-interaction](../responsive-interaction/responsive.md) | Responsive, interaction, and required state realization | Preserve Phase 1 semantics. |
| 9 | [Visual craft review](../visual-language/craft-review.md) | Grammar/density findings and targeted fixes | Run adversarial review for redesign/generic-density risk. |
| 10 | [07-visual-qa](../visual-qa/browser-loop.md) | Visual review evidence and refinements | Compile success is not visual success. |
| 10a | [Design quality evals](../../evals/quality/README.md) | `DESIGN-QUALITY-REPORT.md` (E65–E80) | Runtime-dependent items stay `NEEDS_RUNTIME` without evidence. |
| 11 | [08-final-quality-gate](../final-quality-gate/final-gate.md) | Quality report and pass/fail | Structural mismatch → Phase 1; other issue → Phase 2. |

Small projects may merge Design Direction + Design System, Component Spec + implementation notes, and Visual Review + Final Review. Large projects should establish tokens, base, shared components, representative pages, then page groups; do not redesign all pages in one context.

Steps 3a, 3b, 5a and 5b run only when the router selects them. Small tasks merge them into `DESIGN-DIRECTION.md`/`VISUAL-GRAMMAR.md` (archetype, type character, motion character) rather than creating separate artifacts.
