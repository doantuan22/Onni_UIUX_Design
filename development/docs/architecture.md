# Architecture

The skill is deliberately split into orchestration, phase ownership, review gates, templates, and supporting documentation.

```text
SKILL.md (entry point and controller)
├─ workflow/ (routing, state, transitions, contracts, execution hardening)
├─ phase-1/ (router, UX structure engine, selectively loaded references)
├─ phase-2/ (router, eight frontend design engines, visual language, design inspiration,
│            typography, motion, web patterns, design knowledge system, capability resolver;
│            all selectively loaded)
├─ review/ (gate-specific loops)
├─ templates/ (artifact shapes and hardening records)
├─ evals/ (agent-agnostic evaluation framework and fixtures)
├─ execution/ (capability-driven rendered UI verification contracts)
├─ uiux/ (platform-neutral Python core: core foundation, knowledge, engine, runtime, evals, tooling, Core API)
├─ scripts/ (backward-compatible CLIs + unified CLI scripts/uiux_cli.py)
├─ plugin/ (plugin layer: manifest, adapters, packaging boundary; the core never depends on it)
└─ tests/ (standard-library test suite; not packaged)
```

`SKILL.md` operates as the primary entry point, directing requests through the UI Orchestrator (`uiux.api.orchestrate_ui`). The orchestrator leverages the Repo Intelligence layer (`uiux.api.analyze_repository`, see [phase-2.md](phase-2.md)) to extract evidence-based facts into a normalized `repo_profile`, determine the UI state (`GREENFIELD`, `PARTIAL_UI`, `EXISTING_UI`, `UNKNOWN`), and split into two dedicated workflows:
- **Greenfield Workflow** ([workflows/greenfield-workflow.md](../../plugins/ui-engineering/workflows/greenfield-workflow.md)): For brand-new projects or explicit rebuilds. Grounded design freedom with user constraints given top precedence.
- **Existing UI/UX Workflow** ([workflows/existing-ui-workflow.md](../../plugins/ui-engineering/workflows/existing-ui-workflow.md)): Enforces `PRESERVE FIRST → IMPROVE SECOND → REDESIGN ONLY WHEN EXPLICITLY REQUESTED` using the L1/L2/L3 Change Budget model and granular permissions ([workflows/preservation-rules.md](../../plugins/ui-engineering/workflows/preservation-rules.md)), backed by the **Existing UI Analyzer & Preservation Guard** (`uiux.api.analyze_existing_ui`, `evaluate_preservation`, see [phase-3.md](phase-3.md)).
- **Knowledge Router & Framework Packs** ([phase-4.md](phase-4.md)): Deterministic, context-efficient routing layer (`uiux.api.route_knowledge`) selecting framework/styling packs, design skills, preservation invariants, and runtime validation under a strict context budget.
- **Domain Design Packs** ([phase-5.md](phase-5.md)): Product and domain intelligence (`uiux.api.detect_domain`, `resolve_domain_pack`), multi-signal domain classification, task-aware subtopic routing, and 8 canonical Domain Design Packs operating at Level 6 precedence.
- **Implementation Planning & Controlled Editing** ([phase-6.md](phase-6.md)): Machine-readable planning and blast-radius control (`uiux.api.plan_modification`, `validate_modification_plan`, `evaluate_plan_permissions`, `compare_plan_to_changes`), L1/L2/L3 permission & justification gates, preservation boundaries, and plan drift detection.
- **Runtime Critic & Repair Loop** ([phase-7.md](phase-7.md)): Runtime verification, 7-dimensional inspection (visual regression, preservation invariants, responsive, states, accessibility, runtime errors, plan-drift), pre-existing vs new regression classification, bounded targeted repair, and minimal evidence recapture (`uiux.api.run_runtime_validation`, `build_critic_report`, `evaluate_runtime_result`, `build_repair_plan`, `run_targeted_repair`, `recapture_evidence`).

Each operational state loads only the relevant file(s), which keeps context narrow and makes future specialization additive. `workflows/` is the source of truth for lifecycle behavior; review files define gates; templates carry stable handoff metadata.

The central invariant is the structure lock: Phase 1 produces and owns structural decisions, then the lock freezes their active versions for Phase 2. If later work needs a structural change, workflow rolls back to Phase 1 and issues a new lock after review. This preserves a one-way artifact dependency graph and prevents Phase 2 from bypassing UX structure.

The execution hardening layer runs after routing and before phase work. It selects minimum sufficient context, resolves active/locked artifacts, prevents duplicate creation and re-analysis, detects stale downstream work, constrains scope, and protects review loops/completion. The evaluation layer is agent-agnostic: fixtures and E01–E28 scenarios test workflow and execution contracts without requiring a browser runtime. See [docs/hardening.md](hardening.md) and [evals/README.md](../../plugins/ui-engineering/evals/README.md).

The execution layer is selected only for rendered UI work when capability warrants it. It is independent of any agent API: adapters implement a browser contract, Playwright is reused only when already present, and manual fallback reports limitation honestly. Evidence flows into Phase 2 visual review and the final quality gate. See [docs/execution-layer.md](execution-layer.md).

Browser runtime evidence may feed the accessibility runtime: local axe scan evidence plus manual review flows through the Accessibility Gate before Final Quality Gate. It reuses execution session/server/viewport contracts and does not create a second browser lifecycle. See [docs/accessibility-runtime.md](accessibility-runtime.md).

The Design Knowledge System adds a knowledge layer (structured, schema-validated catalogs), a reasoning bridge (Capability Resolver), implementation intelligence (technology resolver, performance budget) and outcome evaluation (E65–E80 with a static analyzer and optional runtime motion probes). See [design-knowledge-system.md](design-knowledge-system.md).

The repository is plugin-ready: a layered `uiux` package exposes a public Core API, knowledge and tool registries, and portable resource discovery and configuration, while `plugin/` holds only integration metadata. See [plugin-architecture.md](plugin-architecture.md).
