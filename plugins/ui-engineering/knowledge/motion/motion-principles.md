# Motion principles and grammar

The shared grammar every motion decision follows. Two rules are non-negotiable:

> **Motion must have purpose.**
> **Premium does not mean more animation.**

## Purposes

Every motion serves at least one purpose; otherwise remove it. Catalog entries record purposes in `serves`.

| Purpose (`serves`) | Meaning | Example |
|---|---|---|
| `feedback` | Confirms the system received input | Button press, toggle, saved confirmation |
| `state-change` | Makes a change of state legible | Expand/collapse, loading → loaded, error near its field |
| `orientation` | Shows where something came from and went | Drawer slides from its trigger side |
| `continuity` | Keeps identity of an object across states/pages | Thumbnail becomes the detail image |
| `hierarchy` | Orders attention by arrival | Primary element arrives first; secondary follows |
| `attention` | Draws the eye to something that changed or needs action | New notification slides in once |
| `storytelling` | Explains a sequence or narrative | Scroll-linked product reveal |
| `delight` | Rewards a meaningful milestone | Celebration on completing onboarding |
| `brand-expression` | Carries brand character in a signature moment | One ambient light drift in the hero |

`delight` and `brand-expression` never justify motion on their own when the element is routine. "It looks nice" is not a purpose.

## Priority hierarchy

When motions compete for the same moment or budget, keep the higher one and cut the lower one:

```text
user feedback  >  state transition  >  navigation / orientation  >  storytelling  >  decorative / ambient
```

Feedback is never delayed by any other motion. Decorative motion stops while the user interacts.

## Motion tiers

| Tier | Scope | Catalog |
|---|---|---|
| primitive | Building blocks (fade, fade-up, slide, scale, clip, stagger, ambient drift) | [motion-vocabulary.md](motion-vocabulary.md) |
| M1 — Micro motion | Single control feedback | [microinteractions.md](microinteractions.md) |
| M2 — Component transition | A component changes state or appears | [spatial-motion.md](spatial-motion.md) |
| M3 — Layout transition | Elements move between layouts or views | [layout-motion.md](layout-motion.md) |
| M4 — Scroll choreography | Motion driven by scroll position | [scroll-motion.md](scroll-motion.md), [text-motion.md](text-motion.md) |
| M5 — Cinematic / immersive | Scenes, 3D, shaders, physics | [cinematic-motion.md](cinematic-motion.md) |

Tiers above the chosen style's `motion_ceiling` are not used. M5 needs visual intensity 4 or higher, desktop-capable audiences, and a static fallback.

## Duration scale

| Token | Range | Used for |
|---|---|---|
| `motion-micro` | 50–120ms | Press, focus, color/opacity feedback |
| `motion-fast` | 120–200ms | Hover, toggles, tooltips, dropdowns |
| `motion-normal` | 200–350ms | Modals, drawers, tabs, layout moves |
| `motion-expressive` | 350–700ms | Marketing reveals, shared-element hero moves |
| `motion-cinematic` | 700–1500ms or scroll-linked | Signature scenes only; never blocks input |

Larger distances and surfaces sit at the upper end of their range; exits run at about 70–80% of their entrance. Anything a user waits on longer than ~400ms before acting is `SLOW_INTERACTION`.

## Timing (by interaction type)

| Type | Duration range | Notes |
|---|---|---|
| Microinteraction (hover, press, focus, toggle) | 80–150ms | Press feedback can be 50–100ms; focus ring may be instant |
| Component transition (tabs, accordion, tooltip, dropdown) | 150–250ms | Scale with distance/size |
| Spatial transition (modal, drawer, sheet, page) | 200–350ms enter; exit ≈ 70–80% of enter | Larger surfaces take longer |
| Marketing entrance (section reveal) | 300–600ms | Stagger 40–80ms per item; total sequence ≤ ~800ms |
| Storytelling (scroll-linked) | tied to scroll, not time | Must be reversible and scrubbable |
| Text reveal (hero headline) | 400–900ms total | Content readable within ~1s |

Never use one global `transition: all 0.3s ease`. Transition specific properties and name durations as tokens.

## Easing

