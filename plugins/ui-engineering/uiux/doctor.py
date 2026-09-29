"""User-facing, read-only capability diagnosis built on existing health probes."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any


def diagnose(project: str = ".") -> dict[str, Any]:
    from uiux import __version__
    from uiux.core import resources
    from uiux.api import capability_map, self_test
    from uiux.runtime.capabilities import command_version, detect
    from uiux.engine.verification.strategy import detect_verification_capabilities

    root = Path(project).expanduser().resolve()
    runtime = detect(str(root))
    verification_caps = detect_verification_capabilities(root, runtime_detection=runtime)
    health = self_test()
    capabilities: dict[str, dict[str, Any]] = {}

    def add(name: str, state: str, detail: str, impact: str | None = None) -> None:
        row = {"status": state, "detail": detail}
        if impact:
            row["impact"] = impact
        capabilities[name] = row

    py_ok = sys.version_info >= (3, 9)
    add("python", "AVAILABLE" if py_ok else "MISSING", f"Python {sys.version.split()[0]}; plugin requires 3.9+",
        None if py_ok else "The plugin cannot run until Python 3.9 or newer is available.")
    node = command_version("node")
    add("node", "AVAILABLE" if node.get("status") == "AVAILABLE" else "MISSING",
        node.get("version") or "Node.js was not found on PATH.",
        None if node.get("status") == "AVAILABLE" else "Browser capture and axe scans requiring Node cannot run.")

    manager_files = {"npm": "package-lock.json", "pnpm": "pnpm-lock.yaml", "yarn": "yarn.lock", "bun": "bun.lockb"}
    managers = [name for name, marker in manager_files.items() if (root / marker).exists()]
    add("package_manager", "AVAILABLE" if managers else "UNKNOWN",
        ", ".join(managers) if managers else "No recognized package-manager lockfile found.")

    package_health = health.get("status") == "PASS"
    add("plugin_core", "AVAILABLE" if package_health else "BLOCKED",
        f"UI/UX plugin {__version__}; self_test={health.get('status')}.",
        None if package_health else "One or more plugin registries, manifests, or public API checks failed.")
    package_root = resources.get_package_root()
    phase_files = {
        "P0_SEE": ["uiux/engine/repo_intelligence/__init__.py", "uiux/engine/existing_ui/__init__.py"],
        "P1_KNOW": ["uiux/engine/knowledge_router/__init__.py", "knowledge/domains/registry.json"],
        "P2_THINK": ["uiux/engine/modification_planner/planner.py"],
        "P3_DO": ["uiux/engine/executor/executor.py"],
        "P4_CHECK": ["uiux/engine/verification/engine.py", "uiux/engine/runtime_critic/critic.py"],
    }
    for name, paths in phase_files.items():
        available = all((package_root / p).is_file() for p in paths)
        add(name, "AVAILABLE" if available else "BLOCKED", "Required phase modules are present." if available else "Required phase module is missing.",
            None if available else f"The {name} phase cannot run until the package is repaired.")

    playwright_state = runtime["playwright"]["runtime_state"]["state"]
    pw = playwright_state == "READY"
    add("playwright_package", "AVAILABLE" if runtime["playwright"].get("package_present", {}).get("status") == "AVAILABLE" else "MISSING",
        f"Runtime state: {playwright_state}.", None if pw else "Rendered browser verification is unavailable until Playwright is installed in the target project.")
    browser = runtime["playwright"].get("browser_ready", {})
    browser_ok = browser.get("status") == "AVAILABLE"
    add("playwright_browser", "AVAILABLE" if browser_ok else "MISSING", f"{playwright_state}; browser readiness: {browser.get('status', 'UNKNOWN')}.",
        None if browser_ok else "Browser-based responsive, interaction and screenshot verification cannot run.")
    app = runtime.get("project", {})
    app_command = app.get("dev_command") or app.get("build_command") or app.get("test_command")
    add("runtime_command", "AVAILABLE" if app_command else "UNKNOWN",
        f"Detected project command: {app_command}." if app_command else "No runtime start command was detected; doctor does not start applications.")
    add("browser_runtime", "AVAILABLE" if pw else "BLOCKED", f"Playwright state is {playwright_state}.",
        None if pw else "P4 browser verification is blocked; install/configure the target runtime yourself, then rerun doctor.")

    try:
        caps = capability_map(str(root))
        registry_state = "AVAILABLE" if caps.get("tools") else "BLOCKED"
    except Exception as exc:  # doctor reports; it does not raise
        caps = {}
        registry_state = "BLOCKED"
        registry_detail = str(exc)
    else:
        registry_detail = f"{len(caps.get('tools', {}))} tools discovered from the registry."
    add("mcp_tool_registry", registry_state, registry_detail,
        None if registry_state == "AVAILABLE" else "MCP tool discovery and calls may be unavailable.")
    add("schema_registry", registry_state, "Tool input schemas passed registry checks." if registry_state == "AVAILABLE" else registry_detail,
        None if registry_state == "AVAILABLE" else "Tool calls may fail schema validation or dispatch checks.")

    evidence_root = root / ".evidence"
    storage_parent = evidence_root if evidence_root.exists() else root
    storage_ok = storage_parent.is_dir() and os.access(storage_parent, os.W_OK)
    add("artifact_evidence_storage", "AVAILABLE" if storage_ok else "BLOCKED",
        str(evidence_root), None if storage_ok else "Task state and runtime evidence cannot be persisted for this project.")

    limitations = [{"capability": key, "impact": item["impact"]} for key, item in capabilities.items() if item.get("impact")]
    core_blockers = ["plugin_core", "P0_SEE", "P1_KNOW", "P2_THINK", "P3_DO", "P4_CHECK", "mcp_tool_registry", "schema_registry", "artifact_evidence_storage"]
    blocked = [key for key in core_blockers if capabilities[key]["status"] in {"BLOCKED", "MISSING"}]
    overall = "BLOCKED" if blocked else "PARTIAL" if limitations else "READY"
    next_actions = []
    for item in limitations:
        next_actions.append({"capability": item["capability"], "action": item["impact"], "automatic_install": False})
    summary = "UI task workflow is ready with the detected project capabilities." if not limitations else \
        f"Core UI workflow is available; {len(limitations)} capability limitation(s) affect optional runtime or storage checks."
    verification_capabilities = {name.upper(): dict(value) for name, value in verification_caps.items() if isinstance(value, dict)}
    maximum_trust_level = verification_caps["maximum_trust_level"]
    verification_limitations = [lim for value in verification_capabilities.values() for lim in value.get("limitations", [])]
    if verification_limitations:
        summary += " Verification ceiling: " + maximum_trust_level + "."
    static_summary = "Current environment can verify source structure"
    if verification_caps["build_validation"]["status"] == "AVAILABLE":
        static_summary += " and detected build validity"
    else:
        static_summary += "; no supported build command was detected"
    verification_summary = (static_summary + ", but cannot verify rendered responsive behavior, visual intent, or browser interactions."
        if verification_caps["runtime_dom"]["status"] != "AVAILABLE" else
        "Current environment has browser runtime capability; task-specific evidence and contract determine the trust actually achieved.")
    return {"overall_status": overall, "summary": summary, "capabilities": capabilities,
            "verification_capabilities": verification_capabilities,
            "maximum_trust_level": maximum_trust_level, "trust_ceiling": maximum_trust_level,
            "verification_summary": verification_summary,
            "verification_limitations": list(dict.fromkeys(verification_limitations)),
            "limitations": limitations, "next_actions": next_actions, "self_test": health,
            "project": str(root)}
