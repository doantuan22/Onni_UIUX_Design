"""Helpers for packaging tests: throwaway git repositories built from the package file list.

Tests never build from (or modify) the real repository: they copy the packaged files into a temporary git repo
with a deterministic commit, which also works when the suite runs against an extracted artifact (V13).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

import _paths

ROOT = _paths.PACKAGE_ROOT
PACKAGING = ROOT / "packaging"
if str(PACKAGING) not in sys.path:
    sys.path.insert(0, str(PACKAGING))

import artifact  # noqa: E402
import build  # noqa: E402
import package_files  # noqa: E402
import verify  # noqa: E402

GIT_AVAILABLE = shutil.which("git") is not None
DEFAULT_GITATTRIBUTES = "* text=auto eol=lf\n*.png binary\n"
COMMIT_DATE = "2026-01-02T03:04:05+00:00"
COMMIT_EPOCH = 1767323045


def git(repo: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "GIT_AUTHOR_DATE": COMMIT_DATE, "GIT_COMMITTER_DATE": COMMIT_DATE,
           "GIT_AUTHOR_NAME": "packaging-test", "GIT_AUTHOR_EMAIL": "packaging@test.invalid",
           "GIT_COMMITTER_NAME": "packaging-test", "GIT_COMMITTER_EMAIL": "packaging@test.invalid"}
    # gc.auto/maintenance.auto off: a background gc must not rewrite .git/objects while a test copies or clones it
    result = subprocess.run(["git", "-C", str(repo), "-c", "core.autocrlf=false", "-c", "commit.gpgsign=false",
                             "-c", "gc.auto=0", "-c", "maintenance.auto=false", *args],
                            capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed: {result.stderr}")
    return result


def make_repo(parent: Path, name: str = "repo") -> Path:
    """A committed repository containing exactly the package file list (+ .gitattributes)."""
    repo = (parent / name).resolve()
    repo.mkdir(parents=True)
    for rel in package_files.compute(ROOT)["included"]:
        target = repo / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / rel, target)
    source = ROOT / ".gitattributes"
    # write_bytes keeps LF on every OS (Path.write_text(newline=) needs Python 3.10+)
    text = source.read_text(encoding="utf-8") if source.is_file() else DEFAULT_GITATTRIBUTES
    (repo / ".gitattributes").write_bytes(text.replace("\r\n", "\n").encode("utf-8"))
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "fixture")
    return repo


def clone(repo: Path, parent: Path, name: str) -> Path:
    """An independent clone with the same commit (no raw copy of .git/objects, which races with git on macOS)."""
    target = (parent / name).resolve()
    git(parent, "clone", "-q", "--no-hardlinks", str(repo), str(target))
    return target


def commit_all(repo: Path, message: str = "change") -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)


def run_build(repo: Path, out: Path, *args: str) -> tuple[int, dict]:
    """Run build.py as a subprocess from an unrelated working directory."""
    with tempfile.TemporaryDirectory(prefix="uiux-test-cwd-") as cwd:
        result = subprocess.run([sys.executable, str(PACKAGING / "build.py"), "--repo", str(repo), "--out", str(out), *args],
                                capture_output=True, text=True, encoding="utf-8", cwd=cwd,
                                env={k: v for k, v in build.clean_env().items() if k != "SOURCE_DATE_EPOCH"})
    return result.returncode, json.loads(result.stdout)


def rewrite_zip(source: Path, target: Path, mutate) -> None:
    """Copy a built zip, let ``mutate(files: dict[str, bytes])`` edit relative paths, then refresh
    PACKAGE-MANIFEST.json hashes so only the intended check can fail."""
    with zipfile.ZipFile(source) as archive:
        names = [i.filename for i in archive.infolist()]
        top = names[0].split("/", 1)[0]
        files = {n.split("/", 1)[1]: archive.read(n) for n in names}
    manifest = json.loads(files.pop("PACKAGE-MANIFEST.json"))
    mutate(files)
    layers = {item["path"]: item["layer"] for item in manifest["files"]}
    entries = []
    for rel in sorted(files, key=lambda p: p.encode("utf-8")):
        data = files[rel]
        entries.append({"path": rel, "size": len(data), "sha256": artifact.sha256(data),
                        "layer": layers.get(rel, "core-skill"), "mode": "0644"})
    manifest["files"], manifest["file_count"] = entries, len(entries)
    files["PACKAGE-MANIFEST.json"] = artifact.canonical_json(manifest)
    items = sorted((f"{top}/{rel}", data) for rel, data in files.items())
    artifact.write_zip(target, items, manifest["source_date_epoch"], 0o644, 9)