| Use | Easing |
|---|---|
| Entering / appearing | ease-out family, e.g., `cubic-bezier(0.2, 0, 0, 1)` or a stronger `cubic-bezier(0.16, 1, 0.3, 1)` for expressive |
| Exiting / dismissing | ease-in family, e.g., `cubic-bezier(0.4, 0, 1, 1)`, shorter duration |
| Moving on screen (A → B) | ease-in-out, e.g., `cubic-bezier(0.4, 0, 0.2, 1)` |
| Scroll-linked, progress, loaders | `linear` |
| Tactile/playful | spring (library spring if present, or CSS `linear()` approximation) with low overshoot |

Define 3–4 named easings and don't invent one per component.

### Spring characteristics

Springs suit direct manipulation and tactile styles. Describe them by feel, then map to the library's parameters:

| Feel | Damping ratio | Overshoot | Use |
|---|---|---|---|
| `critically-damped` | ~1.0 | none | Layout moves, drawers, most UI |
| `gentle` | ~0.8 | small | Cards, toggles in friendly products |
| `bouncy` | ~0.5–0.6 | visible | Playful celebrations only |

Serious products (finance, enterprise, health) use critically damped springs or easing curves only.

## Intensity budget

| Level | Meaning | Examples |
|---|---|---|
| `LOW` | Barely noticed; ≤ 150ms; small distance/opacity | Hover color, focus ring, press scale 0.98 |
| `MEDIUM` | Noticed but brief; ≤ 400ms; moderate distance | Section fade-up, tab content switch, drawer |
| `HIGH` | A deliberate moment; scroll-linked or multi-step; large area | Cinematic hero, sticky storytelling, product reveal |

Rules:

- A page has **at most one `HIGH` region** (two on long storytelling pages if separated by low sections). Never every section `HIGH`.
- If the hero is `HIGH`, body sections are `LOW`/`MEDIUM` and controls stay subtle.
- App/dashboard/form surfaces: `LOW` everywhere; `MEDIUM` only for spatial overlays and meaningful state transitions.
- Entrance animation on ordinary content is limited to the first appearance of a section, not each element, and never re-triggers on scroll up.

Record the budget per region:

```yaml
motion_budget:
  hero: high
  sections: low-medium
  controls: low
  navigation: low
  decorative_loop: none
```

The page-level point budget across motion, effects and interactions is in [performance-budget.md](../../skills/frontend-implementation/performance-budget.md).

## Direction and consistency

- One spatial model per product: overlays come from their trigger, navigation forward moves in one direction, back reverses it.
- Adjacent elements never move in competing directions at the same time.
- Equivalent components share the same duration and easing tokens.

## Anti-patterns

| Anti-pattern | Signal | Review code |
|---|---|---|
| Animate everything | Every element has entrance/hover motion; no calm region | `EVERYTHING_ANIMATED` |
| Excessive floating | Cards, blobs or icons bob or float continuously | `MOTION_FOR_DECORATION` |
| Excessive parallax | Parallax on several sections, text, or mobile | `UNJUSTIFIED_PARALLAX` |
| Long blocking animation | Intro or transition delays reading or input beyond ~400ms | `SLOW_INTERACTION` |
| Scroll hijacking without reason | Wheel/touch speed or direction overridden; forced snapping through content | `SCROLL_HIJACKING` |
| Multiple competing motion directions | Simultaneous movements in different directions | `COMPETING_MOTION_DIRECTIONS` |
| Inconsistent easing | Different curves/durations for equivalent components | `MOTION_STYLE_DRIFT` |
| Decorative animation hiding content | Content at opacity 0 until an animation or observer runs | `MOTION_WITHOUT_REDUCED_MODE` / `EXCESSIVE_ENTRANCE_ANIMATION` |
| Motion causing layout instability | Animated width/height/top/margin or late-loading motion causing shifts | `MOTION_LAYOUT_INSTABILITY` |

## Implementation strategy (order of preference)

1. **CSS transitions** on `transform`/`opacity`/`color` for state changes.
2. **CSS keyframes** for entrance/loading sequences.
3. **`IntersectionObserver`** to add a class once when a section enters the viewport (then unobserve).
4. **Native scroll-driven animation** (`animation-timeline: view()`/`scroll()`) inside `@supports`, with a static or IO-based fallback.
5. **View Transitions API** for spatial/page continuity as progressive enhancement.
6. **`requestAnimationFrame`** only for continuous, measured, scroll/pointer-linked effects that CSS cannot express; throttle and stop when off-screen.
7. **Existing project animation library** when present — use it consistently for the effects it already handles.
8. **New library** only with need + authorization + recorded justification. The full decision matrix is the [technology resolver](../../skills/frontend-implementation/technology-resolver.md).
