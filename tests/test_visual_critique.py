"""Visual critique loop: rubric validation, measured gates, verdicts, the critic subagent and the layout probe."""
from __future__ import annotations

import copy
import re
import unittest

import _paths
from uiux import api
from uiux.engine import critique
from uiux.runtime import browser
from uiux.runtime.probes import LAYOUT_PROBE_JS

ROOT = _paths.PACKAGE_ROOT


def _critique(scores: dict, issues: list | None = None, subject: str = "after") -> dict:
    return {"schema_version": 1, "subject": subject, "routes": ["/"],
            "scores": {d: (None if s is None else {"score": s, "evidence": f"desktop {d}: seen"})
                       for d, s in scores.items()},
            "issues": issues or [], "signature_moves_seen": ["asymmetric-split"], "content_concerns": []}


BEFORE = _critique({"hierarchy": 2, "composition": 2, "typography": 3, "color_surfaces": 2, "distinctiveness": 1,
                    "craft": 3, "responsiveness": 2, "motion": None}, subject="before")
GOOD = _critique({"hierarchy": 4, "composition": 4, "typography": 4, "color_surfaces": 4, "distinctiveness": 4,
                  "craft": 4, "responsiveness": 4, "motion": 4})
DIFF_OK = {"routes": [{"path": "/", "content_removed": [], "banlist_introduced": []}], "routes_removed": [],
           "content_preserved": True, "recomposition_ratio": 0.86, "elevate_bar": {"met": True}}


def _capture(width: int, overflow: int = 0, targets: int = 0, reduced: bool = False, infinite: int = 0) -> dict:
    cap = {"route": "/", "viewport": "mobile" if width < 640 else "desktop", "width": width, "status": "CAPTURED",
           "layout_probe": {"horizontal_overflow_px": overflow, "small_targets": {"count": targets},
                            "small_text": {"count": 0}, "above_fold": {"h1_visible": True, "primary_action_visible": True}}}
    if reduced:
        cap["reduced_motion"] = "reduce"
        cap["motion_probe"] = {"animations": {"infinite": infinite}, "effects": {"filter_blur": 1}}
    return cap


