"""Build a self-contained Claude Code plugin bundle from a verified generic artifact.

    python plugins/ui-engineering/.claude-plugin/export.py --source <extracted-artifact-root> --out dist/<version>/adapters/
    python plugins/ui-engineering/.claude-plugin/export.py --dev --source plugins/ui-engineering --out dist/dev/adapters/

The bundle is a ZIP containing the full generic payload plus Claude-specific overlay files
(.claude-plugin/plugin.json, .mcp.json); the same files are committed in the source tree so the plugin
installs directly from GitHub, and the rendered overlay replaces them in the bundle. It delegates to the common adapter framework
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


def _mcp_json_content() -> str:
    """Render the .mcp.json (``mcpServers`` wrapper) with portable ${CLAUDE_PLUGIN_ROOT} paths."""
    return json.dumps({
        "mcpServers": {
            "ui-ux-design-mcp": {
                "command": "python3",
                "args": ["${CLAUDE_PLUGIN_ROOT}/adapters/mcp/server.py"],
                "env": {}
            }
        }
    }, indent=2, ensure_ascii=False) + "\n"


def export(source: Path, out_dir: Path, dev: bool = False) -> dict:
    """Build the Claude Code plugin bundle and marketplace bundle."""
    source = source.resolve()
    
    # Delegate to common bundle utilities
    version = bundle.read_version(source)
    name = bundle.read_manifest_name(source)
    
    plugin_manifest = json.loads((source / "plugin.json").read_text(encoding="utf-8"))
    description = plugin_manifest.get("description", "UI/UX Design Skill")

    # Delegate to common descriptor validator
    # Validate adapter.json schema (adapter metadata)
    descriptor.load_and_validate(_HERE, source / "schemas")

    # Add Claude-specific overlay files
    claude_manifest = bundle.render_template(
        _HERE / "templates" / "claude-plugin.json", 
        {"version": version}
    )
    mcp_config = _mcp_json_content()

    overlay = [
        (".claude-plugin/plugin.json", claude_manifest.encode("utf-8")),
        (".mcp.json", mcp_config.encode("utf-8")),
    ]

    # Collect generic payload using common utility (excluding files rendered by overlay)
    overlay_targets = {rel for rel, _ in overlay}
    payload = [p for p in bundle.collect_generic_payload(source) if p[0] not in overlay_targets]

    # Delegate safe assembly to common framework for standard plugin bundle
    plugin_result = bundle.assemble_bundle(
        name=name,
        version=version,
        adapter_id="claude-code",
        payload=payload,
        overlay=overlay,
        out_dir=out_dir,
        dev=dev
    )

    marketplace_manifest = {
        "name": "uiux-local",
        "owner": {"name": "UIUX Local"},
        "plugins": [{
            "name": name,
            "source": f"./plugins/{name}",
            "description": description,
        }],
    }
    plugin_result.update(bundle.assemble_marketplace_bundle(
        name=name,
        version=version,
        adapter_id="claude",
        marketplace_manifest_path=".claude-plugin/marketplace.json",
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
    parser = argparse.ArgumentParser(description="Build a Claude Code plugin bundle")
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
