# Signature moves

A signature move is a deliberate, repeated design decision that makes an interface recognizable. Generic
interfaces have none: every section uses the category default. Elevate and Reimagine work commits to
**at least three** moves — normally one each from composition, typography and surface/motion — records them
in `DESIGN-DIRECTION.md`, and applies them consistently across the key pages.

Choose moves from the product's content and character, not from this list's order. Every move keeps the
[Elevate invariants](../../workflows/ambition-levels.md#elevate-contract): content, routes, data and brand
hues stay. Tailwind hints are starting points; translate them to the project's tokens and utilities.

## How to pick

1. Write the thesis: *"<Product> should feel <two adjectives> because <audience/task reason>."*
2. For each move, ask which content it serves. A bento grid needs items of unequal importance; an
   editorial index needs sequential content; a data-forward hero needs a real product view.
3. Reject a move that fights the brand (a brutalist grid for a calm healthcare portal) or the density
   (oversized display type on a dense admin console).
4. Apply each move to at least two places so it reads as a system, not a one-off decoration.

## Composition

| Move | Use when | Avoid when | Tailwind hint |
|---|---|---|---|
| **Asymmetric split** — 7/5 or 8/4 columns, text anchored left, product visual bleeding off the edge | A product with a strong visual (UI, device, photo) | No real visual to show | `grid lg:grid-cols-12`, `lg:col-span-7`, visual `lg:col-span-5 lg:-mr-[max(0px,calc((100vw-80rem)/2))]` |
| **Bento with real hierarchy** — one hero tile, two mid tiles, several small; spans follow importance | 4–7 features of unequal weight | Features of equal weight (use a list) | `grid grid-cols-6 auto-rows-[minmax(10rem,auto)]`, `col-span-6 md:col-span-4 row-span-2` |
| **Editorial index** — numbered sections (01, 02…) with a narrow label column and wide content column | Sequential process, principles, chapters | Unordered content | `grid md:grid-cols-[10rem_1fr] gap-x-12`, numbers in `font-mono tabular-nums` |
| **Sticky narrative** — a sticky left column (title, progress) while right-side steps scroll | Multi-step workflows, how-it-works, docs landing | Short pages, mobile-first flows (degrade to stacked) | `lg:sticky lg:top-24 self-start` |
| **Full-bleed breaks** — alternate contained sections with edge-to-edge bands (tinted brand surface, image, big quote) | Long pages whose sections blur together | Dense apps; more than one break per three sections | wrapper `w-full bg-brand-950 text-brand-50` + inner `mx-auto max-w-7xl` |
| **Proof as structure** — logos, metrics or quotes woven into the hero or between sections instead of a separate generic "trusted by" row | Real proof exists | Invented stats or logos | inline `dl` metrics row with `divide-x` |
| **Content-first dashboard** — the key number/chart takes the largest area; secondary KPIs shrink to a strip | Monitoring and analytics screens | Pure CRUD lists | `grid xl:grid-cols-[2fr_1fr]`, KPI strip `grid grid-cols-2 md:grid-cols-4 divide-x` |
| **Overlap and layering** — a card or image crossing a section boundary to connect two sections | Story continuity between sections | Every section (becomes noise) | `relative -mt-24 z-10` |

## Typography

| Move | Use when | Avoid when | Tailwind hint |
|---|---|---|---|
| **Display contrast** — one oversized, tightly tracked display size against a calm body size (ratio ≥ 3:1) | Marketing, landing, empty states | Dense tools | `text-5xl md:text-7xl tracking-tight leading-[0.95]` + body `text-base/7` |
| **Serif or grotesk display + neutral body** — a companion display family within the brand's character | Editorial, premium, fintech, craft brands | Brand guidelines forbid it | `next/font` two families; `font-display` token |
| **Mono as metadata** — labels, numbers, timestamps, section indices in a monospace | Developer tools, data products, technical brands | Consumer lifestyle brands | `font-mono text-xs uppercase tracking-widest` |
| **Tabular data voice** — `tabular-nums`, aligned decimals, restrained weights | Fintech, analytics, pricing tables | — | `tabular-nums slashed-zero` |
| **Measured reading width** — 60–72ch body, generous leading, strong section headings | Docs, long-form, legal-heavy products | — | `max-w-[68ch] text-lg/8` |

## Surfaces, color and depth (within the brand hues)

| Move | Use when | Avoid when | Tailwind hint |
|---|---|---|---|
| **Hairline system** — flat surfaces separated by 1px borders and dividers, shadows only on overlays | Tools, dashboards, developer products | Playful consumer brands | `border border-black/10 dark:border-white/10`, `divide-y` |
| **Tinted layers** — 3–4 surface steps derived from the brand hue (50/100/900/950) instead of grey cards | Friendly or warm brands | Brand with strict neutral palette | `bg-brand-50`, `bg-brand-100/60`, dark `bg-brand-950` |
| **One accent, used sparingly** — the brand color reserved for the primary action and one highlight per view | Any product with a clear primary action | — | primary button only `bg-brand-600`; everything else neutral |
| **Texture** — subtle grain, dot grid or line grid behind hero or section bands | Premium, creative, editorial | Data-dense screens, low-end devices | SVG noise at `opacity-[0.04]`, `bg-[radial-gradient(...)] bg-[size:24px_24px]` |
| **Real imagery treatment** — duotone from brand hues, consistent crop ratio, framed product screenshots | Photo or screenshot heavy sites | No real assets (do not invent) | `aspect-[4/3] object-cover`, `mix-blend-multiply` duotone overlay |
| **Soft elevation scale** — two or three shadow levels with a colored shadow tint, applied by role | Consumer apps, commerce | Hairline system chosen | `shadow-[0_1px_2px_rgb(0_0_0/0.06),0_8px_24px_-8px_rgb(var(--brand-rgb)/0.25)]` |

## Motion and interaction

| Move | Use when | Avoid when | Implementation |
|---|---|---|---|
| **Choreographed hero entrance** — headline, subline, CTA, visual in a 60–90 ms stagger, once | Landing and product pages | App screens users revisit often | Motion `variants` + `staggerChildren`, or CSS `animation-delay` |
| **Scroll-linked reveal of the product** — screenshot scales/tilts into place as it enters | A key product visual | Pages without one | CSS `animation-timeline: view()` or Motion `useScroll` + `useTransform` |
| **Pinned walkthrough** — a section pins while steps advance | 3–5 step workflows | Mobile (unpin below `lg`) | GSAP ScrollTrigger `pin: true, scrub: true` in `gsap.matchMedia` |
| **Shared-element transitions** — list item expands into its detail | Galleries, cards → detail, tabs | Unrelated views | Motion `layoutId`, or View Transitions API in Next.js |
| **Tactile feedback** — spring press on buttons, optimistic state change, animated counters | Interactive products | Destructive actions | `whileTap={{ scale: 0.97 }}`, spring `stiffness: 400, damping: 30` |
| **Marquee proof strip** — slow, pausable logo or quote marquee | Many real logos/quotes | Few items; users with reduced motion (static row) | CSS `@keyframes` translate + `hover:[animation-play-state:paused]` |

Every motion move follows the [Motion Engine](../../knowledge/motion/README.md) budget (at most one
high-intensity region per view) and ships a `prefers-reduced-motion` equivalent.

## Recording moves

```yaml
signature_moves:
  - id: asymmetric-split
    where: [home hero, pricing header]
    serves: "product UI is the strongest proof"
  - id: mono-metadata
    where: [section indices, changelog dates, KPI labels]
    serves: "developer audience, technical credibility"
  - id: hairline-system
    where: [all cards, tables, nav]
    serves: "calm, tool-like density"
```
