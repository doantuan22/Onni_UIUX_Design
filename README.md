# Onni UI/UX Design

**`ui-ux-design`** is a plugin for AI coding agents (Claude Code, Codex, any MCP client) that turns
"build me a UI" into a disciplined design-and-engineering workflow: the agent first locks the UX
structure, then designs and implements the interface, and only calls it done when rendered evidence
passes review.

[![Release](https://img.shields.io/github/v/release/doantuan22/Onni_UIUX_Design)](https://github.com/doantuan22/Onni_UIUX_Design/releases)
[![CI](https://github.com/doantuan22/Onni_UIUX_Design/actions/workflows/ci.yml/badge.svg)](https://github.com/doantuan22/Onni_UIUX_Design/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue)](LICENSE)

```bash
claude plugin marketplace add doantuan22/Onni_UIUX_Design
claude plugin install ui-ux-design@ui-engineering
```

---

## Why

Left alone, coding agents jump straight to CSS: pages get invented, flows drift, every product ends
up with the same generic "AI look", and "done" means "it compiles". This plugin gives the agent a
workflow, a design knowledge base and executable checks so that UI work is:

- **Structured before styled** — actors, use cases, pages, flows and states are specified and locked
  before any visual decision.
- **Intentional, not generic** — style, layout, typography and motion are chosen from a curated
  knowledge system with an explicit *why* and *why not*, and reviewed against "AI-slop" patterns.
- **Safe on existing code** — existing UIs are preserved first and improved second; redesigns need
  explicit permission.
- **Verified** — completion requires review gates and, when a browser runtime is available, real
  screenshots and accessibility evidence — never claimed without proof.

## How it works

```
INITIAL → ANALYZING → PHASE_1 → PHASE_1_REVIEW → STRUCTURE_LOCKED → PHASE_2 → PHASE_2_REVIEW → FINAL_REVIEW → DONE
                                                                                   (BLOCKED whenever a contract cannot be met)
```

| Phase | What the agent produces | What it may not do |
|---|---|---|
| **Phase 1 — UX structure** | Requirement spec, actor and use-case maps, information architecture, page map, UX flows, state model, wireframe specs → `STRUCTURE-LOCK.md` | Choose colors, fonts, CSS or components; invent business rules |
| **Phase 2 — Visual realization** | Design direction and inspiration, design system and tokens, typography, visual grammar, motion, component specs, frontend implementation, rendered evidence | Change anything locked in Phase 1 (a structural change sends work back to Phase 1) |
| **Review gates** | Phase 1 review, Phase 2 review, final quality gate (accessibility, performance, consistency) → `FINAL-REVIEW.md` | Declare `DONE` without passing evidence |

**Existing UIs** follow *preserve first → improve second → redesign only when explicitly requested*,
with a change budget — **L1** safe refinement, **L2** local structural change, **L3** major redesign
(only with your explicit permission) — and an **ambition level** that says how far the result must move:

| Ambition | When | What changes | What stays |
|---|---|---|---|
| **Refine** | "keep the current look", local fixes, a11y/responsive | Spacing, states, contrast, responsive polish | Everything visible |
| **Elevate** *(default for "nâng cấp / làm đẹp / modernize")* | Upgrade requests | Page composition, hierarchy, type scale, surfaces, motion — with a committed direction, signature moves and no generic "AI look" defaults | App shell, navigation, routes, content, data, brand hues and logo |
| **Reimagine** | "full redesign", greenfield | Whatever you explicitly unlock | Whatever you don't |

Under Elevate/Reimagine the agent may propose one motion library (Motion/Framer Motion or GSAP) when CSS is
not enough; it never installs packages itself. See
[ambition-levels.md](plugins/ui-engineering/workflows/ambition-levels.md).

## Features

- **Workflow controller** — [`SKILL.md`](plugins/ui-engineering/SKILL.md) with a state machine,
  routing for greenfield vs. existing UI, artifact contracts and rollback rules; 15 focused skills
  (UX structure, design direction, inspiration, typography, visual language, design system,
  responsive interaction, frontend implementation, visual QA, final quality gate, …) and 42 artifact
  templates.
- **Design Knowledge System** — 248 catalogued entries (31 styles, 37 layouts, 28 screens,
  68 motion, 26 interactions, 26 effects, 16 recipes, 4 graphics techniques, 12 technologies), plus
  8 domain packs (SaaS/AI, fintech, e-commerce, healthcare, developer tools, …) and 10 framework packs
  (React, Next.js, Vue, Nuxt, Svelte/SvelteKit, Angular, static HTML, …), retrieved progressively
  instead of loaded wholesale.
- **Resolvers** — a capability resolver turns a design profile (brand, audience, density, intensity)
  into a ranked plan; a technology resolver picks the simplest way to build it, preferring what the
  project already has and never adding dependencies automatically.
- **Repository intelligence** — detects framework, routes, components, styling and design tokens;
  profiles an existing UI and plans modifications with blast radius and scope gates.
- **UI structure map** — `map_ui_structure` reads React/Next.js (+ Tailwind), Vue, Svelte, Astro and HTML
  sources into routes → layout shell → ordered sections → components, with each section's role, content
  inventory, layout pattern, motion and "AI look" signals; `diff_ui_maps` compares before/after to prove
  content was kept and the composition really changed.
- **Code recipes** — 18 type-checked React + Tailwind / Next.js recipes (asymmetric hero, bento, editorial index,
  sticky narrative, pricing emphasis, testimonial spotlight, FAQ split, CTA band, dashboard focus, Motion and GSAP
  motion, brand-derived tokens) in [knowledge/code-recipes](plugins/ui-engineering/knowledge/code-recipes/README.md);
  `suggest_recipes` picks them per mapped section by role and by the "AI look" signals they replace.
- **Visual critique loop** — before/after screenshots from the project's Playwright with a layout probe
  (overflow, tap targets, small text, fold) and axe, scored by an independent `visual-critic` subagent against a
  rubric; `score_visual_critique` merges the scores with measured gates and returns pass, iterate (with what to fix)
  or stop.
- **Runtime evidence** — screenshots, motion probes and axe accessibility scans using the *target
  project's own* Playwright; reports `BLOCKED` instead of installing anything.
- **Quality evals** — static design-quality analysis and 80 eval scenarios (E01–E80).

### Tools (MCP / CLI)

31 tools, exposed through the bundled MCP server `ui-ux-design-mcp` and the CLI:

| Area | Tools |
|---|---|
| Orchestration & knowledge | `orchestrate_ui`, `route_knowledge`, `build_knowledge_plan`, `retrieve_knowledge`, `resolve_capabilities`, `resolve_technology` |
| Repository & existing UI | `analyze_repository`, `analyze_existing_ui`, `map_ui_structure`, `diff_ui_maps`, `suggest_recipes`, `plan_modification`, `build_validation_handoff` |
| Controlled execution & verification | `check_execution_gate`, `guard_edits`, `verify_implementation` |
| Runtime & accessibility | `detect_runtime`, `run_runtime`, `accessibility_scan`, `score_visual_critique`, `run_runtime_validation`, `build_critic_report`, `evaluate_runtime_result`, `build_repair_plan`, `run_targeted_repair`, `recapture_evidence` |
| Quality & health | `analyze_design_quality`, `run_evals`, `validate_skill`, `capability_map`, `self_test` |

## Install

### Claude Code (recommended)

```bash
claude plugin marketplace add doantuan22/Onni_UIUX_Design
claude plugin install ui-ux-design@ui-engineering
```

or inside a session: `/plugin marketplace add doantuan22/Onni_UIUX_Design`, then
`/plugin install ui-ux-design@ui-engineering`. This registers the `ui-ux-workflow` skill and the
`ui-ux-design-mcp` MCP server. For a single session from a clone:
`claude --plugin-dir plugins/ui-engineering`.

### Codex (experimental)

From a clone: `codex plugin marketplace add ./Onni_UIUX_Design` (reads
`.agents/plugins/marketplace.json`), or use `ui-ux-design-<version>-codex-marketplace.zip` from the
[latest release](https://github.com/doantuan22/Onni_UIUX_Design/releases/latest).

### Release archive or any MCP client

Download `ui-ux-design-<version>.zip` and `SHA256SUMS` from
[Releases](https://github.com/doantuan22/Onni_UIUX_Design/releases), verify, extract, then run
`claude --plugin-dir ui-ux-design-<version>` — or register the stdio server
`python3 <plugin-root>/adapters/mcp/server.py` in any MCP client.

Full instructions, Windows notes and troubleshooting:
[INSTALLATION.md](plugins/ui-engineering/docs/INSTALLATION.md) ·
[COMPATIBILITY.md](plugins/ui-engineering/docs/COMPATIBILITY.md) ·
[TROUBLESHOOTING.md](plugins/ui-engineering/docs/TROUBLESHOOTING.md).

### Requirements

- Python 3.9+ on `PATH` (standard library only; nothing to `pip install`).
- Optional: Node.js with Playwright (and `@axe-core/playwright` or `axe-core`) in the **target**
  project for screenshots and accessibility scans. Without it those tools report `BLOCKED`; the plugin
  never installs packages or downloads browsers.

## Usage

After installing, just describe the UI work; the agent picks up the `ui-ux-workflow` skill:

- *"Design and build a pricing page for our developer-tool SaaS in this Next.js app."*
- *"Nâng cấp giao diện trang chủ cho chuyên nghiệp hơn."* (existing UI, **Elevate**: new composition,
  type and motion; content, routes and brand kept)
- *"Audit the dashboard in `src/app/dashboard` and fix spacing, states and accessibility — keep the
  current look."* (existing UI, **Refine**, L1 budget)
- *"Plan an onboarding flow for a fintech app — structure first, no styling yet."* (Phase 1 only)

The agent writes its artifacts (`REQUIREMENT-SPEC.md`, `STRUCTURE-LOCK.md`, `DESIGN-DIRECTION.md`,
`DESIGN-SYSTEM.md`, `FINAL-REVIEW.md`, …) into your project as it goes, so every decision is
reviewable.

The tools also work without an agent:

```bash
python plugins/ui-engineering/scripts/uiux_cli.py tools
python plugins/ui-engineering/scripts/uiux_cli.py call self_test
python plugins/ui-engineering/scripts/uiux_cli.py call analyze_repository --params '{"project": "path/to/app"}'
```

## Repository layout

```
plugins/ui-engineering/     The plugin (packaged artifact): SKILL.md, skills/, workflows/, knowledge/,
                            templates/, review/, execution/, uiux/ (Python core), adapters/ (MCP),
                            .claude-plugin/, .codex-plugin/, packaging/, schemas/, evals/, docs/
.claude-plugin/             Claude Code marketplace (ui-engineering → ./plugins/ui-engineering)
.agents/plugins/            Codex marketplace
tests/                      Test suite (run from the repository root)
development/                Architecture and phase docs, benchmark harness, fixture targets
.github/workflows/          CI (Python 3.9–3.13 × Linux/Windows/macOS) and packaging (build, verify, cross-OS parity)
```

Upgrade history, open plan items and roadmap (Vietnamese): [docs/nang-cap](docs/nang-cap/README.md).

Architecture: [development/docs/architecture.md](development/docs/architecture.md) and
[development/docs/plugin-architecture.md](development/docs/plugin-architecture.md).

## Development

```bash
python -m unittest discover -s tests -t tests                 # full test suite
python plugins/ui-engineering/scripts/validate_skill.py         # skill structure and links
python plugins/ui-engineering/scripts/knowledge_lib.py check    # knowledge catalogs and registry
python plugins/ui-engineering/scripts/uiux_cli.py call run_evals
python plugins/ui-engineering/packaging/build.py --dev --verify   # build + verify a package into dist/
claude plugin validate . && claude plugin validate plugins/ui-engineering
```

`VERSION` is the single version source. See [CHANGELOG.md](CHANGELOG.md) and
[CONTRIBUTING.md](CONTRIBUTING.md).

## Status

Version **0.1.1** — MCP launcher fix on top of the first public release (0.1.0); see [CHANGELOG.md](CHANGELOG.md).

- Claude Code: install, skill discovery and MCP connection verified with the Claude Code CLI.
- Codex: structurally verified; not yet tested on a live Codex host.
- The MCP server starts with `python3`. On Windows with the python.org installer (no `python3`),
  run `setx UIUX_PYTHON python`, open a new terminal and restart Claude Code.

## License

[Apache License 2.0](LICENSE) — see [NOTICE](NOTICE).
