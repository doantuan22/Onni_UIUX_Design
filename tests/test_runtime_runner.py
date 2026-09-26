"""Standard-library tests for runner input and path safety; no Playwright required."""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import _paths  # noqa: F401
from uiux.runtime import browser as runner


def request(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "session_id": "safe-session", "base_url": "http://127.0.0.1:4173",
        "routes": [{"page_id": "PAGE-HOME", "route": "/"}],
        "viewports": ["desktop"], "iteration": 1,
    }
    value.update(overrides)
    return value


class RunnerInputTests(unittest.TestCase):
    def test_valid_request_uses_project_evidence_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()  # Windows 8.3 short names, macOS /var -> /private/var
            _, session = runner.validate(request(), root)
            self.assertEqual(session, root / ".evidence" / "safe-session")

    def test_rejects_unknown_viewport(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "unknown viewport"):
                runner.validate(request(viewports=["phone-xl"]), Path(temporary))

    def test_rejects_path_outside_project(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaisesRegex(ValueError, "inside project root"):
                runner.validate(request(output_dir=str(root.parent / "outside")), root)

    def test_rejects_unsafe_session_id(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "invalid session_id"):
                runner.validate(request(session_id="../unsafe"), Path(temporary))


class RunnerMotionOptionTests(unittest.TestCase):
    def test_accepts_reduced_motion_and_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            options = {"reduced_motion": "reduce", "motion_probe": True, "probe_wait_ms": 500}
            raw, _ = runner.validate(request(options=options), Path(temporary))
            self.assertEqual(raw["options"]["reduced_motion"], "reduce")

    def test_rejects_invalid_reduced_motion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "reduced_motion"):
                runner.validate(request(options={"reduced_motion": "less"}), Path(temporary))

    def test_rejects_invalid_probe_wait(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "probe_wait_ms"):
                runner.validate(request(options={"motion_probe": True, "probe_wait_ms": 60000}), Path(temporary))

    def test_non_object_options_remain_ignored(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            raw, _ = runner.validate(request(options=None), Path(temporary))
            self.assertIsNone(raw["options"])

    def test_default_behavior_unchanged_without_options(self) -> None:
        self.assertIn("if(i.reduced_motion)co.reducedMotion", runner.HELPER)
        self.assertIn("if(i.motion_probe)", runner.HELPER)
        self.assertNotIn("__PROBE__", runner.HELPER)

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_helper_is_valid_javascript(self) -> None:
        with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False, encoding="utf-8") as handle:
            handle.write(runner.HELPER)
        try:
            result = subprocess.run(["node", "--check", handle.name], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
        finally:
            os.unlink(handle.name)


class RuntimeStateTests(unittest.TestCase):
    """Playwright readiness is classified from the filesystem; the runner blocks honestly and never installs."""

    def setUp(self) -> None:
        from uiux.runtime import capabilities

        self.caps = capabilities
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "app"
        self.project.mkdir()
        self.cache = Path(self.temp.name) / "browsers"
        self.cache.mkdir()
        self.previous = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(self.cache)
        self.addCleanup(self.restore_env)

    def restore_env(self) -> None:
        if self.previous is None:
            os.environ.pop("PLAYWRIGHT_BROWSERS_PATH", None)
        else:
            os.environ["PLAYWRIGHT_BROWSERS_PATH"] = self.previous

    def package(self, declared: bool) -> None:
        deps = {"devDependencies": {"@playwright/test": "^1.0.0"}} if declared else {}
        (self.project / "package.json").write_text(__import__("json").dumps(deps), encoding="utf-8")

    def install(self) -> None:
        pkg = self.project / "node_modules" / "@playwright" / "test"
        pkg.mkdir(parents=True)
        (pkg / "package.json").write_text("{}", encoding="utf-8")

    def state(self) -> str:
        return self.caps.playwright_state(self.project)["state"]

    def test_four_states(self) -> None:
        self.package(False)
        self.assertEqual(self.state(), "NOT_DECLARED")
        self.package(True)
        self.assertEqual(self.state(), "DECLARED_NOT_INSTALLED")
        self.install()
        self.assertEqual(self.state(), "PACKAGE_AVAILABLE_BROWSER_MISSING")
        (self.cache / "chromium-1100").mkdir()
        self.assertEqual(self.state(), "READY")

    def test_hoisted_install_in_parent_is_resolved(self) -> None:
        self.package(True)
        pkg = Path(self.temp.name) / "node_modules" / "playwright"
        pkg.mkdir(parents=True)
        (pkg / "package.json").write_text("{}", encoding="utf-8")
        self.assertEqual(self.state(), "PACKAGE_AVAILABLE_BROWSER_MISSING")

    def blocked_run(self) -> tuple[int, dict, dict]:
        code, summary = runner.execute(request(), self.project)
        report = __import__("json").loads(Path(summary["report"]).read_text(encoding="utf-8"))
        return code, summary, report

    def test_runner_blocks_when_declared_but_not_installed(self) -> None:
        self.package(True)
        code, summary, report = self.blocked_run()
        self.assertEqual((code, summary["status"]), (2, "BLOCKED"))
        self.assertEqual(report["errors"][0]["code"], "PLAYWRIGHT_IMPORT_FAILURE")
        self.assertEqual(report["runtime_state"], "DECLARED_NOT_INSTALLED")
        self.assertFalse((self.project / "node_modules").exists(), "runner must not install anything")

    @unittest.skipUnless(shutil.which("node"), "node not available")
    def test_runner_blocks_when_browser_missing(self) -> None:
        self.package(True)
        self.install()
        code, summary, report = self.blocked_run()
        self.assertEqual(code, 2)
        self.assertEqual(report["errors"][0]["code"], "PLAYWRIGHT_BROWSER_UNAVAILABLE")
        self.assertEqual(list(self.cache.iterdir()), [], "runner must not download browsers")

    def test_dry_run_reports_state_without_writing(self) -> None:
        self.package(True)
        code, plan = runner.execute(request(), self.project, dry_run=True)
        self.assertEqual((code, plan["status"], plan["strategy"]), (0, "DRY_RUN", "BLOCKED"))
        self.assertEqual(plan["runtime_state"], "DECLARED_NOT_INSTALLED")
        self.assertFalse((self.project / ".evidence").exists())


if __name__ == "__main__":
    unittest.main()
