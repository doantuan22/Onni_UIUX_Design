# Agent usage

**Default rule:** use `run_ui_task` for normal UI work.

1. Call `run_ui_task` with `request`.
2. Read `status`.
3. Follow `next_action` exactly.
4. Reuse the returned `task_id` on every continuation.
5. Do not manually construct internal artifacts.
6. Stop when `next_action.type` is `DONE`.
7. If the action is `PROVIDE_INPUT` or `GRANT_PERMISSION`, ask for exactly the requested user input; pass the answer as `user_message`.
8. Use low-level tools only for debugging or explicit advanced workflows.

Each call advances at most one phase. `verbosity` is `compact` by default; use `standard` for summaries or `full` to inspect the canonical artifacts for the current response. Task state and artifacts are referenced from `<project>/.evidence/uiux-tasks/<task_id>/`.

`PARTIAL` means a required runtime/evidence capability is unavailable or a phase is incomplete. `BLOCKED`, `NEEDS_INPUT`, `NEEDS_PERMISSION`, and `DEVIATED` include an actionable `next_action`. The tool never installs dependencies or writes application source files. P3 validates and records changes made by the host agent; P4 needs actual rendered evidence to pass browser checks.

For project diagnostics, call `doctor(project=".")` or run `uiux doctor --project .`. Doctor is read-only and reports capability impacts; it does not install packages or download browsers.
