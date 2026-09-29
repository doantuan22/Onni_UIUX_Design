# P1 Knowledge Audit Report

## 1. Overview of Existing Knowledge System
The current knowledge system under `plugins/ui-engineering/knowledge/` contains 139 Markdown files and 18 Code Recipes (17 `.tsx`, 1 `.css`). While the repository possesses a solid foundational structure for rules and capabilities, the current content heavily skews toward "DO/DON'T" checklists and abstract design direction rather than actionable engineering intelligence.

### High-level Categories
- **visual-language**: 28 files (Components, Anti-slop, Character, Density)
- **domains (UI Patterns)**: 29 files (Screens, Interactions, Effects, Styles, Graphics)
- **references**: 16 files (Layout, Motion, Typography, Accessibility, etc.)
- **motion**: 14 files (Principles, Vocabulary, Spatial, Layout)
- **web-patterns**: 13 files (Hero, Grid, Composition, Navigation)
- **frameworks**: 10 files (React, Vue, Angular, Svelte, Next.js, Nuxt)
- **styling**: 9 files (Tailwind, Bootstrap, MUI, CSS Modules, SCSS)
- **typography**: 7 files (Body, Display, Pairing, Rhythm)
- **runtime-validation**: 4 files (Accessibility, Forms, Responsive)
- **preservation**: 1 file (Existing UI invariants)
- **domain-packs**: Empty (No business domains defined)

## 2. Quality & Depth Assessment
Based on an automated audit of the 139 files:

| Metric | Count / Status | Analysis |
|--------|----------------|----------|
| **Total MD Files** | 139 | High quantity, but shallow depth (many files < 30 lines). |
| **Has "HOW TO" / Implementation** | 64 | ~46% of files mention implementation. Often superficial. |
| **Has "WHEN TO USE" / Purpose** | 36 | Only ~25% explicitly declare selection rules or conditions. |
| **Has Responsive Guidance** | 74 | Mentioned, but rarely explains *how* to transform across breakpoints. |
| **Has Accessibility Notes** | 71 | Present, but mostly checks (e.g., "use ARIA") instead of pattern logic. |
| **Strictly DO/DON'T** | 28 | Purely constraints without explaining the engineering context. |

### Component Guidance Evaluation
Files in `knowledge/visual-language/components/` (e.g., `buttons.md`, `forms-controls.md`) are currently extremely brief (e.g., `buttons.md` is 16 lines). They lack:
- Detailed states (focus-visible, loading, disabled).
- Framework-specific implementation notes.
- Sizing, spacing, and interaction details.
- Explicit connections to Code Recipes.

### Framework & Styling Coverage
- Files exist for `react`, `vue`, `nextjs`, `tailwindcss`, `bootstrap`, etc.
- **Depth**: Shallow. For instance, `tailwindcss.md` (23 lines) lists 3 rules (Avoid arbitrary values, consistent scales, mobile-first) without providing actionable implementations or anti-patterns for complex layouts.

### Domain Coverage
- **Current `domains` directory**: Stores UI Patterns (e.g., `effects/`, `interactions/`).
- **Business Domains**: **Missing.** The `domain-packs/` directory exists but contains no business logic (e.g., e-commerce, SaaS, AI tools, developer tools).

## 3. Code Recipe Coverage
Total: 18 Recipes (located in `knowledge/code-recipes/react-tailwind/`)
- **motion (5)**: `hero-entrance.tsx`, `scroll-product-reveal.tsx`, etc.
- **sections (11)**: `bento-features.tsx`, `cta-band.tsx`, `pricing-emphasis.tsx`, etc.
- **surfaces (1)**: `grain-texture.tsx`
- **tokens (1)**: `brand-theme.css`

**Observation:** Recipes are heavily centered around `react-tailwind`. Missing crucial UX flows like checkout, multi-step forms, search filtering, and dense data tables.

## 4. Duplication & Architecture Overlap
- **Duplication Risk**: Rules are scattered across `references/`, `visual-language/`, and `web-patterns/`. E.g., Motion is covered in `knowledge/motion/` as well as `knowledge/references/motion.md` and `knowledge/visual-language/anti-slop/motion.md`.
- **Knowledge Schema**: Currently relies heavily on YAML frontmatter (`id:`, `kind:`), but the structure is inconsistent and often missing canonical metadata for contextual routing. The `catalog.py` parser expects specific keys, which restricts flexibility.

## 5. What Needs to be Refactored vs. Added

### **To Refactor (Reuse & Normalize):**
- **Components (`visual-language/components/`)**: Refactor from short checklists into robust *Component Engineering Guides* (anatomy, states, variants, accessibility).
- **Frameworks & Styling**: Move from "rules" to "implementation guides" (e.g., how to use Next.js routing with UI layouts, how to extend Tailwind theme).
- **Web Patterns & UX Flows**: Expand `web-patterns/` to include flow-based guides (auth, onboarding, data table).

### **To Add (Enrich):**
- **Business Domain Packs**: Create `domain-packs/` for E-commerce, SaaS, AI Product, Developer Tool, Hospitality, etc.
- **Responsive Engineering**: Create a dedicated taxonomy for viewport transformation logic (e.g., sidebar to drawer).
- **New Code Recipes**: Multi-step forms, data tables, advanced filter bars, dashboard shells.

### **To Route (Index):**
- The `Knowledge Router` must be enhanced to dynamically select the minimum sufficient knowledge chunks based on `ui_context` (from P0) + `task_type` + `domain`.

## 6. Next Steps for P1 (KNOW)
1. **Schema & Taxonomy Normalization**: Standardize the knowledge schema to support `when`, `avoid_when`, `responsive`, `accessibility`, and `implementation` fields. (Checkpoint 1)
2. **Foundation & Layout**: Expand design foundations (Color, Typography) and robust layout engineering. (Checkpoint 2)
3. **Component & UX Patterns**: Refactor the current shallow component markdown files into full engineering specifications. (Checkpoint 3)
4. **Domain Packs**: Build the missing Business Domain packs. (Checkpoint 6)

The current system has the *skeleton* of a registry and router (`catalog.py`, `registry.json`), but the *flesh* (the actual knowledge content) must transition from "Constraints/Rules" to "Engineering/Implementation Guidance."
