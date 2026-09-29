"""Tier 2 verification capability, evidence provenance, degraded mode and trust semantics."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import _paths  # noqa: F401
from uiux import api
from uiux.doctor import diagnose
from uiux.engine.verification.engine import VerificationEngine
from uiux.engine.verification.static import StaticVerificationEngine
from uiux.engine.verification.status_audit import audit_status_semantics
from uiux.engine.verification.strategy import detect_verification_capabilities, resolve_verification_strategy
from uiux.engine.verification.trust import CLAIM_TYPES, TRUST_LEVELS, VERIFICATION_LEVELS, VERIFICATION_STATUSES, validate_verification_result
from uiux.runtime.evidence import validate_runtime_directory


class VerificationTrustTests(unittest.TestCase):
    def _plan(self, path: str = "src/Checkout.tsx") -> dict:
        return {"plan_id": "plan-test", "repository": {"framework": "generic"},
            "affected_surface": {"files": [path], "allowed_files": [path], "planned_files": [path],
                "protected_files": [], "protected_tokens": []},
            "impact": {"affected_files": [path]}, "changes": [],
            "preservation": {"granular_permissions": {"palette": "locked", "brand": "locked"}, "protected_tokens": []}}

    def _implementation(self, path: str = "src/Checkout.tsx") -> dict:
        return {"status": "COMPLETED", "ready_for_p4": True, "plan_id": "plan-test",
            "files_modified": [path], "ledger": [{"file": path, "change_id": "change-1"}], "deviations": []}

    def _runtime_detection(self, state: str = "NOT_DECLARED", commands: list[str] | None = None) -> dict:
        return {"playwright": {"runtime_state": {"state": state}},
            "project": {"framework": {"value": "React"}, "validation_commands": commands or []},
            "package_manager": {"detected": "npm" if commands else None}}

    def test_canonical_vocabulary_is_exact(self) -> None:
        self.assertEqual(VERIFICATION_LEVELS, ("SOURCE_DIFF", "STATIC_STRUCTURE", "BUILD_VALIDATION", "RUNTIME_DOM", "VISUAL_RENDER", "INTERACTION_A11Y"))
        self.assertEqual(TRUST_LEVELS, ("UNVERIFIED", "STATICALLY_VERIFIED", "RUNTIME_VERIFIED", "MULTIMODAL_VERIFIED"))
        self.assertEqual(VERIFICATION_STATUSES, ("NOT_RUN", "PASS", "PASS_WITH_WARNINGS", "PARTIAL", "FAIL", "BLOCKED"))
        self.assertEqual(len(CLAIM_TYPES), 10)

    def test_strategy_degrades_without_browser_and_keeps_static_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            caps = detect_verification_capabilities(temp, self._implementation(), self._runtime_detection())
            strategy = resolve_verification_strategy({"viewports": ["mobile_375"]}, self._implementation(), caps)
        self.assertTrue(strategy["degraded_mode"])
        self.assertEqual(strategy["selected_checks"], ["SOURCE_DIFF", "STATIC_STRUCTURE"])
        self.assertEqual({x["check"] for x in strategy["unavailable_checks"]}, {"RUNTIME_DOM", "VISUAL_RENDER"})
        self.assertEqual(strategy["expected_trust_ceiling"], "STATICALLY_VERIFIED")

    def test_static_fallback_reports_signal_without_rendered_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "src/Checkout.tsx"
            source.parent.mkdir(parents=True)
            source.write_text("<main className='grid grid-cols-1 md:grid-cols-2'>Checkout</main>", encoding="utf-8")
            report = StaticVerificationEngine().verify(self._plan(), self._implementation(),
                {"project_root": temp, "actual_changed_files": ["src/Checkout.tsx"], "token_baseline": {}},
                {"viewports": ["mobile_375"]}, temp)
        self.assertEqual(report["source_diff"]["status"], "PASS")
        self.assertEqual(report["structure"]["status"], "PASS")
        self.assertEqual(report["responsive_signals"]["status"], "STATIC_RESPONSIVE_SIGNAL")
        self.assertEqual(report["responsive_signals"]["rendered_behavior"], "UNVERIFIED")
        self.assertEqual(report["status"], "PARTIAL")
        self.assertIn("Rendered UI has not been verified.", report["limitations"])

    def test_locked_palette_violation_fails_without_browser(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "src/Checkout.css"
            source.parent.mkdir(parents=True)
            source.write_text(":root { --color-brand: #111111; }", encoding="utf-8")
            report = StaticVerificationEngine().verify(self._plan("src/Checkout.css"), self._implementation("src/Checkout.css"),
                {"project_root": temp, "token_baseline": {"--color-brand": "#000000"}},
                {"viewports": ["mobile_375"], "preservation_checks": ["locked_palette_intact"]}, temp)
        self.assertEqual(report["status"], "FAIL")
        self.assertTrue(any(i["category"] == "PRESERVATION_VIOLATION" and i["route_to"] == "P3" for i in report["issues"]))

    def test_degraded_p4_keeps_execution_separate_from_static_trust(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "src/Checkout.tsx"
            source.parent.mkdir(parents=True)
            source.write_text("<main className='grid md:grid-cols-2'>Checkout</main>", encoding="utf-8")
            plan = self._plan()
            implementation = self._implementation()
            session = {"project_root": temp, "actual_changed_files": ["src/Checkout.tsx"],
                "token_baseline": {}, "runtime_detection": self._runtime_detection(),
                "after_evidence": {}, "modification_plan": plan}
            result = VerificationEngine(session).verify(implementation,
                {"pages": ["/checkout"], "viewports": ["mobile_375"], "preservation_checks": ["locked_palette_intact"]}, [])
        self.assertEqual(result["execution_status"], "COMPLETED")
        self.assertEqual(result["verification_status"], "PARTIAL")
        self.assertEqual(result["trust_level"], "STATICALLY_VERIFIED")
        self.assertIn("RUNTIME_DOM", {item["check"] for item in result["verification_levels_unavailable"]})
        self.assertTrue(any(item["claim_type"] == "RESPONSIVE_BEHAVIOR" for item in result["unverified_claims"]))
        self.assertTrue(any("Rendered UI has not been verified." == item for item in result["limitations"]))

    def test_build_validation_uses_only_detected_named_script(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "package.json").write_text(json.dumps({"scripts": {"build": "not executed by test"}}), encoding="utf-8")
            (root / "package-lock.json").write_text("{}", encoding="utf-8")
            source = root / "src/Checkout.tsx"
            source.parent.mkdir(parents=True)
            source.write_text("<main/>", encoding="utf-8")
            detected = self._runtime_detection(commands=["build"])
            with patch("uiux.engine.verification.static.subprocess.run", return_value=type("Result", (), {"returncode": 2, "stdout": "", "stderr": "build failed"})()) as run:
                report = StaticVerificationEngine().verify(self._plan(), self._implementation(),
                    {"project_root": temp, "runtime_detection": detected, "token_baseline": {}}, {}, temp)
        run.assert_called_once()
        self.assertEqual(run.call_args.args[0], ["npm", "run", "build"])
        self.assertFalse(run.call_args.kwargs["shell"])
        self.assertEqual(report["build"]["status"], "FAIL")
        self.assertTrue(any(item["category"] == "BUILD_VALIDATION" for item in report["issues"]))

    def test_runtime_evidence_validator_checks_manifest_report_and_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "capture.png").write_bytes(b"capture")
            manifest = {"schema_version": 1, "session_id": "s", "status": "COMPLETED", "captures": [
                {"id": "home-mobile", "route": "/", "page_id": "home", "viewport": "mobile_375",
                 "width": 375, "height": 812, "iteration": 1, "status": "CAPTURED", "file": "capture.png"}]}
            report = {"schema_version": 1, "session_id": "s", "status": "COMPLETED", "captures_completed": 1, "captures_expected": 1}
            (root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            (root / "execution-report.json").write_text(json.dumps(report), encoding="utf-8")
            self.assertEqual(validate_runtime_directory(root)["status"], "VALID")
            (root / "capture.png").unlink()
            self.assertEqual(validate_runtime_directory(root)["status"], "INVALID")

    def test_no_fake_pass_rejects_empty_provenance_and_incomplete_checks(self) -> None:
        errors = validate_verification_result({"verification_status": "PASS", "trust_level": "RUNTIME_VERIFIED",
            "verified_claims": [{"claim_type": "VISUAL_INTENT", "status": "VERIFIED", "evidence_refs": []}],
            "evidence_summary": "", "required_checks": ["VISUAL_RENDER"], "completed_checks": [], "evidence_refs": []})
        self.assertTrue(any("no evidence provenance" in item for item in errors))
        self.assertTrue(any("missing required checks" in item for item in errors))

    def test_completed_task_cannot_have_not_run_verification(self) -> None:
        errors = validate_verification_result({"execution_status": "COMPLETED", "verification_status": "NOT_RUN",
            "trust_level": "UNVERIFIED", "public_task_status": "COMPLETED", "limitations": ["CHECK did not run"]})
        self.assertTrue(any("public task cannot be COMPLETED" in item for item in errors))

    def test_runtime_without_required_visual_evidence_stays_runtime_trust(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "src/Checkout.tsx"
            source.parent.mkdir(parents=True)
            source.write_text("<main>Checkout</main>", encoding="utf-8")
            plan = self._plan()
            captures = [{"id": "checkout-mobile", "route": "/checkout", "viewport": "mobile_375", "status": "CAPTURED", "file": "checkout.png"}]
            session = {"project_root": temp, "actual_changed_files": ["src/Checkout.tsx"], "token_baseline": {},
                "runtime_detection": self._runtime_detection("READY"), "runtime_evidence_validation": {"status": "VALID"},
                "after_evidence": {"captures": captures}, "modification_plan": plan}
            result = VerificationEngine(session).verify(self._implementation(),
                {"required_routes": ["/checkout"], "required_viewports": ["mobile_375"]}, [])
        self.assertEqual(result["verification_status"], "PARTIAL")
        self.assertEqual(result["trust_level"], "RUNTIME_VERIFIED")
        self.assertIn("VISUAL_RENDER", result["required_checks"])
        self.assertFalse(any(claim["claim_type"] == "VISUAL_INTENT" for claim in result["verified_claims"]))

    def test_trust_achieved_does_not_inherit_environment_ceiling(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "src/Checkout.tsx"
            source.parent.mkdir(parents=True)
            source.write_text("<main>Checkout</main>", encoding="utf-8")
            plan = self._plan()
            session = {"project_root": temp, "actual_changed_files": ["src/Checkout.tsx"], "token_baseline": {},
                "runtime_detection": self._runtime_detection("READY"), "after_evidence": {}, "modification_plan": plan}
            result = VerificationEngine(session).verify(self._implementation(), {"viewports": ["mobile_375"]}, [])
        self.assertEqual(result["trust_ceiling"], "MULTIMODAL_VERIFIED")
        self.assertEqual(result["trust_achieved"], "STATICALLY_VERIFIED")

    def test_completed_task_cannot_have_not_run_verification(self) -> None:
        errors = validate_verification_result({"execution_status": "COMPLETED", "verification_status": "NOT_RUN",
            "trust_level": "UNVERIFIED", "public_task_status": "COMPLETED", "limitations": ["CHECK did not run"]})
        self.assertTrue(any("public task cannot be COMPLETED" in item for item in errors))

    def test_runtime_without_required_visual_evidence_stays_runtime_trust(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "src/Checkout.tsx"
            source.parent.mkdir(parents=True)
            source.write_text("<main>Checkout</main>", encoding="utf-8")
            plan = self._plan()
            captures = [{"id": "checkout-mobile", "route": "/checkout", "viewport": "mobile_375", "status": "CAPTURED", "file": "checkout.png"}]
            session = {"project_root": temp, "actual_changed_files": ["src/Checkout.tsx"], "token_baseline": {},
                "runtime_detection": self._runtime_detection("READY"), "runtime_evidence_validation": {"status": "VALID"},
                "after_evidence": {"captures": captures}, "modification_plan": plan}
            result = VerificationEngine(session).verify(self._implementation(),
                {"required_routes": ["/checkout"], "required_viewports": ["mobile_375"]}, [])
        self.assertEqual(result["verification_status"], "PARTIAL")
        self.assertEqual(result["trust_level"], "RUNTIME_VERIFIED")
        self.assertIn("VISUAL_RENDER", {x["check"] for x in result["verification_levels_unavailable"]} | set(result["required_checks"]))
        self.assertFalse(any(claim["claim_type"] == "VISUAL_INTENT" for claim in result["verified_claims"]))

    def test_trust_achieved_does_not_inherit_environment_ceiling(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "src/Checkout.tsx"
            source.parent.mkdir(parents=True)
            source.write_text("<main>Checkout</main>", encoding="utf-8")
            plan = self._plan()
            session = {"project_root": temp, "actual_changed_files": ["src/Checkout.tsx"], "token_baseline": {},
                "runtime_detection": self._runtime_detection("READY"), "after_evidence": {}, "modification_plan": plan}
            result = VerificationEngine(session).verify(self._implementation(), {"viewports": ["mobile_375"]}, [])
        self.assertEqual(result["trust_ceiling"], "MULTIMODAL_VERIFIED")
        self.assertEqual(result["trust_achieved"], "STATICALLY_VERIFIED")

    def test_doctor_reports_ladder_and_static_ceiling_without_installing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = diagnose(temp)
        self.assertEqual(result["maximum_trust_level"], "STATICALLY_VERIFIED")
        self.assertEqual(result["verification_capabilities"]["RUNTIME_DOM"]["status"], "BLOCKED")
        self.assertIn("cannot verify rendered responsive behavior", result["verification_summary"])

    def test_status_semantics_audit_passes(self) -> None:
        self.assertEqual(audit_status_semantics()["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
