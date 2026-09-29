"""Capability mapping and deterministic verification strategy selection."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from uiux.engine.verification.trust import (
    VerificationCapabilities, VerificationCapability, VerificationStrategy,
)


def _cap(status: str, reason: str, requirements: list[str], evidence: list[str], limitations: list[str]) -> VerificationCapability:
    return {"status": status, "reason": reason, "requirements": requirements,
            "evidence_types": evidence, "limitations": limitations}


def detect_verification_capabilities(project: str | Path | None, implementation_report: dict[str, Any] | None = None,
                                     runtime_detection: dict[str, Any] | None = None) -> VerificationCapabilities:
    """Reuse the existing runtime detector and project scripts; do not install or launch anything."""
    root = Path(project or ".").expanduser().resolve()
    report = implementation_report or {}
    detected = runtime_detection or {}
    runtime_state = detected.get("playwright", {}).get("runtime_state", {}).get("state", "NOT_DECLARED")
    browser_available = project is not None and runtime_state == "READY"
    browser_reason = f"Existing runtime detector reports Playwright state {runtime_state}."
    package_path = root / "package.json"
    build_commands = detected.get("project", {}).get("validation_commands", []) if project is not None else []
    if not isinstance(build_commands, list):
        build_commands = []
    # Capability means the static diff checker exists in this environment; P3 output is
    # a per-task requirement, not an environment capability.
    source_ok = Path(__file__).is_file()
    root_ok = project is not None and root.is_dir()
    framework = detected.get("project", {}).get("framework", {}).get("value")
    maximum = "UNVERIFIED" if not source_ok or not root_ok else "MULTIMODAL_VERIFIED" if browser_available else "STATICALLY_VERIFIED"
    return {
        "source_diff": _cap("AVAILABLE" if source_ok else "UNAVAILABLE",
            "Source/diff verifier is installed; this task still requires a P3 report." if source_ok else "Source/diff verifier is missing.",
            ["P3 ImplementationReport and ChangeLedger"], ["SOURCE_DIFF"], [] if source_ok else ["Source change claims cannot be checked without P3 output."]),
        "static_structure": _cap("AVAILABLE" if root_ok else "UNAVAILABLE",
            "Target project is readable." if root_ok else "Target project directory is unavailable.",
            ["Readable target project"], ["STATIC_STRUCTURE", "FRAMEWORK_VALIDATION", "TOKEN_COMPARISON", "RESPONSIVE_SOURCE_SIGNAL"],
            [] if framework else ["Framework could not be detected; generic source checks only."]),
        "build_validation": _cap("AVAILABLE" if build_commands else "UNAVAILABLE",
            f"Detected configured commands: {', '.join(build_commands)}." if build_commands else "No supported build/typecheck/lint/test script and package manager were detected.",
            ["Recognized package manager", "Existing project script"], ["BUILD_OUTPUT"],
            [] if build_commands else ["Build validation was not run because no configured command was detected."]),
        "runtime_dom": _cap("AVAILABLE" if browser_available else "BLOCKED", browser_reason,
            ["Project Playwright package and browser"], ["RUNTIME_DOM", "RUNTIME_EVIDENCE"],
            [] if browser_available else ["Rendered DOM and runtime behavior cannot be verified."]),
        "visual_render": _cap("AVAILABLE" if browser_available else "BLOCKED", browser_reason,
            ["Runtime browser and screenshot capture"], ["SCREENSHOT", "VISUAL_CRITIC"],
            [] if browser_available else ["Rendered visual appearance cannot be verified."]),
        "interaction_a11y": _cap("AVAILABLE" if browser_available else "BLOCKED", browser_reason,
            ["Runtime browser; task-relevant interaction and accessibility tools"], ["INTERACTION", "ACCESSIBILITY"],
            [] if browser_available else ["Browser interactions and browser-backed accessibility cannot be verified."]),
        "maximum_trust_level": maximum,
    }


def resolve_verification_strategy(verification_contract: dict[str, Any], implementation_report: dict[str, Any],
                                  verification_capabilities: VerificationCapabilities,
                                  ui_context: dict[str, Any] | None = None,
                                  existing_baseline: dict[str, Any] | None = None,
                                  affected_surfaces: dict[str, Any] | None = None) -> VerificationStrategy:
    """Select all useful available checks without weakening or rewriting P2's contract."""
    del implementation_report, ui_context, existing_baseline, affected_surfaces
    required = ["SOURCE_DIFF", "STATIC_STRUCTURE"]
    # Build/typecheck/lint/test is required only when a recognized, configured project command exists.
    if verification_capabilities["build_validation"]["status"] == "AVAILABLE":
        required.append("BUILD_VALIDATION")
    contract_text = " ".join(str(v) for v in verification_contract.values()).lower()
    needs_runtime = bool(verification_contract.get("viewports") or verification_contract.get("pages") or
                         verification_contract.get("required_viewports") or verification_contract.get("required_routes") or
                         verification_contract.get("scenarios") or verification_contract.get("interactions") or
                         verification_contract.get("accessibility_checks") or any(k in contract_text for k in ("runtime", "visual", "screenshot", "responsive", "interaction", "accessibility", "axe", "render", "console", "browser", "dom")))
    if needs_runtime:
        required.append("RUNTIME_DOM")
        if (verification_contract.get("viewports") or verification_contract.get("required_viewports") or
                any(k in contract_text for k in ("visual", "screenshot", "visual_intent"))):
            required.append("VISUAL_RENDER")
        scenarios = " ".join(str(v) for v in verification_contract.get("scenarios", []))
        if verification_contract.get("interactions") or verification_contract.get("accessibility_checks") or any(k in (contract_text + " " + scenarios) for k in ("interaction", "keyboard", "form", "modal", "navigation", "accessibility", "axe")):
            required.append("INTERACTION_A11Y")
    names = {"SOURCE_DIFF": "source_diff", "STATIC_STRUCTURE": "static_structure", "BUILD_VALIDATION": "build_validation",
             "RUNTIME_DOM": "runtime_dom", "VISUAL_RENDER": "visual_render", "INTERACTION_A11Y": "interaction_a11y"}
    available = [level for level, field in names.items() if verification_capabilities[field]["status"] == "AVAILABLE"]
    selected = [level for level in available if level in required]
    unavailable = [{"check": level, "reason": verification_capabilities[names[level]]["reason"]}
                   for level in required if level not in available]
    return {"required_levels": required, "available_levels": available, "selected_checks": selected,
            "unavailable_checks": unavailable, "degraded_mode": any(level in {"RUNTIME_DOM", "VISUAL_RENDER", "INTERACTION_A11Y"} for level in required if level not in available),
            "expected_trust_ceiling": verification_capabilities["maximum_trust_level"]}
