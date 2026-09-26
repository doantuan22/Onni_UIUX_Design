# Accessibility contract for advanced design

Every advanced effect, motion, interaction or graphic must satisfy this contract before it ships. It extends, and does not replace, the [Accessibility Gate](../../execution/accessibility/gate.md) and Phase 2 [accessibility quality](../../skills/final-quality-gate/accessibility.md). Accessibility is never optional polish.

| Requirement | Applies to | Rule |
|---|---|---|
| `prefers-reduced-motion` | All non-essential motion | Per-entry `reduced_motion` fallback implemented; content fully visible and operable ([reduced-motion.md](../motion/reduced-motion.md)) |
| Keyboard | Every interaction | Full keyboard path; gestures have visible control alternatives |
| Focus visibility | Every focusable element, including over effects | Focus ring visible over glass, gradients, media and dark stages; never clipped |
| Screen reader | Canvas, WebGL, split text, streaming content | Equivalent text; animated splits `aria-hidden` with full text available; polite announcements, not per-token |
| Contrast | Text over effects (gradients, glass, images, glow) | Verified at the worst point of the background; control boundaries 3:1 |
| Touch target | All controls | At least 24px minimum (44px recommended) regardless of visual size |
| Non-hover alternative | Hover previews, hover-only affordances, spotlights, magnetic effects | Same information/action available on focus and touch |
| Motion fallback | M4/M5, continuous loops | Pause/stop for anything moving more than 5 seconds; poster for graphics |
| Transparency and contrast preferences | Glass, backdrop blur, layered transparency | `prefers-reduced-transparency` and `prefers-contrast: more` switch to opaque, higher-contrast surfaces where supported |
| Flashing | Glitch, chromatic, shader, particles | No more than 3 flashes per second |

## Review codes

A failure is recorded with the most specific code: `MOTION_WITHOUT_REDUCED_MODE`, `HOVER_ONLY_INTERACTION`, `HIDDEN_INTERACTION`, or an accessibility gate finding. Evidence comes from the accessibility runtime when available; otherwise the limitation is reported honestly.
