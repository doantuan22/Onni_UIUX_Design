# Reference extraction

Use when the user supplies a screenshot, URL, site name, or other visual reference. Extract **transferable design DNA** into [REFERENCE-ANALYSIS.md](../../templates/REFERENCE-ANALYSIS.md). Adjectives such as "clean", "modern", or "premium" are not extraction; each dimension must name observable, reusable decisions.

## Source handling

- **Screenshot/image:** analyze what is visible; mark unseen states (hover, motion, mobile) as `unknown`, not assumed.
- **URL:** inspect only if a browsing capability exists *and* the task allows it; otherwise treat as a named reference. The skill never depends on fetching it; offline work must still succeed.
- **Site name only:** use a matching [reference profile](reference-profiles.md) if present; otherwise ask for a screenshot or extract from general knowledge and mark confidence `low`.
- Record each observation's **confidence** (`observed` / `inferred` / `unknown`).

## Dimensions

| Dimension | Extract (observable) | Not enough |
|---|---|---|
| Composition | alignment axis, symmetry, hero scale vs viewport, focal object, whitespace ratio | "spacious" |
| Grid | column count, gutters, visible/invisible grid, breakouts, full-bleed usage | "nice layout" |
| Type | families' classification (grotesk/humanist/serif/mono), display:body size ratio, weight contrast, tracking, measure, case usage | "modern font" |
| Spacing rhythm | section spacing vs intra-group spacing ratio, repetition or variation of section heights | "airy" |
| Surface behavior | card frequency, border vs shadow vs tone, radius family, nesting | "minimal cards" |
| Color behavior | base temperature, accent frequency and roles, dark/light alternation, gradient scope | "blue" |
| Imagery | subject (product/people/UI/abstract), scale, crop, treatment, consistency | "good photos" |
| Iconography | style (line/solid), weight, frequency, labeling | "icons" |
| Motion | where motion appears, character, intensity, trigger (load/scroll/hover) | "animated" |
| Interaction | primary interaction models (tabs, switchers, sliders), feedback style | "interactive" |
| Section rhythm | sequence of section *types* and their narrative job | "sections" |
| Information hierarchy | what is read first/second/third; how proof relates to claims | "clear" |

## Output

For each dimension write: *observed language → transferable principle → reinterpretation for this product → do-not-copy item*. Then classify the reference into one primary [archetype](archetypes.md) and list 3–6 **transferable traits** that will enter `DESIGN-INSPIRATION.md`.

Example (abridged):

```yaml
reference: user screenshot of a premium audio product page
archetype: premium-product (secondary trait: technical-platform spec presentation)
transferable_traits:
  - one product idea per section, full-width tonal bands
  - display:body ratio ≈ 5:1 on desktop, tight display tracking
  - specs presented as a mono-accented comparison table after the story
  - motion concentrated in one scroll-linked product reveal
do_not_copy: [product renders, exact headline copy, section order, brand typeface, logo]
```

## Multiple references

Extract each, then find the **shared** traits. Traits appearing in only one reference are candidates for a scoped accent or are dropped. Apply the compatibility rules in [archetypes.md](archetypes.md#compatibility); never merge every reference's signature.

## Mapping to the Design Knowledge System

After extraction, name the closest catalog entries for each dimension: style ([styles](../../knowledge/domains/styles/README.md)), layout ([web-patterns](../../knowledge/web-patterns/README.md)), motion (tier and entry id), interaction ([interactions](../../knowledge/domains/interactions/README.md)) and effect ([effects](../../knowledge/domains/effects/README.md)). Record them in REFERENCE-ANALYSIS as "maps to" ids. An observation with no catalog match is described in words and may justify a new catalog entry (see [docs/design-knowledge-system.md](../../../../development/docs/design-knowledge-system.md)).
