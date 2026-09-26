"""Relative Markdown links must resolve.

Agents follow the links in SKILL.md, skills/, knowledge/, workflows/ and review/ to load instructions, so a broken
link silently drops guidance. Two views are checked:

- repository: every tracked Markdown file's relative links resolve in the source checkout;
- package: links in files under the plugin root resolve inside the plugin root, except links into the repository's
  ``development/`` docs, which are repository-only (the same convention as ``uiux/tooling/validate.py``).
"""
from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

import _paths

REPO_ROOT = _paths.REPO_ROOT
PACKAGE_ROOT = _paths.PACKAGE_ROOT
SKIP_DIRS = {".git", "__pycache__", "node_modules", "dist", "build", ".venv", "venv"}
_FENCE = re.compile(r"```.*?```", re.DOTALL)
_LINK = re.compile(r"\]\(([^)\s]+)\)")


def relative_links(path: Path) -> list[tuple[str, Path]]:
    """(link text, resolved target) for every relative link outside fenced code blocks."""
    text = _FENCE.sub("", path.read_text(encoding="utf-8", errors="replace"))
    links = []
    for raw in _LINK.findall(text):
        target = raw.strip("<>").split("#", 1)[0]
        if not target or "://" in target or target.startswith(("mailto:", "/")):
            continue
        links.append((raw, (path.parent / target).resolve()))
    return links


def markdown_files(root: Path) -> list[Path]:
    try:
        listed = subprocess.run(["git", "-C", str(root), "ls-files", "*.md"], capture_output=True, text=True,
                                encoding="utf-8", check=True).stdout.splitlines()
        if listed:
            return [root / name for name in listed]
    except (OSError, subprocess.CalledProcessError):
        pass
    return [p for p in root.rglob("*.md") if not SKIP_DIRS.intersection(p.relative_to(root).parts)]


class MarkdownLinkTests(unittest.TestCase):
    def test_repository_links_resolve(self) -> None:
        if not (REPO_ROOT / ".git").exists():
            self.skipTest("not a source checkout")
        broken = [f"{md.relative_to(REPO_ROOT).as_posix()}: {raw}"
                  for md in markdown_files(REPO_ROOT) if md.is_file()
                  for raw, target in relative_links(md) if not target.exists()]
        self.assertEqual(broken, [], "broken relative links:\n" + "\n".join(broken))

    def test_packaged_links_stay_inside_the_plugin(self) -> None:
        package = PACKAGE_ROOT.resolve()
        problems = []
        for md in (p for p in package.rglob("*.md") if not SKIP_DIRS.intersection(p.relative_to(package).parts)):
            for raw, target in relative_links(md):
                inside = package == target or package in target.parents
                if inside and not target.exists():
                    problems.append(f"{md.relative_to(package).as_posix()}: {raw} (missing)")
                elif not inside and "development" not in target.relative_to(target.anchor).parts:
                    problems.append(f"{md.relative_to(package).as_posix()}: {raw} (points outside the plugin)")
        self.assertEqual(problems, [], "packaged links:\n" + "\n".join(problems))


if __name__ == "__main__":
    unittest.main()
