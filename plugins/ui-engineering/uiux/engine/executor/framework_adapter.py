"""Framework Adapter.
Ensures edits adhere to framework-specific structural conventions (React, Vue, Next.js, etc).
"""
from typing import Any
from uiux.engine.executor.deviation import build_deviation

class FrameworkAdapter:
    """Validates and enforces framework conventions during implementation."""
    
    def __init__(self, plan_id: str, framework: str):
        self.framework = framework
        self.plan_id = plan_id
        
    def validate_implementation_structure(self, file_path: str, content: str) -> dict[str, Any]:
        """Validate if the edited content conforms to the detected framework conventions."""
        
        # Next.js Server Components constraint check
        if "next" in self.framework.lower():
            if "'use client'" not in content and '"use client"' not in content:
                # If they try to use client hooks in a server component without use client, warn them.
                if any(hook in content for hook in ["useState", "useEffect", "useRef"]):
                    return {
                        "valid": False,
                        "deviation": build_deviation(
                            self.plan_id, "architecture_conflict",
                            "Client hooks used in Server Component without 'use client'.",
                            "Add 'use client' or refactor state.", "framework_conventions"
                        )
                    }
                    
        # Vue Component constraints
        if "vue" in self.framework.lower():
            if not ("<template>" in content and "<script" in content):
                return {
                    "valid": False,
                    "deviation": build_deviation(
                        self.plan_id, "architecture_conflict",
                        "Vue SFC structure missing <template> or <script> tags.",
                        "Restore valid Vue SFC structure.", "framework_conventions"
                    )
                }
                
        return {"valid": True}
