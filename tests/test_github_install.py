"""Direct GitHub installation: the committed marketplace and plugin manifests must stay installable.

Claude Code reads ``.claude-plugin/marketplace.json`` at the repository root and the plugin's
``.claude-plugin/plugin.json``, ``.mcp.json`` and ``skills/<name>/SKILL.md``; Codex reads
``.agents/plugins/marketplace.json`` and ``.codex-plugin/plugin.json``. These files are committed
(not only rendered into bundles), so they must match VERSION, the exporters' rendered output and
the files they point to.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

import _paths

REPO_ROOT = _paths.REPO_ROOT
PACKAGE_ROOT = _paths.PACKAGE_ROOT
VERSION = (PACKAGE_ROOT / "VERSION").read_text(encoding="utf-8").strip()
PLUGIN_NAME = json.loads((PACKAGE_ROOT / "plugin.json").read_text(encoding="utf-8"))["name"]


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _frontmatter(path: Path) -> dict:
    match = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
    assert match, f"{path} has no frontmatter"
    return dict(line.split(": ", 1) for line in match.group(1).splitlines())


def _marketplace_source(marketplace_root: Path, source: str) -> Path:
    sys.path.insert(0, str(PACKAGE_ROOT / "adapters"))
    try:
        from common import bundle
    finally:
        sys.path.remove(str(PACKAGE_ROOT / "adapters"))
    resolved, problems = bundle.validate_marketplace_source_path(source, marketplace_root)
    assert not problems, problems
    return resolved


class ClaudeCodeInstallTests(unittest.TestCase):
    def test_plugin_manifest_matches_rendered_template(self) -> None:
        template = (PACKAGE_ROOT / ".claude-plugin/templates/claude-plugin.json").read_text(encoding="utf-8")
        expected = json.loads(template.replace("{version}", VERSION))
        self.assertEqual(_load(PACKAGE_ROOT / ".claude-plugin/plugin.json"), expected)

    def test_mcp_json_matches_exporter_and_points_to_shared_server(self) -> None:
        export = _load_module("claude_export", PACKAGE_ROOT / ".claude-plugin/export.py")
        committed = _load(PACKAGE_ROOT / ".mcp.json")
        self.assertEqual(committed, json.loads(export._mcp_json_content()))
        for server in committed["mcpServers"].values():
            scripts = [a for a in server["args"] if a.endswith(".py")]
            self.assertTrue(scripts)
            for arg in scripts:
                self.assertTrue(arg.startswith("${CLAUDE_PLUGIN_ROOT}/"), arg)
                self.assertTrue((PACKAGE_ROOT / arg.split("/", 1)[1]).is_file(), arg)

    def test_skill_is_discoverable_and_delegates_to_canonical_skill(self) -> None:
        skill = PACKAGE_ROOT / "skills/ui-ux-workflow/SKILL.md"
        self.assertTrue(skill.is_file())
        self.assertEqual(_frontmatter(skill), _frontmatter(PACKAGE_ROOT / "SKILL.md"))
        text = skill.read_text(encoding="utf-8")
        self.assertIn("../../SKILL.md", text)
        self.assertTrue((skill.parent / "../../SKILL.md").resolve().samefile(PACKAGE_ROOT / "SKILL.md"))

    def test_repository_marketplace_points_to_plugin(self) -> None:
        path = REPO_ROOT / ".claude-plugin/marketplace.json"
        if not path.is_file():
            self.skipTest("repository marketplace is not part of an extracted artifact")
        marketplace = _load(path)
        self.assertIsInstance(marketplace.get("name"), str)
        self.assertIsInstance(marketplace.get("owner", {}).get("name"), str)
        self.assertEqual(len(marketplace["plugins"]), 1)
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], PLUGIN_NAME)
        self.assertEqual(entry.get("version", VERSION), VERSION)
        plugin_root = _marketplace_source(REPO_ROOT, entry["source"])
        self.assertEqual(_load(plugin_root / ".claude-plugin/plugin.json")["name"], PLUGIN_NAME)


class LicenseTests(unittest.TestCase):
    """Apache-2.0: the packaged LICENSE/NOTICE match the repository copies and every manifest declares it."""

    def test_packaged_license_is_apache_2(self) -> None:
        text = (PACKAGE_ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Apache License", text)
        self.assertIn("Version 2.0, January 2004", text)
        self.assertTrue((PACKAGE_ROOT / "NOTICE").is_file())

    def test_manifests_declare_the_license(self) -> None:
        self.assertEqual(_load(PACKAGE_ROOT / "plugin.json")["license"], "Apache-2.0")
        for manifest in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json"):
            self.assertEqual(_load(PACKAGE_ROOT / manifest)["license"], "Apache-2.0", manifest)

    def test_repository_copies_match_packaged_copies(self) -> None:
        for name in ("LICENSE", "NOTICE"):
            path = REPO_ROOT / name
            if not path.is_file():
                self.skipTest("repository root is not part of an extracted artifact")
            self.assertEqual(path.read_bytes(), (PACKAGE_ROOT / name).read_bytes(), name)


class CodexInstallTests(unittest.TestCase):
    def test_plugin_manifest_references_existing_files(self) -> None:
        manifest = _load(PACKAGE_ROOT / ".codex-plugin/plugin.json")
        self.assertEqual(manifest["name"], PLUGIN_NAME)
        self.assertEqual(manifest["version"], VERSION)
        for skill in manifest["skills"].values():
            self.assertTrue((PACKAGE_ROOT / skill["path"]).is_file(), skill["path"])
        self.assertTrue((PACKAGE_ROOT / manifest["mcp"]["config"]).is_file())

    def test_mcp_config_matches_template_and_points_to_shared_server(self) -> None:
        manifest = _load(PACKAGE_ROOT / ".codex-plugin/plugin.json")
        committed = _load(PACKAGE_ROOT / manifest["mcp"]["config"])
        self.assertEqual(committed, _load(PACKAGE_ROOT / ".codex-plugin/templates/mcp.json"))
        for server in committed["mcpServers"].values():
            for arg in (a for a in server["args"] if a.endswith(".py")):
                self.assertTrue(arg.startswith("${PLUGIN_ROOT}/"), arg)
                self.assertTrue((PACKAGE_ROOT / arg.split("/", 1)[1]).is_file(), arg)

    def test_repository_marketplace_points_to_plugin(self) -> None:
        path = REPO_ROOT / ".agents/plugins/marketplace.json"
        if not path.is_file():
            self.skipTest("repository marketplace is not part of an extracted artifact")
        marketplace = _load(path)
        self.assertIsInstance(marketplace.get("name"), str)
        self.assertEqual(len(marketplace["plugins"]), 1)
        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], PLUGIN_NAME)
        self.assertEqual(entry["source"]["source"], "local")
        plugin_root = _marketplace_source(REPO_ROOT, entry["source"]["path"])
        self.assertEqual(_load(plugin_root / ".codex-plugin/plugin.json")["name"], PLUGIN_NAME)


if __name__ == "__main__":
    unittest.main()
