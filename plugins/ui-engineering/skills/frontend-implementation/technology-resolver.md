# Technology resolver

Chooses the **simplest technology that satisfies a selected motion, effect, interaction or graphic**. It runs after the [Capability Resolver](../capability-resolver/README.md) has chosen capabilities and before implementation. The resolver never installs anything; a new dependency needs a need that native tooling cannot meet **and** task authorization.

## Resolution order

1. **Existing project dependency** that can do the job (detected read-only by `scripts/detect_capabilities.py` → `design_runtime`). Reuse it; do not add a second library for the same job.
2. **Native platform** option among the capability's *preferred* technologies: CSS (transitions, keyframes, scroll-driven animations, `@starting-style`), native JS (IntersectionObserver, rAF, pointer events), Web Animations API, View Transitions API, SVG, Canvas 2D, WebGL.
3. **Preferred library**, only if a new dependency is authorized: Motion → GSAP → Rive/Lottie (asset-driven) → Three.js (3D). Under ambition Elevate/Reimagine, `allow_motion_library` sanctions exactly one of Motion or GSAP (reusing whichever is already installed) without a general dependency authorization; it is still listed in `new_dependencies` and reported to the user with its install command.
4. **Native fallback** among the capability's *alternatives* (e.g., CSS scroll-driven animation instead of GSAP pinning), recorded as a fallback.
5. Otherwise **degrade**: drop the capability, use its documented reduced/static version, and record why. Never silently add a package.

## Decision matrix

| Need | First choice | Escalate to | Never for this need |
|---|---|---|---|
| Hover, press, focus, color/opacity state | `tech.css` | — | any library |
| Simple enter/exit, disclosure, tabs | `tech.css` (`@starting-style`, grid-rows) | `tech.waapi`, existing `tech.motion` | GSAP, Three.js |
| Reveal on scroll (once) | `tech.native-js` IntersectionObserver + CSS | `tech.css` scroll-driven (`@supports`) | scroll listeners doing layout reads |
| Scroll-linked scrub (progress, parallax, pinned) | `tech.css` scroll-driven with static fallback | `tech.gsap` (ScrollTrigger) or existing `tech.motion` `useScroll` | rAF + scroll handler without throttling |
| Layout morph, shared element, reorder | `tech.view-transitions` (same-document) | `tech.motion` layout animations, FLIP via `tech.waapi` | manual per-frame DOM measurement |
| Complex multi-step timeline | `tech.waapi` sequences if short | `tech.gsap` timeline | chained setTimeouts |
| Interactive vector animation with states | `tech.rive` | `tech.svg` + `tech.waapi` for simple cases | video |
| Designer-exported illustration playback | `tech.lottie` | animated `tech.svg` / video with poster | Rive when no state machine is needed |
| Complex SVG path morph | `tech.svg` + `tech.gsap` (MorphSVG-like) or `tech.waapi` on compatible paths | — | Canvas re-implementation |
| Many 2D particles/procedural drawing | `tech.canvas` | `tech.webgl` for > few thousand elements | DOM nodes per particle |
| 3D product/scene | `tech.threejs` | raw `tech.webgl` only for custom pipelines | CSS 3D hacks for real models |
| Shader effect (distortion, noise field, liquid) | `tech.webgl` (small fragment shader) | `tech.threejs` if a scene exists | CSS filters stacked to fake it |

## Technologies

```yaml
id: tech.css
name: CSS (transitions, keyframes, scroll-driven animations, @starting-style)
kind: technology
category: native
use_for: State feedback, entrances, disclosure, scroll-linked progress where supported, ambient light and gradient effects.
when_to_use: Default for any effect or motion expressible declaratively on transform, opacity, color, clip-path or filter.
when_not_to_use: Physics, gesture-driven values, orchestrated timelines with many dependencies, or 3D scenes.
requires_dependency: false
packages: []
cost: none
fallback: Static final state via prefers-reduced-motion and @supports guards.
accessibility: Wrap motion in prefers-reduced-motion no-preference; never hide content in the initial keyframe without a no-JS path.
responsive: Media queries for hover/pointer/width; disable heavy effects under pointer coarse.
lifecycle: Declarative; infinite animations must pause via animation-play-state when off-screen.
```

