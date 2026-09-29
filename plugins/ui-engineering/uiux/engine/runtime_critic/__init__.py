"""Runtime Critic Engine – Phase 7.

Stays the runtime evidence critic and repair loop. ``uiux.engine.verification`` (``verify_implementation``) sits in front of
it: it gates on the P3 report and the plan's evidence contract, reuses this package's session model, and routes repairs.

Core concept:
  Modification Plan  →  Controlled Editing  →  Change Manifest
       ↓
  Runtime Execution  →  Before / After Evidence
       ↓
  Critic   (visual_regression | preservation | responsive | interaction |
             accessibility | runtime_error | plan_drift | missing_required_state)
       ↓
  Critic Report  →  Repair Decision  →  Targeted Repair  →  Targeted Recapture
       ↓
  Re-critique  →  Final Validation

Principles:
  OBSERVE → COMPARE → CRITIQUE → REPAIR ONLY VERIFIED FAILURES
  → RECAPTURE ONLY AFFECTED EVIDENCE → STOP WHEN PASS OR BUDGET EXHAUSTED

This package is the public entry for Phase 7. All external callers
use only the functions exposed here.
"""
from __future__ import annotations

from uiux.engine.runtime_critic.session import RuntimeValidationSession
from uiux.engine.runtime_critic.critic import CriticEngine
from uiux.engine.runtime_critic.repair import RepairEngine
from uiux.engine.runtime_critic.loop import CriticRepairLoop

__all__ = [
    "RuntimeValidationSession",
    "CriticEngine",
    "RepairEngine",
    "CriticRepairLoop",
    "run_runtime_validation",
    "build_critic_report",
    "evaluate_runtime_result",
    "build_repair_plan",
    "run_targeted_repair",
    "recapture_evidence",
]


def run_runtime_validation(
    modification_plan: dict,
    change_manifest: dict | None = None,
    before_evidence: dict | None = None,
    after_evidence: dict | None = None,
    workflow: str = "existing-ui",
    validate_only: bool = False,
    max_repair_iterations: int = 3,
) -> dict:
    """Top-level entry: run validation session and return a full critic report.

    Args:
        modification_plan: Phase 6 ModificationPlan.
        change_manifest: Phase 6 ChangeManifest (actual changes).
        before_evidence: Runtime evidence captured before editing.
        after_evidence: Runtime evidence captured after editing.
        workflow: "greenfield" or "existing-ui".
        validate_only: If True, no repairs are attempted.
        max_repair_iterations: Maximum repair loop iterations.

    Returns:
        critic_report dict.
    """
    from uiux.engine.runtime_critic.validation import (
        validate_evidence,
        make_invalid_argument_error,
    )

    if modification_plan is not None and not isinstance(modification_plan, dict):
        return make_invalid_argument_error(
            f"Invalid modification_plan: expected dictionary or null, got {type(modification_plan).__name__}",
            {"field": "modification_plan", "expected": "object", "actual": type(modification_plan).__name__},
        )

    if change_manifest is not None and not isinstance(change_manifest, dict):
        return make_invalid_argument_error(
            f"Invalid change_manifest: expected dictionary or null, got {type(change_manifest).__name__}",
            {"field": "change_manifest", "expected": "object", "actual": type(change_manifest).__name__},
        )

    # Validate before_evidence defensively
    is_valid, err_msg, details = validate_evidence(before_evidence, "before_evidence")
    if not is_valid:
        return make_invalid_argument_error(err_msg, details)

    # Validate after_evidence defensively
    is_valid, err_msg, details = validate_evidence(after_evidence, "after_evidence")
    if not is_valid:
        return make_invalid_argument_error(err_msg, details)

    session = RuntimeValidationSession(
        modification_plan=modification_plan,
        change_manifest=change_manifest,
        before_evidence=before_evidence,
        after_evidence=after_evidence,
        workflow=workflow,
    )
    engine = CriticEngine()
    report = engine.critique(session)

    if validate_only:
        report["validate_only"] = True
        return report

    loop = CriticRepairLoop(
        critic_engine=engine,
        repair_engine=RepairEngine(),
        max_iterations=max_repair_iterations,
    )
    return loop.run(session, report)


def build_critic_report(session_data: dict) -> dict:
    """Build a critic report from a pre-assembled session data dict."""
    from uiux.engine.runtime_critic.session import RuntimeValidationSession
    from uiux.engine.runtime_critic.critic import CriticEngine
    from uiux.engine.runtime_critic.validation import (
        validate_evidence,
        make_invalid_argument_error,
    )

    if not isinstance(session_data, dict):
        return make_invalid_argument_error(
            f"Invalid session_data: expected dictionary, got {type(session_data).__name__}",
            {"field": "session_data", "expected": "object", "actual": type(session_data).__name__},
        )

    for field in ("before_evidence", "after_evidence"):
        if field in session_data:
            is_valid, err_msg, details = validate_evidence(session_data.get(field), field)
            if not is_valid:
                return make_invalid_argument_error(err_msg, details)

    session = RuntimeValidationSession.from_dict(session_data)
    return CriticEngine().critique(session)


