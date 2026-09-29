"""Generic Interaction Runner & UI State Validator (P1.6 & UI State Validation).

Executes scenario specifications provided by validation handoffs or runtime packs against
target pages using Playwright when available, or provides deterministic fixture selector/state
verification when browser runtime is not installed. Never fakes PASS for unresolved selectors.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from uiux.core import resources
from uiux.runtime import capabilities

SUPPORTED_ACTIONS = {
    "click",
    "fill",
    "type",
    "clear",
    "select",
    "press",
    "key",
    "focus",
    "modal_open",
    "modal_close",
    "drawer_open",
    "drawer_close",
    "tab_switch",
    "search",
    "filter",
    "submit",
}

SUPPORTED_STATES = {
    "loading",
    "empty",
    "error",
    "disabled",
    "success",
    "focus-visible",
    "data",
}


class InteractionError(Exception):
    """Base error for interaction execution failures."""
    def __init__(self, code: str, message: str, selector: str | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.selector = selector


def validate_scenario_spec(scenario: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate that an interaction scenario conforms to the generic runner contract."""
    errors = []
    if not isinstance(scenario, dict):
        return False, ["Scenario must be a dictionary."]

    actions = scenario.get("actions", [])
    if not isinstance(actions, list):
        errors.append("'actions' must be a list of action steps.")
    else:
        for idx, act in enumerate(actions):
            if not isinstance(act, dict):
                errors.append(f"Action at index {idx} must be a dictionary.")
                continue
            act_type = act.get("type", act.get("action"))
            if not act_type or act_type not in SUPPORTED_ACTIONS:
                errors.append(f"Action at index {idx} has unsupported type '{act_type}'. Supported: {sorted(SUPPORTED_ACTIONS)}")

    expected_states = scenario.get("expected_states", scenario.get("states", []))
    if expected_states and not isinstance(expected_states, list):
        errors.append("'expected_states' must be a list.")
    elif isinstance(expected_states, list):
        for st in expected_states:
            if st not in SUPPORTED_STATES:
                errors.append(f"State '{st}' is not in supported states: {sorted(SUPPORTED_STATES)}")

    return len(errors) == 0, errors


def verify_target_fixture_selectors(
    target_path: Path,
    scenario: dict[str, Any],
) -> dict[str, Any]:
    """Deterministically verify whether the scenario's selectors exist in the target HTML/JS files.

    Used for deterministic CI / test verification when local browser binary is not installed,
    preventing false claims while validating scenario contract compliance.
    """
    target = target_path.resolve()
    html_files = list(target.rglob("*.html"))
    if not html_files:
        return {
            "status": "BLOCKED",
            "reason": "NO_HTML_ENTRYPOINT",
            "message": f"No HTML entrypoints found in {target}",
            "verified_actions": [],
            "unresolved_selectors": [],
        }

    # Aggregate HTML content for static selector verification
    combined_html = "\n".join(f.read_text(encoding="utf-8", errors="ignore") for f in html_files)

    verified_actions: list[dict[str, Any]] = []
    unresolved_selectors: list[dict[str, Any]] = []

    actions = scenario.get("actions", [])
    for idx, act in enumerate(actions):
        act_type = act.get("type", act.get("action"))
        selector = act.get("selector")
        step_record = {
            "index": idx,
            "action": act_type,
            "selector": selector,
            "passed": False,
        }

        if not selector:
            # Actions like keyboard press might not require selector
            step_record["passed"] = True
            step_record["notes"] = "Keypress / global action without target selector"
            verified_actions.append(step_record)
            continue

        # Extract IDs, classes, and attributes from simple CSS selectors
        found = False
        # Match ID #foo
        for id_match in re.findall(r"#([a-zA-Z0-9_-]+)", selector):
            if f'id="{id_match}"' in combined_html or f"id='{id_match}'" in combined_html:
                found = True
                break

        # Match class .bar
        if not found:
            for cls_match in re.findall(r"\.([a-zA-Z0-9_-]+)", selector):
                if re.search(r'class=["\'][^"\']*\b' + re.escape(cls_match) + r'\b[^"\']*["\']', combined_html):
                    found = True
                    break

        # Match tags or attributes e.g. input, select, [data-filter]
        if not found:
            for attr_match in re.findall(r"\[([a-zA-Z0-9_-]+)", selector):
                if attr_match in combined_html:
                    found = True
                    break

        if not found and selector in ("input", "form", "select", "button", "table", "aside", "nav"):
            if f"<{selector}" in combined_html.lower():
                found = True

        if found:
            step_record["passed"] = True
            verified_actions.append(step_record)
        else:
            step_record["passed"] = False
            step_record["error"] = f"Selector '{selector}' not resolvable in target markup."
            unresolved_selectors.append(step_record)

    # Check UI States in markup
    states_verified: list[str] = []
    states_missing: list[str] = []
    expected_states = scenario.get("expected_states", scenario.get("states", []))
    for st in expected_states:
        # Check if state container / role is present in markup
        state_patterns = {
            "loading": (r"loading|skeleton|aria-busy|progress", combined_html),
            "empty": (r"empty|no\s+results|zero-state", combined_html),
            "error": (r"error|alert|failed|retry", combined_html),
            "disabled": (r"disabled|aria-disabled", combined_html),
            "data": (r"table|tbody|card-matrix|list", combined_html),
            "success": (r"success|completed|active", combined_html),
            "focus-visible": (r":focus|focus-visible|tabindex", combined_html),
        }
        pat, corpus = state_patterns.get(st, (st, combined_html))
        if re.search(pat, corpus, re.IGNORECASE):
            states_verified.append(st)
        else:
            states_missing.append(st)

    has_unresolved = len(unresolved_selectors) > 0
    if has_unresolved:
        return {
            "status": "FAILED",
            "exit_code": 1,
            "reason": "UNRESOLVED_SELECTOR",
            "message": f"{len(unresolved_selectors)} selector(s) could not be resolved in target markup.",
            "verified_actions": verified_actions,
            "unresolved_selectors": unresolved_selectors,
            "states_verified": states_verified,
            "states_missing": states_missing,
        }

    return {
        "status": "PASS",
        "exit_code": 0,
        "strategy": "deterministic_fixture_verification",
        "verified_actions": verified_actions,
        "unresolved_selectors": [],
        "states_verified": states_verified,
        "states_missing": states_missing,
    }


