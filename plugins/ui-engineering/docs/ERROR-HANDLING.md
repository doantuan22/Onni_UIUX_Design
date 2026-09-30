# Error Handling

The public error source is `uiux.api.error_contract()` and `uiux/core/errors` (contract version 1). Public tool boundaries return an error envelope with status, error, error code, category, remediation, and optional details; unexpected internal exceptions do not expose tracebacks by default.

| Category | Typical condition | Caller action |
|---|---|---|
| validation | Malformed tool id, required argument, type, or enum | Correct the request using `list_tools` schema |
| configuration | Invalid or unsupported plugin configuration | Correct or remove the unsupported setting |
| unsupported | Valid operation unavailable in this package/adapter | Select a supported operation from the capability map |
| package / registry | Manifest, version, registry, or knowledge index is inconsistent | Repair/reinstall or rebuild the local index as remediation states |
| runtime / dependency | Optional Node/browser/runtime capability unavailable | Preserve the BLOCKED result; do not report successful execution |
| internal | Unexpected package failure | Use the sanitized remediation; enable `UIUX_DEBUG=1` only for local diagnosis |

Not every unavailable capability is an exception. Browser evidence requirements are represented as blocked critic issues. In the real smoke traces, all four fixtures returned `BLOCKED_BROWSER_RUNTIME` because Playwright was `NOT_DECLARED`; the task was not authorized to proceed. The paired benchmark emits `BLOCKED_*` and `NOT_SCORED` for absent fixtures or arms.

Never convert missing evidence, unknown targets, an empty plan, timeout, or tool error into a pass. Keep raw stdout/stderr only in local benchmark run artifacts and do not copy secrets into public reports.
