# Visual Effect Intelligence

An **effect** changes how a surface or element *looks* (light, material, texture, shape). It is not **motion** (how things change over time, in [motion](../../motion/README.md)) and not **interaction** (how input produces a result, in [interactions](../interactions/README.md)). One effect can be animated by a motion pattern and triggered by an interaction; each is still decided and budgeted separately.

| File | Effects |
|---|---|
| [light-and-color.md](light-and-color.md) | gradient, mesh gradient, radial lighting, spotlight, glow, edge highlight, specular highlight, holographic, chromatic |
| [depth-and-material.md](depth-and-material.md) | shadow, contact shadow, inner shadow, depth, blur, backdrop blur, glass, layered transparency, reflection, liquid |
| [texture-and-shape.md](texture-and-shape.md) | noise, grain, mask, clipping, distortion, particles, shader |

## Rules

1. **Purpose before effect.** Every effect answers one visual purpose: focus, depth/layering, material identity, atmosphere, or brand signature. No purpose means no effect.
2. **Budget.** Effect cost counts toward the page [effect budget](../../../skills/frontend-implementation/performance-budget.md#effect-budget). High-cost effects need visual intensity 4 or higher and a fallback.
3. **One signature effect.** A page has at most one signature effect (e.g., radial lighting *or* mesh gradient), plus supporting low-cost effects.
4. **Default tells.** Effects marked `default_tell: true` (glass, glow, mesh gradient, backdrop blur, particles) are overused in generated UIs; stacking two or more without a recorded reason is `HOMOGENIZED_DESIGN`.
5. **Accessibility.** Text never sits on an effect without verified contrast. Honor `prefers-reduced-transparency` and `prefers-contrast` where the effect reduces legibility.

Schema: [schema.md](../schema.md#effect).