def evaluate_runtime_result(critic_report: dict) -> dict:
    """Evaluate an already-built critic report for overall pass/fail/blocked status."""
    if not isinstance(critic_report, dict):
        return {
            "authorized_to_proceed": False,
            "overall_status": "fail",
            "critical_issue_count": 0,
            "repair_required": False,
            "blocked": True,
        }

    overall = critic_report.get("overall_status", "fail")
    issues = critic_report.get("issues", [])
    if not isinstance(issues, list):
        issues = []
    critical_issues = [i for i in issues if isinstance(i, dict) and i.get("severity") in ("HIGH", "CRITICAL") and i.get("status") != "pre_existing"]
    has_insufficient = any(isinstance(i, dict) and i.get("category") == "insufficient_evidence" for i in issues)
    is_blocked = overall in ("blocked", "needs_runtime", "insufficient_evidence") or critic_report.get("blocked", False) or has_insufficient
    authorized = (overall in ("pass", "warn")) and not is_blocked
    return {
        "authorized_to_proceed": authorized,
        "overall_status": overall,
        "critical_issue_count": len(critical_issues),
        "repair_required": overall in ("warn", "fail") and any(isinstance(i, dict) and i.get("repairable") for i in issues),
        "blocked": is_blocked,
    }


def build_repair_plan(critic_report: dict, modification_plan: dict) -> dict:
    """Build a targeted repair plan from a critic report and the original modification plan."""
    from uiux.engine.runtime_critic.validation import make_invalid_argument_error

    if not isinstance(critic_report, dict):
        return make_invalid_argument_error(
            f"Invalid critic_report: expected dictionary, got {type(critic_report).__name__}",
            {"field": "critic_report", "expected": "object", "actual": type(critic_report).__name__},
        )
    if not isinstance(modification_plan, dict):
        return make_invalid_argument_error(
            f"Invalid modification_plan: expected dictionary, got {type(modification_plan).__name__}",
            {"field": "modification_plan", "expected": "object", "actual": type(modification_plan).__name__},
        )
    return RepairEngine().build_repair_plan(critic_report, modification_plan)


def run_targeted_repair(
    repair_plan: dict,
    modification_plan: dict,
) -> dict:
    """Execute a targeted repair plan through Phase 6 Controlled Editing gate."""
    from uiux.engine.runtime_critic.validation import make_invalid_argument_error

    if not isinstance(repair_plan, dict):
        return make_invalid_argument_error(
            f"Invalid repair_plan: expected dictionary, got {type(repair_plan).__name__}",
            {"field": "repair_plan", "expected": "object", "actual": type(repair_plan).__name__},
        )
    if not isinstance(modification_plan, dict):
        return make_invalid_argument_error(
            f"Invalid modification_plan: expected dictionary, got {type(modification_plan).__name__}",
            {"field": "modification_plan", "expected": "object", "actual": type(modification_plan).__name__},
        )
    return RepairEngine().execute_repair(repair_plan, modification_plan)


def recapture_evidence(
    repair_result: dict,
    modification_plan: dict,
    before_evidence: dict | None = None,
) -> dict:
    """Determine the minimal recapture surface after a repair and return a recapture plan."""
    from uiux.engine.runtime_critic.recapture import build_recapture_plan
    from uiux.engine.runtime_critic.validation import (
        validate_repair_result,
        validate_evidence,
        make_invalid_argument_error,
    )

    is_valid, err_msg, details = validate_repair_result(repair_result)
    if not is_valid:
        res = make_invalid_argument_error(err_msg, details)
        res["recapture_plan"] = {
            "status": "blocked",
            "recapture_pages": [],
            "recapture_viewports": [],
            "recapture_scenarios": [],
            "rationale": f"Blocked: {err_msg}",
            "is_full_site": False,
        }
        return res

    if not isinstance(modification_plan, dict):
        res = make_invalid_argument_error(
            f"Invalid modification_plan: expected dictionary, got {type(modification_plan).__name__}",
            {"field": "modification_plan", "expected": "object", "actual": type(modification_plan).__name__},
        )
        res["recapture_plan"] = {
            "status": "blocked",
            "recapture_pages": [],
            "recapture_viewports": [],
            "recapture_scenarios": [],
            "rationale": "Blocked due to invalid modification_plan payload.",
            "is_full_site": False,
        }
        return res

    if before_evidence is not None:
        is_valid, err_msg, details = validate_evidence(before_evidence, "before_evidence")
        if not is_valid:
            res = make_invalid_argument_error(err_msg, details)
            res["recapture_plan"] = {
                "status": "blocked",
                "recapture_pages": [],
                "recapture_viewports": [],
                "recapture_scenarios": [],
                "rationale": f"Blocked: {err_msg}",
                "is_full_site": False,
            }
            return res

    return build_recapture_plan(repair_result, modification_plan, before_evidence)