class ScoringTests(unittest.TestCase):
    def test_elevated_change_passes(self) -> None:
        result = api.call_tool("score_visual_critique", {
            "after": GOOD, "before": BEFORE, "ui_map_diff": DIFF_OK,
            "captures": [_capture(390), _capture(1440), _capture(1440, reduced=True)],
            "accessibility_scans": [{"route": "/", "viewport": "desktop", "status": "SCANNED", "violations": 0}]})
        self.assertEqual(result["verdict"], "pass", result["criteria"])
        self.assertEqual(result["score"]["after"], 4.0)
        self.assertGreater(result["score"]["delta"], 0.75)
        self.assertEqual(result["next_focus"], [])
        self.assertIn("Verdict: **pass**", result["markdown"])

    def test_motion_null_redistributes_weight(self) -> None:
        self.assertEqual(critique.weighted(BEFORE), round(
            sum(critique.WEIGHTS[d] * e["score"] for d, e in BEFORE["scores"].items() if e) /
            sum(critique.WEIGHTS[d] for d, e in BEFORE["scores"].items() if e), 2))

    def test_measured_gates_block_a_good_looking_score(self) -> None:
        diff = copy.deepcopy(DIFF_OK)
        diff["content_preserved"] = False
        diff["routes"][0]["content_removed"] = ["h2:frequently asked questions"]
        result = api.score_visual_critique(GOOD, BEFORE, diff, [_capture(390, overflow=47),
                                                                _capture(1440, reduced=True, infinite=1)])
        self.assertEqual(result["verdict"], "iterate")
        failed = {g["id"] for g in result["gates"] if not g["passed"]}
        self.assertEqual(failed, {"content_preserved", "no_horizontal_overflow", "reduced_motion_still"})
        self.assertEqual(result["issues"][0]["severity"], "blocker")
        self.assertTrue(any("frequently asked questions" in f for f in result["next_focus"]))

    def test_generic_result_iterates_then_stops(self) -> None:
        flat = _critique({"hierarchy": 3, "composition": 3, "typography": 3, "color_surfaces": 3, "distinctiveness": 2,
                          "craft": 3, "responsiveness": 3, "motion": None},
                         issues=[{"severity": "major", "dimension": "distinctiveness", "where": "/ features",
                                  "observation": "equal icon cards", "fix": "bento with a lead tile"}])
        first = api.score_visual_critique(flat, BEFORE, DIFF_OK, iteration=1)
        self.assertEqual(first["verdict"], "iterate")
        self.assertIn("equal icon cards", first["next_focus"][0])
        stalled = api.score_visual_critique(flat, BEFORE, DIFF_OK, iteration=2, previous_score=first["score"]["after"])
        self.assertEqual(stalled["verdict"], "stop")
        self.assertIn("no material progress", stalled["reason"])
        spent = api.score_visual_critique(flat, BEFORE, DIFF_OK, iteration=3, previous_score=2.0)
        self.assertEqual(spent["verdict"], "stop")

    def test_elevate_requires_real_improvement_and_refine_does_not(self) -> None:
        same = copy.deepcopy(GOOD)
        result = api.score_visual_critique(GOOD, same, DIFF_OK)
        self.assertFalse(next(c for c in result["criteria"] if c["id"] == "improvement")["passed"])
        refine = api.score_visual_critique(GOOD, same, None, ambition="refine")
        self.assertEqual(refine["verdict"], "pass")

    def test_invalid_critiques_are_rejected(self) -> None:
        bad = copy.deepcopy(GOOD)
        del bad["scores"]["craft"]
        with self.assertRaises(api.ToolError):
            api.call_tool("score_visual_critique", {"after": bad})
        no_evidence = copy.deepcopy(GOOD)
        no_evidence["scores"]["craft"]["evidence"] = " "
        with self.assertRaises(api.ToolError):
            api.score_visual_critique(no_evidence)
        out_of_range = copy.deepcopy(GOOD)
        out_of_range["scores"]["craft"]["score"] = 7
        with self.assertRaises(api.ToolError):
            api.score_visual_critique(out_of_range)


class CriticAgentTests(unittest.TestCase):
    def test_agent_definition(self) -> None:
        path = ROOT / "agents/visual-critic.md"
        text = path.read_text(encoding="utf-8")
        front = dict(line.split(": ", 1) for line in re.match(r"^---\n(.*?)\n---\n", text, re.S).group(1).splitlines())
        self.assertEqual(front["name"], "visual-critic")
        self.assertEqual({t.strip() for t in front["tools"].split(",")}, {"Read", "Glob", "Grep"})  # read-only
        for phrase in ("review/visual-critique.md", "before", "after", "JSON", "Do not read source code"):
            self.assertIn(phrase, text)

    def test_rubric_matches_engine(self) -> None:
        text = (ROOT / "review/visual-critique.md").read_text(encoding="utf-8")
        rows = dict(re.findall(r"^\| `([a-z_]+)` \| ([0-9.]+) \|", text, re.M))
        self.assertEqual({k: float(v) for k, v in rows.items()}, critique.WEIGHTS)
        self.assertAlmostEqual(sum(critique.WEIGHTS.values()), 1.0)


class LayoutProbeTests(unittest.TestCase):
    def test_probe_is_wired_into_the_runner(self) -> None:
        self.assertIn("horizontal_overflow_px", LAYOUT_PROBE_JS)
        self.assertIn("const LAYOUT=", browser.HELPER)
        self.assertIn("layout_probe:layout", browser.HELPER)
        self.assertNotIn("__LAYOUT__", browser.HELPER)
        with self.assertRaises(ValueError):
            browser.validate_options({"layout_probe": "yes"})
        self.assertEqual(browser.validate_options({"layout_probe": True}), {"layout_probe": True})


if __name__ == "__main__":
    unittest.main()
