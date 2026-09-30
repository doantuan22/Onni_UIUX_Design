"""Tests for reference target projects and benchmark harness (P0.4)."""
import os
import sys
import unittest
from pathlib import Path

# Add plugins/ui-engineering and development to path
import _paths
REPO_ROOT = _paths.REPO_ROOT
PLUGIN_DIR = _paths.PACKAGE_ROOT
DEV_DIR = REPO_ROOT / "development"
for p in (PLUGIN_DIR, DEV_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from benchmark_harness import run_target_benchmark
import uiux.api as api


class BenchmarkTargetsTests(unittest.TestCase):
    def setUp(self):
        self.target_a = REPO_ROOT / "development" / "fixtures" / "targets" / "target-a-static"
        self.target_b = REPO_ROOT / "development" / "fixtures" / "targets" / "target-b-react"

    def test_target_a_static_pipeline_execution(self):
        """Target A Static executes all stages through benchmark harness."""
        self.assertTrue(self.target_a.is_dir(), "Target A directory must exist")
        self.assertTrue((self.target_a / "index.html").is_file())
        self.assertTrue((self.target_a / "styles.css").is_file())
        self.assertTrue((self.target_a / "app.js").is_file())

        task = "Create a responsive landing page hero and card layout with contact form"
        res = run_target_benchmark(self.target_a, task)

        self.assertIn(res["status"], ("INTEGRATION_VERIFIED", "BLOCKED_BROWSER_RUNTIME"))
        stages = res["stages"]
        self.assertEqual(stages["analyze_repository"]["status"], "PASS")
        self.assertEqual(stages["orchestrate_ui"]["status"], "PASS")
        self.assertEqual(stages["build_knowledge_plan"]["status"], "PASS")
        self.assertEqual(stages["plan_modification"]["status"], "PASS")
        self.assertEqual(stages["build_validation_handoff"]["status"], "PASS")
        self.assertEqual(stages["detect_runtime"]["status"], "PASS")
        # In environment without playwright browser, critic must not pass with empty evidence
        self.assertFalse(res["authorized_to_proceed"])

    def test_target_b_react_dashboard_pipeline_execution(self):
        """Target B React Dashboard executes all stages through benchmark harness."""
        self.assertTrue(self.target_b.is_dir(), "Target B directory must exist")
        self.assertTrue((self.target_b / "package.json").is_file())
        self.assertTrue((self.target_b / "index.html").is_file())
        self.assertTrue((self.target_b / "styles.css").is_file())
        self.assertTrue((self.target_b / "app.js").is_file())

        task = "Build cloud workload dashboard with sidebar drawer, search filter, and loading skeleton"
        res = run_target_benchmark(self.target_b, task)

        self.assertIn(res["status"], ("INTEGRATION_VERIFIED", "BLOCKED_BROWSER_RUNTIME"))
        stages = res["stages"]
        self.assertEqual(stages["analyze_repository"]["status"], "PASS")
        self.assertEqual(stages["orchestrate_ui"]["status"], "PASS")
        self.assertEqual(stages["build_knowledge_plan"]["status"], "PASS")
        self.assertEqual(stages["plan_modification"]["status"], "PASS")
        self.assertEqual(stages["build_validation_handoff"]["status"], "PASS")
        self.assertEqual(stages["detect_runtime"]["status"], "PASS")
        self.assertFalse(res["authorized_to_proceed"])

    def test_simulated_evidence_never_claims_real_browser_execution(self):
        """Fixture data is not treated as a real browser run or runtime authorization."""
        task = "Update landing page layout"
        mock_evidence = {
            "captures": [
                {
                    "route": "/landing",
                    "viewport": "desktop_1440",
                    "screenshot_path": "captures/landing_desktop.png",
                }
            ],
            "runtime_evidence": [{"check": "render", "passed": True}],
            "console_evidence": [],
            "implemented_states": ["ready"],
        }
        res = run_target_benchmark(self.target_a, task, mock_browser_evidence=mock_evidence)
        self.assertNotEqual(res["status"], "BROWSER_E2E_VERIFIED")
        self.assertNotEqual(res.get("runtime_classification"), "REAL_BROWSER_EXECUTED")


if __name__ == "__main__":
    unittest.main()
