# Codex Adapter (Agent Plugins Format)

This adapter enables the generic UI/UX Design skill to be used as a **local OpenAI Codex plugin** (following the portable Agent Plugins format).

## Status

- **Implementation Phase**: COMPLETE
- **Tested**: Structurally verified (X1-X16 PASS).
- **Portability**: HARDENED
- **Live Host Test**: `NOT_RUN` (Wait for an actual Codex workspace installation).
- **Public Directory Ready**: NOT CLAIMED. This adapter uses local MCP standard I/O for secure, internal workspace operations. It is not currently configured for public HTTP/SSE distribution.
- **Overall Status**: `experimental`
- **Marketplace**: IMPLEMENTED and STRUCTURALLY VERIFIED (K1-K16); live install remains `NOT_RUN`.

## Portability Contract

- Portable plugin format: YES
- Portable paths: YES
- Cross-platform bundle structure: YES

Default Python command: `python3`

Runtime prerequisite:
A compatible Python 3 interpreter must be available through the configured command.

Execution on Windows/Linux/macOS depends on the local runtime environment and is not guaranteed until live host testing is completed.

## Architecture

The Codex adapter is a thin metadata overlay. It does not contain any tool definitions or business logic.

```text
Codex
  ↓
Codex Adapter (mcp.json, plugin.json; skill entry skills/ui-ux-workflow/SKILL.md → SKILL.md)
  ↓
Common Adapter Framework
  ↓
Shared MCP stdio transport (plugins/ui-engineering/adapters/mcp/server.py)
  ↓
uiux.api
```

## Building the Bundle

To generate a self-contained development ZIP for testing:

```powershell
# From the repository root
python plugins/ui-engineering/.codex-plugin/export.py --dev --source plugins/ui-engineering --out dist/dev/adapters
```

This produces both `ui-ux-design-<version>-dev-codex.zip` and
`ui-ux-design-<version>-dev-codex-marketplace.zip`. See
[MARKETPLACE_INSTALL.md](MARKETPLACE_INSTALL.md) for the exact local marketplace flow,
repo config template, supported surfaces, and known host limitations.

## Testing Locally

```powershell
python plugins/ui-engineering/.codex-plugin/verify.py --bundle dist/dev/adapters/ui-ux-design-0.1.0-dev-codex.zip
```

## Permissions and Security

When loaded into Codex, the tools are *exposed*, but they are not automatically granted execution approval.
You can configure plugin-scoped MCP policies in your Codex host settings to define default approval modes and specific tool permissions.
