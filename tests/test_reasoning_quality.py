"""Tier 3 reasoning corpus: structured expectations, not exact prose snapshots."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

import _paths  # noqa: F401
from uiux.engine.modification_planner.semantic_requirements import analyze_semantic_requirements
from uiux.engine.modification_planner.planner import ModificationPlanner


ROOT = Path(__file__).resolve().parents[1]
CORPUS = json.loads((ROOT / "development/reasoning-cases.json").read_text(encoding="utf-8"))


def _target_names(req: dict) -> list[str]:
    values = (req.get("target_surfaces") or {}).get("value") or []
    return [str(item.get("name", "")).lower().replace(" ", "_") if isinstance(item, dict) else str(item).lower() for item in values]


class ReasoningCorpusTests(unittest.TestCase):
    def test_corpus_has_at_least_fifty_cases_and_twenty_vietnamese(self) -> None:
        self.assertGreaterEqual(len(CORPUS["cases"]), 50)
        self.assertGreaterEqual(sum(c["language"] == "VI" for c in CORPUS["cases"]), 20)

    def test_structured_expectations_for_every_case(self) -> None:
        for case in CORPUS["cases"]:
            with self.subTest(case=case["id"]):
                actual = analyze_semantic_requirements(case["request"], ui_context=case.get("context"))
                expected = case.get("expect", {})
                self.assertEqual(actual["language"], case["language"])
                self.assertEqual(actual["reasoning_mode"], "HEURISTIC_FALLBACK")
                self.assertIn(actual["confidence"], {"HIGH", "MEDIUM", "LOW"})
                for concern in expected.get("concerns", []):
                    self.assertIn(concern, actual["concerns"])
                if "task_type" in expected:
                    self.assertEqual(actual["task_type"]["value"], expected["task_type"])
                if "scope" in expected:
                    self.assertEqual(actual["scope"]["value"], expected["scope"])
                if "target" in expected:
                    aliases = {"product_listing": ("product", "products", "product_listing"),
                        "landing_page": ("landing", "landing_page", "home"),
                        "checkout": ("checkout", "thanh toan"), "cart": ("cart", "gio hang")}
                    self.assertTrue(any(alias in name for name in _target_names(actual) for alias in aliases.get(expected["target"], (expected["target"],))),
                        (case["id"], _target_names(actual), expected["target"]))
                if expected.get("target_unknown"):
                    self.assertEqual(actual["target_surfaces"]["state"], "UNKNOWN")
                if expected.get("ambiguous"):
                    self.assertTrue(actual["ambiguities"], case["id"])
                if "permission" in expected:
                    self.assertEqual(actual["redesign_intent"]["value"]["value"], expected["permission"])
                if "redesign" in expected:
                    self.assertEqual(actual["redesign_intent"]["value"]["value"], expected["redesign"])
                if expected.get("palette_locked"):
                    self.assertTrue(actual["preservation_intent"]["value"]["palette"], case["id"])
                if expected.get("palette_allowed"):
                    self.assertEqual(actual["permission_intent"]["palette_change"]["value"], "EXPLICITLY_ALLOWED")
                if expected.get("layout_allowed"):
                    self.assertEqual(actual["permission_intent"]["layout_change"]["value"], "EXPLICITLY_ALLOWED")
                if expected.get("framework_locked"):
                    self.assertTrue(actual["preservation_intent"]["value"]["framework"], case["id"])
                if expected.get("desktop_locked"):
                    self.assertTrue(actual["preservation_intent"]["value"]["desktop_layout"], case["id"])
                for required_keep in expected.get("must_keep", []):
                    self.assertIn(required_keep, [f["value"] for f in actual["must_keep"]], case["id"])

    def test_vi_cases_keep_redesign_permission_target_scoped(self) -> None:
        for request, expected_surface in (
            ("Thiết kế lại toàn bộ dashboard, có thể đổi màu và bố cục.", "dashboard"),
            ("Đập đi làm lại trang landing page này.", "landing_page"),
        ):
            with self.subTest(request=request):
                req = analyze_semantic_requirements(request)
                self.assertEqual(req["redesign_intent"]["value"]["value"], "EXPLICITLY_ALLOWED")
                self.assertTrue(any(expected_surface in n for n in _target_names(req)))
                self.assertNotEqual(req["scope"]["value"], "global")

    def test_vietnamese_preservation_does_not_grant_l3(self) -> None:
        req = analyze_semantic_requirements("Làm đẹp trang checkout nhưng giữ nguyên tông màu.")
        self.assertEqual(req["language"], "VI")
        self.assertTrue(req["preservation_intent"]["value"]["palette"])
        self.assertEqual(req["redesign_intent"]["value"]["value"], "NOT_AUTHORIZED")
        plan = ModificationPlanner().plan(user_request="Làm đẹp trang checkout nhưng giữ nguyên tông màu.",
            repo_profile={"framework": {"name": "react-tailwind"}, "files": ["src/pages/checkout.tsx"],
                "routes": [{"path": "/checkout", "name": "checkout"}]})
        self.assertNotEqual(plan["change_classification"]["overall_level"], "L3")
        self.assertEqual(plan["preservation"]["granular_permissions"]["palette"], "locked")

    def test_compound_vietnamese_keeps_all_distinct_concerns(self) -> None:
        req = analyze_semantic_requirements("Giữ layout desktop, sửa lỗi mobile của filter, đồng bộ button, và sửa focus state cho form tìm kiếm.")
        self.assertEqual(req["language"], "VI")
        self.assertTrue(req["preservation_intent"]["value"]["desktop_layout"])
        self.assertTrue({"responsive", "component_consistency", "accessibility", "interaction"} <= set(req["concerns"]))

    def test_ambiguous_multi_route_planning_requires_context(self) -> None:
        plan = ModificationPlanner().plan(user_request="Làm tốt hơn.", workflow="existing-ui",
            repo_profile={"framework": {"name": "react"}, "files": ["src/a.tsx", "src/b.tsx"],
                "routes": [{"path": "/checkout", "name": "checkout"}, {"path": "/cart", "name": "cart"}]})
        self.assertEqual(plan["status"], "insufficient_context")
        self.assertEqual(plan["affected_surface"]["files"], [])

    def test_chunk_and_diagnosis_completeness_gate(self) -> None:
        plan = ModificationPlanner().plan(user_request="Fix responsive checkout on mobile", workflow="existing-ui",
            repo_profile={"framework": {"name": "react"}, "files": ["src/Checkout.tsx"],
                "routes": [{"path": "/checkout", "name": "checkout"}]})
        self.assertTrue(plan["execution_chunks"])
        self.assertTrue(all(c["description"].strip() and c["expected_result"].strip() and c["scope"].strip()
            for c in plan["execution_chunks"]))
        self.assertTrue(all(i["description"].strip() for i in plan["diagnosis"]["issues"]))
        self.assertEqual(plan["reasoning_completeness"]["status"], "PASS", plan["reasoning_completeness"])


if __name__ == "__main__":
    unittest.main()
