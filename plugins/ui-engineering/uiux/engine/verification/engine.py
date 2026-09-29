"""Main P4 Verification Engine.

Orchestrates gates, correctness checks, preservation checks, design intent evaluations,
and repair routing to produce the FinalVerificationReport.
"""
from typing import Any
from uiux.engine.verification.schemas import FinalVerificationReport
from uiux.engine.verification.gates import run_verification_gate, run_evidence_sufficiency_gate
from uiux.engine.verification.checks import verify_correctness, verify_preservation, verify_design_intent
from uiux.engine.verification.repair import generate_repair_plan
from uiux.engine.runtime_critic.session import RuntimeValidationSession

class VerificationEngine:
    """The P4 Check Engine."""
    
    def __init__(self, session_data: dict[str, Any]):
        self.session = RuntimeValidationSession.from_dict(session_data)
        
    def verify(self, 
               implementation_report: dict[str, Any], 
               verification_contract: dict[str, Any],
               decisions: list[dict[str, Any]]) -> FinalVerificationReport:
        """Run the full P4 Verification pipeline."""
        
        # 1. Verification Gate
        v_gate = run_verification_gate(implementation_report, verification_contract)
        if v_gate["status"] == "BLOCKED":
            return self._build_blocked_report(v_gate["reason"], "Verification Gate Failed")
            
        # 2. Evidence Sufficiency Gate
        e_gate = run_evidence_sufficiency_gate(
            self.session.after_evidence, 
            verification_contract, 
            has_baseline=self.session.has_baseline()
        )
        if e_gate["status"] == "FAIL":
            return self._build_blocked_report(e_gate["reason"], "Evidence Sufficiency Gate Failed")
            
        # 3. Core Checks
        correctness_issues = verify_correctness(self.session)
        preservation_issues = verify_preservation(self.session, self.session.modification_plan or {})
        design_intent_results = verify_design_intent(decisions, self.session)
        
        all_issues = correctness_issues + preservation_issues
        
        # 4. Status Evaluation
        correctness_status = "PASS" if not correctness_issues else "FAIL"
        preservation_status = "PASS" if not preservation_issues else "FAIL"
        
        final_status = "PASS"
        if any(i["blocking"] for i in all_issues):
            final_status = "FAIL"
        elif all_issues:
            final_status = "PASS_WITH_WARNINGS"
            
        # 5. Repair Routing
        repair_requests = generate_repair_plan(all_issues)
        
        return {
            "schema_version": 2,
            "task_id": self.session.plan_id,
            "plan_id": self.session.plan_id,
            "implementation_id": implementation_report.get("plan_id", "unknown"),
            "status": final_status, # type: ignore
            "correctness": {
                "status": correctness_status, # type: ignore
                "issues": correctness_issues
            },
            "preservation": {
                "status": preservation_status, # type: ignore
                "issues": preservation_issues
            },
            "design_intent": {
                "status": "NOT_EVALUATED",
                "decisions": design_intent_results
            },
            "responsive": {"status": "NOT_EVALUATED"},
            "interactions": {"status": "NOT_EVALUATED"},
            "accessibility": {"status": "NOT_EVALUATED"},
            "performance": {"status": "NOT_EVALUATED"},
            "regressions": {"issues": {}},
            "evidence": {
                "completeness": e_gate["status"],
                "refs": ["after_evidence.json"]
            },
            "repair": {
                "required": len(repair_requests) > 0,
                "routes": repair_requests
            },
            "warnings": [],
            "limitations": [
                "Only correctness and preservation are checked here; design intent, responsive, interaction, "
                "accessibility and performance verdicts require build_critic_report on the same evidence.",
            ],
            "final_gate": final_status # type: ignore
        }
        
    def _build_blocked_report(self, reason: str, gate: str) -> FinalVerificationReport:
        return {
            "schema_version": 2,
            "task_id": "unknown",
            "plan_id": "unknown",
            "implementation_id": "unknown",
            "status": "BLOCKED",
            "correctness": {"status": "BLOCKED", "issues": []},
            "preservation": {"status": "BLOCKED", "issues": []},
            "design_intent": {"status": "BLOCKED", "decisions": []},
            "responsive": {"status": "BLOCKED"},
            "interactions": {"status": "BLOCKED"},
            "accessibility": {"status": "BLOCKED"},
            "performance": {"status": "BLOCKED"},
            "regressions": {"issues": {}},
            "evidence": {"completeness": "FAIL", "refs": []},
            "repair": {"required": False, "routes": []},
            "warnings": [f"{gate}: {reason}"],
            "limitations": [],
            "final_gate": "BLOCKED"
        }


def contract_from_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Derive the P4 evidence contract (required viewports/routes) from a Modification Plan's ``verification`` block."""
    verification = plan.get("verification") or {}
    return {
        "required_viewports": list(verification.get("viewports", [])),
        "required_routes": list(verification.get("required_routes", [])),
        "requires_baseline": bool(verification.get("requires_baseline", False)),
    }
