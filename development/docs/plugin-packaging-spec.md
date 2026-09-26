# Plugin Packaging Phase — Technical Specification

- Status: **proposed** (specification only; nothing in this document is implemented yet unless marked *existing*)
- Target version range: `0.2.0` (first packaged release) → `1.0.0`
- Audience: an engineer or AI coding agent implementing the packaging phase without further architectural input
- Related: [plugin-architecture.md](plugin-architecture.md) (current architecture), [plugins/ui-engineering/adapters/CONTRACT.md](../../plugins/ui-engineering/adapters/CONTRACT.md), [plugins/ui-engineering/schemas/plugin-manifest-README.md](../../plugins/ui-engineering/schemas/plugin-manifest-README.md), [plugins/ui-engineering/packaging/README.md](../../plugins/ui-engineering/packaging/README.md)

Normative words: **MUST**, **MUST NOT**, **SHOULD**, **MAY** as in RFC 2119. Paths are package-relative POSIX paths unless stated otherwise.

---

## Implementation status (updated 2026-09-24)

| Spec item | Status | Where |
|---|---|---|
| P0: `.gitattributes`, `.gitignore`, baseline green | **done**, except the commit itself: the refactor is still uncommitted (`COMMIT_REQUIRED_BEFORE_RELEASE_BUILD`), so release builds of this repository are refused until it is committed | `.gitattributes`, `.gitignore` |
| P1: build, verify (V1–V13), schemas, `UIUX_TEST_ROOT`, git-optional tests | **done** | `plugins/ui-engineering/packaging/{build,verify,artifact}.py`, `plugins/ui-engineering/schemas/`, `tests/_paths.py` |
| P2: full `plugin.schema.json`, CI `ci` + `package` workflows, reproducibility (V14) | **done (configured)**; CI not yet executed (no remote run available) | `plugins/ui-engineering/schemas/plugin.schema.json`, `.github/workflows/` |
| P2: contract hardening (error envelope §13, parameter type validation, `accessibility_scan` tool, tool annotations, `capability_map`, `adapter.json` + `self_test` for the generic adapter) | **done locally**; source, validator, evals, artifact smoke and extracted-artifact verification pass. Cross-OS V14 remains CI-only and is not claimed as executed. | `uiux/core/{errors,schema,tools,capabilities}.py/json`, `uiux/api.py`, `plugins/ui-engineering/adapters/generic/` |
| P3: shared MCP stdio transport | **done locally (experimental)**; stdlib-only JSON-RPC 2.0 over stdio, pinned to MCP `2025-06-18`; extracted-artifact V10 smoke covers lifecycle, discovery, calls, error envelopes, `BLOCKED` and public `self_test`. | `plugins/ui-engineering/adapters/mcp/`, `tests/test_mcp_transport.py`, `plugins/ui-engineering/packaging/verify.py` |
| P3+: Claude Code/Codex/Cline/OpenCode/Copilot adapters and `release.py` | not started | — |

Deviations from the text below, decided during implementation:

1. `SHA256SUMS` lists the archives and the package manifest, **not** `build-info.json` (§5.6 said all three). Build-info records the build machine, which would make otherwise identical builds differ.
2. Reproducibility (§5.7, V14): byte-identical archives are guaranteed for the same platform and deflate implementation. Across operating systems, **content** identity (identical `PACKAGE-MANIFEST.json`) is guaranteed, and archive byte identity is reported. The `package` workflow enforces content identity and warns on archive byte differences.
3. Release builds require a clean tree even when `--commit` names an older commit, and there is no `--allow-dirty` flag. Non-release builds use the explicit `--dev` mode instead (distinct names, directory and metadata).
4. `V8` checks invalid calls against the current CLI contract (`INVALID_CALL`, exit 3), including additive error codes/remediation and registry-schema type validation.
5. MCP implements only the tools capability and the required lifecycle/ping path. Resources, prompts, sampling, HTTP/SSE and every host-specific adapter remain deliberately out of scope. The `2025-06-18` protocol revision is pinned in one module and MCP metadata; protocol upgrades are an explicit compatibility decision.
6. This implementation deliberately splits the historical P3 row: the reusable MCP transport is complete as `experimental`, while the Claude Code adapter, other platform adapters and `release.py` remain not started. No host integration was inferred from transport availability.

---

## 0. How to use this document

1. Read §1 (Repository Findings) first: it states the real starting point, which differs from the brief in several places.
2. Treat §21 (Invariants) as hard constraints. If an implementation step seems to require breaking one, stop and record why.
3. Implement in the order of §17 (Migration Plan). Each phase has its own exit criteria. The phase as a whole is done when §18 (Definition of Done) is met.
4. Host-platform details in §8 (file names, config keys) change over time. They are marked **[verify]** and MUST be confirmed against the host's current documentation when that adapter is implemented. The adapter interface and requirements in §8 do not depend on those details.

---

## 1. Repository Findings (audit of the actual state)

Audited on 2026-09-24 against the working tree of `D:\Skill_AIcoding_Frontend`.

### 1.1 Confirmed as described

| Assumption | Finding |
|---|---|
| Layered architecture `plugin → uiux.api → uiux.knowledge / uiux.engine / uiux.runtime → uiux.evals`, `uiux.core` foundation | Confirmed. Modules: `uiux/{core,knowledge,engine,runtime,evals,tooling}`, `uiux/api.py`, `uiux/cli.py`, `uiux/__main__.py`. Import direction is enforced by `tests/test_architecture.py` using `uiux/core/layers.json`. |
| Manifest | `plugins/ui-engineering/plugin.json` (`manifest_version: 1`, `name: ui-ux-design`, `version: 0.1.0`) + `plugin.schema.json`. |
| Tool registry | `uiux/core/tools.json` has 8 tools: `resolve_capabilities`, `retrieve_knowledge`, `resolve_technology`, `analyze_design_quality`, `detect_runtime`, `run_runtime`, `run_evals`, `validate_skill`. Every entrypoint is `uiux.api:<fn>`. |
| Knowledge registry | `phase-2/knowledge/registry.json` (generated): 248 catalog entries + 13 component grammars. Collections: styles 31, layouts 37, screens 28, motion 68, interactions 26, effects 26, recipes 16, graphics 4, technologies 12, components 13. |
| VERSION single source | `VERSION` = `0.1.0`. `uiux.__version__` reads it; tests assert that manifest, `api.version()` and `CHANGELOG.md` agree. |
| Compatibility scripts | `scripts/{validate_skill,knowledge_lib,resolve_capabilities,analyze_design_quality,run_browser_execution,detect_capabilities,run_accessibility_scan,validate_runtime_evidence,validate_accessibility_evidence}.py` are wrappers over `uiux.*` modules via `scripts/_bootstrap.py` (module aliasing). Unified CLI: `scripts/uiux_cli.py`. |
| Tests pass | `python -m unittest discover -s tests` → 89 tests OK. `python scripts/validate_skill.py` passes. `python plugins/ui-engineering/packaging/package_files.py` → PASS, 475 files. |
| Public API | `uiux.api.__all__`: `version, get_config, reload_config, list_tools, describe_architecture, layer_of, call_tool, resolve_capabilities, retrieve_knowledge, get_knowledge, knowledge_collections, resolve_technology, analyze_design_quality, detect_runtime, run_runtime, run_evals, validate_skill`. |
| Generic adapter | `plugins/ui-engineering/adapters/generic/adapter.py` is a working JSON adapter (describe / instructions / call / `--config`) that imports only `uiux.api`. |
| Runtime optionality | No module imports Playwright. Readiness states `NOT_DECLARED`, `DECLARED_NOT_INSTALLED`, `PACKAGE_AVAILABLE_BROWSER_MISSING` and `READY` exist in `uiux/runtime/capabilities.py`. The browser runner blocks before capture unless `READY`. |

### 1.2 Differences and gaps (the spec is designed around these)

