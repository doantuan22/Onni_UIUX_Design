# Design inspiration workflow

## Inputs

Active `DESIGN-DIRECTION.md`, locked `DESIGN-BRIEF.md` and relevant `PAGE-SPEC.md`/`WIREFRAME-SPEC.md` sections, `CURRENT-DESIGN-SYSTEM.md` for existing UI, and any user-supplied reference.

## Steps

1. **Classify the signal.** Record product type, audience, business goal, content density, interaction density, brand character, platform, and page goal (convert / inform / operate / read / browse / transact).
2. **Check the existing language.** If the current system is coherent (`KEEP`/`REFINE` in Visual Language terms), inspiration only fills gaps; it does not re-theme the product.
3. **Select a primary archetype** from [archetypes.md](archetypes.md) using the selection matrix below. Record at least one rejected archetype and why.
4. **Optionally select a secondary DNA source**: another archetype, a [reference profile](reference-profiles.md), or an extracted user reference ([reference-extraction.md](reference-extraction.md)). Run the compatibility check.
5. **Derive direction lines** for composition, typography, surface/color, imagery, and motion. These are *intent statements* consumed by [Typography](../typography/README.md), [Design System](../design-system/workflow.md), [Visual Grammar](../../knowledge/visual-language/visual-grammar.md), and [Motion](../../knowledge/motion/README.md).
6. **Shortlist patterns** with [pattern-selection.md](pattern-selection.md): candidates, selected, rejected, each with a content reason.
7. **Apply [anti-copying.md](anti-copying.md)** and record transformation constraints.
8. Write [DESIGN-INSPIRATION.md](../../templates/DESIGN-INSPIRATION.md).

## Selection matrix (starting points, not rules)

| Signal | Leans toward | Leans away from |
|---|---|---|
| Physical/hero product, high price, emotional purchase | premium-product, consumer-tech, luxury | data-heavy-product, marketplace |
| Developers are the buyer and user; docs/CLI/API matter | developer-tool, technical-platform | luxury, creative-portfolio |
| Infrastructure, security, reliability, enterprise evaluation | technical-platform, modern-saas | playful consumer-tech |
| Long-form reading, publishing, knowledge | editorial-product, minimal-product | high-density product |
| Portfolio, studio, agency, personal work | creative-portfolio, editorial-product | marketplace |
| Many sellers/listings, search-first, trust and price | marketplace, travel-commerce | cinematic premium-product |
| Operational monitoring, analytics, tables | data-heavy-product, modern-saas | cinematic/luxury |
| Few actions, one clear job, calm brand | minimal-product | expressive-marketing styles |
| Rarity, craft, heritage, price opacity | luxury, editorial-product | dense-transactional |

A tie is resolved by the **primary task**, then **content that actually exists**, then **brand character**. If the content needed by an archetype (e.g., large product imagery) does not exist and cannot be supplied, that archetype is rejected.

## Scale-down

- **Small visual task / component polish:** skip this module; Visual Grammar governs.
- **Single page, no references:** one archetype + direction lines, recorded inside `DESIGN-DIRECTION.md` (no separate artifact).
- **Landing/marketing/product showcase, redesign, or any reference:** full `DESIGN-INSPIRATION.md`.
- **Dashboard/app screens:** archetype only (usually data-heavy-product, modern-saas, or developer-tool); skip hero/storytelling pattern selection.

## Exit check

- One primary archetype with evidence; rejected alternatives recorded.
- ≤ 2 DNA sources plus at most one scoped accent trait; compatibility passed.
- Direction lines exist for type, composition, surfaces/color, imagery, motion.
- Pattern shortlist reasoned from content; anti-copy constraints recorded when a reference exists.
- Nothing contradicts the Structure Lock. A needed content/section change is a Phase 1 rollback request, not a pattern choice.

## Inspiration pipeline (knowledge-backed)

```text
Reference → Decompose (style, layout, typography, color, motion, interaction, effect, composition)
→ Extract principles (map each observation to catalog ids) → Adapt (Capability Resolver + anti-copying) → Implement
```

When a reference exists, [reference extraction](reference-extraction.md) maps observations to Design Knowledge ids (`style.*`, `layout.*`, `motion.*`, `interaction.*`, `effect.*`). The resolver profile then uses them as `explicit_styles` or overrides, which keeps the adaptation explainable and prevents cloning. This is the same pipeline as above, not a parallel workflow.
