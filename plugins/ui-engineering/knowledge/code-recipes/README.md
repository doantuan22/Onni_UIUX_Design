# Code recipes (React + Tailwind, Next.js)

Real, type-checked components that turn a [design direction](../../skills/design-direction/signature-moves.md)
into code. Each recipe realizes one or more signature moves and replaces the matching
[default-banlist](../visual-language/anti-slop/default-banlist.md) signals that `map_ui_structure` reports.
The registry is [index.json](index.json); `suggest_recipes` ranks recipes for every section of a UI map.

| Kind | Recipes |
|---|---|
| Tokens | [brand-derived theme](react-tailwind/tokens/brand-theme.css) (apply first) |
| Sections | [asymmetric hero](react-tailwind/sections/hero-asymmetric-split.tsx), [bento features](react-tailwind/sections/bento-features.tsx), [editorial index](react-tailwind/sections/editorial-index.tsx), [sticky narrative](react-tailwind/sections/sticky-narrative.tsx), [pricing emphasis](react-tailwind/sections/pricing-emphasis.tsx), [testimonial spotlight](react-tailwind/sections/testimonial-spotlight.tsx), [logo marquee](react-tailwind/sections/logo-marquee.tsx), [FAQ split](react-tailwind/sections/faq-split.tsx), [CTA band](react-tailwind/sections/cta-band.tsx), [stats strip](react-tailwind/sections/stats-strip.tsx), [dashboard focus](react-tailwind/sections/dashboard-focus.tsx) |
| Motion | [hero entrance](react-tailwind/motion/hero-entrance.tsx) (Motion), [scroll product reveal](react-tailwind/motion/scroll-product-reveal.tsx) (Motion or CSS), [pinned steps](react-tailwind/motion/pinned-steps-gsap.tsx) (GSAP), [shared-layout cards](react-tailwind/motion/shared-layout-cards.tsx) (Motion), [tactile button](react-tailwind/motion/tactile-button.tsx) (CSS) |
| Surfaces | [grain / dot-grid texture](react-tailwind/surfaces/grain-texture.tsx) |

## How to use a recipe

1. Run `map_ui_structure`, then `suggest_recipes` with the map (pass `allow_motion_library` and the project's
   dependencies from `orchestrate_ui` / `analyze_repository`). Pick recipes that serve the direction's signature
   moves; a suggestion is a candidate, not an instruction.
2. Apply [brand-theme.css](react-tailwind/tokens/brand-theme.css) (or its Tailwind v3 equivalent) with the
   project's existing primary hue, fonts and radii.
3. Copy the recipe into the project's component folder (e.g. `src/components/sections/`), following its naming and
   file conventions. Reuse the project's `Button`, `Link` and icon components instead of the recipe's plain elements
   when they exist; pass `next/link` and `next/image` in Next.js.
4. Feed the existing content through props — headings, copy, actions, plans, quotes, images — unchanged. Never drop
   an item to fit a layout; choose another recipe instead.
5. Motion recipes marked `client` need `"use client"` (App Router) and one sanctioned library (`motion` or `gsap`).
   Without the library, use the recipe's `css_fallback`; tell the user the install command instead of installing.
6. Re-run `map_ui_structure` and `diff_ui_maps`: content preserved, sections re-composed, banlist signals resolved.

## Guarantees and limits

- Every file type-checks with `tsc --strict` (React 19, Next.js 15, Motion 12, GSAP 3) and the section recipes were
  rendered in a Next.js 15 + Tailwind CSS 4 build at 390 and 1440 px without horizontal overflow.
- Sections set `w-full` so they keep their width inside `flex flex-col` page wrappers.
- Tailwind classes work in v4; for v3, move the `@theme` tokens into `tailwind.config` (`theme.extend`).
- All motion has a reduced-motion path; the only infinite animation (marquee) pauses on hover/focus and stops
  under reduced motion.
- Recipes are starting points in the product's own brand, not templates to paste unchanged: adapt spacing, copy
  length and components to the design direction.