```yaml
id: tech.native-js
name: Native JS (IntersectionObserver, requestAnimationFrame, Pointer Events)
kind: technology
category: native
use_for: Triggering reveals once, observing active sections, pointer-driven values, gesture handling.
when_to_use: When CSS needs a trigger or a pointer value; when a rAF loop is bounded and visibility-gated.
when_not_to_use: Replicating what CSS or a present library already does; unthrottled scroll handlers.
requires_dependency: false
packages: []
cost: low
fallback: Content visible by default; enhancement class added only after JS runs.
accessibility: Keyboard equivalents for every pointer gesture; respect reduced motion in JS via matchMedia.
responsive: Separate touch and mouse paths through pointer events and pointerType.
lifecycle: Disconnect observers, cancel rAF and remove listeners on unmount or when hidden.
```

```yaml
id: tech.waapi
name: Web Animations API
kind: technology
category: native
use_for: Imperative, interruptible animations, FLIP transitions, sequences, reading animation state.
when_to_use: Motion that must start, reverse or be cancelled from code without a library.
when_not_to_use: Long choreographed timelines with scroll scrubbing across many elements (GSAP is clearer there).
requires_dependency: false
packages: []
cost: low
fallback: Instant state change.
accessibility: Check prefers-reduced-motion before calling animate; keep focus stable during transitions.
responsive: Durations may shorten on small viewports.
lifecycle: Cancel running animations on state change to avoid stacking; await finished before cleanup.
```

```yaml
id: tech.view-transitions
name: View Transitions API
kind: technology
category: native
use_for: Shared-element continuity, list to detail, cross-page continuity, layout changes.
when_to_use: Continuity between two DOM states or documents as progressive enhancement.
when_not_to_use: Browsers without support as a hard requirement; continuous or scrubbed motion; very large DOM swaps where snapshots cost too much.
requires_dependency: false
packages: []
cost: low
fallback: Instant swap or crossfade when document.startViewTransition is unavailable.
accessibility: Disable or reduce to crossfade under prefers-reduced-motion; move focus to the new primary heading.
responsive: Keep shared elements few on mobile.
lifecycle: Unique view-transition-name per element per transition; remove names after the transition.
```

```yaml
id: tech.motion
name: Motion (Motion One / Framer Motion)
kind: technology
category: library
use_for: React/Vue component transitions, layout and shared-layout animation, gestures, springs, scroll-linked values.
when_to_use: The project already uses it, or a component framework needs layout animation and springs across many components.
when_not_to_use: A few hovers or fades; projects without a component framework; adding it next to GSAP for the same job.
requires_dependency: true
packages: [motion, framer-motion]
cost: medium
fallback: CSS transitions and instant layout changes.
accessibility: Use its reduced-motion hook or config globally.
responsive: Disable drag/gesture physics on coarse pointers where it harms scrolling.
lifecycle: Components unmount animations automatically; stop manual controls on unmount.
```

```yaml
id: tech.gsap
name: GSAP (with ScrollTrigger)
kind: technology
category: library
use_for: Complex timelines, scroll choreography with pinning and scrubbing, SVG morph, orchestrated storytelling.
when_to_use: Multi-step, scroll-scrubbed or tightly sequenced narratives that native tools cannot express cleanly.
when_not_to_use: Simple reveals, hovers, UI state transitions, dashboards; alongside another animation library for the same effects.
requires_dependency: true
packages: [gsap]
cost: medium
fallback: Static stacked sections with IntersectionObserver reveals.
accessibility: gsap.matchMedia with prefers-reduced-motion; pinned sections must remain readable and keyboard scrollable.
responsive: Use matchMedia to simplify or disable pinning on mobile.
lifecycle: Kill timelines and ScrollTriggers on unmount; refresh after layout changes.
```

```yaml
id: tech.rive
name: Rive
kind: technology
category: graphics
use_for: Interactive vector animation with state machines, animated icons and characters that react to input.
when_to_use: A designer-built interactive asset with states exists or is planned.
when_not_to_use: Static or linear illustrations; decoration without interaction; no asset pipeline.
requires_dependency: true
packages: ["@rive-app/canvas", "@rive-app/react-canvas", "@rive-app/webgl2"]
cost: medium
fallback: Static poster frame (SVG/PNG) with the same meaning.
accessibility: Provide text alternative; controls must be real buttons; pause option for looping content.
responsive: Canvas sizing to container and devicePixelRatio; lower resolution on low-power devices.
lifecycle: Pause when off-screen; cleanup instance on unmount.
```

