"""Tests for the Codex adapter build and verification."""
from __future__ import annotations

import json
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

import _paths

ROOT = _paths.PACKAGE_ROOT
CODEX_ADAPTER = ROOT / ".codex-plugin"


class CodexAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="codex-test-")
        self.workspace = Path(self.tmpdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_export_success(self) -> None:
        # Import the export module and run it
        import importlib.util
        spec1 = importlib.util.spec_from_file_location("export", str(ROOT / ".codex-plugin" / "export.py"))
        export = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(export)
        
        spec2 = importlib.util.spec_from_file_location("verify", str(ROOT / ".codex-plugin" / "verify.py"))
        verify = importlib.util.module_from_spec(spec2)
        if (ROOT / ".codex-plugin" / "verify.py").exists():
            spec2.loader.exec_module(verify)
        
        result = export.export(ROOT, self.workspace, dev=True)
        self.assertEqual(result["status"], "BUILT")
        self.assertEqual(result["adapter"], "codex")
        self.assertEqual(result["build_mode"], "dev")
        
        bundle = Path(result["bundle"])
        self.assertTrue(bundle.is_file())
        
        # Verify bundle contents
        with zipfile.ZipFile(bundle) as zf:
            names = zf.namelist()
            base = f"{result['name']}-{result['version']}-dev-codex"
            
            # Check for overlay files
            self.assertIn(f"{base}/plugin.json", names)
            self.assertIn(f"{base}/mcp.json", names)
            self.assertIn(f"{base}/skills/ui-ux-workflow/SKILL.md", names)
            
            # Check for generic payload
            self.assertIn(f"{base}/SKILL.md", names)
            self.assertIn(f"{base}/uiux/__init__.py", names)

    def test_verify_checks(self) -> None:
        import importlib.util
        spec1 = importlib.util.spec_from_file_location("export", str(ROOT / ".codex-plugin" / "export.py"))
        export = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(export)
        
        spec2 = importlib.util.spec_from_file_location("verify", str(ROOT / ".codex-plugin" / "verify.py"))
        verify = importlib.util.module_from_spec(spec2)
        if (ROOT / ".codex-plugin" / "verify.py").exists():
            spec2.loader.exec_module(verify)
        import sys
        
        # First export a valid bundle
        result = export.export(ROOT, self.workspace, dev=True)
        bundle_path = Path(result["bundle"])
        
        # Now verify it
        from _packaging_support import artifact
        extract_dir = self.workspace / "extract"
        artifact.safe_extract(bundle_path, extract_dir)
        
        base = f"{result['name']}-{result['version']}-dev-codex"
        report = verify.verify_bundle(extract_dir / base, sys.executable)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(len(report["failed"]), 0)
        
        # Ensure X1-X16 are present
        check_ids = [c["id"] for c in report["checks"]]
        for i in range(1, 17):
            self.assertIn(f"X{i}", check_ids)
            
        # Ensure X5 passed
        x5 = next(c for c in report["checks"] if c["id"] == "X5")
        self.assertEqual(x5["status"], "PASS")

    def test_verify_x5_failure_when_skill_mutated(self) -> None:
        import importlib.util
        spec1 = importlib.util.spec_from_file_location("export", str(ROOT / ".codex-plugin" / "export.py"))
        export = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(export)
        
        spec2 = importlib.util.spec_from_file_location("verify", str(ROOT / ".codex-plugin" / "verify.py"))
        verify = importlib.util.module_from_spec(spec2)
        if (ROOT / ".codex-plugin" / "verify.py").exists():
            spec2.loader.exec_module(verify)
        import sys
        
        result = export.export(ROOT, self.workspace, dev=True)
        bundle_path = Path(result["bundle"])
        
        from _packaging_support import artifact
        extract_dir = self.workspace / "extract"
        artifact.safe_extract(bundle_path, extract_dir)
        
        base = f"{result['name']}-{result['version']}-dev-codex"
        
        # Mutate the generated skill
        skill = extract_dir / base / "skills" / "ui-ux-workflow" / "SKILL.md"
        skill.write_text("mutated", encoding="utf-8")
        
        report = verify.verify_bundle(extract_dir / base, sys.executable)
        self.assertEqual(report["status"], "FAIL")
        self.assertIn("X5", report["failed"])

    def test_verify_x5_rejects_verbatim_copy_of_canonical_skill(self) -> None:
        """A byte copy of SKILL.md one level down breaks its relative links, so X5 must fail."""
        import importlib.util
        spec1 = importlib.util.spec_from_file_location("export", str(ROOT / ".codex-plugin" / "export.py"))
        export = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(export)
        spec2 = importlib.util.spec_from_file_location("verify", str(ROOT / ".codex-plugin" / "verify.py"))
        verify = importlib.util.module_from_spec(spec2)
        spec2.loader.exec_module(verify)
        import sys

        result = export.export(ROOT, self.workspace, dev=True)
        from _packaging_support import artifact
        extract_dir = self.workspace / "extract-copy"
        artifact.safe_extract(Path(result["bundle"]), extract_dir)
        root = extract_dir / f"{result['name']}-{result['version']}-dev-codex"

        skill = root / "skills" / "ui-ux-workflow" / "SKILL.md"
        self.assertNotEqual(skill.read_bytes(), (root / "SKILL.md").read_bytes(), "bundle must not copy SKILL.md")
        skill.write_bytes((root / "SKILL.md").read_bytes())
        problems = verify.check_skill_entry(skill, root / "SKILL.md", root)
        self.assertTrue(any(p.startswith("broken relative link") for p in problems), problems)

    def test_verify_missing_python(self) -> None:
        import importlib.util
        spec1 = importlib.util.spec_from_file_location("export", str(ROOT / ".codex-plugin" / "export.py"))
        export = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(export)
        
        spec2 = importlib.util.spec_from_file_location("verify", str(ROOT / ".codex-plugin" / "verify.py"))
        verify = importlib.util.module_from_spec(spec2)
        if (ROOT / ".codex-plugin" / "verify.py").exists():
            spec2.loader.exec_module(verify)
        import sys
        
        result = export.export(ROOT, self.workspace, dev=True)
        bundle_path = Path(result["bundle"])
        
        from _packaging_support import artifact
        extract_dir = self.workspace / "extract"
        artifact.safe_extract(bundle_path, extract_dir)
        base = f"{result['name']}-{result['version']}-dev-codex"
        
        # Pass a fake python path
        report = verify.verify_bundle(extract_dir / base, "/path/to/nonexistent/python3")
        self.assertEqual(report["status"], "FAIL")
        
        # Check that X10 fails with the expected missing python message
        x10 = next(c for c in report["checks"] if c["id"] == "X10")
        self.assertEqual(x10["status"], "FAIL")
        self.assertIn("Python executable '/path/to/nonexistent/python3' not found", x10["detail"])
        self.assertIn("(Missing Python runtime)", x10["detail"])

    def test_verify_placeholder_and_cwd_rules(self) -> None:
        import importlib.util
        spec1 = importlib.util.spec_from_file_location("export", str(ROOT / ".codex-plugin" / "export.py"))
        export = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(export)
        
        spec2 = importlib.util.spec_from_file_location("verify", str(ROOT / ".codex-plugin" / "verify.py"))
        verify = importlib.util.module_from_spec(spec2)
        if (ROOT / ".codex-plugin" / "verify.py").exists():
            spec2.loader.exec_module(verify)
        import sys
        
        result = export.export(ROOT, self.workspace, dev=True)
        bundle_path = Path(result["bundle"])
        
        from _packaging_support import artifact
        extract_dir = self.workspace / "extract"
        artifact.safe_extract(bundle_path, extract_dir)
        base = extract_dir / f"{result['name']}-{result['version']}-dev-codex"
        
        mcp_file = base / "mcp.json"
        
        # Test 1: cwd omitted -> PASS
        # The generated mcp.json already omits cwd, verify should PASS
        report = verify.verify_bundle(base, sys.executable)
        x7 = next(c for c in report["checks"] if c["id"] == "X7")
        self.assertEqual(x7["status"], "PASS")
        
        # Helper to test modifying mcp.json
        def check_mcp_mutation(mutation_fn, expected_problem):
            original = json.loads(mcp_file.read_text(encoding="utf-8"))
            mutation_fn(original)
            mcp_file.write_text(json.dumps(original), encoding="utf-8")
            r = verify.verify_bundle(base, sys.executable)
            x7_check = next(c for c in r["checks"] if c["id"] == "X7")
            self.assertEqual(x7_check["status"], "FAIL")
            self.assertTrue(any(expected_problem in p for p in x7_check["detail"].split("; ")))
            # Restore
            mcp_file.write_text(json.dumps(original), encoding="utf-8") # wait, need to restore original, not mutated
        
        def restore_mcp():
            export.export(ROOT, self.workspace, dev=True)
            artifact.safe_extract(bundle_path, extract_dir)
            
        # Test 2: cwd: "" -> FAIL
        def mutate_empty_cwd(data):
            data["mcpServers"]["ui-ux-design-mcp"]["cwd"] = ""
        check_mcp_mutation(mutate_empty_cwd, "cwd cannot be empty string")
        restore_mcp()
        
        # Test 3: absolute cwd -> FAIL
        def mutate_absolute_cwd(data):
            data["mcpServers"]["ui-ux-design-mcp"]["cwd"] = "/absolute/path"
        check_mcp_mutation(mutate_absolute_cwd, "cwd cannot be absolute path")
        restore_mcp()
        
        # Test 4: ${PLUGIN_DIR} -> FAIL
        def mutate_plugin_dir(data):
            data["mcpServers"]["ui-ux-design-mcp"]["cwd"] = "${PLUGIN_DIR}"
        check_mcp_mutation(mutate_plugin_dir, "uses unsupported placeholder ${PLUGIN_DIR}")
        restore_mcp()
        
        # Test 5: placeholder in command -> FAIL
        def mutate_command_placeholder(data):
            data["mcpServers"]["ui-ux-design-mcp"]["command"] = "${PLUGIN_ROOT}/bin/python3"
        check_mcp_mutation(mutate_command_placeholder, "command cannot contain placeholders")
        restore_mcp()


class CodexMarketplaceTests(unittest.TestCase):
    """Codex local marketplace metadata, path safety, and deterministic export."""

    def setUp(self) -> None:
        self.tmpdir = tempfile.mkdtemp(prefix="codex-marketplace-test-")
        self.workspace = Path(self.tmpdir)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _extract_marketplace(self) -> tuple[dict, Path]:
        import importlib.util
        spec1 = importlib.util.spec_from_file_location("export", str(ROOT / ".codex-plugin" / "export.py"))
        export = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(export)
        
        spec2 = importlib.util.spec_from_file_location("verify", str(ROOT / ".codex-plugin" / "verify.py"))
        verify = importlib.util.module_from_spec(spec2)
        if (ROOT / ".codex-plugin" / "verify.py").exists():
            spec2.loader.exec_module(verify)
        from _packaging_support import artifact
        result = export.export(ROOT, self.workspace, dev=True)
        extract_dir = self.workspace / "marketplace"
        artifact.safe_extract(Path(result["marketplace_bundle"]), extract_dir)
        root = extract_dir / f"{result['name']}-{result['version']}-dev-codex-marketplace"
        return result, root

    def test_marketplace_bundle_and_k_checks(self) -> None:
        import importlib.util
        spec1 = importlib.util.spec_from_file_location("export", str(ROOT / ".codex-plugin" / "export.py"))
        export = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(export)
        
        spec2 = importlib.util.spec_from_file_location("verify", str(ROOT / ".codex-plugin" / "verify.py"))
        verify = importlib.util.module_from_spec(spec2)
        if (ROOT / ".codex-plugin" / "verify.py").exists():
            spec2.loader.exec_module(verify)
        result, marketplace_root = self._extract_marketplace()
        self.assertTrue(Path(result["marketplace_bundle"]).is_file())
        manifest = json.loads((marketplace_root / ".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "uiux-local")
        self.assertEqual(manifest["interface"]["displayName"], "UIUX Local Plugins")
        self.assertEqual(manifest["plugins"][0]["source"], {"source": "local", "path": "./plugins/ui-ux-design"})
        self.assertEqual(manifest["plugins"][0]["policy"], {"installation": "AVAILABLE", "authentication": "ON_INSTALL"})
        self.assertTrue((marketplace_root / "plugins/ui-ux-design/plugin.json").is_file())
        report = verify.verify_marketplace(marketplace_root)
        self.assertEqual(report["status"], "PASS", report)
        self.assertEqual({check["id"] for check in report["checks"]}, {f"K{i}" for i in range(1, 17)})

    def test_marketplace_export_is_deterministic(self) -> None:
        import importlib.util
        spec1 = importlib.util.spec_from_file_location("export", str(ROOT / ".codex-plugin" / "export.py"))
        export = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(export)
        
        spec2 = importlib.util.spec_from_file_location("verify", str(ROOT / ".codex-plugin" / "verify.py"))
        verify = importlib.util.module_from_spec(spec2)
        if (ROOT / ".codex-plugin" / "verify.py").exists():
            spec2.loader.exec_module(verify)
        first = export.export(ROOT, self.workspace / "first", dev=True)
        second = export.export(ROOT, self.workspace / "second", dev=True)
        self.assertEqual(first["marketplace_sha256"], second["marketplace_sha256"])

    def test_marketplace_rejects_invalid_metadata_and_paths(self) -> None:
        import importlib.util
        spec1 = importlib.util.spec_from_file_location("export", str(ROOT / ".codex-plugin" / "export.py"))
        export = importlib.util.module_from_spec(spec1)
        spec1.loader.exec_module(export)
        
        spec2 = importlib.util.spec_from_file_location("verify", str(ROOT / ".codex-plugin" / "verify.py"))
        verify = importlib.util.module_from_spec(spec2)
        if (ROOT / ".codex-plugin" / "verify.py").exists():
            spec2.loader.exec_module(verify)
        _, marketplace_root = self._extract_marketplace()
        manifest_path = marketplace_root / ".agents/plugins/marketplace.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        cases = [
            (lambda data: data.pop("name"), "K4"),
            (lambda data: data.pop("interface"), "K5"),
            (lambda data: data.__setitem__("plugins", [{}]), "K7"),
            (lambda data: data["plugins"][0].pop("policy"), "K11"),
            (lambda data: data["plugins"][0].__setitem__("category", ""), "K13"),
            (lambda data: data["plugins"][0]["source"].__setitem__("path", "plugins/ui-ux-design"), "K9"),
            (lambda data: data["plugins"][0]["source"].__setitem__("path", "../plugin"), "K9"),
            (lambda data: data["plugins"][0]["source"].__setitem__("path", "C:\\plugin"), "K9"),
            (lambda data: data["plugins"][0]["source"].__setitem__("path", "/root/plugin"), "K9"),
            (lambda data: data["plugins"][0]["source"].__setitem__("path", "\\\\server\\share"), "K9"),
        ]
        for mutate, expected in cases:
            with self.subTest(expected=expected):
                candidate = json.loads(json.dumps(manifest))
                mutate(candidate)
                manifest_path.write_text(json.dumps(candidate), encoding="utf-8")
                report = verify.verify_marketplace(marketplace_root)
                self.assertIn(expected, report["failed"], report)
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
if __name__ == "__main__":
    unittest.main()
