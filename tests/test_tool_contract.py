"""Tool registry contract: entrypoints, input schemas, output contracts, annotations and the public API agree."""
from __future__ import annotations

import copy
import inspect
import json
import unittest

import _paths
from uiux import api
from uiux.core import registry, schema

ROOT = _paths.PACKAGE_ROOT
TOOLS = registry.tools()["tools"]


class RegistryTests(unittest.TestCase):
    def test_registry_is_structurally_valid(self) -> None:
        self.assertEqual(registry.check_tools(), [])
        self.assertEqual(registry.check_capability_map(), [])

    def test_no_duplicate_ids_or_entrypoints(self) -> None:
        ids = [t["id"] for t in TOOLS]
        self.assertEqual(len(ids), len(set(ids)))
        entrypoints = [t["entrypoint"] for t in TOOLS]
        self.assertEqual(len(entrypoints), len(set(entrypoints)))

    def test_entrypoints_exist_and_match_the_schema(self) -> None:
        for tool in TOOLS:
            with self.subTest(tool=tool["id"]):
                module, name = tool["entrypoint"].split(":")
                self.assertEqual(module, "uiux.api")
                self.assertIn(name, api.__all__)
                function = getattr(api, name)
                self.assertIs(api._DISPATCH[tool["id"]], function)
                signature = inspect.signature(function)
                self.assertEqual(set(signature.parameters), set(tool["input"]["properties"]))
                required = {n for n, p in signature.parameters.items() if p.default is inspect.Parameter.empty}
                self.assertEqual(required, set(tool["input"].get("required", [])))
                self.assertEqual(schema.check_schema(tool["input"]), [])

    def test_public_tools_match_the_api(self) -> None:
        public = {t["id"] for t in TOOLS if t["visibility"] == "public"}
        self.assertEqual(public, set(api._DISPATCH))
        self.assertTrue({"accessibility_scan", "capability_map", "self_test"} <= public)
        self.assertEqual([t["id"] for t in api.list_tools()], [t["id"] for t in TOOLS])

    def test_closed_vocabularies_follow_their_owners(self) -> None:
        from uiux.evals import runner
        from uiux.knowledge import registry as knowledge

        by_id = {t["id"]: t for t in TOOLS}
        suites = by_id["run_evals"]["input"]["properties"]["suites"]["items"]["enum"]
        self.assertEqual(suites, list(runner.ALL_SUITES))
        collections = [c for c in by_id["retrieve_knowledge"]["input"]["properties"]["collection"]["enum"] if c]
        self.assertEqual(collections, list(knowledge.COLLECTIONS))

    def test_annotations(self) -> None:
        writers = {t["id"] for t in TOOLS if not t["annotations"]["read_only"]}
        self.assertEqual(writers, {"run_runtime", "accessibility_scan", "run_ui_task"})
        for tool in TOOLS:
            notes = tool["annotations"]
            with self.subTest(tool=tool["id"]):
                self.assertEqual(notes["writes_to"], "none" if notes["read_only"] else "target-project")
                if notes["requires_node"] or notes["requires_browser"]:
                    self.assertTrue(notes["may_start_process"])
                    self.assertFalse(notes["deterministic"])
        pure = {"resolve_capabilities", "retrieve_knowledge", "resolve_technology", "run_evals", "validate_skill"}
        for tool_id in pure:
            notes = next(t for t in TOOLS if t["id"] == tool_id)["annotations"]
            self.assertEqual((notes["deterministic"], notes["network_access"], notes["may_start_process"]), (True, False, False))

    def test_registry_has_no_platform_metadata(self) -> None:
        text = json.dumps(registry.tools()).lower()
        for word in ("claude", "codex", "cline", "opencode", "copilot", "mcp"):
            self.assertNotIn(word, text)

    def test_checker_detects_broken_entries(self) -> None:
        broken = copy.deepcopy(registry.tools())
        broken["tools"].append(copy.deepcopy(broken["tools"][0]))
        broken["tools"][1]["annotations"]["read_only"] = "yes"
        broken["tools"][2]["entrypoint"] = "uiux.engine.technology:resolve"
        del broken["tools"][3]["input"]["additionalProperties"]
        broken["tools"][4]["annotations"]["filesystem_read"] = ["home-directory"]
        problems = "\n".join(registry.check_tools(broken))
        for fragment in ("duplicate id", "read_only must be boolean", "entrypoint must be uiux.api", "additionalProperties false",
                         "filesystem_read must use"):
            self.assertIn(fragment, problems)