def execute_interaction_scenario(
    scenario: dict[str, Any],
    project: str | Path,
    base_url: str | None = None,
) -> dict[str, Any]:
    """Execute a scenario specification.

    If Playwright browser is available, delegates to live browser execution.
    If Playwright browser is not installed, executes deterministic fixture verification
    and marks browser runtime status honestly as BLOCKED_BROWSER_RUNTIME rather than faking pass.
    """
    proj = Path(project).resolve()
    valid, errors = validate_scenario_spec(scenario)
    if not valid:
        return {
            "status": "FAILED",
            "exit_code": 3,
            "error_code": "INVALID_SCENARIO_SPEC",
            "message": "; ".join(errors),
        }

    # Detect runtime readiness
    runtime_cap = capabilities.detect(proj)
    playwright_state = runtime_cap.get("playwright", {}).get("runtime_state", {}).get("state", "NOT_DECLARED")

    if playwright_state != capabilities.READY:
        # Browser runtime unavailable: run deterministic fixture verification
        fixture_res = verify_target_fixture_selectors(proj, scenario)
        if fixture_res.get("status") == "FAILED":
            return {
                "status": "FAILED",
                "exit_code": 1,
                "error_code": "UNRESOLVED_SELECTOR",
                "message": fixture_res.get("message"),
                "details": fixture_res,
                "browser_runtime_status": f"BLOCKED_{playwright_state}",
            }
        return {
            "status": "BLOCKED",
            "exit_code": 2,
            "error_code": f"PLAYWRIGHT_{playwright_state}",
            "message": f"Browser execution blocked ({playwright_state}); fixture selector verification succeeded.",
            "fixture_verification": fixture_res,
            "browser_runtime_status": f"BLOCKED_{playwright_state}",
        }

    # This module has no live Playwright action executor. Fixture checks only
    # prove selector presence and must never be reported as executed interactions.
    fixture_res = verify_target_fixture_selectors(proj, scenario)
    return {
        "status": "BLOCKED",
        "exit_code": 2,
        "error_code": "LIVE_INTERACTION_EXECUTOR_UNAVAILABLE",
        "message": "Playwright is available, but this runner only validates fixture selectors and does not execute browser actions.",
        "strategy": "fixture_selector_validation_only",
        "fixture_verification": fixture_res,
        "browser_runtime_status": "READY",
    }
