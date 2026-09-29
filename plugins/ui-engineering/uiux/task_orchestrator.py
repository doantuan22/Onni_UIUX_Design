"""Sequential agent-facing UI task orchestration over the existing P0-P4 engines.

Task sessions and canonical phase artifacts live beside runtime evidence in
``<project>/.evidence/uiux-tasks/<task_id>``. This module owns lifecycle,
handoff, projection and routing; phase decisions remain in their existing
engines.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from uiux.core.errors import UiuxError

PHASES = ("SEE", "KNOW", "THINK", "DO", "CHECK", "DONE")
PUBLIC_STATUSES = ("RUNNING", "NEEDS_INPUT", "NEEDS_PERMISSION", "BLOCKED", "DEVIATED", "PARTIAL", "COMPLETED", "FAILED")
TERMINAL = {"COMPLETED", "FAILED"}
TASK_ID_RE = re.compile(r"^uiux_task_[0-9a-f]{16}$")
SKIP_DIRS = {".git", ".evidence", "node_modules", "dist", "build", ".next", ".nuxt", ".svelte-kit", "__pycache__", ".venv", "venv"}
HEAVY_KEYS = {"component_graph", "knowledge_entries", "changes_tree", "change_ledger", "evidence_manifest", "ledger"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class TaskStore:
    """Small JSON artifact store reusing the project's existing evidence root."""

    def __init__(self, project: str | Path):
        self.project = Path(project).expanduser().resolve()
        if not self.project.is_dir():
            raise UiuxError(f"Repository path does not exist or is not a directory: {self.project}", "FILESYSTEM_ERROR")
        self.root = self.project / ".evidence" / "uiux-tasks"

    def task_dir(self, task_id: str) -> Path:
        if not TASK_ID_RE.fullmatch(task_id):
            raise UiuxError("Invalid task_id", "INVALID_ARGUMENT")
        path = (self.root / task_id).resolve()
        if not path.is_relative_to(self.root.resolve()):
            raise UiuxError("Task artifact path escapes evidence storage", "INVALID_ARGUMENT")
        return path

    def save(self, task_id: str, name: str, value: Any) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9_-]*", name):
            raise UiuxError("Invalid task artifact name", "INVALID_ARGUMENT")
        folder = self.task_dir(task_id)
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"{name}.json"
        fd, temp_name = tempfile.mkstemp(prefix=f".{name}-", suffix=".tmp", dir=folder)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, ensure_ascii=False, indent=2, default=str)
                handle.write("\n")
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)
        return target.relative_to(self.project).as_posix()

    def load(self, task_id: str) -> dict[str, Any]:
        path = self.task_dir(task_id) / "task-session.json"
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise UiuxError(f"Task session not found: {task_id}", "INVALID_ARGUMENT") from exc
        except (OSError, ValueError) as exc:
            raise UiuxError(f"Task session is unreadable: {exc}", "FILESYSTEM_ERROR") from exc
        if Path(value.get("repo_root", "")).resolve() != self.project:
            raise UiuxError("task_id belongs to a different repository", "INVALID_ARGUMENT")
        return value

    def load_ref(self, ref: str | None) -> Any:
        if not ref:
            return None
        path = (self.project / ref).resolve()
        allowed = (self.root.resolve(),)
        if not any(path.is_relative_to(root) for root in allowed):
            raise UiuxError("Artifact reference is outside task evidence storage", "INVALID_ARGUMENT")
        return json.loads(path.read_text(encoding="utf-8"))

    def save_session(self, session: dict[str, Any]) -> None:
        self.save(session["task_id"], "task-session", session)


