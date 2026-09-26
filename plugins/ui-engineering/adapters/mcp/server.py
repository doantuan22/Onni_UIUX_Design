"""Shared MCP server over stdio, backed exclusively by ``uiux.api``.

Run from any directory with either::

    python -m adapters.mcp.server  # from plugins/ui-engineering
    python plugins/ui-engineering/adapters/mcp/server.py

Messages are newline-delimited JSON-RPC 2.0. Stdout is protocol-only; diagnostics, including debug tracebacks, use
stderr. The server has no network listener and never installs dependencies or invokes arbitrary code.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from pathlib import Path
from typing import TextIO

if __package__ in (None, ""):  # Direct-script mode: make the package root importable without depending on cwd.
    _ROOT = Path(__file__).resolve().parents[2]
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
    import protocol
else:
    from . import protocol

from uiux import api

SERVER_NAME = "ui-ux-design-mcp"
SERVER_TITLE = "UI/UX Design Skill"


def _mcp_annotations(notes: dict) -> dict[str, object]:
    """Map stable UI/UX annotations to standard MCP hints and retain all richer facts in namespaced metadata."""
    return {
        "annotations": {
            "readOnlyHint": notes["read_only"],
            "destructiveHint": False,
            "idempotentHint": notes["deterministic"],
            "openWorldHint": notes["network_access"],
        },
        "_meta": {"uiux.dev/annotations": {
            "read_only": notes["read_only"],
            "filesystem_read": notes["filesystem_read"],
            "filesystem_write": notes["writes_to"],
            "network_access": notes["network_access"],
            "requires_browser": notes["requires_browser"],
            "requires_node": notes["requires_node"],
            "long_running": notes["long_running"],
            "may_start_process": notes["may_start_process"],
            "deterministic": notes["deterministic"],
        }},
    }


def list_tools() -> dict[str, object]:
    """Derive MCP tool definitions directly from the public registry view; no hand-maintained tool list exists here."""
    tools = []
    for item in api.list_tools():
        if item["visibility"] != "public":
            continue
        tools.append({"name": item["id"], "title": item["id"].replace("_", " ").title(),
                      "description": item["description"], "inputSchema": item["input"]}
                     | _mcp_annotations(item["annotations"]))
    return {"tools": tools}


def _tool_result(value: dict, is_error: bool = False) -> dict[str, object]:
    """MCP structured result plus compatibility text. BLOCKED is a successful tool result, never a transport error."""
    return {"content": [protocol.text_content(value)], "structuredContent": value, "isError": is_error}


class McpServer:
    """Stateless request mapper apart from the MCP initialization lifecycle flags."""

    def __init__(self) -> None:
        self.initialize_seen = False
        self.initialized = False

    def handle(self, message: object) -> dict[str, object] | None:
        identifier, problem = protocol.request_problem(message)
        if problem:
            return protocol.error(identifier, protocol.INVALID_REQUEST, "Invalid Request", {"reason": problem})
        assert isinstance(message, dict)  # narrowed by request_problem
        method = message["method"]
        params = message.get("params", {})
        notification = "id" not in message
        try:
            if method == "initialize":
                response = self._initialize(identifier, params)
            elif method == "notifications/initialized":
                self.initialized = self.initialize_seen
                response = None
            elif method == "ping":
                response = protocol.result(identifier, {}) if not notification else None
            elif method == "tools/list":
                response = self._tools_list(identifier, params)
            elif method == "tools/call":
                response = self._tools_call(identifier, params)
            elif method.startswith("notifications/"):
                response = None
            else:
                response = protocol.error(identifier, protocol.METHOD_NOT_FOUND, "Method not found",
                                          {"method": method})
        except Exception as exc:  # noqa: BLE001 - protocol boundary must not leak or terminate on an unexpected error
            response = protocol.error(identifier, protocol.INTERNAL_ERROR, "Internal server error",
                                      {"error_code": "INTERNAL_ERROR"})
            if os.environ.get("UIUX_DEBUG") == "1":
                traceback.print_exception(type(exc), exc, exc.__traceback__, file=sys.stderr)
        return None if notification else response

    def _initialize(self, identifier: str | int | None, params: dict) -> dict[str, object]:
        if identifier is None:
            return protocol.error(None, protocol.INVALID_REQUEST, "initialize must be a request")
        requested = params.get("protocolVersion")
        if not isinstance(requested, str):
            return protocol.error(identifier, protocol.INVALID_PARAMS, "Invalid initialize parameters",
                                  {"reason": "protocolVersion must be a string"})
        self.initialize_seen = True
        return protocol.result(identifier, {
            "protocolVersion": protocol.MCP_PROTOCOL_VERSION,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": SERVER_NAME, "title": SERVER_TITLE, "version": api.version()},
            "instructions": "Use tools/list for UI/UX Skill tools. Use capability_map for static and runtime capability discovery.",
        })

    def _ready(self, identifier: str | int | None) -> dict[str, object] | None:
        if not self.initialized:
            return protocol.error(identifier, protocol.NOT_INITIALIZED, "Server not initialized",
                                  {"reason": "send initialize, receive its result, then send notifications/initialized"})
        return None

    def _tools_list(self, identifier: str | int | None, params: dict) -> dict[str, object]:
        if identifier is None:
            return protocol.error(None, protocol.INVALID_REQUEST, "tools/list must be a request")
        not_ready = self._ready(identifier)
        if not_ready:
            return not_ready
        if params.get("cursor") not in (None, ""):
            return protocol.error(identifier, protocol.INVALID_PARAMS, "Pagination is not supported")
        return protocol.result(identifier, list_tools())

    def _tools_call(self, identifier: str | int | None, params: dict) -> dict[str, object]:
        if identifier is None:
            return protocol.error(None, protocol.INVALID_REQUEST, "tools/call must be a request")
        not_ready = self._ready(identifier)
        if not_ready:
            return not_ready
        name, arguments = params.get("name"), params.get("arguments", {})
        if not isinstance(name, str) or not name:
            return protocol.error(identifier, protocol.INVALID_PARAMS, "Invalid tools/call parameters",
                                  {"reason": "name must be a non-empty string"})
        if not isinstance(arguments, dict):
            return protocol.error(identifier, protocol.INVALID_PARAMS, "Invalid tools/call parameters",
                                  {"reason": "arguments must be an object"})
        try:
            value = api.call_tool(name, arguments)
        except api.UiuxError as exc:
            envelope = api.error_envelope(exc, "mcp.tools/call")
            if envelope["error_code"] == "INTERNAL_ERROR":
                return protocol.error(identifier, protocol.INTERNAL_ERROR, "Internal server error", envelope)
            return protocol.result(identifier, _tool_result(envelope, is_error=True))
        return protocol.result(identifier, _tool_result(value))


def serve(reader: TextIO = sys.stdin, writer: TextIO = sys.stdout) -> int:
    """Serve newline-delimited requests until EOF. A malformed line gets one error response and the process continues."""
    server = McpServer()
    for line in reader:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError as exc:
            response = protocol.error(None, protocol.PARSE_ERROR, "Parse error", {"reason": exc.msg})
        else:
            response = server.handle(message)
        if response is not None:
            writer.write(json.dumps(response, ensure_ascii=False, separators=(",", ":"), default=str) + "\n")
            writer.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="UI/UX Skill MCP stdio server")
    parser.add_argument("--debug", action="store_true", help="print unexpected server tracebacks to stderr only")
    args = parser.parse_args(argv)
    if args.debug:
        os.environ["UIUX_DEBUG"] = "1"
    return serve()


if __name__ == "__main__":
    raise SystemExit(main())
