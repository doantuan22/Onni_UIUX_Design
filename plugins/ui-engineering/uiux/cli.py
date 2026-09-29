"""Unified command line for the Core API (platform-neutral; used by the generic adapter).

    python scripts/uiux_cli.py version
    python scripts/uiux_cli.py tools
    python scripts/uiux_cli.py architecture
    python scripts/uiux_cli.py call <tool-id> [--params '<json>' | --params @file.json]

Output is always JSON on stdout. Exit codes: 0 success, 1 the tool reported FAIL/BLOCKED, 3 invalid call
(``status: INVALID_CALL``), 1 internal error (``status: ERROR``, ``error_code: INTERNAL_ERROR``). Errors carry
``error_code``, ``category`` and ``remediation`` (uiux/core/errors.json); no traceback unless ``UIUX_DEBUG=1``.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from uiux import api
from uiux.core.errors import internal


def _params(value: str | None) -> dict:
    if not value:
        return {}
    text = Path(value[1:]).read_text(encoding="utf-8") if value.startswith("@") else value
    data = json.loads(text)
    if not isinstance(data, dict):
        raise api.ToolError("--params must be a JSON object", "INVALID_ARGUMENT_TYPE")
    return data


def _fail(exc: api.UiuxError) -> int:
    """Error envelope (0.x fields status/error plus error_code, category, remediation[, details]) and its exit code."""
    print(json.dumps(exc.envelope(), ensure_ascii=False, default=str))
    return exc.exit_code


def _exit_code(result: object) -> int:
    if isinstance(result, dict):
        if "exit_code" in result and isinstance(result["exit_code"], int):
            return 0 if result["exit_code"] == 0 else 1
        if result.get("status") in {"FAIL", "BLOCKED", "FAILED"}:
            return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="uiux", description="UI/UX design skill Core API")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("version")
    sub.add_parser("tools")
    sub.add_parser("architecture")
    doctor = sub.add_parser("doctor", help="Read-only capability report for a target project")
    doctor.add_argument("--project", default=".", help="Target project directory (default: current directory)")
    call = sub.add_parser(
        "call",
        help="Invoke a tool by ID",
        description=(
            "Invoke a registered tool by ID with parameters. Parameters can be provided "
            "as an inline JSON object or read from a JSON file using '@path/to/file.json' "
            "(recommended on Windows PowerShell / cmd to avoid shell quoting issues)."
        ),
    )
    call.add_argument("tool", help="ID of the tool to invoke (e.g. plan_modification, build_knowledge_plan)")
    call.add_argument(
        "--params",
        help=(
            "JSON parameter string or '@path/to/file.json' to load arguments from a file. "
            "Example Windows-safe usage: --params \"@scratch/plan-input.json\""
        ),
    )
    args = parser.parse_args(argv)
    try:
        if args.command == "version":
            result: object = {"version": api.version()}
        elif args.command == "tools":
            result = {"tools": api.list_tools()}
        elif args.command == "architecture":
            result = api.describe_architecture()
        elif args.command == "doctor":
            result = api.doctor(args.project)
        else:
            result = api.call_tool(args.tool, _params(args.params))
    except api.UiuxError as exc:
        return _fail(exc)
    except json.JSONDecodeError as exc:
        return _fail(api.ToolError(str(exc), "INVALID_ARGUMENT"))
    except OSError as exc:
        return _fail(api.ToolError(str(exc), "FILESYSTEM_ERROR"))
    except Exception as exc:  # noqa: BLE001 - JSON envelope instead of a traceback (UIUX_DEBUG=1 prints it to stderr)
        return _fail(internal(exc, f"cli.{args.command}"))
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
    return _exit_code(result)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
