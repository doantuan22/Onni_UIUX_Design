# Claude Code adapter

Status: **experimental** (structurally verified; local-marketplace install verified with the Claude Code CLI; interactive session test not yet run)

This adapter bundles the platform-neutral UI/UX Design Skill as a Claude Code plugin with MCP tool exposure through the shared stdio transport. It contains no design, knowledge, eval or runtime logic (see [CONTRACT.md](../CONTRACT.md)).

## Plugin structure

```text
<plugin-root>/
├── .claude-plugin/
│   ├── plugin.json          # Claude plugin manifest (committed; also rendered into bundles)
│   └── export.py, verify.py, templates/   # adapter tooling
├── .mcp.json                 # MCP server declaration for the shared transport
├── SKILL.md                  # Canonical workflow controller
├── skills/
│   └── ui-ux-workflow/SKILL.md   # Discoverable skill entry; delegates to ../../SKILL.md
├── plugin.json, VERSION, CHANGELOG.md
├── uiux/                     # Core package
├── adapters/                 # Generic adapter, shared MCP transport, adapter contract
├── packaging/, schemas/      # Artifact build/verification and JSON schemas
├── workflows/, review/, templates/   # Workflow definitions, review gates, artifact templates
├── knowledge/                # Design Knowledge System
├── execution/                # Execution contracts
├── evals/                    # Eval scenarios and fixtures
├── docs/                     # Documentation
└── scripts/                  # CLI tools
```

The plugin root IS the package root (`plugins/ui-engineering/` in the repository). `SKILL.md` and all its relative links work without rewriting.

## Name mapping

| Context | Name | Source |
|---|---|---|
| Skill name (frontmatter) | `ui-ux-workflow` | `SKILL.md` |
| Package / plugin id | `ui-ux-design` | `plugins/ui-engineering/plugin.json` |
| Claude plugin name | `ui-ux-design` | `.claude-plugin/plugin.json` |
| MCP server name | `ui-ux-design-mcp` | `.mcp.json` key |
| Python package | `uiux` | `uiux/` |

## Installation

See [VSCODE_INSTALL.md](VSCODE_INSTALL.md) for full installation and VS Code setup instructions.

### From GitHub (repository marketplace)

The repository root carries `.claude-plugin/marketplace.json` (marketplace `ui-engineering`, source `./plugins/ui-engineering`):

```bash
claude plugin marketplace add doantuan22/Onni_UIUX_Design
claude plugin install ui-ux-design@ui-engineering
```

Inside Claude Code the same is `/plugin marketplace add doantuan22/Onni_UIUX_Design` then `/plugin install ui-ux-design@ui-engineering`.
A local clone works the same way: `claude plugin marketplace add /path/to/Onni_UIUX_Design`.

### Development (recommended for testing)

```bash
claude --plugin-dir plugins/ui-engineering        # from a clone
claude --plugin-dir <path-to-extracted-bundle>     # from an exported bundle
```

The agent will discover `SKILL.md`, connect to the MCP server, and expose all public tools.

### Local Marketplace Installation

1. Build the marketplace bundle: `python plugins/ui-engineering/.claude-plugin/export.py --dev --source plugins/ui-engineering --out dist/dev/adapters/`
2. Extract `dist/dev/adapters/ui-ux-design-<version>-dev-claude-marketplace.zip`
3. Add marketplace: `claude plugin marketplace add <extracted-directory>`
4. Install plugin: `claude plugin install ui-ux-design@uiux-local`

Marketplace metadata uses the stable identity `uiux-local` and the required owner
object `{ "name": "UIUX Local" }`. The installation identifier is therefore
always `ui-ux-design@uiux-local`; the marketplace verifier (M1-M16) rejects a
name, owner, or source-path drift.

## MCP configuration

The `.mcp.json` at the plugin root declares one MCP server:

```json
{
  "mcpServers": {
    "ui-ux-design-mcp": {
      "command": "python3",
      "args": ["${CLAUDE_PLUGIN_ROOT}/adapters/mcp/server.py"],
      "env": {}
    }
  }
}
```

- `${CLAUDE_PLUGIN_ROOT}` is resolved by Claude Code to the plugin installation directory
- The command launches the **shared** MCP stdio transport; no second MCP implementation exists
- On Windows, `python3` may need to be `python` or `py -3` — see Python runtime below

## Python runtime

The plugin requires Python 3.9+ on PATH. No Python runtime is bundled or auto-installed.

| OS | Typical executable | Notes |
|---|---|---|
| Linux | `python3` | Most distributions ship `python3` |
| macOS | `python3` | Homebrew, system, or pyenv `python3` |
| Windows | `python` or `py -3` | Python Launcher for Windows (`py`) is standard |

