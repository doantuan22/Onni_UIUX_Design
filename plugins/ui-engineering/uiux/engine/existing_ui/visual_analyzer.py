"""Visual UI Analyzer: Translates layout and design system signals into structured visual evidence."""
from __future__ import annotations

from typing import Any

from uiux.engine.repo_intelligence.scanner import RepositorySnapshot


def analyze_visual_ui(
    repo_profile: dict[str, Any],
    layout_profile: dict[str, Any],
    identity_profile: dict[str, Any],
    snapshot: RepositorySnapshot | None = None,
) -> dict[str, Any]:
    """Analyze visual hierarchy, density, and alignment based on measurable structure."""
    
    measured: dict[str, Any] = {}
    inferred: dict[str, Any] = {}
    model_interpretable_evidence: list[str] = []
    
    # Extract inputs
    density_token = identity_profile.get("density", "normal")
    typography = identity_profile.get("typography", {})
    grid_patterns = layout_profile.get("grid_patterns", [])
    container_patterns = layout_profile.get("container_patterns", [])
    
    # 1. MEASURED
    measured["color_dominance"] = {
        "primary": identity_profile.get("colors", {}).get("primary"),
        "background": identity_profile.get("colors", {}).get("background"),
    }
    
    type_scale = typography.get("scale", [])
    measured["typographic_hierarchy"] = {
        "scale_steps": len(type_scale),
        "has_display_fonts": bool(typography.get("font_family_heading")),
    }
    
    measured["spacing_rhythm"] = layout_profile.get("spacing_rhythm")
    
    # 2. INFERRED
    inferred["visual_hierarchy"] = "clear" if len(type_scale) >= 4 else "flat"
    
    if "css-grid" in grid_patterns or "flexbox-layout" in grid_patterns:
        inferred["alignment"] = "structured_grid"
    else:
        inferred["alignment"] = "flow_based"
        
    inferred["whitespace_density"] = density_token
    
    inferred["surface_hierarchy"] = "layered" if identity_profile.get("shadows", {}).get("scale") else "flat"
    
    if "standard-card-surface" in layout_profile.get("local_structure", {}).get("card_patterns", []):
        inferred["grouping"] = "card_based"
    else:
        inferred["grouping"] = "whitespace_separated"
        
    inferred["contrast_signals"] = "unknown_without_runtime"
    
    # 3. MODEL-INTERPRETABLE EVIDENCE
    model_interpretable_evidence.append(
        f"Visual density is inferred as '{density_token}' based on token scale and component count."
    )
    if inferred["surface_hierarchy"] == "layered":
        model_interpretable_evidence.append("UI employs elevation and shadows to distinguish surfaces.")
    if inferred["grouping"] == "card_based":
        model_interpretable_evidence.append("Content grouping relies on explicit card boundaries rather than just whitespace.")
    
    conf = 0.6 if snapshot else 0.3
    
    return {
        "measured": measured,
        "inferred": inferred,
        "model_interpretable_evidence": model_interpretable_evidence,
        "confidence": conf,
    }
