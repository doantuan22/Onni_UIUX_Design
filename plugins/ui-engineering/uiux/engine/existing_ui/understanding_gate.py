"""Understanding Gate: Ensures the agent has sufficient context before proceeding to THINK."""
from __future__ import annotations

from typing import Any


def evaluate_understanding_gate(
    existing_ui_profile: dict[str, Any],
    repo_profile: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate if the gathered UI context is sufficient to proceed with design modifications."""
    
    missing_context: list[str] = []
    required_next_actions: list[str] = []
    
    # 1. Check Framework & Styling
    framework = repo_profile.get("framework", {}).get("name", "unknown")
    if framework == "unknown":
        missing_context.append("framework")
        required_next_actions.append("Manually inspect repository to determine frontend framework.")
        
    styling = repo_profile.get("styling_system", {}).get("primary")
    if not styling:
        missing_context.append("styling_system")
        required_next_actions.append("Determine CSS/Styling library in use.")
        
    # 2. Check Layout & Architecture
    layout = existing_ui_profile.get("layout", {})
    if not layout.get("global_structure", {}).get("app_shell") and not layout.get("navigation_structure"):
        missing_context.append("layout_structure")
        required_next_actions.append("Identify global application shell and navigation structure.")
        
    # 3. Check Components
    components = existing_ui_profile.get("components", {})
    if not components.get("component_graph", {}).get("dependencies") and not repo_profile.get("components", {}).get("total_count", 0):
        missing_context.append("relevant_components")
        required_next_actions.append("Map component inventory and dependencies.")
        
    # 4. Check Identity & Palette
    identity = existing_ui_profile.get("identity", {})
    if not identity.get("colors", {}).get("primary"):
        missing_context.append("current_palette")
        required_next_actions.append("Extract design tokens and brand colors.")
        
    # 5. Check UX Flows
    ux = existing_ui_profile.get("ux", {})
    if not ux.get("flows"):
        missing_context.append("navigation_flow")
        required_next_actions.append("Identify primary user flows from routes.")

    # 6. Overall Confidence
    confidence = existing_ui_profile.get("overall_confidence", 0.0)
    if confidence < 0.4:
        missing_context.append("low_overall_confidence")
        required_next_actions.append("Run map_ui_structure and targeted evidence collection to boost confidence.")

    # Evaluate Status
    if len(missing_context) == 0 and confidence >= 0.7:
        status = "PASS"
    elif len(missing_context) <= 3 and confidence >= 0.4:
        status = "PARTIAL"
    else:
        status = "BLOCKED"
        
    return {
        "status": status,
        "missing_context": missing_context,
        "required_next_actions": required_next_actions,
        "confidence": confidence,
    }
