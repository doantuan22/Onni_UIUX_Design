# Plugin schemas

| Schema | Describes | Produced by | Checked by |
|---|---|---|---|
| [package-manifest.schema.json](package-manifest.schema.json) | `PACKAGE-MANIFEST.json`, embedded in every artifact and published next to it: identity, provenance and per-file sha256 | `plugins/ui-engineering/packaging/build.py` | `plugins/ui-engineering/packaging/verify.py` (V1) |
| [build-info.schema.json](build-info.schema.json) | `<artifact>.build-info.json`: the build environment record (outside the archive, not in `SHA256SUMS`) | `build.py` | tests |
| [adapter.schema.json](adapter.schema.json) | Host-neutral adapter metadata, including the MCP protocol pin/method list when an adapter exposes `mcp-stdio` | adapter metadata | V10 / tests |
| [orchestrator.schema.json](orchestrator.schema.json) | UI Orchestrator machine-readable contract: inputs, routing outputs, UI state, change budgets (L1/L2/L3) and preservation rules | `uiux.engine.orchestrator` | `tests/test_orchestrator.py` |
| [repo-profile.schema.json](repo-profile.schema.json) | Repo Intelligence normalized repository profile: framework, styling, routes, components, tokens, UI state, and runtime capabilities | `uiux.engine.repo_intelligence` | `tests/test_repo_intelligence.py` |
| [existing-ui-profile.schema.json](existing-ui-profile.schema.json) | Existing UI Analyzer comprehensive profile: identity, layout, components, UX flows, responsive, accessibility, and design system | `uiux.engine.existing_ui` | `tests/test_existing_ui.py` |
| [preservation-profile.schema.json](preservation-profile.schema.json) | Baseline preservation requirements, protected invariants, allowed change budgets (L1/L2/L3), and merged user permissions | `uiux.engine.existing_ui` | `tests/test_existing_ui.py` |
| [preservation-evaluation.schema.json](preservation-evaluation.schema.json) | Preservation Guard evaluation output: pass/warn/fail status, rule violations, and justification traces | `uiux.engine.existing_ui` | `tests/test_existing_ui.py` |
| [knowledge-plan.schema.json](knowledge-plan.schema.json) | Knowledge Router machine-readable load plan: framework/styling packs, design skills, preservation context, budget, and runtime validation | `uiux.engine.knowledge_router` | `tests/test_knowledge_router.py` |
| [modification-plan.schema.json](modification-plan.schema.json) | Modification Planner machine-readable plan: scope, blast radius, change classification (L1/L2/L3), steps, checkpoints, and validation | `uiux.engine.modification_planner` | `tests/test_modification_planner.py` |
| [change-manifest.schema.json](change-manifest.schema.json) | Controlled Editing change manifest: modified/created/deleted files, unexpected changes, drift detection, and actual change levels | `uiux.engine.modification_planner` | `tests/test_modification_planner.py` |
| [critic-report.schema.json](critic-report.schema.json) | Phase 7 Runtime Critic report: multi-dimensional inspection, regressions, plan-drift, pre-existing vs new issues, and repair recommendations | `uiux.engine.runtime_critic` | `tests/test_runtime_critic.py` |
| [repair-plan.schema.json](repair-plan.schema.json) | Phase 7 Targeted Repair plan: scoped repair actions, blocked violations, scope constraints, and evidence recapture plan | `uiux.engine.runtime_critic` | `tests/test_runtime_critic.py` |

The plugin manifest schema is [plugin.schema.json](plugin.schema.json). Validation uses the JSON Schema subset implemented in `plugins/ui-engineering/packaging/artifact.py` (`validate_schema`), so no third-party validator is needed.
