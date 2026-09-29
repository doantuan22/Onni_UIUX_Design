"""Gates for P4 Verification Engine.

Includes VerificationGate (checks if P3 implementation is ready) and 
EvidenceSufficiencyGate (checks if runtime evidence meets P2 VerificationContract).
"""
from typing import Any

def run_verification_gate(implementation_report: dict[str, Any], verification_contract: dict[str, Any]) -> dict[str, Any]:
    """Check if P4 should proceed based on P3 output."""
    if not implementation_report.get("ready_for_p4", False):
        return {
            "status": "BLOCKED",
            "reason": "Implementation Report is not ready for P4.",
            "missing_artifact": "ready_for_p4 flag is False"
        }
        
    if implementation_report.get("deviations"):
        critical_deviations = [d for d in implementation_report.get("deviations", []) if d.get("risk") in ("high", "critical")]
        if critical_deviations:
            return {
                "status": "BLOCKED",
                "reason": "Unresolved critical deviations from P3.",
                "unresolved_deviation": critical_deviations[0].get("type")
            }
            
    if not verification_contract:
        return {
            "status": "BLOCKED",
            "reason": "Missing VerificationContract from P2.",
            "missing_artifact": "verification_contract"
        }
        
    return {"status": "PASS"}

def run_evidence_sufficiency_gate(
    evidence: dict[str, Any], 
    verification_contract: dict[str, Any],
    has_baseline: bool = False,
    runtime_available: bool | None = None,
) -> dict[str, Any]:
    """Check if the captured evidence fulfills the P2 VerificationContract."""
    if not evidence or not evidence.get("captures"):
        return {
            "status": "FAIL",
            "reason": "No evidence captures provided.",
            "missing_evidence": "captures",
            "reason_code": "MISSING_REQUIRED_EVIDENCE" if runtime_available is not False else "CAPABILITY_UNAVAILABLE",
        }
        
    captured_viewports = {cap.get("viewport") for cap in evidence.get("captures", []) if cap.get("status") == "CAPTURED"}
    captured_routes = {cap.get("route") for cap in evidence.get("captures", []) if cap.get("status") == "CAPTURED"}
    
    required_viewports = set(verification_contract.get("required_viewports", []))
    required_routes = set(verification_contract.get("required_routes", []))
    
    missing_viewports = required_viewports - captured_viewports
    if missing_viewports:
        return {
            "status": "FAIL",
            "reason": f"Missing required viewports: {missing_viewports}",
            "missing_evidence": "viewport",
            "reason_code": "MISSING_REQUIRED_EVIDENCE",
        }
        
    missing_routes = required_routes - captured_routes
    if missing_routes:
        return {
            "status": "FAIL",
            "reason": f"Missing required routes: {missing_routes}",
            "missing_evidence": "route",
            "reason_code": "MISSING_REQUIRED_EVIDENCE",
        }
        
    if verification_contract.get("requires_baseline", False) and not has_baseline:
        return {
            "status": "FAIL",
            "reason": "VerificationContract requires baseline comparison, but no baseline is available.",
            "missing_evidence": "baseline",
            "reason_code": "MISSING_REQUIRED_EVIDENCE",
        }
        
    return {"status": "PASS", "reason_code": None, "missing_evidence": None}
