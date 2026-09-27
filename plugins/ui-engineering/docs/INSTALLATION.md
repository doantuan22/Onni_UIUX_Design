# Public Installation Guide

This guide details how to acquire, install, verify, and upgrade the **UI Engineering Plugin** across supported environments.

---

## 1. System Requirements

- **Python**: Version 3.9, 3.10, 3.11, 3.12, or 3.13.
- **Node.js** (Optional): Version 18+ if target projects require local runtime execution or Node-based tooling.
- **Operating System**: Windows, Linux, or macOS.

---

## 2. Installation Methods

Repository: <https://github.com/doantuan22/Onni_UIUX_Design>. The plugin root is
`plugins/ui-engineering/` (plugin id `ui-ux-design`).

### Method A: Install directly from GitHub (Claude Code marketplace)

The repository root is a Claude Code marketplace named `ui-engineering`:

```bash
claude plugin marketplace add doantuan22/Onni_UIUX_Design
claude plugin install ui-ux-design@ui-engineering
```

(Inside a Claude Code session: `/plugin marketplace add doantuan22/Onni_UIUX_Design`, then
`/plugin install ui-ux-design@ui-engineering`.) This registers the `ui-ux-workflow` skill and the
`ui-ux-design-mcp` MCP server.

### Method B: Install from a clone

```bash
git clone https://github.com/doantuan22/Onni_UIUX_Design.git
cd Onni_UIUX_Design
```

- Claude Code: `claude plugin marketplace add .` then `claude plugin install ui-ux-design@ui-engineering`,
  or for a single session `claude --plugin-dir plugins/ui-engineering`.
- Codex: `codex plugin marketplace add .` (reads `.agents/plugins/marketplace.json`; plugin
  `ui-ux-design@ui-engineering`, manifest `plugins/ui-engineering/.codex-plugin/plugin.json`).

### Method C: Install from a release artifact

Download `ui-ux-design-<version>.zip` and `SHA256SUMS` from GitHub Releases, check the checksum and extract:

```bash
unzip ui-ux-design-0.1.1.zip -d ~/.plugins
claude --plugin-dir ~/.plugins/ui-ux-design-0.1.1
```

Host-specific bundles can also be exported from a clone:

```bash
python plugins/ui-engineering/.claude-plugin/export.py --source plugins/ui-engineering --out dist/adapters
python plugins/ui-engineering/.codex-plugin/export.py --source plugins/ui-engineering --out dist/adapters
```

---

## 3. Platform Setup

### A. Claude Code

- Manifest: `plugins/ui-engineering/.claude-plugin/plugin.json`; MCP: `plugins/ui-engineering/.mcp.json`;
  skill: `plugins/ui-engineering/skills/ui-ux-workflow/SKILL.md` (delegates to the canonical `SKILL.md`).
- Check with `claude plugin validate .` (marketplace) and `claude plugin validate plugins/ui-engineering`.
- Details: [../.claude-plugin/README.md](../.claude-plugin/README.md).

### B. OpenAI Codex

- Manifest: `plugins/ui-engineering/.codex-plugin/plugin.json`; MCP: `plugins/ui-engineering/.codex-plugin/mcp.json`.
- Details: [../.codex-plugin/MARKETPLACE_INSTALL.md](../.codex-plugin/MARKETPLACE_INSTALL.md). A live Codex host install has not been run yet.

### C. Standalone MCP server

Add the stdio server to any MCP client configuration (e.g. `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "ui-ux-design-mcp": {
      "command": "python3",
      "args": ["/path/to/Onni_UIUX_Design/plugins/ui-engineering/adapters/mcp/server.py"]
    }
  }
}
```

### Python launcher

The Claude Code MCP config launches `${UIUX_PYTHON:-python3}`: `python3` by default (Linux, macOS, Microsoft Store
Python on Windows). If the `ui-ux-design-mcp` server shows as failed (`claude mcp list` reports
`Executable not found`), set the `UIUX_PYTHON` environment variable to your interpreter and restart Claude Code —
for the python.org Windows installer: `setx UIUX_PYTHON python` (or the full path to `python.exe`).
For other MCP clients, replace `python3` by `python` or `py` (with args `["-3", ...]`) in
the host's MCP configuration.

---

## 4. Verification & Health Check

After installation, verify the installation immediately using the public CLI:

```bash
# Run self-test health check
python plugins/ui-engineering/scripts/uiux_cli.py call self_test

# Expected output:
# {"status": "PASS", "version": "0.1.1", "checks": [...]}
```

---

## 5. Upgrade & Rollback Workflow

### Upgrading
To upgrade to a new version:
1. Obtain the new release archive or pull the latest Git tag.
2. Replace the plugin directory with the new version.
3. Run `python plugins/ui-engineering/scripts/uiux_cli.py call self_test` to confirm registry and contract integrity.
4. *Note*: Plugin upgrades never modify your target repository files.

### Rollback
If you need to roll back to a previous version:
1. Re-extract or check out the previous release tag (e.g., `v0.1.0`).
2. Run `python plugins/ui-engineering/scripts/uiux_cli.py call self_test` to verify rollback validity.
