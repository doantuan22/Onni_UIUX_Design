"""Browser-independent P4 checks over P0/P2/P3 artifacts and the target project."""
from __future__ import annotations

import ast
import json
import re
import shlex
import subprocess
import os
import uuid
from pathlib import Path
from typing import Any

from uiux.engine.executor.framework_adapter import FrameworkAdapter
from uiux.engine.verification.strategy import detect_verification_capabilities, resolve_verification_strategy


_RESPONSIVE = re.compile(r"@media\s*\(|\b(sm|md|lg|xl|2xl):|\b(col|row)-(sm|md|lg|xl)\b|\bgrid-template-columns\b|\bflex-wrap\b", re.I)
_TOKEN = re.compile(r"(--(?:color|brand|primary|bg)-[\w-]+)\s*:\s*([^;{}]+)", re.I)
_IMPORT = re.compile(r"(?:^\s*import\s+(?:[^'\"]+from\s+)?|^\s*from\s+)(['\"])([^'\"]+)\1", re.M)
_SAFE_SCRIPTS = {"build", "typecheck", "lint", "test"}
_SAFE_MANAGER = {"npm": ["npm", "run"], "pnpm": ["pnpm", "run"], "yarn": ["yarn"], "bun": ["bun", "run"]}


def _paths(plan: dict[str, Any]) -> set[str]:
    paths: set[str] = set()
    for key in ("affected_surface", "impact"):
        block = plan.get(key, {})
        if isinstance(block, dict):
            for field in ("files", "allowed_files", "planned_files", "affected_files"):
                paths.update(str(p).replace("\\", "/").lstrip("./") for p in block.get(field, []) if isinstance(p, str))
    for change in plan.get("changes", []):
        if isinstance(change, dict):
            paths.update(str(p).replace("\\", "/").lstrip("./") for p in change.get("affected_files", []) if isinstance(p, str))
    return paths


def _changed(implementation: dict[str, Any], session: dict[str, Any]) -> list[str]:
    paths = set()
    for value in implementation.get("files_modified", []):
        if isinstance(value, str): paths.add(value.replace("\\", "/").lstrip("./"))
    for item in implementation.get("ledger", []):
        if isinstance(item, dict) and item.get("file"):
            paths.add(str(item["file"]).replace("\\", "/").lstrip("./"))
    change_manifest = session.get("change_manifest", {})
    if isinstance(change_manifest, dict):
        for value in change_manifest.get("files", change_manifest.get("modified_files", [])):
            if isinstance(value, str): paths.add(value.replace("\\", "/").lstrip("./"))
    for value in session.get("actual_changed_files", []):
        if isinstance(value, str): paths.add(value.replace("\\", "/").lstrip("./"))
    return sorted(paths)


def _issue(category: str, expected: str, actual: str, ref: str, route_to: str = "P3") -> dict[str, Any]:
    return {"id": f"static_{uuid.uuid4().hex[:10]}", "category": category, "severity": "HIGH",
            "surface": "source", "viewport": "static", "scenario": "static-verification",
            "expected": expected, "actual": actual, "confidence": "confirmed",
            "evidence_refs": [ref], "root_cause": "IMPLEMENTATION_ERROR", "route_to": route_to,
            "related_decision": None, "related_change": None, "blocking": True, "repairable": True}


def _build_commands(runtime_detection: dict[str, Any]) -> list[tuple[str, list[str]]]:
    manager = runtime_detection.get("package_manager", {}).get("detected")
    if manager not in _SAFE_MANAGER:
        return []
    configured = runtime_detection.get("project", {}).get("validation_commands", [])
    return [(name, _SAFE_MANAGER[manager] + [name]) for name in configured if name in _SAFE_SCRIPTS]


def _current_token_snapshot(root: Path) -> dict[str, str]:
    current: dict[str, str] = {}
    skipped = {".git", ".evidence", "node_modules", "dist", "build", ".next", ".venv", "venv", "__pycache__"}
    for base, dirs, files in os.walk(root):
        dirs[:] = [name for name in dirs if name not in skipped and not name.startswith(".")]
        for name in files:
            path = Path(base) / name
            if path.suffix.lower() not in {".css", ".scss", ".less", ".html", ".vue", ".tsx", ".jsx", ".ts", ".js"}:
                continue
            try:
                if path.stat().st_size <= 2_000_000:
                    current.update({key: value.strip() for key, value in _TOKEN.findall(path.read_text(encoding="utf-8"))})
            except (OSError, UnicodeError):
                continue
    return current


