"""Structured P2 strategy synthesis with explicit diagnosis/knowledge/constraint trace."""
from __future__ import annotations

from typing import Any

from uiux.engine.modification_planner.schemas import DesignStrategy, ProblemDiagnosis


def build_design_strategy(
    diagnosis: ProblemDiagnosis,
    knowledge_plan: dict[str, Any],
    ui_context: dict[str, Any],
    semantic_requirement: dict[str, Any] | None = None,
) -> DesignStrategy:
    """Build bounded strategy proposals; UNKNOWN diagnosis is never presented as a fact."""
    semantic = semantic_requirement or {}
    selected = [k for k in knowledge_plan.get("selected_knowledge", []) if isinstance(k, dict) and k.get("id")]
    selected_ids = [str(k["id"]) for k in selected]
    target_values = (semantic.get("target_surfaces", {}) or {}).get("value") or []
    targets = [str(item.get("name") or item.get("route")) if isinstance(item, dict) else str(item) for item in target_values]
    target_label = ", ".join(targets) or "unresolved target"
    constraints = [str(item.get("value")) for item in semantic.get("must_keep", []) if isinstance(item, dict) and item.get("value")]
    constraints += [str(item.get("value")) for item in semantic.get("must_not_change", []) if isinstance(item, dict) and item.get("value")]
    change_level = str((ui_context.get("change_classification") or {}).get("overall_level") or ui_context.get("maximum_change_level") or "L1")

    strategy: DesignStrategy = {"knowledge_used": [], "decisions": []}
    decisions: list[dict[str, Any]] = []
    concern_to_category = {"responsive": "RESPONSIVE", "accessibility": "ACCESSIBILITY",
        "component_consistency": "CONSISTENCY", "interaction": "UX"}
    advice = {
        "responsive": f"Inspect {target_label} at the requested narrow viewports and make only evidence-supported responsive changes; preserve desktop behavior when requested.",
        "accessibility": f"Inspect keyboard focus, labels and scan findings on {target_label}; address only confirmed gaps and retain current framework primitives.",
        "component_consistency": f"Compare the named controls on {target_label} with existing component variants and tokens before changing shared styles.",
        "interaction": f"Trace the named form/control behavior on {target_label}; preserve business logic and change only the UI boundary supported by evidence.",
        "visual": f"Compare {target_label} with the supplied P0 structure/tokens and named visual goal; do not infer a defect from aesthetic wording alone.",
    }
    concerns = list(semantic.get("concerns", []))
    if semantic.get("visual_intent", {}).get("value"):
        concerns.append("visual")
    for concern in dict.fromkeys(concerns):
        category = concern_to_category.get(concern)
        linked = [item for item in diagnosis.get("issues", []) if not category or item.get("category") == category]
        knowledge_matches = [kid for kid in selected_ids if any(term in kid.lower() for term in {
            "responsive": ("responsive", "layout", "grid"),
            "accessibility": ("access", "a11y", "focus", "interaction"),
            "component_consistency": ("component", "button", "style", "token"),
            "interaction": ("interaction", "form", "focus"),
            "visual": ("style", "typography", "layout", "visual", "token"),
        }.get(concern, (concern,)))]
        evidence_refs = list(dict.fromkeys(ref for issue in linked for ref in issue.get("evidence_refs", [])))
        decision = {
            "id": f"strategy_{concern}", "target": targets or [], "concern": concern,
            "reason": f"The normalized request explicitly identifies {concern.replace('_', ' ')}; P0 evidence is required before asserting a defect.",
            "expected_result": f"The requested {concern.replace('_', ' ')} behavior is addressed on the bounded target without extending scope.",
            "knowledge_refs": knowledge_matches, "evidence_refs": evidence_refs,
            "constraints": constraints, "change_level": change_level,
            "diagnosis_refs": [issue.get("id") for issue in linked],
            "target_unknown_reason": "; ".join(item.get("reason", "") for item in semantic.get("ambiguities", [])) if not targets else "",
        }
        decisions.append(decision)
        if concern == "responsive":
            strategy["responsive_strategy"] = advice[concern]
        elif concern == "accessibility":
            strategy["accessibility_strategy"] = advice[concern]
        elif concern == "component_consistency":
            strategy["component_strategy"] = advice[concern]
        elif concern == "interaction":
            strategy["interaction_strategy"] = advice[concern]
        elif concern == "visual":
            strategy["hierarchy_strategy"] = advice[concern]
        for knowledge_id in knowledge_matches:
            strategy["knowledge_used"].append({"knowledge_id": knowledge_id,
                "reason": f"Selected P1 knowledge is relevant to the {concern.replace('_', ' ')} concern on {target_label}.",
                "diagnosis_refs": ",".join(decision["diagnosis_refs"]), "evidence_refs": ",".join(evidence_refs)})
    strategy["decisions"] = decisions
    strategy["target"] = targets
    strategy["constraints"] = list(dict.fromkeys(constraints))
    strategy["reasoning_mode"] = semantic.get("reasoning_mode", "HEURISTIC_FALLBACK")
    return strategy
