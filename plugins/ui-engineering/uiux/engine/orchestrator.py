"""UI Orchestrator: Central entry point and workflow router for the UI Engineering Plugin.

Responsibilities:
1. Normalize user intent & parse request constraints.
2. Determine UI State via UIStateDetector (GREENFIELD, PARTIAL_UI, EXISTING_UI, UNKNOWN).
3. Route to dedicated workflow (Greenfield UI vs. Existing UI/UX).
4. Enforce Hard Preservation Rules & Granular Permissions (L1/L2/L3 change budget).
5. Resolve required capabilities & knowledge categories without embedding raw content.
6. Formulate execution plan, validation requirements, and phase handoff.
"""
from __future__ import annotations

import re
from typing import Any

from uiux.engine.preservation import (
    L1,
    L2,
    L3,
    PRECEDENCE_HIERARCHY,
    evaluate_preservation_policy,
    extract_explicit_permissions,
    infer_requested_scope,
)
from uiux.engine.ui_state import (
    EXISTING_UI,
    GREENFIELD,
    PARTIAL_UI,
    UNKNOWN,
    detect_ui_state,
)

# Known skill modules in this plugin
SKILL_MAP = {
    "ux_structure": "skills/ux-structure",
    "design_direction": "skills/design-direction",
    "design_inspiration": "skills/design-inspiration",
    "design_system": "skills/design-system",
    "typography": "skills/typography",
    "visual_language": "skills/visual-language",
    "component_realization": "skills/component-realization",
    "responsive_interaction": "skills/responsive-interaction",
    "frontend_implementation": "skills/frontend-implementation",
    "visual_qa": "skills/visual-qa",
    "final_quality_gate": "skills/final-quality-gate",
}


def normalize_intent(user_intent: str | None, user_request: str) -> str:
    """Normalize user intent into a canonical category."""
    if user_intent and user_intent.strip():
        return user_intent.strip().lower()
    req_lower = user_request.lower()
    if any(k in req_lower for k in ("từ đầu", "from scratch", "xây mới", "new app", "new project", "create new")):
        return "greenfield_build"
    if any(k in req_lower for k in ("redesign", "thiết kế lại", "overhaul")):
        return "redesign"
    if any(k in req_lower for k in ("responsive", "mobile", "tablet", "co giãn", "màn hình")):
        return "responsive_refinement"
    if any(k in req_lower for k in ("a11y", "accessibility", "trợ năng", "screen reader", "contrast")):
        return "accessibility_refinement"
    if any(k in req_lower for k in ("modernize", "làm đẹp", "nâng cấp", "clean up", "polish")):
        return "visual_polish"
    if any(k in req_lower for k in ("audit", "đánh giá", "kiểm tra", "review")):
        return "ui_audit"
    if any(k in req_lower for k in ("fix", "sửa", "bug", "lỗi")):
        return "local_fix"
    return "general_ui_request"


def resolve_skills_and_knowledge(
    workflow: str,
    max_change_level: str,
    requested_scope: str,
    user_request: str,
    ambition: str = "refine",
) -> tuple[list[str], list[str]]:
    """Resolve required skills and knowledge categories based on workflow and change level."""
    req_lower = user_request.lower()
    skills: list[str] = []
    knowledge: list[str] = []

    if workflow == "greenfield":
        skills.extend([
            "skills/ux-structure",
            "skills/design-direction",
            "skills/design-inspiration",
            "skills/design-system",
            "skills/typography",
            "skills/frontend-implementation",
            "skills/visual-qa",
        ])
        knowledge.extend([
            "styles",
            "layouts",
            "screens",
            "web-patterns",
            "technologies",
        ])
        if any(term in req_lower for term in ("motion", "animation", "transition", "hiệu ứng")):
            knowledge.append("motion")
        if any(term in req_lower for term in ("interact", "gesture", "drag", "modal", "dropdown")):
            knowledge.append("interactions")
        return skills, sorted(set(knowledge))

    if workflow == "unknown":
        return ["skills/ux-structure", "skills/visual-qa"], ["screens"]

    # EXISTING UI WORKFLOW:
    # Scale capabilities by scope and change level
    if max_change_level == L1:
        # Safe refinement only
        if any(term in req_lower for term in ("responsive", "mobile", "tablet")):
            skills.append("skills/responsive-interaction")
            knowledge.extend(["layouts", "web-patterns"])
        if any(term in req_lower for term in ("a11y", "accessibility", "contrast")):
            skills.append("skills/visual-qa")
        if any(term in req_lower for term in ("font", "type", "typography", "chữ")):
            skills.append("skills/typography")
        skills.extend(["skills/visual-qa", "skills/final-quality-gate"])
        knowledge.append("components")

    elif max_change_level == L2 and ambition == "elevate":
        # ELEVATE: re-compose pages inside the protected shell and brand
        skills.extend([
            "skills/design-direction",
            "skills/design-inspiration",
            "skills/typography",
            "skills/visual-language",
            "skills/component-realization",
            "skills/responsive-interaction",
            "skills/frontend-implementation",
            "skills/visual-qa",
            "skills/final-quality-gate",
        ])
        knowledge.extend(["components", "web-patterns", "layouts", "motion", "effects", "visual-language", "typography"])

    elif max_change_level == L2:
        # Local structural change
        skills.extend([
            "skills/ux-structure",
            "skills/component-realization",
            "skills/responsive-interaction",
            "skills/visual-qa",
            "skills/final-quality-gate",
        ])
        knowledge.extend(["components", "web-patterns", "layouts"])

    elif max_change_level == L3:
        # Explicit major redesign
        skills.extend([
            "skills/ux-structure",
            "skills/design-direction",
            "skills/design-system",
            "skills/visual-language",
            "skills/frontend-implementation",
            "skills/visual-qa",
            "skills/final-quality-gate",
        ])
        knowledge.extend(["styles", "layouts", "screens", "components", "web-patterns"])

    # Contextual knowledge adds
    if any(term in req_lower for term in ("motion", "animation", "hiệu ứng")):
        knowledge.append("motion")
    if any(term in req_lower for term in ("interact", "command", "drag")):
        knowledge.append("interactions")

    # If empty skills fallback
    if not skills:
        skills = ["skills/visual-qa", "skills/final-quality-gate"]
    if not knowledge:
        knowledge = ["components"]

    return sorted(set(skills)), sorted(set(knowledge))


