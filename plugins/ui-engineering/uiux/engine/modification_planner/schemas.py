"""Canonical Schemas for P2: Design Reasoning & Modification Planning Engine."""

from typing import Any, Literal
try:
    from typing import NotRequired, TypedDict
except ImportError:  # Python < 3.11
    from typing_extensions import NotRequired, TypedDict

class RequirementProfile(TypedDict):
    user_goal: str
    task_intent: str
    requested_scope: str
    explicit_requirements: list[str]
    explicit_constraints: list[str]
    brand_constraints: list[str]
    preservation_requests: list[str]
    expected_outcome: str

class ProblemDiagnosisItem(TypedDict):
    id: str
    category: Literal["VISUAL", "UX", "RESPONSIVE", "ACCESSIBILITY", "CONSISTENCY", "ARCHITECTURAL_UI", "PERFORMANCE_UI", "UNKNOWN"]
    surface: Any
    description: str
    severity: Literal["low", "medium", "high", "critical"]
    evidence_refs: list[str]
    confidence: float
    confidence_level: NotRequired[Literal["HIGH", "MEDIUM", "LOW"]]
    confidence_score: NotRequired[float]
    user_impact: str
    technical_impact: str
    is_inferred: bool
    finding_state: NotRequired[Literal["CONFIRMED", "UNKNOWN"]]
    unknown_reason: NotRequired[str]

class ProblemDiagnosis(TypedDict):
    issues: list[ProblemDiagnosisItem]
    confidence_score: float
    confidence_level: NotRequired[Literal["HIGH", "MEDIUM", "LOW"]]
    evidence_refs: NotRequired[list[str]]

class PreservationProfile(TypedDict):
    locked: list[str]
    protected: list[str]
    controlled: list[str]
    free: list[str]
    precedence_rules: list[str]

class DesignStrategy(TypedDict):
    layout_strategy: NotRequired[str]
    component_strategy: NotRequired[str]
    hierarchy_strategy: NotRequired[str]
    typography_strategy: NotRequired[str]
    responsive_strategy: NotRequired[str]
    interaction_strategy: NotRequired[str]
    accessibility_strategy: NotRequired[str]
    knowledge_used: list[dict[str, str]]  # list of {"knowledge_id": "...", "reason": "..."}
    decisions: NotRequired[list[dict[str, Any]]]
    target: NotRequired[list[str]]
    constraints: NotRequired[list[str]]
    reasoning_mode: NotRequired[str]

class RecipeSelection(TypedDict):
    recipe_id: str
    use_case: str
    target_component: str
    reason: str
    adaptation_required: list[str]
    framework_match: bool

class ImpactAnalysis(TypedDict):
    affected_pages: list[str]
    affected_components: list[str]
    shared_components: list[str]
    affected_files: list[str]
    routes: list[str]
    blast_radius: Literal["low", "medium", "high", "critical"]
    business_logic_risk: str
    visual_regression_risk: str

class PlannedChange(TypedDict):
    id: str
    target: str
    problem_ref: str
    decision: str
    reason: str
    change_level: Literal["L1", "L2", "L3"]
    affected_files: list[str]
    affected_surfaces: list[str]
    blast_radius: str
    expected_result: str
    knowledge_refs: list[str]
    evidence_refs: list[str]
    confidence: Literal["FACT", "SUPPORTED_INFERENCE", "DESIGN_JUDGMENT", "UNKNOWN"]

class VerificationContract(TypedDict):
    pages: list[str]
    viewports: list[str]
    scenarios: list[str]
    preservation_checks: list[str]
    accessibility_checks: list[str]
    check_steps: list[str]

class ExecutionChunk(TypedDict):
    id: str
    description: str
    scope: str
    expected_result: str
    dependencies: list[str]
    verification_required: list[str]

class PlanningGate(TypedDict):
    status: Literal["PASS", "PARTIAL", "BLOCKED"]
    missing_requirements: list[str]
    permission_needed: list[str]
    conflicts: list[str]
    recommended_next_action: str

class ModificationPlan(TypedDict):
    schema_version: int
    metadata: dict[str, str]
    requirement_profile: RequirementProfile
    diagnosis: ProblemDiagnosis
    preservation: PreservationProfile
    strategy: DesignStrategy
    recipes: list[RecipeSelection]
    changes: list[PlannedChange]
    impact: ImpactAnalysis
    execution_chunks: list[ExecutionChunk]
    verification: VerificationContract
    rollback: dict[str, Any]
    planning_gate: PlanningGate
    decision_trace: list[dict[str, str]]
