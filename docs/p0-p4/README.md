# SEE → KNOW → THINK → DO → CHECK (P0–P4)

Design and audit records for the five-phase restructuring. Read the roadmap first.

| File | Phase | Notes |
|---|---|---|
| [SEE_KNOW_THINK_DO_CHECK_P0-P4.md](SEE_KNOW_THINK_DO_CHECK_P0-P4.md) | all | Roadmap and target architecture |
| [P0_Audit_Report.md](P0_Audit_Report.md) | P0 SEE | Capability matrix of the existing engine |
| [P1_Knowledge_Audit_Report.md](P1_Knowledge_Audit_Report.md), [P1_Knowledge_System_Complete.md](P1_Knowledge_System_Complete.md) | P1 KNOW | Knowledge catalog: domains, frameworks, components |
| [P2_REASONING_AUDIT_REPORT.md](P2_REASONING_AUDIT_REPORT.md), [P2_THINK_Engine_Complete.md](P2_THINK_Engine_Complete.md) | P2 THINK | `uiux/engine/modification_planner` |
| [P3_IMPLEMENTATION_AUDIT_REPORT.md](P3_IMPLEMENTATION_AUDIT_REPORT.md), [P3_Execution_Engine_Complete.md](P3_Execution_Engine_Complete.md) | P3 DO | `uiux/engine/executor` |
| [P4_VERIFICATION_AUDIT_REPORT.md](P4_VERIFICATION_AUDIT_REPORT.md), [P4_CHECK_Engine_Complete.md](P4_CHECK_Engine_Complete.md) | P4 CHECK | `uiux/engine/verification` |

Tests: `tests/test_p1_knowledge_routing.py`, `test_p2_reasoning.py`, `test_p3_executor.py`, `test_p4_verification.py`.

## Current status (integration)

- The `*_Complete.md` files describe each phase as first written. Where they differ, the code and tests win:
  - `guard_edits` never marks a chunk applied unless an edit for it passed every guard; `ready_for_p4` requires all chunks applied with no deviation.
  - `verify_implementation` reports design intent, responsive, interaction, accessibility and performance as `NOT_EVALUATED` (use `build_critic_report` for those); it does not claim `PASS`.
- Public tools: `plan_modification` → `check_execution_gate` → `guard_edits` → `verify_implementation`.
- `compare_plan_to_changes` (post-hoc drift audit) and `runtime_critic` (runtime critic / repair loop) remain supported.
- Known limits: diagnosis and strategy are keyword heuristics; the business-logic guard is a regex; no multi-project benchmark yet.
