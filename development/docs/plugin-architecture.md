# Plugin-ready architecture

The repository is structured so it can later be packaged as a plugin for different agent hosts, **without** making the core depend on any host. This phase prepares the structure; it does not build or publish a package.

```text
             Plugin Layer            plugin/  (manifest, adapters, packaging)
                  │
          Adapter / Manifest         only uiux.api + manifest
                  │
                  ▼
               Core API              uiux/api.py, uiux/cli.py, scripts/uiux_cli.py
                  │
      ┌───────────┼───────────┐
      ▼           ▼           ▼
 Knowledge     Engine       Runtime     uiux/knowledge + catalogs · uiux/engine · uiux/runtime + execution/
      │           │           │
      └───────────┼───────────┘
                  ▼
                Evals                   uiux/evals + evals/
      (Tooling: uiux/tooling, scripts/ · Docs: docs/ · Tests: tests/)
```

## Layers

| Layer | Contents | Notes |
|---|---|---|
| **Plugin** | `plugins/ui-engineering/plugin.json`, `plugins/ui-engineering/adapters`, `plugins/ui-engineering/packaging` | Integration only; no design, knowledge, eval or runtime logic |
| **Core API** | `uiux/api.py`, `uiux/cli.py`, `uiux/__main__.py`, `scripts/uiux_cli.py` | The only surface adapters use |
| **Core foundation** | `uiux/core/` (resources, config, registries), `VERSION` | Imports no other layer |
| **Core skill** | `SKILL.md`, `workflow/`, `phase-1/`, `phase-2/` workflow and reasoning modules, `review/`, `templates/` | Instructions agents follow; platform-neutral Markdown |
| **Knowledge** | `uiux/knowledge/`, `phase-2/knowledge/`, `phase-2/motion/`, `phase-2/web-patterns/`, component grammars | Catalogs + generated `INDEX.md` and `registry.json` |
| **Design engine** | `uiux/engine/` (capability resolver, technology, retrieval, performance), resolver/technology/budget docs | Deterministic, stdlib-only |
| **Runtime engine** | `uiux/runtime/` (detection, browser runner, probes, evidence, accessibility), `execution/` contracts | Optional project-local Playwright |
| **Evaluation** | `uiux/evals/` (quality analyzer, resolver scenarios, eval runner), `evals/` | Automated suites + agent-run scenarios E01–E80 |
| **Tooling** | `uiux/tooling/validate.py`, `scripts/` (compatibility CLIs) | |
| **Docs / Tests** | `docs/`, `CHANGELOG.md` / `tests/` | Tests are not packaged |

Every file belongs to exactly one layer. The map is [uiux/core/layers.json](../../plugins/ui-engineering/uiux/core/layers.json) (first match wins), and `tests/test_architecture.py` fails on unclassified files.

### Why the Markdown did not move

The skill's Markdown is a set of path contracts: SKILL.md routing, around 400 relative links, the reference index, and `expected_context` in E01–E80. Moving `phase-2/knowledge` into a top-level `knowledge/` would change those contracts only to fit the new layout, which the brief ruled out. Location independence comes from the registries and the configured `paths` instead: a host asks for `style.swiss` or `retrieve_knowledge(collection="styles")`, never for a file path. A future relocation needs a config change plus a link rewrite; the API does not change.

## Dependency rules

Allowed imports (enforced by `tests/test_architecture.py`):

| Module | May import |
|---|---|
| `uiux.core` | nothing in `uiux` |
| `uiux.knowledge` | core |
| `uiux.engine`, `uiux.runtime`, `uiux.tooling` | core, knowledge |
| `uiux.evals` | core, knowledge, engine, runtime, tooling |
| `uiux.api`, `uiux.cli` | everything below |
| `plugin/**` | `uiux.api` (and `uiux.__version__`) only |

The core never imports the plugin layer. The whole-package validator checks plugin files only when `plugin/` exists, and a copy without `plugin/` passes `tests/test_plugin_layer.py::CoreWithoutPluginTests`.

## Entry points

