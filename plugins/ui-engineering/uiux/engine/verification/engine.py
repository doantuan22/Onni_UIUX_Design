"""Main P4 Verification Engine.

Orchestrates gates, correctness checks, preservation checks, design intent evaluations,
and repair routing to produce the FinalVerificationReport.
"""
from typing import Any
from pathlib import Path
from uiux.engine.verification.schemas import FinalVerificationReport
from uiux.engine.verification.gates import run_verification_gate, run_evidence_sufficiency_gate
from uiux.engine.verification.checks import verify_correctness, verify_preservation, verify_design_intent
from uiux.engine.verification.repair import generate_repair_plan
from uiux.engine.runtime_critic.session import RuntimeValidationSession
from uiux.engine.verification.static import StaticVerificationEngine
from uiux.engine.verification.strategy import detect_verification_capabilities, resolve_verification_strategy
from uiux.engine.verification.trust import cap_trust, provenance, validate_verification_result

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
            
        # 2. Resolve capabilities and run browser-independent checks before requiring browser evidence.
        session_data = self.session.to_dict()
        project_root = session_data.get("project_root") or session_data.get("repo_path")
        capabilities = session_data.get("verification_capabilities") or detect_verification_capabilities(
            project_root, implementation_report, session_data.get("runtime_detection"))
        evidence_location = self.session.after_evidence.get("evidence_dir")
        manifest_path = self.session.after_evidence.get("manifest_path")
        if manifest_path:
            evidence_location = Path(str(manifest_path)).expanduser().resolve().parent
        runtime_evidence_validation = session_data.get("runtime_evidence_validation")
        runtime_evidence_valid = bool(runtime_evidence_validation and runtime_evidence_validation.get("status") == "VALID")
        if runtime_evidence_valid:
            capabilities["runtime_dom"]["status"] = "AVAILABLE"
            capabilities["runtime_dom"]["reason"] = "Existing runtime evidence validator accepted the supplied capture manifest/files."
            capabilities["visual_render"]["status"] = "AVAILABLE" if any(
                cap.get("screenshot") or cap.get("file") for cap in self.session.after_evidence.get("captures", [])
            ) else capabilities["visual_render"]["status"]
            capabilities["interaction_a11y"]["status"] = "AVAILABLE" if (
                self.session.after_evidence.get("interactions") or self.session.after_evidence.get("accessibility")
            ) else capabilities["interaction_a11y"]["status"]
        strategy = resolve_verification_strategy(verification_contract, implementation_report, capabilities,
            session_data.get("ui_context"), self.session.before_evidence, self.session.affected_surface)
        static_report = None
        # Runtime-only legacy callers may not know the target root. Tier 1 always supplies it.
        if project_root or not runtime_evidence_valid:
            static_report = StaticVerificationEngine().verify(self.session.modification_plan or {}, implementation_report,
                session_data, verification_contract, project_root)

        # 3. Existing Evidence Sufficiency Gate. Missing capability/evidence is not a code failure;
        # static/build checks above remain useful and the result is classified as PARTIAL/BLOCKED.
        runtime_required = "RUNTIME_DOM" in strategy["required_levels"]
        e_gate = run_evidence_sufficiency_gate(
            self.session.after_evidence,
            verification_contract,
            has_baseline=self.session.has_baseline(),
            runtime_available=capabilities["runtime_dom"]["status"] == "AVAILABLE",
        ) if runtime_required else {"status": "PASS", "reason_code": None,
            "reason": "Runtime evidence is not required by the verification contract.", "missing_evidence": None}
        runtime_missing = (runtime_required and e_gate["status"] == "FAIL") or (runtime_required and self.session.has_runtime() and not runtime_evidence_valid)
        runtime_critic_report = None
        runtime_critic_error = None
        if runtime_evidence_valid and not runtime_missing:
            try:
                from uiux.engine.runtime_critic.critic import CriticEngine
                runtime_critic_report = CriticEngine().critique(self.session)
            except Exception as exc:
                runtime_critic_error = f"Existing P4 runtime critic could not evaluate validated evidence ({type(exc).__name__})."
            
        # 3. Core Checks
        correctness_issues = verify_correctness(self.session) if runtime_evidence_valid else []
        preservation_issues = verify_preservation(self.session, self.session.modification_plan or {})
        # Intent is never marked PASS without a real critic verdict and evidence.
        design_intent_results = [{"decision_id": d.get("id", "unknown"),
            "expected": d.get("intent", d.get("expected", "unknown intent")),
            "actual": "Not evaluated by an evidence-backed visual critic.", "result": "UNCERTAIN", "evidence": []}
            for d in decisions]
        
        all_issues = correctness_issues + preservation_issues
        critic_issues: list[dict[str, Any]] = []
        if runtime_critic_report:
            route_map = {
                "VISUAL_REGRESSION": ("IMPLEMENTATION_ERROR", "P3"),
                "PRESERVATION_VIOLATION": ("IMPLEMENTATION_ERROR", "P3"),
                "RESPONSIVE_FAILURE": ("IMPLEMENTATION_ERROR", "P3"),
                "INTERACTION_FAILURE": ("IMPLEMENTATION_ERROR", "P3"),
                "ACCESSIBILITY_REGRESSION": ("IMPLEMENTATION_ERROR", "P3"),
                "RUNTIME_ERROR": ("IMPLEMENTATION_ERROR", "P3"),
                "PLAN_DRIFT": ("PLAN_ERROR", "P2"),
                "MISSING_REQUIRED_STATE": ("PLAN_ERROR", "P2"),
            }
            for issue in runtime_critic_report.get("issues", []):
                if issue.get("status") not in {"new_regression", "worsened"}:
                    continue
                # Missing captures are a verification gap, not evidence of a code defect.
                # The evidence gate and required-level accounting below report PARTIAL.
                if issue.get("category") == "insufficient_evidence":
                    continue
                root_cause, route_to = route_map.get(issue.get("category"), ("UNKNOWN", "P4"))
                cap_ref = next((f"runtime:{cap.get('id') or cap.get('route', '/') + ':' + str(cap.get('viewport', 'unknown'))}"
                    for cap in self.session.after_evidence.get("captures", [])
                    if cap.get("route", cap.get("page_id", "/")) == issue.get("page", "/") and cap.get("viewport") == issue.get("viewport")), "runtime:critic-report")
                critic_issues.append({"id": issue.get("issue_id", "runtime-critic"), "category": issue.get("category", "RUNTIME_ISSUE"),
                    "severity": issue.get("severity", "MEDIUM"), "surface": issue.get("page", "/"),
                    "viewport": issue.get("viewport", "unknown"), "scenario": issue.get("scenario", "runtime"),
                    "expected": issue.get("expected", "Contract requirements pass"), "actual": issue.get("actual", issue.get("description", "Runtime critic found an issue")),
                    "evidence_refs": [cap_ref], "confidence": "confirmed", "root_cause": root_cause,
                    "route_to": route_to, "related_decision": None, "related_change": None,
                    "blocking": issue.get("severity") in {"CRITICAL", "HIGH"}, "repairable": bool(issue.get("repairable"))})
            all_issues.extend(critic_issues)
        
        # 4. Status Evaluation
        correctness_status = ("PASS" if not correctness_issues else "FAIL") if runtime_evidence_valid else "NOT_RUN"
        preservation_status = ("PASS" if not preservation_issues else "FAIL") if self.session.preservation_profile and self.session.change_manifest else "NOT_RUN"
        
        final_status = "PASS"
        if any(i["blocking"] for i in all_issues):
            final_status = "FAIL"
        elif all_issues:
            final_status = "PASS_WITH_WARNINGS"

        static_issues = (static_report or {}).get("issues", [])
        all_issues.extend(static_issues)
        if any(i.get("blocking", True) for i in static_issues):
            final_status = "FAIL"
        if runtime_missing and final_status not in {"FAIL", "BLOCKED"}:
            final_status = "PARTIAL"
        if runtime_critic_error and final_status not in {"FAIL", "BLOCKED"}:
            final_status = "PARTIAL"
        critic_has_regression = bool(runtime_critic_report and any(
            issue.get("category") != "insufficient_evidence" and issue.get("status") in {"new_regression", "worsened"}
            for issue in runtime_critic_report.get("issues", [])))
        if runtime_critic_report and runtime_critic_report.get("overall_status") == "fail" and critic_has_regression and final_status not in {"FAIL", "BLOCKED"}:
            final_status = "FAIL"
        elif runtime_critic_report and runtime_critic_report.get("overall_status") == "warn" and final_status == "PASS":
            final_status = "PASS_WITH_WARNINGS"
        if static_report and static_report.get("status") == "BLOCKED" and not self.session.has_runtime():
            final_status = "BLOCKED"
        elif static_report and static_report.get("status") == "PARTIAL" and final_status == "PASS":
            final_status = "PARTIAL"
        if strategy["unavailable_checks"] and final_status in {"PASS", "PASS_WITH_WARNINGS"}:
            final_status = "PARTIAL"
            
        # 5. Repair Routing
        repair_requests = generate_repair_plan(all_issues)
        
        execution_status = implementation_report.get("status", "UNKNOWN")
        evidence_refs = list(dict.fromkeys(
            list((static_report or {}).get("evidence_refs", [])) +
            [f"runtime:{cap.get('id') or cap.get('route', '/') + ':' + str(cap.get('viewport', 'unknown'))}"
             for cap in self.session.after_evidence.get("captures", []) if cap.get("status") == "CAPTURED"] +
            (["runtime:console_errors"] if self.session.after_evidence.get("console_errors") is not None else [])
        ))
        accessibility_validation = self.session.to_dict().get("accessibility_evidence_validation")
        if accessibility_validation and accessibility_validation.get("status") == "VALID":
            evidence_refs.extend(scan["evidence_ref"] for scan in accessibility_validation.get("scans", [])
                if isinstance(scan.get("evidence_ref"), str))
        if runtime_critic_report and runtime_critic_report.get("report_id"):
            evidence_refs.append(f"visual:critic:{runtime_critic_report['report_id']}")
        evidence_refs = list(dict.fromkeys(evidence_refs))
        completed_levels: list[str] = []
        if static_report and static_report.get("source_diff", {}).get("status") == "PASS": completed_levels.append("SOURCE_DIFF")
        if static_report and static_report.get("structure", {}).get("status") == "PASS": completed_levels.append("STATIC_STRUCTURE")
        if static_report and static_report.get("build", {}).get("status") == "PASS": completed_levels.append("BUILD_VALIDATION")
        if runtime_evidence_valid and not runtime_missing: completed_levels.append("RUNTIME_DOM")
        visual_check_passed = bool(runtime_critic_report and runtime_critic_report.get("overall_status") == "pass")
        if visual_check_passed and runtime_evidence_valid and any(cap.get("file") for cap in self.session.after_evidence.get("captures", [])):
            completed_levels.append("VISUAL_RENDER")
        # Interaction evidence is not accepted from arbitrary manifest fields. The
        # existing runner checks fixtures but has no live action executor or report.
        interaction_pass = False
        accessibility_evidence = self.session.after_evidence.get("accessibility", {})
        scenarios_text = " ".join(str(v) for v in (verification_contract.get("scenarios", []) + verification_contract.get("check_steps", []))).lower()
        needs_interactions = bool(verification_contract.get("interactions") or any(
            word in scenarios_text for word in ("interaction", "keyboard", "form", "modal", "navigation")))
        needs_accessibility = bool(verification_contract.get("accessibility_checks"))
        accessibility_pass = bool(accessibility_validation and accessibility_validation.get("status") == "VALID" and
            isinstance(accessibility_evidence, dict) and accessibility_evidence.get("status") == "PASS" and
            accessibility_evidence.get("evidence_refs"))
        if runtime_evidence_valid and visual_check_passed and ((needs_interactions or needs_accessibility) and
            (not needs_interactions or interaction_pass) and (not needs_accessibility or accessibility_pass)):
            completed_levels.append("INTERACTION_A11Y")
        missing_required_checks = set(strategy["required_levels"]) - set(completed_levels)
        if missing_required_checks and final_status in {"PASS", "PASS_WITH_WARNINGS"}:
            final_status = "PARTIAL"
        if runtime_missing and e_gate.get("reason_code") == "CAPABILITY_UNAVAILABLE" and not completed_levels and final_status not in {"FAIL", "BLOCKED"}:
            final_status = "BLOCKED"
        verification_status = final_status
        if verification_status not in {"NOT_RUN", "PASS", "PASS_WITH_WARNINGS", "PARTIAL", "FAIL", "BLOCKED"}:
            verification_status = "BLOCKED"
        if static_report and static_report.get("status") == "FAIL":
            trust_achieved = "UNVERIFIED"
        elif runtime_evidence_valid and not runtime_missing:
            trust_achieved = "RUNTIME_VERIFIED"
            if "VISUAL_RENDER" in strategy["required_levels"] and "VISUAL_RENDER" in completed_levels and \
               ("INTERACTION_A11Y" not in strategy["required_levels"] or "INTERACTION_A11Y" in completed_levels):
                trust_achieved = "MULTIMODAL_VERIFIED"
        elif static_report and static_report.get("source_diff", {}).get("status") == "PASS" and \
             static_report.get("structure", {}).get("status") == "PASS" and \
             (static_report.get("preservation", {}).get("status") == "PASS" or not (self.session.modification_plan or {}).get("preservation", {}).get("granular_permissions")) and \
             not any(i.get("blocking") for i in all_issues):
            trust_achieved = "STATICALLY_VERIFIED"
        else:
            trust_achieved = "UNVERIFIED"
        trust_achieved = cap_trust(trust_achieved, strategy["expected_trust_ceiling"])
        verified_claims = []
        if static_report and static_report.get("source_diff", {}).get("status") == "PASS":
            refs = [r for r in static_report.get("evidence_refs", []) if r.startswith(("source:", "p3:"))]
            if refs:
                verified_claims.append({**provenance("source-integrity", "SOURCE_INTEGRITY", refs,
                    "SOURCE_DIFF", "static_verification"), "claim": "Changed source files match the reported planned change ledger."})
        if static_report and static_report.get("framework", {}).get("status") == "PASS":
            refs = [f"source:{name}" for name in static_report.get("source_diff", {}).get("changed_files", [])]
            if refs:
                verified_claims.append({**provenance("framework-integrity", "FRAMEWORK_INTEGRITY", refs,
                    "STATIC_STRUCTURE", "existing_framework_adapter"), "claim": "Checked changed files against the detected framework structural rules."})
        if static_report and static_report.get("preservation", {}).get("status") == "PASS":
            refs = [ref for ref in static_report.get("evidence_refs", []) if ref.startswith(("token-baseline:", "p3:change-manifest"))]
            if refs:
                verified_claims.append({**provenance("preservation", "PRESERVATION", refs,
                    "STATIC_STRUCTURE", "static_token_comparison"), "claim": "Protected palette and brand tokens match the captured source baseline."})
        if static_report and static_report.get("build", {}).get("status") == "PASS":
            refs = [row["evidence_ref"] for row in static_report.get("build", {}).get("commands", []) if row.get("status") == "PASS"]
            if refs:
                verified_claims.append({**provenance("build-validity", "BUILD_VALIDITY", refs,
                    "BUILD_VALIDATION", "configured_project_commands"), "claim": "Detected configured build validation commands passed."})
        if runtime_evidence_valid and not runtime_missing and not correctness_issues:
            refs = [f"runtime:{cap.get('id') or cap.get('route', '/') + ':' + str(cap.get('viewport', 'unknown'))}"
                    for cap in self.session.after_evidence.get("captures", []) if cap.get("status") == "CAPTURED"]
            if refs:
                verified_claims.append({**provenance("runtime-correctness", "RUNTIME_CORRECTNESS", refs,
                    "RUNTIME_DOM", "P4_runtime_evidence"), "claim": "Captured routes loaded without newly detected runtime errors."})
        if "VISUAL_RENDER" in completed_levels:
            refs = [f"runtime:{cap.get('id') or cap.get('route', '/') + ':' + str(cap.get('viewport', 'unknown'))}"
                    for cap in self.session.after_evidence.get("captures", []) if cap.get("status") == "CAPTURED"]
            refs.append(f"visual:critic:{runtime_critic_report.get('report_id', 'P4')}" if runtime_critic_report else "visual:critic:P4")
            if refs:
                verified_claims.append({**provenance("visual-intent", "VISUAL_INTENT", list(dict.fromkeys(refs)),
                    "VISUAL_RENDER", "evidence_backed_visual_critic"), "claim": "The evidence-backed visual critic passed the requested visual checks."})
        if "INTERACTION_A11Y" in completed_levels and needs_accessibility:
            refs = accessibility_evidence.get("evidence_refs", [])
            verified_claims.append({**provenance("accessibility", "ACCESSIBILITY", refs,
                "INTERACTION_A11Y", "validated_axe_manifest"), "claim": "Task-required accessibility scans completed with no violations."})
        limitations = list((static_report or {}).get("limitations", []))
        if runtime_missing:
            if self.session.has_runtime() and not runtime_evidence_valid:
                limitations.append("Runtime captures were supplied without valid manifest/report/file provenance; runtime trust was not granted.")
                if runtime_evidence_validation:
                    limitations.extend(runtime_evidence_validation.get("errors", []))
            else:
                limitations.append(e_gate.get("reason", "Required runtime evidence is missing."))
        elif self.session.has_runtime() and not runtime_evidence_valid:
            limitations.append("Optional runtime captures were not trusted because manifest/report/file provenance is invalid.")
        if runtime_critic_error:
            limitations.append(runtime_critic_error)
        if needs_interactions:
            limitations.append("Interaction checks are unverified because the existing runner has no live browser action executor or evidence report.")
        limitations.extend(item["reason"] for item in strategy["unavailable_checks"])
        limitations = list(dict.fromkeys(limitations))
        result = {
            "schema_version": 2,
            "task_id": self.session.plan_id,
            "plan_id": self.session.plan_id,
            "implementation_id": implementation_report.get("plan_id", "unknown"),
            "status": final_status, # type: ignore
            "summary": (
                "Verification found a blocking implementation issue." if final_status == "FAIL" else
                "Implementation completed. Static checks passed, but rendered UI verification is unavailable." if final_status == "PARTIAL" and trust_achieved == "STATICALLY_VERIFIED" else
                "Verification is incomplete; see limitations and next actions." if final_status in {"PARTIAL", "BLOCKED"} else
                f"Required verification passed at {trust_achieved} trust."
            ),
            "execution_status": execution_status,
            "verification_status": verification_status,
            "trust_level": trust_achieved,
            "trust_achieved": trust_achieved,
            "trust_ceiling": strategy["expected_trust_ceiling"],
            "verification_levels_completed": completed_levels,
            "verification_levels_unavailable": strategy["unavailable_checks"],
            "required_checks": strategy["required_levels"],
            "completed_checks": completed_levels,
            "evidence_summary": f"{len(evidence_refs)} evidence reference(s); {len(verified_claims)} evidence-backed claim(s).",
            "evidence_sufficiency": {"status": e_gate.get("status"), "reason_code": e_gate.get("reason_code"),
                "reason": e_gate.get("reason"), "missing_evidence": e_gate.get("missing_evidence")},
            "evidence_refs": evidence_refs,
            "verified_claims": verified_claims,
            "unverified_claims": ([{"claim_type": "RESPONSIVE_BEHAVIOR", "status": "UNVERIFIED",
                "reason": "Responsive source signals are not proof of rendered mobile behavior."}]
                if static_report and static_report.get("responsive_signals", {}).get("status") == "STATIC_RESPONSIVE_SIGNAL" else []) +
                ([{"claim_type": "VISUAL_INTENT", "status": "UNVERIFIED", "reason": "No evidence-backed visual critic result was supplied."}]
                 if "VISUAL_RENDER" in strategy["required_levels"] and "VISUAL_RENDER" not in completed_levels else []) +
                ([{"claim_type": "INTERACTION", "status": "UNVERIFIED", "reason": "No passing interaction evidence was supplied."}]
                 if "INTERACTION_A11Y" in strategy["required_levels"] and "INTERACTION_A11Y" not in completed_levels else []) +
                ([{"claim_type": "RESPONSIVE_BEHAVIOR", "status": "UNVERIFIED", "reason": "Rendered responsive behavior requires runtime viewport evidence."}]
                 if "RUNTIME_DOM" not in strategy["selected_checks"] else []),
            "static_verification": static_report,
            "verification_strategy": strategy,
            "runtime_critic": runtime_critic_report,
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
            "limitations": limitations + [
                "Only correctness and preservation are checked here; design intent, responsive, interaction, "
                "accessibility and performance verdicts require build_critic_report on the same evidence.",
            ],
            "final_gate": final_status # type: ignore
        }
        result["trust_report"] = {"execution_status": execution_status, "verification_status": verification_status,
            "trust_achieved": trust_achieved, "trust_ceiling": strategy["expected_trust_ceiling"],
            "verification_levels_completed": result["verification_levels_completed"],
            "verification_levels_unavailable": strategy["unavailable_checks"], "verified_claims": verified_claims,
            "unverified_claims": result["unverified_claims"], "evidence_summary": result["evidence_summary"],
            "limitations": result["limitations"]}
        result["validation_errors"] = validate_verification_result({**result, "public_task_status": "COMPLETED" if verification_status in {"PASS", "PASS_WITH_WARNINGS"} else "PARTIAL"})
        if result["validation_errors"] and verification_status in {"PASS", "PASS_WITH_WARNINGS"}:
            result["status"] = result["verification_status"] = result["final_gate"] = "PARTIAL"
            result["limitations"].append("Verification result failed NO_FAKE_PASS provenance validation.")
        return result
        
    def _build_blocked_report(self, reason: str, gate: str) -> FinalVerificationReport:
        return {
            "schema_version": 2,
            "task_id": "unknown",
            "plan_id": "unknown",
            "implementation_id": "unknown",
            "status": "BLOCKED",
            "execution_status": "UNKNOWN", "verification_status": "BLOCKED", "trust_level": "UNVERIFIED",
            "trust_achieved": "UNVERIFIED", "trust_ceiling": "UNVERIFIED", "evidence_summary": "No verification evidence was accepted.",
            "evidence_refs": [], "verified_claims": [], "unverified_claims": [], "limitations": [reason],
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
        "scenarios": list(verification.get("scenarios", [])),
        "preservation_checks": list(verification.get("preservation_checks", [])),
        "accessibility_checks": list(verification.get("accessibility_checks", [])),
        "check_steps": list(verification.get("check_steps", [])),
    }
