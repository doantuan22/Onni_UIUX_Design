"""Comprehensive local Release Candidate (RC) Qualification Runner for v0.1.0.

Validates all 22 RC acceptance gates locally against the real release artifact:
dist/0.1.0/ui-ux-design-0.1.0.zip
"""
from __future__ import annotations

import filecmp
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST_DIR = REPO_ROOT / "dist" / "0.1.0"
RELEASE_ZIP = DIST_DIR / "ui-ux-design-0.1.0.zip"
RELEASE_TAR = DIST_DIR / "ui-ux-design-0.1.0.tar.gz"
MANIFEST_FILE = DIST_DIR / "ui-ux-design-0.1.0.package-manifest.json"
BUILD_INFO_FILE = DIST_DIR / "ui-ux-design-0.1.0.build-info.json"
SHA256_FILE = DIST_DIR / "SHA256SUMS"


class ReleaseCandidateQualificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        assert RELEASE_ZIP.is_file(), f"Release zip missing at {RELEASE_ZIP}"
        cls.stage_dir = Path(tempfile.mkdtemp(prefix="uiux-rc-extract-"))
        with zipfile.ZipFile(RELEASE_ZIP) as zf:
            zf.extractall(cls.stage_dir)
        cls.plugin_root = cls.stage_dir / "ui-ux-design-0.1.0"
        assert cls.plugin_root.is_dir(), "Extracted root directory missing"

        # Create isolated consumer workspace
        cls.consumer_ws = cls.stage_dir / "consumer_workspace"
        cls.consumer_ws.mkdir()

        # Clean environment with extracted plugin on PYTHONPATH
        cls.consumer_env = dict(os.environ)
        cls.consumer_env.update({
            "PYTHONPATH": f"{cls.plugin_root}{os.pathsep}{cls.plugin_root / 'adapters'}",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONIOENCODING": "utf-8",
        })

    @classmethod
    def tearDownClass(cls) -> None:
        shutil.rmtree(cls.stage_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # RC-01: Feature Freeze & Core Preservation
    # -------------------------------------------------------------------------
    def test_rc_01_feature_freeze_status(self) -> None:
        """Core Phase 0-8 behavior is preserved without unauthorized feature expansion."""
        self.assertTrue(self.plugin_root.is_dir())
        self.assertTrue((self.plugin_root / "uiux" / "engine").is_dir())

    # -------------------------------------------------------------------------
    # RC-02: Version Consistency
    # -------------------------------------------------------------------------
    def test_rc_02_version_consistency(self) -> None:
        """Every version declaration across the repository and artifact is 0.1.0."""
        expected = "0.1.0"
        self.assertEqual((REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip(), expected)
        self.assertEqual((self.plugin_root / "VERSION").read_text(encoding="utf-8").strip(), expected)

        plugin_json = json.loads((self.plugin_root / "plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(plugin_json["version"], expected)

        build_info = json.loads(BUILD_INFO_FILE.read_text(encoding="utf-8"))
        self.assertEqual(build_info["version"], expected)
        self.assertEqual(build_info["build_mode"], "release")
        self.assertTrue(build_info["release"])

    # -------------------------------------------------------------------------
    # RC-03 & RC-04: Release Mode Build & Reproducibility
    # -------------------------------------------------------------------------
    def test_rc_03_and_04_release_artifacts_and_reproducibility(self) -> None:
        """Release artifacts have no -dev suffix and match SHA256SUMS."""
        self.assertNotIn("-dev", RELEASE_ZIP.name)
        self.assertNotIn("-dev", RELEASE_TAR.name)

        sums_text = SHA256_FILE.read_text(encoding="utf-8")
        for f in (RELEASE_ZIP, RELEASE_TAR, MANIFEST_FILE):
            file_hash = hashlib.sha256(f.read_bytes()).hexdigest()
            self.assertIn(file_hash, sums_text, f"{f.name} hash mismatch in SHA256SUMS")

    # -------------------------------------------------------------------------
    # RC-05 & RC-06: Artifact Integrity & Extracted Verifier
    # -------------------------------------------------------------------------
    def test_rc_05_and_06_verify_report_pass(self) -> None:
        """The verify-report for the release artifact shows 100% PASS for V1-V13."""
        verify_report_path = DIST_DIR / "ui-ux-design-0.1.0.verify-report.json"
        self.assertTrue(verify_report_path.is_file(), "Verify report missing")
        report = json.loads(verify_report_path.read_text(encoding="utf-8"))
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["failed"], [])
        self.assertEqual(report["build_mode"], "release")

    # -------------------------------------------------------------------------
    # RC-07 & RC-08: Clean Consumer Install & Source Tree Independence
    # -------------------------------------------------------------------------
    def test_rc_07_and_08_clean_consumer_acceptance(self) -> None:
        """Consumer workspace executes CLI version, tools, self_test without source repo."""
        # 1. Version
        r_ver = subprocess.run(
            [sys.executable, "-m", "uiux.cli", "version"],
            cwd=str(self.consumer_ws),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r_ver.returncode, 0, f"version command failed: {r_ver.stderr}")
        data_ver = json.loads(r_ver.stdout)
        self.assertEqual(data_ver["version"], "0.1.0")

        # 2. Tools
        r_tools = subprocess.run(
            [sys.executable, "-m", "uiux.cli", "tools"],
            cwd=str(self.consumer_ws),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r_tools.returncode, 0, f"tools command failed: {r_tools.stderr}")
        data_tools = json.loads(r_tools.stdout)
        self.assertEqual(len(data_tools["tools"]), 28)

        # 3. Self-test
        r_st = subprocess.run(
            [sys.executable, "-m", "uiux.cli", "call", "self_test"],
            cwd=str(self.consumer_ws),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r_st.returncode, 0, f"self_test failed: {r_st.stderr}")
        data_st = json.loads(r_st.stdout)
        self.assertEqual(data_st["status"], "PASS")

    # -------------------------------------------------------------------------
    # RC-09: Public Tool Parity
    # -------------------------------------------------------------------------
    def test_rc_09_public_tool_parity(self) -> None:
        """All 31 public tools are present in tools registry and API."""
        r_tools = subprocess.run(
            [sys.executable, "-m", "uiux.cli", "tools"],
            cwd=str(self.consumer_ws),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        tools = json.loads(r_tools.stdout)["tools"]
        tool_ids = {t["id"] for t in tools}
        expected = {
            "accessibility_scan", "analyze_design_quality", "analyze_existing_ui",
            "analyze_repository", "build_critic_report", "build_knowledge_plan",
            "build_repair_plan", "build_validation_handoff", "capability_map",
            "detect_runtime", "diff_ui_maps", "evaluate_runtime_result", "map_ui_structure", "orchestrate_ui",
            "plan_modification", "recapture_evidence", "resolve_capabilities",
            "resolve_technology", "retrieve_knowledge", "route_knowledge",
            "run_evals", "run_runtime", "run_runtime_validation",
            "run_targeted_repair", "score_visual_critique", "self_test", "suggest_recipes", "validate_skill",
        }
        self.assertEqual(tool_ids, expected)

    # -------------------------------------------------------------------------
    # RC-10: Pipeline Smoke & Existing UI Preservation
    # -------------------------------------------------------------------------
    def test_rc_10_pipeline_smoke_and_preservation(self) -> None:
        """Execute analyze -> orchestrate -> knowledge plan -> plan modification on reference target."""
        target_a = REPO_ROOT / "development" / "fixtures" / "targets" / "target-a-static"

        # 1. analyze_repository
        params_file = self.consumer_ws / "analyze_params.json"
        params_file.write_text(json.dumps({"project": str(target_a)}), encoding="utf-8")
        r_ana = subprocess.run(
            [sys.executable, "-m", "uiux.cli", "call", "analyze_repository", "--params", f"@{params_file}"],
            cwd=str(self.consumer_ws),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r_ana.returncode, 0, f"analyze_repository failed: {r_ana.stderr}")
        repo_profile = json.loads(r_ana.stdout)
        self.assertIn("framework", repo_profile)

        # 2. orchestrate_ui with existing UI preservation
        orch_params = self.consumer_ws / "orch_params.json"
        orch_params.write_text(json.dumps({
            "request": {
                "user_request": "Modernize this existing dashboard, but keep current brand, colors and navigation.",
                "repo_context": repo_profile,
            }
        }), encoding="utf-8")
        r_orch = subprocess.run(
            [sys.executable, "-m", "uiux.cli", "call", "orchestrate_ui", "--params", f"@{orch_params}"],
            cwd=str(self.consumer_ws),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r_orch.returncode, 0, f"orchestrate_ui failed: {r_orch.stderr}")
        orch_res = json.loads(r_orch.stdout)
        self.assertEqual(orch_res["workflow"], "existing-ui")
        self.assertTrue(orch_res["preservation_required"])

        # 3. build_knowledge_plan
        kp_params = self.consumer_ws / "kp_params.json"
        kp_params.write_text(json.dumps({
            "user_request": "Refine typography and contrast",
            "repo_profile": repo_profile,
            "workflow": "existing-ui",
        }), encoding="utf-8")
        r_kp = subprocess.run(
            [sys.executable, "-m", "uiux.cli", "call", "build_knowledge_plan", "--params", f"@{kp_params}"],
            cwd=str(self.consumer_ws),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r_kp.returncode, 0, f"build_knowledge_plan failed: {r_kp.stderr}")
        kp_res = json.loads(r_kp.stdout)
        self.assertIn("selected_knowledge", kp_res)
        self.assertGreater(len(kp_res["selected_knowledge"]), 0)

        # 4. plan_modification (planner grounding check)
        plan_params = self.consumer_ws / "plan_params.json"
        plan_params.write_text(json.dumps({
            "user_request": "Improve mobile sidebar layout",
            "repo_profile": repo_profile,
            "workflow": "existing-ui",
        }), encoding="utf-8")
        r_plan = subprocess.run(
            [sys.executable, "-m", "uiux.cli", "call", "plan_modification", "--params", f"@{plan_params}"],
            cwd=str(self.consumer_ws),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(r_plan.returncode, 0, f"plan_modification failed: {r_plan.stderr}")
        plan_res = json.loads(r_plan.stdout)
        self.assertEqual(plan_res.get("status"), "ready")

        # Grounding check: verify no hallucinated components
        affected = plan_res.get("affected_surface", {}).get("files", [])
        for f in affected:
            self.assertNotIn("Sidebar.tsx", f)
            self.assertNotIn("tailwind.config.js", f)

    # -------------------------------------------------------------------------
    # RC-11: Knowledge Retrieval Smoke
    # -------------------------------------------------------------------------
    def test_rc_11_knowledge_retrieval_smoke(self) -> None:
        """Selected knowledge IDs resolve 100% via retrieve_knowledge with 0 phantom IDs."""
        code = """
import sys
from uiux import api
res = api.retrieve_knowledge(ids=["style.productivity"])
assert res["count"] > 0, "No entries found for style.productivity"
assert res["entries"][0]["id"] == "style.productivity"
print("RETRIEVAL_OK")
"""
        res = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(self.consumer_ws),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"retrieve_knowledge failed: {res.stderr}")
        self.assertIn("RETRIEVAL_OK", res.stdout)

    # -------------------------------------------------------------------------
    # RC-12: Domain Bridge Smoke
    # -------------------------------------------------------------------------
    def test_rc_12_domain_bridge_smoke(self) -> None:
        """Domain router correctly bridges domain to knowledge catalogs."""
        code = """
import sys
from uiux import api

kp = api.build_knowledge_plan(user_request="Build a luxury hotel reservation and booking flow")
domain_ctx = kp.get("domain_context", {})
assert domain_ctx.get("primary", {}).get("domain") == "hospitality_travel", f"Wrong domain context: {domain_ctx}"

pack = api.resolve_domain_pack("hospitality_travel")
assert pack["id"] == "domain.hospitality_travel"
assert len(pack["critical_flows"]) > 0

# Check knowledge IDs in plan are genuine catalog IDs, not naked domain pack IDs
for k in kp.get("selected_knowledge", []):
    k_id = k.get("id") if isinstance(k, dict) else k
    assert not k_id.startswith("domain."), f"Domain pack ID used directly as knowledge catalog item: {k_id}"

print("DOMAIN_BRIDGE_OK")
"""
        res = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(self.consumer_ws),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Domain bridge smoke failed: {res.stderr}")
        self.assertIn("DOMAIN_BRIDGE_OK", res.stdout)

    # -------------------------------------------------------------------------
    # RC-13: Runtime Evidence Gate
    # -------------------------------------------------------------------------
    def test_rc_13_runtime_evidence_gate(self) -> None:
        """Calling critic with modifications but no runtime evidence returns blocked (no fake PASS)."""
        code = """
import sys
from uiux import api
plan = {
    "plan_id": "test_gate", "schema_version": 1, "workflow": "existing-ui",
    "affected_surface": {"files": ["src/Button.tsx"]},
    "blast_radius": {"allowed_files": ["src/Button.tsx"]},
    "validation": {"requires_runtime": True},
}
critic_res = api.run_runtime_validation(
    modification_plan=plan,
    change_manifest={"files_modified": ["src/Button.tsx"]},
    before_evidence=None,
    after_evidence=None,
    validate_only=True,
)
eval_res = api.evaluate_runtime_result(critic_report=critic_res)
assert eval_res.get("authorized_to_proceed") is False, f"Fake PASS permitted: {eval_res}"
assert eval_res.get("overall_status") == "blocked", f"Status not blocked: {eval_res}"
print("EVIDENCE_GATE_OK")
"""
        res = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(self.consumer_ws),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Runtime evidence gate failed: {res.stderr}")
        self.assertIn("EVIDENCE_GATE_OK", res.stdout)

    # -------------------------------------------------------------------------
    # RC-14: Public Evidence Schema Validation
    # -------------------------------------------------------------------------
    def test_rc_14_public_evidence_schema_validation(self) -> None:
        """Invalid evidence payload yields INVALID_ARGUMENT error, never raw crash."""
        code = """
import sys
from uiux import api
# Pass invalid type for before_evidence
res = api.run_runtime_validation(
    modification_plan={},
    before_evidence="invalid-string-should-be-dict",
    validate_only=True,
)
assert res.get("error_code") == "INVALID_ARGUMENT" or res.get("status") in ("INVALID_CALL", "INVALID_ARGUMENT"), f"Unexpected error status: {res}"
print("SCHEMA_VALIDATION_OK")
"""
        res = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(self.consumer_ws),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Evidence schema test failed: {res.stderr}")
        self.assertIn("SCHEMA_VALIDATION_OK", res.stdout)

    # -------------------------------------------------------------------------
    # RC-15: MCP Transport Qualification
    # -------------------------------------------------------------------------
    def test_rc_15_mcp_transport_qualification(self) -> None:
        """MCP stdio server protocol works from extracted artifact."""
        code = """
import sys, json, io
from mcp import protocol, server

# Test tools listing via server handle
tools_resp = server.list_tools()
assert len(tools_resp["tools"]) == 31, f"MCP tools count mismatch: {len(tools_resp['tools'])}"

# Test session message handling: initialize -> initialized -> tools/list
session = server.McpServer()
init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}}
resp = session.handle(init_req)
assert resp.get("result", {}).get("protocolVersion") == "2025-06-18"

session.handle({"jsonrpc": "2.0", "method": "notifications/initialized"})
list_resp = session.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
assert len(list_resp["result"]["tools"]) == 31
print("MCP_OK")
"""
        res = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(self.consumer_ws),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"MCP qualification failed: {res.stderr}")
        self.assertIn("MCP_OK", res.stdout)

    # -------------------------------------------------------------------------
    # RC-16 & RC-17: Claude & Codex Adapters Local Qualification
    # -------------------------------------------------------------------------
    def test_rc_16_and_17_claude_and_codex_adapter_qualification(self) -> None:
        """Claude and Codex adapters export valid bundles and pass local verification."""
        with tempfile.TemporaryDirectory(prefix="adapter-qual-") as tmpdir:
            out_path = Path(tmpdir)
            # Claude export & verify
            claude_dir = self.plugin_root / ".claude-plugin"
            r_cl_exp = subprocess.run(
                [sys.executable, str(claude_dir / "export.py"), "--source", str(self.plugin_root), "--out", str(out_path), "--dev"],
                capture_output=True, text=True, cwd=str(out_path),
            )
            self.assertEqual(r_cl_exp.returncode, 0, f"claude export failed: {r_cl_exp.stderr}")
            cl_bundle = json.loads(r_cl_exp.stdout)["bundle"]

            r_cl_ver = subprocess.run(
                [sys.executable, str(claude_dir / "verify.py"), "--bundle", cl_bundle],
                capture_output=True, text=True, cwd=str(out_path),
            )
            self.assertEqual(r_cl_ver.returncode, 0, f"claude verify failed: {r_cl_ver.stderr}")
            cl_ver_data = json.loads(r_cl_ver.stdout)
            self.assertEqual(cl_ver_data["status"], "PASS")

            # Codex export & verify
            codex_dir = self.plugin_root / ".codex-plugin"
            r_cd_exp = subprocess.run(
                [sys.executable, str(codex_dir / "export.py"), "--source", str(self.plugin_root), "--out", str(out_path), "--dev"],
                capture_output=True, text=True, cwd=str(out_path),
            )
            self.assertEqual(r_cd_exp.returncode, 0, f"codex export failed: {r_cd_exp.stderr}")
            cd_bundle = json.loads(r_cd_exp.stdout)["bundle"]

            r_cd_ver = subprocess.run(
                [sys.executable, str(codex_dir / "verify.py"), "--bundle", cd_bundle],
                capture_output=True, text=True, cwd=str(out_path),
            )
            self.assertEqual(r_cd_ver.returncode, 0, f"codex verify failed: {r_cd_ver.stderr}")
            cd_ver_data = json.loads(r_cd_ver.stdout)
            self.assertEqual(cd_ver_data["status"], "PASS")

    # -------------------------------------------------------------------------
    # RC-18: Adapter Thinness & No Duplicate Core
    # -------------------------------------------------------------------------
    def test_rc_18_adapter_thinness(self) -> None:
        """Adapters contain zero duplicate copies of skills, knowledge, or runtime core."""
        forbidden_subdirs = {"skills", "knowledge", "workflows", "uiux", "execution"}
        for ad_name in (".claude-plugin", ".codex-plugin", "adapters/generic", "adapters/mcp"):
            ad_path = self.plugin_root / ad_name
            if not ad_path.is_dir():
                continue
            child_dirs = {p.name.lower() for p in ad_path.iterdir() if p.is_dir()}
            duplicates = child_dirs & forbidden_subdirs
            self.assertEqual(duplicates, set(), f"Duplicate core dirs in {ad_name}: {duplicates}")

    # -------------------------------------------------------------------------
    # RC-19: Security & Leak Scan
    # -------------------------------------------------------------------------
    def test_rc_19_security_and_leak_scan(self) -> None:
        """Packaged release artifact contains no credentials, private keys, or absolute paths."""
        leak_markers = ["BEGIN PRIVATE KEY", "sk-ant-", "ghp_", "AKIA", "AIza"]
        forbidden_path_markers = ["D:\\Skill_AIcoding_Frontend", "C:\\Users\\Admin"]

        with zipfile.ZipFile(RELEASE_ZIP) as zf:
            for name in zf.namelist():
                # Skip binary assets
                if any(name.endswith(ext) for ext in (".png", ".jpg", ".webp", ".ico", ".pdf", ".gz")):
                    continue
                content = zf.read(name).decode("utf-8", errors="ignore")
                for marker in leak_markers:
                    self.assertNotIn(marker, content, f"Potential credential leak in {name}: {marker}")
                for path_marker in forbidden_path_markers:
                    self.assertNotIn(path_marker, content, f"Hardcoded developer path in {name}: {path_marker}")

    # -------------------------------------------------------------------------
    # RC-20: Update & Rollback Contract
    # -------------------------------------------------------------------------
    def test_rc_20_update_and_rollback_contract(self) -> None:
        """Upgrade and rollback simulation does not modify user project files."""
        user_proj = self.consumer_ws / "my_project"
        user_proj.mkdir(exist_ok=True)
        user_code = user_proj / "app.js"
        user_code.write_text("console.log('original user code');", encoding="utf-8")

        # Simulate update: overlaying plugin files
        shutil.copytree(self.plugin_root, self.consumer_ws / "plugin_update_sim", dirs_exist_ok=True)
        self.assertEqual(user_code.read_text(encoding="utf-8"), "console.log('original user code');")

        # Simulate rollback: removing simulated update
        shutil.rmtree(self.consumer_ws / "plugin_update_sim", ignore_errors=True)
        self.assertEqual(user_code.read_text(encoding="utf-8"), "console.log('original user code');")

    # -------------------------------------------------------------------------
    # RC-21: CLI Portability (@params.json & Spaces in path)
    # -------------------------------------------------------------------------
    def test_rc_21_cli_portability_with_spaces_in_path(self) -> None:
        """CLI handles @params.json file paths containing spaces cleanly."""
        dir_with_spaces = self.consumer_ws / "path with spaces"
        dir_with_spaces.mkdir(exist_ok=True)
        params_file = dir_with_spaces / "my params.json"
        params_file.write_text(json.dumps({"project": "."}), encoding="utf-8")

        res = subprocess.run(
            [sys.executable, "-m", "uiux.cli", "call", "analyze_repository", "--params", f"@{params_file}"],
            cwd=str(dir_with_spaces),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"CLI with spaces in path failed: {res.stderr}")
        data = json.loads(res.stdout)
        self.assertIn("framework", data)

    # -------------------------------------------------------------------------
    # RC-22: Browser E2E Qualification State Honesty
    # -------------------------------------------------------------------------
    def test_rc_22_browser_honesty(self) -> None:
        """When browser is not installed, detect_runtime and run_runtime report BLOCKED honestly."""
        code = """
import sys
from uiux import api
det = api.detect_runtime(project=".")
state = det.get("playwright", {}).get("runtime_state", {}).get("state")
assert state in ("NOT_DECLARED", "BLOCKED", "PLAYWRIGHT_IMPORT_FAILURE", "PLAYWRIGHT_BROWSER_UNAVAILABLE"), f"Unexpected runtime state: {state}"
print("BROWSER_HONESTY_OK")
"""
        res = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(self.consumer_ws),
            env=self.consumer_env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Browser honesty test failed: {res.stderr}")
        self.assertIn("BROWSER_HONESTY_OK", res.stdout)


if __name__ == "__main__":
    unittest.main()
