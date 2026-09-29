"""Verification Checks for P4.

Contains evaluators for Correctness, Preservation, Visual Regression, and Design Intent.
"""
import uuid
from typing import Any
from uiux.engine.verification.schemas import VerificationIssue

def _build_issue(
    category: str, 
    severity: str, 
    description: str,
    evidence_refs: list[str],
    expected: str,
    actual: str,
    root_cause: str,
    route_to: str,
    repairable: bool,
    blocking: bool = False,
    page: str = "/",
    viewport: str = "desktop_1440"
) -> VerificationIssue:
    return {
        "id": f"issue_{uuid.uuid4().hex[:8]}",
        "category": category,
        "severity": severity,  # type: ignore
        "surface": page,
        "viewport": viewport,
        "scenario": "default",
        "expected": expected,
        "actual": actual,
        "evidence_refs": evidence_refs,
        "confidence": "high",
        "root_cause": root_cause,  # type: ignore
        "route_to": route_to,
        "related_decision": None,
        "related_change": None,
        "blocking": blocking,
        "repairable": repairable
    }

def verify_correctness(session: Any) -> list[VerificationIssue]:
    """Check for basic correctness (errors, crashes)."""
    issues = []
    if not session.has_runtime():
        return issues
        
    after_errors = session.get_console_errors()
    before_errors = {e.get("message", "") for e in session.get_before_console_errors()}
    
    for err in after_errors:
        msg = err.get("message", "")
        if msg not in before_errors:
            issues.append(_build_issue(
                category="RUNTIME_ERROR",
                severity="HIGH",
                description=f"Console error: {msg[:100]}",
                evidence_refs=["console.log"],
                expected="No console errors",
                actual=f"Error: {msg[:100]}",
                root_cause="IMPLEMENTATION_ERROR",
                route_to="P3",
                repairable=True,
                page=err.get("page_id", "/")
            ))
            
    # Capture failures
    for cap in session.after_evidence.get("captures", []):
        if cap.get("status") == "SCREENSHOT_FAILURE":
            issues.append(_build_issue(
                category="RUNTIME_ERROR",
                severity="CRITICAL",
                description="Page render failure",
                evidence_refs=[f"capture_{cap.get('id')}"],
                expected="Page renders successfully",
                actual="Render failure",
                root_cause="IMPLEMENTATION_ERROR",
                route_to="P3",
                repairable=True,
                page=cap.get("page_id", "/")
            ))
    return issues

def verify_preservation(session: Any, plan: dict[str, Any]) -> list[VerificationIssue]:
    """Check if protected tokens or files were modified."""
    issues = []
    pres = session.preservation_profile
    if not pres:
        return issues
        
    palette_locked = pres.get("granular_permissions", {}).get("palette") == "locked"
    manifest = session.change_manifest
    
    if palette_locked and manifest:
        changed_tokens = manifest.get("changed_tokens", [])
        for token in changed_tokens:
            if "primary" in token or "brand" in token or "bg-" in token: # Simplified heuristic
                issues.append(_build_issue(
                    category="PRESERVATION_VIOLATION",
                    severity="CRITICAL",
                    description=f"Color token '{token}' modified but palette is locked.",
                    evidence_refs=["change_manifest"],
                    expected="Palette unchanged",
                    actual=f"Token {token} modified",
                    root_cause="IMPLEMENTATION_ERROR",
                    route_to="P3",
                    repairable=True,
                    blocking=True
                ))
                
    return issues

def verify_design_intent(decisions: list[dict[str, Any]], session: Any) -> list[dict[str, Any]]:
    """Check if the Design Decisions were actually fulfilled."""
    results = []
    # Intent is not inferred from the absence of regressions. A visual critic must
    # provide a separately evidence-backed verdict before any decision can pass.
    for decision in decisions:
        results.append({
            "decision_id": decision.get("id", "unknown"),
            "expected": decision.get("intent", "unknown intent"),
            "actual": "Not evaluated by an evidence-backed visual critic.",
            "result": "UNCERTAIN",
            "evidence": []
        })
    return results
