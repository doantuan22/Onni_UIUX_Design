# Advanced Tool Flow

For a normal task, begin with `run_ui_task` and follow its returned action. The task state machine advances at most one phase per call. Continue with the returned `task_id`; supply a user response only when the action asks for input or permission. `DONE` requires a passing final review and completion evidence. See `AGENT-USAGE.md` for the adapter contract.

For direct analysis or controlled integration work, use the tool sequence below and retain returned artifacts:

1. `analyze_repository` and `detect_ui_state` establish P0 context.
2. `map_ui_structure` and `analyze_existing_ui` provide route/component and observed UI evidence when applicable.
3. `orchestrate_ui` resolves workflow, change level, permissions, and requirements.
4. `build_knowledge_plan` selects P1 references.
5. `plan_modification` returns diagnosis, bounded strategies, chunks, and validation steps.
6. Apply changes only through the host agent under the returned scope and permissions.
7. `build_validation_handoff`, `detect_runtime`, `run_runtime`, and `run_runtime_validation` establish evidence. If runtime is blocked, stop and report it.
8. Complete the review and evidence gates before claiming `DONE`.

The recorded Tier 3 smoke artifact calls stages 1, 3–5, and validation handoff on four local fixtures. It did not apply code changes, execute a browser, or complete the final task state machine. It is therefore labeled a blocked pipeline smoke rather than a completed tool workflow.
