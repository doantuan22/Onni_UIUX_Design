# Anti-copying rules

References are design-language inspiration, not templates to reproduce. This file is the source of truth for copy boundaries across inspiration, reference analysis, and web patterns.

## Never copy

- Logos, marks, trademarks, brand names in UI, or brand-identifying color combinations.
- Proprietary photography, renders, illustrations, icons, video, fonts, or any downloaded asset.
- Exact copywriting, headlines, taglines, or microcopy.
- Source code, CSS, or markup from the reference.
- The exact page hierarchy/section order when the project's content does not require it.
- A complete, recognizable visual identity (the combination that makes someone think "this is X's site").

## Transform instead

| Borrowed | Transform into |
|---|---|
| A specific layout | The *principle* behind it (e.g., "one idea per section") realized with project content and grid |
| A signature visual (gradient field, illustration style) | A project-owned signature moment derived from its own brand/product |
| A proprietary typeface | A licensed family chosen by [font-selection](../typography/font-selection.md) for similar character |
| An interaction | The interaction's *job* (orientation, proof, comparison) realized with a fitting pattern |
| A section sequence | A narrative built from [storytelling patterns](../../knowledge/web-patterns/storytelling/storytelling-patterns.md) and the locked content |

## Distance test (run before implementation)

A result fails (`REFERENCE_COPYING`) when two or more hold:

1. Side by side, a viewer would name the reference brand rather than the project.
2. Three or more consecutive sections match the reference's type-order and layout.
3. The signature visual element is reproduced rather than reinterpreted.
4. Copy or asset text is reused or trivially paraphrased.
5. The reference's proprietary typeface or an intentional look-alike is used to mimic identity.

## Explicit user request to clone

If the user asks to replicate another brand's site: explain the boundary, offer design-DNA extraction, and proceed with a transformed direction. Only the user's **own** assets/brand may be reproduced exactly.

## Recording

Every reference-influenced direction lists `do_not_copy` items and the transformation applied in `DESIGN-INSPIRATION.md`. Craft review checks them.
