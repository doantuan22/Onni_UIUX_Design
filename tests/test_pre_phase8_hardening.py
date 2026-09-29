"""Comprehensive verification suite for Pre-Phase 8 Hardening (P0.5 & P1.1 to P1.7)."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest import mock

# Set up paths
import _paths
REPO_ROOT = _paths.REPO_ROOT
PLUGIN_DIR = _paths.PACKAGE_ROOT
if str(PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(PLUGIN_DIR))

from uiux import api
from uiux.engine.knowledge_router.intent import classify_task_intent, classify_task_intents
from uiux.runtime.interaction import (
    execute_interaction_scenario,
    validate_scenario_spec,
    verify_target_fixture_selectors,
)


class PrePhase8HardeningTests(unittest.TestCase):
    def setUp(self):
        self.target_a = REPO_ROOT / "development" / "fixtures" / "targets" / "target-a-static"
        self.target_b = REPO_ROOT / "development" / "fixtures" / "targets" / "target-b-react"

    # --- P1.1: Compound Intent Classifier ---
    def test_compound_intent_classification(self):
        """Compound intents are recognized with primary and secondary classification."""
        prompt = "Make responsive animated sidebar with smooth drawer transition"
        res = classify_task_intents(prompt)

        self.assertEqual(res["primary_intent"], "navigation_ux")
        self.assertIn("responsive_fix", res["secondary_intents"])
        self.assertIn("motion", res["secondary_intents"])
        self.assertTrue(res["compound"])

        # Backward compatibility for single classify_task_intent
        self.assertEqual(classify_task_intent(prompt), "navigation_ux")

    def test_motion_keyword_coverage(self):
        """All required motion keywords are recognized by classifier."""
        keywords = [
            "animate", "animated", "animation", "animations",
            "transition", "transitions", "motion", "stagger",
            "reveal", "scroll reveal", "entrance", "exit",
            "page transition", "layout animation", "micro-interaction",
        ]
        for kw in keywords:
            prompt = f"Please add smooth {kw} to the cards"
            res = classify_task_intents(prompt)
            self.assertIn("motion", res["all_intents"], f"Failed to detect motion keyword '{kw}'")

    # --- P1.2: Framework-Specific Motion Routing ---
    def test_framework_specific_motion_routing_with_framer(self):
        """Projects with Framer Motion dependency route tech.motion."""
        repo_profile = {
            "framework": {"name": "react", "version": "18.2.0"},
            "dependencies": {"react": "^18.2.0", "framer-motion": "^10.0.0"},
            "motion_library": "framer-motion",
        }
        plan = api.build_knowledge_plan(
            user_request="Add smooth animated transitions to cards",
            repo_profile=repo_profile,
            workflow="existing-ui",
        )
        selected_ids = [k["id"] for k in plan.get("selected_knowledge", [])]
        self.assertIn("tech.motion", selected_ids)
        self.assertIn("motion.fade-up", selected_ids)

    def test_framework_specific_motion_routing_without_library(self):
        """Projects without motion library route native CSS without adding dependencies."""
        repo_profile = {
            "framework": {"name": "static_html", "version": None},
            "dependencies": {},
        }
        plan = api.build_knowledge_plan(
            user_request="Add smooth animated transitions to cards",
            repo_profile=repo_profile,
            workflow="existing-ui",
        )
        selected_ids = [k["id"] for k in plan.get("selected_knowledge", [])]
        self.assertIn("tech.css", selected_ids)
        self.assertNotIn("tech.motion", selected_ids)

    # --- P1.3 & P1.4: Domain Auto-Detection and Subtopics ---
    def test_domain_auto_detection_from_repo_profile(self):
        """Domain is inferred from repo routes and components when not explicitly passed."""
        repo_profile = {
            "routes": ["/dashboard", "/workloads", "/clusters", "/analytics"],
            "components": ["ClusterTable", "MetricsCard"],
        }
        plan = api.build_knowledge_plan(
            user_request="Modernize layout and improve density",
            repo_profile=repo_profile,
            workflow="existing-ui",
        )
        domain_ctx = plan.get("domain_context", {})
        primary = domain_ctx.get("primary", {})
        self.assertEqual(primary.get("domain"), "saas_ai")

    def test_domain_subtopics_to_actual_knowledge(self):
        """Domain subtopics map to actual catalog knowledge entries."""
        plan = api.build_knowledge_plan(
            user_request="Build SaaS dashboard with pricing tier comparisons",
            workflow="greenfield",
        )
        selected_ids = [k["id"] for k in plan.get("selected_knowledge", [])]
        self.assertIn("screen.dashboard", selected_ids)
        self.assertIn("screen.pricing", selected_ids)

    # --- P0.5: Actual Knowledge Catalog Retrieval & Planner Consumption ---
    def test_router_selects_comprehensive_catalog_categories(self):
        """Knowledge Router selects screen, layout, interaction, effect, style, typography, recipe, motion."""
        plan = api.build_knowledge_plan(
            user_request="Create responsive dashboard with glassmorphism sidebar, search filter, and animated skeleton loading states",
            workflow="greenfield",
        )
        selected = plan.get("selected_knowledge", [])
        categories = {k.get("category") for k in selected}

        # Must cover key design catalog categories
        self.assertIn("screens", categories)
        self.assertIn("layouts", categories)
        self.assertIn("interactions", categories)
        self.assertIn("effects", categories)
        self.assertIn("motion", categories)
        self.assertIn("components", categories)

        # Check contract fields for each entry
        for k in selected:
            self.assertIn("id", k)
            self.assertIn("category", k)
            self.assertIn("name", k)
            self.assertIn("reason", k)
            self.assertIn("priority", k)
            self.assertIn("source", k)
            self.assertIn("reference", k)
            self.assertIn("relevance", k)
            self.assertIn("required", k)

    def test_planner_consumes_routed_knowledge(self):
        """Planner consumes routed knowledge and incorporates references into steps."""
        know_plan = api.build_knowledge_plan(
            user_request="Build dashboard with modal dialog and search filter",
            workflow="greenfield",
        )
        plan = api.plan_modification(
            user_request="Build dashboard with modal dialog and search filter",
            workflow="greenfield",
            knowledge_plan=know_plan,
        )
        knowledge_ctx = plan.get("knowledge", {})
        self.assertTrue(len(knowledge_ctx.get("selected_knowledge", [])) > 0)
        self.assertTrue(len(knowledge_ctx.get("routed_catalog_ids", [])) > 0)

        # Implementation steps carry guidance references
        steps = plan.get("implementation_steps", [])
        self.assertTrue(len(steps) > 0)
        first_step = steps[0]
        self.assertIn("guidance_references", first_step)

    # --- P1.5: Executable Scenarios in Validation Handoff ---
    def test_executable_scenarios_in_validation_handoff(self):
        """Validation handoff contains executable scenario specifications."""
        know_plan = api.build_knowledge_plan(
            user_request="Build workload dashboard with search filter, sidebar drawer, and modal form",
            workflow="greenfield",
        )
        plan = api.plan_modification(
            user_request="Build workload dashboard with search filter, sidebar drawer, and modal form",
            workflow="greenfield",
            knowledge_plan=know_plan,
        )
        handoff = api.build_validation_handoff(plan)
        scenarios = handoff.get("scenarios", [])
        self.assertTrue(len(scenarios) >= 3, "Expected at least 3 scenarios generated")

        scenario_ids = [s["id"] for s in scenarios]
        self.assertIn("scenario_smoke_test", scenario_ids)
        self.assertIn("scenario_responsive_viewport", scenario_ids)
        self.assertIn("scenario_accessibility_audit", scenario_ids)

    # --- P1.6 & UI State Validation: Interaction Runner ---
    def test_interaction_runner_fixture_verification_pass(self):
        """Interaction runner validates selectors and states on Target B."""
        scenario = {
            "id": "scenario_target_b_dashboard",
            "actions": [
                {"action": "click", "selector": "#menu-toggle-btn"},
                {"action": "fill", "selector": "#search-input", "value": "auth"},
                {"action": "click", "selector": ".chip[data-filter='all']"},
                {"action": "click", "selector": "#open-new-deployment-btn"},
                {"action": "press", "key": "Escape"},
            ],
            "expected_states": ["loading", "empty", "error", "data"],
        }
        res = verify_target_fixture_selectors(self.target_b, scenario)
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(len(res["unresolved_selectors"]), 0)
        self.assertIn("loading", res["states_verified"])
        self.assertIn("empty", res["states_verified"])
        self.assertIn("error", res["states_verified"])

    def test_interaction_runner_unresolved_selector_never_fakes_pass(self):
        """Interaction runner fails with UNRESOLVED_SELECTOR when target element is missing."""
        scenario = {
            "id": "scenario_target_b_missing_selector",
            "actions": [
                {"action": "click", "selector": "#non-existent-button-xyz"},
            ],
            "expected_states": ["data"],
        }
        res = verify_target_fixture_selectors(self.target_b, scenario)
        self.assertEqual(res["status"], "FAILED")
        self.assertEqual(res["reason"], "UNRESOLVED_SELECTOR")
        self.assertEqual(len(res["unresolved_selectors"]), 1)

    def test_interaction_runner_does_not_claim_live_pass_without_action_executor(self):
        scenario = {"id": "scenario_target_b_live", "actions": [{"action": "click", "selector": "#menu-toggle-btn"}]}
        ready = {"playwright": {"runtime_state": {"state": "READY"}}}
        with mock.patch("uiux.runtime.interaction.capabilities.detect", return_value=ready):
            result = execute_interaction_scenario(scenario, self.target_b, "http://localhost")
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["error_code"], "LIVE_INTERACTION_EXECUTOR_UNAVAILABLE")

    # --- P1.7: Manifest Path Validation in Self Test ---
    def test_self_test_verifies_manifest_paths(self):
        """self_test verifies all declared manifest resources exist."""
        res = api.self_test()
        manifest_check = next(c for c in res["checks"] if c["id"] == "manifest")
        self.assertEqual(manifest_check["status"], "PASS")
        self.assertIn("all declared resource paths verified", manifest_check["message"])


if __name__ == "__main__":
    unittest.main()
