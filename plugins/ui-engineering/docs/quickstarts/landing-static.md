# Quickstart: Static Landing Page

Fixture: `development/fixtures/targets/target-a-static` (static HTML/CSS/JS).

1. Start `run_ui_task` with a request that names the route/section, desired result, and preserved content/brand constraints.
2. Follow the returned action and keep its `task_id`. Inspect repository and UI-map artifacts before choosing a target.
3. Review the P2 requirement record and deterministic permission result. Vague “make it better” language does not grant redesign permission.
4. Apply only the returned bounded plan, then capture desktop/tablet/mobile evidence and run the final review.

The verified local trace is [tier3-plugin-pipeline-smoke.json](../../../../development/benchmark-runs/tier3-plugin-pipeline-smoke.json). Its landing fixture reached planning and emitted three execution chunks, then stopped at `BLOCKED_BROWSER_RUNTIME` (`NOT_DECLARED`). It contains no implementation or screenshot and is not a completed quickstart run.
