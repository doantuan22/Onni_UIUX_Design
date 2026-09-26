# Design Knowledge System

The design knowledge layer of Phase 2: a modular, retrievable, composable catalog of design vocabulary that the reasoning layer uses to make **explainable** design decisions. It answers *what options exist, when they fit, what they cost, and how to build them*. The workflow modules decide *which one to use here and why*.

```text
DESIGN KNOWLEDGE LAYER            styles · layouts · screens · components · motion · interactions · effects · graphics · composition
        ↓ (retrieved by id, never scanned)
DESIGN REASONING LAYER            Design Direction · Design Intelligence + Capability Resolver · Design Inspiration
                                  · Typography Intelligence · Design System · Visual Grammar · Motion System
        ↓
IMPLEMENTATION INTELLIGENCE       Technology Resolver · Performance Budget · Stack Strategy
        ↓
RUNTIME / VISUAL / INTERACTION EVALUATION   Browser runtime evidence · Accessibility gate · E65–E80 quality evals
```

## Modules

| Intelligence | Location | Entries |
|---|---|---|
| Style | [styles/](styles/README.md) | 31 visual languages |
| Layout | [web-patterns/](../web-patterns/README.md): hero, grid, storytelling, application | 37 structured layouts (+ section, composition, navigation and conversion guidance) |
| Screen | [screens/](screens/README.md) | 28 screen types |
| Component | [visual-language/components/](../visual-language/components/README.md) | Component grammars incl. command/search, data display and AI interfaces |
| Motion | [motion/](../motion/README.md) | 68 patterns across primitives and tiers M1–M5, plus grammar, responsive and reduced motion |
| Interaction | [interactions/](interactions/README.md) | 26 patterns |
| Visual effect | [effects/](effects/README.md) | 26 effects |
| Advanced graphics | [graphics/techniques.md](graphics/techniques.md) + technology entries | 4 techniques + 12 technologies |
| Composition | [composition/](composition/README.md) | 16 recipes, anti-homogenization, premium quality model |
| Accessibility contract | [advanced-accessibility.md](advanced-accessibility.md) | Required for every advanced item |
| Implementation | [technology-resolver.md](../../skills/frontend-implementation/technology-resolver.md), [performance-budget.md](../../skills/frontend-implementation/performance-budget.md) | Technology decisions and budgets |

`Effect ≠ Motion ≠ Interaction`: an effect is how something looks, motion is how it changes over time, and an interaction is how input produces a result. They are decided, budgeted and reviewed separately.

## Files

- [schema.md](schema.md): the base and specialized schemas every entry follows.
- [retrieval.md](retrieval.md): how to load only what a task needs.
- [INDEX.md](INDEX.md): the generated id index (never edited by hand).

Tools (standard library only): `scripts/knowledge_lib.py` (validate, index), `scripts/resolve_capabilities.py` (resolver), `tests/test_knowledge.py` (schema, retrieval, resolver, diversity tests). Extension guide: [docs/design-knowledge-system.md](../../../../development/docs/design-knowledge-system.md).

## Principles

- Knowledge is modular (one entry, one id), retrievable (index + resolver retrieval list), composable (typed references between entries) and extensible (schema-validated).
- Every advanced technique states when to use it, when not to use it, its cost, its fallback and its accessibility behavior.
- Premium does not mean more effects ([premium quality model](composition/premium-quality-model.md)), and motion must have a purpose ([motion grammar](../motion/motion-principles.md)).
- Catalog entries never override the Structure Lock, an existing coherent design system (`KEEP`), or explicit brand guidelines.
