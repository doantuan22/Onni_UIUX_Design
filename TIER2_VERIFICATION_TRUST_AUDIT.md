# Tier 2 Verification Trust Audit

**Audit completed before Tier 2 implementation.** This records the repository state after the Tier 1 changes already present in the working tree. No verification implementation code was changed before this audit.

## 1. Existing verification capabilities

- P4 entrypoint: `uiux.engine.verification.engine.VerificationEngine`, exposed through `uiux.api.verify_implementation`.
- Existing P4 pieces: verification gate, runtime evidence sufficiency gate, runtime correctness, token preservation, design intent placeholder, and repair routing.
- Existing runtime critic: `uiux.engine.runtime_critic` handles rendered evidence critique and targeted repairs. Keep its Playwright/runtime implementation and repair routing; Tier 2 must not replace it.
- Existing capability detection: `uiux.runtime.capabilities.detect`, already reused by `doctor`, runtime tools, and Tier 1 task orchestration.
- Existing source/framework signals: P0 repository intelligence and P3 execution gate/framework adapter/scope lock/file editor. These are useful inputs, but they do not currently form a P4 static verification report.
- Existing validations: `uiux.tooling.validate` validates the plugin/skill/package contracts; runtime and accessibility evidence validators validate their current manifest formats. Neither is a general source-diff/build verifier.
- Existing checks cover P0–P4 in `tests/test_*`; focused P4 coverage is `test_p4_verification.py`, `test_p3_p4_tools.py`, `test_runtime_critic.py`, and runtime/accessibility tests. Runtime eval scenarios E19–E47 include completion gates, missing browser, partial capture, route failure, and axe capability cases. Existing design quality evals E65–E80 are unrelated to verification trust and must not be repurposed as benchmarks.

## 2. Browser-dependent capabilities

Playwright DOM/render capture, browser console and route observations, screenshots, visual critique, interaction execution, and browser-backed axe scans need a usable browser/runtime. `uiux.runtime.capabilities.detect` distinguishes `NOT_DECLARED`, `DECLARED_NOT_INSTALLED`, `PACKAGE_AVAILABLE_BROWSER_MISSING`, and `READY`; it is read-only and does not install or launch anything.

## 3. Browser-independent capabilities

Repository/source diff, changed-file/scope checks, change-ledger consistency, token/config inspection, framework/source heuristics, and explicitly detected build/typecheck/lint/test commands can run without a browser. P0/P3 contain reusable framework/scope knowledge, but there is no canonical P4 engine to collect these results or report their evidence today. Build commands must come from project detection; no command may be invented or auto-installed.

## 4. Existing evidence types

- Runtime manifests and execution reports with route/viewport captures, statuses, file paths, and console errors.
- Before/after captures and optional change manifests consumed by `RuntimeValidationSession`.
- Accessibility scan manifests and axe result artifacts.
- P3 change ledger and target-project file-change observation made by Tier 1 orchestration.
- P0 repository/UI maps, preservation profiles, P2 verification contracts, and P3 implementation reports.
- Evidence is stored in existing `.evidence` project storage; no second evidence store is needed.

## 5. Fake-PASS risk locations

- `engine/verification/checks.py::verify_design_intent` currently returns `result="PASS"` for every decision, describes rendered UI as matching intent heuristically, and emits the literal ref `screenshot_after` without validating a screenshot exists. This is the clearest fake verified claim.
- `engine/verification/engine.py` returns report `status="PASS"` after its correctness/preservation checks even though design intent is explicitly not evaluated and responsive/interactions/accessibility/performance are `NOT_EVALUATED`. Its generic `evidence.refs=["after_evidence.json"]` is not provenance validation.
- `engine/verification/gates.py` returns `PASS` for gate success and evidence sufficiency. These are local gate outcomes, not overall verification or user-facing UI claims; callers must preserve this distinction.
- `runtime_critic/critic.py` and `loop.py` use `PASS` as a quality-loop decision. This is based on the critic’s current report/evidence path, but the literal alone does not disclose coverage or provenance.
- `task_orchestrator.py` currently changes the whole task to `COMPLETED` when P4 `final_gate` is `PASS`, `PASS_WITH_WARNINGS`, or `COMPLETED`, without separate execution/verification/trust fields. Conversely, when browser evidence is absent it records `PARTIAL` before trying any static checks.
- `doctor.py` reports `self_test=PASS`; that means plugin health checks pass, not UI verification. `READY` means environment capability readiness, not task verification.
- P3 `COMPLETED` means all planned chunks were accepted in the P3 ledger and `ready_for_p4` is true; it does not mean P4 verification passed.
- Packaging/validator `PASS` values are validation of their own artifacts, not UI verification. Preserve these semantics and add context rather than globally renaming every `PASS` literal.

