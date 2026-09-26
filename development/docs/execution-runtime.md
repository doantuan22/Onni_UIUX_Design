# Playwright runtime execution

The optional runtime runner invokes read-only detection before using project-local Playwright. It validates a JSON request, resolves semantic viewport IDs from `execution/viewports.json`, uses a temporary Node helper inside a session directory for local module resolution, and never installs browsers/packages or edits project configuration.

It reuses a responding server; an explicit argv start command needs `--allow-start`, is marked owned, checked by HTTP polling, and terminated only if owned. Each route/viewport gets an isolated headless context, basic body/root render check, optional expected selector/text check, screenshot capture, and compact console-error evidence. It writes atomic session manifest/report JSON and preserves partial evidence.

Use `--dry-run` to validate input, capability and evidence paths without launch. Use [validate_runtime_evidence.py](../../plugins/ui-engineering/scripts/validate_runtime_evidence.py) to check storage integrity. Runtime evals E29–E36 are fixture-ready but must report `SKIP_RUNTIME`/blocked honestly when this environment lacks runnable project Playwright.
