# Typography archetypes

Pick one type voice. Each archetype gives reasoning plus default *ranges* that [typography-rhythm.md](typography-rhythm.md) turns into a scale. Values are starting points; content and viewport testing decide.

| Archetype | Communicates | Family classes | Display : body (desktop) | Weights | Tracking | Fits |
|---|---|---|---|---|---|---|
| `neutral-product` | clarity, no opinion | neo-grotesk or humanist sans, single family | 2.5–4× | 400/500/600 | ~0 body, slight negative ≥32px | modern-saas, minimal-product, apps |
| `premium-modern` | confidence, precision, calm | neo-grotesk/grotesk, optical sizes or variable | 4–7× | 2–3 (e.g., 400/600, display 600–700) | tight negative on display (−1% to −3%) | premium-product, consumer-tech |
| `editorial` | authorship, depth, reflection | serif display (or serif throughout) + serif/humanist body | 3–5× | regular/italic/bold; italic has a job | normal; small caps slightly positive | editorial-product, luxury, portfolios |
| `technical` | rigor, systems, specs | grotesk sans + mono accent | 2.5–4× | 400/500/600 | slight negative display; mono normal | technical-platform |
| `developer` | precision, tooling fluency | neutral sans + monospace as a core voice | 2.5–4× | 400/500/700 | tight display; mono 0 | developer-tool |
| `friendly-consumer` | warmth, approachability | rounded/geometric or humanist sans | 3–5× | 400/600/700–800 | ~0; avoid very tight | consumer-tech, marketplace (consumer) |
| `luxury` | rarity, restraint | high-contrast serif or refined sans; spaced caps for labels | 4–8× (sparse use) | light/regular; contrast-checked | positive on caps labels (+5% to +15%) | luxury, fashion, hospitality |
| `dense-transactional` | efficiency, trust in numbers | neutral sans with good tabular figures; system stack acceptable | 1.6–2.5× | 400/500/600 | 0 | marketplace, travel results, dashboards, data-heavy |
| `expressive-marketing` | energy, point of view | characterful display (condensed/wide/serif) + neutral body | 5–10× (one moment) | display may be heavy | tight | campaigns, portfolios, launches (scoped) |

## Reasoning rules

- **Archetype follows the design archetype and task, not taste.** A developer tool with luxury type misleads; a data-heavy product with editorial serif body reduces scan speed.
- **Two voices at most:** a page may use a scoped secondary voice (e.g., `expressive-marketing` only in the hero of a `premium-modern` system) when recorded.
- **Dense surfaces override:** inside tables, forms and app shells, fall back to `dense-transactional` or `neutral-product` behavior even in expressive products.
- **Language first:** if the product serves Vietnamese (or other diacritic-heavy languages), eliminate archetype candidates whose natural families lack coverage before judging style. See [font-selection.md](../../skills/typography/font-selection.md#vietnamese-and-diacritics).
- **Existing brand type wins** when it is licensed, readable and coherent.

## Record

```yaml
typography_character:
  archetype: premium-modern
  secondary_scope: none            # or "hero only: expressive-marketing"
  reason: flagship hardware; product imagery carries color, type carries confidence
  display: {family_class: neo-grotesk, weight: 600, tracking: -2%, case: sentence}
  body: {size: 17-18px, line_height: 1.5, measure: 60-72ch}
  mono: specs table and model numbers only
  numerals: tabular in specs/prices; proportional in prose
```
