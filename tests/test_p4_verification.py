"""P4 CHECK: verification gates, evidence sufficiency, root-cause routing."""
from __future__ import annotations

import unittest

import _paths  # noqa: F401
from uiux.engine.verification.engine import VerificationEngine

REPORT = {"ready_for_p4": True, "plan_id": "plan_123", "deviations": []}
CONTRACT = {"required_viewports": ["desktop_1440", "mobile_375"], "required_routes": ["/checkout"],
            "requires_baseline": False}
DECISIONS = [{"id": "dec_1", "intent": "Improve CTA hierarchy"}]


def capture(viewport):
    return {"viewport": viewport, "route": "/checkout", "status": "CAPTURED"}


def session(viewports, changed_tokens=None):
    data = {"after_evidence": {"captures": [capture(v) for v in viewports]}}
    if changed_tokens is not None:
        data["modification_plan"] = {"preservation": {"granular_permissions": {"palette": "locked"}}}
        data["change_manifest"] = {"changed_tokens": changed_tokens}
    return data


class VerificationEngineTests(unittest.TestCase):
    def verify(self, data, report=REPORT):
        return VerificationEngine(data).verify(report, CONTRACT, DECISIONS)

    def test_missing_viewport_evidence_is_partial(self) -> None:
        result = self.verify(session(["desktop_1440"]))
        self.assertEqual(result["verification_status"], "PARTIAL")
        self.assertEqual(result["trust_level"], "UNVERIFIED")
        self.assertTrue(result["limitations"])

    def test_locked_palette_change_routes_to_p3(self) -> None:
        result = self.verify(session(["desktop_1440", "mobile_375"], ["primary_color"]))
        route = result["repair"]["routes"][0]
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual((route["route_to"], route["root_cause"]), ("P3", "IMPLEMENTATION_ERROR"))

    def test_unproven_capture_records_partial_not_verified(self) -> None:
        result = self.verify(session(["desktop_1440", "mobile_375"], []))
        self.assertEqual(result["verification_status"], "PARTIAL")
        self.assertEqual(result["trust_level"], "UNVERIFIED")
        self.assertIn("without valid manifest/report/file provenance", " ".join(result["limitations"]))

    def test_unready_implementation_report_blocks(self) -> None:
        result = self.verify(session(["desktop_1440", "mobile_375"], []), {**REPORT, "ready_for_p4": False})
        self.assertEqual(result["status"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