def resolve_validation_requirements(
    workflow: str,
    max_change_level: str,
    preservation_required: bool,
) -> list[str]:
    """Define machine-readable validation checks."""
    reqs: list[str] = [
        "Structure Contract Check (Artifact versions & scope match)",
        "Accessibility Gate (WCAG AA contrast & keyboard navigation)",
        "Visual QA & Responsive Viewport Check",
    ]
    if preservation_required and max_change_level in (L1, L2):
        reqs.append("Preservation Policy Enforcer: Verify Brand & Palette remain unmodified")
        reqs.append("Layout Non-regression Check: Ensure established navigation model is retained")
    if workflow == "greenfield":
        reqs.append("Design System Consistency Check: Token hierarchy, type scale & palette compliance")
        reqs.append("UX Flow Completeness Check: Page inventory and state coverage")
    return reqs


def orchestrate(request: dict[str, Any]) -> dict[str, Any]:
    """Primary orchestration entry point.

    Takes OrchestratorInput and produces OrchestratorOutput.
    """
    user_request: str = request.get("user_request", "").strip()
    raw_intent: str | None = request.get("user_intent")
    repo_context: dict[str, Any] | None = request.get("repo_context")
    explicit_constraints: dict[str, Any] | None = request.get("explicit_constraints")
    requested_scope: str = request.get("requested_scope", "unspecified")
    explicit_permissions: dict[str, Any] | None = request.get("explicit_permissions")

    # 1. Normalize intent
    normalized_intent = normalize_intent(raw_intent, user_request)

    # 2. Extract explicit permissions
    extracted_perms = extract_explicit_permissions(user_request, explicit_permissions)

    # 3. Detect UI State
    state_report = detect_ui_state(repo_context)
    ui_state = state_report["ui_state"]
    confidence = state_report["confidence"]

    # 4. Route Workflow
    # Rule: If confidence < 0.5 or UNKNOWN state -> workflow is "unknown"
    # Rule: If user explicitly asked to rebuild from scratch -> greenfield
    # Rule: If ui_state is GREENFIELD -> greenfield
    # Rule: If ui_state is EXISTING_UI or PARTIAL_UI -> existing-ui
    if extracted_perms["allow_rebuild"] and any(term in user_request.lower() for term in ("từ đầu", "from scratch", "xây mới", "new app")):
        workflow = "greenfield"
    elif ui_state == GREENFIELD:
        workflow = "greenfield"
    elif ui_state in (EXISTING_UI, PARTIAL_UI):
        workflow = "existing-ui"
    else:
        workflow = "unknown"

    # 5. Evaluate Preservation Policy and Permissions (L1 / L2 / L3)
    preservation = evaluate_preservation_policy(
        workflow=workflow,
        ui_state=ui_state,
        user_request=user_request,
        explicit_permissions=explicit_permissions,
        requested_scope=requested_scope,
    )

    max_level = preservation["allowed_change_level"]["max_level"]
    scope = preservation["scope"]

    # 6. Resolve Skills and Knowledge
    required_skills, required_knowledge = resolve_skills_and_knowledge(
        workflow=workflow,
        max_change_level=max_level,
        requested_scope=scope,
        user_request=user_request,
        ambition=preservation["ambition"],
    )

    # 7. Resolve Validation Requirements
    validation_reqs = resolve_validation_requirements(
        workflow=workflow,
        max_change_level=max_level,
        preservation_required=preservation["preservation_required"],
    )

    # 8. Check for user-specified constraints on Greenfield (Case 7 & 8)
    design_freedom = preservation["design_freedom"]
    additional_notes = list(preservation["notes"])
    if workflow == "greenfield":
        has_user_palette = False
        if explicit_constraints and ("palette" in explicit_constraints or "colors" in explicit_constraints):
            has_user_palette = True
        elif any(term in user_request.lower() for term in ("palette", "tông màu", "màu chủ đạo", "màu sắc:", "color:")):
            has_user_palette = True

        if has_user_palette:
            design_freedom = "constrained"
            additional_notes.append(
                "User explicitly specified color palette/constraints: user constraints take precedence over AI choice."
            )
        else:
            design_freedom = "high"
            additional_notes.append(
                "No palette specified by user: AI granted design freedom to select tailored palette based on domain, user, and density."
            )

    # 9. Next Action & Handoff
    if workflow == "greenfield":
        next_action = {
            "step": "plan_greenfield_ux",
            "target_workflow": "workflows/greenfield-workflow.md",
            "recommended_handoff": "skills/ux-structure",
            "rationale": (
                "Establish product domain understanding, page inventory, and UX flow "
                "before initiating multi-page implementation or visual tokens."
            ),
        }
    elif workflow == "existing-ui":
        if max_level == L2 and preservation["ambition"] == "elevate":
            next_action = {
                "step": "execute_elevated_redesign",
                "target_workflow": "workflows/ambition-levels.md",
                "recommended_handoff": "skills/design-direction",
                "rationale": (
                    "ELEVATE: map the current pages and content, commit to a design direction with signature "
                    "moves, then re-compose layout, hierarchy, surfaces and motion inside the protected shell. "
                    "Brand hues, navigation, routes, content and data stay intact."
                ),
            }
        elif max_level == L3:
            next_action = {
                "step": "execute_authorized_redesign",
                "target_workflow": "workflows/existing-ui-workflow.md",
                "recommended_handoff": "skills/ux-structure",
                "rationale": (
                    "Explicit L3 redesign permission verified. Extract current UX map and establish delta "
                    "with authorized palette/branding modifications."
                ),
            }
        elif max_level == L2:
            next_action = {
                "step": "execute_local_structural_change",
                "target_workflow": "workflows/existing-ui-workflow.md",
                "recommended_handoff": "skills/component-realization",
                "rationale": (
                    "Local structural change authorized. Brand palette remains locked; "
                    "reorganize local component layout with clear UX justification."
                ),
            }
        else:
            next_action = {
                "step": "execute_safe_refinement",
                "target_workflow": "workflows/existing-ui-workflow.md",
                "recommended_handoff": "skills/responsive-interaction" if "responsive" in user_request.lower() else "skills/visual-qa",
                "rationale": (
                    "L1 Safe Refinement active. Preserve all brand colors, typography tokens, "
                    "and page layout identity while polishing alignment, responsive behavior, or accessibility."
                ),
            }
    else:
        next_action = {
            "step": "inspect_repository_context",
            "target_workflow": "workflows/routing.md",
            "recommended_handoff": "inspect_context",
            "rationale": (
                "Ambiguous or missing repository signals (confidence < 0.50). "
                "Perform safe inspection of workspace files before executing modifications."
            ),
        }

    return {
        "workflow": workflow,
        "ui_state": ui_state,
        "confidence": confidence,
        "design_freedom": design_freedom,
        "ambition": preservation["ambition"],
        "allow_motion_library": preservation["ambition"] in ("elevate", "reimagine"),
        "preservation_required": preservation["preservation_required"],
        "protected_properties": preservation["protected_properties"],
        "allowed_change_level": preservation["allowed_change_level"],
        "permissions_detail": preservation["permissions_detail"],
        "precedence_order": preservation["precedence_order"],
        "required_skills": required_skills,
        "required_knowledge": required_knowledge,
        "validation_requirements": validation_reqs,
        "next_action": next_action,
        "notes": additional_notes,
    }


