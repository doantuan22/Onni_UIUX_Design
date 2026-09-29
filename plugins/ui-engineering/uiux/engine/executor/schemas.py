"""Canonical Schemas for P3: Controlled UI Editing & Implementation Engine."""

from typing import Any, Literal
try:
    from typing import TypedDict
except ImportError:
    from typing_extensions import TypedDict

class ChangeLedgerEntry(TypedDict):
    change_id: str
    plan_change_id: str
    chunk_id: str
    file: str
    component: str
    operation: Literal["modify", "create", "delete"]
    reason: str
    change_level: Literal["L1", "L2", "L3"]
    scope_status: Literal["within_scope", "deviation"]
    timestamp: float

class PlanDeviation(TypedDict):
    type: Literal[
        "scope_expansion", 
        "strategy_change", 
        "change_level_escalation", 
        "unexpected_dependency", 
        "architecture_conflict", 
        "missing_context", 
        "recipe_mismatch"
    ]
    current_plan_id: str
    discovered_condition: str
    required_change: str
    affected_scope: str
    risk: str
    recommended_action: str

class ImplementationReport(TypedDict):
    task_id: str
    plan_id: str
    status: Literal["COMPLETED", "PARTIAL", "BLOCKED", "DEVIATED"]
    chunks_applied: list[str]
    chunks_failed: list[str]
    chunks_blocked: list[str]
    chunks_pending: list[str]
    ledger: list[ChangeLedgerEntry]
    files_modified: list[str]
    components_modified: list[str]
    deviations: list[PlanDeviation]
    ready_for_p4: bool

class AffectedSurfaceManifest(TypedDict):
    pages: list[str]
    routes: list[str]
    components: list[str]
    layouts: list[str]
    viewports: list[str]
    shared_consumers: list[str]

class ExecutionGateReport(TypedDict):
    status: Literal["PASS", "BLOCKED"]
    reason: str
    missing_contract: list[str]
    invalid_scope: list[str]
