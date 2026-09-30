# Quickstart: React Dashboard

Fixture: `development/fixtures/targets/target-b-react` (React dashboard; its manifest does not declare Tailwind).

1. Start `run_ui_task` with the exact dashboard area, such as mobile navigation or search filter, and state which data/behavior must remain intact.
2. Read the P0 route/component map and selected P1 references. If more than one dashboard surface matches, resolve the target before editing.
3. Inspect `must_keep`, `must_change`, `must_not_change`, and the granular permission fields in the P2 record.
4. Apply the plan through the host agent. Validate desktop and mobile behavior, keyboard use, and preserved dashboard data before final review.

The real pipeline smoke reached planning with three chunks. Runtime validation stopped at `BLOCKED_BROWSER_RUNTIME`; no code was applied. See the linked trace in [BENCHMARK_REPORT.md](../BENCHMARK_REPORT.md).
