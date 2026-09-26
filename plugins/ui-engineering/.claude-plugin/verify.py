"""Claude Code plugin bundle verification (checks C1-C16).

    python plugins/ui-engineering/.claude-plugin/verify.py <extracted-bundle-root>
    python plugins/ui-engineering/.claude-plugin/verify.py --bundle <bundle.zip>

Checks are structural and subprocess-based.  A live Claude Code session is NOT required.
Exit codes: 0 all PASS, 2 at least one FAIL, 1 unusable input.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import tempfile
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_COMMON = _HERE.parent / "adapters" / "common"
if str(_COMMON.parent) not in sys.path:
    sys.path.insert(0, str(_COMMON.parent))

from common import bundle, verify, mcp_smoke


# Ensure packaging is importable for artifact.safe_extract
_PACKAGING = _HERE.parent / "packaging"
if not _PACKAGING.is_dir():
    _PACKAGING = _HERE.parents[1] / "packaging"
if str(_PACKAGING) not in sys.path:
    sys.path.insert(0, str(_PACKAGING))
import artifact  # noqa: E402
from artifact import PackagingError  # noqa: E402


CHECKS = {
    "C1": ".claude-plugin/plugin.json exists",
    "C2": "Claude manifest JSON-parseable with required fields",
    "C3": "version matches VERSION",
    "C4": ".mcp.json exists and valid JSON",
    "C5": "MCP config references shared MCP server only",
    "C6": "no absolute developer paths",
    "C7": "${CLAUDE_PLUGIN_ROOT} used correctly in MCP config",
    "C14": "read-only extracted plugin",
    "C15": "no forbidden development files",
    "C16": "generic package contract preserved",
}


def verify_bundle(root: Path, python: str = sys.executable) -> dict:
    """Run C1-C16 on an extracted Claude Code plugin bundle."""
    checks: list[dict] = []

    def record(cid: str, status: str, detail: str = "") -> None:
        name = CHECKS.get(cid, cid)
        checks.append({"id": cid, "name": name, "status": status, "detail": detail})

    def ok(cid: str, problems: list[str]) -> None:
        record(cid, "FAIL" if problems else "PASS", "; ".join(problems) if problems else "")

    # C1: .claude-plugin/plugin.json exists
    claude_manifest_path = root / ".claude-plugin" / "plugin.json"
    ok("C1", [] if claude_manifest_path.is_file() else [f"{claude_manifest_path} not found"])

    # C2: Claude manifest parseable with required fields
    claude_manifest = {}
    c2_problems: list[str] = []
    if claude_manifest_path.is_file():
        try:
            claude_manifest = json.loads(claude_manifest_path.read_text(encoding="utf-8"))
            required = {"name", "version"}
            missing = sorted(required - set(claude_manifest))
            if missing:
                c2_problems.append(f"missing fields: {', '.join(missing)}")
        except (json.JSONDecodeError, OSError) as exc:
            c2_problems.append(f"cannot parse: {exc}")
    else:
        c2_problems.append("file does not exist")
    ok("C2", c2_problems)

    # C3: version matches VERSION (delegate to common)
    manifest_version = claude_manifest.get("version", "")
    ok("C3", verify.check_version_match(root, manifest_version) if manifest_version else ["cannot check version against missing manifest version"])

    # C4: .mcp.json exists and valid JSON
    mcp_path = root / ".mcp.json"
    mcp_config: dict = {}
    c4_problems: list[str] = []
    if mcp_path.is_file():
        try:
            mcp_config = json.loads(mcp_path.read_text(encoding="utf-8"))
            if not isinstance(mcp_config, dict):
                c4_problems.append(".mcp.json is not a JSON object")
        except (json.JSONDecodeError, OSError) as exc:
            c4_problems.append(f"cannot parse .mcp.json: {exc}")
    else:
        c4_problems.append(".mcp.json not found")
    ok("C4", c4_problems)
    # Claude Code's documented form wraps servers in "mcpServers"; the legacy flat map is still accepted.
    servers = mcp_config.get("mcpServers", mcp_config) if isinstance(mcp_config, dict) else {}
    if not isinstance(servers, dict):
        servers = {}

    # C5: MCP config references shared MCP server only
    c5_problems: list[str] = []
    for server_name, config in servers.items():
        args = config.get("args", [])
        for arg in args:
            if isinstance(arg, str) and "server.py" in arg:
                if "adapters/mcp/server.py" not in arg:
                    c5_problems.append(f"server '{server_name}' does not use the shared MCP transport: {arg}")
    ok("C5", c5_problems)

    # C6: no absolute developer paths in overlay files (delegate to common)
    ok("C6", verify.check_absolute_paths([claude_manifest_path, mcp_path]))

    # C7: ${CLAUDE_PLUGIN_ROOT} used correctly
    c7_problems: list[str] = []
    if mcp_path.is_file():
        for server_name, config in servers.items():
            args = config.get("args", [])
            for arg in args:
                if isinstance(arg, str) and "server.py" in arg:
                    if "${CLAUDE_PLUGIN_ROOT}" not in arg and not arg.startswith("."):
                        c7_problems.append(f"server '{server_name}' arg does not use ${{CLAUDE_PLUGIN_ROOT}}: {arg}")
    ok("C7", c7_problems)

    # C15: no forbidden development files (delegate to common)
    ok("C15", verify.check_forbidden_files(root))

    # C8-C13: MCP subprocess tests (delegate to common)
    server = root / "adapters" / "mcp" / "server.py"
    mcp_report = mcp_smoke.run_mcp_smoke_test(python, server, root)
    checks.extend(mcp_report["checks"])

    # C14: read-only extracted plugin
    record("C14", "NOT_RUN", "read-only enforcement is covered by generic verification V11; "
           "Claude-specific read-only test deferred to CI with full OS coverage")

    # C16: generic package contract preserved (delegate to common)
    ok("C16", verify.check_generic_contract(root))

    failed = [c["id"] for c in checks if c["status"] == "FAIL"]
    return {
        "status": "FAIL" if failed else "PASS",
        "failed": failed,
        "not_run": [c["id"] for c in checks if c["status"] == "NOT_RUN"],
        "checks": checks,
    }


def verify_marketplace(root: Path, python: str = sys.executable) -> dict:
    """Run M1-M16 on an extracted Claude Code marketplace bundle."""
    checks: list[dict] = []

    def record(cid: str, status: str, detail: str = "") -> None:
        checks.append({"id": cid, "name": cid, "status": status, "detail": detail})

    def ok(cid: str, problems: list[str]) -> None:
        record(cid, "FAIL" if problems else "PASS", "; ".join(problems) if problems else "")

    expected_marketplace = "uiux-local"
    expected_plugin = "ui-ux-design"
    ok("M1", [] if root.is_dir() else [f"{root} not found"])
    mp_json_path = root / ".claude-plugin" / "marketplace.json"
    ok("M2", [] if mp_json_path.is_file() else [f"{mp_json_path} not found"])

    mp_json: dict = {}
    m3_problems: list[str] = []
    if mp_json_path.is_file():
        try:
            mp_json = json.loads(mp_json_path.read_text(encoding="utf-8"))
            if not isinstance(mp_json, dict):
                m3_problems.append("marketplace manifest must be a JSON object")
        except (json.JSONDecodeError, OSError) as exc:
            m3_problems.append(f"cannot parse: {exc}")
    ok("M3", m3_problems)

    marketplace_name = mp_json.get("name") if isinstance(mp_json, dict) else None
    ok("M4", [] if marketplace_name == expected_marketplace else [
        f"marketplace name must be '{expected_marketplace}', got {marketplace_name!r}"
    ])
    owner = mp_json.get("owner") if isinstance(mp_json, dict) else None
    owner_problems: list[str] = []
    if not isinstance(owner, dict):
        owner_problems.append("owner must be an object")
    elif not isinstance(owner.get("name"), str) or not owner["name"].strip():
        owner_problems.append("owner.name must be a non-empty string")
    ok("M5", owner_problems)

    plugins = mp_json.get("plugins") if isinstance(mp_json, dict) else None
    ok("M6", [] if isinstance(plugins, list) and len(plugins) == 1 and isinstance(plugins[0], dict)
       else ["plugins must contain exactly one plugin object"])
    plugin = plugins[0] if isinstance(plugins, list) and len(plugins) == 1 and isinstance(plugins[0], dict) else {}
    plugin_name = plugin.get("name")
    ok("M7", [] if plugin_name == expected_plugin else [
        f"plugin name must be '{expected_plugin}', got {plugin_name!r}"
    ])
    install_id = f"{plugin_name}@{marketplace_name}" if isinstance(plugin_name, str) and isinstance(marketplace_name, str) else ""
    ok("M8", [] if install_id == f"{expected_plugin}@{expected_marketplace}" else [
        f"install identifier mismatch: {install_id or '<unavailable>'}"
    ])

    source = plugin.get("source")
    plugin_root, source_problems = bundle.validate_marketplace_source_path(source, root)
    ok("M9", source_problems)
    ok("M10", [] if plugin_root and plugin_root.is_dir() else [
        f"referenced plugin not found at {source!r}"
    ])
    # validate_marketplace_source_path resolves symlinks before checking containment.
    ok("M11", [] if not any("escapes marketplace root" in problem for problem in source_problems)
       else source_problems)

    # The embedded plugin is validated by the normal C1-C16 verifier.
    if plugin_root and plugin_root.is_dir():
        plugin_report = verify_bundle(plugin_root, python)
        by_id = {check["id"]: check for check in plugin_report["checks"]}
        for marketplace_id, source_ids in {
            "M12": ("C1", "C2"), "M13": ("C3",), "M14": ("C4", "C5", "C6", "C7"),
            "M15": ("C8", "C9", "C10", "C11"), "M16": ("C15", "C16"),
        }.items():
            selected = [by_id[cid] for cid in source_ids if cid in by_id]
            problems = [f"{item['id']}: {item['detail']}" for item in selected if item["status"] == "FAIL"]
            not_run = [item["id"] for item in selected if item["status"] == "NOT_RUN"]
            record(marketplace_id, "FAIL" if problems else ("NOT_RUN" if not_run else "PASS"), "; ".join(problems or not_run))
    else:
        for cid in ("M12", "M13", "M14", "M15", "M16"):
            record(cid, "FAIL", "embedded plugin is unavailable")

    failed = [c["id"] for c in checks if c["status"] == "FAIL"]
    return {
        "status": "FAIL" if failed else "PASS",
        "failed": failed,
        "not_run": [c["id"] for c in checks if c["status"] == "NOT_RUN"],
        "checks": checks,
    }


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Verify a Claude Code plugin bundle (C1-C16) or marketplace (M1-M16)")
    parser.add_argument("root", nargs="?", type=Path, help="extracted bundle root")
    parser.add_argument("--bundle", type=Path, help="bundle ZIP to extract and verify")
    parser.add_argument("--marketplace", action="store_true", help="verify a marketplace bundle instead of a plugin bundle")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--keep", action="store_true")
    args = parser.parse_args(argv)

    workspace = None
    try:
        if args.bundle:
            workspace = Path(tempfile.mkdtemp(prefix="claude-verify-"))
            root = artifact.safe_extract(args.bundle, workspace / "extract")
        elif args.root:
            root = args.root.resolve()
        else:
            print(json.dumps({"status": "ERROR", "error": "give a bundle root or --bundle <zip>"}))
            return 1

        if args.marketplace:
            report = verify_marketplace(root, args.python)
        else:
            report = verify_bundle(root, args.python)
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "PASS" else 2
    except PackagingError as exc:
        print(json.dumps(exc.to_dict(), indent=2))
        return 1
    finally:
        if workspace and not args.keep:
            shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
