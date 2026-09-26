# Generic adapter

A working, host-agnostic reference adapter. Any agent or tool that can run a command and read JSON can use it; platform adapters should follow the same shape.

```bash
python plugins/ui-engineering/adapters/generic/adapter.py describe                       # name, version, capabilities, tools
python plugins/ui-engineering/adapters/generic/adapter.py instructions                   # where the skill starts, how to load knowledge
python plugins/ui-engineering/adapters/generic/adapter.py self-test                      # manifest/core/error/capability health report
python plugins/ui-engineering/adapters/generic/adapter.py call retrieve_knowledge --params '{"collection": "styles", "text": "calm"}'
python plugins/ui-engineering/adapters/generic/adapter.py call resolve_capabilities --params @profile-request.json
```

`profile-request.json` holds `{"profile": {...}}` (see `phase-2/capability-resolver/resolver.md#profile`).

- Works from any working directory; the package root is resolved from this file's location (or `UIUX_ROOT`).
- Uses only `uiux.api`; verifies the manifest version equals the core version and exposes error/capability/self-test contracts without importing internal modules.
- Exit codes: 0 result returned (inspect `status` inside), 3 invalid call.
- Status: **skeleton**. It is functional and tested, but it does not register itself with any host, which is the job of platform adapters.
