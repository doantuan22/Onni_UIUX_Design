# Packaging: build and verification

Implements spec phases P0–P2 plus the experimental shared MCP transport smoke checks ([docs/plugin-packaging-spec.md](../../../development/docs/plugin-packaging-spec.md)). Release archives are the primary distribution format. Nothing is published, tagged or installed by these tools.

| File | Role |
|---|---|
| [package-rules.json](package-rules.json) | **The single packaging contract**: selection (`exclude_layers`, `exclude_dirs`, `exclude_globs`), required files (`must_include`), forbidden prefixes (`must_exclude_prefixes`) and artifact metadata (`artifact`: formats, naming, output dirs, file mode, compression, timestamps, binary globs). Layers come from `uiux/core/layers.json`. |
| [package_files.py](package_files.py) | Computes the file list from the contract (`--list` adds paths and layers) |
| [artifact.py](artifact.py) | Shared primitives: glob matching, LF normalization, hashing, deterministic zip/tar.gz writers, safe extraction, JSON-Schema subset validator |
| [build.py](build.py) | Deterministic builder (release and developer modes) |
| [verify.py](verify.py) | Verification of an extracted artifact (V1–V14) |
| [../schemas/](../schemas/README.md) | `PACKAGE-MANIFEST.json` and build-info schemas |

## How to build

```bash
python plugins/ui-engineering/packaging/build.py                    # release build of HEAD -> dist/<version>/
python plugins/ui-engineering/packaging/build.py --commit v0.2.0    # release build of another commit/tag
python plugins/ui-engineering/packaging/build.py --dev              # developer build of the working tree -> dist/dev/<version>/
python plugins/ui-engineering/packaging/build.py --verify           # build, then run verify.py on the zip
python plugins/ui-engineering/packaging/build.py --out <dir> --formats zip,tar.gz --repo <repo-root>
```

All commands work from any working directory. Exit codes: `0` built, `1` refused or failed (JSON error with a stable `code`), `2` verification failed.

## Release build vs developer build

| | Release (default) | Developer (`--dev`) |
|---|---|---|
| Source | `git archive` of a commit, extracted into a staging dir in the system temp directory | The working tree as it is |
| Clean tree | **Required.** Any modified or untracked file refuses the build with `DIRTY_TREE` and `COMMIT_REQUIRED_BEFORE_RELEASE_BUILD`. | Allowed; `worktree_clean` is recorded |
| Contract used | The committed `package-rules.json` and layer map, run from the staged tree | The working tree's own |
| Timestamps | Commit time (`SOURCE_DATE_EPOCH` overrides) | `artifact.dev_source_date_epoch` (1980-01-02) or `SOURCE_DATE_EPOCH` |
| Names | `ui-ux-design-<version>.{zip,tar.gz}` in `dist/<version>/` | `ui-ux-design-<version>-dev.{zip,tar.gz}` in `dist/dev/<version>/` |
| Metadata | `build_mode: "release"`, `release: true` | `build_mode: "dev"`, `release: false` |
| `verify.py --require-release` | passes | **fails** (`NOT_A_RELEASE`) |

Both modes run the same preflight on the tree being packaged: the tree's own `package_files.py` must PASS, `scripts/knowledge_lib.py check` must pass (the knowledge registry is fresh and never regenerated silently), `VERSION` must equal the plugin manifest version, the manifest must match its schema, and `CHANGELOG.md` must have a `## <version>` section. The source tree is never modified.

**Commit requirement.** Release builds need a committed, clean repository root. Commit the change set first; after introducing `.gitattributes`, commit with `git add --renormalize .` so every text file is stored with LF.

## Artifact structure

```text
dist/<version>/
├── ui-ux-design-<version>.zip                    deterministic zip (sorted entries, fixed time/mode, Unix host)
├── ui-ux-design-<version>.tar.gz                 same content as tar (uid/gid 0, fixed mtime) + gzip (mtime 0, no name)
├── ui-ux-design-<version>.package-manifest.json  byte-identical copy of the embedded PACKAGE-MANIFEST.json
├── ui-ux-design-<version>.build-info.json        environment record (Python, platform, zlib, archive hashes)
├── ui-ux-design-<version>.verify-report.json     written by verify.py
└── SHA256SUMS                                     archives + package manifest (GNU coreutils format)

ui-ux-design-<version>/            single top-level directory inside each archive = the package root
├── PACKAGE-MANIFEST.json          name, skill_name, python_package, version, manifest_version, build_mode,
│                                  release, source {kind, commit, worktree_clean}, source_date_epoch,
│                                  rules_sha256, file_count, files [{path, size, sha256, layer, mode}]
├── SKILL.md, VERSION, CHANGELOG.md, uiux/, scripts/, plugin/, workflow/, phase-1/, phase-2/, review/,
└── templates/, execution/, evals/, docs/          (exactly the package file list)
```

Excluded: `tests/`, `.git/`, `.github/`, `.gitignore`, `.gitattributes`, caches (`__pycache__`, `*.pyc`), runtime evidence (`.evidence/`) and helper temporaries, benchmark/eval outputs, logs, temporary files, local config, virtualenvs, IDE folders, `dist/`, `build/` and staging directories. Evals fixtures are packaged on purpose: they are inputs to `run_evals` and `validate_skill`.

