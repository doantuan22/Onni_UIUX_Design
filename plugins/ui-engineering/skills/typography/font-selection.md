# Font selection

Select families by evidence, not by a "beautiful fonts" list. The skill stores knowledge only: it never ships, downloads, or vendors font files.

## Order of preference

1. **Existing project/brand font** that is licensed, readable and covers required languages → keep.
2. **System font stack** when the archetype is neutral/dense and performance matters most.
3. **Licensed open web font** (OFL/Apache) loaded through the project's existing mechanism (framework font loader, existing `@font-face`, existing CDN policy).
4. **Commercial font** only when the user supplies the license and files/kit.

## Criteria (evaluate in this order; an early failure eliminates)

| # | Criterion | Check |
|---|---|---|
| 1 | Licensing | OFL/Apache or user-provided license. Platform-restricted brand faces (e.g., OS vendor fonts) must not be self-hosted; reach them only via `system-ui` on their platforms. |
| 2 | Language coverage | All required scripts/diacritics render in the chosen weights; see below. |
| 3 | Readability | Clear at body sizes: open apertures, distinct `Il1`, `O0`, `rn/m`; adequate x-height. |
| 4 | Screen rendering | Hinting/rendering acceptable on Windows at 14–16px; test thin weights. |
| 5 | Brand character | Matches the [typography archetype](../../knowledge/typography/typography-archetypes.md). |
| 6 | Performance | Prefer one variable file per family; ≤ 2 families and ≤ ~4 font files on first load; subset to needed scripts; `font-display: swap` (or `optional` for non-critical); preload only the above-the-fold face. |
| 7 | Availability | Accessible to the project's hosting policy (self-host vs CDN); works offline builds when required. |
| 8 | Fallback quality | A metric-close fallback stack; use `size-adjust`/`ascent-override` when the project supports it to limit layout shift. |

## Vietnamese and diacritics

Vietnamese stacks diacritics (e.g., `ặ ẫ ỡ ự Ở ề`). Requirements:

- The font must include the `vietnamese` subset/character set in **every weight used**; otherwise browsers synthesize from fallback fonts and marks misalign.
- Verify with a test string in every used weight/style: `Tiếng Việt: Ặ ặ Ẫ ẫ Ỡ ỡ Ự ự Ở ở Ề ề — Quý khách đặt phòng thành công.`
- Line-height: give display text ≥ 1.1–1.15 and body ≥ 1.5 so stacked marks do not collide with the line above; very tight display leading (< 1.05) clips marks.
- Uppercase + tight tracking is riskier for Vietnamese; test before adopting all-caps headings.
- Coverage below is **expected** from public distributions; always verify the version the project loads.

## Curated shortlist

Small by design. Add a family only when it covers a gap here.

| Family | Class | Character / use | License | Vietnamese (verify) | Variable |
|---|---|---|---|---|---|
| Inter | neo-grotesk | neutral-product, dense UI, premium-modern with tight display | OFL | expected ✓ | ✓ (opsz in newer versions) |
| Be Vietnam Pro | neo-grotesk | Vietnamese-first products, neutral/premium | OFL | ✓ (designed for it) | static weights |
| Roboto / Roboto Flex | neo-grotesk | neutral, Android-native feel; Flex offers width/optical axes | OFL/Apache | expected ✓ | Flex ✓ |
| Noto Sans / Noto Serif | humanist / serif | maximum script coverage, multilingual products | OFL | ✓ | ✓ |
| Source Sans 3 | humanist | readable UI and long text, technical docs | OFL | expected ✓ | ✓ |
| IBM Plex Sans | grotesk | technical, developer, enterprise | OFL | verify per version | ✓ (newer) |
| Plus Jakarta Sans | geometric-humanist | friendly-consumer, modern-saas | OFL | expected ✓ | ✓ |
| Lexend | geometric | readability-focused friendly UI | OFL | expected ✓ | ✓ |
| Nunito | rounded | friendly-consumer, education | OFL | expected ✓ | ✓ |
| Archivo | grotesk (width axis) | technical/expressive display via width, marketing | OFL | expected ✓ | ✓ (wdth) |
| Space Grotesk | quirky grotesk | technical/expressive display only; not long body | OFL | expected ✓ | ✓ |
| Source Serif 4 | transitional serif | editorial body and display (optical sizes) | OFL | expected ✓ | ✓ (opsz) |
| Literata | book serif | long reading | OFL | expected ✓ | ✓ |
| Newsreader | editorial serif | editorial display/body with optical sizes | OFL | expected ✓ | ✓ |
| Fraunces | soft display serif | editorial/friendly display; never dense UI | OFL | expected ✓ | ✓ |
| Playfair Display | high-contrast serif | luxury/editorial display only (≥ 28px) | OFL | expected ✓ | ✓ |
| JetBrains Mono | mono | developer code, terminals | OFL | expected ✓ | ✓ |
| IBM Plex Mono | mono | technical metadata paired with Plex Sans | OFL | verify | static |
| Roboto Mono / Noto Sans Mono / Source Code Pro | mono | neutral code/IDs | Apache/OFL | expected ✓ | ✓ |

Families sometimes chosen for trendiness but historically shipped **without** a Vietnamese subset in some distributions (e.g., certain releases of DM Sans or Instrument Serif) must be verified before use in Vietnamese products; if coverage is missing, choose a covered alternative with similar character rather than mixing fallback glyphs.

## System stacks

```css
/* neutral sans — native on each platform; Vietnamese covered by Segoe UI, SF, Roboto, Noto */
font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Noto Sans", "Helvetica Neue", Arial, sans-serif;
/* serif */
font-family: ui-serif, Georgia, "Noto Serif", "Times New Roman", serif;
/* mono */
font-family: ui-monospace, SFMono-Regular, "Cascadia Mono", Menlo, Consolas, "Liberation Mono", "Noto Sans Mono", monospace;
```

System stacks are a **valid first choice** for `dense-transactional`, `neutral-product`, and developer app shells; they are weak for `editorial`, `luxury`, and `expressive-marketing` where character must be consistent across platforms.

## Record in DESIGN-SYSTEM.md

For each family: role, class, reason, license, language verification result, weights used, loading method, fallback stack, and whether it was existing/system/new.