```yaml
id: tech.lottie
name: Lottie
kind: technology
category: graphics
use_for: Playing designer-exported After Effects animations (illustrations, onboarding loops, success moments).
when_to_use: A finished Lottie/dotLottie asset exists and playback without complex input is enough.
when_not_to_use: UI state transitions, icons that CSS can animate, interactive state machines (prefer Rive), heavy files over roughly 200 KB.
requires_dependency: true
packages: [lottie-web, "@lottiefiles/dotlottie-web", lottie-react]
cost: medium
fallback: Static SVG/PNG of the key frame.
accessibility: Decorative animations aria-hidden; meaningful ones need text; honor reduced motion by showing the final frame.
responsive: Use SVG renderer for crispness, canvas renderer for many layers.
lifecycle: Destroy animation instance on unmount; lazy-load the JSON.
```

```yaml
id: tech.svg
name: SVG (inline, SMIL-free, CSS/WAAPI animated)
kind: technology
category: native
use_for: Icons, diagrams, line illustrations, path drawing, masks, simple morphs between compatible paths.
when_to_use: Resolution-independent vector graphics that need styling, accessibility or light animation.
when_not_to_use: Thousands of animated nodes (use Canvas), photographic content, complex 3D.
requires_dependency: false
packages: []
cost: low
fallback: Same SVG without animation.
accessibility: role="img" with title/desc for meaningful graphics; aria-hidden for decoration.
responsive: viewBox scaling; simplify detail at small sizes.
lifecycle: Animated filters inside SVG are expensive; keep them static.
```

```yaml
id: tech.canvas
name: Canvas 2D
kind: technology
category: native
use_for: Particles, procedural patterns, data-heavy visualizations, image processing, generative backgrounds.
when_to_use: Many drawn elements or per-frame drawing where DOM/SVG would be too heavy.
when_not_to_use: Text-heavy or interactive UI that needs semantics; small counts of shapes that SVG handles.
requires_dependency: false
packages: []
cost: medium
fallback: Static image or CSS gradient with the same composition.
accessibility: Canvas is opaque to assistive tech; provide equivalent text/data; aria-hidden when decorative.
responsive: Scale with devicePixelRatio capped at 2; reduce element count on small or low-power devices.
lifecycle: Stop the render loop when hidden (IntersectionObserver, visibilitychange); release references on unmount.
```

```yaml
id: tech.threejs
name: Three.js
kind: technology
category: graphics
use_for: 3D product viewers, spatial scenes, 3D sequences, camera motion.
when_to_use: Real 3D content (models, depth, lighting) is central to understanding the product and assets exist.
when_not_to_use: Fake depth achievable with layered 2D, decorative hero backgrounds without meaning, enterprise/app UI.
requires_dependency: true
packages: [three, "@react-three/fiber"]
cost: high
fallback: Pre-rendered image sequence or poster render.
accessibility: Equivalent textual product information; keyboard controls for rotate/zoom; pause/stop control.
responsive: Lower pixel ratio, fewer lights and simpler materials on mobile; static poster under save-data.
lifecycle: Dispose geometries, materials, textures and renderer on unmount; pause the loop off-screen.
```

```yaml
id: tech.webgl
name: WebGL (raw or thin wrappers such as OGL/regl)
kind: technology
category: graphics
use_for: Fragment-shader effects, GPU particles, distortion, liquid and noise fields, custom rendering pipelines.
when_to_use: A small, purposeful shader effect that CSS cannot achieve, with a fallback.
when_not_to_use: Effects CSS gradients/filters approximate well; text rendering; apps where GPU contention hurts UI.
requires_dependency: false
packages: [ogl, regl, pixi.js]
cost: high
fallback: CSS gradient or static image with the same color story.
accessibility: Decorative canvases aria-hidden; no flashing above three per second; pause control for motion.
responsive: Reduce resolution (render at 0.5-0.75 scale) and complexity on mobile; disable on low-power.
lifecycle: Handle context loss; delete buffers/programs on teardown; stop the loop when hidden.
```

`requires_dependency: false` on `tech.webgl` refers to the raw API; its listed wrappers are dependencies and follow the same authorization rule.