| # | Finding | Consequence for this phase |
|---|---|---|
| F1 | **The plugin-ready refactor is not committed.** `HEAD` is `81f8121`; the working tree has 40 untracked, 13 modified, 11 renamed and 6 deleted (`.pyc`) entries. | A reproducible build needs a commit. Committing the refactor is step 0 of §17. |
| F2 | **Mixed line endings.** `core.autocrlf=true`, no `.gitattributes`; e.g. `uiux/api.py` and `registry.json` are CRLF and `SKILL.md`/`VERSION` are LF in the working tree. | File checksums from a working tree differ between Windows and Linux. Builds MUST come from committed, LF-normalized content (§5.7), and a `.gitattributes` is required (§19). |
| F3 | **Not pip-installable as-is.** There is no `pyproject.toml`. `uiux/__init__.py` reads `../VERSION`, and `resources.get_package_root()` requires `SKILL.md` next to the `uiux/` directory (or `UIUX_ROOT`). Skill data (Markdown, JSON, fixtures) lives outside `uiux/`. | Archive distribution works as-is. A wheel needs a payload strategy that does not move Markdown in the source tree (§9.4). |
| F4 | **Skill name mismatch.** `SKILL.md` frontmatter `name: ui-ux-workflow`; manifest `name: ui-ux-design`. | Adapters MUST define which name each host sees (§5.1, §8). Neither name may be changed silently (§21). |
| F5 | **Unstructured errors.** `uiux.api.ToolError` carries only a message. The CLI prints `{"status":"INVALID_CALL","error":"..."}` with exit 3. Unexpected exceptions inside a tool propagate as Python tracebacks. | A machine-readable error code field is required before platform adapters (§13), added without breaking current output. |
| F6 | **Parameter validation is shallow.** `call_tool` checks required and unknown parameter names and binds the Python signature, but it does not check JSON types against `tools.json` input schemas. | MCP-style hosts send `inputSchema`-driven arguments; type validation is required (§6.1). |
| F7 | **Accessibility scan is not a registered tool** and still gates on `playwright.package_present`, not `runtime_state` (`uiux/runtime/accessibility.py`). | Consistency debt (§19). Adapters cannot reach the a11y scan through the registry. |
| F8 | **No LICENSE file.** The manifest says `"license": "UNLICENSED"`. | Blocks any public distribution. Internal distribution may proceed (§19). |
| F9 | **Python requirement untested.** The manifest and tools say `python >=3.9`; only 3.11.9 has been exercised. No CI exists. | CI matrix (§16) must prove the declared floor, or the floor must be raised. |
| F10 | **`tests/test_architecture.py` uses `git ls-files`** for layer classification and degrades to `uiux/` files when git is unavailable. `tests/_paths.py` hard-wires the package root as the tests' parent directory. | Running tests against an extracted artifact needs a root override (§10.3). |
| F11 | **Package root is read-only safe at runtime.** The only write into the package root is `scripts/knowledge_lib.py index` (a development command). Runtime evidence is written to the *target project* (`<project>/.evidence`). Local overrides use `uiux.config.json` at the package root. | Installed packages MAY be read-only. Hosts must configure through `UIUX_CONFIG` (§6.6). |
| F12 | **Current packaging** is a dry-run file list only (`plugins/ui-engineering/packaging/package_files.py`, `package-rules.json`); no archive, checksum or verification exists. The list currently includes 475 files and excludes `tests/` (9) and `.gitignore` (1). | This phase adds build, checksum and verification (§10–§11). |
| F13 | `external-references/` no longer exists in the repository (removed in `81f8121`); validator rules still mention it harmlessly. | No action; `must_exclude_prefixes` keeps guarding it. |

---

## 2. Goals and scope

### 2.1 Goals

1. Produce **deterministic, verifiable release artifacts** of the skill from a committed source tree: a generic archive plus per-platform adapter bundles.
2. Define and enforce the **package, plugin and adapter contracts** so any host integration goes through `uiux.api` only.
3. Ship **one complete platform adapter** and define the remaining ones by interface and requirements. Each is added later behind the same contract.
4. Keep every current capability, path contract, CLI and test working (§12, §21).

### 2.2 In scope

- `plugins/ui-engineering/packaging/` build, checksum and verify tooling; release artifact layout.
- New schemas: package manifest (file list + hashes), adapter metadata, error envelope, build info.
- Error model extension (§13) and parameter type validation (§6.1) in the Core API. These are additive only.
- A shared MCP transport adapter (§8.0) and platform adapters, delivered phase by phase (§17).
- Verification pipeline on extracted artifacts; CI proposal.
- Distribution models: git clone, local install, release archive; wheel as an optional later phase.

### 2.3 Out of scope

- Moving Markdown knowledge or workflow files (§21).
- Publishing to any marketplace or registry (the pipeline prepares artifacts; publishing is a manual, separately authorized step).
- Installing Node, Playwright, axe or browsers, ever.
- Changing design logic, knowledge content, eval semantics or resolver behavior.

---

## 3. Packaging architecture and boundaries

```text
┌──────────────────────────── Distribution artifact ────────────────────────────┐
│ ui-ux-design-<version>.{zip,tar.gz} + package-manifest.json + SHA256SUMS      │
│                                                                                │
│  ┌──────────── Platform adapters (plugins/ui-engineering/adapters/<platform>/) ────────────┐   │
│  │ host metadata + install/export + instructions mapping                   │   │
│  │ may use: the MCP transport adapter, the generic adapter, the manifest   │   │
│  └─────────────────────────────────┬───────────────────────────────────────┘   │
│  ┌──────────── Generic plugin layer (plugin/) ─────────────────────────────┐   │
│  │ manifest · schemas · generic adapter · MCP transport · packaging tools  │   │
│  └─────────────────────────────────┬───────────────────────────────────────┘   │
│                                    │ uiux.api only                             │
│  ┌──────────── Core package (uiux/) + skill payload ───────────────────────┐   │
│  │ uiux.api → knowledge/engine/runtime → evals; uiux.core foundation       │   │
│  │ payload: SKILL.md, workflow/, phase-1/, phase-2/, review/, templates/,  │   │
│  │ execution/, evals/, docs/, scripts/, VERSION, CHANGELOG.md              │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────┘
```

| Boundary | Owns | MUST NOT |
|---|---|---|
| **Core package `uiux` + skill payload** | All business/design logic, knowledge, runtime, evals, validation, configuration, resource discovery | Import or read `plugin/` (the whole-package validator checks plugin files only when present — existing rule) |
| **Generic plugin layer `plugin/`** | Platform-neutral manifest, schemas, generic adapter, MCP transport adapter, packaging/build/verify tools | Contain design logic; import anything from `uiux` except `uiux.api` and `uiux.__version__` |
| **Platform adapters `plugins/ui-engineering/adapters/<platform>/`** | Host-specific metadata, instruction-file mapping, install/export steps, tool mapping to the host's mechanism | Reimplement or wrap core logic; call anything but `uiux.api` (directly, or via the generic/MCP adapters) |
| **Distribution artifact** | Byte-exact, verified copy of the packaged file list + integrity metadata | Contain tests, caches, `.pyc`, evidence, captures, benchmark/eval outputs, local config, VCS data |

Dependency direction is strictly downward. Build tools in `plugins/ui-engineering/packaging/` are the only code that reads the whole tree; they do so as file I/O plus `uiux.api.layer_of` and `uiux.api.version`.

---

## 4. Target directory structure

Existing items are marked *(existing)*; everything else is new in this phase.

```text
plugin/
├── README.md                              (existing, update)
├── manifest/
│   ├── plugin.json                        (existing, extend: adapters, schemas, artifacts)
│   ├── plugin.schema.json                 (existing, extend to full JSON Schema)
│   └── README.md                          (existing)
├── schemas/
│   ├── package-manifest.schema.json       file list + hashes of a built artifact
│   ├── adapter.schema.json                adapter.json metadata contract
│   ├── error.schema.json                  error envelope (§13)
│   ├── build-info.schema.json             reproducibility record
│   └── README.md
├── adapters/
│   ├── README.md                          (existing, update status table)
│   ├── CONTRACT.md                        (existing, extend with §7)
│   ├── generic/                           (existing) adapter.py, README.md; add adapter.json
│   ├── mcp/                               shared stdio MCP transport over uiux.api
│   │   ├── adapter.json
│   │   ├── server.py
│   │   └── README.md
│   ├── claude-code/                       first complete platform adapter (§17 P3)
│   │   ├── adapter.json
│   │   ├── export.py                      builds the host bundle from the package file list
│   │   ├── templates/                     host files rendered at export time (plugin manifest, command/agent stubs)
│   │   └── README.md
│   ├── codex/        adapter.json, export.py, templates/, README.md
│   ├── cline/        adapter.json, export.py, templates/, README.md
│   ├── opencode/     adapter.json, export.py, templates/, README.md
│   └── copilot/      adapter.json, export.py, templates/, README.md
└── packaging/
    ├── README.md                          (existing, update)
    ├── package-rules.json                 (existing)
    ├── package_files.py                   (existing) file list
    ├── build.py                           archive + package-manifest + SHA256SUMS + build-info
    ├── verify.py                          extract to clean env + verification pipeline (§11)
    └── release.py                         orchestrates build → verify → adapter bundles (no publishing)

dist/                                       (gitignored; release artifacts, never committed)
└── <version>/
    ├── ui-ux-design-<version>.zip
    ├── ui-ux-design-<version>.tar.gz
    ├── ui-ux-design-<version>.package-manifest.json
    ├── ui-ux-design-<version>.build-info.json
    ├── ui-ux-design-<version>.verify-report.json
    ├── SHA256SUMS
    └── adapters/
        ├── ui-ux-design-<version>-claude-code.zip
        ├── ui-ux-design-<version>-<platform>.zip ...
        └── SHA256SUMS
```

Rules:

- Platform adapter directories MUST NOT be created before their phase (§17). An empty or stub adapter looks supported without working (*existing* rule in `plugins/ui-engineering/adapters/README.md`).
- `dist/` MUST be added to `.gitignore` (already ignored as `dist/`, *existing*) and to `package-rules.json` `exclude_dirs` (*existing*).
- New files under `plugin/` are automatically in the `plugin` layer (`uiux/core/layers.json`: `plugin/**`). No layer map change is needed.

