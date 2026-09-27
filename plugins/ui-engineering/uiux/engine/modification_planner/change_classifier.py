"""Change Classifier: Classifies changes into L1, L2, L3 and enforces permission gates.

Enforces:
- L1 (Safe Refinement): Allowed by default
- L2 Justification Gate: Requires concrete, objective evidence why L1 is insufficient.
  Subjective aesthetic reasons ("looks nicer", "trông đẹp hơn") are rejected.
- L3 Permission Gate: Requires explicit user instruction.
  Vague requests ("modernize", "làm đẹp") are strictly rejected.
- Granular permissions: Palette != Layout, Layout != Navigation, Navigation != Framework.
- Ambition ELEVATE (preservation_profile["ambition"] == "elevate"): section re-composition inside the
  protected shell is an authorized L2 change justified by the recorded design direction.
"""
from __future__ import annotations

import re
from typing import Any

from uiux.engine.preservation import (
    L1,
    L2,
    L3,
    extract_explicit_permissions,
    is_vague_enhancement,
)

LEVEL_ORDER = {L1: 1, L2: 2, L3: 3}


def is_valid_l2_justification(justification: dict[str, Any] | None) -> tuple[bool, str]:
    """Validate that an L2 justification provides concrete, non-subjective engineering reasons."""
    if not justification or not isinstance(justification, dict):
        return False, "L2 structural change requires a structured justification."

    required_keys = ("issue", "evidence", "why_L1_is_insufficient", "expected_improvement")
    for k in required_keys:
        val = str(justification.get(k, "")).strip()
        if not val or len(val) < 8:
            return False, f"L2 justification field '{k}' is missing or too brief."

    # Reject purely subjective / aesthetic justifications
    combined_text = " ".join(str(justification.get(k, "")) for k in required_keys).lower()
    subjective_patterns = [
        r"\btrông\s+đẹp\s+hơn\b",
        r"\blooks?\s+nicer\b",
        r"\blooks?\s+better\b",
        r"\bmore\s+aesthetic\b",
        r"\bmodern\s+feel\b",
        r"\bpersonal\s+preference\b",
        r"\bđẹp\s+mắt\b",
        r"\bnhìn\s+thích\s+hơn\b",
    ]
    for pat in subjective_patterns:
        if re.search(pat, combined_text):
            return False, f"Subjective aesthetic justification ('{pat}') is rejected for L2 structural changes."

    return True, "Valid L2 justification provided."


