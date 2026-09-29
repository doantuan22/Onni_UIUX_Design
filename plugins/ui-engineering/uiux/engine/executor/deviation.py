"""Plan Deviation Protocol.
Handles scenarios where P3 cannot proceed because the plan is incompatible with the reality of the implementation.
"""
from uiux.engine.executor.schemas import PlanDeviation

def build_deviation(
    plan_id: str,
    deviation_type: str,
    condition: str,
    required_change: str,
    affected_scope: str,
    risk: str = "high"
) -> PlanDeviation:
    """Create a PlanDeviation artifact to return to P2."""
    return {
        "type": deviation_type,  # type: ignore
        "current_plan_id": plan_id,
        "discovered_condition": condition,
        "required_change": required_change,
        "affected_scope": affected_scope,
        "risk": risk,
        "recommended_action": "Return to P2 to replan with the newly discovered constraints."
    }