| Entry | Where |
|---|---|
| Skill | `SKILL.md` |
| Knowledge | `phase-2/knowledge/README.md`, registry `phase-2/knowledge/registry.json`, tool `retrieve_knowledge` |
| Capability Resolver | tool `resolve_capabilities` (`uiux.api.resolve_capabilities`, `scripts/resolve_capabilities.py`) |
| Technology Resolver | tool `resolve_technology` |
| Quality Analyzer | tool `analyze_design_quality` (`scripts/analyze_design_quality.py`) |
| Runtime Runner | tools `detect_runtime`, `run_runtime` (`scripts/run_browser_execution.py`) |
| Evals | tool `run_evals`; agent-run scenarios in `evals/scenarios/` |
| Validation | tool `validate_skill` (`scripts/validate_skill.py`) |

## Public vs internal API

- **Public:** `uiux.api` functions (`resolve_capabilities`, `retrieve_knowledge`, `get_knowledge`, `knowledge_collections`, `resolve_technology`, `analyze_design_quality`, `detect_runtime`, `run_runtime`, `accessibility_scan`, `run_evals`, `validate_skill`, `capability_map`, `self_test`, `error_contract`, `error_envelope`, `list_tools`, `call_tool`, `describe_architecture`, `layer_of`, `version`, `get_config`, `reload_config`), the tool registry ids and JSON shapes, the manifest, the knowledge registry schema, and the `scripts/*.py` CLIs.
- **Internal:** `uiux.knowledge.catalog` (parser, schema validation), `uiux.core.registry`, `uiux.runtime.evidence`, `uiux.runtime.probes`, `uiux.tooling.validate` internals, `uiux.engine.retrieval` (listed in `layers.json` → `internal_modules`). Adapters must not import these.

## Configuration and resource discovery

- `uiux/core/resources.py` is the only place that knows where things live (`get_package_root`, `get_core_root`, `get_plugin_root`, `get_knowledge_root(s)`, `get_eval_root`, `get_runtime_root`, `get_templates_root`, …). The root derives from the package location or `UIUX_ROOT`, never from the working directory.
- `uiux/core/config.py` merges `uiux/core/defaults.json` → `uiux.config.json` (package root, not packaged) → the file in `UIUX_CONFIG` → caller overrides. Sections: `paths`, `browser`, `dependency_policy`, `motion_budget`, `performance_budget`, `feature_flags`. Paths must be relative with no `..`, and `dependency_policy.auto_install` must stay `false`.
- The legacy scripts keep their names and CLIs. `scripts/_bootstrap.py` puts the package root on `sys.path` and aliases the old module names (`import knowledge_lib`) to the implementation modules.

## Registries

- **Knowledge registry** (`phase-2/knowledge/registry.json`, generated by `python scripts/knowledge_lib.py index` together with `INDEX.md`): every catalog entry and component grammar with id, kind, collection, category, name, file, line and summary. Query it through `uiux.knowledge.registry` or `retrieve_knowledge`. Collections: styles, layouts, screens, motion, interactions, effects, recipes, graphics, technologies, components.
- **Tool registry** (`uiux/core/tools.json`): id, description, entrypoint (`uiux.api:<fn>`), CLI, closed input schema, output, dependencies, runtime requirements, side effects and platform-neutral annotations. `call_tool` validates required/unknown arguments, scalar and nullable types, enums, arrays and declared nested objects before dispatching.
- **Capability map** (`uiux/core/capabilities.json`, exposed by `uiux.api.capability_map`): maps every manifest capability to its registered tools and instruction files. The API derives `static` versus `runtime-dependent` from tool annotations; with a project it also reports `AVAILABLE`/`BLOCKED` from the read-only runtime detector, and otherwise reports `UNKNOWN` rather than guessing.

## Error and health contracts

Invalid calls retain the 0.x JSON fields `status` and string `error`, plus additive `error_code`, `category` and `remediation`. The centralized taxonomy is [uiux/core/errors.json](../../plugins/ui-engineering/uiux/core/errors.json). Unexpected public-boundary failures become `ERROR` / `INTERNAL_ERROR`; tracebacks stay out of JSON and are printed only with `UIUX_DEBUG=1`.