**Name ownership:** the package id `ui-ux-design` comes from `plugins/ui-engineering/plugin.json`; the skill name `ui-ux-workflow` comes from the `SKILL.md` frontmatter; the Python package is `uiux`. All three are recorded in `PACKAGE-MANIFEST.json`. None is renamed by packaging.

**Version source:** `VERSION` only. The build copies it into every name and metadata file and refuses mismatches.

## Checksums

- Per file: `PACKAGE-MANIFEST.json` → `files[].sha256`, computed on the normalized bytes that are archived.
- Per artifact: `SHA256SUMS` covers both archives and the package manifest. `build-info.json` is deliberately **not** listed, because it records the build machine (Python version, platform), which differs between otherwise identical builds.
- Content digest: `build-info.content_sha256` = sha256 of `PACKAGE-MANIFEST.json`. It is identical for identical content on every OS.

Verify manually: `sha256sum -c SHA256SUMS` (Linux/macOS) or `Get-FileHash -Algorithm SHA256` (Windows).

## How to verify an artifact

```bash
python plugins/ui-engineering/packaging/verify.py dist/<version>/ui-ux-design-<version>.zip --require-release --tests tests
python plugins/ui-engineering/packaging/verify.py --installed <extracted-root>        # an existing install (bytecode caches ignored)
python plugins/ui-engineering/packaging/verify.py <archive> --quick                  # structural checks V1-V5 only
```

The verifier extracts the archive into a fresh temp directory (rejecting absolute, `..`, backslash and symlink members). It then runs every check with the **artifact's own** scripts, from an unrelated working directory, with `PYTHONPATH`/`UIUX_ROOT`/`UIUX_CONFIG` removed, bytecode writes disabled and an empty `PLAYWRIGHT_BROWSERS_PATH`. After a structural failure (V1–V5) the behavioral checks are reported `NOT_RUN`.

| Check | What it proves |
|---|---|
| V1 | every file matches `PACKAGE-MANIFEST.json` (hash, size, set, canonical order); manifest schema-valid |
| V2 | the artifact's own selection contract accepts exactly the present files; required present; forbidden absent |
| V3 | `import uiux`, `uiux.api` works and loads no runtime/engine/evals/tooling module |
| V4 | VERSION = `uiux.__version__` = plugin manifest = PACKAGE-MANIFEST = archive/top-dir name; CHANGELOG section; name ownership; release flag |
| V5 | plugin manifest valid against its full schema; referenced paths exist; tool and knowledge registries readable and consistent |
| V6 | `scripts/validate_skill.py` passes |
| V7 | `run_evals` automated suites pass |
| V8 | every registered tool works (including `accessibility_scan`, `capability_map` and `self_test`), listing matches the registry, typed/unknown/missing calls return additive structured error envelopes with `INVALID_CALL` and exit 3; no evidence written; no browser download |
| V9 | the 9 compatibility scripts and `uiux_cli.py` run with their documented commands |
| V10 | generic adapter describe/call/unknown-tool plus MCP stdio initialize/ping/tool discovery/tool invocation, public `self_test`, unknown-tool envelope and a valid `BLOCKED` runtime result. Platform adapters are intentionally not implemented. |
| V11 | validation, evals and tool smoke on a read-only copy; any write inside the package root fails. On POSIX the OS enforces it; on Windows files are read-only and directory writes are detected by snapshot. |
| V12 | the same checks on a copy without `plugin/` |
| V13 | the test suite (`--tests <dir>`, not packaged) run against the extracted root via `UIUX_TEST_ROOT` |
| V14 | `NOT_RUN` locally; the `package` CI workflow compares builds from Linux and Windows |

## Cross-platform reproducibility assumptions

- **Line endings:** `.gitattributes` stores text with LF (`* text=auto eol=lf`, binaries marked). Release builds call `git archive` with `core.autocrlf=false`. The builder also normalizes CRLF→LF for every non-binary file it reads, so a Windows working tree and a Linux checkout produce the same content hashes.
- **Paths:** archive members are canonical POSIX paths under one top-level directory. The code uses `pathlib` and never `os.sep` or backslashes. Entries are sorted by UTF-8 bytes.
- **Metadata:** fixed timestamps (commit time, or a fixed dev epoch), mode `0644`, zip host system "Unix", tar uid/gid 0 with empty owner names, gzip header mtime 0 with no file name. ZIP stores time with 2-second resolution.
- **Byte identity vs content identity:** the same commit built on the same platform and Python/zlib gives byte-identical archives (tested). Across operating systems the **content** (`PACKAGE-MANIFEST.json`, every file hash) is always identical. Archive bytes are identical when both machines use the same deflate implementation; a different zlib build (e.g. zlib-ng) can change compressed bytes without changing content. The `package` workflow requires content identity and reports archive byte identity.
- **Executed locally:** Windows 11, Python 3.11.9, git 2.55 (all tests, dev and release builds, full verification). **Not executed locally:** Linux and macOS runs, Python 3.9 and 3.13, and the cross-OS comparison. They are configured in `.github/workflows/ci.yml` and `package.yml`.