def _run_build(root: Path, commands: list[tuple[str, list[str]]]) -> list[dict[str, Any]]:
    reports = []
    for name, argv in commands:
        try:
            result = subprocess.run(argv, cwd=root, capture_output=True, text=True, timeout=300, check=False, shell=False)
            reports.append({"command": " ".join(argv), "status": "PASS" if result.returncode == 0 else "FAIL",
                            "exit_code": result.returncode,
                            "summary": ((result.stdout or result.stderr or "command completed")[-1200:]).strip(),
                            "evidence_ref": f"build:{name}"})
        except subprocess.TimeoutExpired:
            reports.append({"command": " ".join(argv), "status": "BLOCKED", "exit_code": None,
                            "summary": "Configured command exceeded the 300 second safety limit.", "evidence_ref": f"build:{name}"})
        except OSError as exc:
            reports.append({"command": " ".join(argv), "status": "BLOCKED", "exit_code": None,
                            "summary": f"Configured package-manager command is unavailable: {type(exc).__name__}.", "evidence_ref": f"build:{name}"})
    return reports


def run_static_verification(plan: dict[str, Any], implementation_report: dict[str, Any],
                            session: dict[str, Any], verification_contract: dict[str, Any],
                            project_root: str | Path | None = None) -> dict[str, Any]:
    target_root = project_root or session.get("project_root") or session.get("repo_path")
    root = Path(target_root or ".").expanduser().resolve()
    capabilities = session.get("verification_capabilities") or detect_verification_capabilities(
        target_root, implementation_report, session.get("runtime_detection"))
    strategy = resolve_verification_strategy(verification_contract, implementation_report, capabilities,
        session.get("ui_context"), session.get("before_evidence"), plan.get("affected_surface"))
    issues: list[dict[str, Any]] = []
    refs: list[str] = []
    if implementation_report.get("ready_for_p4"):
        refs.append("p3:implementation-report")
    changed = _changed(implementation_report, session)
    planned = _paths(plan)
    ledger_files = {str(item.get("file", "")).replace("\\", "/").lstrip("./") for item in implementation_report.get("ledger", []) if isinstance(item, dict) and item.get("file")}
    reported_files = {str(item).replace("\\", "/").lstrip("./") for item in implementation_report.get("files_modified", []) if isinstance(item, str)}
    if ledger_files and reported_files != ledger_files:
        issues.append(_issue("CHANGE_LEDGER_MISMATCH", "P3 files_modified matches ChangeLedger files",
            f"report-only={sorted(reported_files-ledger_files)}; ledger-only={sorted(ledger_files-reported_files)}", "p3:change-ledger"))
    unplanned = sorted(set(changed) - planned) if planned else list(changed)
    change_manifest = session.get("change_manifest", {}) if isinstance(session.get("change_manifest", {}), dict) else {}
    for field, category in {
        "unexpected_dependencies": "UNEXPECTED_DEPENDENCY",
        "unexpected_imports": "UNEXPECTED_IMPORT",
        "unexpected_global_changes": "UNEXPECTED_GLOBAL_CHANGE",
        "business_logic_markers_changed": "BUSINESS_LOGIC_CHANGE",
    }.items():
        values = change_manifest.get(field, [])
        if values:
            issues.append(_issue(category, f"No unapproved {field.replace('_', ' ')}", str(values), "p3:change-manifest"))
    if not changed:
        source_status = "PARTIAL"
        source_reason = "P3 report contains no changed files/ledger entries to inspect."
    elif unplanned:
        source_status = "FAIL"
        source_reason = f"Changed files are outside the approved plan: {', '.join(unplanned)}."
        issues.extend(_issue("UNPLANNED_FILE_CHANGE", "Only planned files change", f"Unplanned files: {', '.join(unplanned)}", "p3:change-ledger") for _ in [0])
    else:
        source_status = "PASS"
        source_reason = f"P3 changed-file ledger is within the plan ({len(changed)} file(s))."
    for name in changed:
        if target_root is None:
            refs.append(f"source:{name}")
            continue
        path = (root / name).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            issues.append(_issue("SOURCE_PATH_ESCAPE", "Changed path remains within project", name, "p3:change-ledger"))
            source_status = "FAIL"
            continue
        refs.append(f"source:{name}")
        if not path.is_file():
            issues.append(_issue("SOURCE_FILE_MISSING", "Changed file exists", f"Missing {name}", f"source:{name}"))
            source_status = "FAIL"

    structure_status = "PASS" if target_root is not None else "PARTIAL"
    structure_notes: list[str] = []
    if target_root is None:
        structure_notes.append("Target project root was not supplied; source structure checks were not run against the caller's working directory.")
    framework = str((plan.get("repository") or {}).get("framework") or "generic")
    adapter = FrameworkAdapter(str(plan.get("plan_id", implementation_report.get("plan_id", "unknown"))), framework)
    token_changes = set(change_manifest.get("changed_tokens", []))
    baseline_tokens = session.get("token_baseline")
    if isinstance(baseline_tokens, dict):
        refs.append("token-baseline:P0_SEE")
    if isinstance(session.get("change_manifest"), dict):
        refs.append("p3:change-manifest")
    locked = set((plan.get("preservation") or {}).get("protected_tokens", []))
    locked.update(k for k, v in (plan.get("preservation") or {}).get("granular_permissions", {}).items() if v == "locked" and k in {"palette", "brand"})
    token_status = "NOT_RUN"
    current_tokens = _current_token_snapshot(root) if isinstance(baseline_tokens, dict) else {}
    if isinstance(baseline_tokens, dict):
        token_changes.update(key for key, old in baseline_tokens.items() if current_tokens.get(key) != old)
        token_changes.update(key for key, value in current_tokens.items() if key not in baseline_tokens and value)
    if token_changes:
        violations = sorted(token for token in token_changes if any(term in token.lower() for term in ("primary", "brand", "palette", "color", "bg-")) and locked)
        refs.append("p3:change-manifest:changed_tokens")
        token_status = "FAIL" if violations else "PASS"
        if violations:
            issues.append(_issue("PRESERVATION_VIOLATION", "Locked brand/palette tokens remain unchanged", ", ".join(violations), "p3:change-manifest:changed_tokens"))
    else:
        structure_notes.append("No changed design token was found in the checked sources.")
    responsive_signal = False
    inspected_files = 0
    import_changes: list[dict[str, Any]] = []
    protected = set((plan.get("affected_surface") or {}).get("protected_files", []))
    protected_changes = sorted(set(changed) & protected)
    if protected_changes:
        issues.append(_issue("PROTECTED_FILE_CHANGED", "Protected files remain unchanged", ", ".join(protected_changes), "p3:change-ledger"))
    for name in changed:
        if target_root is None:
            continue
        path = (root / name).resolve()
        if not path.is_file() or path.suffix.lower() not in {".py", ".js", ".jsx", ".ts", ".tsx", ".vue", ".css", ".html", ".json"}:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            structure_status = "PARTIAL"
            structure_notes.append(f"Could not decode {name} for static inspection.")
            continue
        inspected_files += 1
        if path.suffix.lower() == ".py":
            try: ast.parse(content, filename=name)
            except SyntaxError as exc:
                structure_status = "FAIL"
                issues.append(_issue("STATIC_SYNTAX_ERROR", "Python source parses", f"{name}:{exc.lineno}: {exc.msg}", f"source:{name}"))
        if path.suffix.lower() == ".json":
            try: json.loads(content)
            except ValueError as exc:
                structure_status = "FAIL"
                issues.append(_issue("STATIC_SYNTAX_ERROR", "JSON source parses", f"{name}: {exc}", f"source:{name}"))
        before = (session.get("source_baseline") or {}).get(name)
        if isinstance(before, str):
            added_imports = sorted(set(_IMPORT.findall(content)) - set(_IMPORT.findall(before)))
            if added_imports:
                imports = [item[1] for item in added_imports]
                import_changes.append({"file": name, "added_imports": imports, "evidence_ref": f"source:{name}"})
            if Path(name).name == "package.json":
                try:
                    old_package, new_package = json.loads(before), json.loads(content)
                    old_deps = set()
                    new_deps = set()
                    for key in ("dependencies", "devDependencies"):
                        old_deps.update((old_package.get(key) or {}).keys())
                        new_deps.update((new_package.get(key) or {}).keys())
                    added = new_deps - old_deps
                    approved = set(plan.get("approved_dependencies", [])) | set((plan.get("technology") or {}).get("new_dependencies", []))
                    unexpected = sorted(added - approved)
                    if unexpected:
                        issues.append(_issue("UNEXPECTED_DEPENDENCY", "No unapproved dependency is introduced", ", ".join(unexpected), f"source:{name}"))
                except (ValueError, TypeError):
                    pass
        framework_result = adapter.validate_implementation_structure(name, content)
        if framework_result.get("valid") is False:
            structure_status = "FAIL"
            issues.append(_issue("FRAMEWORK_STRUCTURE", "Source follows detected framework structure", framework_result.get("deviation", {}).get("discovered_condition", "Framework structure is invalid"), f"source:{name}"))
        responsive_signal = responsive_signal or bool(_RESPONSIVE.search(content))
        tokens = _TOKEN.findall(content)
        if tokens:
            refs.append(f"token-source:{name}")
    requested_responsive = any(word in str(verification_contract).lower() for word in ("mobile", "responsive", "viewport"))
    responsive_status = "STATIC_RESPONSIVE_SIGNAL" if responsive_signal and requested_responsive else "NOT_RUN"
    if responsive_status == "STATIC_RESPONSIVE_SIGNAL":
        structure_notes.append("Responsive implementation signals are present in source; rendered behavior remains unverified.")
        refs.extend(f"responsive-source:{name}" for name in changed if (root / name).is_file() and _RESPONSIVE.search((root / name).read_text(encoding="utf-8", errors="ignore")))
    if not inspected_files and changed:
        structure_status = "PARTIAL"
        structure_notes.append("No changed source file had a supported readable format for static structure checks.")
    build_reports = _run_build(root, _build_commands(session.get("runtime_detection", {}))) if capabilities["build_validation"]["status"] == "AVAILABLE" else []
    build_status = "NOT_RUN" if not build_reports else ("FAIL" if any(row["status"] == "FAIL" for row in build_reports) else "BLOCKED" if any(row["status"] == "BLOCKED" for row in build_reports) else "PASS")
    if build_status == "FAIL":
        failed = [row for row in build_reports if row["status"] == "FAIL"]
        issues.extend(_issue("BUILD_VALIDATION", "Configured project validation commands pass", row["summary"], row["evidence_ref"]) for row in failed)
    if (verification_contract.get("preservation_checks") and locked and not token_changes and baseline_tokens is None
            and not isinstance(session.get("change_manifest"), dict)):
        preservation_status = "NOT_RUN"
        structure_notes.append("Preservation checks require a token baseline or change manifest; neither was supplied.")
    refs.extend(row["evidence_ref"] for row in build_reports if row["status"] == "PASS")
    preservation_status = token_status if token_status != "NOT_RUN" else ("PASS" if isinstance(baseline_tokens, dict) else "NOT_RUN")
    framework_status = "FAIL" if structure_status == "FAIL" else "PASS" if changed else "NOT_RUN"
    verification_status = "FAIL" if issues or build_status == "FAIL" else "PARTIAL" if strategy["unavailable_checks"] or source_status == "PARTIAL" or structure_status == "PARTIAL" or preservation_status == "NOT_RUN" or build_status == "BLOCKED" else "PASS"
    if not refs:
        verification_status = "BLOCKED"
    limitations = list(dict.fromkeys(
        [item["reason"] for item in strategy["unavailable_checks"]] +
        capabilities["build_validation"]["limitations"] + structure_notes +
        (["Rendered UI has not been verified."] if "RUNTIME_DOM" not in strategy["selected_checks"] else []) +
        (["Visual appearance has not been verified from screenshots."] if "VISUAL_RENDER" not in strategy["selected_checks"] else []) +
        (["Browser interactions and browser-backed accessibility have not been verified."] if "INTERACTION_A11Y" not in strategy["selected_checks"] else [])
    ))
    return {"status": verification_status, "source_diff": {"status": source_status, "changed_files": changed, "unplanned_files": unplanned, "summary": source_reason},
            "structure": {"status": structure_status, "summary": "Static syntax and existing framework adapter checks over changed supported sources.", "notes": structure_notes, "import_changes": import_changes},
            "preservation": {"status": preservation_status, "summary": "Compared source design tokens to the P0 SEE baseline and P2 locked palette/brand permissions." if isinstance(baseline_tokens, dict) else "NOT_RUN: no token baseline evidence supplied."},
            "framework": {"status": framework_status, "name": framework},
            "responsive_signals": {"status": responsive_status, "rendered_behavior": "UNVERIFIED"},
            "build": {"status": build_status, "commands": build_reports},
            "issues": issues, "evidence_refs": list(dict.fromkeys(refs)), "limitations": limitations,
            "capabilities": capabilities, "strategy": strategy}


class StaticVerificationEngine:
    """Canonical aggregator for existing browser-independent source/framework/build checks."""

    def verify(self, plan: dict[str, Any], implementation_report: dict[str, Any],
               session: dict[str, Any], verification_contract: dict[str, Any],
               project_root: str | Path | None = None) -> dict[str, Any]:
        return run_static_verification(plan, implementation_report, session, verification_contract, project_root)
