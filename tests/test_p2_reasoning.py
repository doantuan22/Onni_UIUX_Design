"""P2 THINK: the modification plan carries diagnosis, strategy, impact, chunks and a planning gate."""
from __future__ import annotations

import unittest

import _paths  # noqa: F401
from uiux.engine.modification_planner.planner import ModificationPlanner

PRESERVATION = {
    "required": True,
    "allowed_changes": {"max_level": "L2"},
    "granular_permissions": {"palette": "locked", "brand": "locked", "layout": "protected", "navigation": "protected"},
}
REPO = {
    "framework": {"name": "react-tailwind"},
    "detected_domain": "ecommerce",
    "files": ["src/components/Checkout.tsx", "src/pages/cart.tsx"],
}
KNOWLEDGE = {
    "task_intent": "improve_ui",
    "selected_packs": {"domain": [{"id": "domain.ecommerce"}], "framework": [{"id": "framework.react-tailwind"}]},
    "selected_knowledge": [{"id": "recipe.consumer-app"}, {"id": "screen.checkout"}],
}


def make_plan(**overrides):
    args = dict(
        user_request="improve checkout UI on mobile, making it more modern",
        workflow="existing-ui",
        repo_profile=REPO,
        existing_ui_profile={"protected_components": ["GlobalNav", "BrandLogo"]},
        preservation_profile=PRESERVATION,
        knowledge_plan=KNOWLEDGE,
        requested_scope="component",
        task_intent="improve_ui",
    )
    args.update(overrides)
    return ModificationPlanner().plan(**args)


class ReasoningLayerTests(unittest.TestCase):
    def test_plan_keeps_legacy_contract_and_adds_p2_layer(self) -> None:
        plan = make_plan()
        for key in ("plan_id", "status", "affected_surface", "blast_radius", "implementation_steps"):
            self.assertIn(key, plan)
        for key in ("requirement_profile", "diagnosis", "strategy", "impact", "execution_chunks",
                    "verification", "planning_gate", "metadata"):
            self.assertIn(key, plan)
        self.assertEqual(plan["metadata"]["plan_id"], plan["plan_id"])

    def test_mobile_request_is_diagnosed_as_responsive(self) -> None:
        categories = {i["category"] for i in make_plan()["diagnosis"]["issues"]}
        self.assertIn("RESPONSIVE", categories)

    def test_valid_plan_passes_gate_and_has_chunks(self) -> None:
        plan = make_plan()
        self.assertEqual(plan["status"], "ready")
        self.assertEqual(plan["planning_gate"]["status"], "PASS")
        self.assertTrue(plan["execution_chunks"])
        self.assertIn("src/components/Checkout.tsx", plan["impact"]["affected_files"])

    def test_locked_properties_are_exposed(self) -> None:
        preservation = make_plan()["preservation"]
        self.assertEqual(set(preservation["locked"]), {"palette", "brand"})
        self.assertEqual(set(preservation["protected"]), {"layout", "navigation"})

    def test_blocked_plan_never_passes_gate(self) -> None:
        plan = make_plan(user_request="refactor database schema for the checkout")
        self.assertNotEqual(plan["status"], "ready")
        self.assertEqual(plan["planning_gate"]["status"], "BLOCKED")

    def test_insufficient_context_plan_is_blocked(self) -> None:
        plan = make_plan(repo_profile={})
        self.assertEqual(plan["status"], "insufficient_context")
        self.assertEqual(plan["planning_gate"]["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
