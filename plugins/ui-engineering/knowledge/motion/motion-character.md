# Motion character

Choose a character before animating anything. It sets default durations, easing, distance and where motion is allowed. [Visual Language motion-character](../visual-language/motion-character.md) records the rendered behavior that realizes it.

| Character | Feel | Durations | Easing | Distance | Fits |
|---|---|---|---|---|---|
| `minimal` | almost static; feedback only | fast | standard ease-out | 0–4px, opacity | data-heavy, forms, minimal-product, editorial reading |
| `snappy` | quick, decisive, responsive | fast–short | sharp ease-out | small | developer-tool, marketplace controls, productivity |
| `soft` | gentle, calm, friendly | short–moderate | smooth ease-out | small–medium | consumer-tech, travel inspiration, warm-document |
| `cinematic` | slow reveals, scale, depth | moderate–long (storytelling) | expressive ease-out, linear for scrub | large | premium-product, luxury (sparse) |
| `expressive-controlled` | confident moments inside a disciplined system | mixed: expressive hero, fast controls | expressive + standard | medium–large in moments | premium SaaS, launches, creative tools |
| `playful` | springy, characterful | short | low-overshoot spring | small–medium | consumer apps, education, games-adjacent |
| `technical` | precise, mechanical, stepwise | short | linear/steps, crisp ease | small; build-ups | technical-platform, developer diagrams |

## Declaring it

```yaml
motion_character:
  base: expressive-controlled
  microinteraction: subtle        # low
  hero: expressive                # high
  navigation: minimal             # low
  scroll_storytelling: medium
  decorative_loop: rare           # none | rare (with rationale)
  reason: premium product launch; one cinematic reveal, calm elsewhere
```

## Rules

- One base character per product; a region may be more expressive only within the [intensity budget](motion-principles.md#intensity-budget).
- The character must match the [design archetype](../../skills/design-inspiration/archetypes.md); `cinematic` in a developer tool or `playful` in a banking dashboard is `MOTION_STYLE_DRIFT`.
- Existing coherent motion (durations, easing, library) is kept unless it violates purpose, performance or reduced-motion rules.
