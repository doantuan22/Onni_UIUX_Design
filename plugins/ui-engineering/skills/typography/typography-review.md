# Typography review

Run on rendered output (or code when rendering is unavailable, marked as such) during [craft review](../visual-language/craft-review.md). Record findings in `VISUAL-REVIEW.md`.

| Code | Detect | Typical fix |
|---|---|---|
| `TYPOGRAPHY_CHARACTER_MISSING` | No recorded type archetype; framework-default type with no decision; type voice contradicts design archetype | Choose archetype via [typography-archetypes.md](../../knowledge/typography/typography-archetypes.md); record it |
| `WEAK_TYPE_HIERARCHY` | Adjacent roles differ < ~1.15× or by weight alone at similar size; headings compete; primary message not dominant | Rebuild scale in [typography-rhythm.md](../../knowledge/typography/typography-rhythm.md); reduce sizes in use |
| `EXCESSIVE_FONT_FAMILIES` | See [font-pairing.md](../../knowledge/typography/font-pairing.md) | Collapse to single family or justified pair |
| `DISPLAY_FONT_MISUSE` | Display face in body/labels/dense UI or below ~20px; oversized hero with long copy | Restrict display role; switch to compact display pattern |
| `POOR_READING_MEASURE` | Reading text > ~85ch or < ~40ch on desktop; body line-height < 1.4 | Set `max-width` in `ch`; adjust line-height |
| `MONO_OVERUSE` | Mono outside technical content | Restrict to code/IDs/metadata role |
| `TYPE_STYLE_DRIFT` | Ad-hoc sizes/weights outside tokens; same role rendered differently across pages | Normalize to tokens; add missing role only if justified |

Additional checks: Vietnamese/diacritic rendering in all used weights; tabular numerals in tables/prices; no text overflow at 320px; contrast of light weights; heading wrap balance; font loading shift (fallback metrics).

Already-good typography: if the existing system passes these checks and fits the direction, record `KEEP` and do not change it.
