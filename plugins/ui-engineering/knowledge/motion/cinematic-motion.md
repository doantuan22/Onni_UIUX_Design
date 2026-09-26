# M5 — Cinematic and immersive motion

Scenes, 3D, shaders and physics. M5 is allowed only when all of these hold:

1. The chosen style's `motion_ceiling` is `M5` and visual intensity is 4 or higher.
2. The content (3D assets, video, product renders) exists and explains the product better than a static alternative.
3. A static or reduced version with the same information exists, and it is what mobile, low-power, `save-data` and reduced-motion users receive.
4. The page budget allows it: one M5 region per page. See [performance-budget.md](../../skills/frontend-implementation/performance-budget.md).
5. The technology is authorized (most M5 entries need a dependency). Otherwise degrade to M4.

Graphics engineering details (lifecycles, context loss, fallbacks) are in [advanced graphics](../domains/graphics/techniques.md).

```yaml
id: motion.m5-cinematic-hero
name: Cinematic hero
kind: motion
category: cinematic
tier: M5
purpose: Open the page with a single, memorable product or brand scene.
serves: [brand-expression, storytelling]
trigger: Page load, then scroll.
behavior: Media-led scene with timed light/product reveal, handing off to scroll.
duration: motion-cinematic (700-1500ms) initial; then scroll-linked
easing: cubic-bezier(0.16, 1, 0.3, 1)
spring: none
entrance: Content readable within ~1s; scene continues behind.
exit: Scrolls away normally.
interruption: Any scroll or input completes the intro instantly.
responsive: Poster image and simple fade on mobile.
reduced_motion: Static poster with headline.
performance:
  cost: high
  notes: LCP must be the poster or headline, not the video/canvas.
technology:
  preferred: [tech.css, tech.native-js]
  alternatives: [tech.gsap, tech.threejs]
intensity: high
contexts: [marketing]
avoid_when: Apps, repeat-visit tools, weak media.
examples: Product emerging from darkness as light sweeps across it.
```

```yaml
id: motion.m5-3d-sequence
name: 3D sequence
kind: motion
category: cinematic
tier: M5
purpose: Show a product's form and parts in 3D as the story progresses.
serves: [storytelling]
trigger: Scroll within a pinned section.
behavior: 3D model or pre-rendered image sequence rotates or explodes as scroll scrubs.
duration: Scroll-linked
easing: linear scrub
spring: none
entrance: Model visible as poster first.
exit: Releases to next section.
interruption: Scrubs backward.
responsive: Short video or static exploded view on mobile.
reduced_motion: Static labelled images.
performance:
  cost: very-high
  notes: Image sequences need preloading budgets; real-time 3D needs dispose/pause discipline.
technology:
  preferred: [tech.canvas, tech.threejs]
  alternatives: [tech.gsap]
intensity: high
contexts: [marketing]
avoid_when: No real 3D assets; low-end audiences.
examples: Headphones exploding into components while scrolling.
```

```yaml
id: motion.m5-camera-motion
name: Camera motion
kind: motion
category: cinematic
tier: M5
purpose: Move a virtual camera through a scene to guide attention.
serves: [storytelling, orientation]
trigger: Scroll or chapter navigation.
behavior: Camera dolly/orbit between framed viewpoints.
duration: Scroll-linked or motion-cinematic per move
easing: ease-in-out
spring: none
entrance: From an establishing view.
exit: Settles on the final framing.
interruption: Input re-targets smoothly.
responsive: Fixed framings on mobile.
reduced_motion: Cut between framings.
performance:
  cost: very-high
  notes: Real-time rendering; cap pixel ratio.
technology:
  preferred: [tech.threejs]
  alternatives: [tech.webgl]
intensity: high
contexts: [marketing]
avoid_when: 2D content; vestibular-sensitive audiences as the primary users.
examples: Moving through a spatial product environment.
```

```yaml
id: motion.m5-webgl-transition
name: WebGL transition
kind: motion
category: cinematic
tier: M5
purpose: Transition between images or scenes with a custom shader effect.
serves: [continuity, brand-expression]
trigger: Navigation between projects/slides.
behavior: Displacement, dissolve or distortion shader blends image A to B.
duration: motion-expressive (500-900ms)
easing: ease-in-out
spring: none
entrance: n/a
exit: n/a
interruption: Next input finishes current transition instantly.
responsive: Crossfade on mobile.
reduced_motion: Crossfade or cut.
performance:
  cost: high
  notes: Keep textures sized to display; dispose textures.
technology:
  preferred: [tech.webgl]
  alternatives: [tech.threejs]
intensity: high
contexts: [marketing]
avoid_when: UI state changes; text-bearing images.
examples: Portfolio slides dissolving with a liquid distortion.
```