def main(argv: list[str] | None = None) -> int:
    import argparse
    import json
    import sys
    from pathlib import Path

    parser = argparse.ArgumentParser(description="UI Orchestrator entry point")
    parser.add_argument("--request", help="Path to request JSON file")
    parser.add_argument("--prompt", help="Direct text prompt / user request")
    parser.add_argument("--project", default=".", help="Project workspace root")
    parser.add_argument("--intent", help="User intent")
    parser.add_argument("--scope", default="unspecified", help="Requested scope")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")

    args = parser.parse_args(argv)

    if args.request:
        req_data = json.loads(Path(args.request).read_text(encoding="utf-8"))
    elif args.prompt:
        req_data = {
            "user_request": args.prompt,
            "user_intent": args.intent,
            "requested_scope": args.scope,
            "repo_context": {"workspace_root": args.project},
        }
    else:
        if not sys.stdin.isatty():
            req_data = json.loads(sys.stdin.read())
        else:
            parser.error("Must provide either --request <file.json> or --prompt '<text>'")

    result = orchestrate(req_data)
    if args.format == "json":
        print(json.dumps(result, indent=2))
    else:
        print(f"Workflow: {result['workflow']}")
        print(f"UI State: {result['ui_state']} (confidence: {result['confidence']:.2f})")
        print(f"Design Freedom: {result['design_freedom']}")
        print(f"Ambition: {result['ambition']}")
        print(f"Max Change Level: {result['allowed_change_level']['max_level']}")
        print(f"Next Action: {result['next_action']['step']} -> {result['next_action']['target_workflow']}")
    return 0
