# UI Engineering Plugin

A structured AI coding plugin for frontend engineering, design systems, and UI/UX implementation.

It drives an AI coding agent through a two-phase web UI/UX workflow — Phase 1 locks the UX structure
(actors, flows, pages, information architecture), Phase 2 realizes the visual design and frontend with
rendered evidence — backed by a Design Knowledge System, capability/technology resolvers, a Playwright
runtime runner and design-quality evals.

## Architecture

The repository holds one shared, platform-neutral plugin core (`plugins/ui-engineering`) with thin
platform adapters for different AI agents (Claude Code, Codex, MCP).

```
.
├── plugins/ui-engineering/      # Shared plugin core (the packaged artifact)
│   ├── SKILL.md                 # Workflow controller — agents start here
│   ├── plugin.json              # Platform-neutral plugin manifest
│   ├── workflows/               # State machine, routing, preservation rules, artifact contracts
│   ├── skills/                  # Phase skills; skills/ui-ux-workflow/SKILL.md is the host-discoverable entry
│   ├── knowledge/               # Design Knowledge System (domains/registry.json, motion, web-patterns, …)
│   ├── templates/               # Artifact templates (STRUCTURE-LOCK.md, PAGE-SPEC.md, FINAL-REVIEW.md, …)
│   ├── review/                  # Phase and final review checklists
│   ├── execution/               # Browser runtime, accessibility and evidence contracts
│   ├── uiux/                    # Python core package (public API: uiux.api; tools: uiux/core/tools.json)
│   ├── scripts/                 # CLIs (uiux_cli.py, validate_skill.py, knowledge_lib.py, …)
│   ├── adapters/                # Generic adapter and shared MCP stdio transport
│   ├── .mcp.json                # MCP server declaration (Claude Code)
│   ├── .claude-plugin/          # Claude Code manifest (plugin.json) + bundle export/verify
│   ├── .codex-plugin/           # Codex manifest (plugin.json, mcp.json) + bundle export/verify
│   ├── packaging/               # Deterministic artifact build and verification
│   ├── schemas/                 # JSON schemas for manifests and engine outputs
│   ├── evals/                   # Eval scenarios, fixtures and rubric
│   └── docs/                    # User-facing install, compatibility and troubleshooting docs
├── .claude-plugin/marketplace.json   # Claude Code marketplace (plugin source: ./plugins/ui-engineering)
├── .agents/plugins/marketplace.json  # Codex marketplace (plugin source: ./plugins/ui-engineering)
├── tests/                       # Unit test suite (run from the repository root)
├── development/                 # Architecture docs, phase docs, benchmark harness, fixture targets
└── .github/workflows/           # CI (tests on Windows/Linux/macOS) and packaging
```

Detailed architecture documentation lives in `development/docs/`
(start with `architecture.md` and `plugin-architecture.md`). Installation and compatibility notes for
users are in `plugins/ui-engineering/docs/`.

## Install

Claude Code, directly from GitHub (the repository is a plugin marketplace named `ui-engineering`):

```bash
claude plugin marketplace add doantuan22/Onni_UIUX_Design
claude plugin install ui-ux-design@ui-engineering
```

Codex (from a clone): `codex plugin marketplace add ./Onni_UIUX_Design` (reads `.agents/plugins/marketplace.json`).
Other options — a single session with `claude --plugin-dir plugins/ui-engineering`, release archives and a standalone
MCP server — are described in [plugins/ui-engineering/docs/INSTALLATION.md](plugins/ui-engineering/docs/INSTALLATION.md).

## Requirements

- Python 3.9+ (standard library only).
- Optional, for browser evidence and accessibility scans: Node.js with Playwright (and `@axe-core/playwright`
  or `axe-core`) installed in the **target** project. The plugin never installs them; without them the
  runtime tools report `BLOCKED`.

## Usage

```bash
# Version, tool list and a tool call through the unified CLI
python plugins/ui-engineering/scripts/uiux_cli.py version
python plugins/ui-engineering/scripts/uiux_cli.py tools
python plugins/ui-engineering/scripts/uiux_cli.py call self_test
python plugins/ui-engineering/scripts/uiux_cli.py call analyze_repository --params '{"project": "path/to/app"}'

# Shared MCP server (stdio JSON-RPC)
python plugins/ui-engineering/adapters/mcp/server.py

# Host bundles (Claude Code / Codex) and their verification
python plugins/ui-engineering/.claude-plugin/export.py --dev --source plugins/ui-engineering --out dist/dev/adapters
python plugins/ui-engineering/.codex-plugin/export.py --dev --source plugins/ui-engineering --out dist/dev/adapters
python plugins/ui-engineering/.claude-plugin/verify.py --bundle dist/dev/adapters/ui-ux-design-0.1.0-dev-claude-code.zip
```

## Development

Run the same checks as CI from the repository root:

```bash
python -m unittest discover -s tests -t tests
python plugins/ui-engineering/scripts/validate_skill.py
python plugins/ui-engineering/scripts/knowledge_lib.py check
python plugins/ui-engineering/packaging/package_files.py
python plugins/ui-engineering/scripts/uiux_cli.py call run_evals
```

Validate the installable manifests with the Claude Code CLI: `claude plugin validate .` and
`claude plugin validate plugins/ui-engineering`.

Build and verify a package (outputs go to the git-ignored `dist/`):

```bash
python plugins/ui-engineering/packaging/build.py --dev --verify   # developer build of the working tree
python plugins/ui-engineering/packaging/build.py --verify         # release build (clean commit required)
```

`VERSION` (mirrored in `plugins/ui-engineering/VERSION`) is the single version source; see
[CHANGELOG.md](CHANGELOG.md) for changes and [CONTRIBUTING.md](CONTRIBUTING.md) for contribution rules.

## License

Licensed under the [Apache License, Version 2.0](LICENSE); see [NOTICE](NOTICE). The packaged plugin carries the same `LICENSE` and `NOTICE` files.
