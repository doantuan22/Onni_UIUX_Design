# P2 REASONING AUDIT REPORT

## 1. Current Modules & Responsibility

- `uiux/engine/orchestrator.py`: Entry point for workflow routing (GREENFIELD vs EXISTING_UI), preservation evaluation, change level budgeting (L1/L2/L3), and resolving high-level required skills/knowledge.
- `uiux/engine/modification_planner/planner.py`: Core planner generating a structured `plan_dict`. Orchestrates scope, surface, change classification, and blast radius.
- `uiux/engine/modification_planner/scope_resolver.py`: Normalizes user task intent and identifies monorepo scope.
- `uiux/engine/modification_planner/surface_resolver.py`: Maps the user intent to affected pages, files, and components.
- `uiux/engine/modification_planner/change_classifier.py`: Evaluates the user request against the preservation constraints to classify if the change is L1, L2, or L3 and flags authorization violations.
- `uiux/engine/modification_planner/blast_radius.py`: Estimates cross-application and component-level impact based on surface mappings.
- `uiux/engine/modification_planner/step_planner.py`: Translates changes into implementation steps and validation requirements.

## 2. Capability State Matrix

| Capability | Current State | Missing / Gaps | Action |
|------------|---------------|----------------|--------|
| **Requirement Intelligence** | Partially exists in `scope_resolver.py` & `orchestrator.py`. | Lacks separation of explicit vs. inferred requirements. Doesn't parse detailed constraints (e.g., must_keep, functional vs visual). | Upgrade `semantic_parser.py` / `scope_resolver.py`. |
| **Workflow Classification** | Exists in `orchestrator.py`. | Functionally complete but outputs are scattered. | Reuse & Normalize. |
| **Problem Diagnosis** | **Missing**. | Currently skips directly to `implementation_steps` without formal diagnosis (visual, UX, a11y). Circular reasoning risk. | **Create** `diagnosis_engine.py`. |
| **Preservation Reasoning** | Exists (`preservation.py`). | Structured output is good, but needs to tightly integrate with Diagnosis to define "FREE vs LOCKED" properties dynamically. | Reuse & Centralize in Planner. |
| **Change Budget (L1/L2/L3)** | Exists (`change_classifier.py`). | Good enforcement. | Reuse. |
| **Design Strategy** | **Missing**. | The planner lacks a middle layer deciding *how* to solve the problem before implementing (e.g., layout strategy, component reuse strategy). | **Create** `design_strategy.py`. |
| **Recipe Selection** | Missing in Planner. | `recipes.py` exists in engine but is not integrated into `modification_planner`. | Integrate `recipes.py` into `planner.py`. |
| **Impact Analysis** | Exists (`blast_radius.py`). | Needs to consume the `P0 Component Graph` directly rather than guessing. | Refactor to consume P0 context. |
| **Modification Plan** | Exists (`planner.py`). | Missing diagnosis, design strategy, decision trace, and explicit verification contract. | Refactor & Upgrade Schema. |
| **Planning Gate** | Partially exists (`status: blocked/ready`). | Needs formal integration as `PLANNING_GATE` output block with explicit permission checks. | Normalize as `planning_gate`. |
| **Editor / Code Gen** | Currently, `controlled_editor.py` is in the planner package! | This is a P3 (DO) capability, violating P2 separation. | Migrate `controlled_editor.py` to P3/Executor layer. |

## 3. Duplication & Misplaced Layers

- **Duplication:** Intent parsing happens in both `orchestrator.py` (`normalize_intent`) and `knowledge_router/intent.py`.
- **Misplaced Layer:** `controlled_editor.py` is inside `uiux/engine/modification_planner/`. A planner should NEVER contain an editor. It must be moved to P3/DO.

## 4. Refactor & Integration Plan

1. **Purge Editors:** Ignore/Deprecate `controlled_editor.py` from P2 scope. P2 must output read-only schemas.
2. **Centralize Input:** Update `ModificationPlanner.plan()` to explicitly consume `UI_CONTEXT` (from P0) and `KNOWLEDGE_LOAD_PLAN` (from P1).
3. **Build Diagnosis Engine:** Create `diagnosis.py` to separate *Problem* from *Solution*.
4. **Build Strategy Engine:** Create `strategy.py` to formulate layout/component strategies based on Knowledge and Diagnosis.
5. **Integrate Recipes:** Call `recipes.suggest()` during planning to select valid component implementations without writing code.
6. **Refactor Output Schema:** Update `planner.py` to output the canonical P2 schema: `RequirementProfile`, `Diagnosis`, `Preservation`, `Strategy`, `Recipes`, `Impact`, `ExecutionChunks`, `VerificationContract`, `PlanningGate`.
