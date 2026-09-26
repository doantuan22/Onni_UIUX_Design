"""Plugin layer: manifest, versioning, generic adapter, packaging boundary, core without plugin."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import _paths
from uiux import __version__, api

ROOT = _paths.PACKAGE_ROOT
MANIFEST = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
SCHEMA = json.loads((ROOT / "schemas/plugin.schema.json").read_text(encoding="utf-8"))
sys.path.insert(0, str(ROOT / "packaging"))
import package_files  # noqa: E402


def run(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], capture_output=True, text=True, cwd=cwd, encoding="utf-8")


class ManifestTests(unittest.TestCase):
    def test_required_fields_and_version_format(self) -> None:
        for field in SCHEMA["required"]:
            self.assertIn(field, MANIFEST)
        self.assertRegex(MANIFEST["version"], SCHEMA["properties"]["version"]["pattern"])
        for key in SCHEMA["properties"]["entrypoints"]["required"]:
            self.assertIn(key, MANIFEST["entrypoints"])

    def test_single_version_source(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(version, "0.1.0")
        self.assertEqual({version}, {MANIFEST["version"], __version__, api.version()})
        self.assertIn(f"## {version}", (ROOT / "CHANGELOG.md").read_text(encoding="utf-8"))

    def test_referenced_paths_and_tools_exist(self) -> None:
        paths = [MANIFEST["knowledge"]["registry"], MANIFEST["knowledge"]["index"], MANIFEST["tools"]["registry"],
                 MANIFEST["evals"]["scenarios"], MANIFEST["runtime"]["contracts"], MANIFEST["configuration"]["defaults"],
                 MANIFEST["packaging"]["rules"], *MANIFEST["compatibility"]["backward_compatible_cli"]]
        paths += [v["path"] for v in MANIFEST["entrypoints"].values() if "path" in v]
        for rel in paths:
            self.assertTrue((ROOT / rel).exists(), rel)
        tools = {t["id"] for t in api.list_tools()}
        for entry in MANIFEST["entrypoints"].values():
            if "tool" in entry:
                self.assertIn(entry["tool"], tools)
        self.assertEqual(MANIFEST["entrypoints"]["core_api"]["module"], "uiux.api")
        self.assertEqual(set(MANIFEST["knowledge"]["collections"]), set(api.knowledge_collections()))

    def test_manifest_has_no_machine_paths(self) -> None:
        text = json.dumps(MANIFEST)
        self.assertNotRegex(text, r"[A-Za-z]:\\\\|/Users/|/home/")


class GenericAdapterTests(unittest.TestCase):
    ADAPTER = str(ROOT / "adapters/generic/adapter.py")

    def test_describe_and_call_from_another_directory(self) -> None:
        with tempfile.TemporaryDirectory() as cwd:
            described = run([self.ADAPTER, "describe"], cwd)
            self.assertEqual(described.returncode, 0, described.stderr)
            info = json.loads(described.stdout)
            self.assertEqual(info["version"], __version__)
            self.assertEqual(len(info["tools"]), len(api.list_tools()))
            called = run([self.ADAPTER, "call", "retrieve_knowledge", "--params", '{"ids": ["style.swiss"]}'], cwd)
            self.assertEqual(json.loads(called.stdout)["entries"][0]["id"], "style.swiss")
            invalid = run([self.ADAPTER, "call", "nope"], cwd)
            self.assertEqual(invalid.returncode, 3)

    def test_configure_rejects_unsafe_config(self) -> None:
        with tempfile.TemporaryDirectory() as cwd:
            Path(cwd, "host.json").write_text('{"schema_version": 1, "dependency_policy": {"auto_install": true}}', encoding="utf-8")
            result = run([self.ADAPTER, "--config", "host.json", "describe"], cwd)
            self.assertEqual(result.returncode, 3)
            self.assertIn("auto_install", result.stdout)


class PackagingTests(unittest.TestCase):
    result = package_files.compute()

    def test_boundary_passes(self) -> None:
        self.assertEqual(self.result["status"], "PASS", self.result["problems"])

    def test_no_caches_evidence_tests_or_outputs(self) -> None:
        forbidden = re.compile(r"(__pycache__|\.pyc$|(^|/)\.evidence/|^tests/|^external-references/|runtime-helper\.cjs|"
                               r"evals/benchmark/output/|evals/results/|\.log$|\.tmp$)")
        self.assertEqual([f for f in self.result["included"] if forbidden.search(f)], [])

    def test_required_content_present(self) -> None:
        for rel in ("SKILL.md", "VERSION", "uiux/api.py", "uiux/core/tools.json", "knowledge/domains/registry.json",
                    "plugin.json", "evals/scenarios/E80-composition-quality.md", "scripts/run_browser_execution.py"):
            self.assertIn(rel, self.result["included"])

    def test_generated_artifacts_are_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for rel in self.result["included"]:
                target = root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / rel, target)
            (root / "scripts/__pycache__").mkdir(parents=True, exist_ok=True)
            (root / "scripts/__pycache__/x.cpython-311.pyc").write_bytes(b"0")
            (root / ".evidence/s1/pages").mkdir(parents=True)
            (root / ".evidence/s1/pages/a.png").write_bytes(b"0")
            (root / "evals/results").mkdir(parents=True)
            (root / "evals/results/run.json").write_text("{}", encoding="utf-8")
            again = package_files.compute(root)
            self.assertEqual(sorted(again["included"]), sorted(self.result["included"]))


class CoreWithoutPluginTests(unittest.TestCase):
    """Copy only the packaged core (no plugin/, no tests/) and use it from an unrelated working directory."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name).resolve() / "skill"  # Windows 8.3 short names, macOS /private/var
        for rel in PackagingTests.result["included"]:
            if rel.startswith("plugin/"):
                continue
            target = cls.root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / rel, target)
        cls.cwd = tempfile.TemporaryDirectory()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()
        cls.cwd.cleanup()

    def test_core_tools_work_without_plugin(self) -> None:
        self.assertFalse((self.root / "plugin").exists())
        cli = str(self.root / "scripts/uiux_cli.py")
        cases = {
            "retrieve_knowledge": '{"collection": "effects", "text": "glass"}',
            "resolve_capabilities": json.dumps({"profile": json.loads(
                (ROOT / "evals/resolver-scenarios/developer-tool.json").read_text(encoding="utf-8"))["profile"]}),
            "analyze_design_quality": json.dumps({"project": str(self.root / "evals/fixtures/quality/restrained")}),
            "run_evals": '{"suites": ["knowledge", "resolver", "quality-fixtures"]}',
            "validate_skill": "{}",
        }
        for tool, params in cases.items():
            with self.subTest(tool=tool):
                result = run([cli, "call", tool, "--params", params], self.cwd.name)
                self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
                self.assertIn(str(self.root), json.loads(result.stdout).get("project", str(self.root))) if tool == "analyze_design_quality" else None


if __name__ == "__main__":
    unittest.main()
