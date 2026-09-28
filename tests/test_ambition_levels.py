"""Ambition levels (Refine / Elevate / Reimagine) on top of the L1/L2/L3 change budget.

Upgrade requests on an existing UI resolve to ELEVATE: page composition becomes evolvable (L2) while the
palette, brand, app shell, navigation and architecture stay protected and L3 stays denied. Conservative
phrasing and local scope resolve to REFINE; explicit redesign and greenfield to REIMAGINE.
See plugins/ui-engineering/workflows/ambition-levels.md.
"""
from __future__ import annotations

import json
import unittest

import _paths
from uiux import api
from uiux.engine import preservation
from uiux.engine.existing_ui.preservation_profile import build_preservation_profile
from uiux.engine.modification_planner.change_classifier import classify_changes

ROOT = _paths.PACKAGE_ROOT
EXISTING_REPO = {"files": ["src/app/page.tsx", "src/components/Hero.tsx", "src/components/Nav.tsx",
                           "src/components/Footer.tsx", "src/app/globals.css", "tailwind.config.ts"]}


def _orchestrate(prompt: str, **extra) -> dict:
    return api.orchestrate_ui({"user_request": prompt, "repo_context": EXISTING_REPO, **extra})


class OrchestratorAmbitionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema_doc = json.loads((ROOT / "schemas/orchestrator.schema.json").read_text(encoding="utf-8"))

    def test_upgrade_requests_resolve_to_elevate(self) -> None:
        for prompt in ("nâng cấp giao diện trang chủ", "làm đẹp giao diện giúp tôi", "modernize the UI",
                       "make it look premium and less generic", "upgrade the landing page"):
            with self.subTest(prompt=prompt):
                res = _orchestrate(prompt)
                self.assertEqual(res["workflow"], "existing-ui")
                self.assertEqual(res["ambition"], "elevate")
                self.assertEqual(res["allowed_change_level"]["max_level"], "L2")
                self.assertEqual(res["allowed_change_level"]["local_structural_change"], "allowed")
                self.assertEqual(res["protected_properties"]["page_composition"], "evolvable")
                self.assertTrue(res["allow_motion_library"])
                self.assertEqual(res["next_action"]["step"], "execute_elevated_redesign")
                self.assertIn("skills/design-direction", res["required_skills"])
                self.assertIn("motion", res["required_knowledge"])
                props = self.schema_doc["definitions"]["OrchestratorOutput"]["properties"]
                self.assertIn(res["ambition"], props["ambition"]["enum"])
                self.assertIn(res["protected_properties"]["page_composition"],
                              self.schema_doc["definitions"]["ProtectedProperties"]["properties"]["page_composition"]["enum"])

    def test_elevate_keeps_identity_protected_and_l3_denied(self) -> None:
        res = _orchestrate("làm đẹp giao diện giúp tôi")
        props = res["protected_properties"]
        self.assertEqual(props["color_palette"], "locked")
        self.assertEqual(props["brand_identity"], "locked")
        self.assertEqual(props["overall_layout_identity"], "protected")
        self.assertEqual(props["navigation_model"], "protected")
        self.assertEqual(props["information_architecture"], "protected")
        self.assertEqual(res["allowed_change_level"]["major_redesign"], "explicit_user_permission_only")
        self.assertFalse(res["permissions_detail"]["palette_editable"])

    def test_conservative_phrasing_wins_over_upgrade_words(self) -> None:
        for prompt in ("nâng cấp giao diện nhưng giữ nguyên bố cục", "polish the dashboard, keep the current look",
                       "làm đẹp nhưng chỉ tinh chỉnh nhẹ", "improve the UI with minimal changes"):
            with self.subTest(prompt=prompt):
                res = _orchestrate(prompt)
                self.assertEqual(res["ambition"], "refine")
                self.assertEqual(res["allowed_change_level"]["max_level"], "L1")
                self.assertEqual(res["protected_properties"]["page_composition"], "protected")
                self.assertFalse(res["allow_motion_library"])

    def test_narrow_or_local_requests_stay_refine(self) -> None:
        for prompt in ("fix the button padding", "improve responsive layout on mobile", "fix contrast for a11y"):
            with self.subTest(prompt=prompt):
                self.assertEqual(_orchestrate(prompt)["ambition"], "refine")

    def test_explicit_redesign_and_greenfield_reimagine(self) -> None:
        self.assertEqual(_orchestrate("full redesign of the marketing site")["ambition"], "reimagine")
        res = api.orchestrate_ui({"user_request": "Build a landing page for our new product",
                                  "repo_context": {"files": ["main.py", "README.md"]}})
        self.assertEqual(res["workflow"], "greenfield")
        self.assertEqual(res["ambition"], "reimagine")

    def test_unknown_state_is_refine(self) -> None:
        res = api.orchestrate_ui({"user_request": "modernize the interface", "repo_context": None})
        self.assertEqual(res["workflow"], "unknown")
        self.assertEqual(res["ambition"], "refine")
        self.assertEqual(res["allowed_change_level"]["max_level"], "L1")

    def test_structured_ambition_cannot_self_grant_reimagine(self) -> None:
        res = _orchestrate("update the pricing page", explicit_permissions={"ambition": "reimagine"})
        self.assertEqual(res["ambition"], "elevate")
        self.assertNotEqual(res["allowed_change_level"]["max_level"], "L3")
        res = _orchestrate("modernize the UI", explicit_permissions={"ambition": "refine"})
        self.assertEqual(res["ambition"], "refine")

    def test_resolve_ambition_contract(self) -> None:
        self.assertEqual(preservation.resolve_ambition("existing-ui", "modernize", "component", False), "refine")
        self.assertEqual(preservation.resolve_ambition("existing-ui", "anything", "page", True), "reimagine")
        self.assertEqual(preservation.resolve_ambition("existing-ui", "rename a label", "page", False), "refine")


