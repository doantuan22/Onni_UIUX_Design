"""Build a self-contained Codex plugin bundle from a verified generic artifact.

    python plugins/ui-engineering/.codex-plugin/export.py --source <extracted-artifact-root> --out dist/<version>/adapters/
    python plugins/ui-engineering/.codex-plugin/export.py --dev --source plugins/ui-engineering --out dist/dev/adapters/

The bundle is a ZIP containing the full generic payload plus Codex-specific overlay files
(plugin.json, mcp.json). The skill entry skills/ui-ux-workflow/SKILL.md comes from the payload: it is the
committed pointer to the canonical SKILL.md, so every relative link keeps resolving (a byte copy of SKILL.md
one directory level down would break them). It delegates to the common adapter framework
for safe overlay assembly and deterministic ZIP creation.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_COMMON = _HERE.parent / "adapters" / "common"
if str(_COMMON.parent) not in sys.path:
    sys.path.insert(0, str(_COMMON.parent))

from common import bundle, descriptor


def export(source: Path, out_dir: Path, dev: bool = False) -> dict:
    """Build the Codex plugin bundle and its local marketplace bundle."""
    source = source.resolve()
    
    # Delegate to common bundle utilities
    version = bundle.read_version(source)
    name = bundle.read_manifest_name(source)
    
    # Validate adapter.json schema (adapter metadata)
    descriptor.load_and_validate(_HERE, source / "schemas")

    # Add Codex-specific overlay files
    codex_manifest = bundle.render_template(
        _HERE / "templates" / "plugin.json", 
        {"version": version}
    )
    
    mcp_config = (_HERE / "templates" / "mcp.json").read_text(encoding="utf-8")
    
    # The skill entry is part of the generic payload (never re-rendered): it delegates to the canonical SKILL.md.
    for required in ("SKILL.md", "skills/ui-ux-workflow/SKILL.md"):
        if not (source / required).is_file():
            raise RuntimeError(f"{required} not found in {source}")

    overlay = [
        ("plugin.json", codex_manifest.encode("utf-8")),
        ("mcp.json", mcp_config.encode("utf-8")),
    ]

    # Collect generic payload using common utility (excluding files rendered by overlay)
    overlay_targets = {rel for rel, _ in overlay}
    payload = [p for p in bundle.collect_generic_payload(source) if p[0] not in overlay_targets]

    # Delegate safe assembly to common framework
    plugin_result = bundle.assemble_bundle(
        name=name,
        version=version,
        adapter_id="codex",
        payload=payload,
        overlay=overlay,
        out_dir=out_dir,
        dev=dev
    )
    # Build from the same exact payload and overlay as the verified Codex bundle.
    marketplace_manifest = {
        "name": "uiux-local",
        "interface": {"displayName": "UIUX Local Plugins"},
        "plugins": [{
            "name": name,
            "source": {"source": "local", "path": f"./plugins/{name}"},
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": "Developer Tools",
        }],
    }
    plugin_result.update(bundle.assemble_marketplace_bundle(
        name=name,
        version=version,
        adapter_id="codex",
        marketplace_manifest_path=".agents/plugins/marketplace.json",
        marketplace_manifest=marketplace_manifest,
        plugin_payload=payload + overlay,
        plugin_name=name,
        out_dir=out_dir,
        dev=dev,
    ))
    return plugin_result


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Build a Codex plugin bundle")
    parser.add_argument("--source", type=Path, help="extracted generic artifact root or repo root")
    parser.add_argument("--out", type=Path, required=True, help="output directory for the bundle ZIP")
    parser.add_argument("--dev", action="store_true", help="build from the working tree (non-release)")
    args = parser.parse_args(argv)

    source = args.source
    if source is None:
        source = _HERE.parent  # the plugin root (plugins/ui-engineering)

    try:
        result = export(source, args.out, args.dev)
    except RuntimeError as exc:
        print(json.dumps({"status": "ERROR", "error": {"message": str(exc)}}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
