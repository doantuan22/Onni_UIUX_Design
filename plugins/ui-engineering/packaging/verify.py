"""Verify a built artifact after extracting it into a clean directory (docs/plugin-packaging-spec.md §11, V1-V14).

    python plugins/ui-engineering/packaging/verify.py dist/<version>/ui-ux-design-<version>.zip [--require-release]
    python plugins/ui-engineering/packaging/verify.py --installed <extracted-root>
    options: --quick (V1-V5 only) --tests <dir> | --no-tests  --report <file>  --keep  --python <exe>

Every check runs the *artifact's own* scripts in subprocesses from an unrelated working directory with a clean
environment (no PYTHONPATH/UIUX_ROOT/UIUX_CONFIG, no bytecode writes, an empty PLAYWRIGHT_BROWSERS_PATH), so the
result does not depend on the source repository or the caller's cwd. Statuses: PASS, FAIL, NOT_RUN (with reason),
NOT_APPLICABLE. The overall status is PASS only when no check FAILs; NOT_RUN checks are listed, never hidden.
Exit codes: 0 PASS, 2 FAIL, 1 unusable input (JSON error).
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import artifact  # noqa: E402
from artifact import PackagingError  # noqa: E402

AUTO = object()
RUNTIME_STATES = {"NOT_DECLARED", "DECLARED_NOT_INSTALLED", "PACKAGE_AVAILABLE_BROWSER_MISSING", "READY"}
HEAVY_MODULE_PREFIXES = ("uiux.runtime", "uiux.engine", "uiux.evals", "uiux.tooling")
STRUCTURAL = ("V1", "V2", "V3", "V4", "V5")
NAMES = {
    "V1": "integrity (PACKAGE-MANIFEST hashes, file set, canonical paths)",
    "V2": "whitelist (required present, forbidden absent, selection contract)",
    "V3": "import uiux / uiux.api without side effects",
    "V4": "version and identity consistency",
    "V5": "manifest schema and references; tool and knowledge registries readable",
    "V6": "validate_skill",
    "V7": "run_evals automated suites",
    "V8": "tool registry smoke",
    "V9": "compatibility scripts",
    "V10": "adapter smoke",
    "V11": "read-only install",
    "V12": "core without plugin/",
    "V13": "test suite against the artifact",
    "V14": "cross-OS reproducibility",
}


class Verifier:
    def __init__(self, root: Path, workspace: Path, python: str) -> None:
        self.root, self.workspace, self.python = root, workspace, python
        self.browsers = workspace / "empty-playwright-browsers"
        self.browsers.mkdir(exist_ok=True)
        self.cwd = workspace / "cwd"
        self.cwd.mkdir(exist_ok=True)

    def env(self, **extra: str) -> dict:
        env = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "UIUX_ROOT", "UIUX_CONFIG", "UIUX_TEST_ROOT"}}
        env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8",
                    "PLAYWRIGHT_BROWSERS_PATH": str(self.browsers)}, **extra)
        return env

    def run(self, args: list[str], timeout: int = 900, **env: str) -> subprocess.CompletedProcess:
        return subprocess.run([self.python, *args], capture_output=True, text=True, encoding="utf-8",
                              cwd=self.cwd, env=self.env(**env), timeout=timeout)

    def cli(self, root: Path, *args: str) -> tuple[int, dict | None, str]:
        result = self.run([str(root / "scripts/uiux_cli.py"), *args])
        try:
            data = json.loads(result.stdout)
        except ValueError:
            data = None
        return result.returncode, data, (result.stdout + result.stderr)[-800:]


# --------------------------------------------------------------------------- structural checks
def _files_on_disk(root: Path, metadata_file: str, ignore_caches: bool = False) -> dict[str, Path]:
    """Files under root except the metadata file. Installed roots may hold bytecode caches written after install."""
    found = {}
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            if rel == metadata_file or (ignore_caches and ("__pycache__" in rel.split("/") or rel.endswith(".pyc"))):
                continue
            found[rel] = path
    return found


def check_integrity(root: Path, manifest: dict, metadata_file: str, ignore_caches: bool = False) -> list[str]:
    problems = artifact.validate_schema(manifest, json.loads(
        (root / "schemas/package-manifest.schema.json").read_text(encoding="utf-8")))
    listed = {item["path"]: item for item in manifest.get("files", [])}
    on_disk = _files_on_disk(root, metadata_file, ignore_caches)
    problems += [f"file not in PACKAGE-MANIFEST: {p}" for p in sorted(set(on_disk) - set(listed))]
    problems += [f"file missing from artifact: {p}" for p in sorted(set(listed) - set(on_disk))]
    for rel in sorted(set(listed) & set(on_disk)):
        try:
            artifact.canonical_path(rel)
        except PackagingError as exc:
            problems.append(exc.message)
        data = on_disk[rel].read_bytes()
        if artifact.sha256(data) != listed[rel]["sha256"] or len(data) != listed[rel]["size"]:
            problems.append(f"content differs from PACKAGE-MANIFEST: {rel}")
    if manifest.get("file_count") != len(listed):
        problems.append("file_count does not match files")
    order = [item["path"] for item in manifest.get("files", [])]
    if order != sorted(order, key=lambda p: p.encode("utf-8")):
        problems.append("files are not in canonical order")
    return problems


def check_whitelist(v: Verifier, root: Path, metadata_file: str, ignore_caches: bool = False) -> list[str]:
    result = v.run([str(root / "packaging/package_files.py"), "--list"])
    try:
        selection = json.loads(result.stdout)
    except ValueError:
        return [f"package_files.py failed: {(result.stdout + result.stderr)[-500:]}"]
    problems = list(selection.get("problems", []))
    present = set(_files_on_disk(root, metadata_file, ignore_caches))
    allowed = set(selection.get("included", []))
    problems += [f"forbidden or unselected file present: {p}" for p in sorted(present - allowed)]
    problems += [f"selected file absent: {p}" for p in sorted(allowed - present)]
    return problems


def frontmatter_name(root: Path) -> str | None:
    match = re.match(r"^---\n(.*?)\n---", (root / "SKILL.md").read_text(encoding="utf-8"), re.DOTALL)
    return next((line.split(":", 1)[1].strip() for line in (match.group(1).splitlines() if match else [])
                 if line.startswith("name:")), None)


def check_identity(root: Path, manifest: dict, core: dict, archive_base: str | None, require_release: bool) -> list[str]:
    problems = []
    version = (root / "VERSION").read_text(encoding="utf-8").strip()
    plugin = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    rules = artifact.load_rules(root)
    values = {"VERSION": version, "uiux.__version__": core.get("version"), "plugin.json": plugin.get("version"),
              "PACKAGE-MANIFEST": manifest.get("version")}
    if len(set(values.values())) != 1:
        problems.append(f"version mismatch: {values}")
    if manifest.get("name") != plugin.get("name"):
        problems.append("package name differs from plugin manifest")
    if manifest.get("skill_name") != frontmatter_name(root):
        problems.append("skill_name differs from SKILL.md frontmatter")
    if manifest.get("manifest_version") != plugin.get("manifest_version"):
        problems.append("manifest_version differs from plugin manifest")
    expected = f"{plugin.get('name')}-{version}" + (rules["artifact"]["dev_suffix"] if manifest.get("build_mode") == "dev" else "")
    if archive_base is not None and root.name != expected:
        problems.append(f"top-level directory {root.name!r} != {expected!r}")
    if archive_base is not None and archive_base != expected:
        problems.append(f"archive name {archive_base!r} != {expected!r}")
    if manifest.get("release") != (manifest.get("build_mode") == "release"):
        problems.append("release flag inconsistent with build_mode")
    if require_release and manifest.get("build_mode") != "release":
        problems.append("NOT_A_RELEASE: developer artifact where a release artifact is required")
    if not re.search(rf"^## {re.escape(version)}\b", (root / "CHANGELOG.md").read_text(encoding="utf-8"), re.MULTILINE):
        problems.append(f"CHANGELOG.md has no '## {version}' section")
    return problems


def check_manifest(root: Path) -> list[str]:
    plugin = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    schema = json.loads((root / "schemas/plugin.schema.json").read_text(encoding="utf-8"))
    problems = artifact.validate_schema(plugin, schema)
    paths = [plugin["knowledge"]["registry"], plugin["knowledge"].get("index"), plugin["tools"]["registry"],
             plugin["evals"]["scenarios"], plugin["runtime"].get("contracts"),
             plugin.get("configuration", {}).get("defaults"), plugin.get("packaging", {}).get("rules"),
             *plugin["compatibility"].get("backward_compatible_cli", []),
             *[e["path"] for e in plugin["entrypoints"].values() if isinstance(e, dict) and "path" in e]]
    problems += [f"manifest references missing path: {p}" for p in paths if p and not (root / p).exists()]
    try:
        tools = json.loads((root / plugin["tools"]["registry"]).read_text(encoding="utf-8"))["tools"]
        ids = {t["id"] for t in tools}
        problems += [f"tool entrypoint not in uiux.api: {t['id']}" for t in tools if not t["entrypoint"].startswith("uiux.api:")]
        problems += [f"entrypoint tool missing: {e['tool']}" for e in plugin["entrypoints"].values()
                     if isinstance(e, dict) and "tool" in e and e["tool"] not in ids]
        if plugin["evals"]["entry_tool"] not in ids:
            problems.append("evals.entry_tool is not a registered tool")
    except (OSError, ValueError, KeyError) as exc:
        problems.append(f"tool registry unreadable: {exc}")
    try:
        registry = json.loads((root / plugin["knowledge"]["registry"]).read_text(encoding="utf-8"))
        if set(registry["collections"]) != set(plugin["knowledge"]["collections"]):
            problems.append("knowledge registry collections differ from manifest")
        if not registry["entries"]:
            problems.append("knowledge registry is empty")
    except (OSError, ValueError, KeyError) as exc:
        problems.append(f"knowledge registry unreadable: {exc}")
    return problems


# --------------------------------------------------------------------------- behavioral checks
def smoke(v: Verifier, root: Path, full: bool = True) -> list[str]:
    problems: list[str] = []
    profile = json.loads((root / "evals/resolver-scenarios/developer-tool.json").read_text(encoding="utf-8"))["profile"]
    fixture = root / "evals/runtime-fixtures/playwright-ready"
    calls = [
        ("retrieve_knowledge", {"ids": ["style.swiss"]}, lambda d: d["entries"][0]["id"] == "style.swiss"),
        ("resolve_capabilities", {"profile": profile}, lambda d: d["style"]["primary"]["id"].startswith("style.")),
        ("resolve_technology", {"capabilities": ["motion.m1-hover"]},
         lambda d: d["assignments"]["motion.m1-hover"]["technology"] == "tech.css"),
        ("analyze_design_quality", {"project": str(root / "evals/fixtures/quality/restrained")},
         lambda d: d["evals"]["E66"]["status"] == "PASS"),
    ]
    if full:
        calls += [
            ("detect_runtime", {"project": str(fixture)}, lambda d: d["playwright"]["runtime_state"]["state"] in RUNTIME_STATES),
            ("run_runtime", {"request": {"session_id": "verify-dry", "base_url": "http://127.0.0.1:9",
                                         "routes": [{"page_id": "P", "route": "/"}], "viewports": ["desktop"]},
                             "project": str(fixture), "dry_run": True},
             lambda d: d["summary"]["status"] == "DRY_RUN"),
            ("accessibility_scan", {"request": {"session_id": "verify-dry", "base_url": "http://127.0.0.1:9",
                                                "routes": [{"page_id": "P", "route": "/"}], "viewports": ["desktop"]},
                                    "project": str(fixture), "dry_run": True},
             lambda d: d["summary"]["status"] == "DRY_RUN" and d["summary"]["runtime_state"] in RUNTIME_STATES),
            ("run_evals", {"suites": ["knowledge"]}, lambda d: d["status"] == "PASS"),
            ("validate_skill", {}, lambda d: d["status"] == "PASS"),
            ("capability_map", {}, lambda d: d["capabilities"] and all(
                c["availability"] == ("UNKNOWN" if c["kind"] == "runtime-dependent" else "AVAILABLE")
                for c in d["capabilities"].values())),
            ("self_test", {}, lambda d: d["status"] == "PASS"),
        ]
    for tool, params, ok in calls:
        code, data, tail = v.cli(root, "call", tool, "--params", json.dumps(params))
        try:
            passed = code == 0 and data is not None and ok(data)
        except (KeyError, IndexError, TypeError):
            passed = False
        if not passed:
            problems.append(f"{tool}: exit {code}: {tail}")
    if full:
        if (fixture / ".evidence").exists():
            problems.append("run_runtime dry-run wrote evidence")
        code, data, _ = v.cli(root, "tools")
        registry = json.loads((root / "uiux/core/tools.json").read_text(encoding="utf-8"))["tools"]
        if code != 0 or not data or len(data["tools"]) != len(registry):
            problems.append("`tools` listing differs from the tool registry")
        invalid = ((("call", "does-not-exist"), "UNKNOWN_TOOL"),
                   (("call", "resolve_capabilities", "--params", "{}"), "MISSING_REQUIRED_ARGUMENT"),
                   (("call", "retrieve_knowledge", "--params", '{"ids": "style.swiss"}'), "INVALID_ARGUMENT_TYPE"),
                   (("call", "retrieve_knowledge", "--params", '{"nope": 1}'), "UNEXPECTED_ARGUMENT"))
        for args, expected in invalid:
            code, data, tail = v.cli(root, *args)
            if (code != 3 or not data or data.get("status") != "INVALID_CALL" or data.get("error_code") != expected
                    or not data.get("remediation") or "Traceback" in tail):
                problems.append(f"invalid call {args[1:]} not rejected with INVALID_CALL/{expected}/exit 3: {tail}")
        if any(v.browsers.iterdir()):
            problems.append("a browser cache was written (download attempted)")
    return problems


def check_compat_scripts(v: Verifier, root: Path) -> list[str]:
    fixture = root / "evals/runtime-fixtures/playwright-ready"
    request = v.workspace / "dry-request.json"
    request.write_text(json.dumps({"session_id": "verify-compat", "base_url": "http://127.0.0.1:9",
                                   "routes": [{"page_id": "P", "route": "/"}], "viewports": ["desktop"]}), encoding="utf-8")
    s = root / "scripts"
    commands = {
        "validate_skill.py": [str(s / "validate_skill.py")],
        "knowledge_lib.py": [str(s / "knowledge_lib.py"), "check"],
        "resolve_capabilities.py": [str(s / "resolve_capabilities.py"), "--profile", str(root / "evals/resolver-scenarios/developer-tool.json")],
        "analyze_design_quality.py": [str(s / "analyze_design_quality.py"), str(root / "evals/fixtures/quality/restrained")],
        "detect_capabilities.py": [str(s / "detect_capabilities.py"), str(fixture)],
        "run_browser_execution.py": [str(s / "run_browser_execution.py"), "--input", str(request), "--project", str(fixture), "--dry-run"],
        "run_accessibility_scan.py": [str(s / "run_accessibility_scan.py"), "--input", str(request), "--project", str(fixture), "--dry-run"],
        "validate_runtime_evidence.py": [str(s / "validate_runtime_evidence.py"), str(root / "evals/runtime-fixtures/evidence-valid")],
        "validate_accessibility_evidence.py": [str(s / "validate_accessibility_evidence.py"), str(root / "evals/runtime-fixtures/accessibility/evidence-valid")],
        "uiux_cli.py": [str(s / "uiux_cli.py"), "version"],
    }
    problems = []
    for name, args in commands.items():
        result = v.run(args)
        if result.returncode != 0:
            problems.append(f"{name}: exit {result.returncode}: {(result.stdout + result.stderr)[-300:]}")
    return problems


def check_generic_adapter(v: Verifier, root: Path) -> list[str]:
    adapter = root / "adapters/generic/adapter.py"
    problems = []
    described = v.run([str(adapter), "describe"])
    try:
        if described.returncode != 0 or not json.loads(described.stdout)["tools"]:
            problems.append("generic adapter describe failed")
    except (ValueError, KeyError):
        problems.append(f"generic adapter describe output invalid: {described.stdout[-300:]}")
    called = v.run([str(adapter), "call", "retrieve_knowledge", "--params", '{"ids": ["style.swiss"]}'])
    if called.returncode != 0 or '"style.swiss"' not in called.stdout:
        problems.append("generic adapter call failed")
    unknown = v.run([str(adapter), "call", "does-not-exist"])
    if unknown.returncode != 3 or '"UNKNOWN_TOOL"' not in unknown.stdout:
        problems.append("generic adapter did not reject an unknown tool with UNKNOWN_TOOL and exit 3")
    tested = v.run([str(adapter), "self-test"])
    try:
        if tested.returncode != 0 or json.loads(tested.stdout)["status"] != "PASS":
            problems.append(f"generic adapter self-test failed: {tested.stdout[-300:]}")
    except (ValueError, KeyError):
        problems.append(f"generic adapter self-test output invalid: {tested.stdout[-300:]}")
    schema = json.loads((root / "schemas/adapter.schema.json").read_text(encoding="utf-8"))
    for metadata in sorted((root / "adapters").glob("*/adapter.json")):
        errors = artifact.validate_schema(json.loads(metadata.read_text(encoding="utf-8")), schema)
        problems += [f"{metadata.relative_to(root).as_posix()}: {error}" for error in errors]
    return problems


def check_mcp_transport(v: Verifier, root: Path) -> list[str]:
    """Run the real stdio server from an extracted artifact; stdout must contain only protocol replies."""
    server = root / "adapters/mcp/server.py"
    if not server.is_file():
        return ["MCP server missing"]
    project = v.workspace / "mcp-blocked-project"
    project.mkdir(exist_ok=True)
    request = {"session_id": "verify-mcp-blocked", "base_url": "http://127.0.0.1:9",
               "routes": [{"page_id": "P", "route": "/"}], "viewports": ["desktop"], "iteration": 1}
    messages = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                    "clientInfo": {"name": "artifact-verifier", "version": "1"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "retrieve_knowledge", "arguments": {"ids": ["style.swiss"]}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "nope", "arguments": {}}},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
         "params": {"name": "run_runtime", "arguments": {"request": request, "project": str(project)}}},
        {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "self_test", "arguments": {}}},
    ]
    process = subprocess.run([v.python, str(server)], input="\n".join(json.dumps(m) for m in messages) + "\n",
                             capture_output=True, text=True, encoding="utf-8", cwd=v.cwd, env=v.env(), timeout=120)
    problems: list[str] = []
    try:
        responses = [json.loads(line) for line in process.stdout.splitlines() if line.strip()]
    except ValueError as exc:
        return [f"MCP server stdout was not protocol-only JSON: {exc}: {process.stdout[-300:]}"]
    if process.returncode != 0:
        problems.append(f"MCP server exited {process.returncode}: {process.stderr[-300:]}")
    if len(responses) != 6:
        return problems + [f"MCP server produced {len(responses)} responses, expected 6"]
    by_id = {response.get("id"): response for response in responses}
    if by_id.get(1, {}).get("result", {}).get("protocolVersion") != "2025-06-18":
        problems.append("MCP initialize response is invalid")
    listed = by_id.get(2, {}).get("result", {}).get("tools", [])
    registry = [t for t in json.loads((root / "uiux/core/tools.json").read_text(encoding="utf-8"))["tools"]
                if t["visibility"] == "public"]
    if [t.get("name") for t in listed] != [t["id"] for t in registry]:
        problems.append("MCP tools/list differs from the public registry")
    if by_id.get(3, {}).get("result", {}).get("structuredContent", {}).get("entries", [{}])[0].get("id") != "style.swiss":
        problems.append("MCP tools/call did not return retrieve_knowledge content")
    unknown = by_id.get(4, {}).get("result", {})
    if not unknown.get("isError") or unknown.get("structuredContent", {}).get("error_code") != "UNKNOWN_TOOL":
        problems.append("MCP unknown tool did not preserve the public error envelope")
    blocked = by_id.get(5, {}).get("result", {})
    if blocked.get("isError") or blocked.get("structuredContent", {}).get("summary", {}).get("status") != "BLOCKED":
        problems.append("MCP BLOCKED runtime result was not returned as a valid tool result")
    if by_id.get(6, {}).get("result", {}).get("structuredContent", {}).get("status") != "PASS":
        problems.append("MCP self_test did not return the public health result")
    return problems


def _snapshot(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): (artifact.sha256_file(p) if p.is_file() else "<dir>")
            for p in sorted(root.rglob("*"))}


def _set_readonly(root: Path, readonly: bool) -> str:
    posix = os.name == "posix"
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_file():
            os.chmod(path, stat.S_IREAD if readonly else stat.S_IREAD | stat.S_IWRITE)
        elif posix:
            os.chmod(path, 0o555 if readonly else 0o755)
    if posix:
        os.chmod(root, 0o555 if readonly else 0o755)
    return "os-enforced (files and directories)" if posix else "files read-only; directory writes detected by snapshot"


def check_readonly(v: Verifier, root: Path) -> tuple[list[str], str]:
    copy = v.workspace / "readonly" / root.name
    shutil.copytree(root, copy)
    before = _snapshot(copy)
    mode = _set_readonly(copy, True)
    try:
        problems = []
        if v.run([str(copy / "scripts/validate_skill.py")]).returncode != 0:
            problems.append("validate_skill failed on a read-only install")
        code, data, tail = v.cli(copy, "call", "run_evals")
        if code != 0 or not data or data["status"] != "PASS":
            problems.append(f"run_evals failed on a read-only install: {tail}")
        problems += smoke(v, copy, full=False)
    finally:
        _set_readonly(copy, False)
    after = _snapshot(copy)
    changed = sorted(k for k in set(before) | set(after) if before.get(k) != after.get(k))
    problems += [f"write inside the package root: {p}" for p in changed]
    return problems, mode


def check_without_plugin(v: Verifier, root: Path) -> list[str]:
    copy = v.workspace / "no-plugin" / root.name
    shutil.copytree(root, copy, ignore=lambda d, names: ["plugin"] if Path(d) == root else [])
    problems = []
    result = v.run([str(copy / "scripts/validate_skill.py")])
    if result.returncode != 0:
        problems.append(f"validate_skill failed without plugin/: {result.stdout[-500:]}")
    code, data, tail = v.cli(copy, "call", "run_evals")
    if code != 0 or not data or data["status"] != "PASS":
        problems.append(f"run_evals failed without plugin/: {tail}")
    problems += smoke(v, copy, full=False)
    return problems


def run_tests(v: Verifier, root: Path, tests_dir: Path) -> tuple[list[str], str]:
    scratch = v.workspace / "tests-scratch" / "tests"
    shutil.copytree(tests_dir, scratch, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    result = v.run(["-m", "unittest", "discover", "-s", str(scratch), "-t", str(scratch)], timeout=3600,
                   UIUX_TEST_ROOT=str(root), UIUX_REPO_ROOT=str(tests_dir.parent.resolve()))
    tail = (result.stdout + result.stderr).strip().splitlines()[-3:]
    return ([] if result.returncode == 0 else [f"unit tests failed: {' | '.join(tail)}"]), " | ".join(tail)


# --------------------------------------------------------------------------- orchestration
def verify(archive: Path | None = None, installed: Path | None = None, require_release: bool = False,
           tests_dir: object = AUTO, python: str = sys.executable, keep: bool = False, quick: bool = False,
           report_path: Path | None = None) -> dict:
    workspace = Path(tempfile.mkdtemp(prefix="uiux-verify-"))
    checks: dict[str, dict] = {}

    def record(cid: str, status: str, detail: object = None) -> None:
        checks[cid] = {"id": cid, "name": NAMES[cid], "status": status, "detail": detail}

    def outcome(cid: str, problems: list[str], note: str | None = None) -> None:
        record(cid, "FAIL" if problems else "PASS", problems or note)

    def guarded(cid: str, function, *args, note: str | None = None) -> None:
        """Run one check; an exception (e.g. a required file missing) is a FAIL, never a crash."""
        try:
            outcome(cid, function(*args), note)
        except (OSError, ValueError, KeyError, TypeError, IndexError, PackagingError) as exc:
            record(cid, "FAIL", [f"check raised {type(exc).__name__}: {exc}"])

    root, manifest, archive_base = None, {}, None
    try:
        if archive is not None:
            archive = archive.resolve()
            archive_base = re.sub(r"\.(zip|tar\.gz)$", "", archive.name)
            root = artifact.safe_extract(archive, workspace / "extract")
        elif installed is not None:
            root = installed.resolve()
        else:
            raise PackagingError("INVALID_ARGUMENT", "an archive or --installed root is required")
        v = Verifier(root, workspace, python)
        metadata_file = artifact.load_rules(root)["artifact"]["metadata_file"]
        manifest_path = root / metadata_file
        if not manifest_path.is_file():
            raise PackagingError("MANIFEST_INVALID", f"{metadata_file} missing from the artifact")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        installed_mode = archive is None
        guarded("V1", check_integrity, root, manifest, metadata_file, installed_mode)
        guarded("V2", check_whitelist, v, root, metadata_file, installed_mode)
        probe = v.run(["-c", "import json, sys; sys.path.insert(0, sys.argv[1]); import uiux, uiux.api; "
                       "print(json.dumps({'version': uiux.__version__, 'heavy': sorted(m for m in sys.modules "
                       f"if m.startswith({HEAVY_MODULE_PREFIXES!r}))}}))", str(root)])
        try:
            core = json.loads(probe.stdout)
            outcome("V3", [f"importing uiux.api loaded {core['heavy']}"] if core["heavy"] else [],
                    f"uiux {core['version']} imported from {root.name}")
        except ValueError:
            core = {}
            outcome("V3", [f"import failed: {(probe.stdout + probe.stderr)[-500:]}"])
        guarded("V4", check_identity, root, manifest, core, archive_base, require_release)
        guarded("V5", check_manifest, root)

        structural_failed = any(checks[c]["status"] == "FAIL" for c in STRUCTURAL)
        later = ["V6", "V7", "V8", "V9", "V10", "V11", "V12", "V13"]
        if quick or structural_failed:
            reason = "--quick" if quick else "skipped after a structural failure (V1-V5)"
            for cid in later:
                record(cid, "NOT_RUN", reason)
        else:
            result = v.run([str(root / "scripts/validate_skill.py")])
            outcome("V6", [] if result.returncode == 0 else [result.stdout[-1500:]])
            code, data, tail = v.cli(root, "call", "run_evals")
            suites = {k: s["status"] for k, s in (data or {}).get("suites", {}).items()}
            outcome("V7", [] if code == 0 and data and data["status"] == "PASS" else [tail], suites)
            outcome("V8", smoke(v, root), "tool smoke, registry listing, typed parameter validation and structured "
                    "error envelopes (spec P2 contract hardening)")
            outcome("V9", check_compat_scripts(v, root))
            if (root / "adapters/generic/adapter.py").is_file():
                outcome("V10", check_generic_adapter(v, root) + check_mcp_transport(v, root),
                        "generic adapter, shared MCP stdio transport, and host adapter templates (claude-code, codex)")
            else:
                record("V10", "NOT_APPLICABLE", "artifact has no plugin/ adapters")
            problems, mode = check_readonly(v, root)
            outcome("V11", problems, f"read-only enforcement: {mode}")
            outcome("V12", check_without_plugin(v, root))
            if tests_dir is AUTO:
                candidate = _HERE.parents[2] / "tests"
                if not candidate.is_dir():
                    candidate = _HERE.parents[1] / "tests"
                tests_dir = candidate if candidate.is_dir() else None
            if tests_dir is None:
                record("V13", "NOT_RUN", "no tests directory available (tests are not packaged); pass --tests <dir>")
            else:
                problems, summary = run_tests(v, root, Path(tests_dir))
                outcome("V13", problems, summary)
        record("V14", "NOT_RUN", "cross-OS reproducibility needs builds on two operating systems "
               "(.github/workflows/package.yml); same-OS determinism is covered by tests/test_packaging_build.py")
    except PackagingError as exc:
        record("V1", "FAIL", [f"{exc.code}: {exc.message}"])
    finally:
        if not keep:
            _rmtree(workspace)

    ordered = [checks[c] for c in NAMES if c in checks]
    failed = [c["id"] for c in ordered if c["status"] == "FAIL"]
    report = {"schema_version": 1, "status": "FAIL" if failed else "PASS", "failed": failed,
              "not_run": [c["id"] for c in ordered if c["status"] == "NOT_RUN"],
              "artifact": str(archive) if archive else None, "installed_root": str(installed) if installed else None,
              "name": manifest.get("name"), "version": manifest.get("version"), "build_mode": manifest.get("build_mode"),
              "commit": (manifest.get("source") or {}).get("commit"),
              "environment": {"python": platform.python_version(), "platform": platform.platform()},
              "workspace": str(workspace) if keep else None, "checks": ordered}
    if report_path is None and archive is not None:
        report_path = archive.parent / f"{archive_base}.verify-report.json"
    if report_path is not None:
        Path(report_path).write_bytes(artifact.canonical_json(report))
        report["report_path"] = str(report_path)
    return report


def _force_remove(function, path, _info) -> None:  # Windows: read-only files block deletion
    os.chmod(path, stat.S_IWRITE)
    function(path)


def _rmtree(path: Path) -> None:
    if sys.version_info >= (3, 12):
        shutil.rmtree(path, onexc=_force_remove)
    else:
        shutil.rmtree(path, onerror=_force_remove)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Verify an extracted plugin artifact (V1-V14)")
    parser.add_argument("archive", nargs="?", type=Path)
    parser.add_argument("--installed", type=Path, help="verify an already extracted artifact root")
    parser.add_argument("--require-release", action="store_true", help="fail on developer artifacts")
    parser.add_argument("--quick", action="store_true", help="structural checks only (V1-V5)")
    parser.add_argument("--tests", type=Path, help="tests directory to run against the artifact (V13)")
    parser.add_argument("--no-tests", action="store_true", help="do not run V13")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--keep", action="store_true", help="keep the extraction workspace")
    parser.add_argument("--python", default=sys.executable)
    args = parser.parse_args(argv)
    if bool(args.archive) == bool(args.installed):
        print(json.dumps(PackagingError("INVALID_ARGUMENT", "give exactly one of <archive> or --installed").to_dict()))
        return 1
    tests: object = None if args.no_tests else (args.tests if args.tests else AUTO)
    report = verify(args.archive, args.installed, args.require_release, tests, args.python, args.keep, args.quick, args.report)
    print(json.dumps({k: report[k] for k in ("status", "failed", "not_run", "name", "version", "build_mode", "commit")}
                     | {"report": report.get("report_path"),
                        "checks": {c["id"]: c["status"] for c in report["checks"]}}, indent=2))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
