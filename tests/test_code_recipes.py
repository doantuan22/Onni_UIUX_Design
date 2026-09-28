"""Code recipes (knowledge/code-recipes) and suggest_recipes.

The registry must stay consistent with the recipe files, the signature moves and the banlist signal ids; an Elevate
rebuild of the generic Next.js fixture made from the recipes must keep all content, re-compose the sections and clear
the design signals. (The recipes also type-check with tsc --strict and render in a Next.js 15 + Tailwind 4 build;
that check needs npm and runs outside this suite.)
"""
from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import _paths
from uiux import api
from uiux.engine.ui_map import build_ui_map, diff_ui_maps
from uiux.engine.ui_map.signals import BANLIST_IDS

ROOT = _paths.PACKAGE_ROOT
RECIPES = ROOT / "knowledge/code-recipes"
INDEX = json.loads((RECIPES / "index.json").read_text(encoding="utf-8"))
BASE = _paths.REPO_ROOT / "development/fixtures/targets/target-c-next-tailwind"
OVERLAY = _paths.REPO_ROOT / "development/fixtures/targets/target-c-next-tailwind-elevated"
ROLES = {"navigation", "hero", "social-proof", "stats", "features", "steps", "pricing", "testimonials", "faq", "cta",
         "newsletter", "team", "gallery", "blog", "data-table", "dashboard-metrics", "form", "sidebar", "footer",
         "content"}


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _signature_moves() -> set[str]:
    text = (ROOT / "skills/design-direction/signature-moves.md").read_text(encoding="utf-8")
    return {_slug(m) for m in re.findall(r"^\| \*\*([^*]+)\*\*", text, re.M)}


def _files(root: Path, prefix: str = "") -> dict[str, str]:
    return {prefix + p.relative_to(root).as_posix(): p.read_text(encoding="utf-8")
            for p in sorted(root.rglob("*")) if p.is_file() and p.suffix in (".tsx", ".ts", ".css", ".json")}


def _map(contents: dict[str, str]) -> dict:
    return build_ui_map(".", {"files": sorted(contents), "file_contents": contents,
                              "package_json": json.loads(contents.get("package.json", "{}"))})


class RegistryTests(unittest.TestCase):
    def test_entries_are_complete_and_consistent(self) -> None:
        moves = _signature_moves()
        self.assertIn("asymmetric-split", moves)
        ids = [r["id"] for r in INDEX["recipes"]]
        self.assertEqual(len(ids), len(set(ids)))
        for recipe in INDEX["recipes"]:
            with self.subTest(recipe=recipe["id"]):
                path = RECIPES / recipe["file"]
                self.assertTrue(path.is_file(), recipe["file"])
                text = path.read_text(encoding="utf-8")
                self.assertIn(f"@recipe {recipe['id']}", text)
                self.assertIn(recipe["kind"], ("tokens", "section", "motion", "surface"))
                self.assertLessEqual(set(recipe["roles"]), ROLES)
                self.assertLessEqual(set(recipe["signature_moves"]), moves)
                self.assertLessEqual(set(recipe["replaces"]), set(BANLIST_IDS))
                self.assertLessEqual(set(recipe["dependencies"]), {"motion", "gsap"})
                self.assertEqual(recipe["client"], text.startswith('"use client";'))
                if "motion" in recipe["dependencies"]:
                    self.assertIn('from "motion/react"', text)
                    self.assertTrue(recipe.get("css_fallback"))
                if "gsap" in recipe["dependencies"]:
                    self.assertIn('from "gsap"', text)
                    self.assertIn("matchMedia", text)
                if recipe["kind"] in ("motion", "section") and re.search(r"animat|transition-transform|translate-|motion\.", text):
                    self.assertRegex(text, r"reduce|reduced-motion|motion-reduce|MotionConfig", "reduced-motion path")

    def test_every_recipe_file_is_registered(self) -> None:
        registered = {r["file"] for r in INDEX["recipes"]}
        on_disk = {p.relative_to(RECIPES).as_posix() for p in RECIPES.rglob("*") if p.suffix in (".tsx", ".css")}
        self.assertEqual(on_disk, registered)

    def test_banlist_doc_lists_every_signal_id(self) -> None:
        text = (ROOT / "knowledge/visual-language/anti-slop/default-banlist.md").read_text(encoding="utf-8")
        documented = set(re.findall(r"^\| `([a-z-]+)` \|", text, re.M))
        self.assertEqual(documented, set(BANLIST_IDS))

    def test_section_recipes_keep_full_width_in_flex_columns(self) -> None:
        for recipe in INDEX["recipes"]:
            text = (RECIPES / recipe["file"]).read_text(encoding="utf-8")
            self.assertNotRegex(text, r'className="mx-auto max-w-', recipe["id"])


