"""Canonical verification trust vocabulary and provenance validation."""
from __future__ import annotations

from typing import Any, Literal, TypedDict


VERIFICATION_LEVELS = (
    "SOURCE_DIFF",
    "STATIC_STRUCTURE",
    "BUILD_VALIDATION",
    "RUNTIME_DOM",
    "VISUAL_RENDER",
    "INTERACTION_A11Y",
)
TRUST_LEVELS = (
    "UNVERIFIED",
    "STATICALLY_VERIFIED",
    "RUNTIME_VERIFIED",
    "MULTIMODAL_VERIFIED",
)
VERIFICATION_STATUSES = (
    "NOT_RUN",
    "PASS",
    "PASS_WITH_WARNINGS",
    "PARTIAL",
    "FAIL",
    "BLOCKED",
)
CLAIM_TYPES = (
    "SOURCE_INTEGRITY",
    "FRAMEWORK_INTEGRITY",
    "PRESERVATION",
    "BUILD_VALIDITY",
    "RUNTIME_CORRECTNESS",
    "RESPONSIVE_BEHAVIOR",
    "VISUAL_INTENT",
    "INTERACTION",
    "ACCESSIBILITY",
    "PERFORMANCE_SIGNAL",
)

VerificationStatus = Literal["NOT_RUN", "PASS", "PASS_WITH_WARNINGS", "PARTIAL", "FAIL", "BLOCKED"]
TrustLevel = Literal["UNVERIFIED", "STATICALLY_VERIFIED", "RUNTIME_VERIFIED", "MULTIMODAL_VERIFIED"]


class VerificationCapability(TypedDict):
    status: str
    reason: str
    requirements: list[str]
    evidence_types: list[str]
    limitations: list[str]


class VerificationCapabilities(TypedDict):
    source_diff: VerificationCapability
    static_structure: VerificationCapability
    build_validation: VerificationCapability
    runtime_dom: VerificationCapability
    visual_render: VerificationCapability
    interaction_a11y: VerificationCapability
    maximum_trust_level: TrustLevel


class VerificationStrategy(TypedDict):
    required_levels: list[str]
    available_levels: list[str]
    selected_checks: list[str]
    unavailable_checks: list[dict[str, str]]
    degraded_mode: bool
    expected_trust_ceiling: TrustLevel


class EvidenceProvenance(TypedDict):
    claim_id: str
    claim_type: str
    evidence_refs: list[str]
    verification_level: str
    source: str
    status: str
    confidence: str


def validate_verified_claims(claims: list[dict[str, Any]]) -> list[str]:
    """Reject verified claims without valid, typed evidence references."""
    errors: list[str] = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            errors.append(f"verified_claims[{index}] must be an object")
            continue
        refs = claim.get("evidence_refs", claim.get("evidence", []))
        if claim.get("status", "VERIFIED") in {"VERIFIED", "PASS"} and (
            not isinstance(refs, list) or not refs or not all(isinstance(ref, str) and ref.strip() for ref in refs)
        ):
            errors.append(f"verified_claims[{index}] has no evidence provenance")
        elif isinstance(refs, list) and claim.get("status", "VERIFIED") in {"VERIFIED", "PASS"}:
            invalid_refs = [ref for ref in refs if not ref.startswith(("source:", "p3:", "runtime:", "build:", "token-baseline:", "accessibility:", "interaction:", "visual:"))]
            if invalid_refs:
                errors.append(f"verified_claims[{index}] has invalid evidence refs: {invalid_refs}")
        claim_type = claim.get("claim_type")
        if claim_type is not None and claim_type not in CLAIM_TYPES:
            errors.append(f"verified_claims[{index}] has unknown claim_type {claim_type!r}")
        level = claim.get("verification_level")
        if level is not None and level not in VERIFICATION_LEVELS:
            errors.append(f"verified_claims[{index}] has unknown verification_level {level!r}")
    return errors


def validate_verification_result(result: dict[str, Any]) -> list[str]:
    """Validate public verification semantics; execution success is never verification proof."""
    errors: list[str] = []
    status = result.get("verification_status")
    trust = result.get("trust_level", result.get("trust_achieved"))
    if status not in VERIFICATION_STATUSES:
        errors.append(f"invalid verification_status: {status!r}")
    if trust not in TRUST_LEVELS:
        errors.append(f"invalid trust_level: {trust!r}")
    errors.extend(validate_verified_claims(result.get("verified_claims", [])))
    global_refs = set(result.get("evidence_refs", []))
    for index, claim in enumerate(result.get("verified_claims", [])):
        if isinstance(claim, dict):
            refs = set(claim.get("evidence_refs", claim.get("evidence", [])) or [])
            if not refs.issubset(global_refs):
                errors.append(f"verified_claims[{index}] references evidence absent from result.evidence_refs")
    if status == "PASS":
        required = ("evidence_summary", "required_checks", "completed_checks", "evidence_refs")
        for key in required:
            if not result.get(key):
                errors.append(f"PASS result is missing {key}")
        if result.get("unavailable_checks") or result.get("verification_levels_unavailable"):
            errors.append("PASS result has unavailable required checks")
        missing_checks = set(result.get("required_checks", [])) - set(result.get("completed_checks", []))
        if missing_checks:
            errors.append("PASS result is missing required checks: " + ", ".join(sorted(missing_checks)))
    if status in {"PARTIAL", "BLOCKED"} and not result.get("limitations"):
        errors.append(f"{status} result must explain limitations")
    if result.get("execution_status") == "COMPLETED" and status not in {"PASS", "PASS_WITH_WARNINGS"}:
        # Allowed only for the separate TrustReport, never as a public task completion result.
        if result.get("public_task_status") == "COMPLETED":
            errors.append("public task cannot be COMPLETED when required verification did not pass")
    return errors


def provenance(claim_id: str, claim_type: str, refs: list[str], level: str,
               source: str, status: str = "VERIFIED", confidence: str = "confirmed") -> EvidenceProvenance:
    return {"claim_id": claim_id, "claim_type": claim_type, "evidence_refs": list(refs),
            "verification_level": level, "source": source, "status": status, "confidence": confidence}


def trust_rank(level: str) -> int:
    try:
        return TRUST_LEVELS.index(level)
    except ValueError:
        return 0


def cap_trust(achieved: str, ceiling: str) -> str:
    return achieved if trust_rank(achieved) <= trust_rank(ceiling) else ceiling