```yaml
id: motion.m5-particle-interaction
name: Particle interaction
kind: motion
category: cinematic
tier: M5
purpose: Visualize a concept (data flow, energy, network) that responds to the user.
serves: [storytelling, brand-expression]
trigger: Pointer or scroll.
behavior: Particles form shapes or flows and react to input.
duration: Continuous while visible
easing: Physics-based
spring: n/a
entrance: Forms from scattered state.
exit: Pauses off-screen.
interruption: Input changes forces.
responsive: Static illustration on mobile.
reduced_motion: Static illustration.
performance:
  cost: very-high
  notes: Device-scaled particle counts; pause when hidden.
technology:
  preferred: [tech.canvas]
  alternatives: [tech.webgl, tech.threejs]
intensity: high
contexts: [marketing]
avoid_when: Particles do not represent anything; behind text.
examples: Network nodes forming the product's architecture.
```

```yaml
id: motion.m5-cursor-reactive-scene
name: Cursor-reactive scene
kind: motion
category: cinematic
tier: M5
purpose: Make a hero scene respond to the pointer to invite exploration.
serves: [delight, brand-expression]
trigger: Pointer movement over the scene.
behavior: Light, tilt or elements follow the pointer with damping.
duration: Continuous, damped 200-400ms response
easing: Damped interpolation
spring: gentle
entrance: Neutral pose.
exit: Returns to neutral on pointer leave.
interruption: Follows pointer.
responsive: Off on touch; optional gyroscope only with permission and restraint.
reduced_motion: Static pose.
performance:
  cost: medium
  notes: Update CSS variables or uniforms in rAF; no layout reads.
technology:
  preferred: [tech.css, tech.native-js]
  alternatives: [tech.threejs, tech.webgl]
intensity: medium
contexts: [marketing]
avoid_when: Content-heavy pages; precise pointer tasks.
examples: Product tilts slightly toward the cursor.
```

```yaml
id: motion.m5-physics-interaction
name: Physics interaction
kind: motion
category: cinematic
tier: M5
purpose: Let users play with objects that obey physical rules to convey tactility or fun.
serves: [delight, brand-expression]
trigger: Drag, throw, pointer collision.
behavior: Objects respond with gravity, collisions, springs.
duration: Continuous while interacting
easing: Physics simulation
spring: tuned per object
entrance: Objects settle into place.
exit: Sleep when at rest.
interruption: Input applies forces.
responsive: Simplified or disabled on mobile.
reduced_motion: Static arrangement.
performance:
  cost: high
  notes: Physics engines add weight; stop simulation when at rest or hidden.
technology:
  preferred: [tech.canvas]
  alternatives: [tech.motion, tech.threejs]
intensity: high
contexts: [marketing]
avoid_when: Professional tools; serious brands.
examples: Tags that can be tossed around on a creative studio page.
```

```yaml
id: motion.m5-svg-morph
name: SVG morph
kind: motion
category: cinematic
tier: M5
purpose: Transform one illustrated shape into another to explain change.
serves: [storytelling, continuity]
trigger: Step change or scroll.
behavior: Path interpolates between shapes.
duration: motion-expressive (400-800ms)
easing: ease-in-out
spring: none
entrance: From source shape.
exit: n/a
interruption: Re-targets or jumps to end.
responsive: Same; simpler shapes on small screens.
reduced_motion: Crossfade between shapes.
performance:
  cost: medium
  notes: Compatible paths animate natively; incompatible ones need a morph library.
technology:
  preferred: [tech.svg, tech.waapi]
  alternatives: [tech.gsap]
intensity: medium
contexts: [marketing, content]
avoid_when: Icons (use M1 icon transition).
examples: Logo mark morphing into a product diagram.
```

```yaml
id: motion.m5-interactive-shader
name: Interactive shader
kind: motion
category: cinematic
tier: M5
purpose: Signature procedural visual that responds to pointer or scroll.
serves: [brand-expression]
trigger: Continuous plus pointer/scroll uniforms.
behavior: Fragment shader animates noise, light or liquid fields.
duration: Continuous while visible
easing: Shader-defined
spring: n/a
entrance: Fades in over the poster after load.
exit: Pauses off-screen.
interruption: Input modifies uniforms.
responsive: Poster on mobile and low-power.
reduced_motion: Static poster.
performance:
  cost: very-high
  notes: Render at reduced resolution; handle context loss.
technology:
  preferred: [tech.webgl]
  alternatives: [tech.threejs]
intensity: high
contexts: [marketing]
avoid_when: Behind text; as the only evidence of product quality.
examples: Liquid light field reacting to the cursor in a hero.
```

```yaml
id: motion.m5-spatial-navigation
name: Spatial navigation
kind: motion
category: cinematic
tier: M5
purpose: Navigate content arranged in space (zooming canvas, depth layers).
serves: [orientation, continuity]
trigger: Navigation input.
behavior: Camera moves or zooms between regions of a large canvas.
duration: motion-normal to motion-expressive (300-600ms)
easing: ease-in-out
spring: critically-damped
entrance: From overview.
exit: Back to overview.
interruption: Input re-targets.
responsive: List navigation on mobile.
reduced_motion: Cut between regions.
performance:
  cost: high
  notes: Large transformed canvases; virtualize off-screen content.
technology:
  preferred: [tech.css, tech.native-js]
  alternatives: [tech.threejs, tech.motion]
intensity: high
contexts: [marketing, application]
avoid_when: Hierarchical content better served by pages.
examples: Zoomable project map in a portfolio or canvas tool.
```
