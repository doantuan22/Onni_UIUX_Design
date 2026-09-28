"""Existing UI Profile Builder: Orchestrates all specialized analyzers into a single coherent existing_ui_profile."""
from __future__ import annotations

from typing import Any

from uiux.engine.existing_ui.accessibility import analyze_accessibility
from uiux.engine.existing_ui.component_graph import analyze_component_graph
from uiux.engine.existing_ui.components import analyze_component_consistency
from uiux.engine.existing_ui.design_system import extract_design_system
from uiux.engine.existing_ui.identity import analyze_visual_identity
from uiux.engine.existing_ui.layout import analyze_layout
from uiux.engine.existing_ui.responsive import analyze_responsive
from uiux.engine.existing_ui.understanding_gate import evaluate_understanding_gate
from uiux.engine.existing_ui.ux_flows import analyze_ux_flows
from uiux.engine.existing_ui.visual_analyzer import analyze_visual_ui
from uiux.engine.repo_intelligence.scanner import RepositorySnapshot


def build_existing_ui_profile(
    repo_profile: dict[str, Any],
    snapshot: RepositorySnapshot | None = None,
) -> dict[str, Any]:
    """Execute all Existing UI sub-analyzers and return a machine-readable existing_ui_profile."""
    warnings: list[str] = []
    unsupported_analysis: list[str] = []
    analyzer_failures: list[str] = []

    # 1. Visual Identity Analysis
    try:
        identity_data = analyze_visual_identity(repo_profile, snapshot)
    except Exception as exc:
        identity_data = {
            "colors": {"primary": None, "secondary": None, "accent": None, "neutral": [], "background": None, "surface": None, "text": None, "semantic": {}},
            "typography": {"font_family_base": None, "font_family_heading": None, "font_family_mono": None, "scale": [], "weights": []},
            "radius": {"default": None, "scale": []},
            "shadows": {"scale": []},
            "density": "unknown",
            "visual_language": "standard",
            "confidence": 0.0,
            "evidence": [f"VisualIdentityAnalyzer failed: {exc}"],
        }
        analyzer_failures.append(f"IdentityAnalyzer: {exc}")

    # 2. Layout Analysis
    try:
        layout_data = analyze_layout(repo_profile, snapshot)
    except Exception as exc:
        layout_data = {
            "container_patterns": [], "grid_patterns": [], "spacing_rhythm": None,
            "section_hierarchy": [], "navigation_structure": {"type": "unknown", "placement": None, "items": []},
            "responsive_breakpoints": [], "global_structure": {}, "local_structure": {},
            "confidence": 0.0, "evidence": [f"LayoutAnalyzer failed: {exc}"],
        }
        analyzer_failures.append(f"LayoutAnalyzer: {exc}")

    # 3. Component Consistency Analysis
    try:
        comp_data = analyze_component_consistency(repo_profile, snapshot)
        comp_graph = analyze_component_graph(repo_profile, snapshot)
        comp_data["component_graph"] = {
            "dependencies": comp_graph["dependencies"],
            "dependents": comp_graph["dependents"],
            "blast_radius": comp_graph["blast_radius"]
        }
    except Exception as exc:
        comp_data = {
            "variants": {}, "consistency": "unknown", "shared_patterns": [],
            "anomalies": [], "canonical_patterns": {}, "duplicate_signals": [],
            "component_graph": {},
            "severity": "info", "confidence": 0.0, "evidence": [f"ComponentAnalyzer failed: {exc}"],
        }
        analyzer_failures.append(f"ComponentAnalyzer: {exc}")

    # 4. UX Flow Analysis
    try:
        ux_data = analyze_ux_flows(repo_profile, snapshot)
    except Exception as exc:
        ux_data = {
            "flows": [], "states": [], "missing_states": [], "friction_signals": [],
            "confidence": 0.0, "evidence": [f"UXFlowAnalyzer failed: {exc}"],
        }
        analyzer_failures.append(f"UXFlowAnalyzer: {exc}")

    # 5. Responsive Analysis
    try:
        responsive_data = analyze_responsive(repo_profile, snapshot)
    except Exception as exc:
        responsive_data = {
            "breakpoints": [], "layout_adaptations": [], "possible_overflow": [],
            "touch_target_signals": [], "mobile_navigation": None, "content_priority": [],
            "risks": [], "severity": "info", "confidence": 0.0, "evidence": [f"ResponsiveAnalyzer failed: {exc}"],
        }
        analyzer_failures.append(f"ResponsiveAnalyzer: {exc}")

    # 6. Accessibility Analysis
    try:
        accessibility_data = analyze_accessibility(repo_profile, snapshot)
    except Exception as exc:
        accessibility_data = {
            "labels": [], "semantics": [], "focus": [], "keyboard": [], "contrast_signals": [],
            "missing_form_labels": [], "heading_hierarchy_issues": [],
            "confidence": 0.0, "evidence": [f"AccessibilityAnalyzer failed: {exc}"],
        }
        analyzer_failures.append(f"AccessibilityAnalyzer: {exc}")

    # 7. Design System Extraction
    try:
        design_system_data = extract_design_system(repo_profile, identity_data, comp_data)
    except Exception as exc:
        design_system_data = {
            "tokens": {}, "component_conventions": {}, "typography_scale": [],
            "spacing_scale": [], "radius_scale": [], "semantic_colors": {},
            "maturity": "unknown", "confidence": 0.0, "evidence": [f"DesignSystemExtractor failed: {exc}"],
        }
        analyzer_failures.append(f"DesignSystemExtractor: {exc}")

    # 8. Visual UI Analysis
    try:
        visual_data = analyze_visual_ui(repo_profile, layout_data, identity_data, snapshot)
    except Exception as exc:
        visual_data = {
            "measured": {}, "inferred": {}, "model_interpretable_evidence": [],
            "confidence": 0.0, "evidence": [f"VisualUIAnalyzer failed: {exc}"],
        }
        analyzer_failures.append(f"VisualUIAnalyzer: {exc}")

    # Monorepo notice
    if repo_profile.get("repository_signals", {}).get("is_monorepo"):
        warnings.append("Monorepo detected: Existing UI profile scoped to primary application context.")

    confidences = [
        identity_data["confidence"],
        layout_data["confidence"],
        comp_data["confidence"],
        ux_data["confidence"],
        responsive_data["confidence"],
        accessibility_data["confidence"],
        design_system_data["confidence"],
        visual_data.get("confidence", 0.0),
    ]
    overall_confidence = round(sum(confidences) / len(confidences), 2)

    result = {
        "schema_version": 1,
        "identity": identity_data,
        "layout": layout_data,
        "components": comp_data,
        "ux": ux_data,
        "responsive": responsive_data,
        "accessibility": accessibility_data,
        "design_system": design_system_data,
        "visual_analysis": visual_data,
        "diagnostics": {
            "warnings": warnings,
            "unsupported_analysis": unsupported_analysis,
            "analyzer_failures": analyzer_failures,
        },
        "next_actions": [
            "Pass existing_ui_profile to orchestrate_ui, build_knowledge_plan, or plan_modification.",
        ],
        "overall_confidence": overall_confidence,
    }

    # 9. Understanding Gate
    try:
        gate_data = evaluate_understanding_gate(result, repo_profile)
        result["understanding_gate"] = gate_data
    except Exception as exc:
        result["understanding_gate"] = {
            "status": "BLOCKED", "missing_context": ["understanding_gate_failed"],
            "required_next_actions": [f"Fix Understanding Gate: {exc}"],
            "confidence": 0.0
        }
        analyzer_failures.append(f"UnderstandingGate: {exc}")

    return result
