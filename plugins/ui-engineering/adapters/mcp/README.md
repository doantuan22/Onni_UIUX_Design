# Shared MCP stdio transport

This is the experimental, host-neutral MCP transport for the UI/UX Skill. It is a stdlib-only JSON-RPC 2.0 server pinned to MCP protocol revision `2025-06-18`; it exposes tools only and calls no internal UI/UX modules.

Run it from any working directory:

```bash
python -m adapters.mcp.server  # from plugins/ui-engineering
# or
python plugins/ui-engineering/adapters/mcp/server.py
```

The transport uses newline-delimited JSON on standard input/output. Standard output is protocol data only. Diagnostics and `--debug` tracebacks go to standard error. EOF cleanly stops the process; there is no network listener, daemon, dependency installation, browser download, resource API, prompt API, sampling API, or host-specific configuration.

## Lifecycle and methods

1. Send `initialize` with a `protocolVersion` string. The server negotiates its pinned revision, reports the public `uiux.api.version()` and declares only `tools` capability.
2. Send the `notifications/initialized` notification.
3. Call `ping`, `tools/list`, or `tools/call`.
4. Close stdin to stop the server.

`tools/list` is derived on every request from `uiux.api.list_tools()`: the name, description and input schema are unchanged. Standard MCP hints are derived from tool annotations; all UI/UX annotations are retained under `_meta["uiux.dev/annotations"]` (filesystem read/write, browser/Node need, network access, process start, determinism and long-running status).

`tools/call` accepts `{name, arguments}` and invokes only `uiux.api.call_tool(name, arguments)`. Registry-schema validation remains in the public API. Successful results, including runtime `BLOCKED`, return MCP `content` plus `structuredContent` with `isError: false`. Public invalid-call errors return `isError: true` with the complete UI/UX error envelope. Malformed JSON-RPC, invalid request shapes and unknown methods are JSON-RPC errors; unexpected server failures are `-32603` without a traceback.

Capability discovery is exposed through the registered `capability_map` tool. It retains static versus runtime-dependent capability states and does not make tools disappear when a particular project runtime is blocked. Health is exposed through the registered `self_test` tool.

Raw smoke example (one object per line):

```json
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"raw-test","version":"1"}}}
{"jsonrpc":"2.0","method":"notifications/initialized"}
{"jsonrpc":"2.0","id":2,"method":"tools/list"}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"retrieve_knowledge","arguments":{"ids":["style.swiss"]}}}
```

The transport is packaged in every artifact and tested from an extracted artifact. It is not a Claude Code, Codex, Cline, OpenCode or Copilot adapter; those remain separate future work.
