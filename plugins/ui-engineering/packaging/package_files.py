"""Compute the package file list from the packaging contract (package-rules.json + uiux/core/layers.json).

    python plugins/ui-engineering/packaging/package_files.py            # summary JSON
    python plugins/ui-engineering/packaging/package_files.py --list     # plus "included" paths and per-file "entries" (path, layer)

Uses only the public Core API (architecture layers) and package-rules.json. build.py and verify.py run *this file
from the tree being packaged or verified*, so an artifact is always selected by its own contract.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_PLUGIN_ROOT = _HERE.parent
PACKAGE_ROOT = Path(os.environ.get("UIUX_ROOT", _PLUGIN_ROOT)).resolve()
for entry in (str(PACKAGE_ROOT), str(_HERE)):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from uiux import api  # noqa: E402
import artifact  # noqa: E402  (packaging primitives; same directory)

RULES_PATH = _HERE / "package-rules.json"


def _match(rel: str, pattern: str) -> bool:
    """Backward-compatible name for the shared matcher."""
    return artifact.match(rel, pattern)


def _excluded_by_glob(rel: str, globs: list[str]) -> bool:
    return artifact.matches_any(rel, globs)


def compute(root: Path = PACKAGE_ROOT, rules_path: Path = RULES_PATH) -> dict:
    rules = json.loads(rules_path.read_text(encoding="utf-8"))
    entries, excluded, unclassified = [], {}, []
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in rules["exclude_dirs"])
        for name in sorted(filenames):
            rel = (Path(directory) / name).relative_to(root).as_posix()
            layer = api.layer_of(rel)
            if layer is None:
                unclassified.append(rel)
                continue
            if layer in rules["exclude_layers"]:
                excluded[f"layer:{layer}"] = excluded.get(f"layer:{layer}", 0) + 1
                continue
            if _excluded_by_glob(rel, rules["exclude_globs"]):
                excluded["glob"] = excluded.get("glob", 0) + 1
                continue
            entries.append({"path": rel, "layer": layer})
    entries.sort(key=lambda item: item["path"].encode("utf-8"))
    included = [item["path"] for item in entries]
    problems = [f"unclassified file: {rel}" for rel in unclassified]
    problems += [f"required file not packaged: {rel}" for rel in rules["must_include"] if rel not in included]
    problems += [f"forbidden file packaged: {rel}" for rel in included
                 if any(rel.startswith(prefix) for prefix in rules["must_exclude_prefixes"])]
    return {"status": "FAIL" if problems else "PASS", "version": api.version(), "files": len(included),
            "excluded": excluded, "problems": problems, "included": included, "entries": entries}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Plugin package file list (dry run)")
    parser.add_argument("--list", action="store_true", help="include the file list and per-file layers")
    args = parser.parse_args(argv)
    result = compute()
    if not args.list:
        result = {k: v for k, v in result.items() if k not in ("included", "entries")}
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
