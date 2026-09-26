"""Generic, host-agnostic adapter: JSON in, JSON out, over the public Core API only.

    python plugins/ui-engineering/adapters/generic/adapter.py describe
    python plugins/ui-engineering/adapters/generic/adapter.py instructions
    python plugins/ui-engineering/adapters/generic/adapter.py self-test
    python plugins/ui-engineering/adapters/generic/adapter.py call <tool-id> [--params '<json>' | --params @file.json]
    python plugins/ui-engineering/adapters/generic/adapter.py --config host-config.json call ...   # configure(overrides)

Importable as a module too: ``GenericAdapter().call("retrieve_knowledge", {"collection": "styles"})``.
Integration only: no design, knowledge, eval or runtime logic lives here (see ../CONTRACT.md). Declarative metadata
is in adapter.json (schema plugins/ui-engineering/schemas/adapter.schema.json). Errors are the core's error envelope; exit codes:
0 success, 1 self-test FAIL or internal error, 3 invalid call or incompatible package.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

_ADAPTER_DIR = Path(__file__).resolve().parent
_PLUGIN_ROOT = _ADAPTER_DIR.parents[1]
PACKAGE_ROOT = Path(os.environ.get("UIUX_ROOT", _PLUGIN_ROOT)).resolve()
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from uiux import api  # noqa: E402  (public Core API only)

METADATA = json.loads((_ADAPTER_DIR / "adapter.json").read_text(encoding="utf-8"))


def _version_tuple(text: str) -> tuple[int, ...]:
    return tuple(int(part) for part in text.split("."))


def version_satisfies(found: str, requirement: str) -> bool:
    """``found`` satisfies a comma-separated range such as ``>=0.1.0,<1.0.0``."""
    compare = {">=": lambda a, b: a >= b, ">": lambda a, b: a > b, "<=": lambda a, b: a <= b,
               "<": lambda a, b: a < b, "==": lambda a, b: a == b}
    for clause in requirement.split(","):
        operator, bound = re.match(r"^(>=|>|<=|<|==)(.+)$", clause.strip()).groups()
        if not compare[operator](_version_tuple(found), _version_tuple(bound)):
            return False
    return True


class GenericAdapter:
    def __init__(self) -> None:
        self.metadata = METADATA
        try:
            manifest_path = _PLUGIN_ROOT / "plugin.json" if (_PLUGIN_ROOT / "plugin.json").is_file() else _PLUGIN_ROOT / "manifest" / "plugin.json"
            self.manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise api.UiuxError(f"plugin manifest unreadable: {exc}", "MANIFEST_INVALID") from exc
        if self.manifest.get("manifest_version") not in self.metadata["manifest_version"]:
            raise api.UiuxError(f"unsupported manifest_version {self.manifest.get('manifest_version')}", "MANIFEST_INVALID")
        core = self.metadata["core_api"]
        if self.manifest.get("version") != api.version():
            raise api.UiuxError(f"manifest version {self.manifest.get('version')} does not match core {api.version()}",
                                "VERSION_MISMATCH", manifest=self.manifest.get("version"), core=api.version())
        if not version_satisfies(api.version(), core["core_version"]) or core["plugin_api_version"] != api.API_VERSION:
            raise api.UiuxError(f"adapter requires core {core['core_version']} (API {core['plugin_api_version']}); found "
                                f"{api.version()} (API {api.API_VERSION})", "VERSION_MISMATCH",
                                required=core["core_version"], found=api.version())

    def describe(self) -> dict:
        return {"name": self.manifest["name"], "version": api.version(), "description": self.manifest["description"],
                "adapter": {"id": self.metadata["id"], "status": self.metadata["status"],
                            "transports": self.metadata["transports"]},
                "capabilities": self.manifest["capabilities"], "entrypoints": self.manifest["entrypoints"],
                "tools": [{"id": t["id"], "description": t["description"], "input": t["input"],
                           "annotations": t["annotations"]} for t in api.list_tools() if t["visibility"] == "public"]}

    def instructions(self) -> dict:
        entry = self.manifest["entrypoints"]
        return {"start": entry["skill"]["path"], "knowledge": entry["knowledge"]["path"],
                "knowledge_registry": entry["knowledge"]["registry"], "note": self.metadata["knowledge"]["rule"]}

    @staticmethod
    def configure(config_file: str | Path) -> dict:
        """Apply host configuration through the core's config layer (UIUX_CONFIG); returns the effective config."""
        os.environ["UIUX_CONFIG"] = str(Path(config_file).resolve())
        return api.reload_config()

    def call(self, tool_id: str, params: dict | None = None) -> dict:
        if any(t["id"] == tool_id and t["visibility"] != "public" for t in api.list_tools()):
            raise api.UiuxError(f"{tool_id} is not exposed by the {self.metadata['id']} adapter", "UNSUPPORTED_OPERATION")
        return api.call_tool(tool_id, params or {})

    def self_test(self) -> dict:
        """Core self-test plus the adapter's own checks: manifest and capability agreement, error contract version,
        a knowledge call and an unknown-tool call (spec section 7.3). Never installs, downloads or writes."""
        core = api.self_test()
        checks = list(core["checks"])

        def add(check_id: str, ok: bool, message: str, code: str) -> None:
            checks.append({"id": check_id, "status": "PASS" if ok else "FAIL", "message": message,
                           **({} if ok else {"error_code": code})})

        declared = sorted(self.manifest["capabilities"])
        mapped = sorted(api.capability_map()["capabilities"])
        add("adapter.manifest", declared == mapped,
            f"manifest {self.manifest['name']} {self.manifest['version']}; capabilities match the capability map"
            if declared == mapped else f"manifest capabilities {declared} != capability map {mapped}", "MANIFEST_INVALID")
        contract = api.error_contract()["error_contract_version"]
        add("adapter.error_contract", contract == self.metadata["errors"]["error_contract_version"],
            f"error_contract_version {contract}", "VERSION_MISMATCH")
        try:
            found = self.call("retrieve_knowledge", {"ids": ["style.swiss"]})["count"] == 1
            add("adapter.call", found, "retrieve_knowledge(ids=[style.swiss]) returned one entry", "INTERNAL_ERROR")
        except api.UiuxError as exc:
            add("adapter.call", False, exc.message, exc.code)
        try:
            self.call("nope")
            add("adapter.unknown_tool", False, "unknown tool was not rejected", "INTERNAL_ERROR")
        except api.UiuxError as exc:
            add("adapter.unknown_tool", exc.code == "UNKNOWN_TOOL", f"unknown tool -> {exc.code}", "INTERNAL_ERROR")
        return {"status": "FAIL" if any(c["status"] == "FAIL" for c in checks) else "PASS", "version": api.version(),
                "adapter": self.metadata["id"], "checks": checks}