If Python is not found, the MCP server will fail to start and Claude Code will report the MCP server as unavailable. The error message will indicate that Python 3 is required.

**To configure a non-standard Python path**, edit `.mcp.json` in the extracted bundle:

```json
{
  "mcpServers": {
    "ui-ux-design-mcp": {
      "command": "/path/to/python3",
      "args": ["${CLAUDE_PLUGIN_ROOT}/adapters/mcp/server.py"],
      "env": {}
    }
  }
}
```

## Tool exposure

All public tools are exposed through MCP `tools/list`:

| Tool | Read-only | Description |
|---|---|---|
| `resolve_capabilities` | ✓ | Turn a design profile into a capability plan |
| `retrieve_knowledge` | ✓ | Query the Design Knowledge System (248 entries, 10 collections) |
| `resolve_technology` | ✓ | Choose the simplest technology for capabilities |
| `analyze_design_quality` | ✓ | Static design quality analysis (E65-E80) |
| `detect_runtime` | ✓ | Read-only Playwright/Node capability detection |
| `run_runtime` | | Capture rendered evidence (writes to target project) |
| `accessibility_scan` | | axe accessibility scan (writes to target project) |
| `run_evals` | ✓ | Run automated eval suites |
| `validate_skill` | ✓ | Structural validation |
| `capability_map` | ✓ | Discover capabilities, tools, knowledge, runtime |
| `self_test` | ✓ | Fast health check |

Tool permissions are driven by MCP annotations (`readOnlyHint`, `destructiveHint`, etc.) and the extended `_meta["uiux.dev/annotations"]` metadata. Tools are not pre-approved via wildcard.

## Skill integration

Claude Code discovers `skills/ui-ux-workflow/SKILL.md`, which delegates to the canonical `SKILL.md` at the plugin root. The skill instructs the agent to:
1. Follow the workflow state machine
2. Load knowledge progressively through `retrieve_knowledge`
3. Use capability and technology resolvers before design decisions
4. Gate phase transitions on review criteria
5. Use runtime tools only when the target project has Playwright

No duplicate skill content exists in the adapter: `skills/ui-ux-workflow/SKILL.md` carries only the frontmatter and a pointer to the canonical `SKILL.md`.

## Verification

### Automated (no Claude Code required)

```bash
# Structural + subprocess verification (C1-C16)
python plugins/ui-engineering/.claude-plugin/verify.py <extracted-bundle>
python plugins/ui-engineering/.claude-plugin/verify.py --bundle <bundle.zip>
```

### Live host test (requires Claude Code)

```bash
claude --plugin-dir <extracted-bundle>
# In session: verify plugin load, tool discovery, read-only call, self_test
```

If Claude Code is not available: `CLAUDE_CODE_LIVE_TEST = NOT_RUN`

Marketplace verification is structural and does not claim a live install:

```bash
python plugins/ui-engineering/.claude-plugin/verify.py --marketplace --bundle dist/dev/adapters/ui-ux-design-0.1.0-dev-claude-marketplace.zip
```

## Limitations

- Verified with the Claude Code CLI (2.1.x): `claude plugin validate`, local marketplace add/install, component inventory (1 skill, 1 MCP server) and MCP health (`Connected`); an interactive session and a GitHub-hosted install have not been run yet
- No `min_version` for Claude Code is declared (docs verified 2026-09-25, no pinned host release)
- Python 3 must be available on PATH
- On Windows, `.mcp.json` uses `python3`; users may need to adjust to `python` or `py -3`
- Tool auto-approval is not configured (Claude Code manages this through its own permission system)

## Docs checked

Claude Code plugin documentation verified: **2026-09-25**
- `.claude-plugin/plugin.json`: manifest with `name`, `version`, `description`
- `.mcp.json`: MCP server declarations at plugin root
- `${CLAUDE_PLUGIN_ROOT}`: portable path variable
- `claude --plugin-dir`: local plugin testing
- `skills/` auto-discovery: subdirectories with `SKILL.md`
- Plugin validation: `claude plugin validate`
- Marketplace contract: `.claude-plugin/marketplace.json` has a kebab-case `name`,
  an object `owner` with `owner.name`, and relative `./plugins/...` sources.
- Marketplace CLI: `claude plugin marketplace add <marketplace-root>` then
  `claude plugin install ui-ux-design@uiux-local`.

## Marketplace status

```text
Claude Marketplace: IMPLEMENTED / SCHEMA VERIFIED / INSTALL IDENTIFIER CONSISTENT
Claude VS Code Installation: READY
Claude Live VS Code: NOT_RUN
CLAUDE_MARKETPLACE_LIVE_VALIDATE = PASS (claude plugin validate, local marketplace install)
CLAUDE_GITHUB_INSTALL = NOT_RUN (requires the manifests on the default branch)
```
