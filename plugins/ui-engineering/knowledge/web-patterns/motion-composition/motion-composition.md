# Motion composition

Distributes the [motion intensity budget](../../motion/motion-principles.md#intensity-budget) across selected patterns so the page has one focal motion moment and calm elsewhere.

## Pattern → motion defaults

| Pattern | Default intensity | Typical vocabulary |
|---|---|---|
| minimal-typographic hero | low | fade, optional line reveal |
| product-stage hero | medium | scale/fade of product |
| cinematic-product hero | high | image sequence/scale, scroll-linked reveal |
| editorial-split hero | low | mask reveal on image (optional) |
| immersive-fullscreen hero | medium | slow image scale, fade |
| feature-alternating | low–medium | section fade-up once |
| feature-grid | low | none or group fade |
| sticky-storytelling | medium | state crossfade/transform per step (pinned scrubbing = high) |
| comparison / FAQ / technical-detail | low | expand/collapse |
| metric-story | low–medium | counter on enter |
| CTA | low | press/hover only |

## Page recipes (examples, not templates)

```text
Premium launch:   cinematic hero (HIGH) → feature-alternating (low) → pinned demo? ✗ (second HIGH too close; sticky reveal at medium is fine)
                  → technical-detail (low) → CTA (low)
Developer tool:   minimal-typographic (low) → capability→evidence with code (low) → comparison (low) → docs CTA
Editorial:        editorial-split (low) → long-form (none) → index (none)
Travel:           media-led with search (low) → listing (low, feedback only) → gallery interactions (medium, on demand)
```

If two HIGH patterns are both justified on a long page, separate them by at least two low sections and confirm the performance budget. Otherwise downgrade one.

Pattern names above are the `aliases` of structured layout entries (e.g., minimal-typographic → `layout.hero-centered`, cinematic-product → `layout.hero-cinematic`). The motion cost of every layout is its `motion_cost` field, and the page budget is enforced by the [Capability Resolver](../../../skills/capability-resolver/resolver.md#motion-gating).
