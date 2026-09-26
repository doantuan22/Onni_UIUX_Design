"""Claude Code adapter: architecture boundary, bundle structure, MCP integration, determinism and C1-C16."""
from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

import _paths

ROOT = _paths.PACKAGE_ROOT
ADAPTER_DIR = ROOT / ".claude-plugin"


class ArchitectureTests(unittest.TestCase):
    """The adapter must not import internal uiux modules or contain design/tool logic."""

    def _adapter_py_files(self) -> list[Path]:
        return sorted(ADAPTER_DIR.glob("*.py"))

    def test_adapter_files_exist(self) -> None:
        self.assertTrue(ADAPTER_DIR.is_dir(), ".claude-plugin/ must exist")
        self.assertTrue((ADAPTER_DIR / "adapter.json").is_file())
        self.assertTrue((ADAPTER_DIR / "export.py").is_file())
        self.assertTrue((ADAPTER_DIR / "verify.py").is_file())
        self.assertTrue((ADAPTER_DIR / "README.md").is_file())

    def test_no_internal_uiux_imports(self) -> None:
        """adapter Python files must not import uiux.core, uiux.engine, uiux.runtime, etc."""
        forbidden = {"uiux.core", "uiux.engine", "uiux.runtime", "uiux.knowledge", "uiux.evals", "uiux.tooling"}
        for path in self._adapter_py_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        for f in forbidden:
                            self.assertFalse(alias.name.startswith(f),
                                             f"{path.name} imports {alias.name}")
                elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                    for f in forbidden:
                        self.assertFalse(node.module.startswith(f),
                                         f"{path.name} imports from {node.module}")

    def test_no_dynamic_execution(self) -> None:
        """No eval/exec/importlib/os.system/shell=True in adapter code."""
        forbidden = ("eval(", "exec(", "importlib", "os.system", "shell=True")
        for path in self._adapter_py_files():
            source = path.read_text(encoding="utf-8")
            for pattern in forbidden:
                with self.subTest(file=path.name, pattern=pattern):
                    self.assertNotIn(pattern, source)

    def test_no_knowledge_ids_in_adapter(self) -> None:
        """Adapters must not hard-code knowledge ids (they come from the registry)."""
        knowledge_pattern = re.compile(r"""["'](?:style|layout|screen|motion|interaction|effect|recipe)\.\w+["']""")
        for path in self._adapter_py_files():
            source = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                # Exclude verify.py which calls MCP tools with test ids
                if path.name == "verify.py":
                    continue
                self.assertIsNone(knowledge_pattern.search(source),
                                  f"{path.name} contains hard-coded knowledge ids")


class AdapterMetadataTests(unittest.TestCase):
    def test_adapter_json_is_schema_valid(self) -> None:
        schema = json.loads((ROOT / "schemas/adapter.schema.json").read_text(encoding="utf-8"))
        data = json.loads((ADAPTER_DIR / "adapter.json").read_text(encoding="utf-8"))
        # Use the packaging artifact validator
        sys.path.insert(0, str(ROOT / "packaging"))
        import artifact
        problems = artifact.validate_schema(data, schema)
        self.assertEqual(problems, [], f"adapter.json schema errors: {problems}")

    def test_adapter_json_fields(self) -> None:
        data = json.loads((ADAPTER_DIR / "adapter.json").read_text(encoding="utf-8"))
        self.assertEqual(data["id"], "claude-code")
        self.assertEqual(data["status"], "experimental")
        self.assertIn("mcp-stdio", data["transports"])
        self.assertEqual(data["tools"]["exposure"], "all-public")
        self.assertEqual(data["tools"]["source"], "uiux.api.list_tools")
        self.assertEqual(data["tools"]["invoke"], "uiux.api.call_tool")
        self.assertEqual(data["host"]["name"], "Claude Code")
        self.assertEqual(data["runtime"]["optional"], True)
        self.assertEqual(data["runtime"]["installs_dependencies"], False)
        self.assertEqual(data["runtime"]["downloads_browsers"], False)

    def test_rendered_files_declared(self) -> None:
        data = json.loads((ADAPTER_DIR / "adapter.json").read_text(encoding="utf-8"))
        rendered = {r["target"] for r in data.get("rendered_files", [])}
        self.assertIn(".claude-plugin/plugin.json", rendered)
        self.assertIn(".mcp.json", rendered)


