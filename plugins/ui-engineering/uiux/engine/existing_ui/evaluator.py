"""Preservation Evaluator / Guard: Compares proposed changes against baseline preservation invariants."""
from __future__ import annotations

from typing import Any


class PreservationEvaluator:
    """Evaluates proposed UI modifications against the baseline preservation profile."""

    def evaluate(
        self,
        baseline_profile: dict[str, Any],
        proposed_changes: dict[str, Any],
        permissions: dict[str, Any] | None = None,
        requested_scope: str | None = None,
    ) -> dict[str, Any]:
        """Perform deterministic audit of proposed changes against preservation rules."""
        protected = baseline_profile.get("protected_design", {})
        allowed = baseline_profile.get("allowed_changes", {})
        baseline_perms = baseline_profile.get("user_permissions", {})
        merged_perms = permissions or baseline_perms

        scope = requested_scope or baseline_profile.get("requested_scope", "global")

        violations: list[dict[str, str]] = []
        warnings: list[str] = []
        checked_rules: list[str] = [
            "RULE_1: PALETTE_PRESERVATION",
            "RULE_2: BRAND_PRESERVATION",
            "RULE_3: LAYOUT_PRESERVATION",
            "RULE_4: NAVIGATION_PRESERVATION",
            "RULE_5: ARCHITECTURE_PRESERVATION",
            "RULE_6: SCOPE_CONFINEMENT",
            "RULE_7: L2_JUSTIFICATION_TRACE",
            "RULE_8: L3_EXPLICIT_PERMISSION_TRACE",
            "RULE_9: CONTENT_PRESERVATION",
        ]
        ambition = str(baseline_profile.get("ambition", "refine")).lower()

        # 1. Palette Preservation
        palette_policy = protected.get("color_palette", {}).get("policy", "locked")
        palette_changes = proposed_changes.get("palette_changes")
        is_a11y_tweak = bool(proposed_changes.get("is_accessibility_contrast_adjustment", False))

        if palette_changes:
            old_val = palette_changes.get("old", "baseline")
            new_val = palette_changes.get("new", "modified")
            if is_a11y_tweak:
                warnings.append(
                    f"Minimal accessibility contrast adjustment applied ('{old_val}' -> '{new_val}'); "
                    "primary color identity and brand recognition preserved."
                )
            elif palette_policy == "locked" and not merged_perms.get("allow_palette_change"):
                violations.append({
                    "rule": "PALETTE_PRESERVATION",
                    "severity": "critical",
                    "affected_area": "color_palette",
                    "evidence": f"Unauthorized color palette shift from '{old_val}' to '{new_val}' while palette is LOCKED.",
                    "required_permission": "allow_palette_change",
                    "actual_permission": "denied",
                })

        # 2. Brand Preservation
        brand_policy = protected.get("brand_identity", {}).get("policy", "locked")
        brand_changes = proposed_changes.get("brand_changes")
        if brand_changes and brand_policy == "locked" and not merged_perms.get("allow_branding_change"):
            violations.append({
                "rule": "BRAND_PRESERVATION",
                "severity": "critical",
                "affected_area": "brand_identity",
                "evidence": "Brand identity token, logo, or aesthetic identity modified without explicit permission.",
                "required_permission": "allow_branding_change",
                "actual_permission": "denied",
            })

        # 3. Layout Preservation
        layout_policy = protected.get("overall_layout_identity", {}).get("policy", "protected")
        layout_changes = proposed_changes.get("layout_changes", {})
        if layout_changes.get("is_global_rewrite") and layout_policy == "protected" and not merged_perms.get("allow_layout_change"):
            violations.append({
                "rule": "LAYOUT_PRESERVATION",
                "severity": "high",
                "affected_area": "overall_layout_identity",
                "evidence": "Global layout shell rewrite attempted while layout identity is PROTECTED.",
                "required_permission": "allow_layout_change",
                "actual_permission": "denied",
            })

        # 4. Navigation Model Preservation
        nav_policy = protected.get("navigation_model", {}).get("policy", "protected")
        nav_changes = proposed_changes.get("navigation_changes", {})
        if nav_changes and nav_policy == "protected" and not merged_perms.get("allow_navigation_change"):
            mod_routes = nav_changes.get("routes_modified", []) or nav_changes.get("routes_removed", [])
            violations.append({
                "rule": "NAVIGATION_PRESERVATION",
                "severity": "high",
                "affected_area": "navigation_model",
                "evidence": f"Navigation routes altered outside plan ({', '.join(mod_routes) or 'routes modified'}) while navigation model is PROTECTED.",
                "required_permission": "allow_navigation_change",
                "actual_permission": "denied",
            })

        # 5. Information Architecture Preservation
        ia_policy = protected.get("information_architecture", {}).get("policy", "protected")
        ia_changes = proposed_changes.get("architecture_changes", {})
        if ia_changes and ia_policy == "protected" and not merged_perms.get("allow_architecture_change"):
            violations.append({
                "rule": "ARCHITECTURE_PRESERVATION",
                "severity": "critical",
                "affected_area": "information_architecture",
                "evidence": "Information architecture and page hierarchy modified without explicit permission.",
                "required_permission": "allow_architecture_change",
                "actual_permission": "denied",
            })

        # 6. Scope Confinement
        if scope in ("component", "section"):
            if layout_changes.get("is_global_rewrite") or ia_changes or nav_changes:
                violations.append({
                    "rule": "SCOPE_CONFINEMENT",
                    "severity": "critical",
                    "affected_area": "requested_scope",
                    "evidence": f"Requested scope is strictly '{scope}'; global layout or architectural mutation is forbidden.",
                    "required_permission": f"scope:{scope}",
                    "actual_permission": "exceeded",
                })

        # 7. L2 Change Justification
        level = proposed_changes.get("level")
        is_l2 = level == "L2" or proposed_changes.get("has_l2_change", False)
        if is_l2:
            reason = proposed_changes.get("change_reason")
            direction = proposed_changes.get("design_direction")
            if ambition == "elevate" and not reason and direction:
                reason = {"issue": f"ELEVATE design direction: {direction}"}
            if not reason or not isinstance(reason, dict) or not (reason.get("issue") or reason.get("why_local_structure_change_needed")):
                violations.append({
                    "rule": "L2_JUSTIFICATION_TRACE",
                    "severity": "medium",
                    "affected_area": "L2_change_budget",
                    "evidence": "L2 local structural change lacks required justification reason trace.",
                    "required_permission": "justified_only",
                    "actual_permission": "unjustified",
                })
            else:
                warnings.append(f"L2 change justified by trace: {reason.get('issue') or reason.get('why_local_structure_change_needed')}")

        # 8. L3 Explicit Permission Trace
        is_l3 = level == "L3" or proposed_changes.get("has_l3_change", False) or layout_changes.get("is_full_rebuild", False)
        if is_l3:
            l3_policy = allowed.get("L3", {}).get("policy")
            has_l3_perm = l3_policy == "granted" or merged_perms.get("explicit_l3_granted", False)
            if not has_l3_perm:
                violations.append({
                    "rule": "L3_EXPLICIT_PERMISSION_TRACE",
                    "severity": "critical",
                    "affected_area": "L3_change_budget",
                    "evidence": "L3 major redesign requested but explicit user permission is missing.",
                    "required_permission": "explicit_user_permission_only",
                    "actual_permission": "denied",
                })
            else:
                trace = proposed_changes.get("permission_trace", {})
                warnings.append(f"L3 major redesign verified with explicit permission: {trace.get('user_instruction', 'Granted')}")

        # 9. Content Preservation: re-composition keeps copy, actions and data (ELEVATE never deletes content)
        content_changes = proposed_changes.get("content_changes", {}) or {}
        removed = list(content_changes.get("removed", []) or []) + list(content_changes.get("actions_removed", []) or [])
        if removed and not (merged_perms.get("allow_architecture_change") or merged_perms.get("allow_rebuild")):
            violations.append({
                "rule": "CONTENT_PRESERVATION",
                "severity": "high",
                "affected_area": "content_inventory",
                "evidence": f"Content or primary actions removed during a visual change: {', '.join(map(str, removed))}.",
                "required_permission": "allow_architecture_change",
                "actual_permission": "denied",
            })

        # Compute status
        has_critical = any(v["severity"] in ("critical", "high") for v in violations)
        has_medium = any(v["severity"] == "medium" for v in violations)

        if has_critical:
            status = "fail"
            summary = f"Preservation check FAILED with {len(violations)} rule violation(s)."
        elif has_medium:
            status = "warn"
            summary = f"Preservation check passed with WARNINGS: {len(violations)} non-critical issue(s) detected."
        else:
            status = "pass"
            summary = "Preservation check PASSED. All baseline invariants, change budgets, and permissions respected."

        return {
            "schema_version": 1,
            "status": status,
            "violations": violations,
            "warnings": warnings,
            "checked_rules": checked_rules,
            "summary": summary,
        }
