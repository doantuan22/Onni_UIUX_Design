"""P1 KNOW: the router resolves framework/domain packs that live only in the knowledge catalog."""
from __future__ import annotations

import unittest

import _paths  # noqa: F401
from uiux.api import build_knowledge_plan


class CatalogBackedRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_knowledge_plan(
            repo_profile={"framework": {"name": "react-tailwind"}, "detected_domain": "ecommerce"},
            task_intent="improve_ui",
            user_request="Cải thiện nút checkout trong giỏ hàng",
            workflow="existing-ui",
        )
        self.packs = self.plan["selected_packs"]

    def test_framework_pack_comes_from_catalog(self) -> None:
        ids = [p["id"] for p in self.packs["framework"]]
        self.assertEqual(ids, ["framework.react-tailwind"])
        self.assertIn("version_guidance", self.packs["framework"][0])

    def test_domain_pack_is_selected(self) -> None:
        self.assertIn("domain.ecommerce", [p["id"] for p in self.packs["domain"]])

    def test_unknown_framework_falls_back_to_generic_pack(self) -> None:
        plan = build_knowledge_plan(
            repo_profile={"framework": {"name": "no-such-framework"}},
            task_intent="improve_ui",
            user_request="polish the header",
            workflow="existing-ui",
        )
        self.assertEqual([p["id"] for p in plan["selected_packs"]["framework"]], ["framework.fallback"])


if __name__ == "__main__":
    unittest.main()
