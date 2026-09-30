"""Reference E2E benchmark harness for UI Engineering Plugin.

Runs the complete UI pipeline on reference target projects (Target A Static, Target B React/Dashboard,
or Existing UI fixtures) to verify capability integration and E2E readiness without false claims.

Execution classification:
- BROWSER_E2E_VERIFIED: Real browser runtime executed, evidence captured and critic evaluated.
- INTEGRATION_VERIFIED: Static and pipeline tools executed through handoff without runtime requirement.
- BLOCKED_BROWSER_RUNTIME: Runtime was required but local Playwright/browser binary was unavailable.
- FAILED: A pipeline stage failed with an error or contract violation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure plugin package is in sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
_PLUGIN_DIR = _REPO_ROOT / "plugins" / "ui-engineering"
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

import uiux.api as api


def run_target_benchmark(
    target_path: str | Path,
    task: str,
    workflow: str | None = None,
    mock_browser_evidence: dict | None = None,
    mock_before_evidence: dict | None = None,
) -> dict[str, Any]:
    """Execute the full UI engineering pipeline on a reference target project.

    Args:
        target_path: Path to target project directory.
        task: User task instruction prompt.
        workflow: Optional explicit workflow override ('greenfield', 'existing-ui', etc.).
        mock_browser_evidence: Optional simulated evidence dict for testing critic gating.

    Returns:
        Structured benchmark report dict with stage results and final status.
    """
    target = Path(target_path).resolve()
    if not target.is_dir():
        return {
            "status": "FAILED",
            "error": f"Target directory not found: {target}",
            "stages": {},
        }

    report: dict[str, Any] = {
        "target": str(target),
        "task": task,
        "stages": {},
        "status": "INITIALIZED",
        "authorized_to_proceed": False,
        "runtime_classification": None,
    }

    try:
        # Stage 1: Analyze Repository
        repo_profile = api.analyze_repository(project=str(target))
        report["stages"]["analyze_repository"] = {
            "status": "PASS",
            "framework": repo_profile.get("framework"),
            "styling": repo_profile.get("styling"),
            "component_count": len(repo_profile.get("components", [])),
        }

        # Stage 2: Orchestrate UI
        orch_req = {"user_request": task, "repo_context": {"workspace_root": str(target), "files": repo_profile.get("files", [])}}
        if workflow:
            orch_req["workflow"] = workflow
        orch_res = api.orchestrate_ui(request=orch_req)
        resolved_workflow = orch_res.get("workflow", workflow or "existing-ui")
        report["stages"]["orchestrate_ui"] = {
            "status": "PASS",
            "workflow": resolved_workflow,
            "intent": orch_res.get("intent"),
            "ui_state": orch_res.get("ui_state"),
        }

        # Stage 3: Build Knowledge Plan
        know_plan = api.build_knowledge_plan(
            repo_profile=repo_profile,
            user_request=task,
            workflow=resolved_workflow,
            task_intent=orch_res.get("intent"),
        )
        report["stages"]["build_knowledge_plan"] = {
            "status": "PASS",
            "framework_pack": know_plan.get("framework_pack", {}).get("framework"),
            "selected_knowledge_count": len(know_plan.get("selected_knowledge", [])),
        }

        # Stage 4: Plan Modification
        plan_res = api.plan_modification(
            user_request=task,
            workflow=resolved_workflow,
            repo_profile=repo_profile,
            knowledge_plan=know_plan,
            task_intent=orch_res.get("intent"),
        )
        report["stages"]["plan_modification"] = {
            "status": "PASS" if plan_res.get("steps") or plan_res.get("execution_chunks") else "INCOMPLETE",
            "step_count": len(plan_res.get("steps", [])),
            "execution_chunk_count": len(plan_res.get("execution_chunks", [])),
            "affected_files": plan_res.get("affected_files", []),
        }

        # Stage 5: Build Validation Handoff
        handoff = api.build_validation_handoff(plan=plan_res)
        requires_runtime = handoff.get("requires_runtime", True)
        report["stages"]["build_validation_handoff"] = {
            "status": "PASS",
            "requires_runtime": requires_runtime,
            "viewports": handoff.get("viewports", []),
        }

        # Stage 6: Detect Runtime Capability
        runtime_detection = api.detect_runtime(project=str(target))
        playwright_state = runtime_detection.get("playwright", {}).get("runtime_state", {}).get("state", "NOT_DECLARED")
        browser_ready = (playwright_state == "READY")
        report["stages"]["detect_runtime"] = {
            "status": "PASS",
            "playwright_state": playwright_state,
            "browser_ready": browser_ready,
        }

        # Stage 7: Runtime Critic Gate Evaluation
        before_ev = mock_before_evidence if mock_before_evidence is not None else mock_browser_evidence
        critic_rep = api.run_runtime_validation(
            modification_plan=plan_res,
            change_manifest={"files_modified": plan_res.get("affected_files", [])},
            before_evidence=before_ev,
            after_evidence=mock_browser_evidence,
            workflow=resolved_workflow,
            validate_only=True,
        )
        eval_res = api.evaluate_runtime_result(critic_report=critic_rep)

        report["stages"]["runtime_critic"] = {
            "status": eval_res.get("overall_status"),
            "authorized_to_proceed": eval_res.get("authorized_to_proceed", False),
            "issues": critic_rep.get("issues", []),
        }
        report["authorized_to_proceed"] = eval_res.get("authorized_to_proceed", False)

        # Final Classification
        plan_complete = report["stages"]["plan_modification"]["status"] == "PASS"
        if mock_browser_evidence is not None:
            report["status"] = "SIMULATED_EVIDENCE_TEST_ONLY"
            report["runtime_classification"] = "SIMULATED_EVIDENCE_ONLY"
        elif not plan_complete:
            report["status"] = "BLOCKED_INSUFFICIENT_PLAN"
            report["runtime_classification"] = "BLOCKED_EMPTY_MODIFICATION_PLAN"
        elif not requires_runtime:
            report["status"] = "INTEGRATION_VERIFIED"
            report["runtime_classification"] = "RUNTIME_NOT_REQUIRED"
        elif not browser_ready:
            report["status"] = "BLOCKED_BROWSER_RUNTIME"
            report["runtime_classification"] = f"BLOCKED_{playwright_state}"
        else:
            report["status"] = "BLOCKED_BROWSER_RUNTIME"
            report["runtime_classification"] = "NO_EVIDENCE_CAPTURED"

    except Exception as exc:
        report["status"] = "FAILED"
        report["error"] = str(exc)

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run UI engineering benchmark harness on target")
    parser.add_argument("target", help="Path to target project directory")
    parser.add_argument("--task", default="Modernize UI and verify responsiveness", help="Task prompt")
    parser.add_argument("--workflow", default=None, help="Workflow override")
    args = parser.parse_args()

    res = run_target_benchmark(args.target, args.task, workflow=args.workflow)
    print(json.dumps(res, indent=2))
    sys.exit(0 if res["status"] in ("INTEGRATION_VERIFIED", "BROWSER_E2E_VERIFIED", "BLOCKED_BROWSER_RUNTIME") else 1)