class SuggestTests(unittest.TestCase):
    def test_suggestions_for_the_generic_fixture(self) -> None:
        if not BASE.is_dir():
            self.skipTest("fixture is repository-only")
        ui = _map(_files(BASE) | {"package.json": (BASE / "package.json").read_text(encoding="utf-8")})
        result = api.call_tool("suggest_recipes", {"ui_map": ui, "allow_motion_library": True})
        top = {(s["route"], s["role"]): s["candidates"][0]["id"] for s in result["sections"]}
        self.assertEqual(top[("/", "hero")], "hero-asymmetric-split")
        self.assertEqual(top[("/", "features")], "bento-features")
        self.assertEqual(top[("/", "pricing")], "pricing-emphasis")
        self.assertEqual(top[("/", "testimonials")], "testimonial-spotlight")
        self.assertEqual(top[("/", "faq")], "faq-split")
        self.assertEqual(top[("/", "cta")], "cta-band")
        hero = next(s for s in result["sections"] if s["role"] == "hero" and s["route"] == "/")
        self.assertIn("centered-hero", " ".join(hero["candidates"][0]["why"]))
        self.assertEqual(result["tokens"][0]["id"], "brand-derived-theme")
        entrance = next(m for m in result["motion"] if m["id"] == "hero-entrance")
        self.assertEqual((entrance["status"], entrance["install"]), ("needs_install", "npm install motion"))
        self.assertEqual(result["motion_library"], "motion")

    def test_dependency_policy(self) -> None:
        without = api.suggest_recipes(roles=["hero", "steps"])
        statuses = {m["id"]: m["status"] for m in without["motion"]}
        self.assertEqual(statuses["hero-entrance"], "css_fallback")
        self.assertEqual(statuses["pinned-steps-gsap"], "css_fallback")
        self.assertEqual(statuses["tactile-button"], "available")
        self.assertTrue(all("css_fallback" in m for m in without["motion"] if m["status"] == "css_fallback"))
        installed = api.suggest_recipes(roles=["hero", "steps"], existing_dependencies=["framer-motion"],
                                        allow_motion_library=True)
        statuses = {m["id"]: m["status"] for m in installed["motion"]}
        self.assertEqual(statuses["hero-entrance"], "available")
        self.assertEqual(statuses["pinned-steps-gsap"], "css_fallback")  # never a second library
        with_code = api.suggest_recipes(roles=["faq"], include_code=True)
        self.assertIn("@recipe faq-split", with_code["sections"][0]["candidates"][0]["code"])

    def test_shell_roles_are_not_redesigned(self) -> None:
        result = api.suggest_recipes(roles=["navigation", "footer", "hero"])
        self.assertEqual([s["role"] for s in result["sections"]], ["hero"])


@unittest.skipUnless(BASE.is_dir() and OVERLAY.is_dir(), "fixtures are repository-only")
class ElevatedFixtureTests(unittest.TestCase):
    """Base fixture vs. the same app rebuilt from the recipes (overlay + recipes mounted at components/recipes)."""

    @classmethod
    def setUpClass(cls) -> None:
        base = _files(BASE) | {"package.json": (BASE / "package.json").read_text(encoding="utf-8")}
        after = dict(base)
        after.update(_files(OVERLAY / "src", "src/"))
        after.update(_files(RECIPES / "react-tailwind", "src/components/recipes/"))
        cls.before, cls.after = _map(base), _map(after)
        cls.diff = diff_ui_maps(cls.before, cls.after)

    def test_content_is_preserved_and_elevate_bar_met(self) -> None:
        self.assertTrue(self.diff["content_preserved"], [r["content_removed"] for r in self.diff["routes"]])
        self.assertTrue(self.diff["elevate_bar"]["met"], self.diff["recomposition_ratio"])
        home = next(r for r in self.diff["routes"] if r["path"] == "/")
        self.assertEqual(home["order_before"], home["order_after"])
        self.assertGreaterEqual(home["sections_recomposed"], 6)

    def test_design_signals_are_cleared(self) -> None:
        home = next(r for r in self.diff["routes"] if r["path"] == "/")
        self.assertEqual(home["banlist_introduced"], [])
        for signal in ("centered-hero", "purple-gradient", "gradient-text", "blur-blobs", "equal-icon-cards",
                       "uniform-radius-shadow", "hover-scale", "low-contrast-body", "centered-everything",
                       "uniform-rhythm"):
            self.assertIn(signal, home["banlist_resolved"])
        # copy is kept under Elevate, so copy-level signals remain and are reported to the user
        self.assertLessEqual(set(home["banlist_remaining"]), {"hype-copy", "round-number-stats"})
        after_home = next(r for r in self.after["routes"] if r["path"] == "/")
        self.assertEqual(after_home["layouts"], ["src/app/layout.tsx"])  # app shell untouched

    def test_recipe_content_is_materialized_from_props(self) -> None:
        home = next(r for r in self.after["routes"] if r["path"] == "/")
        for item in ("h1:unlock the power of seamless automation", "h3:starter", "h3:pro", "action:upgrade",
                     "action:contact sales", "h3:fast", "h2:frequently asked questions"):
            self.assertIn(item, home["fingerprint"])


if __name__ == "__main__":
    unittest.main()
