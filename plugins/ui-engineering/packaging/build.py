"""Deterministic artifact builder for the plugin package.

    python plugins/ui-engineering/packaging/build.py                         # release build of HEAD (clean tree required)
    python plugins/ui-engineering/packaging/build.py --commit v0.2.0         # release build of a tag/commit (clean tree required)
    python plugins/ui-engineering/packaging/build.py --dev                   # developer build of the working tree (never a release)
    python plugins/ui-engineering/packaging/build.py --verify                # build, then verify the artifact (verify.py)
    python plugins/ui-engineering/packaging/build.py --repo <dir> --out <dir>

Release flow: git commit -> git archive (LF via .gitattributes, core.autocrlf off) -> staging dir (system temp)
-> the staged tree's own package_files.py selects files -> preflight (registry fresh, VERSION == manifest,
CHANGELOG section) -> PACKAGE-MANIFEST.json -> deterministic zip + tar.gz -> SHA256SUMS -> build-info.json.

Developer builds read the working tree, are named ``<name>-<version>-dev``, are written under ``dist/dev/``,
and are marked ``build_mode: dev`` / ``release: false`` in every metadata file; ``verify.py --require-release``
rejects them. The source tree is never modified; staging happens in the system temp directory.

Exit codes: 0 built (and verified when --verify), 1 build refused or failed (JSON error with a stable code),
2 verification failed.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zlib
from pathlib import Path

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))
import artifact  # noqa: E402
from artifact import PackagingError  # noqa: E402

DEFAULT_REPO = _HERE.parents[2]
GIT = ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "-c", "core.quotepath=off"]
COMMIT_REQUIRED = "COMMIT_REQUIRED_BEFORE_RELEASE_BUILD"


# --------------------------------------------------------------------------- helpers
def clean_env(**extra: str) -> dict:
    """Environment for subprocesses: no inherited package overrides, no bytecode written into trees."""
    env = {k: v for k, v in os.environ.items() if k not in {"PYTHONPATH", "UIUX_ROOT", "UIUX_CONFIG", "UIUX_TEST_ROOT"}}
    env.update({"PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}, **extra)
    return env


def git(repo: Path, *args: str, binary: bool = False) -> subprocess.CompletedProcess:
    if shutil.which("git") is None:
        raise PackagingError("GIT_UNAVAILABLE", "git is required for release builds")
    return subprocess.run([*GIT, "-C", str(repo), *args], capture_output=True, text=not binary)


def run_tree_tool(root: Path, script: str, *args: str, python: str = sys.executable) -> tuple[int, str]:
    """Run a script *from the tree being built* (its own code and contract) with a neutral cwd."""
    with tempfile.TemporaryDirectory(prefix="uiux-build-cwd-") as cwd:
        result = subprocess.run([python, str(root / script), *args], capture_output=True, text=True,
                                encoding="utf-8", cwd=cwd, env=clean_env())
    return result.returncode, result.stdout + result.stderr


def package_root_of(root: Path) -> Path:
    cand = root / "plugins" / "ui-engineering"
    if (cand / "SKILL.md").is_file():
        return cand
    return root


def skill_name(root: Path) -> str:
    pkg = package_root_of(root)
    match = re.match(r"^---\n(.*?)\n---", (pkg / "SKILL.md").read_text(encoding="utf-8").replace("\r\n", "\n"), re.DOTALL)
    name = next((line.split(":", 1)[1].strip() for line in (match.group(1).splitlines() if match else [])
                 if line.startswith("name:")), None)
    if not name:
        raise PackagingError("MANIFEST_INVALID", "SKILL.md frontmatter has no name")
    return name


# --------------------------------------------------------------------------- sources
def release_source(repo: Path, commit: str, staging: Path) -> dict:
    top = git(repo, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        raise PackagingError("NOT_A_GIT_REPOSITORY", f"{repo} is not a git work tree", hint=COMMIT_REQUIRED)
    if Path(top.stdout.strip()).resolve() != repo.resolve():
        raise PackagingError("NOT_REPOSITORY_ROOT", "release builds must run on the repository root",
                             toplevel=top.stdout.strip())
    status = git(repo, "status", "--porcelain", "--untracked-files=normal")
    if status.returncode != 0:
        raise PackagingError("GIT_FAILED", status.stderr.strip())
    if status.stdout.strip():
        changed = status.stdout.splitlines()
        raise PackagingError("DIRTY_TREE", f"{COMMIT_REQUIRED}: working tree has {len(changed)} uncommitted change(s); "
                             "commit (with `git add --renormalize .`) or use --dev for a non-release build",
                             hint=COMMIT_REQUIRED, changes=changed[:20])
    resolved = git(repo, "rev-parse", "--verify", f"{commit}^{{commit}}")
    if resolved.returncode != 0:
        raise PackagingError("COMMIT_NOT_FOUND", f"cannot resolve commit {commit!r}", hint=COMMIT_REQUIRED)
    sha = resolved.stdout.strip()
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH") or git(repo, "log", "-1", "--format=%ct", sha).stdout.strip())
    archive = git(repo, "archive", "--format=tar", sha, binary=True)
    if archive.returncode != 0:
        raise PackagingError("GIT_FAILED", archive.stderr.decode("utf-8", "replace").strip())
    tar_path = staging.parent / "source.tar"
    tar_path.write_bytes(archive.stdout)
    with tarfile.open(tar_path) as source:
        members = [m for m in source.getmembers() if m.isfile() or m.isdir()]
        for member in members:
            artifact.canonical_path(member.name.rstrip("/"))
        extra = {"filter": "data"} if hasattr(tarfile, "data_filter") else {}
        source.extractall(staging, members=members, **extra)
    tar_path.unlink()
    return {"kind": "git-archive", "commit": sha, "worktree_clean": True, "epoch": epoch}


def dev_source(repo: Path, rules: dict) -> dict:
    head = git(repo, "rev-parse", "HEAD") if shutil.which("git") else None
    status = git(repo, "status", "--porcelain", "--untracked-files=normal") if head and head.returncode == 0 else None
    epoch = int(os.environ.get("SOURCE_DATE_EPOCH") or rules["artifact"]["dev_source_date_epoch"])
    return {"kind": "working-tree",
            "commit": head.stdout.strip() if head and head.returncode == 0 else None,
            "worktree_clean": (not status.stdout.strip()) if status and status.returncode == 0 else None,
            "epoch": epoch}


# --------------------------------------------------------------------------- preflight and assembly
def select(root: Path) -> list[dict]:
    pkg_script = "plugins/ui-engineering/packaging/package_files.py" if (root / "plugins/ui-engineering/packaging/package_files.py").is_file() else "packaging/package_files.py"
    code, output = run_tree_tool(root, pkg_script, "--list")
    try:
        result = json.loads(output[output.index("{"):])
    except ValueError as exc:
        raise PackagingError("PACKAGE_SELECTION_FAILED", f"package_files.py produced no JSON: {output[-500:]}") from exc
    if code != 0 or result["status"] != "PASS":
        raise PackagingError("PACKAGE_SELECTION_FAILED", "packaging contract violated", problems=result.get("problems"))
    return result["entries"]


def preflight(root: Path) -> dict:
    klib_script = "plugins/ui-engineering/scripts/knowledge_lib.py" if (root / "plugins/ui-engineering/scripts/knowledge_lib.py").is_file() else "scripts/knowledge_lib.py"
    code, output = run_tree_tool(root, klib_script, "check")
    if code != 0:
        raise PackagingError("REGISTRY_STALE", "knowledge catalogs/registry are invalid or stale; run "
                             "`python scripts/knowledge_lib.py index` and commit", output=output[-1000:])
    pkg = package_root_of(root)
    version = (pkg / "VERSION").read_text(encoding="utf-8").strip()
    manifest = json.loads((pkg / "plugin.json").read_text(encoding="utf-8"))
    if manifest.get("version") != version:
        raise PackagingError("VERSION_MISMATCH", "plugin manifest version differs from VERSION",
                             version=version, manifest=manifest.get("version"))
    schema = json.loads((pkg / "schemas/plugin.schema.json").read_text(encoding="utf-8"))
    problems = artifact.validate_schema(manifest, schema)
    if problems:
        raise PackagingError("MANIFEST_INVALID", "plugin manifest does not match its schema", problems=problems)
    changelog = (pkg / "CHANGELOG.md").read_text(encoding="utf-8")
    if not re.search(rf"^## {re.escape(version)}\b", changelog, re.MULTILINE):
        raise PackagingError("CHANGELOG_MISSING", f"CHANGELOG.md has no '## {version}' section", version=version)
    return {"version": version, "name": manifest["name"], "manifest_version": manifest["manifest_version"],
            "skill_name": skill_name(root)}


def package_manifest(root: Path, entries: list[dict], ident: dict, source: dict, rules: dict, dev: bool
                     ) -> tuple[dict, list[tuple[str, bytes]]]:
    pkg = package_root_of(root)
    binary = rules["artifact"]["binary_globs"]
    files, contents = [], []
    for entry in entries:
        rel = artifact.canonical_path(entry["path"])
        data = artifact.normalize(rel, (pkg / rel).read_bytes(), binary)
        files.append({"path": rel, "size": len(data), "sha256": artifact.sha256(data), "layer": entry["layer"],
                      "mode": rules["artifact"]["file_mode"]})
        contents.append((rel, data))
    rules_path = artifact.resolve_rules_path(root)
    layers_path = pkg / "uiux/core/layers.json"
    rules_bytes = b"".join((artifact.normalize(rules_path.name, rules_path.read_bytes(), binary),
                            artifact.normalize("layers.json", layers_path.read_bytes(), binary)))
    manifest = {"schema_version": 1, "archive_format_version": rules["artifact"]["format_version"],
                "name": ident["name"], "skill_name": ident["skill_name"], "python_package": "uiux",
                "version": ident["version"], "manifest_version": ident["manifest_version"],
                "build_mode": "dev" if dev else "release", "release": not dev,
                "source": {k: source[k] for k in ("kind", "commit", "worktree_clean")},
                "source_date_epoch": source["epoch"], "rules_sha256": artifact.sha256(rules_bytes),
                "file_count": len(files), "files": files}
    return manifest, contents


def build(repo: Path = DEFAULT_REPO, commit: str = "HEAD", dev: bool = False, out: Path | None = None,
          formats: list[str] | None = None) -> dict:
    repo = repo.resolve()
    with tempfile.TemporaryDirectory(prefix="uiux-build-") as temporary:
        rules = artifact.load_rules(repo)
        if dev:
            root, source = repo, dev_source(repo, rules)
        else:
            root = Path(temporary) / "staging"
            root.mkdir()
            source = release_source(repo, commit, root)
            rules = artifact.load_rules(root)  # the committed contract governs a release build
        formats = formats or rules["artifact"]["formats"]
        unknown = [f for f in formats if f not in ("zip", "tar.gz")]
        if unknown:
            raise PackagingError("INVALID_ARGUMENT", f"unsupported formats: {unknown}")
        ident = preflight(root)
        entries = select(root)
        manifest, contents = package_manifest(root, entries, ident, source, rules, dev)
        pkg = package_root_of(root)
        problems = artifact.validate_schema(manifest, json.loads(
            (pkg / "schemas/package-manifest.schema.json").read_text(encoding="utf-8")))
        if problems:
            raise PackagingError("MANIFEST_INVALID", "generated PACKAGE-MANIFEST.json violates its schema", problems=problems)

        base = f"{ident['name']}-{ident['version']}" + (rules["artifact"]["dev_suffix"] if dev else "")
        target = rules["artifact"]["dev_dir" if dev else "release_dir"].format(version=ident["version"])
        out_dir = (out or repo / target).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        manifest_bytes = artifact.canonical_json(manifest)
        archive_entries = [(f"{base}/{rel}", data) for rel, data in contents]
        archive_entries.append((f"{base}/{rules['artifact']['metadata_file']}", manifest_bytes))
        archive_entries.sort(key=lambda item: item[0].encode("utf-8"))
        mode, level, epoch = int(rules["artifact"]["file_mode"], 8), rules["artifact"]["compression_level"], source["epoch"]

        written = []
        for fmt in formats:
            path = out_dir / f"{base}.{fmt}"
            (artifact.write_zip if fmt == "zip" else artifact.write_targz)(path, archive_entries, epoch, mode, level)
            written.append(path)
        manifest_path = out_dir / f"{base}.package-manifest.json"
        manifest_path.write_bytes(manifest_bytes)
        sums = sorted([*written, manifest_path], key=lambda p: p.name)
        (out_dir / "SHA256SUMS").write_bytes("".join(f"{artifact.sha256_file(p)}  {p.name}\n" for p in sums).encode("ascii"))
        info = {"schema_version": 1, "name": ident["name"], "version": ident["version"],
                "build_mode": manifest["build_mode"], "release": manifest["release"], "source": manifest["source"],
                "source_date_epoch": epoch, "content_sha256": artifact.sha256(manifest_bytes),
                "archives": [{"file": p.name, "sha256": artifact.sha256_file(p), "size": p.stat().st_size} for p in written],
                "environment": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                                "platform": platform.platform(), "zlib": zlib.ZLIB_RUNTIME_VERSION},
                "tool": {"name": "plugins/ui-engineering/packaging/build.py", "archive_format_version": rules["artifact"]["format_version"]}}
        info_path = out_dir / f"{base}.build-info.json"
        info_path.write_bytes(artifact.canonical_json(info))
    return {"status": "BUILT", "build_mode": manifest["build_mode"], "release": manifest["release"],
            "name": ident["name"], "version": ident["version"], "commit": source["commit"],
            "files": manifest["file_count"], "content_sha256": info["content_sha256"], "out_dir": str(out_dir),
            "artifacts": [str(p) for p in written], "package_manifest": str(manifest_path),
            "build_info": str(info_path), "checksums": str(out_dir / "SHA256SUMS")}


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Build deterministic plugin artifacts")
    parser.add_argument("--repo", type=Path, default=DEFAULT_REPO, help="source repository root (default: this checkout)")
    parser.add_argument("--commit", default="HEAD", help="release source commit (default: HEAD)")
    parser.add_argument("--dev", action="store_true", help="developer build of the working tree (non-release)")
    parser.add_argument("--out", type=Path, help="output directory (default: dist/<version> or dist/dev/<version>)")
    parser.add_argument("--formats", default=None, help="comma-separated: zip,tar.gz")
    parser.add_argument("--verify", action="store_true", help="run verify.py on the built zip afterwards")
    args = parser.parse_args(argv)
    try:
        result = build(args.repo, args.commit, args.dev, args.out, args.formats.split(",") if args.formats else None)
    except PackagingError as exc:
        print(json.dumps(exc.to_dict(), indent=2))
        return 1
    if args.verify:
        import verify  # noqa: PLC0415 - same directory

        zips = [a for a in result["artifacts"] if a.endswith(".zip")] or result["artifacts"]
        report = verify.verify(Path(zips[0]), require_release=not args.dev)
        result["verification"] = {"status": report["status"], "report": report.get("report_path")}
        print(json.dumps(result, indent=2))
        return 0 if report["status"] == "PASS" else 2
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
