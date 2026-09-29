"""Execution Gate Validator.
Ensures P3 only runs if P2 correctly approved the plan.
"""
from typing import Any
from uiux.engine.executor.schemas import ExecutionGateReport

def check_execution_gate(plan: dict[str, Any]) -> ExecutionGateReport:
    """Validate that the plan is ready for P3 execution."""
    gate = plan.get("planning_gate", {})
    if gate.get("status") != "PASS":
        return {
            "status": "BLOCKED",
            "reason": "PlanningGate did not pass.",
            "missing_contract": gate.get("missing_requirements", []),
            "invalid_scope": []
        }
        
    missing = []
    if not plan.get("impact", {}).get("affected_files"):
        missing.append("No allowed files in impact analysis.")
        
    if not plan.get("execution_chunks"):
        missing.append("No execution chunks defined.")
        
    if not plan.get("verification", {}).get("check_steps"):
        missing.append("No verification contract defined.")
        
    if missing:
        return {
            "status": "BLOCKED",
            "reason": "ModificationPlan is missing required execution contracts.",
            "missing_contract": missing,
            "invalid_scope": []
        }
        
    return {
        "status": "PASS",
        "reason": "Plan is fully authorized and ready for implementation.",
        "missing_contract": [],
        "invalid_scope": []
    }
