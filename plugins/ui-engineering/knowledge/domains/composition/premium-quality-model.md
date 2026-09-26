# Premium quality model

> **Premium ≠ more effects.**

```text
Premium Quality = Visual Hierarchy + Consistency + Typography + Spacing
                + Interaction Feedback + Motion Timing + Transition Continuity
                + Detail Quality + Responsiveness + Performance + Accessibility + Restraint
```

Each dimension is necessary. A single failing dimension caps the whole: a beautiful page that janks, or ignores keyboard users, is not premium.

| Dimension | Premium signal | Evidence | Eval |
|---|---|---|---|
| Visual hierarchy | Primary message/action dominant in under 3 seconds | Screenshot review, squint test | E80 |
| Consistency | Equivalent components look and behave identically | Component samples, token usage | E74 |
| Typography | Deliberate type character, scale, measure | Typography review codes | E75, E80 |
| Spacing | Grouping by spacing with a clear rhythm | Screenshot + token audit | E73 |
| Interaction feedback | Every control responds within ~100ms with states | Static analysis + manual/runtime check | E69 |
| Motion timing | Durations/easings from tokens, purposeful | Static duration/easing inventory | E66 |
| Transition continuity | Objects keep identity between states | Artifact + runtime probe | E70 |
| Detail quality | States, edge cases, alignment, optical adjustments | Detail checklist | E76 |
| Responsiveness | Layout and motion adapted, not shrunk | Mobile captures + probes | E78 |
| Performance | No jank, no layout shift from motion/effects | Static risk + CLS probe | E67 |
| Accessibility | Reduced motion, focus, contrast, keyboard | Accessibility gate + E68 | E68 |
| Restraint | One signature moment; effects within budget | Effect/motion inventory | E72 |

## Detail checklist (premium detail density)

- Focus-visible styles designed, not default outlines left by accident.
- Hover, pressed, disabled, loading, empty and error states exist for interactive components.
- Nested radii are concentric; borders align; icons optically centered.
- Numbers use tabular numerals where they change or align.
- Images have reserved aspect ratios (no layout shift) and art-directed crops.
- Text wraps balanced in headings; no orphans in key lines where supported.
- Copy is specific (no "Ready to get started?" placeholders).
- Micro-typography: proper quotes, dashes and non-breaking spaces in units and currencies.

## Using the model

- **Before implementation:** state which dimensions the design direction invests in and which restraint decisions were made (what was *not* added).
- **During review:** the [craft review](../../../skills/visual-language/craft-review.md) and E65–E80 evaluate the dimensions. A failure in performance, accessibility or consistency blocks a "premium" claim regardless of visual polish (`PREMIUM_BY_EFFECTS` when polish was pursued through effects instead).
