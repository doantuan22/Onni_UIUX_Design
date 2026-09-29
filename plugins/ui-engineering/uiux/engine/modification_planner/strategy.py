"""Design Strategy Generator.
Maps Diagnosed Problems + Knowledge -> Implementation Strategy.
"""
from typing import Any
from uiux.engine.modification_planner.schemas import DesignStrategy, ProblemDiagnosis

def build_design_strategy(
    diagnosis: ProblemDiagnosis,
    knowledge_plan: dict[str, Any],
    ui_context: dict[str, Any]
) -> DesignStrategy:
    """Generate Design Strategy tracing back to knowledge and diagnosis."""
    strategy: DesignStrategy = {
        "knowledge_used": []
    }
    
    selected_knowledge = knowledge_plan.get("selected_knowledge", [])
    selected_knowledge_ids = [k.get("id", "") for k in selected_knowledge if isinstance(k, dict)]
    
    # Analyze layout strategy based on diagnosis
    has_responsive_issue = any(iss["category"] == "RESPONSIVE" for iss in diagnosis["issues"])
    if has_responsive_issue:
        strategy["responsive_strategy"] = "Adopt flexible flex/grid structures. Ensure touch targets are >= 44px."
        strategy["knowledge_used"].append({
            "knowledge_id": "runtime.responsive_viewport" if "runtime.responsive_viewport" in selected_knowledge_ids else "universal_fallback",
            "reason": "Responsive diagnosis requires strict viewport constraint management."
        })
        
    has_ux_issue = any(iss["category"] == "UX" for iss in diagnosis["issues"])
    if has_ux_issue:
        strategy["interaction_strategy"] = "Provide clear immediate feedback, sticky primary CTA, and persistent contextual state."
        strategy["layout_strategy"] = "Re-compose primary sections for progressive disclosure."
        
        # Trace back to domain knowledge if available
        domain_packs = knowledge_plan.get("selected_packs", {}).get("domain", [])
        if domain_packs:
            domain_id = domain_packs[0].get("id")
            strategy["knowledge_used"].append({
                "knowledge_id": domain_id,
                "reason": "Applying domain-specific UX patterns to solve flow friction."
            })
            
    has_visual_issue = any(iss["category"] == "VISUAL" for iss in diagnosis["issues"])
    if has_visual_issue:
        strategy["hierarchy_strategy"] = "Establish clear L1/L2/L3 visual hierarchy using typography scales and consistent spacing tokens."
        framework_packs = knowledge_plan.get("selected_packs", {}).get("framework", [])
        if framework_packs:
            fw_id = framework_packs[0].get("id")
            strategy["knowledge_used"].append({
                "knowledge_id": fw_id,
                "reason": "Using framework-specific styling primitives to enforce hierarchy without breaking tokens."
            })
            
    has_a11y_issue = any(iss["category"] == "ACCESSIBILITY" for iss in diagnosis["issues"])
    if has_a11y_issue:
        strategy["accessibility_strategy"] = "Enforce WCAG AA contrast, aria-labels for icon-only buttons, and visible focus rings."
        strategy["knowledge_used"].append({
            "knowledge_id": "skill.visual_qa",
            "reason": "Accessibility diagnosis mandates focus and contrast enforcement."
        })

    return strategy
