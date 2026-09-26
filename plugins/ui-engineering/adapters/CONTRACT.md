# Adapter contract

An adapter connects one host platform (an agent runtime or IDE assistant) to the platform-neutral core. It is **integration code only**: no design logic, no knowledge, no eval or runtime reimplementation.

## Allowed dependencies

- `uiux.api` (public Core API) and `uiux.__version__`: nothing else from `uiux`.
- The manifest (`plugins/ui-engineering/plugin.json`) and the host platform's own SDK.
- Enforced by `tests/test_architecture.py` (imports inside `plugin/` are scanned).

## Required operations

| Operation | Must do | Core call |
|---|---|---|
| `describe()` | Return name, version, capabilities, entry points and tool list from the manifest and the tool registry | `uiux.api.version()`, `uiux.api.list_tools()` |
| `instructions()` | Tell the host where the skill instructions start (`SKILL.md`) and how to load knowledge progressively | manifest `entrypoints.skill`, `entrypoints.knowledge` |
| `call(tool_id, params)` | Invoke a registered tool with JSON parameters and return JSON | `uiux.api.call_tool(tool_id, params)` |
| `configure(overrides)` | Pass host settings (paths, browser behavior, dependency policy, budgets, flags) as a config file named by `UIUX_CONFIG` or `uiux.config.json` | `uiux.core` config layer via environment, never by patching code |

## Rules

1. **Map, don't reimplement.** Host "tools" or "commands" map 1:1 to tool-registry ids; inputs/outputs are the registry's JSON shapes.
2. **Paths stay relative.** Resolve the package root from the adapter's own location or `UIUX_ROOT`; never embed machine paths.
3. **Optional runtime stays optional.** Do not import or install Playwright, Node packages or browsers. Surface `BLOCKED` results and `runtime_state` honestly.
4. **Errors are data.** `uiux.api.ToolError` keeps the 0.x `status`/string `error` fields and adds `error_code`, `category` and `remediation`; map it to the host's invalid-argument error while retaining that envelope as structured content. Tool results with status `FAIL`/`BLOCKED` are returned, not raised. Unexpected failures are `ERROR` / `INTERNAL_ERROR`, never a public traceback.
5. **No startup side effects.** Importing the adapter must not spawn processes or touch the network.
6. **Versioned.** An adapter declares the manifest `version` range it supports and fails fast outside it.
7. **Discover, do not inspect internals.** Hosts obtain tool schemas/annotations from `uiux.api.list_tools`, capabilities from `uiux.api.capability_map`, health from `uiux.api.self_test`, and taxonomy from `uiux.api.error_contract`.

## Adding an adapter

1. Create `plugins/ui-engineering/adapters/<platform>/` with a README (host version, install and registration steps, mapping table) and the adapter code.
2. Implement the four operations above using only `uiux.api` and the manifest.
3. Add the adapter's status in `plugins/ui-engineering/plugin.json` → `compatibility.adapters` (`skeleton`, `experimental`, `supported`).
4. Add a test that loads the adapter and calls `describe()` and at least one read-only tool (`retrieve_knowledge`), and include it in the import-boundary scan.
5. Do not mark an adapter `supported` until it has been exercised on the real host platform.