---

## 5. Package contract

### 5.1 Identity

| Field | Value | Source of truth |
|---|---|---|
| Package id | `ui-ux-design` | `plugins/ui-engineering/plugin.json` → `name` |
| Skill name shown to skill-aware hosts | `ui-ux-workflow` | `SKILL.md` frontmatter (unchanged; F4). Adapters that expose a "skill" use this name; adapters that expose a "plugin/package" use the package id. |
| Version | semantic version | `VERSION` only |
| Python package | `uiux` | `uiux/` |

### 5.2 Files included and excluded

The file list is **exactly** the output of `plugins/ui-engineering/packaging/package_files.py --list` (*existing*): layers with `package: true` in `uiux/core/layers.json`, minus `exclude_dirs`, `exclude_globs` and `exclude_layers` from `package-rules.json`.

| Included (current layers) | Excluded |
|---|---|
| `SKILL.md`, `VERSION`, `CHANGELOG.md`; `workflow/`, `phase-1/`, `phase-2/`, `review/`, `templates/`; `execution/`; `evals/` (scenarios, fixtures, resolver scenarios, quality docs, reports); `docs/`; `scripts/`; `uiux/`; `plugin/` | `tests/`; `.git/`, `.gitignore`, `.gitattributes`; `__pycache__/`, `*.pyc`, `*.pyo`; `.evidence/` (any depth); `runtime-helper.cjs`, `runtime-input.json`, `axe-helper.cjs`, `axe-input.json`; `evals/benchmark/output/`, `evals/results/`, `**/benchmark-output/`; `*.log`, `*.tmp`, `.DS_Store`, `Thumbs.db`; `uiux.config.json`; `node_modules/`, `.venv/`, `venv/`, `dist/`, `build/`, IDE folders |

Additional rules for this phase:

- `LICENSE` (when added, §19) MUST be classified in the `docs` layer or a new `legal` layer with `package: true`, and it MUST be in `must_include`.
- Adapter bundles (§8) contain the full package file list plus files **rendered** by the adapter's `export.py`. Rendered files live only in the bundle, never in the source tree.
- Any file that is not classified fails the build (*existing* behavior of `package_files.py`).

### 5.3 Dependencies

| Kind | Requirement |
|---|---|
| Runtime | CPython `>=3.9` as declared today. This MUST be proven in CI (§16, F9); otherwise raise the floor in the manifest, tools and `pyproject.toml` together. No third-party Python packages. |
| Build | Same Python, standard library only (`zipfile`, `tarfile`, `hashlib`, `json`, `subprocess` for `git`). `git` is required for commit-based builds. |
| Test | Standard library `unittest`. PyYAML is an optional parity check that is skipped when absent (*existing*). |

### 5.4 Optional dependencies (never installed by the skill)

| Dependency | Scope | Used by | When absent |
|---|---|---|---|
| Node.js | host machine | `detect_runtime` (version probe), `run_runtime`, a11y scan | `detect_runtime` reports `NOT_AVAILABLE`; `run_runtime` → `BLOCKED` |
| `playwright` / `@playwright/test` | target project `package.json` + `node_modules` | `run_runtime`, a11y scan | `BLOCKED` with `PLAYWRIGHT_IMPORT_FAILURE` |
| Playwright browser build | Playwright cache | `run_runtime` | `BLOCKED` with `PLAYWRIGHT_BROWSER_UNAVAILABLE` |
| `@axe-core/playwright` / `axe-core` | target project | a11y scan | `BLOCKED` with `AXE_NOT_AVAILABLE` |
| PyYAML | development | parser parity test | test skipped |

### 5.5 Version

- `VERSION` is the only place a version is written by hand. `plugin.json` `version` MUST equal it (*existing* test). The build MUST fail if they differ, if `CHANGELOG.md` lacks a `## <version>` section, or if the tree is dirty (unless `--allow-dirty` is set, which marks the build `non-reproducible` in build-info and must never be used for a release).
- Artifact names embed the version: `ui-ux-design-<version>`. Build metadata (commit) goes in `build-info.json`, never in `VERSION`.

### 5.6 Checksum and integrity

- **Per-file:** `ui-ux-design-<version>.package-manifest.json` (schema `plugins/ui-engineering/schemas/package-manifest.schema.json`):
  ```json
  {"schema_version": 1, "name": "ui-ux-design", "version": "0.2.0",
   "source": {"commit": "<40-hex>", "tree_clean": true},
   "rules_sha256": "<sha256 of package-rules.json + layers.json>",
   "files": [{"path": "SKILL.md", "size": 5723, "sha256": "<hex>", "layer": "core-skill", "mode": "0644"}]}
  ```
  `files` is sorted by `path` (byte order of UTF-8), covering every file in the archive except the manifest itself.
- **Per-archive:** `SHA256SUMS` in GNU coreutils format (`<hex>  <filename>`), covering the archives, the package manifest and build-info.
- The package manifest MUST also be embedded in the archive root as `PACKAGE-MANIFEST.json`, so an extracted tree can verify itself offline.
- Signing (Sigstore/GPG) is out of scope before `1.0.0`. Checksums are integrity checks, not authenticity. §15 schedules signing.

### 5.7 Deterministic / reproducible build

A build is reproducible when two builds of the same commit, on any OS, produce byte-identical archives. Requirements:

1. **Source:** export from the commit, not the working tree: `git archive --format=tar <commit>`, extracted to a temporary staging directory. This removes working-tree line-ending drift (F2) and untracked files. `.gitattributes` MUST normalize text files to LF (`* text=auto eol=lf`, with explicit `binary` for `*.png`).
2. **File list:** run `package_files.compute(staging_root)` against the staging directory, not the working tree.
3. **Generated files:** `phase-2/knowledge/INDEX.md` and `registry.json` MUST be fresh in the commit (`catalog.check()` passes in staging). The build MUST NOT regenerate them silently. A stale registry fails the build.
4. **Archive normalization:** entries sorted by path; directories omitted (zip) or emitted sorted (tar); mtime = commit time (`git show -s --format=%ct`), overridable only by `SOURCE_DATE_EPOCH`; uid/gid 0, uname/gname empty; mode `0644` for files and `0755` for `*.py` files with a shebang (none today, so all are `0644`); zip compression `ZIP_DEFLATED` level 9 with fixed `date_time`; tar gzip with `mtime=0` in the gzip header and no filename in the gzip header.
5. **Top-level directory:** every archive entry is prefixed `ui-ux-design-<version>/`.
6. **Build info:** `build-info.json` records commit, `SOURCE_DATE_EPOCH`, Python version, platform, `rules_sha256`, tool versions and `reproducible: true|false`.
7. **Check:** CI builds twice (two runners, e.g., Linux and Windows) and compares `SHA256SUMS`.

---

## 6. Plugin contract (what a host can rely on)

### 6.1 Tools

- Source: `uiux/core/tools.json` (*existing*). Each tool has `id`, `visibility`, `description`, `entrypoint` (`uiux.api:<fn>`), `cli`, `input` (JSON Schema object), `output`, `dependencies`, `runtime_requirements`, `side_effects`.
- Invocation: `uiux.api.call_tool(tool_id, params)` or `python scripts/uiux_cli.py call <tool-id> --params '<json>'` (*existing*).
- **Required changes:**
  1. `input` schemas MUST be complete JSON Schema (types for every property, `additionalProperties: false`, enums where closed). `call_tool` MUST validate types with a small stdlib validator (types, required, enum, `additionalProperties`, array item type). Unknown parameters stay rejected (*existing*).
  2. Add `accessibility_scan` as a registered public tool (F7) with the same runtime-state gating as `run_runtime`. Keep `scripts/run_accessibility_scan.py` unchanged in CLI shape.
  3. Add `"annotations": {"read_only": bool, "writes_to": "none|target-project", "may_start_process": bool}` to every tool, so hosts can apply their own permission prompts. Values: all tools `read_only: true` except `run_runtime` and `accessibility_scan` (`writes_to: target-project`; `may_start_process: true` only with `allow_start`).
- Tool ids are **stable public API**. Renaming or removing one is a major version change (§15).

### 6.2 Knowledge

- Source: `phase-2/knowledge/registry.json` (*existing*). Access via `retrieve_knowledge` / `uiux.api.get_knowledge` / `knowledge_collections`.
- Contract: collection names (`styles, layouts, screens, motion, interactions, effects, recipes, graphics, technologies, components`), entry `id` format `<kind>.<slug>`, and row fields (`id, kind, collection, category, name, file, line, summary`) are public. `file` and `line` are informational and MAY change between patch releases. Adapters MUST NOT hard-code them.
- Hosts MUST load knowledge progressively (by id / collection), never whole folders. Adapter instruction files (§8) MUST state this.

### 6.3 Capabilities

