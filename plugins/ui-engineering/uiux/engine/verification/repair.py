"""Repair Routing and Issue Classification for P4.

Classifies issues by root cause and routes them to the appropriate upstream phase.
"""
from typing import Any
from uiux.engine.verification.schemas import VerificationIssue, RepairRequest

def classify_and_route(issue: VerificationIssue) -> RepairRequest:
    """Classify the root cause of an issue and generate a Repair Request."""
    root_cause = issue["root_cause"]
    route_to = issue["route_to"]
    
    # Heuristics for overriding root cause
    if issue["category"] == "PRESERVATION_VIOLATION":
        # If P3 changed it despite plan saying locked
        root_cause = "IMPLEMENTATION_ERROR"
        route_to = "P3"
    elif issue["category"] == "PLAN_DRIFT":
        # If P2 generated a plan that didn't include required files
        # Actually PLAN_DRIFT means P3 deviated from P2.
        root_cause = "IMPLEMENTATION_ERROR"
        route_to = "P3"
        
    return {
        "issue_id": issue["id"],
        "route_to": route_to,
        "root_cause": root_cause,
        "target": issue["surface"],
        "evidence": issue["evidence_refs"],
        "expected": issue["expected"],
        "actual": issue["actual"],
        "allowed_scope": "targeted_repair",
        "related_plan": issue["related_decision"],
        "required_recheck": [issue["viewport"]]
    }

def generate_repair_plan(issues: list[VerificationIssue]) -> list[RepairRequest]:
    """Generate repair requests for all repairable issues."""
    return [classify_and_route(issue) for issue in issues if issue["repairable"]]
