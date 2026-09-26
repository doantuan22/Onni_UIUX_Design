# Execution layer

The execution layer is agent-agnostic and supports rendered Phase 2 verification without assuming a particular browser API. It begins with read-only capability detection, then selects the best existing strategy: agent browser capability, project Playwright, compatible automation, lightweight local mechanism, or truthful manual fallback.

Runtime detection resolves documented command, package script, configuration, then safe inference; it reuses an already responding URL and records server ownership. Readiness requires an observable response/root signal rather than a blind delay. Browser adapters expose open/navigate/viewport/readiness/capture/basic inspection/close, and target only routes from task scope, Page Specs, or Implementation Map.

Evidence attaches semantic route and viewport IDs, session/iteration, render/basic DOM state, optional console observations, and errors to screenshots/captures. Rendered UI requires execution evidence whenever capability exists. Missing capability becomes `NOT_EXECUTED`, `LIMITED`, or `BLOCKED`, never a visual pass. Owned servers and browser sessions are cleaned up; user-owned processes remain untouched.

See [execution README](../../plugins/ui-engineering/execution/README.md), [capability detection](../../plugins/ui-engineering/execution/capability-detection.md), [strategy router](../../plugins/ui-engineering/execution/execution-router.md), [browser contract](../../plugins/ui-engineering/execution/browser-contract.md), [evidence contract](../../plugins/ui-engineering/execution/evidence-contract.md), and [failure handling](../../plugins/ui-engineering/execution/failure-handling.md).
