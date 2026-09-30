"""Contract tests for Tier 3 docs and the paired harness (not benchmark scores)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from development.validate_tier3_artifacts import validate
from development.paired_benchmark import run_paired_benchmark


class Tier3ArtifactTests(unittest.TestCase):
    def test_documentation_and_recorded_result_integrity(self) -> None:
        self.assertEqual(validate(), [])

    def test_paired_harness_uses_identical_fixture_copies_and_tracks_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            fixture = root / "development" / "fixtures" / "minimal"
            fixture.mkdir(parents=True)
            (fixture / "start.txt").write_text("same initial state", encoding="utf-8")
            manifest_path = root / "development" / "manifest.json"
            manifest_path.write_text(json.dumps({
                "benchmark_id": "harness-contract-test",
                "pairing_contract": {"same_time_budget_seconds": 10, "repetitions_per_arm": 1},
                "cases": [{"id": "one", "fixture": "development/fixtures/minimal", "request": "test request"}],
            }), encoding="utf-8")
            command = [sys.executable, "-c", "from pathlib import Path; Path('generated.txt').write_text('observed')"]
            report = run_paired_benchmark(manifest_path, root / "output", command, command)
            self.assertEqual(report["status"], "READY_FOR_BLIND_REVIEW")
            self.assertTrue(report["paired_arms_compared"])
            pair = report["results"][0]
            baseline = pair["arms"]["baseline"]["runs"][0]
            plugin = pair["arms"]["plugin"]["runs"][0]
            self.assertEqual(baseline["initial_fixture_sha256"], plugin["initial_fixture_sha256"])
            self.assertEqual(baseline["changed_files"], ["generated.txt"])
            self.assertEqual(plugin["changed_files"], ["generated.txt"])


if __name__ == "__main__":
    unittest.main()
