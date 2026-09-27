# Claude Code VS Code Extension Installation Guide

This document describes how to install and use the UI/UX Design plugin in the Claude Code VS Code extension.

## Prerequisites

- **VS Code** with the **Claude Code extension** installed.
- **Claude CLI** (if using the installation flow).
- **Python 3** installed and available in your `PATH`.
- The `ui-ux-design-<version>-claude-marketplace.zip` artifact.

## Build

To build the local marketplace bundle from the source code, run the export script from the repository root:

```powershell
python plugins/ui-engineering/.claude-plugin/export.py --dev --source plugins/ui-engineering --out dist/dev/adapters
```

This will produce the `dist/dev/adapters/ui-ux-design-0.1.0-dev-claude-marketplace.zip` archive. You must extract this ZIP archive to a permanent directory on your machine before installing it. The marketplace identity is `uiux-local`, so the plugin installation identifier is `ui-ux-design@uiux-local`.

## Install

### From GitHub (no build needed)

The repository itself is a Claude Code marketplace (`ui-engineering`):

```bash
claude plugin marketplace add doantuan22/Onni_UIUX_Design
claude plugin install ui-ux-design@ui-engineering
```

### Mode A: Local Installation from an exported bundle

1. Unzip the marketplace artifact to a known location, e.g., `~/claude-marketplaces/ui-ux-design`.
2. Open your terminal and add the marketplace to Claude Code:
   ```bash
   claude plugin marketplace add ~/claude-marketplaces/ui-ux-design
   ```
3. Install the plugin from the local marketplace:
   ```bash
   claude plugin install ui-ux-design@uiux-local
   ```
4. Verify the installation:
   ```bash
   claude plugin list
   ```

### Mode B: VS Code Development Fallback (CLAUDE_CODE_PLUGIN_DIRS)

If you cannot install the plugin globally, or if you want to test the plugin bundle dynamically:

1. Extract the standard plugin bundle (`ui-ux-design-0.1.0-dev-claude-code.zip`) to a location, e.g., `~/claude-plugins/ui-ux-design`.
2. Set the `CLAUDE_CODE_PLUGIN_DIRS` environment variable for your VS Code session.
   - On Windows (PowerShell):
     ```powershell
     $env:CLAUDE_CODE_PLUGIN_DIRS="C:\path\to\claude-plugins\ui-ux-design"
     code .
     ```
   - On Linux/macOS:
     ```bash
     export CLAUDE_CODE_PLUGIN_DIRS="/path/to/claude-plugins/ui-ux-design"
     code .
     ```

*Note: This is a fallback and does not persist across VS Code restarts unless you modify your profile.*

## VS Code

1. Reload the VS Code window (`Developer: Reload Window`).
2. Open the Claude Code extension panel.
3. Check available plugins by typing `/plugin` in the chat. The `ui-ux-design` plugin should be listed.
4. Verify the MCP connection by typing `/mcp`.
5. Run the self-test by asking Claude to invoke `self_test` tool.
6. Verify tools by asking Claude to invoke `capability_map`.
7. You are now ready to use the UI/UX design workflow.

## Update

When the plugin source code is updated, follow this flow:
1. Rebuild the marketplace bundle using `export.py`.
2. Overwrite the extracted marketplace folder with the new bundle contents.
3. Type `/reload-plugins` in the Claude Code chat or reload the VS Code window to apply the changes.

## Uninstall

To remove the plugin from Claude Code, run the official plugin CLI command:
```bash
claude plugin remove ui-ux-design
```

## Troubleshooting

- **Plugin not visible:** Check if you correctly extracted the bundle and provided the absolute path to `marketplace add`. Make sure you reloaded the VS Code window or used `/reload-plugins`.
- **MCP disconnected / "Executable not found":** the MCP server is started with `python3` unless `UIUX_PYTHON` is set. Run `python3 --version`; if it fails (typical on Windows with the python.org installer), set `UIUX_PYTHON` to a working interpreter (`setx UIUX_PYTHON python`), open a new terminal and restart Claude Code. Check with `claude mcp list`.
- **Python not found:** Ensure Python 3.9+ is on your `PATH`.
- **Marketplace not recognized:** Verify the `marketplace.json` exists in the `.claude-plugin` directory of the extracted marketplace archive.
- **Stale plugin cache:** Use `/reload-plugins` in the chat or restart VS Code.

*Note: Do not manually edit the files inside the `~/.claude` internal directory.*

## Verification status

The artifact is structurally verified by the repository's M1-M16 checks. A live
Claude Code/VS Code validation is environment-specific and has not been run:
`CLAUDE_MARKETPLACE_LIVE_VALIDATE = NOT_RUN` and `CLAUDE_LIVE_VSCODE = NOT_RUN`.
