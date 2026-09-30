# Tier 3 Reasoning Audit

Audit date: 2026-09-30  
Scope: P2 Modification Planner and upstream requirement/context signals only. This file was created before Tier 3 implementation changes.

## Current capability map

| Capability | Existing implementation | Audit finding |
|---|---|---|
| Request intent | `uiux/engine/knowledge_router/intent.py` | Deterministic ordered regex patterns; returns one primary plus at most three secondary intents. Compound meaning is truncated and phrase order can affect primary intent. Vietnamese support covers a small vocabulary. |
| Permission/negation | `uiux/engine/modification_planner/semantic_parser.py`, `uiux/engine/preservation.py`, `change_classifier.py` | Existing action-scoped parser distinguishes mentioned/requested/prohibited/explicitly allowed, with prohibition precedence. This is a valuable deterministic safety guard. It is still regex/clause based, has a finite phrase catalog, and does not produce a canonical semantic requirement object or field-level provenance. |
| Scope | `scope_resolver.py` | Uses named page/component/application patterns, requested scope and monorepo signals. It suppresses vague requests from expanding to global, but defaults and substring checks can still select an incorrect target or insufficient-context result. |
| Surface mapping | `surface_resolver.py` | Uses repo files, components, routes and page inventory. It also invents `/{target_entity}` when a page target was not found in the graph, contrary to the desired grounded-candidate behavior. Fallback file selection can choose generic UI files. |
| Change level and permissions | `change_classifier.py`, `preservation.py`, `planning_gate.py` | L1/L2/L3, granular preservation and L3 checks are already deterministic and must remain authoritative. Several decisions still derive from keyword/parser output. PlanningGate validates presence/status, but does not validate reasoning completeness or provenance. |
| Diagnosis | `diagnosis.py` | Keyword presence creates generic conclusions (e.g. any “mobile” means possible overflow; “modernize” means visual presentation lacks modern hierarchy). `ui_context` and `knowledge_plan` are accepted but barely used as evidence. Generic issue fallback is not explicitly marked UNKNOWN. Confidence is a float assigned by rule, not calibrated. |
| Strategy | `strategy.py` | Category-to-template mapping emits generic flex/grid, CTA and hierarchy advice. Knowledge trace can point to `universal_fallback` or the first selected domain/framework pack without showing a direct diagnosis-to-knowledge-to-constraint chain. |
| Plan/chunks | `planner.py`, `step_planner.py`, `schemas.py` | P2 attaches a second, additive contract to the legacy plan. Requirement fields `explicit_requirements`, `preservation_requests` and `decision_trace` are empty. Chunk descriptions are generated with a fallback string, but can still become near-empty when target/action are absent; scope and verification fields may be generic. |
| Knowledge selection | `knowledge_router/router.py`, `domain_registry.py`, intent classifier | Reuses P1 catalogs and domain/framework routing. Routing contains many phrase/keyword checks, limits secondary intents and sometimes selects based on literal terms. It is useful as a deterministic candidate generator, not semantic ground truth. |
| Workflow/context | `task_orchestrator.py`, P0 repo/UI analysis, P2 planner | `run_ui_task` supplies repo/UI context and workflow; direct planning callers can default to `existing-ui`. The planner does not itself detect language or establish a structured evidence hierarchy for those inputs. |

## Heuristic inventory and allowed role

- **Classification hints:** intent regexes, domain keyword matching, request term matching, scope patterns and task-intent defaults.
- **Deterministic guards:** explicit prohibition and L3 checks, preservation locks, framework/library restrictions, business-logic boundary, file grounding, PlanningGate and execution permission validation. Keep these authoritative.
- **Fallback behavior:** generic intent, default viewport/checks, generic diagnosis, first matching route/file and universal knowledge fallback. These must be labeled as heuristic/unknown rather than presented as semantic findings.
- **Reasoning substituted by heuristic:** diagnosis conclusion, target surface inference when P0 graph is available, strategy text, affected page fallback, compound concern extraction and design freedom/permission interpretation beyond covered phrases.

Keyword families found include `mobile`, `responsive`, `modernize`, `clean`, `improve`, `polish`, `landing`, `checkout`, `dashboard`, `redesign`, `rebuild`, Vietnamese `làm đẹp`, `hiện đại`, `nâng cấp`, `đồng bộ`, `giữ nguyên`, `không đổi`, `thiết kế lại`, `đập đi làm lại`, `trợ năng`, `bố cục`, `toàn bộ`, and mixed English/Vietnamese phrases. Occurrences in deterministic policy guards are not all defects; interpretation rules in diagnosis/scope/strategy are the highest-risk cases.

## Gaps

- **Vietnamese:** selected terms are recognized, but many required phrases are absent or only work through substring/regex coincidences. Accented/unaccented variants are uneven. “đập đi làm lại” and “được phép đổi bố cục” are not consistently modeled as target-scoped permissions.
- **Mixed language:** some permission aliases are bilingual, but there is no `EN`/`VI`/`MIXED`/`OTHER` language field and mixed clauses are not normalized into concerns.
- **Compound requests:** intent classifier caps secondary intents at three; the planner's requirement profile stores no extracted requirements; validation booleans are aggregated, so preservation, responsive, consistency and accessibility concerns can collapse into one diagnosis.
- **Ambiguous requests:** “make it better” can receive a generic visual diagnosis; scope fallback may over- or under-specify. A uniquely selected P0 page is not consistently carried through a grounded match; an unmatched page can be synthesized as a route.
- **Diagnosis quality/completeness:** conclusions are not supported by P0 evidence references; descriptions and surfaces are generic; `is_inferred` is not paired with explicit UNKNOWN/reason; float confidence values look more precise than the rule warrants.
- **Strategy traceability:** strategy does not reliably point to a specific diagnosis, evidence ref, applicable P1 knowledge id, repository constraint, target, expected result and permitted change level.
- **Empty/default risks:** direct planner defaults to `general_ui`; missing intent/context often gets generic diagnosis; `requested_scope` defaults to `global`; step targets can be empty; affected pages/routes can be empty or synthetic; decision trace is always empty.
- **Model reasoning:** no provider abstraction or model reasoning service was found in P2. Tier 3 should expose structured context/rationale for the host coding agent, not add a direct external model call.

## Heuristics to retain

Keep keyword/regex logic for classification hints, deterministic safety guards and an explicitly labeled fallback when structured semantic interpretation is unavailable. Preserve `semantic_parser` action prohibition precedence and the existing L1/L2/L3, palette, framework, scope and business-logic guards. Improve the semantic layer around these contracts instead of rewriting P2.

## Benchmark targets

Measure grounded repo/surface selection, P1 knowledge relevance, completeness of extracted concerns, scope creep, permission correctness, framework/preservation drift, chunk completeness, verification/repair routing, regression outcomes, language parity and context/tool usage. Do not use beauty/preference as the primary metric. Baseline and plugin runs must share a fixture, task, starting tree, environment and grading rules; results must carry provenance and report blocked cases without numeric scores.