class TaskOrchestrator:
    """Advance a persisted task by at most one P0-P4 phase per call."""

    def orchestrate_ui(self, request: dict[str, Any]) -> dict[str, Any]:
        # Keep the existing policy/router as the one source for legacy decisions.
        from uiux.engine import orchestrator
        return orchestrator.orchestrate(request)

    def run_ui_task(
        self,
        task_id: str | None = None,
        request: str | None = None,
        repo_path: str | None = None,
        user_message: str | None = None,
        verbosity: str = "compact",
    ) -> dict[str, Any]:
        if verbosity not in {"compact", "standard", "full"}:
            raise UiuxError("verbosity must be compact, standard, or full", "INVALID_ARGUMENT")
        if task_id is None:
            if not request or not request.strip():
                return self._recoverable(
                    task_id=None, phase="SEE", status="NEEDS_INPUT", code="INSUFFICIENT_CONTEXT",
                    summary="A UI task request is required.", cause="The first call needs a non-empty request.",
                    missing=["request"], verbosity=verbosity,
                )
            store = TaskStore(repo_path or ".")
            task_id = f"uiux_task_{uuid.uuid4().hex[:16]}"
            now = _now()
            session: dict[str, Any] = {
                "task_id": task_id, "user_request": request.strip(), "repo_root": str(store.project),
                "current_phase": "SEE", "internal_state": "NEW", "public_status": "RUNNING",
                "phase_history": [], "artifact_refs": {}, "pending_input": None, "pending_permission": None,
                "repair_history": [], "last_error": None, "created_at": now, "updated_at": now,
                "request_context": {},
            }
            store.task_dir(task_id).mkdir(parents=True, exist_ok=True)
            self._write_index(task_id, store.project)
        else:
            # repo_path may be omitted on continuation; load from the project's persisted task metadata.
            if repo_path:
                store = TaskStore(repo_path)
            else:
                store = self._find_store(task_id)
            session = store.load(task_id)
            if session.get("public_status") in TERMINAL or session.get("internal_state") == "COMPLETED":
                return self._envelope(session, store, "Task is already in a terminal state.", {"type": "DONE", "tool": None,
                    "task_id": task_id, "message": "This task is already complete or stopped.", "required_input": []}, verbosity)
            if session.get("pending_input") and not (user_message and user_message.strip()):
                return self._envelope(session, store, session["pending_input"]["summary"], self._action(
                    "PROVIDE_INPUT", task_id, session["pending_input"]["message"], session["pending_input"].get("required_input", ["user_message"])), verbosity)
            if session.get("pending_permission"):
                if not (user_message and user_message.strip()):
                    return self._envelope(session, store, session["pending_permission"]["summary"], self._action(
                        "GRANT_PERMISSION", task_id, session["pending_permission"]["message"], ["user_message"]), verbosity)
                session["request_context"]["permission_response"] = user_message.strip()
                session["pending_permission"] = None
                session["internal_state"] = "THINK_PENDING"
                session["public_status"] = "RUNNING"
            elif session.get("pending_input"):
                session["request_context"]["user_message"] = user_message.strip()
                session["pending_input"] = None
                session["public_status"] = "RUNNING"

        phase = session["current_phase"]
        try:
            result = self._advance(store, session, phase)
        except UiuxError as exc:
            session["last_error"] = {"code": exc.code, "message": exc.message}
            session["public_status"] = "FAILED"
            session["internal_state"] = "FAILED"
            session["phase_history"].append({"phase": phase, "status": "FAILED", "at": _now()})
            session["updated_at"] = _now()
            store.save_session(session)
            return self._envelope(session, store, f"{phase} failed: {exc.message}", self._action(
                "FIX_ENVIRONMENT", task_id, exc.remediation or "Resolve the reported problem and retry.", []), verbosity,
                extra={"code": exc.code, "cause": exc.message})
        except Exception as exc:  # public task boundary
            session["last_error"] = {"code": "INTERNAL_FAILURE", "message": str(exc)}
            session["public_status"] = "FAILED"
            session["internal_state"] = "FAILED"
            session["phase_history"].append({"phase": phase, "status": "FAILED", "at": _now()})
            session["updated_at"] = _now()
            store.save_session(session)
            return self._envelope(session, store, f"{phase} failed unexpectedly.", self._action(
                "FIX_ENVIRONMENT", task_id, "Inspect the task artifact and retry after resolving the error.", []), verbosity,
                extra={"code": "INTERNAL_FAILURE", "cause": str(exc)})
        if result:
            return self._envelope(session, store, result["summary"], result["action"], verbosity, result.get("extra"))
        return self._envelope(session, store, session.get("phase_summary", f"{phase} phase finished."),
                              self._action("CALL_AGAIN", task_id, f"Continue to {session['current_phase']} phase.", []), verbosity)

    def _find_store(self, task_id: str) -> TaskStore:
        if not TASK_ID_RE.fullmatch(task_id):
            raise UiuxError("Invalid task_id", "INVALID_ARGUMENT")
        # Cross-call invocation from a different cwd: project path is recorded in a small index under the
        # current evidence root when possible. Explicit repo_path remains the portable fallback.
        index = Path(".evidence") / "uiux-tasks" / "task-index.json"
        if index.is_file():
            try:
                root = json.loads(index.read_text(encoding="utf-8")).get(task_id)
                if root:
                    return TaskStore(root)
            except (OSError, ValueError):
                pass
        return TaskStore(".")

    def _write_index(self, task_id: str, project: Path) -> None:
        index = Path.cwd() / ".evidence" / "uiux-tasks" / "task-index.json"
        try:
            index.parent.mkdir(parents=True, exist_ok=True)
            current = json.loads(index.read_text(encoding="utf-8")) if index.is_file() else {}
        except (OSError, ValueError):
            current = {}
        current[task_id] = str(project)
        temp = index.with_suffix(".tmp")
        temp.write_text(json.dumps(current, indent=2), encoding="utf-8")
        os.replace(temp, index)

    def _advance(self, store: TaskStore, session: dict[str, Any], phase: str) -> dict[str, Any] | None:
        session["internal_state"] = f"{phase}_PENDING"
        session["public_status"] = "RUNNING"
        if phase == "SEE":
            return self._see(store, session)
        if phase == "KNOW":
            return self._know(store, session)
        if phase == "THINK":
            return self._think(store, session)
        if phase == "DO":
            return self._do(store, session)
        if phase == "CHECK":
            return self._check(store, session)
        session["current_phase"] = "DONE"
        session["internal_state"] = "COMPLETED"
        session["public_status"] = "COMPLETED"
        return {"summary": "UI task completed.", "action": self._action("DONE", session["task_id"], "UI task completed.", [])}

    def _see(self, store: TaskStore, s: dict[str, Any]) -> dict[str, Any] | None:
        from uiux.api import analyze_existing_ui, analyze_repository, map_ui_structure
        from uiux.engine.ui_state import detect_ui_state
        repo = analyze_repository(str(store.project))
        state = detect_ui_state({"repo_profile": repo})
        route = self.orchestrate_ui({"user_request": s["user_request"],
            "repo_context": {"ui_signals": {"ui_state": state.get("ui_state", "UNKNOWN"),
                                             "confidence": state.get("confidence", 0.0)}},
            "requested_scope": "global"})
        s["request_context"].update({"repo_profile_ref": store.save(s["task_id"], "repo-profile", repo), "ui_state": state})
        s["request_context"]["workflow"] = route.get("workflow", "unknown")
        s["artifact_refs"]["orchestration_decision"] = store.save(s["task_id"], "orchestration-decision", route)
        existing = None
        if state.get("ui_state") in {"EXISTING_UI", "PARTIAL_UI"}:
            existing = analyze_existing_ui(str(store.project), repo_profile=repo)
            s["request_context"]["existing_ui_profile_ref"] = store.save(s["task_id"], "existing-ui-profile", existing)
            from uiux.api import build_preservation_profile
            preservation = build_preservation_profile(existing, requested_scope="global")
            s["request_context"]["preservation_profile_ref"] = store.save(s["task_id"], "preservation-profile", preservation)
        ui_map = map_ui_structure(str(store.project))
        s["request_context"]["ui_context_ref"] = store.save(s["task_id"], "ui-context", {
            "ui_state": state, "repo_profile": repo, "existing_ui_profile": existing, "ui_map": ui_map,
            "affected_surfaces": (existing or {}).get("layout", {}).get("pages", []),
            "baseline_refs": {"ui_map": s["request_context"].get("ui_map_ref")},
        })
        s["artifact_refs"].update({"repo_profile": s["request_context"]["repo_profile_ref"],
                                   "ui_context": s["request_context"]["ui_context_ref"]})
        if existing:
            s["artifact_refs"].update({"existing_ui_profile": s["request_context"]["existing_ui_profile_ref"],
                                       "preservation_profile": s["request_context"]["preservation_profile_ref"]})
        s["request_context"]["ui_map_ref"] = store.save(s["task_id"], "ui-map", ui_map)
        # refresh ui_context now that the baseline map ref is known
        context = store.load_ref(s["request_context"]["ui_context_ref"])
        context["baseline_refs"]["ui_map"] = s["request_context"]["ui_map_ref"]
        s["request_context"]["ui_context_ref"] = store.save(s["task_id"], "ui-context", context)
        s["artifact_refs"]["ui_context"] = s["request_context"]["ui_context_ref"]
        s["request_context"]["file_snapshot"] = self._snapshot(store.project)
        s["internal_state"] = "SEE_COMPLETE"
        s["phase_history"].append({"phase": "SEE", "status": "COMPLETED", "at": _now()})
        s["current_phase"] = "KNOW"
        s["updated_at"] = _now()
        store.save_session(s)
        s["phase_summary"] = f"Repository scanned; UI state is {state.get('ui_state', 'UNKNOWN')}. UI context and baseline saved for the next phase."
        return None

    def _know(self, store: TaskStore, s: dict[str, Any]) -> dict[str, Any] | None:
        from uiux.api import build_knowledge_plan
        ctx = s["request_context"]
        repo = store.load_ref(ctx["repo_profile_ref"])
        existing = store.load_ref(ctx.get("existing_ui_profile_ref"))
        preservation = store.load_ref(ctx.get("preservation_profile_ref"))
        ui_state = ctx.get("ui_state", {}).get("ui_state", "UNKNOWN")
        workflow = ctx.get("workflow", "greenfield" if ui_state == "GREENFIELD" else "existing-ui")
        knowledge = build_knowledge_plan(repo_profile=repo, existing_ui_profile=existing,
            preservation_profile=preservation, user_request=s["user_request"], workflow=workflow)
        ref = store.save(s["task_id"], "knowledge-plan", knowledge)
        s["artifact_refs"]["knowledge_plan"] = ref
        s["request_context"]["knowledge_plan_ref"] = ref
        s["internal_state"] = "KNOW_COMPLETE"
        s["phase_history"].append({"phase": "KNOW", "status": "COMPLETED", "at": _now()})
        s["current_phase"] = "THINK"
        s["updated_at"] = _now()
        store.save_session(s)
        s["phase_summary"] = "Relevant knowledge, framework/domain guidance, and preservation context are loaded."
        return None

    def _think(self, store: TaskStore, s: dict[str, Any]) -> dict[str, Any] | None:
        from uiux.api import build_validation_handoff, plan_modification
        ctx = s["request_context"]
        repo = store.load_ref(ctx["repo_profile_ref"])
        existing = store.load_ref(ctx.get("existing_ui_profile_ref"))
        preservation = store.load_ref(ctx.get("preservation_profile_ref"))
        knowledge = store.load_ref(ctx["knowledge_plan_ref"])
        permission_text = ctx.pop("permission_response", None)
        constraints = None
        ui_state = ctx.get("ui_state", {}).get("ui_state", "UNKNOWN")
        workflow = ctx.get("workflow", "greenfield" if ui_state == "GREENFIELD" else "existing-ui")
        effective_request = s["user_request"]
        if permission_text:
            effective_request += "\n\n" + permission_text
        elif ctx.get("user_message"):
            effective_request += "\n\nAdditional user context: " + ctx.pop("user_message")
        plan = plan_modification(user_request=effective_request, workflow=workflow,
            repo_profile=repo, existing_ui_profile=existing, preservation_profile=preservation,
            knowledge_plan=knowledge, explicit_constraints=constraints)
        plan_ref = store.save(s["task_id"], "modification-plan", plan)
        s["artifact_refs"]["modification_plan"] = plan_ref
        s["request_context"]["modification_plan_ref"] = plan_ref
        gate = plan.get("planning_gate") or {}
        handoff = build_validation_handoff(plan)
        s["artifact_refs"]["verification_contract"] = store.save(s["task_id"], "verification-contract", handoff)
        permission = (plan.get("status") == "needs_permission" or gate.get("status") == "NEEDS_PERMISSION"
                      or bool(gate.get("permission_needed")))
        s["internal_state"] = "THINK_COMPLETE"
        s["phase_history"].append({"phase": "THINK", "status": "NEEDS_PERMISSION" if permission else "COMPLETED", "at": _now()})
        s["updated_at"] = _now()
        if permission:
            s["public_status"] = "NEEDS_PERMISSION"
            s["internal_state"] = "NEEDS_PERMISSION"
            s["last_error"] = {"code": "NEEDS_PERMISSION", "cause": "; ".join(plan.get("status_reasons", []))}
            s["pending_permission"] = {"summary": "The plan requires explicit permission before it can proceed.",
                "message": "Grant the requested change level explicitly in user_message to re-plan.", "required_input": ["user_message"]}
            s["current_phase"] = "THINK"
            store.save_session(s)
            return {"summary": s["pending_permission"]["summary"], "action": self._action("GRANT_PERMISSION", s["task_id"], s["pending_permission"]["message"], ["user_message"]),
                    "extra": {"code": "NEEDS_PERMISSION", "cause": "; ".join(plan.get("status_reasons", []))}}
        if plan.get("status") in {"insufficient_context", "blocked"} or gate.get("status") == "BLOCKED":
            missing = self._missing_plan_fields(plan)
            status = "NEEDS_INPUT" if missing else "BLOCKED"
            s["public_status"] = status
            s["internal_state"] = "NEEDS_INPUT" if missing else "BLOCKED"
            s["last_error"] = {"code": "INSUFFICIENT_CONTEXT" if missing else "EXECUTION_BLOCKED",
                                "cause": "; ".join(plan.get("status_reasons", [])), "missing": missing}
            s["current_phase"] = "THINK"
            s["pending_input"] = {"summary": "The modification plan cannot proceed with the available context.",
                "message": "Provide the missing scope or project context in user_message.", "required_input": ["user_message"]} if missing else None
            store.save_session(s)
            action = self._action("PROVIDE_INPUT" if missing else "FIX_ENVIRONMENT", s["task_id"],
                "Provide the missing planning context." if missing else "Review the planning gate and resolve its blocker.", ["user_message"] if missing else [])
            return {"summary": "Planning is blocked; no implementation phase ran.", "action": action,
                    "extra": {"code": "INSUFFICIENT_CONTEXT" if missing else "EXECUTION_BLOCKED", "cause": "; ".join(plan.get("status_reasons", [])), "missing": missing}}
        s["current_phase"] = "DO"
        store.save_session(s)
        s["phase_summary"] = "Modification plan passed its planning gate; scope, preservation rules, and verification contract are saved."
        return None

    def _do(self, store: TaskStore, s: dict[str, Any]) -> dict[str, Any] | None:
        from uiux.api import check_execution_gate, guard_edits
        ctx = s["request_context"]
        plan = store.load_ref(ctx["modification_plan_ref"])
        gate = check_execution_gate(plan)
        gate_ref = store.save(s["task_id"], "execution-gate", gate)
        if gate.get("status") != "PASS":
            s["public_status"] = "BLOCKED"
            s["last_error"] = {"code": "EXECUTION_BLOCKED", "details": gate}
            s["phase_history"].append({"phase": "DO", "status": "BLOCKED", "at": _now()})
            s["updated_at"] = _now()
            store.save_session(s)
            return {"summary": "The execution gate blocked the implementation plan.",
                "action": self._action("FIX_ENVIRONMENT", s["task_id"], "Resolve the planning/execution gate findings before continuing.", []),
                "extra": {"code": "EXECUTION_BLOCKED", "cause": gate.get("reason", "Execution gate did not pass."), "artifact_refs": {"execution_gate": gate_ref}}}
        edits = self._changed_files(store.project, ctx.get("file_snapshot", {}), plan)
        if not edits:
            s["public_status"] = "NEEDS_INPUT"
            s["pending_input"] = {"summary": "No implementation changes were found for the approved plan.",
                "message": "Apply the approved UI changes in the target repository, then call run_ui_task again.", "required_input": ["user_message"]}
            s["internal_state"] = "NEEDS_INPUT"
            s["current_phase"] = "DO"
            s["last_error"] = {"code": "INSUFFICIENT_CONTEXT", "cause": "No source changes were found since SEE."}
            store.save_session(s)
            return {"summary": s["pending_input"]["summary"], "action": self._action("PROVIDE_INPUT", s["task_id"], s["pending_input"]["message"], ["user_message"]),
                    "extra": {"code": "INSUFFICIENT_CONTEXT", "cause": s["last_error"]["cause"], "missing": ["implementation changes"]}}
        report = guard_edits(plan, edits)
        ref = store.save(s["task_id"], "implementation-report", report)
        s["artifact_refs"]["implementation_report"] = ref
        s["request_context"]["implementation_report_ref"] = ref
        if report.get("status") == "DEVIATED" or report.get("deviations"):
            s["internal_state"] = "REPAIR_ROUTED"
            s["public_status"] = "DEVIATED"
            s["last_error"] = {"code": "PLAN_DEVIATION", "cause": "P3 rejected one or more edits."}
            s["repair_history"].append({"from": "DO", "to": "THINK", "cause": "PLAN_DEVIATION", "at": _now(), "artifact_ref": ref})
            s["current_phase"] = "THINK"
            s["phase_history"].append({"phase": "DO", "status": "DEVIATED", "at": _now()})
            s["internal_state"] = "THINK_PENDING"
            s["updated_at"] = _now()
            store.save_session(s)
            return {"summary": "P3 found changes outside the approved plan; the task is routed to THINK for re-planning.",
                    "action": self._action("CALL_AGAIN", s["task_id"], "Continue with THINK to re-plan the deviation.", []),
                    "extra": {"code": "PLAN_DEVIATION", "cause": "P3 rejected one or more edits.", "artifact_refs": {"implementation_report": ref}}}
        if report.get("status") != "COMPLETED" or not report.get("ready_for_p4"):
            s["public_status"] = "PARTIAL"
            s["phase_history"].append({"phase": "DO", "status": "PARTIAL", "at": _now()})
            s["current_phase"] = "DO"
            s["updated_at"] = _now()
            store.save_session(s)
            return {"summary": "P3 accepted the in-scope changes but one or more planned chunks remain incomplete.",
                    "action": self._action("PROVIDE_INPUT", s["task_id"], "Complete the remaining planned chunks, then retry DO.", ["user_message"]),
                    "extra": {"code": "EXECUTION_BLOCKED", "cause": "Implementation report is not ready for P4.", "artifact_refs": {"implementation_report": ref}}}
        s["phase_history"].append({"phase": "DO", "status": "COMPLETED", "at": _now()})
        s["internal_state"] = "DO_COMPLETE"
        s["current_phase"] = "CHECK"
        s["updated_at"] = _now()
        store.save_session(s)
        s["phase_summary"] = "P3 accepted all detected changes against the plan and saved the implementation report and change ledger."
        return None

    def _check(self, store: TaskStore, s: dict[str, Any]) -> dict[str, Any] | None:
        from uiux.api import detect_runtime, verify_implementation
        ctx = s["request_context"]
        plan = store.load_ref(ctx["modification_plan_ref"])
        implementation = store.load_ref(ctx["implementation_report_ref"])
        runtime = detect_runtime(str(store.project))
        s["artifact_refs"]["runtime_capabilities"] = store.save(s["task_id"], "runtime-capabilities", runtime)
        runtime_state = ((runtime.get("playwright") or {}).get("runtime_state") or {}).get("state")
        evidence = s.get("request_context", {}).get("after_evidence") or self._discover_evidence(store.project)
        if evidence:
            s["artifact_refs"]["runtime_evidence"] = store.save(s["task_id"], "runtime-evidence", evidence)
            s["request_context"]["after_evidence_ref"] = s["artifact_refs"]["runtime_evidence"]
        if not evidence and runtime_state != "READY":
            status = "PARTIAL" if runtime_state else "BLOCKED"
            impact = "Browser-based responsive, interaction, accessibility and screenshot verification cannot run without the target project's Playwright package and browser."
            report = {"status": status, "code": "VERIFICATION_BLOCKED", "summary": impact,
                "runtime_state": runtime_state or "UNKNOWN", "issues": [], "repair_requests": [], "limitations": [impact]}
            ref = store.save(s["task_id"], "verification-report", report)
            s["artifact_refs"]["verification_report"] = ref
            s["phase_history"].append({"phase": "CHECK", "status": status, "at": _now()})
            s["public_status"] = status
            s["internal_state"] = "PARTIAL" if status == "PARTIAL" else "BLOCKED"
            s["current_phase"] = "CHECK"
            s["last_error"] = {"code": "VERIFICATION_BLOCKED", "cause": impact}
            s["updated_at"] = _now()
            store.save_session(s)
            return {"summary": impact, "action": self._action("FIX_ENVIRONMENT", s["task_id"], "Make the target browser runtime available and provide rendered evidence, then resume CHECK.", []),
                    "extra": {"code": "VERIFICATION_BLOCKED", "cause": impact, "artifact_refs": {"verification_report": ref}}}
        if evidence:
            contract = store.load_ref(s["artifact_refs"].get("verification_contract")) or {}
            verification = verify_implementation(implementation, {"after_evidence": evidence,
                "before_evidence": s["request_context"].get("before_evidence"), "modification_plan": plan},
                plan=plan, verification_contract=contract)
        else:
            verification = {"status": "BLOCKED", "final_gate": "BLOCKED", "warnings": [
                "Runtime package is ready, but no rendered evidence has been captured for the planned routes/viewports."], "repair": {"routes": []}}
        ref = store.save(s["task_id"], "verification-report", verification)
        s["artifact_refs"]["verification_report"] = ref
        repair = self._repair_route(verification)
        if repair:
            target, cause = repair
            s["repair_history"].append({"from": "CHECK", "to": target, "cause": cause, "at": _now(), "artifact_ref": ref})
            s["current_phase"] = target
            s["internal_state"] = f"{target}_PENDING"
            s["public_status"] = "RUNNING"
            s["phase_history"].append({"phase": "CHECK", "status": "REPAIR_ROUTED", "at": _now()})
            s["updated_at"] = _now()
            store.save_session(s)
            return {"summary": f"CHECK found {cause}; the task is routed to {target} for repair.",
                    "action": self._action("CALL_AGAIN", s["task_id"], f"Continue in {target} for the routed repair.", []),
                    "extra": {"artifact_refs": {"verification_report": ref}, "repair_root_cause": cause}}
        state = verification.get("final_gate", verification.get("status", "BLOCKED"))
        if state in {"PASS", "COMPLETED", "PASS_WITH_WARNINGS"}:
            s["phase_history"].append({"phase": "CHECK", "status": "COMPLETED", "at": _now()})
            s["current_phase"] = "DONE"
            s["internal_state"] = "COMPLETED"
            s["public_status"] = "COMPLETED"
            s["updated_at"] = _now()
            store.save_session(s)
            return {"summary": "P4 verification passed for the available evidence.", "action": self._action("DONE", s["task_id"], "UI task completed.", []),
                    "extra": {"artifact_refs": {"verification_report": ref}}}
        s["phase_history"].append({"phase": "CHECK", "status": "PARTIAL", "at": _now()})
        s["public_status"] = "PARTIAL"
        s["internal_state"] = "PARTIAL"
        s["updated_at"] = _now()
        store.save_session(s)
        return {"summary": "CHECK could not verify the implementation against a complete rendered evidence set.",
                "action": self._action("FIX_ENVIRONMENT", s["task_id"], "Provide the missing runtime evidence and resume CHECK.", []),
                "extra": {"code": "VERIFICATION_BLOCKED", "cause": "; ".join(verification.get("warnings", [])), "artifact_refs": {"verification_report": ref}}}

    def _repair_route(self, report: dict[str, Any]) -> tuple[str, str] | None:
        repair = report.get("repair") or {}
        routes = repair.get("routes") or report.get("repair_requests") or []
        route_map = {"IMPLEMENTATION_ERROR": "DO", "PLAN_ERROR": "THINK", "UNDERSTANDING_ERROR": "SEE", "KNOWLEDGE_GAP": "KNOW"}
        for item in routes:
            cause = item.get("root_cause") or item.get("type") or item.get("category")
            target = route_map.get(str(cause).upper())
            if not target and item.get("route_to"):
                target = {"P0": "SEE", "P1": "KNOW", "P2": "THINK", "P3": "DO", "P4": "DO"}.get(str(item["route_to"]).upper())
            if target:
                return target, str(cause)
        return None

    def _discover_evidence(self, root: Path) -> dict[str, Any] | None:
        """Reuse the newest captured runtime manifest already present in the target evidence store."""
        evidence_root = root / ".evidence"
        candidates: list[tuple[float, Path]] = []
        if not evidence_root.is_dir():
            return None
        for manifest in evidence_root.glob("*/manifest.json"):
            if manifest.parent.name == "uiux-tasks":
                continue
            try:
                value = json.loads(manifest.read_text(encoding="utf-8"))
                if isinstance(value, dict) and value.get("captures"):
                    candidates.append((manifest.stat().st_mtime, manifest))
            except (OSError, ValueError):
                continue
        if not candidates:
            return None
        try:
            return json.loads(max(candidates, key=lambda item: item[0])[1].read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None

    def _snapshot(self, root: Path) -> dict[str, str]:
        result: dict[str, str] = {}
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".") or d == ".github"]
            for name in files:
                path = Path(base) / name
                try:
                    if path.stat().st_size > 2_000_000:
                        continue
                    rel = path.relative_to(root).as_posix()
                    result[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
                except OSError:
                    continue
        return result

    def _changed_files(self, root: Path, baseline: dict[str, str], plan: dict[str, Any]) -> list[dict[str, Any]]:
        current = self._snapshot(root)
        changed = [path for path, digest in current.items() if baseline.get(path) != digest]
        changed.extend(path for path in baseline if path not in current)
        chunks = plan.get("execution_chunks") or []
        files = plan.get("impact", {}).get("affected_files", []) or plan.get("blast_radius", {}).get("allowed_files", [])
        edits: list[dict[str, Any]] = []
        for index, rel in enumerate(sorted(set(changed))):
            matching = [c for c in chunks if rel == c.get("target") or rel in (c.get("files") or c.get("target_files") or [])]
            if not matching and chunks:
                matching = [chunks[min(index, len(chunks) - 1)]]
            if not matching:
                continue
            path = root / Path(rel)
            try:
                content = path.read_text(encoding="utf-8") if path.exists() else ""
            except (OSError, UnicodeError):
                continue
            component = Path(rel).stem
            for chunk in matching:
                edits.append({"chunk_id": chunk.get("id"), "target_file": rel, "target_component": component,
                    "operation": "delete" if rel not in current else "modify" if baseline.get(rel) else "create", "reason": "Detected repository change since SEE baseline.",
                    "new_content": content, "change_level": plan.get("change_classification", {}).get("overall_level", "L1")})
        return edits

    def _missing_plan_fields(self, plan: dict[str, Any]) -> list[str]:
        reason = " ".join(plan.get("status_reasons", []))
        missing = []
        for field in ("repo_profile.framework", "repo_profile.styling_system", "target_surface"):
            if field.split(".")[-1].replace("_", " ") in reason.lower():
                missing.append(field)
        if not missing and plan.get("status") == "insufficient_context":
            missing = ["target page, route, or component"]
        return missing

    def _action(self, kind: str, task_id: str, message: str, required: list[str]) -> dict[str, Any]:
        return {"type": kind, "tool": "run_ui_task" if kind != "DONE" else None, "task_id": task_id,
                "message": message, "required_input": list(required)}

    def _recoverable(self, task_id: str | None, phase: str, status: str, code: str, summary: str,
                     cause: str, missing: list[str], verbosity: str) -> dict[str, Any]:
        action = {"type": "PROVIDE_INPUT", "tool": "run_ui_task", "task_id": task_id,
                  "message": "Provide a non-empty UI request to begin.", "required_input": ["request"]}
        return {"task_id": task_id, "status": status, "phase": phase, "summary": summary,
                "next_action": action, "warnings": [], "artifact_refs": {}, "code": code,
                "cause": cause, "missing": missing}

    def _envelope(self, s: dict[str, Any], store: TaskStore, summary: str, action: dict[str, Any],
                  verbosity: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        completed_phase = (s.get("phase_history") or [{}])[-1].get("phase", s.get("current_phase", "SEE"))
        value: dict[str, Any] = {"task_id": s.get("task_id"), "status": s.get("public_status", "RUNNING"),
            "phase": completed_phase, "summary": summary[:600], "next_action": action,
            "warnings": [], "artifact_refs": dict(s.get("artifact_refs", {}))}
        if extra:
            extra = dict(extra)
            if isinstance(extra.get("artifact_refs"), dict):
                value["artifact_refs"].update(extra.pop("artifact_refs"))
            value.update(extra)
        if value["status"] in {"NEEDS_INPUT", "NEEDS_PERMISSION", "BLOCKED", "PARTIAL", "DEVIATED", "FAILED"}:
            issue = s.get("last_error") or {}
            warning = issue.get("cause") or issue.get("message") or value.get("cause")
            if warning:
                value["warnings"] = [str(warning)]
        if verbosity in {"standard", "full"}:
            value["key_findings"] = self._findings(store, s)
            value["key_decisions"] = self._decisions(store, s)
            value["key_issues"] = self._issues(store, s)
            value["affected_surfaces"] = self._affected(store, s)
            value["gate_result"] = self._gate_result(store, s)
            value["selected_knowledge_ids"] = self._knowledge_ids(store, s)
            value["change_summary"] = self._change_summary(store, s)
            value["verification_summary"] = self._verification_summary(store, s)
        if verbosity == "full":
            value["phase_artifacts"] = self._phase_artifacts(store, s)
        return value

    def _artifact(self, store: TaskStore, s: dict[str, Any], key: str) -> Any:
        return store.load_ref(s.get("artifact_refs", {}).get(key))

    def _findings(self, store: TaskStore, s: dict[str, Any]) -> list[Any]:
        plan = self._artifact(store, s, "modification_plan") or {}
        return list(plan.get("diagnosis", {}).get("issues", []))[:8]

    def _decisions(self, store: TaskStore, s: dict[str, Any]) -> list[Any]:
        plan = self._artifact(store, s, "modification_plan") or {}
        return list(plan.get("strategy", {}).get("decisions", []))[:8]

    def _issues(self, store: TaskStore, s: dict[str, Any]) -> list[Any]:
        report = self._artifact(store, s, "verification_report") or {}
        return list(report.get("issues", []))[:8]

    def _affected(self, store: TaskStore, s: dict[str, Any]) -> list[Any]:
        context = self._artifact(store, s, "ui_context") or {}
        return context.get("affected_surfaces", [])[:20]

    def _gate_result(self, store: TaskStore, s: dict[str, Any]) -> Any:
        gate = self._artifact(store, s, "execution_gate")
        plan = self._artifact(store, s, "modification_plan") or {}
        return gate or plan.get("planning_gate")

    def _knowledge_ids(self, store: TaskStore, s: dict[str, Any]) -> list[str]:
        kp = self._artifact(store, s, "knowledge_plan") or {}
        vals = kp.get("selected_knowledge", []) or []
        ids = [x.get("id", "") for x in vals if isinstance(x, dict) and x.get("id")]
        packs = kp.get("selected_packs", {})
        if isinstance(packs, dict):
            for group in packs.values():
                if isinstance(group, list):
                    ids.extend(x.get("id", "") for x in group if isinstance(x, dict) and x.get("id"))
        return list(dict.fromkeys(ids))[:30]

    def _change_summary(self, store: TaskStore, s: dict[str, Any]) -> Any:
        report = self._artifact(store, s, "implementation_report") or {}
        return {k: report.get(k) for k in ("status", "chunks_applied", "chunks_pending", "files_modified") if k in report}

    def _verification_summary(self, store: TaskStore, s: dict[str, Any]) -> Any:
        report = self._artifact(store, s, "verification_report") or {}
        return {k: report.get(k) for k in ("status", "final_gate", "runtime_state", "limitations", "warnings") if k in report}

    def _phase_artifacts(self, store: TaskStore, s: dict[str, Any]) -> dict[str, Any]:
        result = {}
        completed_phase = (s.get("phase_history") or [{}])[-1].get("phase", s.get("current_phase"))
        allowed = {
            "SEE": {"repo_profile", "existing_ui_profile", "preservation_profile", "ui_context", "orchestration_decision"},
            "KNOW": {"knowledge_plan"},
            "THINK": {"modification_plan", "verification_contract"},
            "DO": {"execution_gate", "implementation_report"},
            "CHECK": {"runtime_capabilities", "verification_report"},
            "DONE": set(s.get("artifact_refs", {})),
        }.get(completed_phase, set())
        for key, ref in s.get("artifact_refs", {}).items():
            if key not in allowed:
                continue
            try:
                result[key] = store.load_ref(ref)
            except (OSError, ValueError):
                result[key] = {"unavailable": True, "ref": ref}
        return result


_CORE = TaskOrchestrator()


def run_ui_task(task_id: str | None = None, request: str | None = None, repo_path: str | None = None,
                user_message: str | None = None, verbosity: str = "compact") -> dict[str, Any]:
    return _CORE.run_ui_task(task_id, request, repo_path, user_message, verbosity)


def orchestrate_ui(request: dict[str, Any]) -> dict[str, Any]:
    return _CORE.orchestrate_ui(request)
