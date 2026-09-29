"""Recipe Adapter.
Adapts standardized UI recipes (from P1) to the existing UI context (styling system, tokens, brand).
"""
import re
from typing import Any

class RecipeAdapter:
    """Adapts a canonical recipe string to the host repository's design system."""
    
    def __init__(self, plan: dict[str, Any]):
        self.plan = plan
        
    def adapt_recipe(self, recipe_content: str, token_map: dict[str, str]) -> str:
        """Replace canonical tokens in a recipe with the repository's active tokens.
        
        Args:
            recipe_content: The raw HTML/React recipe string (e.g. using generic classes like 'bg-brand-500').
            token_map: Mapping of canonical semantic names to repository specific ones.
                       e.g. {"brand": "primary", "neutral": "slate"}
        """
        adapted = recipe_content
        
        # Naive implementation for Tailwind-like classes:
        for canonical, actual in token_map.items():
            if canonical != actual:
                # Replace exact class segment. 
                # e.g. bg-brand-500 -> bg-primary-500
                pattern = rf"\b({canonical})\b"
                adapted = re.sub(pattern, actual, adapted)
                
        return adapted
        
    def verify_recipe_compatibility(self, recipe_metadata: dict[str, Any]) -> dict[str, Any]:
        """Verify the recipe matches the plan's framework and styling system."""
        repo_fw = self.plan.get("repository", {}).get("framework", "").lower()
        recipe_fw = recipe_metadata.get("framework", "").lower()
        
        if recipe_fw and repo_fw and recipe_fw != "generic" and repo_fw not in recipe_fw and recipe_fw not in repo_fw:
            return {
                "compatible": False,
                "reason": f"Recipe framework '{recipe_fw}' does not match repo framework '{repo_fw}'."
            }
            
        return {"compatible": True}
