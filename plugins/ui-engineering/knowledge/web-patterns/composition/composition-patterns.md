# Visual composition patterns

Page-level composition decides how space, alignment and scale are distributed. Choose one dominant composition per page; a second may appear in a scoped region.

| Composition | Character | Use when | Grid / rules | Risk |
|---|---|---|---|---|
| **asymmetric editorial** | authored, dynamic | editorial, luxury, portfolio | 12-col grid with offset columns (e.g., 2–7 / 8–12); captions and media break alignment deliberately | Looks accidental if offsets are inconsistent — use 2–3 repeated offsets |
| **strict grid** | orderly, credible | SaaS, technical, developer, marketplace | Consistent columns, gutters and alignment; visible hairline grid optional (developer) | Monotony; fix with scale/density variation, not decoration |
| **cinematic centered** | calm, focused, premium | premium-product, launches | Centered axis, large media, one message per section, generous vertical space | Stretching thin content; long scroll with little information |
| **split composition** | balanced explanation | feature explanation, editorial hero, forms with context | Two columns with unequal weight (5/7 or 4/8) rather than 6/6 by default | Symmetric 50/50 splits everywhere read as template |
| **layered depth** | spatial, product-rich | consumer-tech, creative tools, premium SaaS previews | Overlapping media/UI layers with consistent elevation logic | Visual noise, floating decorative cards, contrast issues |
| **full-bleed media** | immersive | travel, hospitality, portfolio, luxury | Edge-to-edge media with contained text; art-directed crops | Text over busy images; heavy media |
| **high-density product** | efficient | dashboards, admin, results | App shell, compact spacing, tables and panels | Clutter without hierarchy; card-in-card |
| **low-density premium** | exclusive, calm | premium, luxury, minimal | Few elements per viewport; strong scale contrast | Hiding productive actions; excessive scrolling |

Compatibility with archetypes follows [archetypes.md](../../../skills/design-inspiration/archetypes.md). Composition must preserve reading order in the DOM; visual reordering must not change keyboard/screen-reader order.
