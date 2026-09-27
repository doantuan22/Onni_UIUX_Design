---
name: ui-ux-workflow
description: Orchestrate a two-phase web UI/UX delivery workflow with structure locking, artifact contracts, and review gates. Use for new interface work, redesigns, or UI audits; do not use it for standalone visual styling guidance.
---

# UI/UX Workflow Engine

## Purpose and role

Act as the workflow controller for web UI/UX work. Establish the project state, select a valid entry point, and preserve the boundary between UX structure and visual/frontend delivery. Phase 1 defines the complete structural handoff; Phase 2 remains out of scope for structural decisions.

## Operating loop

1. Inspect the project and active artifacts.
2. Read [workflows/execution-contract.md](workflows/execution-contract.md) and [workflows/routing.md](workflows/routing.md) to select an entry state.
3. Follow [workflows/state-machine.md](workflows/state-machine.md) and load the relevant phase or review file.
4. Create or update only artifacts authorized for that state, using the templates as starting points.
5. Run the state-specific review loop and apply [workflows/phase-transition.md](workflows/phase-transition.md).
6. Stop at `BLOCKED` when a required contract cannot be satisfied; record the reason and rollback target.

The valid happy path is `INITIAL → ANALYZING → PHASE_1 → PHASE_1_REVIEW → STRUCTURE_LOCKED → PHASE_2 → PHASE_2_REVIEW → FINAL_REVIEW → DONE`.

## UI Orchestration & Workflow Routing

All requests enter via the UI Orchestrator (`uiux.api.orchestrate_ui` or CLI `python scripts/orchestrate_ui.py`):
1. Inspect project context and determine UI state (`GREENFIELD`, `PARTIAL_UI`, `EXISTING_UI`, `UNKNOWN`).
2. Route to the dedicated workflow:
   - **Greenfield UI** ([workflows/greenfield-workflow.md](workflows/greenfield-workflow.md)): For brand-new projects or explicit rebuilds. AI applies grounded design freedom (domain, target users, density); user constraints take highest precedence. Multi-page builds require page inventory and UX flow before code.
   - **Existing UI/UX** ([workflows/existing-ui-workflow.md](workflows/existing-ui-workflow.md)): For codebases with established UI footprint. Strictly enforces **PRESERVE FIRST → IMPROVE SECOND → REDESIGN ONLY WHEN EXPLICITLY REQUESTED**. Employs L1/L2/L3 change budget and granular permissions ([workflows/preservation-rules.md](workflows/preservation-rules.md)).
3. Evaluate Change Budget and Ambition. Budget: L1 (Safe Refinement, default: allowed), L2 (Local Structural Change, default: justified only), L3 (Major Redesign, default: denied unless explicit permission). Upgrade requests ("modernize", "làm đẹp", "nâng cấp giao diện") NEVER authorize L3 or palette changes, but they resolve to ambition **Elevate** ([workflows/ambition-levels.md](workflows/ambition-levels.md)): page composition, hierarchy, type scale, surfaces and motion must visibly improve (L2) while the app shell, navigation, routes, content, data and brand hues stay. "Keep the current look" or local fixes resolve to **Refine**; explicit redesign to **Reimagine**.
4. For detailed workflow routing, consult [workflows/routing.md](workflows/routing.md).
5. In Phase 1 structure definition, load [skills/ux-structure/router.md](skills/ux-structure/router.md) after [skills/ux-structure/README.md](skills/ux-structure/README.md).
6. For the structure gate, load [workflows/phase-transition.md](workflows/phase-transition.md) and [templates/STRUCTURE-LOCK.md](templates/STRUCTURE-LOCK.md).
7. In Phase 2 visual realization, load [skills/ui-orchestrator/README.md](skills/ui-orchestrator/README.md), the active `STRUCTURE-LOCK.md`, and [skills/ui-orchestrator/router.md](skills/ui-orchestrator/router.md).
8. For review, load the applicable file in [review/](review/).

Executable tools (capability resolver, knowledge retrieval, technology resolver, quality analyzer, runtime runner, evals, validation) are listed in `uiux/core/tools.json` and run with `python scripts/uiux_cli.py call <tool-id>`; see [../development/docs/plugin-architecture.md](../../development/docs/plugin-architecture.md).

