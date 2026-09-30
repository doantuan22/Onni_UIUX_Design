# Quickstart: Runtime Review

1. Use `build_validation_handoff` to obtain required routes, states, and viewports.
2. Call `detect_runtime` before capture. If the state is not `READY`, report the specific blocker and do not claim a browser pass.
3. When ready, capture before/after evidence with `run_runtime`; include responsive and reduced-motion cases when requested by the handoff.
4. Submit evidence to `run_runtime_validation`, resolve regressions, and complete the required review artifacts.

In the four real Tier 3 pipeline smoke calls, Playwright was `NOT_DECLARED`, each critic returned a critical insufficient-evidence issue, and all runs were blocked. See [the run trace](../../../../development/benchmark-runs/tier3-plugin-pipeline-smoke.json).