class TemplateTests(unittest.TestCase):
    def test_claude_plugin_template_has_version_placeholder(self) -> None:
        template = (ADAPTER_DIR / "templates" / "claude-plugin.json").read_text(encoding="utf-8")
        self.assertIn("{version}", template)
        # Should be valid JSON when placeholder is replaced
        rendered = template.replace("{version}", "0.1.0")
        data = json.loads(rendered)
        self.assertEqual(data["name"], "ui-ux-design")
        self.assertEqual(data["version"], "0.1.0")

    def test_mcp_template_has_placeholders(self) -> None:
        template = (ADAPTER_DIR / "templates" / "mcp.json").read_text(encoding="utf-8")
        # Template has placeholders; the actual rendered file uses ${CLAUDE_PLUGIN_ROOT}
        self.assertTrue("{python_command}" in template or "{mcp_server_path}" in template
                        or "CLAUDE_PLUGIN_ROOT" in template or "server.py" in template)


class ExportTests(unittest.TestCase):
    """Test the bundle builder in dev mode against the repository root."""

    def test_export_dev_produces_a_valid_bundle(self) -> None:
        with tempfile.TemporaryDirectory(prefix="claude-export-test-") as out_dir:
            result = subprocess.run(
                [sys.executable, str(ADAPTER_DIR / "export.py"),
                 "--source", str(ROOT), "--out", out_dir, "--dev"],
                capture_output=True, text=True, encoding="utf-8",
                cwd=str(Path(out_dir)), timeout=120,
            )
            self.assertEqual(result.returncode, 0, f"export failed: {result.stdout + result.stderr}")
            data = json.loads(result.stdout)
            self.assertEqual(data["status"], "BUILT")
            self.assertEqual(data["adapter"], "claude-code")
            self.assertIn(".claude-plugin/plugin.json", data["overlay_files"])
            self.assertIn(".mcp.json", data["overlay_files"])

            # Check the ZIP exists and contains key files
            bundle_path = Path(data["bundle"])
            self.assertTrue(bundle_path.is_file())
            with zipfile.ZipFile(bundle_path) as zf:
                names = zf.namelist()
                # All entries should be prefixed with the base name
                base = names[0].split("/")[0]
                required = [
                    f"{base}/.claude-plugin/plugin.json",
                    f"{base}/.mcp.json",
                    f"{base}/SKILL.md",
                    f"{base}/VERSION",
                    f"{base}/uiux/api.py",
                    f"{base}/adapters/mcp/server.py",
                ]
                for req in required:
                    self.assertIn(req, names, f"missing in bundle: {req}")

    def test_export_determinism(self) -> None:
        """Two exports of the same source produce identical ZIP content."""
        sums = []
        for _ in range(2):
            with tempfile.TemporaryDirectory(prefix="claude-export-det-") as out_dir:
                result = subprocess.run(
                    [sys.executable, str(ADAPTER_DIR / "export.py"),
                     "--source", str(ROOT), "--out", out_dir, "--dev"],
                    capture_output=True, text=True, encoding="utf-8",
                    cwd=str(Path(out_dir)), timeout=120,
                    env={**os.environ, "SOURCE_DATE_EPOCH": "1700000000"},
                )
                self.assertEqual(result.returncode, 0)
                data = json.loads(result.stdout)
                sums.append(data["sha256"])
        self.assertEqual(sums[0], sums[1], "two exports with same SOURCE_DATE_EPOCH must be identical")


