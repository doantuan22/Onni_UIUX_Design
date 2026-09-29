"""Planning Gate Validator.
Verifies the Modification Plan is complete and authorized before allowing P3 execution.
"""
from typing import Any
from uiux.engine.modification_planner.schemas import ModificationPlan, PlanningGate
from uiux.engine.preservation import L3

def evaluate_planning_gate(plan: ModificationPlan) -> PlanningGate:
    """Evaluate the plan against strict P2 gate criteria."""
    missing_reqs = []
    permission_needed = []
    conflicts = []
    
    # 1. Check Goal & Workflow
    if not plan["requirement_profile"]["user_goal"]:
        missing_reqs.append("missing_user_goal")
        
    if not plan.get("metadata", {}).get("workflow"):
        missing_reqs.append("missing_workflow")
        
    # 2. Check Diagnosis
    if not plan["diagnosis"]["issues"]:
        missing_reqs.append("missing_diagnosis")
        
    # 3. Check Context
    if not plan["impact"]["affected_files"]:
        missing_reqs.append("missing_affected_files_surface")
        
    # 4. Check L3 Permissions
    overall_level = "L1"
    for change in plan["changes"]:
        if change["change_level"] == "L3":
            overall_level = "L3"
            
    preservation = plan.get("preservation", {})
    if overall_level == "L3" and "L3" not in preservation.get("precedence_rules", []):
        # We need to verify if permission is actually granted.
        # This is a simplification; realistically we check if explicit permission trace exists.
        has_l3_permission = False
        for req in plan["requirement_profile"]["preservation_requests"]:
            if "allow_redesign" in req.lower() or "override" in req.lower():
                has_l3_permission = True
                
        if not has_l3_permission:
            permission_needed.append("L3_major_redesign_permission_required")
            
    # 5. Legacy plan status must also allow execution
    legacy_status = plan.get("status")
    if legacy_status and legacy_status != "ready":
        conflicts.append(f"plan_status_{legacy_status}")
        if legacy_status == "needs_permission":
            permission_needed.append("explicit_user_permission_required")

    # 6. Check Verification Requirements
    if not plan["verification"]["check_steps"]:
        missing_reqs.append("missing_verification_contract")
        
    status = "PASS"
    if missing_reqs or permission_needed or conflicts:
        status = "BLOCKED"
        
    return {
        "status": status,
        "missing_requirements": missing_reqs,
        "permission_needed": permission_needed,
        "conflicts": conflicts,
        "recommended_next_action": "Proceed to DO phase (P3)." if status == "PASS" else "Request additional context or explicit permission from user."
    }
