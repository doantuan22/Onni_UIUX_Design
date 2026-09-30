"""Evidence-bounded P2 diagnosis.

Request intent is not treated as proof of a defect. P0 findings are carried
forward with their evidence; absent findings remain explicitly UNKNOWN.
"""
from __future__ import annotations

from typing import Any

from uiux.engine.modification_planner.schemas import ProblemDiagnosis, ProblemDiagnosisItem


def diagnose_ui_issues(
    user_request: str,
    ui_context: dict[str, Any],
    knowledge_plan: dict[str, Any],
    semantic_requirement: dict[str, Any] | None = None,
) -> ProblemDiagnosis:
    """Build diagnostic records from P0 evidence plus normalized request concerns."""
    semantic = semantic_requirement or {}
    issues: list[ProblemDiagnosisItem] = []
    supplied = ui_context.get("findings") or ui_context.get("issues") or ui_context.get("diagnostic_findings") or []
    if isinstance(supplied, list):
        for idx, finding in enumerate(supplied):
            if not isinstance(finding, dict) or not str(finding.get("description", "")).strip():
                continue
            description = str(finding["description"]).strip()
            refs = finding.get("evidence_refs") or finding.get("evidence") or []
            if isinstance(refs, str):
                refs = [refs]
            category = str(finding.get("category", "UNKNOWN")).upper()
            if category not in {"VISUAL", "UX", "RESPONSIVE", "ACCESSIBILITY", "CONSISTENCY", "ARCHITECTURAL_UI", "PERFORMANCE_UI", "UNKNOWN"}:
                category = "UNKNOWN"
            target = finding.get("surface") or finding.get("target") or semantic.get("target_surfaces", {}).get("value") or []
            issues.append({
                "id": str(finding.get("id") or f"diag_p0_{idx + 1}"),
                "category": category,
                "surface": target,
                "description": description,
                "severity": str(finding.get("severity", "medium")).lower(),
                "evidence_refs": list(refs) if isinstance(refs, list) else [],
                "confidence": 0.9 if refs else 0.3,
                "confidence_level": "HIGH" if refs else "LOW",
                "confidence_score": 0.9 if refs else 0.3,
                "user_impact": str(finding.get("user_impact") or "Impact requires confirmation against the supplied UI context."),
                "technical_impact": str(finding.get("technical_impact") or "Implementation impact is not yet established."),
                "is_inferred": False,
                "finding_state": "CONFIRMED" if refs else "UNKNOWN",
                "unknown_reason": "" if refs else "P0 finding did not include an evidence reference.",
            })

    request_categories = {"responsive": "RESPONSIVE", "accessibility": "ACCESSIBILITY",
        "component_consistency": "CONSISTENCY", "interaction": "UX"}
    target = semantic.get("target_surfaces", {}).get("value") or []
    target_label = ", ".join(str(x.get("name", x)) if isinstance(x, dict) else str(x) for x in target) or "an unspecified surface"
    for concern in semantic.get("concerns", []):
        category = request_categories.get(concern)
        if not category or any(item["category"] == category for item in issues):
            continue
        desc = f"The request targets {concern.replace('_', ' ')} for {target_label}; supplied P0 context contains no measured finding for this concern."
        issues.append({
            "id": f"diag_request_{concern}",
            "category": category,
            "surface": target,
            "description": desc,
            "severity": "low",
            "evidence_refs": list(semantic.get("evidence_refs", ["user_request"])),
            "confidence": 0.3,
            "confidence_level": "LOW",
            "confidence_score": 0.3,
            "user_impact": "User-stated quality goal; impact has not been measured in the supplied UI evidence.",
            "technical_impact": "Inspect the named surface and verify the concern before selecting implementation details.",
            "is_inferred": True,
            "finding_state": "UNKNOWN",
            "unknown_reason": "A requested concern is not itself proof of a defect; no corresponding P0 measurement was supplied.",
        })

    if not issues:
        issues.append({
            "id": "diag_unknown_01",
            "category": "UNKNOWN",
            "surface": target,
            "description": "No concrete UI defect is established by the supplied request and P0 evidence.",
            "severity": "low",
            "evidence_refs": [],
            "confidence": 0.0,
            "confidence_level": "LOW",
            "confidence_score": 0.0,
            "user_impact": "Unknown until the target and observed behavior are clarified.",
            "technical_impact": "No implementation diagnosis can be made without additional evidence.",
            "is_inferred": False,
            "finding_state": "UNKNOWN",
            "unknown_reason": "No evidence-backed finding or explicit concern was available.",
        })

    confirmed = [item for item in issues if item["finding_state"] == "CONFIRMED"]
    confidence = "HIGH" if confirmed and all(item["evidence_refs"] for item in confirmed) else "LOW" if any(item["finding_state"] == "UNKNOWN" for item in issues) else "MEDIUM"
    score = 0.9 if confidence == "HIGH" else 0.3 if confidence == "LOW" else 0.6
    return {"issues": issues, "confidence_level": confidence, "confidence_score": score,
        "evidence_refs": list(dict.fromkeys(ref for issue in issues for ref in issue["evidence_refs"]))}