- `plugin.json` → `capabilities` (*existing* list of 11). Each capability MUST map to at least one tool or instruction entrypoint in a new `capability_map` field, e.g. `"design-knowledge-retrieval": {"tools": ["retrieve_knowledge"], "instructions": ["phase-2/knowledge/README.md"]}`. The verification pipeline checks that every mapped item exists.

### 6.4 Runtime

- Runtime is **optional**. `detect_runtime` reports `playwright.runtime_state ∈ {NOT_DECLARED, DECLARED_NOT_INSTALLED, PACKAGE_AVAILABLE_BROWSER_MISSING, READY}` (*existing*).
- `run_runtime` returns `{exit_code, summary}` (*existing*). `summary.status ∈ {COMPLETED, PARTIAL, FAILED, BLOCKED, DRY_RUN, INVALID_INPUT}`. Hosts MUST treat `BLOCKED` as an honest, non-exceptional result and show its error code to the user. They MUST NOT retry by installing anything.
- Evidence is written only under the target project's evidence directory (default `<project>/.evidence/<session>`), never under the package root.

### 6.5 Evals

- `run_evals` (*existing*): automated suites `structure`, `knowledge`, `resolver`, `quality-fixtures` → `PASS|FAIL`. The `scenarios` suite lists E01–E80 with status `MANUAL`, because agent-behavior scenarios cannot be executed by a script.
- Packaged artifacts MUST pass all automated suites (§11). Hosts MAY expose `run_evals` to users. They MUST NOT report `MANUAL` scenarios as passed.

### 6.6 Config

- Resolution order (*existing*): `uiux/core/defaults.json` → `<package-root>/uiux.config.json` → file named by `UIUX_CONFIG` → caller overrides. Sections: `paths`, `browser`, `dependency_policy`, `motion_budget`, `performance_budget`, `feature_flags`. Paths are package-relative without `..`, and `dependency_policy.auto_install` MUST be `false` (*existing* validation).
- Installed packages SHOULD be treated as read-only (F11). Hosts MUST configure through `UIUX_CONFIG` (a file outside the package) and MUST NOT write `uiux.config.json` into an installed package.
- `UIUX_ROOT` MAY point the code at another payload root (*existing*).

### 6.7 Error handling

See §13. Every plugin-facing call returns JSON. Invalid calls and internal failures are expressed through the error envelope, never as a raw traceback on stdout.

---

## 7. Adapter contract (extends `plugins/ui-engineering/adapters/CONTRACT.md`)

### 7.1 Rules for every adapter

1. **Core API only.** Python adapters import only `uiux.api` and `uiux.__version__` (*existing* test `test_adapters_use_only_the_public_api`, extended to every `plugins/ui-engineering/adapters/**/*.py`). Non-Python adapters invoke `python <root>/scripts/uiux_cli.py` or the MCP transport, never internal modules or scripts other than `uiux_cli.py` and the generic adapter.
2. **No business/design logic.** Adapters map, normalize and install. They do not rank, filter, validate design content, rewrite knowledge, or compute budgets. Checked in review, and mechanically by a size and import budget (§20): adapter Python files MUST NOT import `json` schema logic beyond the error envelope, and MUST NOT reference knowledge ids.
3. **Request normalization.** Host arguments (strings, host-specific wrappers, missing optionals) are converted to the tool's JSON input. Normalizations allowed: parse a JSON string into an object; map host parameter names 1:1 to tool parameter names as declared in `adapter.json`; drop host-only envelope fields; resolve relative `project` paths against the host's workspace root. Nothing else: no default values beyond the tool schema's defaults.
4. **Response normalization.** Core JSON results are passed through unchanged inside the host's result container. Errors become the host's error mechanism *and* keep the error envelope (§13) as structured content. Adapters MUST NOT turn `BLOCKED`/`FAIL` results into exceptions or successes.
5. **Capability/runtime detection.** On startup an adapter checks, and reports through `describe()`:
   - core import works and `uiux.api.version()` satisfies `adapter.json` → `core_version` range;
   - `manifest_version` is supported;
   - Python version meets the manifest;
   - optional runtime by calling `detect_runtime` **only when the host requests a runtime tool**, never at startup (no subprocess at import; *existing* rule).
6. **Platform-specific metadata** lives only in `plugins/ui-engineering/adapters/<platform>/adapter.json` and `templates/`. The core, the generic manifest and the skill payload stay platform-neutral.
7. **Configuration.** Host settings become a JSON file passed via `UIUX_CONFIG` (*existing* `configure` operation), never by patching files in the package.
8. **No startup side effects**, no network access, no auto-install, no writes into the package root.

### 7.2 `adapter.json` (schema `plugins/ui-engineering/schemas/adapter.schema.json`)

```json
{
  "schema_version": 1,
  "id": "claude-code",
  "status": "planned|skeleton|experimental|supported",
  "core_version": ">=0.2.0,<1.0.0",
  "manifest_version": [1],
  "host": {"name": "Claude Code", "min_version": "[verify]", "docs_checked": "YYYY-MM-DD"},
  "integration": {"instructions": "skill|agents-md|rules-dir|instructions-file", "tools": "mcp-stdio|cli|none"},
  "tool_map": {"resolve_capabilities": "resolve_capabilities"},
  "exposed_tools": ["resolve_capabilities", "retrieve_knowledge", "resolve_technology", "analyze_design_quality",
                    "detect_runtime", "run_runtime", "run_evals", "validate_skill"],
  "rendered_files": [{"template": "templates/plugin.json.tmpl", "target": ".claude-plugin/plugin.json"}],
  "bundle_layout": {"payload_dir": "skills/ui-ux-workflow"},
  "limitations": []
}
```

`tool_map` values are host-visible names. The default is the identity mapping. Hosts with naming restrictions may rename (e.g., prefixing), but the mapping MUST stay 1:1.

### 7.3 Required operations (per adapter)

| Operation | Contract |
|---|---|
| `describe() -> dict` | Name, version, status, capabilities, exposed tools with input schemas, detected environment (Python, core version); no runtime probing |
| `instructions() -> dict` | Where instructions start (`SKILL.md`), progressive loading rule, knowledge registry location, tool invocation method for this host |
| `call(tool_id, params) -> dict` | Normalize → `uiux.api.call_tool` → normalize result/error |
| `configure(config_file) -> dict` | Set `UIUX_CONFIG`, `uiux.api.reload_config()`, return effective config |
| `export(output_dir) -> list[str]` | Platform adapters only: produce the host bundle (§9.3) from the verified package file list plus rendered templates; deterministic; returns written files |
| `self_test() -> dict` | Smoke test used by the verification pipeline: `describe`, `retrieve_knowledge(ids=["style.swiss"])`, `call("nope")` returns `TOOL_NOT_FOUND` |

---

## 8. Platform adapter designs (interface and requirements only)

### 8.0 Shared MCP transport adapter (`plugins/ui-engineering/adapters/mcp/`)

Most target hosts can consume tools through the Model Context Protocol (MCP) over stdio **[verify per host]**. One shared transport avoids five tool bridges:

- `server.py`: a standard-library implementation of JSON-RPC 2.0 over stdio implementing `initialize`, `tools/list` (from `uiux.api.list_tools()`: `name`, `description`, `inputSchema` = tool `input`, optional `annotations` from §6.1), and `tools/call` (→ `uiux.api.call_tool`). It returns results as a text content item containing the JSON plus structured content, and sets `isError: true` with the error envelope for failures. Protocol version negotiation follows the MCP specification version pinned in `adapter.json` **[verify current spec]**.
- It MUST NOT implement resources, prompts or sampling in this phase (tools only), log to stdout (stderr only), or import anything but `uiux.api`.
- Command line: `python <root>/plugins/ui-engineering/adapters/mcp/server.py` (root resolved from the file location or `UIUX_ROOT`, as the generic adapter already does).
- Status target: `experimental` in P2, `supported` once two hosts use it (§17).

### 8.1 Claude Code (first complete platform adapter)

