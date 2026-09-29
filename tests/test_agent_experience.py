"""Tier 1 agent entrypoint, state, projection, doctor and schema contracts."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import _paths  # noqa: F401
from test_p2_reasoning import KNOWLEDGE, PRESERVATION, REPO, make_plan
from uiux import api
from uiux.task_orchestrator import TaskOrchestrator, TaskStore, _now


def scan_objects(schema, where, problems, top=False):
    if not isinstance(schema, dict):
        return
    if schema.get("type") == "object" and not top:
        desc = schema.get("description", "").lower()
        arbitrary = any(term in desc for term in ("arbitrary map", "open-ended map", "free-form map", "canonical artifact"))
        if not schema.get("properties") and not arbitrary:
            problems.append(where)
        if not desc:
            problems.append(where + " (missing description)")
    for key, child in schema.get("properties", {}).items():
        scan_objects(child, where + "." + key, problems)
    if "items" in schema:
        scan_objects(schema["items"], where + "[]", problems)


class AgentToolTests(unittest.TestCase):
    def test_new_tools_are_public_and_dispatchable(self):
        tools = {item["id"]: item for item in api.list_tools()}
        self.assertIn("run_ui_task", tools)
        self.assertIn("doctor", tools)
        self.assertEqual(tools["run_ui_task"]["input"]["properties"]["verbosity"]["default"], "compact")
        self.assertEqual(tools["run_ui_task"]["output"]["required"],
                         ["task_id", "status", "phase", "summary", "next_action", "warnings", "artifact_refs"])
        self.assertIn("DEFAULT", tools["run_ui_task"]["description"])

    def test_all_public_nested_objects_are_documented_or_open_maps(self):
        problems = []
        for tool in api.list_tools():
            if tool["visibility"] == "public":
                scan_objects(tool["input"], tool["id"], problems, top=True)
        self.assertEqual(problems, [])

    def test_edit_schema_matches_editor_contract(self):
        item = api.list_tools()
        edit_schema = next(t for t in item if t["id"] == "guard_edits")["input"]["properties"]["edits"]["items"]
        self.assertEqual(set(edit_schema["required"]), {"chunk_id", "target_file", "target_component", "operation", "reason", "new_content"})
        self.assertIn("planned_change_id", edit_schema["properties"])
        self.assertNotIn("unknown", edit_schema["properties"])

    def test_doctor_reports_core_and_runtime_impact_without_installing(self):
        with patch("uiux.runtime.capabilities.command_version", return_value={"status": "NOT_AVAILABLE", "version": None}), \
             patch("uiux.runtime.capabilities.detect") as detect, patch("uiux.api.self_test", return_value={"status": "PASS", "checks": []}), \
             patch("uiux.api.capability_map", return_value={"tools": {"run_ui_task": {}}}):
            detect.return_value = {
                "playwright": {"runtime_state": {"state": "NOT_DECLARED"}, "package_present": {"status": "NOT_AVAILABLE"}, "browser_ready": {"status": "UNKNOWN"}},
                "runtime": {"node": {"status": "NOT_AVAILABLE"}}, "project": {}, "browser": {}, "accessibility": {},
            }
            report = api.doctor(".")
        self.assertEqual(report["overall_status"], "PARTIAL")
        self.assertEqual(report["capabilities"]["P0_SEE"]["status"], "AVAILABLE")
        self.assertEqual(report["capabilities"]["browser_runtime"]["status"], "BLOCKED")
        self.assertTrue(any("cannot run" in item["impact"] for item in report["limitations"]))
        self.assertTrue(all(item.get("automatic_install") is False for item in report["next_actions"]))

    def test_sequential_single_entrypoint_handoff_and_completion(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            source = project / "src/components/Checkout.tsx"
            source.parent.mkdir(parents=True)
            source.write_text("<main>Before</main>", encoding="utf-8")
            profile = {**REPO, "files": ["src/components/Checkout.tsx"], "framework": {"name": "react-tailwind"}}
            plan = make_plan()
            with patch("uiux.api.analyze_repository", return_value=profile), \
                 patch("uiux.engine.ui_state.detect_ui_state", return_value={"ui_state": "EXISTING_UI", "confidence": 0.95}), \
                 patch("uiux.api.analyze_existing_ui", return_value={"schema_version": 1, "layout": {"pages": ["checkout"]}, "protected_components": ["GlobalNav"]}), \
                 patch("uiux.api.build_preservation_profile", return_value=PRESERVATION), \
                 patch("uiux.api.map_ui_structure", return_value={"schema_version": 1, "routes": [], "shell": {}, "components": [], "tokens": {}, "summary": {}}), \
                 patch("uiux.api.build_knowledge_plan", return_value=KNOWLEDGE), \
                 patch("uiux.api.plan_modification", return_value=plan), \
                 patch("uiux.api.detect_runtime", return_value={"playwright": {"runtime_state": {"state": "READY"}}}), \
                 patch("uiux.api.verify_implementation", return_value={"status": "PASS", "final_gate": "PASS", "repair": {"routes": []}}):
                first = api.run_ui_task(request="Improve checkout UI on mobile while keeping brand colors", repo_path=temp)
                self.assertEqual((first["phase"], first["status"]), ("SEE", "RUNNING"))
                second = api.run_ui_task(task_id=first["task_id"], repo_path=temp)
                self.assertEqual((second["phase"], second["status"]), ("KNOW", "RUNNING"))
                third = api.run_ui_task(task_id=first["task_id"], repo_path=temp)
                self.assertEqual((third["phase"], third["status"]), ("THINK", "RUNNING"))
                source.write_text("<main className='p-4'>After</main>", encoding="utf-8")
                fourth = api.run_ui_task(task_id=first["task_id"], repo_path=temp)
                self.assertEqual((fourth["phase"], fourth["status"]), ("DO", "RUNNING"))
                fifth = api.run_ui_task(task_id=first["task_id"], repo_path=temp)
                self.assertEqual((fifth["phase"], fifth["status"]), ("CHECK", "PARTIAL"))
                self.assertEqual(fifth["next_action"]["type"], "FIX_ENVIRONMENT")
                self.assertIn("implementation_report", fifth["artifact_refs"], fifth)
                self.assertTrue(fifth["artifact_refs"]["implementation_report"].endswith("implementation-report.json"))
                self.assertTrue(fifth["artifact_refs"]["verification_report"].endswith("verification-report.json"))
                session = TaskStore(temp).load(first["task_id"])
                self.assertEqual([x["phase"] for x in session["phase_history"]], ["SEE", "KNOW", "THINK", "DO", "CHECK"])

    def test_end_to_end_reaches_completed_when_runtime_evidence_passes(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            source = project / "src/components/Checkout.tsx"
            source.parent.mkdir(parents=True)
            source.write_text("<main>Before</main>", encoding="utf-8")
            profile = {**REPO, "files": ["src/components/Checkout.tsx"], "framework": {"name": "react-tailwind"}}
            plan = make_plan()
            with patch("uiux.api.analyze_repository", return_value=profile), \
                 patch("uiux.engine.ui_state.detect_ui_state", return_value={"ui_state": "EXISTING_UI", "confidence": 0.95}), \
                 patch("uiux.api.analyze_existing_ui", return_value={"schema_version": 1, "layout": {"pages": ["checkout"]}}), \
                 patch("uiux.api.build_preservation_profile", return_value=PRESERVATION), \
                 patch("uiux.api.map_ui_structure", return_value={"schema_version": 1, "routes": [], "shell": {}, "components": [], "tokens": {}, "summary": {}}), \
                 patch("uiux.api.build_knowledge_plan", return_value=KNOWLEDGE), \
                 patch("uiux.api.plan_modification", return_value=plan), \
                 patch("uiux.api.detect_runtime", return_value={"playwright": {"runtime_state": {"state": "READY"}}}):
                first = api.run_ui_task(request="Improve checkout UI on mobile", repo_path=temp)
                second = api.run_ui_task(task_id=first["task_id"], repo_path=temp)
                third = api.run_ui_task(task_id=first["task_id"], repo_path=temp)
                source.write_text("<main className='p-4'>After</main>", encoding="utf-8")
                fourth = api.run_ui_task(task_id=first["task_id"], repo_path=temp)
                self.assertEqual(fourth["phase"], "DO")
                evidence_dir = project / ".evidence/runtime-session"
                evidence_dir.mkdir(parents=True)
                viewports = plan["verification"]["viewports"]
                routes = plan["verification"].get("required_routes") or plan["verification"].get("pages") or ["/"]
                captures = [{"route": route, "viewport": viewport, "status": "CAPTURED"}
                            for route in routes for viewport in viewports]
                (evidence_dir / "manifest.json").write_text(json.dumps({"status": "COMPLETED", "captures": captures}), encoding="utf-8")
                fifth = api.run_ui_task(task_id=first["task_id"], repo_path=temp)
            self.assertEqual((fifth["phase"], fifth["status"], fifth["next_action"]["type"]),
                             ("CHECK", "COMPLETED", "DONE"))
            self.assertEqual(len([first, second, third, fourth, fifth]), 5)

    def test_standard_and_full_projection_add_details(self):
        with tempfile.TemporaryDirectory() as temp:
            profile = {**REPO, "files": []}
            with patch("uiux.api.analyze_repository", return_value=profile), \
                 patch("uiux.engine.ui_state.detect_ui_state", return_value={"ui_state": "GREENFIELD", "confidence": 0.9}), \
                 patch("uiux.api.map_ui_structure", return_value={"schema_version": 1, "routes": [], "shell": {}, "components": [], "tokens": {}, "summary": {}}):
                standard = api.run_ui_task(request="Create a landing page", repo_path=temp, verbosity="standard")
            self.assertIn("key_findings", standard)
            self.assertIn("affected_surfaces", standard)
            self.assertNotIn("phase_artifacts", standard)

        with tempfile.TemporaryDirectory() as temp:
            profile = {**REPO, "files": []}
            with patch("uiux.api.analyze_repository", return_value=profile), \
                 patch("uiux.engine.ui_state.detect_ui_state", return_value={"ui_state": "GREENFIELD", "confidence": 0.9}), \
                 patch("uiux.api.map_ui_structure", return_value={"schema_version": 1, "routes": [], "shell": {}, "components": [], "tokens": {}, "summary": {}}):
                full = api.run_ui_task(request="Create a landing page", repo_path=temp, verbosity="full")
            self.assertIn("repo_profile", full["phase_artifacts"])

    def test_compact_exposes_no_canonical_heavy_payloads(self):
        with tempfile.TemporaryDirectory() as temp:
            first = api.run_ui_task(request="", repo_path=temp)
            self.assertEqual(first["status"], "NEEDS_INPUT")
            self.assertIn("next_action", first)
            self.assertNotIn("modification_plan", first)
            self.assertIn("missing", first)

    def test_run_task_schema_errors_are_actionable(self):
        result = api.call_tool("run_ui_task", {"request": "Improve checkout", "verbosity": "verbose"})
        self.assertEqual(result["code"], "SCHEMA_VALIDATION_ERROR")
        self.assertEqual(result["field"], "verbosity")
        self.assertEqual(result["expected"], ["compact", "standard", "full"])
        self.assertEqual(result["next_action"]["type"], "PROVIDE_INPUT")
        self.assertIn("summary", result)

    def _seed_session(self, root: Path, phase: str, plan: dict | None = None):
        store = TaskStore(root)
        task_id = "uiux_task_0123456789abcdef"
        store.task_dir(task_id).mkdir(parents=True)
        refs = {
            "repo_profile": store.save(task_id, "repo-profile", REPO),
            "existing_ui_profile": store.save(task_id, "existing-ui-profile", {"protected_components": ["GlobalNav"]}),
            "preservation_profile": store.save(task_id, "preservation-profile", PRESERVATION),
            "knowledge_plan": store.save(task_id, "knowledge-plan", KNOWLEDGE),
        }
        context = {"repo_profile_ref": refs["repo_profile"], "existing_ui_profile_ref": refs["existing_ui_profile"],
                   "preservation_profile_ref": refs["preservation_profile"], "knowledge_plan_ref": refs["knowledge_plan"],
                   "workflow": "existing-ui", "ui_state": {"ui_state": "EXISTING_UI"}, "file_snapshot": {}}
        if plan is not None:
            refs["modification_plan"] = store.save(task_id, "modification-plan", plan)
            context["modification_plan_ref"] = refs["modification_plan"]
        session = {"task_id": task_id, "user_request": "Improve checkout UI", "repo_root": str(root),
                   "current_phase": phase, "internal_state": f"{phase}_PENDING", "public_status": "RUNNING",
                   "phase_history": [{"phase": p, "status": "COMPLETED", "at": _now()} for p in ("SEE", "KNOW") if p != phase],
                   "artifact_refs": refs, "pending_input": None, "pending_permission": None,
                   "repair_history": [], "last_error": None, "created_at": _now(), "updated_at": _now(),
                   "request_context": context}
        store.save_session(session)
        return store, task_id

    def test_needs_permission_blocks_do_until_explicit_user_message(self):
        with tempfile.TemporaryDirectory() as temp:
            blocked = make_plan()
            blocked["status"] = "blocked"
            blocked["status_reasons"] = ["L3 change level requires explicit permission."]
            blocked["planning_gate"]["permission_needed"] = ["L3_major_redesign_permission_required"]
            store, task_id = self._seed_session(Path(temp), "THINK")
            with patch("uiux.api.plan_modification", return_value=blocked), patch("uiux.api.build_validation_handoff", return_value={}):
                wait = api.run_ui_task(task_id=task_id, repo_path=temp)
            self.assertEqual((wait["status"], wait["phase"], wait["next_action"]["type"]),
                             ("NEEDS_PERMISSION", "THINK", "GRANT_PERMISSION"))
            with patch("uiux.api.plan_modification", return_value=make_plan()) as planner, patch("uiux.api.build_validation_handoff", return_value={}):
                resumed = api.run_ui_task(task_id=task_id, repo_path=temp,
                    user_message="I explicitly authorize the requested L3 change for checkout.")
            self.assertEqual((resumed["status"], resumed["phase"], resumed["next_action"]["type"]),
                             ("RUNNING", "THINK", "CALL_AGAIN"))
            self.assertIn("explicitly authorize", planner.call_args.kwargs["user_request"])
            self.assertEqual(TaskStore(temp).load(task_id)["current_phase"], "DO")

    def test_plan_deviation_is_persisted_and_routed_back_to_think(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "src/components/Checkout.tsx"
            source.parent.mkdir(parents=True)
            source.write_text("before", encoding="utf-8")
            plan = make_plan()
            store, task_id = self._seed_session(root, "DO", plan)
            session = store.load(task_id)
            session["request_context"]["file_snapshot"] = TaskOrchestrator()._snapshot(root)
            store.save_session(session)
            (root / "outside.txt").write_text("out of scope", encoding="utf-8")
            deviation = {"status": "DEVIATED", "ready_for_p4": False, "deviations": [{"type": "scope_expansion"}], "ledger": []}
            with patch("uiux.api.check_execution_gate", return_value={"status": "PASS"}), \
                 patch("uiux.api.guard_edits", return_value=deviation):
                result = api.run_ui_task(task_id=task_id, repo_path=temp)
            self.assertEqual((result["status"], result["phase"], result["next_action"]["type"]),
                             ("DEVIATED", "DO", "CALL_AGAIN"))
            saved = store.load(task_id)
            self.assertEqual(saved["current_phase"], "THINK")
            self.assertEqual(saved["repair_history"][-1]["cause"], "PLAN_DEVIATION")

    def test_p4_repair_routes_to_the_specified_phase(self):
        router = TaskOrchestrator()
        expected = {"IMPLEMENTATION_ERROR": "DO", "PLAN_ERROR": "THINK",
                    "UNDERSTANDING_ERROR": "SEE", "KNOWLEDGE_GAP": "KNOW"}
        for cause, phase in expected.items():
            with self.subTest(cause=cause):
                self.assertEqual(router._repair_route({"repair": {"routes": [{"root_cause": cause}]}}), (phase, cause))


if __name__ == "__main__":
    unittest.main()
