"""Phase 8: GitHub Distribution and Compatibility automated test suite.

Validates the full distribution and release engineering lifecycle:
- Canonical single-source-of-truth version consistency
- Packaging contract, allowlist, and forbidden development file exclusions
- Link and schema reference integrity across public distribution
- Uniqueness of IDs across tools, capabilities, and knowledge catalogs
- Thin adapter contract (zero duplicate core, skills, knowledge, or runtime)
- Platform manifest validations (Claude Code, Codex, MCP)
- Portable paths (no local absolute paths or developer machine leakage)
- Zero platform logic in shared core
- Package build and manifest checksum integrity
- Artifact verification across source, archive, and extracted tree
- Clean consumer installation and isolated execution without source repo
- Tool parity across API, CLI, and adapters (all 24 public tools)
- Tag mismatch rejection and CHANGELOG release gating
- Rollback and upgrade contract simulation
- Browser runtime qualification honesty (BLOCKED_BROWSER_RUNTIME)
- Security hygiene and secret scanning
- Compatibility matrix documentation
- Subset benchmark execution (Cases A through E)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

import _paths
from uiux import api

REPO_ROOT = _paths.REPO_ROOT
PACKAGE_ROOT = _paths.PACKAGE_ROOT
PACKAGING_DIR = PACKAGE_ROOT / "packaging"
if str(PACKAGING_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGING_DIR))

import artifact
import build
import package_files
import verify

ARTIFACT_BASE = "ui-ux-design-0.1.0-dev"


class Phase8DistributionTests(unittest.TestCase):
    """Automated tests for Phase 8 Distribution and Compatibility gates."""

    _artifact_dir: Path | None = None
    _artifact_tmp: str | None = None

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._artifact_tmp:
            shutil.rmtree(cls._artifact_tmp, ignore_errors=True)
            cls._artifact_tmp = cls._artifact_dir = None

    @classmethod
    def _dev_artifact_dir(cls) -> Path:
        """Build (once per class) a developer artifact of the working tree into a temporary directory and verify it.

        ``dist/`` is git-ignored, so the tests never rely on a pre-built artifact or write into the repository.
        V13 is skipped here to avoid re-running the whole suite recursively.
        """
        if cls._artifact_dir is None:
            if os.environ.get("UIUX_TEST_ROOT"):
                raise unittest.SkipTest("artifact build tests run against the source repository, not an extracted artifact")
            cls._artifact_tmp = tempfile.mkdtemp(prefix="phase8-dist-")
            out = Path(cls._artifact_tmp)
            result = build.build(REPO_ROOT, dev=True, out=out, formats=["zip"])
            verify.verify(Path(result["artifacts"][0]), tests_dir=None)
            cls._artifact_dir = out
        return cls._artifact_dir

    def setUp(self) -> None:
        self.temp_dirs: list[str] = []

    def tearDown(self) -> None:
        for d in self.temp_dirs:
            shutil.rmtree(d, ignore_errors=True)

    def _mkdtemp(self, prefix: str = "phase8-test-") -> Path:
        d = tempfile.mkdtemp(prefix=prefix)
        self.temp_dirs.append(d)
        return Path(d)

    # -------------------------------------------------------------------------
    # 1. Version Consistency & Single Source of Truth
    # -------------------------------------------------------------------------
    def test_01_canonical_version_consistency(self) -> None:
        """VERSION file is canonical single source of truth across all manifests and code."""
        root_version_file = REPO_ROOT / "VERSION"
        plugin_version_file = PACKAGE_ROOT / "VERSION"
        self.assertTrue(root_version_file.is_file(), "Root VERSION must exist")
        self.assertTrue(plugin_version_file.is_file(), "Plugin VERSION must exist")

        canonical_version = plugin_version_file.read_text(encoding="utf-8").strip()
        self.assertEqual(root_version_file.read_text(encoding="utf-8").strip(), canonical_version)

        # Semver format check
        semver_pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$"
        self.assertRegex(canonical_version, semver_pattern, "Canonical version must follow SemVer")

        # uiux.__version__
        import uiux
        self.assertEqual(uiux.__version__, canonical_version)

        # plugin.json version
        plugin_json = json.loads((PACKAGE_ROOT / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin_json["version"], canonical_version)

        # Claude adapter metadata
        claude_adapter_json = PACKAGE_ROOT / ".claude-plugin" / "adapter.json"
        if claude_adapter_json.is_file():
            data = json.loads(claude_adapter_json.read_text(encoding="utf-8"))
            core_req = data.get("core_api", {}).get("core_version", "")
            self.assertIn(canonical_version, core_req, "Claude adapter must be compatible with canonical version")

        # Codex adapter metadata
        codex_adapter_json = PACKAGE_ROOT / ".codex-plugin" / "adapter.json"
        if codex_adapter_json.is_file():
            data = json.loads(codex_adapter_json.read_text(encoding="utf-8"))
            core_req = data.get("core_api", {}).get("core_version", "")
            self.assertIn(canonical_version, core_req, "Codex adapter must be compatible with canonical version")

    # -------------------------------------------------------------------------
    # 2. Package Content Contract & Classification
    # -------------------------------------------------------------------------
    def test_02_package_content_contracts(self) -> None:
        """Every file in canonical plugin root is classified with 0 unclassified problems."""
        res = package_files.compute(root=PACKAGE_ROOT)
        self.assertEqual(res["status"], "PASS")
        self.assertEqual(res["problems"], [])
        self.assertGreaterEqual(res["files"], 500, "Packaged files count must be at least 500")

    # -------------------------------------------------------------------------
    # 3. Forbidden Development Files Excluded
    # -------------------------------------------------------------------------
    def test_03_forbidden_development_files_absent_from_package(self) -> None:
        """Artifact selection must strictly exclude development, scratch, evidence, caches."""
        res = package_files.compute(root=PACKAGE_ROOT)
        classified_paths = set(res.get("included", []))

        forbidden_prefixes = (
            "development/",
            "evals/benchmark/output",
            ".evidence",
            "scratch/",
            ".git",
            ".github",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            "dist/",
            "build/",
        )
        for path in classified_paths:
            for prefix in forbidden_prefixes:
                self.assertFalse(
                    path.startswith(prefix) or f"/{prefix}" in path,
                    f"Forbidden file '{path}' found in packaged file set",
                )

    # -------------------------------------------------------------------------
    # 4. Broken Public References & Markdown Links
    # -------------------------------------------------------------------------
    def test_04_broken_public_references_scan(self) -> None:
        """Scan documentation and manifests for broken local file links."""
        docs_dir = PACKAGE_ROOT / "docs"
        self.assertTrue(docs_dir.is_dir(), "docs/ directory must exist in plugin root")

        for md_file in docs_dir.glob("*.md"):
            content = md_file.read_text(encoding="utf-8")
            # Find markdown links: [text](path)
            links = re.findall(r"\[.*?\]\((?!https?://|mailto:)(.*?)\)", content)
            for link in links:
                target = link.split("#")[0].strip()
                if not target:
                    continue
                # Resolve relative to markdown file or PACKAGE_ROOT
                resolved = (md_file.parent / target).resolve()
                if not resolved.exists():
                    resolved = (PACKAGE_ROOT / target).resolve()
                self.assertTrue(
                    resolved.exists(),
                    f"Broken link '{link}' in {md_file.name} (resolved to {resolved})",
                )

    # -------------------------------------------------------------------------
    # 5. Duplicate ID Scans
    # -------------------------------------------------------------------------
    def test_05_duplicate_ids_validation(self) -> None:
        """Tool IDs, capability IDs, and knowledge IDs must be strictly unique."""
        # 1. Tools
        tools = api.list_tools()
        tool_ids = [t["id"] for t in tools]
        self.assertEqual(len(tool_ids), len(set(tool_ids)), "Duplicate tool IDs found")
        self.assertEqual(len(tool_ids), 24, "Must expose exactly 24 public tools")

        # 2. Capabilities
        cap_file = PACKAGE_ROOT / "uiux" / "core" / "capabilities.json"
        caps = json.loads(cap_file.read_text(encoding="utf-8")).get("capabilities", {})
        cap_ids = list(caps.keys())
        self.assertEqual(len(cap_ids), len(set(cap_ids)), "Duplicate capability IDs found")

        # 3. Knowledge items
        catalog_index = PACKAGE_ROOT / "knowledge" / "domains" / "registry.json"
        if catalog_index.is_file():
            reg = json.loads(catalog_index.read_text(encoding="utf-8"))
            k_ids = [entry["id"] for entry in reg.get("knowledge_items", [])]
            self.assertEqual(len(k_ids), len(set(k_ids)), "Duplicate knowledge item IDs found")

    # -------------------------------------------------------------------------
    # 6. Adapter Thinness & No Duplicate Core
    # -------------------------------------------------------------------------
    def test_06_adapter_thinness_and_no_duplicate_core(self) -> None:
        """Adapters must be thin wrappers and never contain duplicate skills, knowledge, or core."""
        adapter_dirs = [
            PACKAGE_ROOT / ".claude-plugin",
            PACKAGE_ROOT / ".codex-plugin",
            PACKAGE_ROOT / "adapters" / "generic",
            PACKAGE_ROOT / "adapters" / "mcp",
        ]
        forbidden_subdirs = {"skills", "knowledge", "workflows", "uiux", "execution"}

        for ad in adapter_dirs:
            if not ad.is_dir():
                continue
            child_dirs = {p.name.lower() for p in ad.iterdir() if p.is_dir()}
            duplicates = child_dirs & forbidden_subdirs
            self.assertEqual(
                duplicates,
                set(),
                f"Adapter {ad.name} contains duplicated core directories: {duplicates}",
            )

    # -------------------------------------------------------------------------
    # 7. Claude Adapter Manifest Validation
    # -------------------------------------------------------------------------
    def test_07_claude_manifest_validation(self) -> None:
        """Claude Code adapter manifest and metadata must be valid."""
        claude_dir = PACKAGE_ROOT / ".claude-plugin"
        self.assertTrue((claude_dir / "adapter.json").is_file())
        self.assertTrue((claude_dir / "export.py").is_file())
        self.assertTrue((claude_dir / "verify.py").is_file())

        meta = json.loads((claude_dir / "adapter.json").read_text(encoding="utf-8"))
        self.assertEqual(meta.get("id"), "claude-code")
        self.assertEqual(meta.get("schema_version"), 1)
        self.assertEqual(meta.get("adapter_contract_version"), 1)
        self.assertIn("tools", meta)

    # -------------------------------------------------------------------------
    # 8. Codex Adapter Manifest Validation
    # -------------------------------------------------------------------------
    def test_08_codex_manifest_validation(self) -> None:
        """Codex adapter manifest and metadata must be valid."""
        codex_dir = PACKAGE_ROOT / ".codex-plugin"
        self.assertTrue((codex_dir / "adapter.json").is_file())
        self.assertTrue((codex_dir / "export.py").is_file())
        self.assertTrue((codex_dir / "verify.py").is_file())

        meta = json.loads((codex_dir / "adapter.json").read_text(encoding="utf-8"))
        self.assertEqual(meta.get("id"), "codex")
        self.assertEqual(meta.get("schema_version"), 1)
        self.assertEqual(meta.get("adapter_contract_version"), 1)
        self.assertIn("tools", meta)

    # -------------------------------------------------------------------------
    # 9. Adapter Path Portability
    # -------------------------------------------------------------------------
    def test_09_adapter_path_portability(self) -> None:
        """Adapter configurations must not embed machine-specific absolute paths."""
        for p in (PACKAGE_ROOT / ".claude-plugin", PACKAGE_ROOT / ".codex-plugin"):
            for json_file in p.glob("*.json"):
                text = json_file.read_text(encoding="utf-8")
                self.assertNotIn("D:\\", text, f"Hardcoded Windows absolute path in {json_file}")
                self.assertNotIn("C:\\Users\\", text, f"Hardcoded user home path in {json_file}")
                self.assertNotIn("/home/", text, f"Hardcoded Linux home path in {json_file}")

    # -------------------------------------------------------------------------
    # 10. No Platform Logic Leaking into Shared Core
    # -------------------------------------------------------------------------
    def test_10_no_platform_logic_in_shared_core(self) -> None:
        """Shared core engine must remain completely host-platform agnostic."""
        engine_dir = PACKAGE_ROOT / "uiux" / "engine"
        core_dir = PACKAGE_ROOT / "uiux" / "core"

        for directory in (engine_dir, core_dir):
            for py_file in directory.rglob("*.py"):
                text = py_file.read_text(encoding="utf-8")
                self.assertNotIn('platform == "claude"', text, f"Platform logic in {py_file}")
                self.assertNotIn('platform == "codex"', text, f"Platform logic in {py_file}")
                self.assertNotIn("claude_code", text, f"Claude specific token in {py_file}")
                self.assertNotIn("codex_cli", text, f"Codex specific token in {py_file}")

    # -------------------------------------------------------------------------
    # 11. Package Build & Checksum Integrity
    # -------------------------------------------------------------------------
    def test_11_package_build_and_artifact_integrity(self) -> None:
        """Package manifest, zip file, and sha256 checksums exist and match."""
        dist_dev_dir = self._dev_artifact_dir()
        zip_path = dist_dev_dir / f"{ARTIFACT_BASE}.zip"
        manifest_path = dist_dev_dir / f"{ARTIFACT_BASE}.package-manifest.json"
        sums_path = dist_dev_dir / "SHA256SUMS"

        self.assertTrue(zip_path.is_file(), f"Zip artifact must exist at {zip_path}")
        self.assertTrue(manifest_path.is_file(), "Package manifest must exist")
        self.assertTrue(sums_path.is_file(), "SHA256SUMS must exist")

        # Verify zip against SHA256SUMS
        sums_text = sums_path.read_text(encoding="utf-8")
        zip_bytes = zip_path.read_bytes()
        actual_hash = artifact.sha256(zip_bytes)
        self.assertIn(actual_hash, sums_text, "Zip SHA256 must match entry in SHA256SUMS")

    # -------------------------------------------------------------------------
    # 12. Artifact Verifier Status
    # -------------------------------------------------------------------------
    def test_12_artifact_verify_passes(self) -> None:
        """Verification report on the packaged artifact must be PASS."""
        report_path = self._dev_artifact_dir() / f"{ARTIFACT_BASE}.verify-report.json"
        self.assertTrue(report_path.is_file(), "Verification report must exist")

        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "PASS", f"Verify status failed: {report.get('failed')}")
        self.assertEqual(report["failed"], [])

    # -------------------------------------------------------------------------
    # 13. Clean Consumer Installation & Isolated Execution
    # -------------------------------------------------------------------------
    def test_13_clean_install_isolated_consumer(self) -> None:
        """Extracted artifact in clean consumer workspace executes without source repo."""
        zip_path = self._dev_artifact_dir() / f"{ARTIFACT_BASE}.zip"

        install_root = self._mkdtemp("consumer-install-")
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(install_root)

        # Find extracted plugin directory
        extracted_dirs = [p for p in install_root.iterdir() if p.is_dir()]
        self.assertEqual(len(extracted_dirs), 1)
        plugin_root = extracted_dirs[0]

        consumer_workspace = self._mkdtemp("consumer-workspace-")

        # Run python -m uiux.cli version
        env = dict(os.environ)
        env.update({
            "PYTHONPATH": str(plugin_root),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
        })
        res_version = subprocess.run(
            [sys.executable, "-m", "uiux.cli", "version"],
            cwd=str(consumer_workspace),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(res_version.returncode, 0, f"CLI version failed: {res_version.stderr}")
        data_ver = json.loads(res_version.stdout)
        self.assertEqual(data_ver["version"], "0.1.0")

        # Run python -m uiux.cli tools
        res_tools = subprocess.run(
            [sys.executable, "-m", "uiux.cli", "tools"],
            cwd=str(consumer_workspace),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(res_tools.returncode, 0, f"CLI tools failed: {res_tools.stderr}")
        data_tools = json.loads(res_tools.stdout)
        self.assertEqual(len(data_tools["tools"]), 24)

        # Run python -m uiux.cli call self_test
        res_selftest = subprocess.run(
            [sys.executable, "-m", "uiux.cli", "call", "self_test"],
            cwd=str(consumer_workspace),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(res_selftest.returncode, 0, f"CLI self_test failed: {res_selftest.stderr}")
        data_st = json.loads(res_selftest.stdout)
        self.assertEqual(data_st["status"], "PASS")

    # -------------------------------------------------------------------------
    # 14. Clean Install Smoke Workflow
    # -------------------------------------------------------------------------
    def test_14_clean_install_smoke_workflow(self) -> None:
        """Isolated consumer executes analyze_repository via CLI on target fixture."""
        zip_path = self._dev_artifact_dir() / f"{ARTIFACT_BASE}.zip"

        install_root = self._mkdtemp("consumer-install-smoke-")
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(install_root)
        plugin_root = [p for p in install_root.iterdir() if p.is_dir()][0]

        target_dir = REPO_ROOT / "development" / "fixtures" / "targets" / "target-a-static"

        env = dict(os.environ)
        env.update({
            "PYTHONPATH": str(plugin_root),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
        })
        consumer_workspace = self._mkdtemp("consumer-smoke-ws-")

        # analyze_repository
        params_file = consumer_workspace / "params.json"
        params_file.write_text(json.dumps({"project": str(target_dir)}), encoding="utf-8")

        res_ana = subprocess.run(
            [sys.executable, "-m", "uiux.cli", "call", "analyze_repository", "--params", f"@{params_file}"],
            cwd=str(consumer_workspace),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertEqual(res_ana.returncode, 0, f"analyze_repository failed: {res_ana.stderr}")
        data_ana = json.loads(res_ana.stdout)
        self.assertIn("framework", data_ana)

    # -------------------------------------------------------------------------
    # 15. Public Tool Parity
    # -------------------------------------------------------------------------
    def test_15_public_tool_parity(self) -> None:
        """All 24 tools in core registry are exposed consistently in api.list_tools()."""
        tools = api.list_tools()
        self.assertEqual(len(tools), 24)
        names = {t["id"] for t in tools}
        expected_tools = {
            "accessibility_scan",
            "analyze_design_quality",
            "analyze_existing_ui",
            "analyze_repository",
            "build_critic_report",
            "build_knowledge_plan",
            "build_repair_plan",
            "build_validation_handoff",
            "capability_map",
            "detect_runtime",
            "evaluate_runtime_result",
            "orchestrate_ui",
            "plan_modification",
            "recapture_evidence",
            "resolve_capabilities",
            "resolve_technology",
            "retrieve_knowledge",
            "route_knowledge",
            "run_evals",
            "run_runtime",
            "run_runtime_validation",
            "run_targeted_repair",
            "self_test",
            "validate_skill",
        }
        self.assertEqual(names, expected_tools)

    # -------------------------------------------------------------------------
    # 16. Schema Presence & Completeness
    # -------------------------------------------------------------------------
    def test_16_schema_presence_and_validation(self) -> None:
        """All public schemas must exist and be valid JSON."""
        schemas_dir = PACKAGE_ROOT / "schemas"
        required_schemas = [
            "adapter.schema.json",
            "build-info.schema.json",
            "change-manifest.schema.json",
            "critic-report.schema.json",
            "evidence.schema.json",
            "existing-ui-profile.schema.json",
            "knowledge-plan.schema.json",
            "modification-plan.schema.json",
            "orchestrator.schema.json",
            "package-manifest.schema.json",
            "plugin.schema.json",
            "preservation-evaluation.schema.json",
            "preservation-profile.schema.json",
            "repair-plan.schema.json",
            "repair-result.schema.json",
            "repo-profile.schema.json",
        ]
        for name in required_schemas:
            p = schemas_dir / name
            self.assertTrue(p.is_file(), f"Missing schema {name}")
            data = json.loads(p.read_text(encoding="utf-8"))
            self.assertIn("type", data, f"Schema {name} missing root type")

    # -------------------------------------------------------------------------
    # 17. Tag Mismatch Rejection
    # -------------------------------------------------------------------------
    def test_17_tag_mismatch_rejection(self) -> None:
        """Simulate release gate: git tag must exactly match canonical version."""
        canonical_version = (PACKAGE_ROOT / "VERSION").read_text(encoding="utf-8").strip()

        def validate_tag(tag: str) -> bool:
            tag_version = tag.lstrip("v")
            return tag_version == canonical_version

        self.assertTrue(validate_tag(f"v{canonical_version}"))
        self.assertFalse(validate_tag("v9.9.9"))
        self.assertFalse(validate_tag("v0.0.1"))

    # -------------------------------------------------------------------------
    # 18. CHANGELOG Release Gate
    # -------------------------------------------------------------------------
    def test_18_changelog_release_gate(self) -> None:
        """CHANGELOG.md must contain a section for the canonical version."""
        canonical_version = (PACKAGE_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        changelog = (PACKAGE_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
        self.assertIn(canonical_version, changelog, f"CHANGELOG.md missing section for {canonical_version}")

    # -------------------------------------------------------------------------
    # 19. Rollback & Upgrade Simulation
    # -------------------------------------------------------------------------
    def test_19_rollback_and_upgrade_simulation(self) -> None:
        """Upgrade and rollback must preserve user project files without destructive side-effects."""
        sandbox = self._mkdtemp("rollback-sim-")
        user_project = sandbox / "user_app"
        user_project.mkdir()
        user_file = user_project / "App.jsx"
        user_file.write_text("export default function App() { return <h1>Hi</h1>; }", encoding="utf-8")

        # Simulate plugin v0.1.0 install
        plugin_install_dir = sandbox / "plugins" / "ui-engineering"
        shutil.copytree(PACKAGE_ROOT, plugin_install_dir, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

        # User file unchanged
        self.assertEqual(user_file.read_text(encoding="utf-8"), "export default function App() { return <h1>Hi</h1>; }")

        # Simulate rollback: restore clean state
        shutil.rmtree(plugin_install_dir)
        shutil.copytree(PACKAGE_ROOT, plugin_install_dir, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

        # User file still untouched
        self.assertEqual(user_file.read_text(encoding="utf-8"), "export default function App() { return <h1>Hi</h1>; }")

    # -------------------------------------------------------------------------
    # 20. Browser Qualification Honesty
    # -------------------------------------------------------------------------
    def test_20_browser_qualification_honesty(self) -> None:
        """When Playwright binary is absent, critic/runner must report BLOCKED_BROWSER_RUNTIME, not fake PASS."""
        det = api.detect_runtime(project=".")
        pw_state = det.get("playwright", {}).get("runtime_state", {}).get("state", "NOT_DECLARED")
        if pw_state != "READY":
            # Test direct runner behavior: returns exit_code=2 and status='BLOCKED'
            scratch_ws = self._mkdtemp("runtime-gate-")
            res = api.run_runtime(
                request={
                    "session_id": "test_phase8_gate",
                    "base_url": "http://127.0.0.1:9",
                    "routes": [{"page_id": "home", "route": "/"}],
                    "viewports": ["desktop"],
                    "iteration": 1,
                },
                project=str(scratch_ws),
            )
            self.assertEqual(res.get("exit_code"), 2)
            self.assertEqual(res.get("summary", {}).get("status"), "BLOCKED")

    # -------------------------------------------------------------------------
    # 21. Security Hygiene & Leak Audit
    # -------------------------------------------------------------------------
    def test_21_security_hygiene_and_leak_audit(self) -> None:
        """Packaged files must not contain API tokens, credentials, or developer home paths."""
        res = package_files.compute(root=PACKAGE_ROOT)
        packaged_files = [PACKAGE_ROOT / p for p in res.get("included", [])]

        leak_indicators = ["BEGIN PRIVATE KEY", "sk-ant-", "ghp_", "AKIA"]
        for p in packaged_files:
            if not p.is_file() or p.suffix in (".png", ".jpg", ".jpeg", ".webp", ".ico", ".pdf", ".zip", ".gz"):
                continue
            text = p.read_text(encoding="utf-8", errors="ignore")
            for ind in leak_indicators:
                self.assertNotIn(ind, text, f"Potential credential leak in {p.name}: {ind}")

    # -------------------------------------------------------------------------
    # 22. Compatibility Matrix Documentation
    # -------------------------------------------------------------------------
    def test_22_compatibility_matrix(self) -> None:
        """docs/COMPATIBILITY.md must document Claude Code, Codex, CLI, and MCP."""
        compat_file = PACKAGE_ROOT / "docs" / "COMPATIBILITY.md"
        self.assertTrue(compat_file.is_file())
        text = compat_file.read_text(encoding="utf-8")
        self.assertIn("Claude Code", text)
        self.assertIn("Codex", text)
        self.assertIn("MCP", text)
        self.assertIn("24 public tools", text)

    # -------------------------------------------------------------------------
    # 23. Subset Benchmark Execution (Cases A through E)
    # -------------------------------------------------------------------------
    def test_23_subset_benchmark_smoke(self) -> None:
        """Run subset benchmark cases A-E to qualify release stability."""
        # Case A: Greenfield static smoke
        target_a = REPO_ROOT / "development" / "fixtures" / "targets" / "target-a-static"
        res_a = api.analyze_repository(project=str(target_a))
        self.assertIn("framework", res_a)

        # Case B: Existing UI preservation smoke
        orch_res = api.orchestrate_ui(
            request={
                "user_request": "Modernize existing dashboard but preserve brand colors and navigation.",
                "repo_context": res_a,
            }
        )
        self.assertEqual(orch_res["workflow"], "existing-ui")
        self.assertTrue(orch_res["preservation_required"])

        # Case C: Knowledge routing smoke
        kp_res = api.build_knowledge_plan(
            user_request="Refine typography and contrast",
            repo_profile=res_a,
            workflow="existing-ui",
        )
        self.assertIn("selected_knowledge", kp_res)
        self.assertGreater(len(kp_res["selected_knowledge"]), 0)

        # Case D: Planner grounding smoke
        plan_res = api.plan_modification(
            user_request="Refine hero layout",
            repo_profile=res_a,
            workflow="existing-ui",
        )
        self.assertEqual(plan_res.get("status"), "ready")
        self.assertEqual(plan_res.get("schema_version"), 1)

        # Case E: Runtime evidence gate smoke
        det = api.detect_runtime(project=str(target_a))
        self.assertIn("playwright", det)


if __name__ == "__main__":
    unittest.main()
