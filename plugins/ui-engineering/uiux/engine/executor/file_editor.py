"""Controlled File Editor.
Safe, trackable file operations strictly bounded by ScopeLock.
"""
import time
from typing import Any
from uiux.engine.executor.schemas import ChangeLedgerEntry
from uiux.engine.executor.scope_lock import ScopeLock
from uiux.engine.executor.deviation import build_deviation
from uiux.engine.executor.framework_adapter import FrameworkAdapter

class FileEditor:
    """Provides safe edit operations bounded by plan scope."""
    
    def __init__(self, scope_lock: ScopeLock, plan_id: str, framework: str):
        self.scope_lock = scope_lock
        self.plan_id = plan_id
        self.framework_adapter = FrameworkAdapter(plan_id, framework)
        self.ledger: list[ChangeLedgerEntry] = []
        self.deviations: list[dict[str, Any]] = []
        self.rejected_chunks: set[str] = set()
        
    def _guard_business_logic(self, content: str) -> bool:
        """Heuristic guard against backend/business logic edits."""
        bad_keywords = ["db.query", "SELECT * FROM", "transaction", "paymentService", "Stripe"]
        return any(k in content for k in bad_keywords)
        
    def apply_edit(
        self,
        chunk_id: str,
        target_file: str,
        target_component: str,
        operation: str,
        reason: str,
        new_content: str,
        change_level: str = "L1"
    ) -> dict[str, Any]:
        """Validate an edit against every gate and ledger it. The host agent performs the actual file write."""
        result = self._check_edit(chunk_id, target_file, target_component, operation, reason, new_content, change_level)
        if not result["success"]:
            self.deviations.append(result["deviation"])
            self.rejected_chunks.add(chunk_id)
        return result

    def _check_edit(
        self,
        chunk_id: str,
        target_file: str,
        target_component: str,
        operation: str,
        reason: str,
        new_content: str,
        change_level: str,
    ) -> dict[str, Any]:
        
        # 1. Scope Lock Check
        if not self.scope_lock.is_file_allowed(target_file):
            return {
                "success": False,
                "deviation": build_deviation(
                    self.plan_id, "scope_expansion", 
                    f"File {target_file} not allowed.", 
                    "Allow edit", "file_system"
                )
            }
            
        # 2. Preservation Check
        if self.scope_lock.check_preservation_violation(new_content):
            return {
                "success": False,
                "deviation": build_deviation(
                    self.plan_id, "strategy_change",
                    "Attempted to modify locked global token/palette.",
                    "Re-evaluate preservation profile.", "tokens"
                )
            }
            
        # 3. Business Logic Guard
        if self._guard_business_logic(new_content):
            return {
                "success": False,
                "deviation": build_deviation(
                    self.plan_id, "architecture_conflict",
                    "Business logic detected in UI edit.",
                    "Separate backend logic.", "services"
                )
            }
            
        # 4. Framework Conventions Guard
        fw_check = self.framework_adapter.validate_implementation_structure(target_file, new_content)
        if not fw_check.get("valid"):
            return {
                "success": False,
                "deviation": fw_check.get("deviation")
            }
            
        # 5. Perform the edit (simulated in this engine logic, actual edit happens via MCP/Agent tools in practice, 
        # but this engine provides the interface contract)
        
        # 6. Record Ledger Entry
        entry: ChangeLedgerEntry = {
            "change_id": f"chg_{time.time()}",
            "plan_change_id": f"plan_chg_{target_component}",
            "chunk_id": chunk_id,
            "file": target_file,
            "component": target_component,
            "operation": operation,  # type: ignore
            "reason": reason,
            "change_level": change_level, # type: ignore
            "scope_status": "within_scope",
            "timestamp": time.time()
        }
        self.ledger.append(entry)
        
        return {"success": True, "ledger_entry": entry}