def classify_changes(
    user_goal: str,
    surface: dict[str, Any],
    workflow: str = "existing-ui",
    preservation_profile: dict[str, Any] | None = None,
    explicit_constraints: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify planned changes and enforce L1/L2/L3 permission gates.
    
    Returns:
    {
        "overall_level": "L1" | "L2" | "L3",
        "changes": list[dict],
        "has_unjustified_l2": bool,
        "has_unauthorized_l3": bool,
        "has_palette_violation": bool,
        "violations": list[str],
        "permission_traces": list[dict],
    }
    """
    active_pres = preservation_profile or {}
    granular_perms = active_pres.get("granular_permissions", {})
    palette_perm = granular_perms.get("palette", "locked")
    brand_perm = granular_perms.get("brand", "locked")
    layout_perm = granular_perms.get("layout", "protected")
    nav_perm = granular_perms.get("navigation", "protected")
    ambition = str(active_pres.get("ambition", "refine")).lower()

    explicit_perms = extract_explicit_permissions(user_goal)
    is_vague = is_vague_enhancement(user_goal)
    goal_lower = user_goal.lower()

    changes: list[dict[str, Any]] = []
    violations: list[str] = []
    has_unjustified_l2 = False
    has_unauthorized_l3 = False
    has_palette_violation = False

    from uiux.engine.modification_planner.semantic_parser import (
        parse_action_negation,
        ACTION_PALETTE,
        ACTION_REDESIGN,
        ACTION_STRUCTURE,
        ACTION_BRAND,
        ACTION_NAVIGATION,
    )

    palette_state = parse_action_negation(ACTION_PALETTE, user_goal, explicit_perms)
    redesign_state = parse_action_negation(ACTION_REDESIGN, user_goal, explicit_perms)
    structure_state = parse_action_negation(ACTION_STRUCTURE, user_goal, explicit_perms)
    brand_state = parse_action_negation(ACTION_BRAND, user_goal, explicit_perms)
    nav_state = parse_action_negation(ACTION_NAVIGATION, user_goal, explicit_perms)

    # Check for Palette changes
    keeps_palette = palette_state["prohibited"]
    wants_palette_change = palette_state["requested"] and not palette_state["prohibited"]
    has_palette_perm = palette_state["explicitly_allowed"] or bool(explicit_perms.get("allow_palette_change"))
    if wants_palette_change:
        if palette_perm == "locked" and not has_palette_perm:
            has_palette_violation = True
            has_unauthorized_l3 = True
            violations.append("Global palette change requested but palette is LOCKED under preservation policy.")
            changes.append({
                "id": "change_palette",
                "target": "design_tokens.colors",
                "change_type": "token",
                "level": L3,
                "reason": "Palette modification requested.",
                "evidence": "User prompt mentions color/palette modification.",
                "permission_required": "explicit_palette_permission",
                "justification": None,
                "permission_trace": None,
            })
        else:
            changes.append({
                "id": "change_palette",
                "target": "design_tokens.colors",
                "change_type": "token",
                "level": L3,
                "reason": "Authorized palette modification.",
                "evidence": "Explicit user permission granted for palette.",
                "permission_required": None,
                "justification": None,
                "permission_trace": {
                    "explicit_user_instruction": user_goal,
                    "allowed_property": "palette",
                    "scope": "global",
                    "source": "explicit_prompt",
                },
            })

    # Check for Page Architecture / Full Redesign
    wants_redesign = redesign_state["requested"] and not redesign_state["prohibited"]
    has_redesign_perm = redesign_state["explicitly_allowed"] or bool(
        explicit_perms.get("allow_architecture_change")
        or explicit_perms.get("allow_rebuild")
        or explicit_perms.get("allow_layout_change")
        or explicit_perms.get("explicit_l3_granted")
    )
    if wants_redesign:
        if not has_redesign_perm or is_vague:
            has_unauthorized_l3 = True
            violations.append("Full redesign requested without explicit authorization (vague enhancement does not grant L3).")
            changes.append({
                "id": "change_architecture",
                "target": "page_architecture",
                "change_type": "structure",
                "level": L3,
                "reason": "Full page architecture overhaul.",
                "evidence": "User prompt requests major redesign.",
                "permission_required": "explicit_redesign_permission",
                "justification": None,
                "permission_trace": None,
            })
        else:
            changes.append({
                "id": "change_architecture",
                "target": "page_architecture",
                "change_type": "structure",
                "level": L3,
                "reason": "Authorized page architecture overhaul.",
                "evidence": "Explicit user instruction permitting redesign.",
                "permission_required": None,
                "justification": None,
                "permission_trace": {
                    "explicit_user_instruction": user_goal,
                    "allowed_property": "layout",
                    "scope": "page",
                    "source": "explicit_prompt",
                },
            })

    # Check for Local Structural (L2) changes (e.g. form reorganization, section rearrangement)
    wants_l2 = not structure_state["prohibited"] and any(w in goal_lower for w in ("reorganize", "reorder", "group fields", "restructure section", "sắp xếp lại"))
    if wants_l2:
        # Check if justification was provided or extractable
        has_issue_keyword = any(k in goal_lower for k in ("overflow", "usability", "clutter", "cản trở", "tràn màn hình", "lỗi", "friction"))
        if ambition == "elevate" and not has_issue_keyword:
            changes.append({
                "id": "change_section_recomposition",
                "target": "section_structure",
                "change_type": "layout",
                "level": L2,
                "reason": "ELEVATE: re-compose sections inside the protected shell following the design direction.",
                "evidence": "Ambition ELEVATE resolved by the preservation policy.",
                "permission_required": None,
                "justification": {
                    "issue": "Current composition does not express the product's hierarchy or character.",
                    "evidence": "Ambition ELEVATE plus the recorded DESIGN-DIRECTION.md signature moves.",
                    "why_L1_is_insufficient": "Spacing and token polish cannot change hierarchy, rhythm or composition.",
                    "affected_scope": "page",
                    "expected_improvement": "Clear focal hierarchy and a distinctive, brand-consistent composition.",
                },
                "permission_trace": {
                    "explicit_user_instruction": user_goal,
                    "allowed_property": "page_composition",
                    "scope": "page",
                    "source": "ambition_elevate",
                },
            })
        elif has_issue_keyword:
            changes.append({
                "id": "change_section_reorder",
                "target": "section_structure",
                "change_type": "layout",
                "level": L2,
                "reason": "Reordering fields/sections to resolve usability issue.",
                "evidence": "User identified layout issue causing friction.",
                "permission_required": "L2_justification",
                "justification": {
                    "issue": "Layout arrangement causes user friction or overflow.",
                    "evidence": "Detected layout friction in prompt/repo.",
                    "why_L1_is_insufficient": "Simple CSS spacing adjustment cannot resolve ordering or field hierarchy.",
                    "affected_scope": "section",
                    "expected_improvement": "Streamlined form completion and reduced cognitive load.",
                },
                "permission_trace": None,
            })
        else:
            # L2 without objective engineering justification
            has_unjustified_l2 = True
            violations.append("L2 structural change lacks objective engineering justification (why L1 is insufficient).")
            changes.append({
                "id": "change_section_reorder",
                "target": "section_structure",
                "change_type": "layout",
                "level": L2,
                "reason": "Reorganizing structure without objective justification.",
                "evidence": "No concrete usability issue identified.",
                "permission_required": "L2_justification",
                "justification": None,
                "permission_trace": None,
            })

    # Default / Safe Refinement (L1) changes
    if not changes or any(w in goal_lower for w in ("spacing", "padding", "margin", "align", "responsive", "contrast", "variant", "fix button")):
        changes.append({
            "id": "change_refinement",
            "target": surface.get("components", ["Component"])[0] if surface.get("components") else "Component",
            "change_type": "styling",
            "level": L1,
            "reason": "Refining spacing, typography, alignment, or interactive state.",
            "evidence": "User requests standard refinement.",
            "permission_required": None,
            "justification": None,
            "permission_trace": None,
        })

    # Compute overall level
    max_lvl = L1
    for c in changes:
        if LEVEL_ORDER.get(c["level"], 1) > LEVEL_ORDER.get(max_lvl, 1):
            max_lvl = c["level"]

    return {
        "overall_level": max_lvl,
        "changes": changes,
        "has_unjustified_l2": has_unjustified_l2,
        "has_unauthorized_l3": has_unauthorized_l3,
        "has_palette_violation": has_palette_violation,
        "violations": violations,
    }