def _params(raw: str | None) -> dict:
    raw = raw or "{}"
    try:
        text = Path(raw[1:]).read_text(encoding="utf-8") if raw.startswith("@") else raw
    except OSError as exc:
        raise api.ToolError(str(exc), "FILESYSTEM_ERROR") from exc
    try:
        return json.loads(text)
    except ValueError as exc:
        raise api.ToolError(f"--params is not valid JSON: {exc}", "INVALID_ARGUMENT") from exc


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Generic UI/UX design skill adapter")
    parser.add_argument("--config", help="host configuration JSON (merged over core defaults; relative paths only)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("describe")
    sub.add_parser("instructions")
    sub.add_parser("self-test")
    call = sub.add_parser("call")
    call.add_argument("tool")
    call.add_argument("--params")
    args = parser.parse_args(argv)
    try:
        if args.config:
            GenericAdapter.configure(args.config)
        adapter = GenericAdapter()
        if args.command == "describe":
            result = adapter.describe()
        elif args.command == "instructions":
            result = adapter.instructions()
        elif args.command == "self-test":
            result = adapter.self_test()
        else:
            result = adapter.call(args.tool, _params(args.params))
    except Exception as exc:  # noqa: BLE001 - every failure leaves as a JSON error envelope, never a traceback
        envelope = api.error_envelope(exc, f"adapter.{args.command}")
        print(json.dumps(envelope, ensure_ascii=False, default=str))
        return 3 if envelope["status"] == "INVALID_CALL" else 1
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return 1 if args.command == "self-test" and result["status"] == "FAIL" else 0


if __name__ == "__main__":
    raise SystemExit(main())