Do not load the entire skill directory by default. Detailed contracts are in [workflows/artifact-contract.md](workflows/artifact-contract.md); the architectural rationale is in [../development/docs/architecture.md](../../development/docs/architecture.md).

## Global execution invariants

- Load the minimum sufficient context by following [workflows/reference-loading.md](workflows/reference-loading.md); reuse validated artifacts rather than rediscovering them.
- Discover the active artifact before creating a new one. Respect `LOCKED > ACTIVE > DRAFT > SUPERSEDED`, and never create ad-hoc duplicate filenames.
- Keep work within explicit scope. Record unknown business rules as questions or assumptions, not facts.
- Review loops must show material progress. Stop after the configured limit or two consecutive no-progress iterations and enter `BLOCKED` with the required record.
- `DONE` needs gate and scope evidence, not merely valid Markdown or compiling code. See [workflows/execution-contract.md](workflows/execution-contract.md).

For rendered UI changes, decide execution need with [workflows/execution-requirement.md](workflows/execution-requirement.md). Detect capability before choosing strategy, reuse existing browser/runtime tooling before adding anything, and never claim browser verification without actual evidence.

Accessibility is not proven by axe alone. Never install accessibility tooling or fake manual verification; when required, the rendered UI must satisfy the [Accessibility Gate](execution/accessibility/gate.md).

An upgrade is judged by the rendered result, not the diff: under Elevate, map pages and sections before editing (`map_ui_structure` → `.uiux/ui-map.json`; `diff_ui_maps` afterwards proves content was kept and sections were re-composed), commit to a direction with at least three [signature moves](skills/design-direction/signature-moves.md), replace the [default banlist](knowledge/visual-language/anti-slop/default-banlist.md) patterns found in the current UI, and compare before/after screenshots. Recipes and guidance prioritize React + Tailwind CSS and Next.js; under Elevate/Reimagine one motion library (Motion or GSAP) may be proposed when CSS cannot deliver the chosen motion.

Tokens alone do not define visual quality. Rendered UI must follow an approved Visual Grammar when visual realization changes. Avoid generic AI UI through intentional craft and adversarial review, not blanket style bans; preserve an existing coherent system unless a documented rationale justifies change.

A strong interface needs intentional inspiration, not random styling: select design DNA with [Design Inspiration](skills/design-inspiration/README.md), and choose composition from content and product intent via the [Web Pattern Library](knowledge/web-patterns/README.md). References provide design DNA, not templates to clone. Typography is part of product character, not merely font sizing ([Typography Intelligence](skills/typography/README.md)). Motion must communicate, orient, or support storytelling, within a budget and with a reduced-motion equivalent ([Motion Engine](knowledge/motion/README.md)).

Design decisions come from the [Design Knowledge System](knowledge/domains/README.md) through the [Capability Resolver](skills/capability-resolver/README.md): declare brand, product, audience, density, interaction model, content and intensity first, then retrieve only the resolved entries. Every chosen style, layout, motion, interaction, effect and technology needs a *why* and a *why not*. Premium does not mean more effects; prefer the simplest technology that meets the need, and never install a dependency or add an asset automatically (a sanctioned motion library is proposed to the user with its install command).

## Phase 1 boundary

Phase 1 resolves what exists, why, who uses it, where it lives, how users move through it, what information and actions each screen needs, and what happens next. It creates a specification-driven structural handoff, not visual styling. Do not choose colors, typography, visual effects, CSS, component appearance, or frontend implementation here.

Phase 1 must not invent business rules or change backend, authentication, API, database, or route contracts. Record unsupported assumptions, dependencies, and open questions. Explicit user requirements override general UX recommendations unless they cause a serious logical conflict.

## Non-negotiable gates

- Phase 2 may start only from `STRUCTURE_LOCKED` with a valid, active structure lock.
- A locked structural artifact is not changed in Phase 2. A requested business, actor, flow, page, field, route, or API change returns work to Phase 1.
- A phase exits only after its review passes and its required artifacts exist.
- `DONE` requires a passed final review and `FINAL-REVIEW.md`.

Phase 2 must produce rendered evidence, not merely compiling code. It may return implementation/visual issues to Phase 2, but it must send a semantic, business, flow, actor, permission, required-data, route, or API mismatch back to Phase 1 without editing the lock.