class BundleStructureTests(unittest.TestCase):
    """Verify the extracted bundle structure meets Claude Code requirements."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.mkdtemp(prefix="claude-bundle-struct-")
        result = subprocess.run(
            [sys.executable, str(ADAPTER_DIR / "export.py"),
             "--source", str(ROOT), "--out", cls._tmpdir, "--dev"],
            capture_output=True, text=True, encoding="utf-8",
            cwd=cls._tmpdir, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"export failed: {result.stdout + result.stderr}")
        data = json.loads(result.stdout)
        bundle_path = Path(data["bundle"])
        cls._extract_dir = Path(cls._tmpdir) / "extracted"
        with zipfile.ZipFile(bundle_path) as zf:
            zf.extractall(cls._extract_dir)
        # The extracted root is the single top-level directory
        dirs = [d for d in cls._extract_dir.iterdir() if d.is_dir()]
        cls._root = dirs[0] if len(dirs) == 1 else cls._extract_dir

    @classmethod
    def tearDownClass(cls) -> None:
        import shutil
        shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_claude_plugin_manifest_valid(self) -> None:
        manifest = json.loads((self._root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "ui-ux-design")
        version = (self._root / "VERSION").read_text(encoding="utf-8").strip()
        self.assertEqual(manifest["version"], version)

    def test_mcp_json_valid_and_uses_plugin_root(self) -> None:
        mcp = json.loads((self._root / ".mcp.json").read_text(encoding="utf-8"))
        self.assertIn("mcpServers", mcp, "Claude Code .mcp.json wraps servers in 'mcpServers'")
        self.assertIn("ui-ux-design-mcp", mcp["mcpServers"])
        server_config = mcp["mcpServers"]["ui-ux-design-mcp"]
        args = server_config.get("args", [])
        # At least one arg should reference the shared MCP server
        server_refs = [a for a in args if "adapters/mcp/server.py" in str(a)]
        self.assertTrue(len(server_refs) > 0, "MCP config must reference the shared transport")
        # Check for ${CLAUDE_PLUGIN_ROOT} portability
        for arg in args:
            if "server.py" in str(arg):
                self.assertIn("${CLAUDE_PLUGIN_ROOT}", str(arg),
                              "MCP args must use ${CLAUDE_PLUGIN_ROOT} for portability")

    def test_no_absolute_paths_in_overlay_files(self) -> None:
        abs_pattern = re.compile(r"""["'](?:[A-Za-z]:[\\\/]|/Users/|/home/|\\\\[A-Za-z0-9])[^"']*["']""")
        for name in (".claude-plugin/plugin.json", ".mcp.json"):
            path = self._root / name
            if path.is_file():
                self.assertIsNone(abs_pattern.search(path.read_text(encoding="utf-8")),
                                  f"absolute path in {name}")

    def test_no_forbidden_files(self) -> None:
        forbidden_dirs = {".git", "tests", "__pycache__", "node_modules", ".venv", "venv", "dist", "build"}
        forbidden_ext = {".pyc", ".pyo", ".log", ".tmp"}
        bundle_path = Path(json.loads(subprocess.run(
            [sys.executable, str(ADAPTER_DIR / "export.py"), "--source", str(ROOT), "--out", self._tmpdir, "--dev"],
            capture_output=True, text=True, cwd=self._tmpdir).stdout)["bundle"])
        with zipfile.ZipFile(bundle_path) as zf:
            for rel in zf.namelist():
                parts = rel.split("/")
                for part in parts:
                    self.assertNotIn(part, forbidden_dirs, f"forbidden directory in bundle: {rel}")
                _, ext = os.path.splitext(rel)
                self.assertNotIn(ext, forbidden_ext, f"forbidden file type: {rel}")

    def test_generic_payload_present(self) -> None:
        for required in ("SKILL.md", "VERSION", "CHANGELOG.md",
                         "uiux/__init__.py", "uiux/api.py", "uiux/core/tools.json",
                         "plugin.json", "adapters/mcp/server.py"):
            self.assertTrue((self._root / required).is_file(), f"missing: {required}")

    def test_mcp_server_works_from_extracted_bundle(self) -> None:
        """The shared MCP server must initialize and list tools from the extracted bundle."""
        server = self._root / "adapters" / "mcp" / "server.py"
        messages = [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize",
             "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                        "clientInfo": {"name": "bundle-test", "version": "1"}}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
             "params": {"name": "self_test", "arguments": {}}},
        ]
        with tempfile.TemporaryDirectory() as cwd:
            process = subprocess.run(
                [sys.executable, str(server)],
                input="\n".join(json.dumps(m) for m in messages) + "\n",
                capture_output=True, text=True, encoding="utf-8",
                cwd=cwd, timeout=30,
            )
        self.assertEqual(process.returncode, 0, process.stderr)
        responses = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual(len(responses), 3)  # init, tools/list, tools/call (notification has no response)
        # Initialize
        self.assertEqual(responses[0]["result"]["protocolVersion"], "2025-06-18")
        # Tools list
        tools = responses[1]["result"]["tools"]
        self.assertGreater(len(tools), 0)
        # Self test
        self.assertEqual(responses[2]["result"]["structuredContent"]["status"], "PASS")


class VerificationTests(unittest.TestCase):
    """Run the Claude-specific verification script (C1-C16) on a dev bundle."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.mkdtemp(prefix="claude-verify-test-")
        result = subprocess.run(
            [sys.executable, str(ADAPTER_DIR / "export.py"),
             "--source", str(ROOT), "--out", cls._tmpdir, "--dev"],
            capture_output=True, text=True, encoding="utf-8",
            cwd=cls._tmpdir, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"export failed: {result.stdout + result.stderr}")
        data = json.loads(result.stdout)
        bundle_path = Path(data["bundle"])
        cls._extract_dir = Path(cls._tmpdir) / "extracted"
        with zipfile.ZipFile(bundle_path) as zf:
            zf.extractall(cls._extract_dir)
        dirs = [d for d in cls._extract_dir.iterdir() if d.is_dir()]
        cls._root = dirs[0] if len(dirs) == 1 else cls._extract_dir

    @classmethod
    def tearDownClass(cls) -> None:
        import shutil
        shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_c1_through_c16(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ADAPTER_DIR / "verify.py"), str(self._root)],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(Path(self._tmpdir)), timeout=120,
        )
        report = json.loads(result.stdout)
        failed = report.get("failed", [])
        not_run = report.get("not_run", [])
        # C14 is expected NOT_RUN (deferred to CI)
        expected_not_run = {"C14"}
        actual_not_run = set(not_run)
        self.assertEqual(actual_not_run, expected_not_run,
                         f"unexpected NOT_RUN checks: {actual_not_run - expected_not_run}")
        self.assertEqual(failed, [], f"verification failures: {failed}\n{json.dumps(report, indent=2)}")


