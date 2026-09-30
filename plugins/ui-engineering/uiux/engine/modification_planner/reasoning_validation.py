"""Development completeness checks for structured P2 reasoning output."""
from __future__ import annotations

from typing import Any


def validate_reasoning_completeness(plan: dict[str, Any]) -> dict[str, Any]:
    """Flag missing reasoning fields while allowing well-explained UNKNOWN values."""
    issues: list[dict[str, str]] = []
    for index, diagnosis in enumerate((plan.get("diagnosis") or {}).get("issues", [])):
        label = str(diagnosis.get("id") or f"diagnosis_{index}")
        if not str(diagnosis.get("description", "")).strip():
            issues.append({"code": "EMPTY_DIAGNOSIS_DESCRIPTION", "item": label, "reason": "Diagnosis descriptions must not be empty."})
        if diagnosis.get("category") == "UNKNOWN" or diagnosis.get("finding_state") == "UNKNOWN":
            if not str(diagnosis.get("unknown_reason", "")).strip():
                issues.append({"code": "UNKNOWN_DIAGNOSIS_WITHOUT_REASON", "item": label, "reason": "Unknown diagnosis needs an explicit reason."})
        if diagnosis.get("finding_state") == "CONFIRMED" and not diagnosis.get("evidence_refs"):
            issues.append({"code": "CONFIRMED_DIAGNOSIS_WITHOUT_EVIDENCE", "item": label, "reason": "Confirmed findings require evidence references."})
    for index, chunk in enumerate(plan.get("execution_chunks", [])):
        label = str(chunk.get("id") or f"chunk_{index}")
        for field in ("description", "scope", "expected_result"):
            if not str(chunk.get(field, "")).strip():
                issues.append({"code": f"EMPTY_CHUNK_{field.upper()}", "item": label, "reason": f"Execution chunk field {field} is required."})
    strategy = plan.get("strategy") or {}
    for index, decision in enumerate(strategy.get("decisions", [])):
        label = str(decision.get("id") or f"strategy_{index}")
        if not decision.get("target") and not decision.get("target_unknown_reason"):
            issues.append({"code": "STRATEGY_TARGET_UNKNOWN", "item": label, "reason": "Target is unresolved; strategy must explain ambiguity."})
        if not decision.get("reason") or not decision.get("expected_result"):
            issues.append({"code": "STRATEGY_TRACE_INCOMPLETE", "item": label, "reason": "Decision rationale and expected result are required."})
        if not decision.get("knowledge_refs") and not decision.get("evidence_refs"):
            issues.append({"code": "STRATEGY_TRACE_WITHOUT_SUPPORT", "item": label, "reason": "Strategy should cite P0 evidence or relevant P1 knowledge when available."})
    semantic = (plan.get("request") or {}).get("semantic_requirements") or {}
    target_field = semantic.get("target_surfaces", {})
    matched_targets = [x for x in (target_field.get("value") or []) if isinstance(x, dict) and x.get("route") and x.get("kind") != "surface_candidate"]
    if len(matched_targets) == 1 and not (plan.get("impact") or {}).get("affected_pages"):
        issues.append({"code": "UNPOPULATED_GROUNDED_PAGE", "item": str(matched_targets[0]["route"]), "reason": "P0 identified one target page, but impact omitted it."})
    return {"status": "PASS" if not issues else "WARN", "issues": issues,
        "reasoning_mode": plan.get("reasoning_mode", "HEURISTIC_FALLBACK")}
