# Ambition Levels: Refine, Elevate, Reimagine

The change budget ([preservation-rules.md](preservation-rules.md)) says **what may not be touched**. The
ambition level says **how far the visual result must move**. A request to upgrade an existing interface
that ends as spacing tweaks has failed just as surely as one that deletes a page.

| Level | Budget | What moves | What stays | Typical request |
|---|---|---|---|---|
| **Refine** | L1 | Spacing, alignment, states, focus, contrast, responsive fixes, token alignment | Everything visible: composition, type scale, surfaces, motion | "fix the spacing", "keep the current look", "chỉ tinh chỉnh", a11y/responsive fixes, single components |
| **Elevate** *(default for upgrade requests)* | L2 | Page composition, section layout and rhythm, visual hierarchy, type scale and pairing within the brand family, surfaces and depth, imagery treatment, motion and micro-interaction, component styling | App shell (header/sidebar/nav placement), navigation model, routes, information architecture, content and copy meaning, primary actions, data and API contracts, brand hues and logo | "nâng cấp giao diện", "làm đẹp", "modernize", "make it premium / less generic", "upgrade the landing page" |
| **Reimagine** | L3 | Anything the user explicitly unlocked (palette, brand, navigation, architecture, rebuild) | Anything not explicitly unlocked | "redesign toàn bộ", "full redesign", "đổi sang tông…", greenfield builds |

The orchestrator resolves the level (`orchestrate_ui` → `ambition`, `protected_properties.page_composition`):

- Greenfield or explicit L3 permission → `reimagine`; unknown UI state → `refine`.
- Local scope (one button, form, card) or conservative phrasing ("keep the current look", "giữ nguyên bố
  cục", "minimal changes", "chỉ tinh chỉnh") → `refine`. Conservative phrasing always wins.
- Upgrade phrasing ("modernize", "làm đẹp", "nâng cấp", "upgrade", "premium", "make it
  professional", "less generic") → `elevate`.
- A structured `explicit_permissions.ambition` overrides the text, but `reimagine` still requires explicit
  L3 permission (otherwise it falls back to `elevate`).

Upgrade phrasing never grants L3: the palette stays on the existing hues, and branding, navigation and
architecture stay protected. Elevate is about composition and craft, not about a new identity.

## Elevate contract

**Preserve (invariants, checked at review):**

1. Every route, page and in-page anchor still exists and is reachable from the same navigation.
2. Content inventory: every heading, paragraph, list, figure, form field and primary/secondary action is
   still present. Copy may be tightened only when the user asked for copy work; meaning never changes.
3. Data bindings, API calls, state management, auth and form submission logic are untouched.
4. Brand hues and logo. Derived tints, shades, neutrals and surface layers built from the existing hues are
   allowed; a new hue family is not.
5. App shell placement: header, sidebar and footer keep their position and role.

**Evolve (expected, not optional):**

1. **Composition**: each key page gets a composition chosen for its content, not the category template
   (see [Web Pattern Library](../knowledge/web-patterns/README.md)). Equal-card grids, centered-everything
   stacks and uniform section padding are replaced where they flatten hierarchy.
2. **Hierarchy and type**: one clear focal point per viewport; a deliberate type scale with real contrast
   between display, heading, body and meta text ([Typography](../skills/typography/README.md)). The brand
   family is kept; a display or mono companion may be added when the direction calls for it.
3. **Surfaces and depth**: one coherent surface model (flat + hairline borders, layered tints, or soft
   elevation) instead of the same shadow on everything
   ([surface-profile.md](../knowledge/visual-language/surface-profile.md)).
4. **Motion**: purposeful entrance, feedback and scroll choreography within the
   [motion budget](../knowledge/motion/README.md), with a reduced-motion equivalent.
5. **Signature moves**: at least three committed moves from
   [signature-moves.md](../skills/design-direction/signature-moves.md) that make the product
   recognizable, recorded in `DESIGN-DIRECTION.md`.

## Elevate procedure

1. **Map before touching.** Run `analyze_repository` and `analyze_existing_ui`, then write
   `CURRENT-UX-MAP.md`: routes → pages → sections (in order) → components, with each section's role
   (hero, proof, feature, workflow, pricing, FAQ, CTA, data, form…) and its content inventory. Capture
   *before* screenshots at 375, 768 and 1440 px when a runtime is available (`run_runtime`).
2. **Diagnose.** For each key page list what makes it generic or weak: check it against the
   [default banlist](../knowledge/visual-language/anti-slop/default-banlist.md) and the
   [AI tell density](../knowledge/visual-language/ai-tell-density.md) scale. Name the problem in terms of
   hierarchy, rhythm, composition, type, surfaces and motion — not "looks old".
3. **Commit to a direction.** Fill `DESIGN-DIRECTION.md` ([template](../templates/DESIGN-DIRECTION.md)):
   ambition, a one-sentence thesis, reference DNA (via
   [Design Inspiration](../skills/design-inspiration/README.md)), the three or more signature moves, what
   stays, and any banlist item kept with its reason.
4. **Plan the re-composition.** Per key page, a before → after table: section, current pattern, new
   pattern, content kept, reason. Sections may be re-composed and, when the reading order improves the
   task, reordered; no section is deleted.
5. **Build in layers.** Tokens first (derived color steps, type scale, spacing rhythm, radii, shadows,
   motion durations/easings), then section compositions, then motion and micro-interaction. Reuse the
   project's components and extend their variants; do not fork a parallel component set.
6. **Prove it.** Capture *after* screenshots at the same viewports, run the accessibility scan, and check
   the invariants above (routes, content inventory, data, brand hues). Review the before/after pair
   against the banlist and the direction; iterate at most twice on the weakest page.

Elevate is not done when the diff only touches spacing, colors of existing elements, or border radii. The
review asks: *would a user recognize the product, and would they notice that it got better at first
glance?* Both answers must be yes.

## Frontend stack focus

Recipes and implementation guidance prioritize the most used stacks:

- **React + Tailwind CSS** (Vite or similar): tokens in the Tailwind theme (`@theme` in v4, `theme.extend`
  in v3) or CSS variables consumed by it; compose with utility classes and `cva`/variant helpers when the
  project has them.
- **Next.js (App Router)**: fonts through `next/font`, images through `next/image`, animation components
  marked `"use client"` and kept as leaves so pages stay server components.

See the [React](../knowledge/frameworks/react.md) and [Next.js](../knowledge/frameworks/nextjs.md) framework packs; other
stacks follow their framework pack in [knowledge/frameworks/](../knowledge/frameworks/) with native CSS equivalents.

## Motion libraries

Under Elevate and Reimagine the orchestrator sets `allow_motion_library: true`. Pass it to
`resolve_technology` / `resolve_capabilities`. The resolver then sanctions **one** motion library when the
chosen motion has no native preferred option:

- **Motion** (`motion`, formerly Framer Motion; `framer-motion` if already installed) for React component
  enter/exit, layout and shared-element transitions, gestures and spring feedback.
- **GSAP** (`gsap` + ScrollTrigger) for scroll-scrubbed, pinned or multi-step timelines.

Rules: reuse a library the project already has; never add both; prefer CSS (transitions, keyframes,
`@starting-style`, scroll-driven animations, View Transitions) when it does the job; every animation has a
`prefers-reduced-motion` path (`useReducedMotion`, `MotionConfig reducedMotion="user"`, `gsap.matchMedia`).
The agent never installs packages itself: it adds the dependency to the plan, tells the user the exact
install command and why, and keeps a native fallback until the user installs it.
