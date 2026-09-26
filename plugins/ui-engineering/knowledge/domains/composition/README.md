# Composition Intelligence

Composition turns separate choices (style, layout, typography, color, components, motion, interaction, effects) into **one design language**. A page is coherent when every layer expresses the same character at a matching intensity.

| File | Use |
|---|---|
| [recipes.md](recipes.md) | Worked, coherent combinations by product category (anchors, not templates) |
| [anti-homogenization.md](anti-homogenization.md) | Pre-design declaration and default-combination guard |
| [premium-quality-model.md](premium-quality-model.md) | What "premium" means and how it is evaluated |

## Composition method

1. **Start from the resolver output** ([CAPABILITY-PLAN.md](../../../templates/CAPABILITY-PLAN.md)): primary style, optional scoped secondary, layout and screen candidates, motion, interaction, effects, technology.
2. **Pick a recipe anchor** (best domain and style match). Keep only the anchor items that also pass the resolver filters, and never copy a recipe wholesale.
3. **Align intensity across layers.** Visual intensity (style, effects), motion intensity and interaction intensity must sit within one level of each other. A calm style with cinematic motion, or a loud style with timid motion, reads as incoherent (`STYLE_INCOHERENCE`).
4. **Choose one signature per page.** Name one memorable moment (a lighting treatment, a product walkthrough, a typographic statement). Everything else supports it. Two signatures compete.
5. **Map each layer to its owner artifact.** Type → Design System typography section; tokens → DESIGN-TOKENS; visual behavior → VISUAL-GRAMMAR; temporal behavior → MOTION-SYSTEM; composition → pattern selection in DESIGN-INSPIRATION; tech → CAPABILITY-PLAN. Nothing is decided twice.
6. **Write the WHY lines.** For style, layout, interaction, motion, effect and technology, record *why this* and *why not the runner-up*. The resolver's scores are evidence, not a substitute for the sentence.
7. **Check the budgets** in [performance-budget.md](../../../skills/frontend-implementation/performance-budget.md) and the [premium quality model](premium-quality-model.md) before implementation.

## Coherence rules

- One surface philosophy per page (card-driven *or* card-free; flat *or* layered).
- One light direction and one elevation logic.
- Equivalent components share motion tokens, radius family and feedback behavior.
- Effects follow the style's `recommended_effects`. An item from `avoid_effects` needs a recorded exception.
- The secondary style is scoped to a region or layer (e.g., "developer-tool traits in docs areas"). It never mixes into every component.
