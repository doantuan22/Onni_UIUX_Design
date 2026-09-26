# Advanced graphics

Two layers of knowledge:

- **Technologies** (SVG, Canvas, WebGL, Three.js, Rive, Lottie) are defined once in the [technology resolver](../../../skills/frontend-implementation/technology-resolver.md). Each one has when to use, when not to use, cost, fallback, accessibility, responsive strategy and lifecycle.
- **Techniques** below (shaders, particle systems, procedural graphics, interactive illustration) are built with those technologies. They inherit the technology rules and add their own.

## Engineering rules for every advanced graphic

1. **Poster first.** Render a static image or CSS equivalent with the same meaning before any canvas/WebGL loads. The poster is the LCP candidate, the reduced-motion state and the error fallback.
2. **Visibility-gated loop.** Start render loops only when visible (IntersectionObserver), stop on `visibilitychange` hidden, and never run two continuous loops on one page.
3. **Resolution budget.** Cap `devicePixelRatio` at 2 (1–1.5 on mobile). Render shaders at 0.5–0.75 scale when full resolution is not visible.
4. **Lifecycle.** Dispose GPU resources on unmount, handle `webglcontextlost`/`restored`, and cancel rAF and observers.
5. **Degradation.** Low-power, `save-data`, reduced motion and failure all lead to the poster (see [responsive-motion](../../motion/responsive-motion.md)).
6. **Semantics.** Canvas content is invisible to assistive tech. Meaningful graphics need equivalent text or data; decorative graphics are `aria-hidden`.
7. **Dependency.** Libraries follow the technology resolver's authorization rule; nothing is installed automatically.

```yaml
id: graphics.shader
name: Shader graphics
kind: graphics
category: technique
purpose: Procedural light, noise, liquid and distortion fields rendered on the GPU.
when_to_use: One signature visual that CSS gradients, filters and SVG cannot approximate, on a marketing page with visual intensity 4 or higher.
when_not_to_use: Behind text; in application UI; when a static gradient conveys the same mood; without a poster fallback.
technology: [tech.webgl, tech.threejs]
cost: very-high
fallback: Static poster exported from the shader or a CSS gradient with the same palette.
accessibility: aria-hidden; no luminance flashing above 3 per second; pause control if it runs continuously.
responsive: Poster on mobile and low-power; reduced resolution on desktop.
lifecycle: Compile once; handle context loss; delete programs/buffers; stop when hidden.
```

```yaml
id: graphics.particle-system
name: Particle system
kind: graphics
category: technique
purpose: Many small elements that together visualize data, flow, energy or a network.
when_to_use: Particles represent something real (data points, network nodes, physical material) and help explain it.
when_not_to_use: Floating dots as generic tech decoration; behind reading content; dashboards.
technology: [tech.canvas, tech.webgl, tech.threejs]
cost: high
fallback: Static illustration of the formed state.
accessibility: aria-hidden unless it encodes data (then provide the data in text); pause for continuous motion.
responsive: Scale particle count by device (hundreds on mobile, low thousands on desktop); off on low-power.
lifecycle: Object pooling; stop simulation at rest or when hidden.
```

```yaml
id: graphics.procedural
name: Procedural graphics
kind: graphics
category: technique
purpose: Generate patterns, textures or illustrations from rules (noise, grids, L-systems) instead of assets.
when_to_use: Variation or data-driven visuals are the point (generative brand patterns, per-user avatars, data art).
when_not_to_use: A single static asset would do; generation cost on each load harms performance.
technology: [tech.svg, tech.canvas, tech.webgl]
cost: medium
fallback: Pre-generated asset.
accessibility: Decorative unless meaningful; deterministic seeds so content is stable for screenshots and tests.
responsive: Generate at display size; cache results.
lifecycle: Generate once per size change (debounced resize); no per-frame regeneration unless animated by design.
```

```yaml
id: graphics.interactive-illustration
name: Interactive illustration
kind: graphics
category: technique
purpose: Illustrations that respond to input or state to explain or delight (onboarding characters, animated diagrams, stateful icons).
when_to_use: The illustration's reaction teaches something or confirms state, and a designer asset pipeline exists.
when_not_to_use: Static illustrations suffice; no one maintains the source files; heavy runtime for a small detail.
technology: [tech.rive, tech.lottie, tech.svg]
cost: medium
fallback: Static frame with the same meaning.
accessibility: Text alternative; controls are real buttons; honor reduced motion by showing the key frame.
responsive: Scale vector assets; simplify state machines on mobile if needed.
lifecycle: Lazy-load assets; pause off-screen; clean up instances on unmount.
```
