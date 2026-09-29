# P4 VERIFICATION AUDIT REPORT

## 1. Existing Runtime Architecture (uiux/runtime)
- **Playwright Runner (`uiux/runtime/browser.py`)**: Well-established, robust, local Playwright execution. It supports full-page screenshots, layout probing (`basic_render`), viewport registry handling, server ownership, readiness checks, and deterministic capture file paths. It returns structured status (`COMPLETED`, `PARTIAL`, `BLOCKED`, `FAILED`).
- **Accessibility & Interaction (`uiux/runtime/accessibility.py`, `uiux/runtime/interaction.py`)**: Integrated to run Axe checks and predefined interaction probes.
- **Evidence Model (`uiux/runtime/evidence.py`)**: Payload definition exists. `RuntimeValidationSession` parses before/after evidence effectively.

## 2. Current Critic Capability (uiux/engine/runtime_critic)
- **`critic.py` (Phase 7)**: Acts as the current P4 validation engine. It correctly groups issues into categories (`VISUAL_REGRESSION`, `PRESERVATION_VIOLATION`, `RESPONSIVE_FAILURE`, `INTERACTION_FAILURE`, `ACCESSIBILITY_REGRESSION`, `RUNTIME_ERROR`, `PLAN_DRIFT`).
- **Eval Coverage**: Relies on basic rendering probes (`basic_render.text`, root element check) and axe scans. It compares `before` vs `after` to distinguish `pre_existing` vs `new_regression`.
- **Limitations**:
  - **No Verification Gate**: Does not verify if P3 `ImplementationReport` is ready and valid before starting.
  - **No Evidence Sufficiency Gate**: Checks partial evidence minimally but lacks strict enforcement of P2's `VerificationContract`.
  - **No Design Intent Check**: It only looks for regressions. It does not know if the intended change from P2 actually succeeded (e.g., "Improve CTA hierarchy").
  - **Weak Root Cause & Routing**: It has a `repairable: bool` and `likely_cause` text, but lacks a structured `Root Cause Classification` (`IMPLEMENTATION_ERROR`, `PLAN_ERROR`, etc.) and a dedicated `Repair Router`.

## 3. Duplication & Reusable Modules
- **Reuse**: We MUST reuse `uiux.runtime.*` as requested. The Playwright orchestrator is complete and must not be duplicated.
- **Reuse**: The existing session builder `RuntimeValidationSession` from `uiux.engine.runtime_critic.session` should be utilized for payload hydration.
- **Refactor**: `critic.py` needs to be significantly enhanced or wrapped inside a higher-level P4 `VerificationEngine` that handles Gates, Design Intents, Root Causes, and structured Repair Requests.

## 4. Refactor Plan
Instead of rewriting `browser.py`, P4 will focus on **Orchestration & Verification Intelligence**:
1. **Verification Gate**: Block execution if P3 `ImplementationReport` is invalid.
2. **Evidence Sufficiency Gate**: Validate that the executed run matches the `VerificationContract`.
3. **Design Intent Evaluator**: Translate P2 `DesignDecision` to verifiable heuristics.
4. **Root Cause Classifier**: Map any failed issue to `IMPLEMENTATION_ERROR -> P3`, `PLAN_ERROR -> P2`, `UNDERSTANDING_ERROR -> P0`, or `KNOWLEDGE_GAP -> P1`.
5. **Repair Router**: Generate `RepairRequest` schemas instead of plain text instructions.
6. **Final Verification Report**: Build the comprehensive final report structured as `FINAL_VERIFICATION_REPORT` merging Correctness, Preservation, Intent, and Accessibility.

## 5. Migration Impact
- By keeping `uiux/runtime/browser.py` untouched, we maintain 100% backward compatibility for all environment runners, MCP tools, and CLI scripts.
- The new `uiux/engine/verification` package will supersede `uiux/engine/runtime_critic` (or we will safely upgrade `critic.py` with the missing Intelligence logic to preserve API contracts).
