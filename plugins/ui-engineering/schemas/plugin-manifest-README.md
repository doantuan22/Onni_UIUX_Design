# Plugin manifest

[plugin.json](../plugin.json) describes the package to any host platform without assuming one. It is **metadata only**: it points at core entry points (SKILL.md, `uiux.api`, registries) and never duplicates their content.

| Field | Meaning |
|---|---|
| `name`, `version`, `description` | Identity. `version` must equal the root `VERSION` file (single source; semantic versioning). |
| `entrypoints` | Skill instructions, knowledge entry, Core API module, unified CLI, and the tool ids behind each engine entry point. |
| `capabilities` | What the plugin offers, for host discovery. |
| `knowledge` | Knowledge registry and collections; hosts query through `retrieve_knowledge`, not file paths. |
| `tools` | Pointer to the tool registry (`uiux/core/tools.json`). |
| `evals` | Scenario location, automated vs agent-run suites, entry tool. |
| `runtime` | Optional runtime, readiness states and the no-install policy. |
| `requirements`, `optional_dependencies` | Python requirement (no Python packages); optional Node/Playwright/axe live in the *target* project and are never installed by the skill. |
| `compatibility` | Platform-neutral status of adapters and backward-compatible CLIs. `mcp` is the shared experimental stdio transport; Claude Code, Codex, Cline, OpenCode and Copilot remain planned. |

[plugin.schema.json](plugin.schema.json) is the structural contract; `tests/test_plugin_layer.py` validates the manifest against it (required fields, version format) and checks that every referenced path and tool exists.

## Versioning

- `VERSION` at the package root is the single source (currently `0.1.0`); `uiux.__version__` reads it, and the manifest must match.
- Semantic versioning: breaking change to the public API (`uiux.api`, tool ids/inputs, manifest schema, registry schema) → major; new tools, collections or knowledge entries → minor; fixes and content corrections → patch. While `0.y.z`, minor releases may still refine public contracts, and each such change is recorded in `CHANGELOG.md`.
- Git commit hashes are build metadata at most (e.g., `0.1.0+abc123`), never the version.
