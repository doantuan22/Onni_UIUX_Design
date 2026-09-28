"""Component Graph Analyzer: Builds dependency graph and calculates blast radius."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from uiux.engine.repo_intelligence.scanner import RepositorySnapshot

def analyze_component_graph(
    repo_profile: dict[str, Any],
    snapshot: RepositorySnapshot | None = None,
) -> dict[str, Any]:
    """Build a component dependency graph and estimate blast radius."""
    components = repo_profile.get("components", {})
    shared = components.get("shared", [])
    layouts = components.get("layouts", [])
    primitives = components.get("primitives", [])
    page_specific = components.get("page_specific", [])
    
    all_comps = list(set(shared + layouts + primitives + page_specific))
    
    dependencies: dict[str, list[str]] = {c: [] for c in all_comps}
    dependents: dict[str, list[str]] = {c: [] for c in all_comps}
    
    evidence: list[str] = []
    
    if snapshot:
        # Build an index of stem to file path to guess imports
        stem_to_file: dict[str, str] = {}
        for c in all_comps:
            stem = Path(c).stem.lower()
            if stem not in ("index", "page", "layout"):
                stem_to_file[stem] = c
                
        for file in all_comps:
            content = snapshot.read_text(file, max_chars=20_000)
            
            # Find all import paths
            imports = re.findall(r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]', content)
            
            for imp in imports:
                imp_lower = imp.lower()
                imp_stem = imp_lower.split("/")[-1]
                
                target = None
                # Check if it matches a known component
                if imp_stem in stem_to_file:
                    target = stem_to_file[imp_stem]
                else:
                    # Check if it's a relative import matching a component
                    for c in all_comps:
                        if c != file and (imp_stem in c.lower() or Path(c).stem.lower() in imp_lower):
                            # Ensure it's not just a substring match of a generic word
                            if Path(c).stem.lower() not in ("index", "page", "layout"):
                                target = c
                                break
                
                if target and target != file:
                    if target not in dependencies[file]:
                        dependencies[file].append(target)
                    if file not in dependents[target]:
                        dependents[target].append(file)

    # Calculate blast radius
    blast_radius: dict[str, str] = {}
    for c in all_comps:
        dep_count = len(dependents[c])
        if dep_count > 5 or c in layouts or c in primitives:
            blast_radius[c] = "high"
        elif dep_count > 1 or c in shared:
            blast_radius[c] = "medium"
        else:
            blast_radius[c] = "low"
            
    conf = 0.85 if snapshot else 0.3
            
    return {
        "dependencies": dependencies,
        "dependents": dependents,
        "blast_radius": blast_radius,
        "confidence": conf,
        "evidence": evidence or ["Component graph inferred from import statements and file naming conventions."],
    }
