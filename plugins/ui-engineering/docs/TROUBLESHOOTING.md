# Troubleshooting Guide

This document lists common issues and resolution procedures when installing, executing, or configuring the **UI Engineering Plugin**.

---

## 1. Plugin Not Discovered

- **Symptom**: The host AI environment does not list the plugin's capabilities or fails to load `plugin.json`.
- **Cause**: The host environment was pointed to the repository root instead of the canonical plugin directory, or manifest files are missing.
- **Resolution**:
  - Ensure the target path points to `plugins/ui-engineering/` (the canonical plugin root).
  - Verify `plugin.json` and `SKILL.md` exist directly in that folder.
  - Test resolution with `python scripts/uiux_cli.py call self_test`.

---

## 2. Windows CLI Shell Quoting Errors

- **Symptom**: `JSONDecodeError` or unexpected character error when passing inline JSON strings to `--params` on PowerShell or CMD.
- **Cause**: Windows shells alter or strip quotes within JSON strings.
- **Resolution**:
  - Save the parameter payload to a JSON file (e.g. `scratch/params.json`).
  - Pass the file reference with the `@` prefix:
    ```powershell
    python scripts/uiux_cli.py call plan_modification --params "@scratch/params.json"
    ```

---

## 3. Runtime Verification Status: `BLOCKED_BROWSER_RUNTIME`

- **Symptom**: Calling `run_runtime_validation` or running benchmark harnesses reports `BLOCKED_BROWSER_RUNTIME` and `authorized_to_proceed: false`.
- **Cause**: The current machine environment does not have Playwright or its headless browser binaries installed.
- **Resolution**:
  - The plugin operates under a strict **No-Auto-Install** policy: it will never download binaries silently in the background.
  - For static code reviews, code analysis, and design planning, browser execution is optional.
  - If E2E browser evidence is required, install Playwright in your environment:
    ```bash
    pip install playwright
    playwright install chromium
    ```

---

## 4. `INVALID_ARGUMENT` Error from Runtime Critic

- **Symptom**: `run_runtime_validation` or `recapture_evidence` returns an error object with `code: "INVALID_ARGUMENT"`.
- **Cause**: The input payload does not match the public schema (`schemas/evidence.schema.json` or `schemas/repair-result.schema.json`). For instance, `actions_executed` was passed as a list of strings instead of a list of objects.
- **Resolution**:
  - Review the schema definition in `schemas/evidence.schema.json` and `schemas/repair-result.schema.json`.
  - Format `actions_executed` as an array of objects:
    ```json
    {
      "actions_executed": [
        {"action_id": "act_1", "description": "Adjusted flex alignment", "files": ["styles.css"]}
      ]
    }
    ```

---

## 5. Version Mismatch Failure During Verification

- **Symptom**: `packaging/verify.py` reports a mismatch between `VERSION`, `plugin.json`, and manifest files.
- **Cause**: Manual edits to version strings without updating canonical version sources.
- **Resolution**:
  - `VERSION` in `plugins/ui-engineering/VERSION` is the single source of truth.
  - Update `plugin.json` and adapter manifests to match `VERSION`.

## MCP server `ui-ux-design-mcp` fails to connect (red status)

`claude mcp list` shows `Failed to connect — ENOENT: Executable not found`: Claude Code could not start the
Python interpreter. The server is launched with `${UIUX_PYTHON:-python3}`.

1. Check `python3 --version` (and `python --version`). Python 3.9+ is required.
2. If `python3` is missing — typical on Windows with the python.org installer — point `UIUX_PYTHON` at a
   working interpreter: `setx UIUX_PYTHON python` (Windows) or `export UIUX_PYTHON=/path/to/python3`.
3. Open a new terminal, restart Claude Code, and re-check with `claude mcp list` or `/mcp`.
