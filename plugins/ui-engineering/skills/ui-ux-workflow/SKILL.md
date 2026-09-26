---
name: ui-ux-workflow
description: Orchestrate a two-phase web UI/UX delivery workflow with structure locking, artifact contracts, and review gates. Use for new interface work, redesigns, or UI audits; do not use it for standalone visual styling guidance.
---

# UI/UX Workflow Engine (plugin entry point)

This file only makes the skill discoverable by plugin hosts that look for `skills/<name>/SKILL.md`.
The canonical workflow controller is the plugin root [SKILL.md](../../SKILL.md); it is not duplicated here.

1. Read [../../SKILL.md](../../SKILL.md) and follow it as the active skill instructions.
2. Resolve every relative path it mentions (`workflows/`, `skills/`, `knowledge/`, `templates/`, `review/`, `execution/`, `scripts/`) against the plugin root, two directories above this file.
3. Executable tools are exposed by the bundled MCP server (`ui-ux-design-mcp`) and by `python scripts/uiux_cli.py call <tool-id>` from the plugin root.
