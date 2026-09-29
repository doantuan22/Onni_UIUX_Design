"""Problem Diagnosis Engine.
Separates Problem Identification (Diagnosis) from Solution Generation (Strategy).
"""
from typing import Any
from uiux.engine.modification_planner.schemas import ProblemDiagnosis, ProblemDiagnosisItem

def diagnose_ui_issues(
    user_request: str,
    ui_context: dict[str, Any],
    knowledge_plan: dict[str, Any]
) -> ProblemDiagnosis:
    """Diagnose problems in the UI context based on the user request and evidence.
    Does NOT propose solutions.
    """
    req_lower = user_request.lower()
    issues: list[ProblemDiagnosisItem] = []
    
    # 1. Analyze Responsive Issues
    if any(w in req_lower for w in ("responsive", "mobile", "tablet", "overflow", "tràn", "co giãn")):
        issues.append({
            "id": "diag_responsive_01",
            "category": "RESPONSIVE",
            "surface": "global_or_target_component",
            "description": "Possible responsive layout overflow or improper stacking on smaller viewports.",
            "severity": "high",
            "evidence_refs": ["user_request"],
            "confidence": 0.8,
            "user_impact": "Users on mobile devices may not see critical information or actions.",
            "technical_impact": "Requires viewport constraint checks.",
            "is_inferred": True
        })
    
    # 2. Analyze Accessibility Issues
    if any(w in req_lower for w in ("a11y", "accessibility", "trợ năng", "contrast", "color blind", "tương phản")):
        issues.append({
            "id": "diag_a11y_01",
            "category": "ACCESSIBILITY",
            "surface": "global",
            "description": "Potential WCAG AA contrast violations or missing aria attributes.",
            "severity": "high",
            "evidence_refs": ["user_request"],
            "confidence": 0.9,
            "user_impact": "Visually impaired users may struggle to read or navigate the UI.",
            "technical_impact": "Requires color token adjustments and semantic HTML audits.",
            "is_inferred": True
        })

    # 3. Analyze UX / Flow Issues
    if any(w in req_lower for w in ("ux", "flow", "checkout", "cart", "form", "confusing", "luồng", "khó dùng")):
        issues.append({
            "id": "diag_ux_01",
            "category": "UX",
            "surface": "target_flow",
            "description": "User experience friction in the primary conversion or data-entry flow.",
            "severity": "medium",
            "evidence_refs": ["user_request", "ui_context"],
            "confidence": 0.7,
            "user_impact": "Increased drop-off rate and user frustration.",
            "technical_impact": "May require state management or layout sequence updates.",
            "is_inferred": True
        })

    # 4. Analyze Visual Polish
    if any(w in req_lower for w in ("modernize", "improve", "polish", "đẹp", "xấu", "cũ", "làm mới")):
        issues.append({
            "id": "diag_visual_01",
            "category": "VISUAL",
            "surface": "global",
            "description": "Visual presentation lacks modern aesthetic rhythm, spacing, or hierarchy.",
            "severity": "low",
            "evidence_refs": ["user_request"],
            "confidence": 0.85,
            "user_impact": "Lower perceived trust and brand quality.",
            "technical_impact": "Requires design token and spacing scale adjustments without breaking layout.",
            "is_inferred": True
        })

    # If no specific issues detected, add a generic one based on intent
    if not issues:
        issues.append({
            "id": "diag_generic_01",
            "category": "VISUAL",
            "surface": "target_component",
            "description": "General UI improvement requested without specific malfunction identified.",
            "severity": "low",
            "evidence_refs": ["user_request"],
            "confidence": 1.0,
            "user_impact": "Marginal improvement to user satisfaction.",
            "technical_impact": "Low risk, localized component styling.",
            "is_inferred": False
        })

    return {
        "issues": issues,
        "confidence_score": 0.85
    }
