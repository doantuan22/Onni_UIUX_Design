"""Scope Lock Engine.
Actively enforces boundaries during implementation.
"""
from typing import Any

class ScopeLock:
    """Provides write-time boundaries based on the approved plan."""
    
    def __init__(self, plan: dict[str, Any]):
        self.plan = plan
        # We can extract allowed files from either affected_surface or impact depending on schema version
        impact = plan.get("impact", {})
        surface = plan.get("affected_surface", {})
        
        self.allowed_files = set(impact.get("affected_files", []) + surface.get("allowed_files", []))
        self.allowed_components = set(impact.get("affected_components", []) + surface.get("allowed_components", []))
        
        preservation = plan.get("preservation", {})
        self.locked_properties = set(preservation.get("locked", []))
        
    @staticmethod
    def _norm(path: str) -> str:
        norm = path.replace("\\", "/").strip()
        while norm.startswith("./"):
            norm = norm[2:]
        return norm.lstrip("/")

    def is_file_allowed(self, file_path: str) -> bool:
        """Check if file modification is permitted (exact path, or one path is a suffix of the other)."""
        target = self._norm(file_path)
        if not target:
            return False
        for allowed in self.allowed_files:
            allowed = self._norm(allowed)
            if allowed and (allowed == target or target.endswith("/" + allowed) or allowed.endswith("/" + target)):
                return True
        return False

    def is_component_allowed(self, component_name: str) -> bool:
        """Check if component modification is permitted."""
        return component_name in self.allowed_components
        
    def check_preservation_violation(self, text_change: str) -> bool:
        """Heuristic to detect if a locked property is being modified (e.g. palette)."""
        if "palette" in self.locked_properties or "brand" in self.locked_properties:
            # If changing global color tokens, block it.
            # Very simplistic heuristic for demonstration.
            if "--color-" in text_change or "theme.colors" in text_change:
                return True
        return False