class PlannerAndGuardAmbitionTests(unittest.TestCase):
    def test_preservation_profile_carries_ambition(self) -> None:
        profile = build_preservation_profile({}, {"ambition": "elevate"})
        self.assertEqual(profile["ambition"], "elevate")
        self.assertEqual(profile["protected_design"]["page_composition"]["policy"], "evolvable")
        self.assertEqual(profile["protected_design"]["color_palette"]["policy"], "locked")
        self.assertEqual(profile["allowed_changes"]["L2"]["policy"], "allowed")
        self.assertEqual(build_preservation_profile({}, {"ambition": "reimagine"})["ambition"], "elevate")
        self.assertEqual(build_preservation_profile({}, None)["ambition"], "refine")

    def test_elevate_recomposition_is_an_authorized_l2_change(self) -> None:
        surface = {"components": ["Hero"]}
        elevated = classify_changes("reorganize the sections of the home page", surface,
                                    preservation_profile={"ambition": "elevate"})
        self.assertFalse(elevated["has_unjustified_l2"])
        self.assertEqual(elevated["overall_level"], "L2")
        refined = classify_changes("reorganize the sections of the home page", surface, preservation_profile={})
        self.assertTrue(refined["has_unjustified_l2"])

    def test_guard_accepts_direction_as_l2_trace_and_rejects_content_loss(self) -> None:
        profile = build_preservation_profile({}, {"ambition": "elevate"})
        ok = api.evaluate_preservation(profile, {"level": "L2", "design_direction": "asymmetric split + hairline system"})
        self.assertNotIn("L2_JUSTIFICATION_TRACE", [v["rule"] for v in ok["violations"]])
        lost = api.evaluate_preservation(profile, {"level": "L2", "design_direction": "bento",
                                                   "content_changes": {"removed": ["FAQ section"]}})
        self.assertEqual(lost["status"], "fail")
        self.assertIn("CONTENT_PRESERVATION", [v["rule"] for v in lost["violations"]])


class MotionLibraryPolicyTests(unittest.TestCase):
    CAP = "motion.m4-pinned-section"

    def test_sanctioned_library_is_recorded_as_new_dependency(self) -> None:
        res = api.resolve_technology([self.CAP], [], False, True)
        self.assertEqual(res["assignments"][self.CAP]["technology"], "tech.gsap")
        self.assertEqual(res["new_dependencies"], ["tech.gsap"])

    def test_installed_library_is_reused(self) -> None:
        res = api.resolve_technology([self.CAP], ["framer-motion"], False, True)
        self.assertEqual(res["new_dependencies"], [])
        self.assertEqual(res["existing_reused"], ["tech.motion"])

    def test_without_sanction_no_library_is_added(self) -> None:
        res = api.resolve_technology([self.CAP], [], False, False)
        self.assertEqual(res["new_dependencies"], [])

    def test_only_one_motion_library(self) -> None:
        from uiux.knowledge import catalog
        entries, _ = catalog.load()
        motion_caps = [cid for cid, e in sorted(entries.items()) if isinstance(e.get("technology"), dict)
                       and set(catalog._as_list(e["technology"]["preferred"])) & {"tech.motion", "tech.gsap"}]
        res = api.resolve_technology(motion_caps, [], False, True)
        self.assertLessEqual(len(set(res["new_dependencies"]) & {"tech.motion", "tech.gsap"}), 1)


class AmbitionDocsTests(unittest.TestCase):
    def test_controller_and_workflows_reference_ambition(self) -> None:
        doc = (ROOT / "workflows/ambition-levels.md").read_text(encoding="utf-8")
        for phrase in ("Elevate contract", "Content inventory", "signature moves", "allow_motion_library",
                       "prefers-reduced-motion", "React + Tailwind", "Next.js"):
            self.assertIn(phrase, doc)
        for rel in ("SKILL.md", "workflows/routing.md", "workflows/preservation-rules.md",
                    "workflows/existing-ui-workflow.md"):
            self.assertIn("ambition-levels.md", (ROOT / rel).read_text(encoding="utf-8"), rel)
        self.assertTrue((ROOT / "skills/design-direction/signature-moves.md").is_file())
        self.assertTrue((ROOT / "knowledge/visual-language/anti-slop/default-banlist.md").is_file())
        template = (ROOT / "templates/DESIGN-DIRECTION.md").read_text(encoding="utf-8")
        for key in ("ambition:", "thesis:", "signature_moves:", "banlist_exceptions:", "motion_library:"):
            self.assertIn(key, template)


if __name__ == "__main__":
    unittest.main()
