# P4 — CHECK: Multi-Modal UI Verification, Visual QA & Repair Routing Engine (Completed)

The P4 phase introduces a strict **Verification Engine** modeled after the **SEE → KNOW → THINK → DO → CHECK** methodology. Instead of blind acceptance, P4 demands proof (`NO SUCCESS WITHOUT EVIDENCE`) and enforces intelligent issue routing (`NO BLIND REPAIR`).

## 1. Audit & Architecture Modernization
- Conducted a comprehensive audit of the existing `uiux/runtime` (Playwright, Axe, interactions, evidence capture) and the old `uiux/engine/runtime_critic/critic.py` (Phase 7).
- Verified that `uiux/runtime/browser.py` is robust and capable of deterministic testing, rendering probes, error catching, and visual capture without duplication.
- Identified the lack of a proper Verification Gate, Evidence Sufficiency checks, Root Cause classification, and structured Repair Routing.
- The `P4 VERIFICATION AUDIT REPORT` detailing this was created and logged at `docs/p0-p4/P4_VERIFICATION_AUDIT_REPORT.md`.

## 2. Core P4 Verification Modules (`uiux/engine/verification`)
We built a decoupled, schema-driven P4 Verification pipeline that orchestrates the existing runtime capability intelligently.

- **`schemas.py`**: Defines canonical structures (`FinalVerificationReport`, `RepairRequest`, `VerificationIssue`) and enumerates `RootCauseType` (e.g., `IMPLEMENTATION_ERROR`, `PLAN_ERROR`).
- **`gates.py`**: 
  - `VerificationGate`: Blocks P4 from running if P3 deviations exist or `ready_for_p4` is false.
  - `EvidenceSufficiencyGate`: Compares `after_evidence.captures` against P2's `VerificationContract`. It blocks passing if required viewports or routes are missing, preventing partial coverage.
- **`checks.py`**: Heuristic engines for verifying:
  - **Correctness**: Checks for browser-level console errors or outright page rendering failures.
  - **Preservation**: Validates whether `change_manifest` manipulated `locked` design tokens (e.g., unauthorized palette changes).
  - **Design Intent**: Establishes the framework to evaluate if the UI meets P2 Design Decisions.
- **`repair.py`**: A **Repair Router & Root Cause Classifier**. It evaluates failed verification checks, determines the actual cause (e.g., "Implementation touched a locked file" -> `IMPLEMENTATION_ERROR`), and produces a `RepairRequest` targeting the exact upstream phase (`P3`, `P2`, `P1`, or `P0`).
- **`engine.py`**: The Orchestrator combining all the above into a unified `FinalVerificationReport`.

## 3. End-to-End Validation
Integration tests (`test_verification.py`) were built and executed successfully:
- ✅ **Evidence Sufficiency Block**: The engine correctly intercepted and blocked validation when a `mobile_375` capture requested by the VerificationContract was missing.
- ✅ **Root Cause Routing**: An unauthorized edit to the global palette triggered a Preservation Violation. The engine automatically classified it as an `IMPLEMENTATION_ERROR` and routed a targeted repair request to `P3` (bypassing a full re-plan).
- ✅ **Successful Pass**: A complete, compliant, error-free run produced a final `PASS` status.

## 4. Final Verification State
P4 now accurately enforces the philosophy:
- `BUILD PASS ≠ UI PASS`
- `IMPLEMENTATION ERROR → P3`
- `PLAN ERROR → P2`
- `UNDERSTANDING ERROR → P0`
- `KNOWLEDGE GAP → P1`

The Verification system is modular, portable, backwards-compatible, and fully integrates the existing Playwright capabilities.
