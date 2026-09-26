# Performance budget for advanced design

Advanced design must not break performance. This file sets **effect, motion and interaction budgets** and device degradation. Motion-specific implementation rules (transform/opacity, scroll listeners, rAF, IntersectionObserver) are in [motion performance safety](../../knowledge/motion/performance-safety.md) and are not repeated here.

## Cost model

Every catalog entry declares `performance.cost` (motion, effects) or `cost` (technology, graphics):

| Cost | Points | Meaning |
|---|---|---|
| none | 0 | Declarative, no paint beyond normal rendering |
| low | 1 | Compositor-friendly or static |
| medium | 2 | Paint per change, or bounded continuous work |
| high | 4 | Continuous paint/GPU work, large layers, heavy runtime |
| very-high | 6 | Real-time GPU rendering or large media sequences |

## Effect budget

| Visual intensity | Page effect points | Signature effects (high/very-high) |
|---|---|---|
| 1 | 2 | 0 |
| 2 | 3 | 0 |
| 3 | 5 | 0 |
| 4 | 8 | 1 |
| 5 | 12 | 1 |

Points count distinct effects in use on a page, not instances. More than 2–3 `backdrop-filter` surfaces in one viewport counts as an extra high-cost effect.

## Motion budget

- At most **one HIGH motion region** per page ([intensity budget](../../knowledge/motion/motion-principles.md#intensity-budget)).
- At most **one continuous animation visible** at a time (ambient drift, shader, particles, video loop).
- At most **one scroll-linked region active** at a time.
- Application surfaces: no continuous decorative motion at all.

## Interaction budget

- Pointer-tracking interactions (spotlight, magnetic, cursor follow, cursor-reactive scene): at most **two kinds per page**, desktop fine pointers only, each updating via CSS variables in one shared rAF.
- Gesture physics (drag with springs, swipe, pull): only where the task needs direct manipulation.
- Input feedback always wins. Nothing decorative may run on the main thread in a way that delays a press, keystroke or scroll response.

## Paint and GPU costs to watch

| Technique | Cost driver | Rule |
|---|---|---|
| `filter: blur()` | Blurs every pixel of the layer each paint | Static only; pre-blur assets; never animate the radius |
| `backdrop-filter` | Re-samples content behind on scroll | Few small surfaces; opaque fallback on mobile/low-power |
| Large `box-shadow` | Paint on each change | Animate the opacity of a pre-rendered shadow layer |
| Large gradients/meshes | Repaint when animated | Animate transforms of a layer, not gradient stops |
| Blend modes | Extra compositing | Small areas only |
| Canvas/WebGL | Continuous GPU/CPU | Visibility-gated loops, DPR cap, dispose on unmount ([graphics](../../knowledge/domains/graphics/techniques.md)) |
| Video backgrounds | Decode and bandwidth | Poster LCP, `preload="none"` or metadata, pause off-screen |

## Lifecycle requirements

- **Animation cleanup:** cancel rAF, disconnect observers, kill library timelines/ScrollTriggers, and remove listeners on unmount or route change.
- **WebGL/canvas lifecycle:** create lazily when visible, handle `webglcontextlost`, and dispose geometries, materials, textures and programs.
- **Lazy loading:** heavy graphics, Lottie/Rive assets and videos load after first paint and only near the viewport.

## Device degradation

| Tier | Detection (progressive, hints only) | Degrade to |
|---|---|---|
| Full | Fine pointer, no reduction preferences | Full plan within budget |
| Reduced | `pointer: coarse`, narrow viewport | No pointer tracking, no pinned scrubbing, halved effect budget |
| Minimal | `prefers-reduced-data`/Save-Data, `deviceMemory <= 4` or `hardwareConcurrency <= 4`, observed long frames | Static effects, posters instead of canvas/WebGL/video, no continuous motion |
| Reduced motion | `prefers-reduced-motion: reduce` | Per-entry reduced-motion fallbacks |

Detection never blocks content; the page first renders the minimal-safe version and enhances.

## Evidence

Static risk signals come from `scripts/analyze_design_quality.py`. Runtime signals (running animations, blur/backdrop counts, layout shift) come from the runner's optional motion probe. Both feed E67 Motion Performance and E72 Effect Overuse. Lighthouse is not required, and nothing is installed to measure performance.
