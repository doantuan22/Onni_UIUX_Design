"""Preservation Profile Builder: Constructs baseline preservation invariants and merges granular user permissions."""
from __future__ import annotations

from typing import Any

from uiux.engine.preservation import AMBITION_LEVELS, ELEVATE, REFINE, REIMAGINE, extract_explicit_permissions


def build_preservation_profile(
    existing_ui_profile: dict[str, Any],
    permissions: dict[str, Any] | None = None,
    requested_scope: str = "global",
) -> dict[str, Any]:
    """Construct an evidence-backed baseline preservation profile merging granular permissions."""
    identity = existing_ui_profile.get("identity", {})
    layout = existing_ui_profile.get("layout", {})
    colors = identity.get("colors", {})

    # Merge permissions: ensure granular dictionary
    if permissions and isinstance(permissions, dict):
        merged_perms = {
            "allow_palette_change": bool(permissions.get("allow_palette_change", False)),
            "allow_branding_change": bool(permissions.get("allow_branding_change", False)),
            "allow_layout_change": bool(permissions.get("allow_layout_change", False)),
            "allow_navigation_change": bool(permissions.get("allow_navigation_change", False)),
            "allow_architecture_change": bool(permissions.get("allow_architecture_change", False)),
            "allow_rebuild": bool(permissions.get("allow_rebuild", False)),
            "explicit_l3_granted": bool(permissions.get("explicit_l3_granted", False)),
        }
    else:
        merged_perms = extract_explicit_permissions(user_request="")

    # Ambition: REIMAGINE needs explicit L3; unknown values fall back to REFINE
    ambition = str((permissions or {}).get("ambition", REFINE)).strip().lower()
    if ambition not in AMBITION_LEVELS:
        ambition = REFINE
    if ambition == REIMAGINE and not merged_perms["explicit_l3_granted"]:
        ambition = ELEVATE

    # Determine policies based strictly on granular permissions
    palette_policy = "unlocked" if merged_perms["allow_palette_change"] else "locked"
    branding_policy = "unlocked" if merged_perms["allow_branding_change"] else "locked"
    layout_policy = "editable" if merged_perms["allow_layout_change"] else "protected"
    nav_policy = "editable" if merged_perms["allow_navigation_change"] else "protected"
    ia_policy = "editable" if merged_perms["allow_architecture_change"] else "protected"

    evidence: list[str] = [
        f"Color palette preservation policy: {palette_policy.upper()}",
        f"Brand identity preservation policy: {branding_policy.upper()}",
        f"Overall layout preservation policy: {layout_policy.upper()}",
        f"Navigation model preservation policy: {nav_policy.upper()}",
        f"Information architecture preservation policy: {ia_policy.upper()}",
    ]

    granted_l3_items = [k for k, v in merged_perms.items() if v and k != "explicit_l3_granted"]

    if merged_perms["allow_layout_change"] or ambition == REIMAGINE:
        composition_policy = "editable"
    elif ambition == ELEVATE:
        composition_policy = "evolvable"
    else:
        composition_policy = "protected"
    evidence.append(f"Page composition policy: {composition_policy.upper()} (ambition {ambition.upper()})")

    return {
      "schema_version": 1,
      "ambition": ambition,
      "protected_design": {
        "color_palette": {
          "policy": palette_policy,
          "baseline": {
            "primary": colors.get("primary"),
            "secondary": colors.get("secondary"),
            "accent": colors.get("accent"),
            "neutral": colors.get("neutral", []),
            "surface": colors.get("surface"),
            "background": colors.get("background"),
          },
          "evidence": identity.get("evidence", ["Baseline color palette extracted from existing UI."]),
        },
        "brand_identity": {
          "policy": branding_policy,
          "baseline": {
            "primary_color": colors.get("primary"),
            "visual_language": identity.get("visual_language"),
          },
          "evidence": [f"Brand identity tied to primary color '{colors.get('primary')}' and {identity.get('visual_language')}"],
        },
        "overall_layout_identity": {
          "policy": layout_policy,
          "baseline_patterns": layout.get("container_patterns", []),
          "evidence": layout.get("evidence", ["Baseline layout patterns extracted from existing UI."]),
        },
        "navigation_model": {
          "policy": nav_policy,
          "baseline": layout.get("navigation_structure", {}),
          "evidence": ["Baseline navigation structure preserved."],
        },
        "page_composition": {
          "policy": composition_policy,
          "scope": ["section_layout", "hierarchy", "type_scale", "surfaces", "depth", "motion", "imagery_treatment"],
          "invariants": ["content_inventory", "primary_actions", "routes", "data_bindings", "brand_hues"],
          "evidence": ["Sections may be re-composed under ELEVATE; content, actions, routes and data are kept."],
        },
        "information_architecture": {
          "policy": ia_policy,
          "routes_pages": layout.get("navigation_structure", {}).get("items", []),
          "evidence": ["Baseline information architecture and route inventory preserved."],
        },
      },
      "allowed_changes": {
        "L1": {
          "policy": "allowed",
          "scope": ["spacing", "typography_scale", "responsive", "states", "a11y", "token_alignment"],
        },
        "L2": {
          "policy": "allowed" if ambition == ELEVATE else "justified_only",
          "required_justification": (
              "ELEVATE: justified by the recorded design direction (DESIGN-DIRECTION.md signature moves)."
              if ambition == ELEVATE else
              "Requires clear UX friction or structural defect evidence in change trace."
          ),
        },
        "L3": {
          "policy": "granted" if merged_perms["explicit_l3_granted"] else "explicit_user_permission_only",
          "granted_permissions": granted_l3_items,
        },
      },
      "user_permissions": merged_perms,
      "requested_scope": requested_scope,
      "confidence": existing_ui_profile.get("overall_confidence", 0.90),
      "evidence": evidence,
    }