class OutputContractTests(unittest.TestCase):
    """Cheap, side-effect free calls return every key promised by ``output.required``."""

    def test_output_required_keys(self) -> None:
        profile = json.loads((ROOT / "evals/resolver-scenarios/developer-tool.json").read_text(encoding="utf-8"))["profile"]
        fixture = ROOT / "evals/runtime-fixtures/playwright-ready"
        request = {"session_id": "contract", "base_url": "http://127.0.0.1:9", "routes": [{"page_id": "P", "route": "/"}],
                   "viewports": ["desktop"]}
        calls = {"resolve_capabilities": {"profile": profile}, "retrieve_knowledge": {"collection": "styles"},
                 "resolve_technology": {"capabilities": ["motion.m1-hover"]},
                 "analyze_design_quality": {"project": str(ROOT / "evals/fixtures/quality/restrained")},
                 "detect_runtime": {"project": str(fixture)},
                 "run_runtime": {"request": request, "project": str(fixture), "dry_run": True},
                 "accessibility_scan": {"request": request, "project": str(fixture), "dry_run": True},
                 "run_evals": {"suites": ["knowledge"]}, "capability_map": {}, "self_test": {}}
        for tool in TOOLS:
            if tool["id"] not in calls:
                continue
            with self.subTest(tool=tool["id"]):
                result = api.call_tool(tool["id"], calls[tool["id"]])
                self.assertEqual([k for k in tool["output"].get("required", []) if k not in result], [])
        self.assertFalse((fixture / ".evidence").exists(), "dry runs must not write evidence")


class PipelineToolSurfaceE2EContractTests(unittest.TestCase):
    """P0.3 Contract: Complete main pipeline reachable through api.call_tool without internal imports."""

    def test_pipeline_tool_surface_e2e_sequence(self) -> None:
        # Step 1: analyze_repository via tool surface
        repo_result = api.call_tool("analyze_repository", {
            "project": str(ROOT / "evals/runtime-fixtures/playwright-ready"),
        })
        self.assertIn("framework", repo_result)
        self.assertIn("styling_system", repo_result)

        # Step 2: orchestrate_ui via tool surface
        orchestration_request = {
            "user_goal": "Add responsive navigation drawer and visual polish",
            "task_intent": "L1_refinement",
            "requested_scope": "component",
            "repo_context": {"workspace_root": str(ROOT / "evals/runtime-fixtures/playwright-ready")},
        }
        orch_result = api.call_tool("orchestrate_ui", {"request": orchestration_request})
        self.assertIn("workflow", orch_result)
        self.assertIn("ui_state", orch_result)
        self.assertIn("next_action", orch_result)

        # Step 3: build_knowledge_plan via tool surface
        knowledge_plan = api.call_tool("build_knowledge_plan", {
            "repo_profile": repo_result,
            "user_request": orchestration_request["user_goal"],
            "workflow": orch_result["workflow"],
            "task_intent": "L1_refinement",
            "requested_scope": "component",
        })
        self.assertIn("selected_packs", knowledge_plan)
        self.assertIn("context_budget", knowledge_plan)

        # Step 4: plan_modification via tool surface
        mod_plan = api.call_tool("plan_modification", {
            "user_request": orchestration_request["user_goal"],
            "workflow": orch_result["workflow"],
            "repo_profile": repo_result,
            "knowledge_plan": knowledge_plan,
            "task_intent": "L1_refinement",
            "requested_scope": "component",
            "plan_only": True,
        })
        self.assertIn("blast_radius", mod_plan)
        self.assertIn("change_classification", mod_plan)
        self.assertIn("validation", mod_plan)

        # Step 5: build_validation_handoff via tool surface
        handoff = api.call_tool("build_validation_handoff", {"plan": mod_plan})
        self.assertIn("required_checks", handoff)
        self.assertIn("affected_viewports", handoff)
        self.assertIn("interactions", handoff)
        self.assertIn("accessibility", handoff)
        self.assertIn("preservation", handoff)


if __name__ == "__main__":
    unittest.main()
