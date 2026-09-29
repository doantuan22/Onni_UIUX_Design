"""P3 Controlled Implementation Engine.
Main Orchestrator for P3 Phase.
"""
from typing import Any
from uiux.engine.executor.schemas import ImplementationReport, PlanDeviation
from uiux.engine.executor.execution_gate import check_execution_gate
from uiux.engine.executor.scope_lock import ScopeLock
from uiux.engine.executor.file_editor import FileEditor

class ChunkExecutor:
    """Orchestrates execution of the Modification Plan."""
    
    def __init__(self, plan: dict[str, Any], framework: str = "generic"):
        self.plan = plan
        self.plan_id = plan.get("metadata", {}).get("plan_id", "unknown_plan")
        self.scope_lock = ScopeLock(plan)
        self.editor = FileEditor(self.scope_lock, self.plan_id, framework)
        
    def execute_plan(self, edits: list[dict[str, Any]] | None = None) -> ImplementationReport:
        """Guard the proposed ``edits`` and build the Implementation Report from what the ledger actually holds.

        The engine never writes files; the host agent does. A chunk counts as applied only when at least one of its
        edits passed every gate, and the report is ``ready_for_p4`` only when every chunk is applied without deviation.
        """
        gate = check_execution_gate(self.plan)
        if gate["status"] == "BLOCKED":
            return self._build_report(status="BLOCKED")

        for edit in edits or []:
            self.editor.apply_edit(**edit)

        chunk_ids = [c.get("id") for c in self.plan.get("execution_chunks", [])]
        ledger = self.editor.ledger
        edited = {entry["chunk_id"] for entry in ledger}
        failed_chunks = [c for c in chunk_ids if c in self.editor.rejected_chunks]
        applied_chunks = [c for c in chunk_ids if c in edited and c not in self.editor.rejected_chunks]
        pending_chunks = [c for c in chunk_ids if c not in edited and c not in self.editor.rejected_chunks]
        deviations: list[PlanDeviation] = list(self.editor.deviations)  # type: ignore[arg-type]

        if deviations:
            status = "DEVIATED"
        elif pending_chunks:
            status = "PARTIAL"
        else:
            status = "COMPLETED"

        return {
            "task_id": self.plan.get("requirement_profile", {}).get("task_intent", "unknown"),
            "plan_id": self.plan_id,
            "status": status,  # type: ignore
            "chunks_applied": applied_chunks,
            "chunks_failed": failed_chunks,
            "chunks_blocked": [],
            "chunks_pending": pending_chunks,
            "files_modified": sorted({entry["file"] for entry in ledger}),
            "components_modified": sorted({entry["component"] for entry in ledger}),
            "deviations": deviations,
            "ledger": list(ledger),
            "ready_for_p4": status == "COMPLETED",
        }

    def _build_report(self, status: str) -> ImplementationReport:
        return {
            "task_id": self.plan.get("requirement_profile", {}).get("task_intent", "unknown"),
            "plan_id": self.plan_id,
            "status": status, # type: ignore
            "chunks_applied": [],
            "chunks_failed": [],
            "chunks_blocked": [c["id"] for c in self.plan.get("execution_chunks", [])],
            "chunks_pending": [],
            "ledger": [],
            "files_modified": [],
            "components_modified": [],
            "deviations": [],
            "ready_for_p4": False
        }