## 6. COMPLETED but not VERIFIED

P3 reports `COMPLETED` independently of P4. Tier 1 `run_ui_task` also has a task-level `COMPLETED` state after a P4 pass; it has no `execution_status`, `verification_status`, `trust_level`, evidence provenance, or trust ceiling. P4's report can mark only a subset of dimensions evaluated while still carrying overall `PASS`. Missing browser currently yields task `PARTIAL` without static fallback. These are the contract gaps to fix additively.

## 7. Current status semantics

- P3: `COMPLETED | PARTIAL | BLOCKED | DEVIATED` describes plan execution/ledger outcome.
- P4: `PASS | PASS_WITH_WARNINGS | PARTIAL | FAIL | BLOCKED`, with a narrower `final_gate` union. In practice missing evidence is returned as `BLOCKED`; some gate `PASS` values are local.
- Runtime: `COMPLETED | PARTIAL | FAILED | BLOCKED` describes capture process completion, not trust in the UI.
- Tier 1 task: `RUNNING | NEEDS_INPUT | NEEDS_PERMISSION | BLOCKED | DEVIATED | PARTIAL | COMPLETED | FAILED`; CHECK pass currently promotes to overall `COMPLETED`.
- Capability detection: `AVAILABLE`/`MISSING`/`UNKNOWN` plus Playwright readiness states; `doctor.overall_status` is `READY | PARTIAL | BLOCKED`.
- There is no canonical `VerificationStatus`, `TrustLevel`, trust ceiling, claim/evidence provenance schema, static report, or audit-status validator.

## 8. Reuse plan

Reuse P2's VerificationContract, P3 ImplementationReport/ledger/scope gates, P0 profiles/maps, runtime capability detector, existing `.evidence` store, P4/runtime critic, runtime/accessibility evidence formats, and existing repair routes. Reuse detected project commands and existing framework adapters; run only checks whose command/capability is confirmed.

## 9. Refactor plan

Add one trust/verification layer above the existing P4 engine: canonical six-level capability ladder and capability report; one strategy resolver; browser-independent static/build aggregation; claim provenance and trust classification; evidence-aware result validation; status-semantics audit; and additive integration into P4, `run_ui_task`, and `doctor`. Missing browser should lower achieved trust and produce a limitation, while available static/build checks continue. Keep runtime verification and visual critique in their current engines.

## 10. Behavior that must remain unchanged

Do not rewrite P0–P4, replace Playwright/runtime critic, create evidence storage, replace Tier 1's state machine/orchestrator, alter P2 reasoning, add arbitrary score/benchmark, add framework/domain/knowledge packs, install dependencies, or claim static signals as rendered proof. Existing repair routing and P0–P3 contracts must remain compatible. Only Tier 2 verification/trust behavior and its docs/tests/registries may be extended.

## Repository status-term audit scope

Scanned status literals and structured status builders across `uiux` Python/JSON, with targeted review of P4, runtime critic, executor, `doctor`, `run_ui_task`, evidence validators, registries, and related tests/evals. Important occurrences are classified above: local gate PASS, P4 final PASS, runtime critic PASS, plugin self-test PASS, environment READY, P3 COMPLETED, and task COMPLETED. These words are not globally interchangeable; user-facing claims need typed metadata and evidence provenance.
