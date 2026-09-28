# Preservation Rules, Change Budget & Precedence Hierarchy

## 1. Machine-Readable Policy Representation

Preservation rules are enforced by the UI Orchestrator via machine-readable contracts evaluated at runtime before any file modification.

```yaml
protected_design:
  color_palette: locked            # locked | unlocked
  brand_identity: locked           # locked | unlocked
  overall_layout_identity: protected # protected | unprotected   (app shell: header, sidebar, footer placement)
  page_composition: protected      # protected | evolvable | unlocked (evolvable under ambition ELEVATE)
  navigation_model: protected      # protected | unprotected
  information_architecture: protected # protected | unprotected
  component_structure: controlled  # controlled | uncontrolled

allowed_changes:
  safe_refinement: true            # L1: true | false
  local_structural_change: justified_only # L2: allowed | justified_only | denied
  major_redesign: explicit_user_permission_only # L3: granted | explicit_user_permission_only | denied
  max_level: L1                    # L1 | L2 | L3

ambition: refine                   # refine | elevate | reimagine (upgrade requests -> elevate, max_level L2)
```

## 2. Change Budget (L1 / L2 / L3) Model

| Level | Classification | Scope & Activities | Default Status | Authorization Requirement |
|---|---|---|---|---|
| **L1** | Safe Refinement | Spacing, typography scale, responsive breakpoints, states, accessibility, visual polish, token alignment. | `ALLOWED` | Standard workflow. |
| **L2** | Local Structural Change | Internal component layout, section ordering, form step flow, card reorganization. | `JUSTIFIED ONLY` | Clear UX / technical justification required in task scope. |
| **L3** | Major Redesign | Global color palette change, branding overhaul, page architecture rebuild, framework migration. | `DENIED` | Explicit, unambiguous user permission required. |

## 3. Granular Permission Enforcement

Permissions are strictly **independent and non-transitive**:

1. **Layout Permission != Palette Permission**:
   - Granting permission to alter layout (e.g. *"được phép thay đổi layout trang chủ"*) unlocks `overall_layout_identity` to L2/L3, but `color_palette` and `brand_identity` remain **LOCKED**.
2. **Palette Permission != Full Redesign Permission**:
   - Granting permission to update colors (e.g. *"đổi màu sang tông xanh dương"*) unlocks `color_palette`, but `navigation_model`, `information_architecture`, and `page_architecture` remain **PROTECTED**.
3. **Local Scope Containment**:
   - If the task target is a single component or form (e.g. *"sửa lại nút submit"*), `max_level` is capped at L2 (local); global redesign is strictly denied.
4. **Vague Enhancement Exclusion**:
   - Generic terms like *"modernize UI"*, *"làm đẹp"*, *"make it professional"* do NOT grant L3 permissions or unlock any protected property.
   - They do resolve to ambition **ELEVATE**: `page_composition` becomes `evolvable` and `max_level` L2, so sections may be re-composed (layout, hierarchy, type scale, surfaces, motion) inside the protected shell. Content inventory, routes, data and brand hues remain invariants. See [ambition-levels.md](ambition-levels.md).
5. **Conservative Phrasing Wins**:
   - *"keep the current look"*, *"giữ nguyên bố cục"*, *"minimal changes"*, *"chỉ tinh chỉnh"* resolve to **REFINE** (L1) even when upgrade words are present.

## 4. Strict Precedence Hierarchy

Every design and engineering decision must adhere to this invariant order of authority:

```text
1. Explicit user instruction
       ↓ (overrules)
2. Existing brand identity
       ↓ (overrules)
3. Existing design system
       ↓ (overrules)
4. Existing UX / information architecture
       ↓ (overrules)
5. Repository / framework constraints
       ↓ (overrules)
6. Domain best practices
       ↓ (overrules)
7. Design inspiration
       ↓ (overrules)
8. AI preference
```

### Precedence Case: Existing Identity vs. Design Inspiration
- If an existing project is in the e-commerce domain and the `design-inspiration` skill recommends an editorial or brutalist style, **Existing Brand Identity (Level 2) and Existing Design System (Level 3) defeat Design Inspiration (Level 7)**.
- Inspiration provides reference DNA for new greenfield builds or explicitly authorized redesigns, but NEVER overwrites an established existing identity.

## 5. Phase 2 Extension Point

In Phase 1, repository state is evaluated through `HeuristicUIStateDetector`.
In Phase 2, the `UIStateDetector` abstraction will be extended with:
- **Framework & Styling Engine Detector** (Tailwind, CSS Modules, Styled Components, Emotion)
- **Design Token Extractor** (CSS variables, theme objects, tailwind color maps)
- **Component & Page Inventory Scanner** (AST component graph)

The interface defined in `uiux/engine/ui_state.py` allows Phase 2 intelligence to plug directly into the orchestrator without changing workflow routing or preservation semantics.
