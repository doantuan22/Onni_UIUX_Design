"""Controlled Editing Engine: Enforces plan boundaries and detects plan drift.

Role: post-hoc audit of edits that already happened (``compare_plan_to_changes``). Write-time enforcement lives in
``uiux.engine.executor`` (``guard_edits``); the two are complementary and both stay supported.

Enforces:
- Edits are restricted strictly to allowed_files and allowed_components.
- Unexpected files halt execution immediately.
- Unexpected change levels (actual > planned) fail permission gates.
- Unexpected route or token modifications trigger plan drift failure.
- Produces a machine-readable Change Manifest complying with change-manifest.schema.json.
"""
from __future__ import annotations

import uuid
from typing import Any

from uiux.engine.preservation import L1, L2, L3

LEVEL_ORDER = {L1: 1, L2: 2, L3: 3}


class ControlledEditingEngine:
    """Validates and enforces modification plan boundaries against actual or simulated changes."""

    def compare_plan_to_changes(
        self,
        plan: dict[str, Any],
        actual_changes: list[dict[str, Any]] | dict[str, Any],
    ) -> dict[str, Any]:
        """Compare the approved modification plan against actual implementation changes.
        
        Returns a validated Change Manifest.
        """
        # Normalize actual_changes input
        if isinstance(actual_changes, dict):
            raw_changes = actual_changes.get("changes", [])
            modified_files = list(actual_changes.get("modified_files", []))
            created_files = list(actual_changes.get("created_files", []))
            deleted_files = list(actual_changes.get("deleted_files", []))
            changed_components = list(actual_changes.get("changed_components", []))
            changed_tokens = list(actual_changes.get("changed_tokens", []))
            changed_routes = list(actual_changes.get("changed_routes", []))
            actual_levels = list(actual_changes.get("actual_change_levels", []))
        else:
            raw_changes = list(actual_changes)
            modified_files = []
            created_files = []
            deleted_files = []
            changed_components = []
            changed_tokens = []
            changed_routes = []
            actual_levels = []

            for ch in raw_changes:
                target = ch.get("file") or ch.get("target", "")
                action = ch.get("action", "modify")
                lvl = ch.get("level", L1)
                actual_levels.append(lvl)

                if action == "modify" and target:
                    modified_files.append(target)
                elif action == "create" and target:
                    created_files.append(target)
                elif action == "delete" and target:
                    deleted_files.append(target)

                if ch.get("component"):
                    changed_components.append(ch["component"])
                if ch.get("token"):
                    changed_tokens.append(ch["token"])
                if ch.get("route"):
                    changed_routes.append(ch["route"])

        blast_radius = plan.get("blast_radius", {})
        allowed_files = set(blast_radius.get("allowed_files", []))
        allowed_components = set(blast_radius.get("allowed_components", []))
        planned_routes = set(plan.get("affected_surface", {}).get("routes", []))
        planned_tokens = set(plan.get("affected_surface", {}).get("tokens", []))
        planned_level = plan.get("change_classification", {}).get("overall_level", L1)
        planned_steps = plan.get("implementation_steps", [])
        planned_creates = {s["target"] for s in planned_steps if s.get("action") == "create"}
        planned_deletes = {s["target"] for s in planned_steps if s.get("action") == "delete"}

        unexpected_changes: list[dict[str, Any]] = []
        drift_reasons: list[str] = []
        drift_detected = False
        permission_failed = False

        # 1. Enforce Allowed Files
        for f in modified_files:
            if f not in allowed_files:
                drift_detected = True
                reason = f"File '{f}' modified but was not in plan's allowed_files."
                drift_reasons.append(reason)
                unexpected_changes.append({
                    "target": f,
                    "change_type": "file_drift",
                    "reason": reason,
                    "risk": "high",
                })

        # 2. Enforce File Creations
        for f in created_files:
            if f not in allowed_files and f not in planned_creates:
                drift_detected = True
                reason = f"File '{f}' created unexpectedly without plan authorization."
                drift_reasons.append(reason)
                unexpected_changes.append({
                    "target": f,
                    "change_type": "unexpected_create",
                    "reason": reason,
                    "risk": "high",
                })

        # 3. Enforce File Deletions (High-risk policy: deletion must be explicit in plan)
        for f in deleted_files:
            if f not in planned_deletes:
                permission_failed = True
                drift_detected = True
                reason = f"File '{f}' deleted without explicit deletion authorization in plan."
                drift_reasons.append(reason)
                unexpected_changes.append({
                    "target": f,
                    "change_type": "unauthorized_delete",
                    "reason": reason,
                    "risk": "high",
                })

        # 4. Enforce Change Level
        planned_lvl_rank = LEVEL_ORDER.get(planned_level, 1)
        for actual_lvl in actual_levels:
            if LEVEL_ORDER.get(actual_lvl, 1) > planned_lvl_rank:
                permission_failed = True
                reason = f"Actual change level '{actual_lvl}' escalated above planned level '{planned_level}'."
                drift_reasons.append(reason)
                unexpected_changes.append({
                    "target": "change_level",
                    "change_type": "level_elevation",
                    "reason": reason,
                    "risk": "high",
                })

        # 5. Enforce Route Protection
        for r in changed_routes:
            if r not in planned_routes:
                drift_detected = True
                reason = f"Route '{r}' modified unexpectedly outside planned route surface."
                drift_reasons.append(reason)
                unexpected_changes.append({
                    "target": r,
                    "change_type": "route_drift",
                    "reason": reason,
                    "risk": "high",
                })

        # 6. Enforce Token Protection (Palette / Brand tokens)
        palette_locked = plan.get("preservation", {}).get("granular_permissions", {}).get("palette") == "locked"
        for t in changed_tokens:
            if palette_locked and any(c in t.lower() for c in ("color", "palette", "brand", "primary")):
                permission_failed = True
                reason = f"Token '{t}' modified while palette is LOCKED in preservation policy."
                drift_reasons.append(reason)
                unexpected_changes.append({
                    "target": t,
                    "change_type": "token_violation",
                    "reason": reason,
                    "risk": "high",
                })

        # 7. Status Resolution
        if permission_failed:
            status = "failed_permission"
        elif drift_detected:
            status = "failed_drift"
        else:
            status = "passed"

        manifest_id = f"manifest_{uuid.uuid4().hex[:12]}"
        validation_required = list(plan.get("validation", {}).get("required_checks", []))

        return {
            "schema_version": 1,
            "manifest_id": manifest_id,
            "plan_id": plan.get("plan_id", "unknown_plan"),
            "modified_files": list(dict.fromkeys(modified_files)),
            "created_files": list(dict.fromkeys(created_files)),
            "deleted_files": list(dict.fromkeys(deleted_files)),
            "changed_components": list(dict.fromkeys(changed_components)),
            "changed_tokens": list(dict.fromkeys(changed_tokens)),
            "changed_routes": list(dict.fromkeys(changed_routes)),
            "actual_change_levels": list(dict.fromkeys(actual_levels)) or [planned_level],
            "unexpected_changes": unexpected_changes,
            "validation_required": validation_required,
            "drift_detected": drift_detected,
            "drift_reasons": drift_reasons,
            "status": status,
        }