`uiux.api.self_test()` is a fast, read-only health report. It checks versions, the optional plugin manifest when present, tool/capability/knowledge registries, public API bindings, the error contract and runtime detection. Missing Node/Playwright/browser capability is `BLOCKED`, not a failed package health check. A core-only artifact reports the optional manifest check as `SKIPPED`.

## Optional runtime dependencies

Playwright, Node and axe belong to the *target project*. The skill never imports, installs or downloads them. Importing `uiux.api` loads no runtime module. Readiness is classified from the filesystem:

| State | Meaning | Runner result |
|---|---|---|
| `NOT_DECLARED` | No Playwright package in `package.json` | `BLOCKED` / `PLAYWRIGHT_IMPORT_FAILURE` |
| `DECLARED_NOT_INSTALLED` | Declared but not in `node_modules` (project or ancestors) | `BLOCKED` / `PLAYWRIGHT_IMPORT_FAILURE` |
| `PACKAGE_AVAILABLE_BROWSER_MISSING` | Package resolvable, no browser build in the Playwright cache | `BLOCKED` / `PLAYWRIGHT_BROWSER_UNAVAILABLE` (config `browser.preflight_browser_check` can disable this preflight) |
| `READY` | Package and browser build present | Capture runs |

`accessibility_scan` is a public tool with the same `runtime_state` gate. `NOT_DECLARED` and `DECLARED_NOT_INSTALLED` produce `BLOCKED` / `PLAYWRIGHT_IMPORT_FAILURE`; `PACKAGE_AVAILABLE_BROWSER_MISSING` produces `BLOCKED` / `PLAYWRIGHT_BROWSER_UNAVAILABLE`; only `READY` proceeds to the axe availability/readiness checks. It never installs a package or downloads a browser.

## Manifest and versioning

See [plugins/ui-engineering/schemas/plugin-manifest-README.md](../../plugins/ui-engineering/schemas/plugin-manifest-README.md). `VERSION` (`0.1.0`) is the single source, and the manifest, `uiux.__version__` and `CHANGELOG.md` must agree (tested). The project uses semantic versioning; commit hashes are build metadata at most.

## Adapter model

Adapters follow [plugins/ui-engineering/adapters/CONTRACT.md](../../plugins/ui-engineering/adapters/CONTRACT.md): `describe`, `instructions`, `call(tool_id, params)` and `configure`, using only `uiux.api` and the manifest. The [generic adapter](../../plugins/ui-engineering/adapters/generic/README.md) is a working JSON adapter and the template for platform adapters. The shared [MCP stdio transport](../../plugins/ui-engineering/adapters/mcp/README.md) is experimental and also uses only `uiux.api`; it exposes tools, not a host-specific integration.

**Adding an adapter:** create `plugins/ui-engineering/adapters/<platform>/` with a README and code, map host tools 1:1 to tool ids, pass host settings through `UIUX_CONFIG`, keep the runtime optional, add a test, and set its status in `plugin.json` → `compatibility.adapters`. Planned hosts: claude-code, codex, cline, opencode, copilot.

## Packaging boundary

[plugins/ui-engineering/packaging/package-rules.json](../../plugins/ui-engineering/packaging/package-rules.json) plus the layer map define the package. Run `python plugins/ui-engineering/packaging/package_files.py [--list]` for a dry run. Tests, caches, `.pyc`, runtime evidence, browser captures, helper temporaries, benchmark and eval outputs, logs and local config are excluded. The next phase builds archives from that list only; see [plugins/ui-engineering/packaging/README.md](../../plugins/ui-engineering/packaging/README.md).

## Building and verifying artifacts

Release archives are built deterministically from a clean commit, and verified after extraction, by `plugins/ui-engineering/packaging/build.py` and `verify.py`. See [plugins/ui-engineering/packaging/README.md](../../plugins/ui-engineering/packaging/README.md) and the phase plan in [plugin-packaging-spec.md](plugin-packaging-spec.md).

## Verification

```bash
python -m unittest discover -s tests -t tests          # add absolute paths to run from any directory
python scripts/validate_skill.py                        # whole package, independent of the working directory
python plugins/ui-engineering/packaging/package_files.py               # packaging boundary
python scripts/uiux_cli.py call run_evals                   # automated eval suites
```
