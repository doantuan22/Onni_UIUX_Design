"""Canonical Verification Schemas for P4 — CHECK.

Defines the structured output of the Verification Engine, including issue classification,
root cause routing, and the final verification report.
"""
from typing import Any, Literal, TypedDict, NotRequired

RootCauseType = Literal[
    "IMPLEMENTATION_ERROR",  # Route to P3
    "PLAN_ERROR",            # Route to P2
    "UNDERSTANDING_ERROR",   # Route to P0
    "KNOWLEDGE_GAP",         # Route to P1
    "ENVIRONMENT_LIMITATION",# Blocked/Partial
    "EXPECTED_VARIATION",    # Pass (False Positive)
    "UNKNOWN"                # Human/Agent Review
]

SeverityLevel = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]

VerificationStatus = Literal["NOT_RUN", "PASS", "PASS_WITH_WARNINGS", "PARTIAL", "FAIL", "BLOCKED"]

class VerificationIssue(TypedDict):
    id: str
    category: str
    severity: SeverityLevel
    surface: str
    viewport: str
    scenario: str
    expected: str
    actual: str
    evidence_refs: list[str]
    confidence: str
    root_cause: RootCauseType
    route_to: str
    related_decision: str | None
    related_change: str | None
    blocking: bool
    repairable: bool

class RepairRequest(TypedDict):
    issue_id: str
    route_to: str
    root_cause: RootCauseType
    target: str
    evidence: list[str]
    expected: str
    actual: str
    allowed_scope: str
    related_plan: str | None
    required_recheck: list[str]

class DesignIntentResult(TypedDict):
    decision_id: str
    expected: str
    actual: str
    result: Literal["PASS", "FAIL", "UNCERTAIN"]
    evidence: list[str]

class CorrectnessResult(TypedDict):
    status: VerificationStatus
    issues: list[VerificationIssue]

class PreservationResult(TypedDict):
    status: VerificationStatus
    issues: list[VerificationIssue]

class FinalVerificationReport(TypedDict):
    schema_version: int
    task_id: str
    plan_id: str
    implementation_id: str
    
    status: VerificationStatus
    
    correctness: CorrectnessResult
    preservation: PreservationResult
    
    design_intent: dict[str, Any] # Contains list of DesignIntentResult
    
    responsive: dict[str, Any]
    interactions: dict[str, Any]
    accessibility: dict[str, Any]
    performance: dict[str, Any]
    regressions: dict[str, Any]
    
    evidence: dict[str, Any]
    repair: dict[str, Any] # Contains RepairRequest items
    warnings: list[str]
    limitations: list[str]
    final_gate: VerificationStatus
    execution_status: NotRequired[str]
    verification_status: NotRequired[VerificationStatus]
    trust_level: NotRequired[Literal["UNVERIFIED", "STATICALLY_VERIFIED", "RUNTIME_VERIFIED", "MULTIMODAL_VERIFIED"]]
    trust_achieved: NotRequired[str]
    trust_ceiling: NotRequired[str]
    evidence_refs: NotRequired[list[str]]
    verified_claims: NotRequired[list[dict[str, Any]]]
    unverified_claims: NotRequired[list[dict[str, Any]]]
    verification_levels_completed: NotRequired[list[str]]
    verification_levels_unavailable: NotRequired[list[dict[str, str]]]
    evidence_summary: NotRequired[str]
    static_verification: NotRequired[dict[str, Any]]
    trust_report: NotRequired[dict[str, Any]]


class BuildValidationEntry(TypedDict):
    command: str
    status: Literal["PASS", "FAIL", "BLOCKED"]
    exit_code: int | None
    summary: str
    evidence_ref: str


class BuildValidationReport(TypedDict):
    status: Literal["PASS", "FAIL", "BLOCKED", "NOT_RUN"]
    commands: list[BuildValidationEntry]


class StaticVerificationReport(TypedDict):
    status: VerificationStatus
    source_diff: dict[str, Any]
    structure: dict[str, Any]
    preservation: dict[str, Any]
    framework: dict[str, Any]
    responsive_signals: dict[str, Any]
    build: BuildValidationReport
    issues: list[VerificationIssue]
    evidence_refs: list[str]
    limitations: list[str]


class TrustReport(TypedDict):
    execution_status: str
    verification_status: VerificationStatus
    trust_achieved: Literal["UNVERIFIED", "STATICALLY_VERIFIED", "RUNTIME_VERIFIED", "MULTIMODAL_VERIFIED"]
    trust_ceiling: Literal["UNVERIFIED", "STATICALLY_VERIFIED", "RUNTIME_VERIFIED", "MULTIMODAL_VERIFIED"]
    verification_levels_completed: list[str]
    verification_levels_unavailable: list[dict[str, str]]
    verified_claims: list[dict[str, Any]]
    unverified_claims: list[dict[str, Any]]
    evidence_summary: str
    limitations: list[str]