class MarketplaceTests(unittest.TestCase):
    """Test the Claude local marketplace structure and verification."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.mkdtemp(prefix="claude-marketplace-test-")
        result = subprocess.run(
            [sys.executable, str(ADAPTER_DIR / "export.py"),
             "--source", str(ROOT), "--out", cls._tmpdir, "--dev"],
            capture_output=True, text=True, encoding="utf-8",
            cwd=cls._tmpdir, timeout=120,
        )
        if result.returncode != 0:
            raise RuntimeError(f"export failed: {result.stdout + result.stderr}")
        data = json.loads(result.stdout)
        bundle_path = Path(data["marketplace_bundle"])
        cls._extract_dir = Path(cls._tmpdir) / "extracted"
        with zipfile.ZipFile(bundle_path) as zf:
            zf.extractall(cls._extract_dir)
        dirs = [d for d in cls._extract_dir.iterdir() if d.is_dir()]
        cls._root = dirs[0] if len(dirs) == 1 else cls._extract_dir

    @classmethod
    def tearDownClass(cls) -> None:
        import shutil
        shutil.rmtree(cls._tmpdir, ignore_errors=True)

    def test_marketplace_structure_valid(self) -> None:
        mp_json_path = self._root / ".claude-plugin" / "marketplace.json"
        self.assertTrue(mp_json_path.is_file())
        mp_json = json.loads(mp_json_path.read_text(encoding="utf-8"))
        self.assertEqual(mp_json["name"], "uiux-local")
        self.assertEqual(mp_json["owner"], {"name": "UIUX Local"})
        self.assertEqual(len(mp_json["plugins"]), 1)
        self.assertEqual(mp_json["plugins"][0]["name"], "ui-ux-design")
        self.assertEqual(mp_json["plugins"][0]["source"], "./plugins/ui-ux-design")

        plugin_root = self._root / "plugins" / "ui-ux-design"
        self.assertTrue(plugin_root.is_dir())
        self.assertTrue((plugin_root / ".claude-plugin" / "plugin.json").is_file())
        self.assertTrue((plugin_root / "SKILL.md").is_file())

    def test_verify_marketplace_success(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ADAPTER_DIR / "verify.py"), str(self._root), "--marketplace"],
            capture_output=True, text=True, encoding="utf-8",
            cwd=str(Path(self._tmpdir)), timeout=120,
        )
        self.assertEqual(result.returncode, 0, f"verification failed: {result.stdout + result.stderr}")
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "PASS")

    def test_verify_marketplace_failures(self) -> None:
        # We need a copy of the root to mutate
        with tempfile.TemporaryDirectory() as mut_dir:
            import shutil
            shutil.copytree(self._root, mut_dir, dirs_exist_ok=True)
            mut_root = Path(mut_dir)

            mp_json_path = mut_root / ".claude-plugin" / "marketplace.json"

            # Helper
            def run_verify() -> dict:
                result = subprocess.run(
                    [sys.executable, str(ADAPTER_DIR / "verify.py"), str(mut_root), "--marketplace"],
                    capture_output=True, text=True, encoding="utf-8",
                    cwd=str(Path(self._tmpdir)), timeout=120,
                )
                return json.loads(result.stdout)

            # Mutate: missing manifest
            mp_json_path.unlink()
            r = run_verify()
            self.assertEqual(r["status"], "FAIL")
            self.assertIn("M2", r["failed"])

            # Mutate: invalid plugin source
            mp_json_path.write_text(json.dumps({"name": "uiux-local", "owner": {"name": "UIUX Local"}, "plugins": [{"name": "ui-ux-design"}]}), encoding="utf-8")
            r = run_verify()
            self.assertIn("M9", r["failed"])

            # Mutate: absolute source path
            mp_json_path.write_text(json.dumps({"name": "uiux-local", "owner": {"name": "UIUX Local"}, "plugins": [{"name": "ui-ux-design", "source": "/absolute/path"}]}), encoding="utf-8")
            r = run_verify()
            self.assertIn("M9", r["failed"])

            # Mutate: missing plugin directory
            mp_json_path.write_text(json.dumps({"name": "uiux-local", "owner": {"name": "UIUX Local"}, "plugins": [{"name": "ui-ux-design", "source": "./plugins/does-not-exist"}]}), encoding="utf-8")
            r = run_verify()
            self.assertIn("M10", r["failed"])

            # Owner must use the current object schema and contain owner.name.
            mp_json_path.write_text(json.dumps({"name": "uiux-local", "owner": "uiux-local", "plugins": [{"name": "ui-ux-design", "source": "./plugins/ui-ux-design"}]}), encoding="utf-8")
            self.assertIn("M5", run_verify()["failed"])
            mp_json_path.write_text(json.dumps({"name": "wrong-marketplace", "owner": {}, "plugins": [{"name": "ui-ux-design", "source": "plugins/ui-ux-design"}]}), encoding="utf-8")
            failed = run_verify()["failed"]
            self.assertIn("M4", failed)
            self.assertIn("M5", failed)
            self.assertIn("M8", failed)
            self.assertIn("M9", failed)


if __name__ == "__main__":
    unittest.main()
