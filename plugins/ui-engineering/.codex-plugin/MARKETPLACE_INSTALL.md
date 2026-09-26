# Codex local marketplace installation

## Status

```text
Codex adapter: IMPLEMENTED / STRUCTURALLY VERIFIED / PORTABILITY HARDENED
Implementation phase: CLOSED
Adapter status: experimental
Codex Marketplace: IMPLEMENTED / STRUCTURALLY VERIFIED
Codex Marketplace Live Host Test: NOT_RUN
CODEX_VSCODE_MARKETPLACE_SUPPORT = NOT_CLAIMED
```

## Repository marketplace (from GitHub)

The repository root carries `.agents/plugins/marketplace.json` (marketplace `ui-engineering`) whose
plugin source is `./plugins/ui-engineering`; that directory contains `.codex-plugin/plugin.json`,
`.codex-plugin/mcp.json` and `skills/ui-ux-workflow/SKILL.md`. Clone the repository and add it:

```bash
git clone https://github.com/doantuan22/Onni_UIUX_Design.git
codex plugin marketplace add ./Onni_UIUX_Design
```

The plugin identifier is `ui-ux-design@ui-engineering`. This layout is structurally tested
(`tests/test_github_install.py`); a live Codex host install has not been run.

## Build and verify

From the repository root:

```bash
python plugins/ui-engineering/.codex-plugin/export.py --dev --source plugins/ui-engineering --out dist/dev/adapters
python plugins/ui-engineering/.codex-plugin/verify.py --bundle dist/dev/adapters/ui-ux-design-0.1.0-dev-codex.zip
python plugins/ui-engineering/.codex-plugin/verify.py --marketplace --bundle dist/dev/adapters/ui-ux-design-0.1.0-dev-codex-marketplace.zip
```

Extract `ui-ux-design-0.1.0-dev-codex-marketplace.zip`. Its root contains:

```text
<marketplace-root>/
├── .agents/plugins/marketplace.json
└── plugins/ui-ux-design/
    ├── plugin.json
    ├── mcp.json
    ├── VERSION
    ├── skills/ui-ux-workflow/SKILL.md
    ├── uiux/
    └── adapters/, packaging/, schemas/, …
```

The marketplace artifact is assembled from the same generic payload and Codex overlay as the separately verified Codex bundle; it does not rebuild the core payload. ZIP timestamps, ordering, permissions, and JSON serialization are deterministic.

## Add, inspect, upgrade, and remove

Use an extracted directory, not the ZIP file:

```bash
codex plugin marketplace add <marketplace-root>
codex plugin marketplace list
codex plugin marketplace upgrade uiux-local
codex plugin marketplace remove uiux-local
```

The CLI commands manage marketplace discovery. Official OpenAI documentation directs local-plugin installation and end-to-end host testing through the Plugins Directory in the ChatGPT desktop app; this repository does not mutate user configuration or run those commands in tests.

## Repo-scoped marketplace

For a project-local source, retain this layout:

```text
PROJECT/
├── .agents/plugins/marketplace.json
├── .codex/config.toml
└── plugins/ui-ux-design/
```

Copy [`templates/config.toml`](templates/config.toml) to the project's `.codex/config.toml` (or merge its table):

```toml
[plugins."ui-ux-design@uiux-local"]
enabled = true
```

Codex loads project config only for trusted projects. The key is always `plugin-name@marketplace-name`; this marketplace therefore uses `ui-ux-design@uiux-local`.

## Personal marketplace (optional)

OpenAI documents a personal catalogue at `~/.agents/plugins/marketplace.json`, commonly with the plugin under `~/.codex/plugins/ui-ux-design/`. These paths are documentation only: the build, verifier, and tests never create or modify any home-directory file, including `~/.codex/config.toml`.

## Troubleshooting

- **Marketplace missing:** confirm extraction preserved `.agents/plugins/marketplace.json`, then run `codex plugin marketplace list`.
- **Invalid source:** `source.path` must be `./plugins/ui-ux-design`, use `/` separators, and remain inside the marketplace root.
- **Plugin not enabled:** add the quoted `ui-ux-design@uiux-local` table in trusted project's `.codex/config.toml`.
- **Stale local snapshot:** replace the extracted artifact and run `codex plugin marketplace upgrade uiux-local`.
- **Python or MCP fails to start:** install a compatible Python 3 interpreter reachable as `python3`; no runtime or dependency is bundled or auto-installed.

## Documentation verification

Docs verified date: **2026-09-25**.

- OpenAI marketplace contract: top-level `name`, `interface.displayName`, `plugins[]`, `source: { source: "local", path: "./..." }`, installation/authentication policy, and category are documented in [Package your plugin](https://developers.openai.com/plugins/build/plugins).
- Supported local surfaces documented there are Codex CLI for marketplace authoring/discovery and Codex in the ChatGPT desktop app / Work mode for marketplace browsing and local plugin install. VS Code marketplace support is not claimed.
