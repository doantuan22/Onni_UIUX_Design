# Motion & Interaction Engine

Motion must communicate, orient, or support storytelling. This module decides **motion character, intensity budget, timing/easing, vocabulary, reduced-motion behavior, and implementation strategy**, then reviews the result. It owns temporal behavior; it does not own static composition (Web Patterns) or tokens (Design System).

## Position

Runs after Visual Grammar and before Web Pattern selection is finalized (pattern choice and motion budget are checked together), then feeds Component Specs. Output goes to [MOTION-SYSTEM.md](../../templates/MOTION-SYSTEM.md) for landing/marketing/storytelling or any medium/high budget work; for low-budget app work, a `motion_character` block in `VISUAL-GRAMMAR.md` is enough. Duration/easing **values** live in `DESIGN-TOKENS.md`; MOTION-SYSTEM references token names.

## Files

| File | Load when |
|---|---|
| [motion-principles.md](motion-principles.md) | Always, when motion is in scope: motion grammar (purposes, hierarchy, tiers, duration scale, easing, springs, budget, anti-patterns) |
| [motion-character.md](motion-character.md) | Choosing the motion personality |
| [motion-vocabulary.md](motion-vocabulary.md) | Tier index and primitives (fade, fade-up, slide, scale, clip, stagger, ambient drift) |
| [microinteractions.md](microinteractions.md) | M1 micro motion: controls, feedback, loading/success/error, skeleton, progress |
| [spatial-motion.md](spatial-motion.md) | M2 component transitions: accordion, modal, drawer, tabs, menus, carousel, toast, command palette, filters |
| [layout-motion.md](layout-motion.md) | M3 layout transitions: shared element, FLIP, list→detail, reorder, morphs, cross-page continuity |
| [scroll-motion.md](scroll-motion.md) | M4 scroll choreography (marketing/content only) |
| [text-motion.md](text-motion.md) | M4 typography motion: line/word/character reveals, counters |
| [cinematic-motion.md](cinematic-motion.md) | M5 cinematic/immersive: 3D, WebGL, particles, physics, shaders (gated) |
| [responsive-motion.md](responsive-motion.md) | Desktop/tablet/mobile/low-power/reduced-motion behavior for M3+ |
| [reduced-motion.md](reduced-motion.md) | Always, when any motion exists |
| [performance-safety.md](performance-safety.md) | Any scroll-linked, continuous, or large-area motion |
| [motion-review.md](motion-review.md) | Review of rendered motion |

Progressive disclosure: dashboards/forms load principles + M1 (+ M2 for overlays, M3 for list/detail) + reduced-motion only. M4 is for marketing/content pages; M5 only when the Capability Resolver allows it. Every entry is a structured catalog item of the [Design Knowledge System](../domains/README.md).

## Dependencies

- Prefer CSS transitions/transforms/keyframes, `IntersectionObserver`, `requestAnimationFrame` when justified, and native scroll-driven animation or View Transitions as progressive enhancement.
- **Reuse** an animation library already present in the project (GSAP, Framer Motion/Motion, Anime.js, etc.) instead of adding another or mixing systems.
- Do **not** add GSAP, Framer Motion, Anime.js, Three.js, Lottie or similar unless the need cannot be met natively *and* the task authorizes a new dependency. Record the justification.
- Exception: under ambition **Elevate** or **Reimagine** (`allow_motion_library: true` from `orchestrate_ui`) one motion library is sanctioned — Motion (`motion`/`framer-motion`) for React component, layout and gesture motion, or GSAP for scroll-scrubbed, pinned and timeline work — when native CSS cannot deliver the chosen motion. Never both; propose the install command to the user instead of installing; keep a reduced-motion path. See [ambition-levels.md](../../workflows/ambition-levels.md#motion-libraries).
