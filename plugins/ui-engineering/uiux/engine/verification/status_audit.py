"""Development audit for public verification/task status builders (NO_FAKE_PASS)."""
from __future__ import annotations

from pathlib import Path
from typing import Any


def audit_status_semantics(package_root: str | Path | None = None) -> dict[str, Any]:
    """Check canonical public builders for provenance and COMPLETED/verification separation."""
    if package_root is None:
        from uiux.core.resources import get_package_root
        package_root = get_package_root()
    root = Path(package_root)
    sources = {
        "p4_engine": root / "uiux/engine/verification/engine.py",
        "claims": root / "uiux/engine/verification/checks.py",
        "task_orchestrator": root / "uiux/task_orchestrator.py",
        "trust_validator": root / "uiux/engine/verification/trust.py",
    }
    findings: list[str] = []
    try:
        engine, claims, task, validator = (path.read_text(encoding="utf-8") for path in sources.values())
    except OSError as exc:
        return {"status": "FAIL", "findings": [f"status audit input missing: {exc}"], "scanned_files": list(sources)}
    if '"verification_status": verification_status' not in engine or '"trust_level": trust_achieved' not in engine:
        findings.append("P4 public result builder must expose verification_status and trust_level")
    if 'validate_verification_result' not in engine or 'def validate_verified_claims' not in validator:
        findings.append("P4 result builder does not enforce NO_FAKE_PASS provenance validation")
    if '"result": "PASS"' in claims and "verify_design_intent" in claims:
        findings.append("design-intent check contains an unconditional PASS claim")
    if 'if state in {"PASS", "PASS_WITH_WARNINGS"}' not in task:
        findings.append("run_ui_task can mark a task COMPLETED without passing required verification")
    probe = {"verification_status": "PASS", "trust_level": "STATICALLY_VERIFIED", "verified_claims": [],
             "evidence_refs": [], "required_checks": ["SOURCE_DIFF"], "completed_checks": [], "evidence_summary": ""}
    from uiux.engine.verification.trust import validate_verification_result
    if not validate_verification_result(probe):
        findings.append("validator accepted a PASS result without evidence")
    return {"status": "PASS" if not findings else "FAIL", "findings": findings, "scanned_files": list(sources)}
