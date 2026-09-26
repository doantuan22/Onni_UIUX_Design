# Typography Intelligence

Typography is part of product character, not merely font sizing. This module decides **type character, families, pairing, display/body/technical strategy, and rhythm** before tokens are written, then reviews the rendered result.

It runs after [Design Inspiration](../design-inspiration/README.md) (or directly after Design Direction for small work) and before [Design System](../design-system/workflow.md). Output is recorded in the **Typography system** section of [DESIGN-SYSTEM.md](../../templates/DESIGN-SYSTEM.md); there is no separate typography artifact. [DESIGN-TOKENS.md](../../templates/DESIGN-TOKENS.md) holds values; [typography-character](../../knowledge/visual-language/typography-character.md) in Visual Grammar records only rendered behavior and exceptions.

## Decisions owned

```text
type character      what the voice communicates (archetype)
display strategy    scale, weight, tracking, case, when display is used
body strategy       size, line-height, measure, weight
weight contrast     number of weights and their jobs
size contrast       ratio between display, headings and body per breakpoint
line-height         per role, tighter as size grows
tracking            per role, negative on large display, positive on small caps/labels
measure             characters per line for reading
font width          normal / condensed / wide and why
mono usage          which content is code/technical
numeric treatment   tabular / proportional / oldstyle, per context
```

## Files

| File | Load when |
|---|---|
| [typography-archetypes.md](../../knowledge/typography/typography-archetypes.md) | Choosing the type voice |
| [font-selection.md](font-selection.md) | Choosing or validating families (includes Vietnamese coverage) |
| [font-pairing.md](../../knowledge/typography/font-pairing.md) | More than one family is considered |
| [display-type.md](../../knowledge/typography/display-type.md) | Heroes, headlines, marketing |
| [body-type.md](../../knowledge/typography/body-type.md) | Reading, forms, app UI text |
| [technical-type.md](../../knowledge/typography/technical-type.md) | Code, data, metrics, IDs, tables |
| [typography-rhythm.md](../../knowledge/typography/typography-rhythm.md) | Scale, line-height, vertical rhythm, responsive type |
| [typographic-composition.md](../../knowledge/typography/typographic-composition.md) | Headline/eyebrow/metric patterns |
| [typography-review.md](typography-review.md) | Review of rendered type |

Small task: load only the file for the role being changed (e.g., body-type for a reading page) plus review.

## Existing type systems

If a coherent type voice exists, classify it with Visual Language (`KEEP`/`REFINE`/`NORMALIZE`/`REPLACE`). Do not replace a working family because another is fashionable. Refine scale, measure or numeric treatment first.

## Constraints

- Never download, vendor, or bundle font files into the skill or a project unless the project already hosts fonts and the task authorizes adding one. Reference families by name and loading method only.
- Never add a font package without need and authorization; prefer an existing project font, then system stacks, then a licensed web font through the project's existing loading mechanism.
