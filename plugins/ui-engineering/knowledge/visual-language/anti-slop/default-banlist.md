# Default banlist

These are the defaults that make interfaces look machine-made. They are **banned as defaults**, not as
styles: an item may stay only when `DESIGN-DIRECTION.md` records a product, brand or task reason for it
(`banlist_exceptions`). An existing brand choice (for example, a purple brand) is a reason by itself.
Clusters matter more than single items — see [AI tell density](../ai-tell-density.md).

Use this list in step 2 of the [Elevate procedure](../../../workflows/ambition-levels.md#elevate-procedure)
to diagnose the current UI, and again when reviewing the result.

## Composition

| Default | Typical code signature | Replace with |
|---|---|---|
| Centered hero: badge, huge headline, subline, two buttons, nothing else | `text-center` hero, `flex justify-center gap-4` twin CTAs | Asymmetric split with a real product visual, or an editorial headline with proof inline |
| Three (or six) equal icon cards for features | `grid md:grid-cols-3` of identical `rounded-xl border p-6` cards with an icon in a circle | Bento with real hierarchy, editorial index, or a feature list with one expanded feature |
| Every section centered with the same heading block | repeated `text-center max-w-2xl mx-auto` + `py-24` | Vary alignment and width by section role; left-aligned reading for most sections |
| Uniform vertical rhythm | `py-20`/`py-24` on every section | A spacing scale by role: tight for related sections, generous before key moments, full-bleed breaks |
| Generic "Trusted by" grey logo row + three testimonial cards | `grayscale opacity-50` logo row, `grid-cols-3` quotes | Proof as structure: one strong quote with a face and metric, logos woven near the claim they support |
| Stats row of round numbers | `10k+`, `99.9%`, `24/7` with no source | Real metrics only; otherwise remove |

## Surfaces and color

| Default | Typical code signature | Replace with |
|---|---|---|
| Purple/indigo → pink/blue gradients on hero, buttons and text | `bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500`, `bg-clip-text text-transparent` | Brand hue steps; one accent reserved for the primary action |
| Blurred gradient blobs and orbs behind the hero | `absolute blur-3xl rounded-full bg-purple-500/30` | Texture (grain, grid), a real product visual, or a tinted full-bleed band |
| Glassmorphism on everything | `backdrop-blur bg-white/10 border-white/20` on cards and nav | Glass only on overlays over rich content; otherwise solid layered surfaces |
| Same radius and shadow on every element | `rounded-2xl shadow-lg` / `shadow-xl` everywhere | A surface model: hairline system or a 2–3 step elevation scale applied by role; radii by component size |
| Dark mode with neon glow | `shadow-[0_0_30px] shadow-cyan-500/50`, glowing borders | Contrast through surface steps and type weight; glow only for a specific live/active state |

## Typography

| Default | Typical code signature | Replace with |
|---|---|---|
| One family, one weight jump | Inter/system only, `font-bold` headings, `text-gray-600` body | Display contrast, a companion display or mono family within the brand character |
| Gradient text on headings | `bg-clip-text text-transparent` on multiple headings | Solid ink; emphasis through weight, size or a single highlighted word |
| Low-contrast grey body text | `text-gray-400`/`text-slate-500` on white | ≥ 4.5:1 body text; hierarchy through size and weight, not paleness |
| Generic hype copy | "Unlock the power of…", "Supercharge your…", "Seamless", "Revolutionize" | Keep the existing copy (Elevate does not rewrite meaning); flag hype copy for the user |

## Icons and imagery

| Default | Typical code signature | Replace with |
|---|---|---|
| Emoji as icons, ✨ sprinkles | `✨`, `🚀`, `⚡` in headings and cards | The project's icon set at a consistent size and stroke; or no icon |
| Icon in a tinted circle above every card title | `rounded-full bg-primary/10 p-3` wrapper | Icons only where they aid scanning; inline with the label |
| Abstract 3D shapes or stock illustrations unrelated to the product | decorative `img` with generic alt | Real product screenshots, real photos, or typographic compositions |

## Motion

| Default | Typical code signature | Replace with |
|---|---|---|
| Fade-up on every element | `whileInView={{ opacity: 1, y: 0 }}` on all blocks, AOS on everything | One choreographed entrance per view; scroll motion only where it explains something |
| Hover scale on every card | `hover:scale-105 transition` everywhere | Hover that reveals information or affordance (border, shadow step, arrow shift) |
| Infinite decorative animations | `animate-pulse`/`animate-bounce` on static content | Motion tied to state changes; static when idle |
| No reduced-motion path | animations without `motion-reduce:` or `useReducedMotion` | Every animation has a reduced or static equivalent |

## Review rule

Count unexplained items per page. Zero or one: fine. Two or three in one region: rework that region.
Four or more: the page has not been elevated — return to the composition plan.
