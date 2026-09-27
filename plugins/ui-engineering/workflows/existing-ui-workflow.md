# Existing UI/UX Workflow

## Trigger Conditions
Use the Existing UI/UX Workflow when:
- The repository already has established UI components, styles, design tokens, or pages (`ui_state == "EXISTING_UI"` or `"PARTIAL_UI"`); AND
- The user has not explicitly requested a full rebuild from scratch.

## Hard Preservation Rule (MANDATORY)

```text
PRESERVE FIRST
    ↓
IMPROVE SECOND
    ↓
REDESIGN ONLY WHEN EXPLICITLY REQUESTED
```

The primary duty of the agent in an existing codebase is to protect established brand identity, design tokens, and user muscle memory while improving consistency, responsiveness, and accessibility.

## Default Protection Matrix

| Property | Default State | Policy |
|---|---|---|
| **Color palette / brand colors** | `LOCKED` | Must NOT be modified or replaced without explicit user permission. |
| **Brand identity & typography** | `LOCKED` | Brand font families, voice, and visual character are strictly maintained. |
| **Overall layout identity** | `PROTECTED` | App shell (header, sidebar, footer placement) is preserved. |
| **Page composition** | `PROTECTED` / `EVOLVABLE` under Elevate | Section layout, hierarchy, type scale, surfaces and motion may be re-composed; content inventory is kept. |
| **Navigation model** | `PROTECTED` | Route structure, URLs, tab models, and primary nav hierarchy are preserved. |
| **Information architecture** | `PROTECTED` | Page hierarchies and entity relationships cannot be arbitrarily restructured. |
| **Component structure** | `CONTROLLED` | Existing component APIs and variants are reused and extended, not rewritten. |
| **Spacing / alignment / hierarchy**| `ALLOWED` | Refining rhythm, alignment bugs, padding inconsistencies is allowed (L1). |
| **Responsive / accessibility** | `ALLOWED` | Adding mobile breakpoints, fixing WCAG AA contrast, keyboard navigation is allowed (L1). |
| **Semantic states & feedback** | `ALLOWED WITH PRESERVATION` | Adding hover, focus, error, loading states using existing color tokens is allowed (L1). |

## Vague Improvement Trap

Requests containing phrases such as:
- *"modernize UI"*
- *"làm đẹp giao diện"*
- *"nâng cấp UI/UX"*
- *"đồng bộ giao diện"*
- *"make it more professional / cleaner / prettier"*

**MUST NEVER** be interpreted as permission to:
- Change the color palette or brand colors
- Introduce an unrequested visual theme or style family
- Execute a full page or global redesign
- Rewrite navigation or information architecture
- Swap out the UI framework or component library

Such requests resolve to ambition **Elevate** ([ambition-levels.md](ambition-levels.md)): the page composition, hierarchy, type scale, surfaces and motion are expected to improve visibly (L2, justified by the recorded design direction), while everything in the list above stays protected. When the user adds conservative phrasing ("keep the current look", "giữ nguyên bố cục", "chỉ tinh chỉnh") they resolve to **Refine** (L1) only.

## Change Budget Model (L1 / L2 / L3)

### L1 – Safe Refinement (Default: `ALLOWED`)
- Spacing, padding, margins, visual alignment
- Typography scale adherence and hierarchy clarity
- Responsive adaptability (mobile/tablet/desktop)
- Component states (hover, active, focus-visible, disabled, loading, empty)
- Accessibility fixes (color contrast, ARIA labels, focus traps)
- Consistency alignment with existing design tokens

### L2 – Local Structural Change (Default: `JUSTIFIED ONLY`; `ALLOWED` under Elevate)
- Internal component layout reorganization
- Section arrangement within an existing page
- Form step grouping or field flow clarification
- Card internal hierarchy adjustments
- Local breadcrumb or in-page navigation details
- Under Elevate: page-level re-composition of sections (layout, rhythm, hierarchy, surfaces, motion) inside the protected shell
- *Condition*: Requires explicit UX rationale or technical necessity documented in task scope; under Elevate the recorded `DESIGN-DIRECTION.md` (diagnosis, signature moves, re-composition plan) is the justification.

### L3 – Major Redesign (Default: `DENIED`)
- Global color palette change or new color system
- Brand visual language overhaul
- Page architecture or global layout rebuilding
- Global navigation hierarchy restructuring
- Full component library replacement or framework swap
- *Condition*: **DENIED by default**. Allowed **ONLY** when explicit, unambiguous user permission is granted.

## Execution Flow for Existing UI

1. **Extraction / Observation**: Inspect current components, styling conventions, design tokens, and layout (`CURRENT-UX-MAP.md`, including the section inventory and before screenshots for Elevate).
2. **Scope Isolation**: Determine if the task is global, page-level, or local component-level. Local component tasks are strictly isolated from global redesign.
3. **Change Budget & Ambition Determination**: Verify permissions for L1, L2, or L3 based on explicit user prompt, and read `ambition` from `orchestrate_ui`.
4. **Direction (Elevate/Reimagine)**: Diagnose against the default banlist and commit to a direction with signature moves and a re-composition plan (`DESIGN-DIRECTION.md`).
5. **Targeted Improvement**: Refine applies polish with existing tokens and components; Elevate builds derived tokens, re-composes sections and adds purposeful motion, extending existing components rather than forking them.
6. **Preservation & Non-regression Gate**: Validate that brand hues, logo, shell, navigation, routes, content inventory and data are intact; for Elevate also compare before/after screenshots and confirm the change is visible at first glance.