- **Integration model:** skill instructions + tools.
  - Instructions: Claude Code discovers skills as directories containing `SKILL.md` with frontmatter `name`/`description` **[verify]**. The bundle places the full payload under a skill directory so every relative link in `SKILL.md` keeps working, e.g. `skills/ui-ux-workflow/` (payload root = skill root). `SKILL.md` is used unchanged (frontmatter name `ui-ux-workflow`).
  - Plugin packaging: a plugin root with a plugin manifest (e.g. `.claude-plugin/plugin.json`: `name`, `version`, `description`) and optional MCP server declaration **[verify file names and keys]**. The manifest `name` is the package id `ui-ux-design` and `version` comes from `VERSION`.
  - Tools: an MCP server entry running the shared transport (`python ${PLUGIN_ROOT}/skills/ui-ux-workflow/plugins/ui-engineering/adapters/mcp/server.py`, using the host's variable for the plugin root **[verify]**). Fallback when MCP is disabled: `SKILL.md` already documents `python scripts/uiux_cli.py call <tool>`.
- **Requirements:** the bundle is produced by `export.py` from the verified package file list; no skill content is duplicated or edited; rendered host files are listed in `adapter.json` → `rendered_files`; install instructions cover user-level and project-level installation **[verify locations]**; `self_test` passes in the extracted bundle.
- **Acceptance:** in a real Claude Code session the skill is discovered, the tools list shows 8 (+ `accessibility_scan`) tools, `retrieve_knowledge` and `resolve_capabilities` work, and `run_runtime` returns an honest `BLOCKED` in a project without Playwright.

### 8.2 Codex (OpenAI Codex CLI/IDE)

- **Integration model:** project instructions file (`AGENTS.md`) **[verify]** + MCP server configured in the user's Codex config (e.g. a TOML `mcp_servers` table with `command`/`args`) **[verify]**.
- **Adapter responsibilities:** render an `AGENTS.md` *snippet* (not a copy of `SKILL.md`) that points to the installed `SKILL.md` path and states the progressive loading rule; render the MCP config snippet; never overwrite an existing `AGENTS.md`. The installer prints or merges snippets only with explicit user action.
- **Interface:** `export(output_dir)` → `agents-snippet.md`, `mcp-config-snippet.toml`, `INSTALL.md`.

### 8.3 Cline

- **Integration model:** rules directory/file (e.g. `.clinerules/`) **[verify]** + MCP server entry in Cline's MCP settings JSON **[verify]**.
- **Adapter responsibilities:** render a rule file that references `SKILL.md` and the tool usage, plus the MCP settings snippet (`command`, `args`, optional `env.UIUX_CONFIG`). Tool auto-approval MUST default to off for `run_runtime` and `accessibility_scan` (uses §6.1 annotations).

### 8.4 OpenCode

- **Integration model:** `AGENTS.md`-style rules **[verify]** + local MCP server in the project/user config (e.g. an `mcp` section with a command array) **[verify]**.
- **Adapter responsibilities:** as for Codex: rules snippet + config snippet + install notes; identical tool mapping.

### 8.5 GitHub Copilot

- **Integration model:** repository custom instructions (e.g. `.github/copilot-instructions.md`) **[verify]** + MCP servers for agent mode in the editor configuration (e.g. a workspace MCP JSON with a `servers` map) **[verify]**. Copilot's cloud coding agent has separate MCP configuration **[verify]**, which is out of scope until the local editor path is supported.
- **Adapter responsibilities:** render an instructions snippet that references `SKILL.md` (Copilot instruction files are typically short, so the snippet is a pointer, not the skill) and the MCP server snippet. Document that runtime tools need a local Node/Playwright in the user's project.

### 8.6 Common requirements for 8.2–8.5

- Status stays `planned` until implemented, `experimental` after automated `self_test`, and `supported` only after a documented manual run on the real host (*existing* contract rule 5).
- Snippets are rendered from templates with `{version}`, `{payload_root}`, `{python}` and `{mcp_command}` placeholders only. No other logic.
- Each adapter README contains: host version tested, install steps, tool mapping table, limitations, uninstall steps.

---

## 9. Installation and distribution model

### 9.1 Git clone (development / power users)

`git clone` → the working tree is a valid package root. Commands run from any directory (*existing*, tested). No build is needed. Tests are available.

### 9.2 Release archive (primary distribution)

Download `ui-ux-design-<version>.zip|tar.gz` and `SHA256SUMS`, verify, and extract anywhere. The extracted `ui-ux-design-<version>/` directory is the package root. `python <root>/plugins/ui-engineering/packaging/verify.py --installed <root>` (offline) re-checks `PACKAGE-MANIFEST.json`.

### 9.3 Local install (per-host bundles)

Platform adapter bundles (`ui-ux-design-<version>-<platform>.zip`) are extracted into the host's plugin/skill location (§8), or the adapter README gives the exact location. A local install MUST NOT modify files outside the chosen install directory, except for configuration snippets the user explicitly applies.

### 9.4 pip / wheel (optional, not before P5)

A wheel is **optional** and gated on the payload design below, because of F3:

- The wheel contains the `uiux` package plus the skill payload copied **at build time** into `uiux/_payload/` (source tree unchanged; Markdown is not moved in the repository).
- `resources.get_package_root()` gains one fallback, tried after `UIUX_ROOT` and after the "SKILL.md next to `uiux/`" check: `uiux/_payload/` if it contains `SKILL.md`. `uiux/__init__.py` reads `VERSION` through the same resolution. These are additive changes; existing behavior is unchanged.
- Console entry point `uiux = uiux.cli:main`. `pyproject.toml` uses a standard-library-only build backend configuration (e.g. setuptools with `package-data`), `requires-python` equals the manifest floor, and there are no runtime dependencies.
- Acceptance: `pip install <wheel>` in a clean venv; `uiux version`, `uiux call validate_skill` and `uiux call run_evals` pass from an unrelated directory.
- If the payload fallback cannot be done without behavior change, drop the wheel. Archives remain the supported path.

### 9.5 How a platform adapter finds the plugin

In order:

1. `UIUX_ROOT` environment variable (*existing*);
2. the adapter file's own location (`plugins/ui-engineering/adapters/<platform>/…` → package root is two levels up from `plugin/`, *existing* pattern);
3. the host's plugin-root variable, where the host provides one **[verify]**.

The adapter then imports `uiux.api` from that root and checks `version()` against `adapter.json` → `core_version`. Failures produce `CORE_NOT_FOUND` or `VERSION_MISMATCH` (§13).

---

## 10. Build process

```text
source repo ──► package file list ──► build ──► checksum ──► extract to clean env ──► validate ──► test
(commit)        (package_files.py)    (build.py)  (SHA256SUMS)  (verify.py)          (§10.2)      (§10.3)
```

### 10.1 `plugins/ui-engineering/packaging/build.py`

```text
python plugins/ui-engineering/packaging/build.py [--commit <rev>] [--out dist/] [--formats zip,tar.gz] [--allow-dirty]
```

1. Resolve the commit (default `HEAD`); refuse a dirty tree unless `--allow-dirty`, which marks the build non-reproducible.
2. `git archive` the commit into a temp staging directory (LF-normalized by `.gitattributes`).
3. In staging: `package_files.compute(staging)` MUST return `PASS`; `catalog.check(staging)` MUST return no errors (fresh registry); `VERSION` == `plugin.json.version` and a CHANGELOG entry exists.
4. Write `PACKAGE-MANIFEST.json` into staging (sorted files with sha256, size, layer, mode).
5. Create archives with the normalization rules of §5.7.
6. Write `<name>.package-manifest.json`, `<name>.build-info.json` and `SHA256SUMS` into `dist/<version>/`.
7. Exit 0 with a JSON summary; non-zero with an error envelope on any failure.

### 10.2 `plugins/ui-engineering/packaging/verify.py`

```text
python plugins/ui-engineering/packaging/verify.py dist/<version>/ui-ux-design-<version>.zip [--python <exe>] [--keep]
python plugins/ui-engineering/packaging/verify.py --installed <extracted-root>
```

Extracts into a fresh temp directory outside the repository, runs every check of §11 from **another** temp working directory with a clean environment (`PYTHONPATH`, `UIUX_ROOT` and `UIUX_CONFIG` unset; `PLAYWRIGHT_BROWSERS_PATH` pointed at an empty temp dir), and writes `<name>.verify-report.json` (all checks, durations, pass/fail).

### 10.3 Tests against the artifact

Tests are not packaged. The pipeline copies the source `tests/` into a scratch directory **next to** the extracted payload (not into it) and runs them with a new environment variable `UIUX_TEST_ROOT=<extracted-root>` that `tests/_paths.py` MUST honor (F10). Git-dependent assertions MUST skip explicitly when the root is not a git work tree.

### 10.4 `plugins/ui-engineering/packaging/release.py`

Runs build → verify → `export` of each adapter with status ≥ `experimental` → verify each adapter bundle (`self_test`) → a combined `SHA256SUMS` for adapter bundles. It never publishes, tags or pushes.

---

## 11. Mandatory verification pipeline on the packaged artifact

Every check runs on the **extracted** artifact with the clean environment of §10.2. Any failure fails the release.

| # | Check | Command / method | Pass criterion |
|---|---|---|---|
| V1 | Integrity | recompute sha256 of every file vs `PACKAGE-MANIFEST.json`; compare the file set | identical; no extra or missing files |
| V2 | Whitelist | every file path is in the package manifest; no path matches `tests/`, `__pycache__`, `*.pyc`, `*.pyo`, `.evidence`, `runtime-helper.cjs`, `*-input.json` helper temporaries, `evals/results/`, `evals/benchmark/output/`, `.git`, `uiux.config.json`, `node_modules`, `*.log`, `*.tmp`, `dist/` | zero violations |
| V3 | Import | `python -c "import sys; sys.path.insert(0, root); import uiux, uiux.api"` from another cwd; assert that no `uiux.runtime.*`, `uiux.engine.*` or `uiux.evals.*` module is loaded (*existing* startup test logic) | OK |
| V4 | Version | `VERSION` == `uiux.__version__` == `plugin.json.version` == archive name version == `build-info.version`; CHANGELOG section present | all equal |
| V5 | Manifest | `plugin.json` validates against `plugin.schema.json` (full JSON Schema, stdlib validator); every referenced path exists; every entrypoint tool exists in `tools.json`; every `capability_map` target exists | valid |
| V6 | Skill validation | `python <root>/scripts/validate_skill.py` | exit 0 |
| V7 | Automated evals | `python <root>/scripts/uiux_cli.py call run_evals` | `status == PASS` for structure, knowledge, resolver, quality-fixtures |
| V8 | Tool registry smoke | for each tool call with minimal safe params: `retrieve_knowledge {"ids":["style.swiss"]}`, `resolve_capabilities` with `evals/resolver-scenarios/developer-tool.json` profile, `resolve_technology {"capabilities":["motion.m1-hover"]}`, `analyze_design_quality` on `evals/fixtures/quality/restrained`, `detect_runtime` on `evals/runtime-fixtures/playwright-ready`, `run_runtime` **dry_run** on the same fixture, `run_evals {"suites":["knowledge"]}`, `validate_skill {}`; plus invalid calls (`nope`, missing params, wrong type) | valid calls return JSON without error; invalid calls return the right error code (§13); `run_runtime` dry-run returns `DRY_RUN` and writes nothing |
| V9 | Compatibility scripts | each of the 9 `scripts/*.py` wrappers + `uiux_cli.py` runs its documented smallest command from another cwd (as `tests/test_entrypoints.py` does today) | exit codes as today |
| V10 | Adapter smoke | generic adapter `describe` / `call` / `call nope`; MCP server: `initialize`, `tools/list` (count == registry), one `tools/call`, one invalid call; each platform bundle: `self_test` | all pass |
| V11 | Read-only install | make the extracted root read-only (chmod / Windows read-only attribute) and repeat V6–V8 | pass; no write attempted in the root |
| V12 | Core without plugin | copy the artifact minus `plugin/` and repeat V6–V8 (*existing* test logic) | pass |
| V13 | Tests | full `tests/` against the artifact via `UIUX_TEST_ROOT` (§10.3) | all pass (git-only assertions skipped) |
| V14 | Reproducibility (CI only) | two builds on different OSes → identical `SHA256SUMS` | identical |

---

## 12. Backward compatibility

The following MUST keep working unchanged: names, arguments, stdout JSON shape, exit codes and files written. Verified by V9 and existing tests.

| Script | Contract kept |
|---|---|
| `scripts/validate_skill.py [root]` | text output, exit 0/1; no argument validates the package root (current behavior) |
| `scripts/knowledge_lib.py check|index` | output lines, exit codes; `index` writes `INDEX.md` + `registry.json` (development only) |
| `scripts/resolve_capabilities.py --profile F [--format md]` | byte-identical plan output for identical knowledge |
| `scripts/analyze_design_quality.py P [--manifest M]... [--visual-intensity N] [--format md]` | report JSON / Markdown |
| `scripts/run_browser_execution.py --input F --project D [--dry-run] [--allow-start]` | summary JSON; exit 0/2/3/4/1 mapping; evidence layout |
| `scripts/detect_capabilities.py [D] [--url U]` | report keys (additive changes only) |
| `scripts/run_accessibility_scan.py --input F --project D [--dry-run]` | summary JSON, exit codes |
| `scripts/validate_runtime_evidence.py DIR`, `scripts/validate_accessibility_evidence.py DIR` | output, exit codes |
| `scripts/uiux_cli.py version|tools|architecture|call` | JSON output; exit 0/1/3 |
| Import names `knowledge_lib`, `resolve_capabilities`, `analyze_design_quality`, `run_browser_execution`, `detect_capabilities`, `run_accessibility_scan`, `validate_runtime_evidence`, `validate_accessibility_evidence`, `validate_skill` (with `scripts/` on `sys.path`) | resolve to the implementation modules (*existing* aliasing) |

Rules: new fields in JSON outputs are **additive only**; no field is renamed or removed before `1.0.0` without a deprecation entry in `CHANGELOG.md` and one minor release of overlap; `scripts/` is never renamed; no new script may shadow `uiux` (*existing* test).

---

## 13. Error model

### 13.1 Envelope (schema `plugins/ui-engineering/schemas/error.schema.json`)

```json
{"status": "ERROR",
 "error": {"code": "VERSION_MISMATCH", "category": "compatibility", "message": "adapter requires core >=0.2.0,<1.0.0; found 0.1.0",
           "retryable": false, "details": {"required": ">=0.2.0,<1.0.0", "found": "0.1.0"}, "remediation": "Install a matching release."}}
```

**Compatibility with today's CLI:** `scripts/uiux_cli.py` currently prints `{"status":"INVALID_CALL","error":"<message>"}`. The new shape keeps `status: "INVALID_CALL"` for invalid calls and adds `error_code`, `category` and `remediation` as **top-level additive fields**. `error` stays a string for the CLI until `1.0.0`. The full envelope above is used by adapters and the MCP transport, and by the CLI only behind `--error-format envelope` until `1.0.0`, when it becomes the default (a documented breaking change).

Core implementation: `uiux.api.ToolError` gains `code`, `category`, `details` and `remediation` attributes (default code `INVALID_PARAMS`, preserving the message). A new `uiux.api.call_tool` guard converts unexpected exceptions into `INTERNAL_ERROR` (message only, no traceback on stdout; traceback to stderr when `UIUX_DEBUG=1`).

### 13.2 Codes

| Situation | Code | Category | Where raised | Tool result vs error | Exit (CLI) | Retryable |
|---|---|---|---|---|---|---|
| Unknown tool | `TOOL_NOT_FOUND` | invocation | `call_tool` | error | 3 | no |
| Missing/unknown/mistyped parameter | `INVALID_PARAMS` | invocation | `call_tool` | error | 3 | no |
| Invalid profile/project/request content | `INVALID_INPUT` | input | tool (resolver `ProfileError`, analyzer, runner `INVALID_INPUT`) | error (runner keeps its `status: INVALID_INPUT` summary) | 3 | no |
| Dependency missing (host lacks Node for runtime) | `DEPENDENCY_MISSING` | runtime | `detect_runtime` data, runner | **result**: `BLOCKED` with runtime error code `PLAYWRIGHT_IMPORT_FAILURE` | 1 (CLI) / 2 (runner script) | after user installs |
| Runtime blocked (Playwright not declared/installed) | `RUNTIME_BLOCKED` (maps `PLAYWRIGHT_IMPORT_FAILURE`) | runtime | runner, a11y scan | result `BLOCKED` | same as above | after user installs |
| Browser missing | `BROWSER_MISSING` (maps `PLAYWRIGHT_BROWSER_UNAVAILABLE`) | runtime | runner | result `BLOCKED` | same | after user installs browsers |
| axe missing | `RUNTIME_BLOCKED` (maps `AXE_NOT_AVAILABLE`) | runtime | a11y scan | result `BLOCKED` | same | after user installs |
| Manifest invalid / unreadable | `MANIFEST_INVALID` | packaging | adapters, verify, `validate_skill` | error | 3 | no |
| Version mismatch (VERSION vs manifest vs adapter range) | `VERSION_MISMATCH` | compatibility | adapters, verify | error | 3 | no |
| Adapter unsupported (unknown platform, unsupported `manifest_version`, host version outside range, status `planned`) | `ADAPTER_UNSUPPORTED` | compatibility | adapters | error | 3 | no |
| Core not importable from the resolved root | `CORE_NOT_FOUND` | compatibility | adapters | error | 3 | no |
| Knowledge registry missing/stale/invalid JSON | `KNOWLEDGE_REGISTRY_INVALID` | integrity | `uiux.knowledge.registry`, `validate_skill`, verify | error for retrieval tools; `FAIL` result for `validate_skill`/`run_evals` | 3 / 1 | no |
| Tool registry invalid (bad JSON, entrypoint not in `uiux.api.__all__`) | `TOOL_REGISTRY_INVALID` | integrity | `uiux.core.registry`, verify | error | 3 | no |
| Config invalid (absolute path, `auto_install: true`, bad types) | `CONFIG_INVALID` | configuration | `uiux.core.config` | error | 3 | no |
| Integrity failure (checksum) | `INTEGRITY_FAILURE` | integrity | verify | error | 3 | no |
| Unexpected exception | `INTERNAL_ERROR` | internal | `call_tool` guard | error | 1 | maybe |

Principle: environmental limitations (missing Node, Playwright, browsers or axe) are **results** with `status: BLOCKED` and a precise code, not errors, because they are honest facts about the target environment. Malformed calls, packages and configurations are **errors**.

---

## 14. Security and safety boundary

1. **No auto-install:** no code path runs `npm`, `npx`, `pip`, `playwright install` or a package manager. `dependency_policy.auto_install` is forced `false` (*existing*). The verification pipeline greps packaged code for `npm install`, `npx playwright install`, `pip install` and `playwright install` outside documentation, and fails on a hit.
2. **No browser download:** the runner and a11y scan only detect browsers (*existing*). V8 runs with an empty `PLAYWRIGHT_BROWSERS_PATH` and asserts it is still empty afterwards.
3. **No Core API bypass:** the adapter import allowlist is `uiux.api` and `uiux.__version__` (*existing* test, extended to all adapters and the MCP server). Non-Python adapters may invoke only `scripts/uiux_cli.py`, `plugins/ui-engineering/adapters/generic/adapter.py` and `plugins/ui-engineering/adapters/mcp/server.py`.
4. **No arbitrary entrypoint execution:** tool dispatch uses the fixed `_DISPATCH` table in `uiux.api` (*existing*). `tools.json` entrypoints are validated to be `uiux.api:<name in __all__>` (*existing* validator + test), and `call_tool` never imports a module named by data. Adapters MUST NOT execute commands or modules named in any manifest, `adapter.json` or config file. Rendered MCP/host configs contain only the fixed command `python <root>/plugins/ui-engineering/adapters/mcp/server.py`.
5. **Process start only on explicit consent:** `run_runtime` starts a server only with `allow_start` **and** an argv array in the request (*existing*). Host adapters MUST surface `annotations.may_start_process` so hosts can prompt.
6. **Writes are bounded:** runtime evidence lives only inside the target project (*existing* `inside()` check). The package root is never written at runtime (V11).
7. **Path safety:** configuration paths are package-relative without `..` (*existing*). Adapters resolve `project` parameters against the host workspace and MUST reject paths outside it when the host defines a workspace.
8. **Supply chain:** no third-party runtime dependencies. Build and verify are standard library. Release artifacts carry SHA-256 sums. Signing is scheduled for 1.0.0 (§15).
9. **Secrets:** runtime error records never include credentials (*existing* runtime-errors contract). Adapters MUST NOT log environment variables.

---

## 15. Versioning and release strategy (`0.1.x` → `1.0.0`)

Semantic versioning with `VERSION` as the single source (*existing*). Public API = `uiux.api` functions, tool ids and input/output shapes, manifest schema, knowledge registry schema and collection names, error codes, script CLIs.

| Version | Content | Stability |
|---|---|---|
| `0.1.x` | Current plugin-ready architecture (commit it first, F1); patch releases only for fixes | internal |
| `0.2.0` | Packaging: `.gitattributes`, build/verify/release tools, package manifest + checksums, error envelope fields, parameter type validation, `accessibility_scan` tool, tool annotations, `UIUX_TEST_ROOT`, CI | first artifact; internal distribution |
| `0.3.0` | MCP transport (experimental) + Claude Code adapter (complete, `supported` after a manual host run) | pre-release for early users |
| `0.4.0` | Codex and Cline adapters (experimental → supported) | |
| `0.5.0` | OpenCode and Copilot adapters; optional wheel (§9.4) if accepted | |
| `0.9.x` | Release candidates: API freeze, deprecations resolved, docs complete, LICENSE decided | API frozen |
| `1.0.0` | Stable public API; envelope becomes the CLI default error format; artifact signing; supported host matrix published | stable |

Rules: while `0.y.z`, a minor bump MAY include documented breaking changes to public contracts (listed under "Breaking" in CHANGELOG). After `1.0.0`, breaking changes require a major bump. Knowledge content additions are minor; knowledge corrections are patch. Pre-releases use `-rc.N` (`1.0.0-rc.1`), allowed by the *existing* VERSION regex. Tags `v<version>` are created by a human after CI passes.

---

## 16. CI/CD proposal

Host-agnostic description. Implement it on the repository's CI provider (GitHub Actions assumed, no workflow exists yet).

| Workflow | Trigger | Jobs |
|---|---|---|
| `ci` | push, pull request | Matrix: OS {ubuntu, windows, macos} × Python {3.9, 3.11, 3.13} (drop 3.9 only by raising the declared floor everywhere). Steps: checkout → `python -m unittest discover -s tests` → `python scripts/validate_skill.py` → `python scripts/knowledge_lib.py check` → `python plugins/ui-engineering/packaging/package_files.py` → `python scripts/uiux_cli.py call run_evals`. No Node/Playwright installed (proves optional runtime). |
| `package` | push to main, tags | ubuntu + windows: `build.py` → `verify.py` → compare `SHA256SUMS` across jobs (V14) → upload `dist/` as CI artifacts |
| `release` | manual dispatch on a tag | Re-run `package` from the tag; run `release.py`; attach artifacts, `SHA256SUMS`, verify reports and the CHANGELOG section to a **draft** release. A human publishes. |
| `runtime-smoke` (optional, non-blocking) | weekly / manual | A job that *itself* sets up Node + Playwright in a throwaway fixture project (a CI concern, not the skill's) and runs `run_runtime` with `motion_probe`, to finally verify live runtime evidence. The skill still never installs anything. |

Policies: `ci` and `package` are required checks; artifacts are never committed; secrets are not needed except for publishing (future, manual).

---

## 17. Migration plan (small phases)

Each phase ends green: all tests pass, `validate_skill` passes, the package boundary passes, CHANGELOG is updated.

| Phase | Scope | Exit criteria |
|---|---|---|
| **P0 — Baseline** | Commit the current plugin-ready refactor (F1). Add `.gitattributes` (`* text=auto eol=lf`, `*.png binary`) and renormalize (`git add --renormalize .`) in a separate commit. Add a LICENSE decision placeholder issue. | Clean tree; `git archive` of HEAD passes the existing tests via a scratch copy |
| **P1 — Build and verify core artifact** | `plugins/ui-engineering/schemas/{package-manifest,build-info}.schema.json`; `build.py`; `verify.py` implementing V1–V9, V11–V13; `UIUX_TEST_ROOT` in `tests/_paths.py`; git-optional skips | `dist/0.2.0-dev/` artifact builds reproducibly on one OS; verify-report all green |
| **P2 — Contract hardening + generic adapter** | Error envelope fields (§13, additive); `call_tool` type validation; `INTERNAL_ERROR` guard; tool annotations; `accessibility_scan` tool with runtime_state gating (F7); `capability_map`; full `plugin.schema.json`; `adapter.schema.json`; `adapter.json` + `self_test` for the generic adapter; V10 for the generic adapter; CI `ci` + `package` workflows (V14) | Release `0.2.0` artifact verified on Linux and Windows with identical checksums |
| **P3 — MCP transport + Claude Code** | `plugins/ui-engineering/adapters/mcp/` (experimental) and `plugins/ui-engineering/.claude-plugin/` (`export.py`, templates, README); `release.py`; V10 for both; a manual session on Claude Code documented in the adapter README | Claude Code adapter `supported`; `0.3.0` released |
| **P4 — Codex, Cline** | Adapters per §8.2–8.3 using the MCP transport; snippets only; manual host runs | Both `supported` (or `experimental` with documented gaps); `0.4.0` |
| **P5 — OpenCode, Copilot, optional wheel** | Adapters per §8.4–8.5; wheel per §9.4 if the payload fallback is accepted | `0.5.0` |
| **P6 — 1.0 readiness** | API freeze, deprecations, envelope default, signing, LICENSE, host matrix, runtime-smoke green | `1.0.0-rc.1` → `1.0.0` |

---

## 18. Definition of Done (Plugin Packaging Phase)

The phase (P0–P3) is done when **all** of the following hold:

1. The refactor is committed; `.gitattributes` enforces LF; the tree is clean at release.
2. `python plugins/ui-engineering/packaging/build.py` produces zip and tar.gz archives, a package manifest, build info and `SHA256SUMS` for the committed `VERSION`, with byte-identical results on Linux and Windows (V14).
3. `python plugins/ui-engineering/packaging/verify.py <archive>` passes V1–V13 in a clean environment from an unrelated working directory, including the read-only install and core-without-plugin checks.
4. The artifact contains exactly the package file list: no tests, caches, `.pyc`, evidence, captures, helper temporaries, benchmark/eval outputs, local config or VCS data (V2).
5. The tool registry has complete JSON Schemas with enforced type validation, annotations and the `accessibility_scan` tool. Every tool passes the smoke test (V8).
6. The error model of §13 is implemented additively. Existing CLI outputs and exit codes are unchanged (V9 + existing tests).
7. The generic adapter and MCP transport pass `self_test`. The Claude Code adapter bundle exports deterministically, passes `self_test`, and is documented as `supported` after a manual run on the real host.
8. No adapter imports anything but `uiux.api`/`uiux.__version__`; no adapter contains design logic (architecture tests + review).
9. The safety checks of §14 are automated (no install commands, empty browser cache after runs, no writes to the package root).
10. CI workflows `ci` and `package` run on every push and are required.
11. Docs are updated: this spec (status → implemented, deviations recorded), `plugin-architecture.md`, `plugin/*/README.md`, `CHANGELOG.md`.
12. All §21 invariants still hold. The full existing test suite (89 tests at audit time) passes, plus the new tests of §20.

---

## 19. Technical debt

### 19.1 Must fix before packaging (P0–P2)

| Debt | Why it blocks | Fix |
|---|---|---|
| Uncommitted refactor (F1) | Reproducible builds need a commit | Commit (P0) |
| Mixed line endings, no `.gitattributes` (F2) | Checksums differ per OS | `.gitattributes` + renormalize (P0) |
| No error codes; tracebacks can escape (F5) | Adapters need machine-readable errors | §13 additive implementation (P2) |
| No parameter type validation (F6) | Hosts send schema-driven args; wrong types reach implementations | Stdlib schema validation in `call_tool` (P2) |
| Tests hard-wired to the source root (F10) | Cannot test an artifact | `UIUX_TEST_ROOT` + git-optional skips (P1) |
| Python floor unproven (F9) | Declared requirement may be false | CI matrix or raise the floor (P2) |
| `plugin.schema.json` is only a required-field list | Manifest validation in V5 is weak | Full JSON Schema + stdlib validator (P2) |

### 19.2 Can wait (after P3, before 1.0.0 unless noted)

| Debt | Note |
|---|---|
| Accessibility scan gating on `package_present` (F7) | Scheduled in P2 because the new tool needs it. Otherwise later. |
| Browser detection relies on default cache locations | `browser.preflight_browser_check` escape hatch exists |
| `uiux.knowledge.catalog` reads config at import time | Only matters when `UIUX_CONFIG` changes mid-process |
| Registry rows include `line` numbers (diff churn) | Informational field; could move to a sidecar |
| Unused imports in `uiux/runtime/browser.py`; `detect` probes `python` on PATH instead of `sys.executable` | Cosmetic / minor accuracy |
| Generic adapter requires exact version equality | Replace with `core_version` range from `adapter.json` in P2 |
| `describe_architecture` returns an absolute `package_root` | Fine locally; adapters should not forward it to remote services |
| Skill name vs package id (F4) | Documented mapping; revisit only with a host requirement |

### 19.3 Must fix before `1.0.0`

- LICENSE decided and packaged (F8); manifest `license` updated.
- Error envelope as the CLI default (breaking, announced in `0.9.x`).
- Artifact signing and a verification guide.
- Supported host matrix with tested host versions.
- Live runtime verification (`runtime-smoke`) green at least once per release.
- Deprecation cleanup of any field marked deprecated during `0.x`.

---

## 20. New tests and evals

| Test (file) | Asserts |
|---|---|
| `tests/test_packaging_build.py` | Build from a temp git repo (created in the test from the source tree) is deterministic (two builds → identical sha256); dirty-tree refusal; stale registry refusal; version/CHANGELOG mismatch refusal; archive entries sorted, prefixed, normalized mtime/mode |
| `tests/test_packaging_verify.py` | `verify.py` passes on a good artifact; fails with the right code on a tampered file (`INTEGRITY_FAILURE`), an injected `.pyc`, `tests/` or `.evidence` file (whitelist), a manifest version change (`VERSION_MISMATCH`), and an invalid manifest (`MANIFEST_INVALID`) |
| `tests/test_error_model.py` | Each §13 code is produced by its trigger; CLI output keeps `status: INVALID_CALL` + string `error` and adds `error_code`; `INTERNAL_ERROR` never prints a traceback to stdout |
| `tests/test_tool_schemas.py` | Every tool input is valid JSON Schema (subset); type validation rejects mistyped params; `annotations` present and consistent with side effects |
| `tests/test_mcp_transport.py` | Scripted JSON-RPC session over subprocess stdio: `initialize`, `tools/list` equals the registry, `tools/call` success, invalid tool → `isError` with envelope, no stdout noise |
| `tests/test_adapter_contract.py` | For every `plugins/ui-engineering/adapters/*/adapter.json`: schema-valid; status honesty (`planned` adapters have no code); imports allowlist; `self_test` passes; `export` deterministic and only writes rendered files listed in `rendered_files` plus the package file list; no knowledge ids or design constants in adapter code |
| `tests/test_install_readonly.py` | Read-only extracted root: validate_skill, run_evals and tool smoke pass; no write attempts |
| `tests/test_safety.py` | No install/download command strings in packaged code paths; browser cache dir untouched after runtime tool calls; `run_runtime` never starts a process without `allow_start` + argv |
| Eval scenario **E81** (agent-behavior) | "Host without Playwright asks for rendered evidence": the agent reports `BLOCKED` with the code and remediation, does not install anything |
| Eval scenario **E82** (agent-behavior) | "Adapter version mismatch": the agent surfaces `VERSION_MISMATCH` and does not fall back to internal modules |

New scenarios follow the existing frontmatter contract. The validator's expected range (`E01–E80`) is updated to `E01–E82` in the same change.

---

## 21. Invariants — do not change without a demonstrated regression reason

1. **Markdown stays where it is.** `SKILL.md`, `workflow/`, `phase-1/`, `phase-2/` (including `phase-2/knowledge`, `motion`, `web-patterns`), `review/`, `templates/`, `execution/`, `evals/` and `docs/` keep their paths. They are path contracts (relative links, reference index, E01–E80 `expected_context`). Distribution layouts (host bundles, wheel payload) copy them at build time; the source tree is never rearranged for packaging.
2. **No design/business logic in adapters or the plugin layer.** Adapters map, normalize, install and document; all decisions stay in `uiux`.
3. **Compatibility scripts stay.** All `scripts/*.py` names, CLIs, outputs and import aliases (§12) keep working; `scripts/` never contains a module named `uiux`.
4. **`VERSION` is the single source of truth** for the version; everything else reads or is checked against it.
5. **`uiux.api` is the only Core API for adapters.** No adapter or plugin tool imports `uiux.core`, `uiux.knowledge`, `uiux.engine`, `uiux.runtime`, `uiux.evals` or `uiux.tooling`.
6. **The core never depends on the plugin layer.** A distribution without `plugin/` keeps working (V12).
7. **Optional runtime stays optional.** No install, no download, no Playwright import in Python; `BLOCKED` is an honest result.
8. **Tool ids, knowledge ids and collection names are stable.** Changes follow §15.
9. **Deterministic behavior.** Resolver and analyzer outputs for identical inputs and knowledge stay byte-identical across refactors (the check used during the plugin-ready refactor: compare against the previous commit's outputs).
10. **Package-relative paths only.** No absolute or machine-specific paths in code, config, manifests, templates or artifacts; resource discovery stays in `uiux.core.resources`.

---

## Appendix A — Command reference (target state)

```bash
# development (existing)
python -m unittest discover -s tests
python scripts/validate_skill.py
python scripts/knowledge_lib.py check
python plugins/ui-engineering/packaging/package_files.py --list

# packaging (new)
python plugins/ui-engineering/packaging/build.py --out dist/
python plugins/ui-engineering/packaging/verify.py dist/<version>/ui-ux-design-<version>.zip
python plugins/ui-engineering/packaging/release.py --out dist/          # build + verify + adapter bundles; never publishes

# adapters (new)
python plugins/ui-engineering/adapters/mcp/server.py                    # stdio MCP server over uiux.api
python plugins/ui-engineering/.claude-plugin/export.py --out dist/<version>/adapters/
python plugins/ui-engineering/adapters/generic/adapter.py self-test
```

## Appendix B — Implementation checklist per file

| File | Action | Phase |
|---|---|---|
| `.gitattributes` | create (`* text=auto eol=lf`, `*.png binary`) | P0 |
| `tests/_paths.py` | honor `UIUX_TEST_ROOT` | P1 |
| `plugins/ui-engineering/schemas/*.schema.json` | create (package-manifest, build-info, error, adapter) | P1–P2 |
| `plugins/ui-engineering/packaging/build.py`, `verify.py` | create | P1 |
| `uiux/api.py` | `ToolError` fields; type validation; `INTERNAL_ERROR` guard; `accessibility_scan` | P2 |
| `uiux/core/tools.json` | complete schemas; annotations; `accessibility_scan` | P2 |
| `uiux/cli.py` | additive `error_code`/`category`/`remediation`; `--error-format envelope` | P2 |
| `uiux/runtime/accessibility.py` | gate on `runtime_state` (behavior aligned with the runner; document in CHANGELOG) | P2 |
| `plugins/ui-engineering/plugin.json`, `plugin.schema.json` | `capability_map`, `adapters` with status, `schemas`, `artifacts`; full schema | P2 |
| `plugins/ui-engineering/adapters/generic/adapter.json`, `adapter.py` | metadata, version range, `self-test` | P2 |
| `plugins/ui-engineering/adapters/mcp/*` | create | P3 |
| `plugins/ui-engineering/.claude-plugin/*` | create | P3 |
| `plugins/ui-engineering/packaging/release.py` | create | P3 |
| `.github/workflows/{ci,package,release}.yml` | create | P2–P3 |
| `uiux/tooling/validate.py` | scenario range when E81/E82 are added; new plugin files in the conditional plugin list | P2+ |
| `CHANGELOG.md`, `docs/plugin-architecture.md`, READMEs | update per phase | all |

## Codex Implementation Status
Codex implementation phase: COMPLETE
Live host verification: PENDING
Public distribution readiness: NOT CLAIMED
