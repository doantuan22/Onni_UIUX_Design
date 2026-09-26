# Design Inspiration Engine

This module turns an approved Design Direction into a **selected design DNA**: a small, compatible set of archetype and reference traits that the rest of Phase 2 realizes. It answers "which good visual language fits this product, and why?" after the anti-generic layer has answered "what should we avoid?".

It sits between [Design Direction](../design-direction/workflow.md) and [Typography Intelligence](../typography/README.md). It never changes the Structure Lock, page responsibilities, required content, or flows.

## Files

| File | Use when | Owns |
|---|---|---|
| [workflow.md](workflow.md) | Any inspiration decision | Inputs, steps, output artifact, scale-down rules |
| [archetypes.md](archetypes.md) | Choosing a product visual family | 12 curated archetypes and their DNA |
| [reference-profiles.md](reference-profiles.md) | A named product/"X-like" style is requested, or an archetype needs a concrete anchor | Abstract DNA of well-known product languages |
| [reference-extraction.md](reference-extraction.md) | User supplies a screenshot, URL, site name, or visual reference | Extraction dimensions and output format |
| [pattern-selection.md](pattern-selection.md) | Choosing composition/section/hero/motion patterns | Pattern Selection Engine and anti-template rule |
| [anti-copying.md](anti-copying.md) | Any reference is involved | Transformation rules and copy boundaries |

## Source-of-truth boundary

| Owner | Owns | Does not own |
|---|---|---|
| Design Direction | desired experience, audience perception, avoid-list | concrete type/motion/pattern choices |
| **Design Inspiration** | archetype, mixed DNA, reference transformation, pattern candidates | tokens, component APIs, page structure |
| Typography Intelligence | type character, families, pairing, rhythm | color or composition |
| Design System | tokens | why a family was chosen |
| Visual Grammar | rendered visual behavior and exceptions | the reference DNA itself |
| Motion System | temporal behavior | static composition |
| Web Patterns | composition vocabulary | which content exists (Phase 1) |

The engine records its decisions in [DESIGN-INSPIRATION.md](../../templates/DESIGN-INSPIRATION.md). For a user-supplied reference, the per-dimension evidence goes to [REFERENCE-ANALYSIS.md](../../templates/REFERENCE-ANALYSIS.md) and is summarized, not duplicated, in the inspiration artifact.

## Invariants

- An archetype is a reasoning anchor, not a style preset or a template.
- References provide design DNA, not layouts to reproduce. See [anti-copying.md](anti-copying.md).
- Mix at most one primary and one secondary DNA source (optionally one narrowly scoped accent trait). Incompatible mixes are rejected.
- Popularity is not a selection reason. Every selected trait traces to product, audience, content, or brand evidence.
- Everything here is local knowledge. No runtime fetch of an external website is required or implied.
