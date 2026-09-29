"""Design Knowledge System loader: parses catalog entries, validates schemas/references, builds the index.

Catalog entries are fenced ```yaml blocks whose first key is ``id:`` inside the knowledge roots. Only a
restricted, YAML-compatible subset is accepted so the loader stays standard-library only:
``key: scalar``, ``key: [a, b]``, nested mappings by two-space indentation, and ``- scalar`` sequences.

Internal module of the knowledge layer: parser, schema validation and generated index/registry. Public access
goes through ``uiux.knowledge.registry`` and ``uiux.api``.

Usage (compatibility CLI):
    python scripts/knowledge_lib.py check        # validate catalogs, INDEX.md and registry.json freshness
    python scripts/knowledge_lib.py index        # regenerate INDEX.md and registry.json
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from uiux.core import config, resources

ROOT = resources.get_package_root()
KNOWLEDGE_ROOTS = tuple(config.get()["paths"]["knowledge_roots"])
INDEX_PATH = config.get()["paths"]["knowledge_index"]
REGISTRY_PATH = config.get()["paths"]["knowledge_registry"]
COMPONENTS_PATH = config.get()["paths"]["components"]
# Registry collection names used by plugins and the public API (kind -> collection).
COLLECTIONS = {
    "style": "styles", "layout": "layouts", "screen": "screens", "motion": "motion", "interaction": "interactions",
    "effect": "effects", "recipe": "recipes", "graphics": "graphics", "technology": "technologies",
    "component": "components", "domain": "domains", "framework": "frameworks",
}

# Controlled vocabularies used by the Capability Resolver. Extend deliberately; see docs/design-knowledge-system.md.
DOMAINS = {
    "saas", "ai", "developer", "enterprise", "analytics", "fintech", "ecommerce", "luxury", "creative",
    "portfolio", "productivity", "consumer", "editorial", "marketplace", "travel", "hardware", "education",
    "healthcare", "gaming", "media", "agency", "data-platform", "public-sector", "fashion", "music",
}
ATTRIBUTES = {
    "premium", "technical", "calm", "playful", "bold", "trustworthy", "friendly", "luxurious", "minimal",
    "experimental", "futuristic", "warm", "precise", "energetic", "editorial", "nostalgic", "rebellious",
    "organic", "impressive", "approachable", "serious", "efficient", "crafted", "human", "innovative",
    "exclusive", "raw", "dense", "cinematic", "immersive", "clean", "confident", "timeless", "tactile",
    # perceived risks
    "flashy", "noisy", "cold", "chaotic", "dated", "gimmicky", "generic", "sterile", "intimidating",
    "childish", "cluttered", "heavy", "loud", "fragile", "unserious",
}
CONTEXTS = {"marketing", "application", "content", "commerce"}
CONTENT = {
    "product-media", "product-ui", "code", "metrics", "testimonials", "long-form", "listings", "data",
    "video", "illustrations", "3d-assets", "brand-photography", "case-studies", "logos",
}
DENSITY = {"low", "medium", "high"}
INTENSITY = {"low", "medium", "high"}
COST = {"none", "low", "medium", "high", "very-high"}
TIERS = {"primitive", "M1", "M2", "M3", "M4", "M5"}
SERVES = {"feedback", "state-change", "orientation", "continuity", "hierarchy", "attention", "storytelling",
          "delight", "brand-expression"}
KINDS = {"style", "layout", "screen", "motion", "interaction", "effect", "recipe", "technology", "graphics", "component", "domain", "framework"}

BASE_FIELDS = ("id", "name", "kind", "category")
SCHEMAS: dict[str, tuple[str, ...]] = {
    "style": ("family", "character", "visual_language", "layout", "typography", "color_behavior", "surface",
              "borders", "shadows", "imagery", "iconography", "motion", "interaction", "recommended_effects",
              "avoid_effects", "recommended_motion", "density", "accessibility_notes", "responsive_behavior",
              "good_for", "avoid_when", "compatible_patterns", "compatible_styles", "implementation_notes",
              "domains", "conveys", "perceived_risks", "intensity", "contexts", "motion_ceiling", "default_tell"),
    "layout": ("purpose", "anatomy", "hierarchy", "grid_behavior", "responsive", "content_requirements",
               "compatible_styles", "compatible_motion", "interactions", "accessibility", "implementation",
               "anti_patterns", "good_for", "avoid_when", "contexts", "density", "motion_cost", "default_tell"),
    "screen": ("anatomy", "hierarchy", "primary_actions", "secondary_actions", "states", "layout", "interaction",
               "motion", "responsive", "accessibility", "common_mistakes", "variants", "compatible_layouts",
               "key_interactions", "key_motion"),
    "motion": ("tier", "purpose", "serves", "trigger", "behavior", "duration", "easing", "spring", "entrance",
               "exit", "interruption", "responsive", "reduced_motion", "performance", "technology", "intensity",
               "contexts", "avoid_when", "examples"),
    "interaction": ("purpose", "flow", "input_methods", "states", "feedback", "motion", "error_behavior",
                    "accessibility", "mobile", "desktop", "recommended_use", "avoid_when", "contexts",
                    "min_interaction_intensity", "technology"),
    "effect": ("visual_purpose", "construction", "parameters", "compatible_styles", "recommended_contexts",
               "performance", "accessibility", "responsive", "implementation", "anti_patterns", "technology",
               "default_tell"),
    "recipe": ("domains", "conveys", "styles", "layouts", "typography", "surface", "color", "effects", "motion",
               "interactions", "technology", "avoid", "why"),
    "technology": ("use_for", "when_to_use", "when_not_to_use", "requires_dependency", "packages", "cost",
                   "fallback", "accessibility", "responsive", "lifecycle"),
    "graphics": ("purpose", "when_to_use", "when_not_to_use", "technology", "cost", "fallback", "accessibility",
                 "responsive", "lifecycle"),
    "component": (), # Handled flexibly to allow incremental upgrades
    "domain": (), 
    "framework": (),
}

# Optional Canonical Fields (P1)
CANONICAL_OPTIONAL = {
    "when", "avoid_when", "goal", "principles", "anatomy", "variants", "selection_rules", 
    "design_guidance", "responsive", "accessibility", "implementation", "anti_patterns", "validation"
}
NESTED_REQUIRED = {
    "motion": {"performance": ("cost", "notes"), "technology": ("preferred", "alternatives")},
    "effect": {"performance": ("cost", "notes"), "technology": ("preferred", "alternatives")},
    "interaction": {"flow": ("input", "feedback", "state", "motion", "result"),
                    "input_methods": ("mouse", "touch", "keyboard"),
                    "technology": ("preferred", "alternatives")},
}
# field -> kinds whose ids it may reference
REFERENCES: dict[str, dict[str, set[str]]] = {
    "style": {"compatible_styles": {"style"}, "recommended_effects": {"effect"}, "avoid_effects": {"effect"},
              "recommended_motion": {"motion"}, "compatible_patterns": {"layout"}},
    "layout": {"compatible_styles": {"style"}, "compatible_motion": {"motion"}, "interactions": {"interaction"}},
    "screen": {"compatible_layouts": {"layout"}, "key_interactions": {"interaction"}, "key_motion": {"motion"}},
    "effect": {"compatible_styles": {"style"}},
    "recipe": {"styles": {"style"}, "layouts": {"layout"}, "effects": {"effect"}, "motion": {"motion"},
               "interactions": {"interaction"}, "technology": {"technology"}},
    "graphics": {"technology": {"technology"}},
    "component": {}, "domain": {}, "framework": {}
}
TECH_REFERENCES = {"motion", "effect", "interaction"}  # technology.preferred / alternatives


class KnowledgeError(ValueError):
    pass


# --------------------------------------------------------------------------- parsing
_KEY = re.compile(r"^( *)([a-z0-9_]+):(?: (.*))?$")
_BAD_START = tuple("&*!|>%@`{?:,'#")


def _scalar(raw: str, where: str) -> str:
    value = raw.strip()
    if value.startswith('"'):
        if not value.endswith('"') or len(value) < 2:
            raise KnowledgeError(f"{where}: unterminated quoted scalar")
        return value[1:-1].replace('\\"', '"')
    if not value:
        raise KnowledgeError(f"{where}: empty scalar")
    if value.startswith(_BAD_START) or value.startswith("- "):
        raise KnowledgeError(f"{where}: plain scalar may not start with {value[0]!r}; quote it")
    if ": " in value or " #" in value or value.endswith(":"):
        raise KnowledgeError(f"{where}: plain scalar contains ': ' or ' #'; quote it")
    return value


def _inline_list(raw: str, where: str) -> list[str]:
    inner = raw.strip()[1:-1].strip()
    if not inner:
        return []
    items = []
    for part in inner.split(","):
        item = part.strip()
        if len(item) > 2 and item[0] == item[-1] == '"' and '"' not in item[1:-1]:
            items.append(item[1:-1])
            continue
        if not item or any(ch in item for ch in "[]{}:#\"'") or item.startswith(_BAD_START):
            raise KnowledgeError(f"{where}: invalid inline list item {item!r}")
        items.append(item)
    return items


def _value(raw: str, where: str) -> object:
    raw = raw.strip()
    if raw.startswith("["):
        if not raw.endswith("]"):
            raise KnowledgeError(f"{where}: unterminated inline list")
        return _inline_list(raw, where)
    return _scalar(raw, where)


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _parse_mapping(lines: list[str], i: int, indent: int, where: str) -> tuple[dict, int]:
    result: dict[str, object] = {}
    while i < len(lines):
        line = lines[i]
        if _indent(line) < indent:
            break
        if _indent(line) > indent:
            raise KnowledgeError(f"{where}: unexpected indentation: {line.strip()!r}")
        match = _KEY.match(line)
        if not match:
            raise KnowledgeError(f"{where}: expected 'key: value', got {line.strip()!r}")
        key, raw = match.group(2), match.group(3)
        if key in result:
            raise KnowledgeError(f"{where}: duplicate key {key!r}")
        i += 1
        if raw is not None and raw.strip():
            result[key] = _value(raw, f"{where}.{key}")
            continue
        if i >= len(lines) or _indent(lines[i]) <= indent:
            raise KnowledgeError(f"{where}.{key}: missing value")
        child = _indent(lines[i])
        if lines[i].lstrip().startswith("- "):
            items = []
            while i < len(lines) and _indent(lines[i]) == child and lines[i].lstrip().startswith("- "):
                items.append(_value(lines[i].lstrip()[2:], f"{where}.{key}[]"))
                i += 1
            result[key] = items
        else:
            result[key], i = _parse_mapping(lines, i, child, f"{where}.{key}")
    return result, i


def parse_block(text: str, where: str = "block") -> dict:
    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip() and not ln.lstrip().startswith("#")]
    if any("\t" in ln for ln in lines):
        raise KnowledgeError(f"{where}: tabs are not allowed")
    data, i = _parse_mapping(lines, 0, 0, where)
    if i != len(lines):
        raise KnowledgeError(f"{where}: trailing content")
    return data


_BLOCK = re.compile(r"^```yaml\n(.*?)^```", re.MULTILINE | re.DOTALL)


def iter_entries(root: Path = ROOT):
    for base in KNOWLEDGE_ROOTS:
        if not (root / base).is_dir():
            continue
        for path in sorted((root / base).rglob("*.md")):
            text = path.read_text(encoding="utf-8")
            for match in _BLOCK.finditer(text):
                body = match.group(1)
                first = next((ln for ln in body.splitlines() if ln.strip() and not ln.lstrip().startswith("#")), "")
                if not first.startswith("id:"):
                    continue
                line = text.count("\n", 0, match.start()) + 2
                rel = path.relative_to(root).as_posix()
                yield rel, line, body


def load(root: Path = ROOT) -> tuple[dict[str, dict], list[str]]:
    entries: dict[str, dict] = {}
    errors: list[str] = []
    for rel, line, body in iter_entries(root):
        where = f"{rel}:{line}"
        try:
            data = parse_block(body, where)
        except KnowledgeError as exc:
            errors.append(str(exc))
            continue
        ident = data.get("id")
        if not isinstance(ident, str) or not re.fullmatch(r"[a-z]+\.[a-z0-9-]+", ident):
            errors.append(f"{where}: invalid id {ident!r}")
            continue
        if ident in entries:
            errors.append(f"{where}: duplicate id {ident} (first in {entries[ident]['_file']})")
            continue
        data["_file"], data["_line"] = rel, line
        entries[ident] = data
    return entries, errors


# --------------------------------------------------------------------------- validation
def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return value
    return [] if value in (None, "none") else [value]  # type: ignore[list-item]


def _check_vocab(where: str, field: str, values: object, vocab: set[str], errors: list[str]) -> None:
    for value in _as_list(values):
        if value not in vocab:
            errors.append(f"{where}: {field} value {value!r} is not in the controlled vocabulary")


def validate(entries: dict[str, dict]) -> list[str]:
    errors: list[str] = []
    for ident, data in entries.items():
        where = f"{data['_file']}:{data['_line']} ({ident})"
        kind = data.get("kind")
        if kind not in KINDS:
            errors.append(f"{where}: unknown kind {kind!r}")
            continue
        if not ident.startswith(("tech." if kind == "technology" else kind + ".")):
            errors.append(f"{where}: id prefix must match kind {kind}")
        for field in BASE_FIELDS + SCHEMAS[kind]:
            if field not in data:
                errors.append(f"{where}: missing field {field}")
        
        # Validate structured canonical block if present
        if "applies_to" in data and not isinstance(data["applies_to"], dict):
            errors.append(f"{where}: applies_to must be a mapping")
        if "related" in data and not isinstance(data["related"], dict):
            errors.append(f"{where}: related must be a mapping")
        if "metadata" in data and not isinstance(data["metadata"], dict):
            errors.append(f"{where}: metadata must be a mapping")
        for field, subfields in NESTED_REQUIRED.get(kind, {}).items():
            value = data.get(field)
            if not isinstance(value, dict):
                errors.append(f"{where}: {field} must be a mapping")
                continue
            for sub in subfields:
                if sub not in value:
                    errors.append(f"{where}: missing field {field}.{sub}")
        # enumerations
        if kind == "style":
            _check_vocab(where, "domains", data.get("domains"), DOMAINS, errors)
            _check_vocab(where, "conveys", data.get("conveys"), ATTRIBUTES, errors)
            _check_vocab(where, "perceived_risks", data.get("perceived_risks"), ATTRIBUTES, errors)
            _check_vocab(where, "contexts", data.get("contexts"), CONTEXTS, errors)
            _check_vocab(where, "density", data.get("density"), DENSITY, errors)
            rng = data.get("intensity")
            if not (isinstance(rng, list) and len(rng) == 2 and all(x.isdigit() for x in rng)
                    and 1 <= int(rng[0]) <= int(rng[1]) <= 5):
                errors.append(f"{where}: intensity must be [min, max] within 1..5")
            if data.get("motion_ceiling") not in TIERS - {"primitive"}:
                errors.append(f"{where}: motion_ceiling must be M1..M5")
        if kind == "layout":
            _check_vocab(where, "contexts", data.get("contexts"), CONTEXTS, errors)
            _check_vocab(where, "content_requirements", data.get("content_requirements"), CONTENT, errors)
            _check_vocab(where, "density", data.get("density"), DENSITY, errors)
            _check_vocab(where, "motion_cost", data.get("motion_cost"), INTENSITY, errors)
        if kind == "motion":
            if data.get("tier") not in TIERS:
                errors.append(f"{where}: tier must be one of {sorted(TIERS)}")
            _check_vocab(where, "intensity", data.get("intensity"), INTENSITY, errors)
            _check_vocab(where, "contexts", data.get("contexts"), CONTEXTS, errors)
            _check_vocab(where, "serves", data.get("serves"), SERVES, errors)
        if kind == "interaction":
            _check_vocab(where, "contexts", data.get("contexts"), CONTEXTS, errors)
            if str(data.get("min_interaction_intensity")) not in {"1", "2", "3", "4", "5"}:
                errors.append(f"{where}: min_interaction_intensity must be 1..5")
        if kind == "effect":
            _check_vocab(where, "recommended_contexts", data.get("recommended_contexts"), CONTEXTS, errors)
        if kind == "recipe":
            _check_vocab(where, "domains", data.get("domains"), DOMAINS, errors)
            _check_vocab(where, "conveys", data.get("conveys"), ATTRIBUTES, errors)
        for container in (data.get("performance"), data):
            if isinstance(container, dict) and "cost" in container and kind in {"motion", "effect", "technology", "graphics"}:
                _check_vocab(where, "cost", container.get("cost"), COST, errors)
        for field in ("default_tell", "requires_dependency"):
            if field in data and data[field] not in {"true", "false"}:
                errors.append(f"{where}: {field} must be true or false")
        # references
        for field, allowed in REFERENCES.get(kind, {}).items():
            for target in _as_list(data.get(field)):
                ref = entries.get(target)
                if ref is None or ref.get("kind") not in allowed:
                    errors.append(f"{where}: {field} references unknown {'/'.join(sorted(allowed))} id {target!r}")
        if kind in TECH_REFERENCES and isinstance(data.get("technology"), dict):
            for sub in ("preferred", "alternatives"):
                for target in _as_list(data["technology"].get(sub)):
                    if entries.get(target, {}).get("kind") != "technology":
                        errors.append(f"{where}: technology.{sub} references unknown technology id {target!r}")
    return errors


# --------------------------------------------------------------------------- index
def summary(data: dict) -> str:
    for field in ("purpose", "character", "visual_purpose", "why", "use_for"):
        value = data.get(field)
        if isinstance(value, str):
            return value if len(value) <= 110 else value[:107].rstrip() + "..."
    return ""


def _index_link(file: str, root: Path) -> str:
    index_dir = (root / INDEX_PATH).parent
    return Path(os.path.relpath(root / file, index_dir)).as_posix()


def render_index(entries: dict[str, dict], root: Path = ROOT) -> str:
    order = ["style", "layout", "screen", "motion", "interaction", "effect", "graphics", "technology", "recipe"]
    lines = [
        "# Design knowledge index",
        "",
        "Generated by `python scripts/knowledge_lib.py index`; do not edit by hand. Load only the section for the",
        "kind you need, then read the single entry (search for `id: <id>` in its file). See [retrieval.md](retrieval.md).",
        "",
    ]
    for kind in order:
        items = sorted((i, d) for i, d in entries.items() if d["kind"] == kind)
        if not items:
            continue
        lines += [f"## {kind} ({len(items)})", "", "| id | category | file | summary |", "|---|---|---|---|"]
        for ident, data in items:
            rel = _index_link(data["_file"], root)
            text = summary(data).replace("|", "/")
            lines.append(f"| `{ident}` | {data.get('tier', data.get('category'))} | [{Path(rel).name}]({rel}) | {text} |")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def component_documents(root: Path = ROOT) -> list[dict]:
    """Prose component grammars exposed through the registry as documents (they have no YAML schema)."""
    docs = []
    for path in sorted((root / COMPONENTS_PATH).glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        
        # Skip if it's already a YAML catalog entry (has ```yaml with id: component.)
        if "```yaml\n" in text and "id: component." in text:
            continue
            
        title = next((ln[2:].strip() for ln in text.splitlines() if ln.startswith("# ")), path.stem)
        docs.append({"id": f"component.{path.stem}", "kind": "component", "collection": "components",
                     "category": "grammar", "name": title, "file": path.relative_to(root).as_posix(), "line": 1,
                     "summary": ""})
    return docs


def render_registry(entries: dict[str, dict], root: Path = ROOT) -> str:
    """Single machine-readable knowledge registry: every catalog entry and component grammar, by collection."""
    rows = [{"id": ident, "kind": data["kind"], "collection": COLLECTIONS[data["kind"]],
             "category": data.get("tier", data.get("category")), "name": data.get("name", ident),
             "file": data["_file"], "line": data["_line"], "summary": summary(data)}
            for ident, data in sorted(entries.items())]
    rows += component_documents(root)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["collection"]] = counts.get(row["collection"], 0) + 1
    registry = {"schema_version": 1, "generated_by": "python scripts/knowledge_lib.py index",
                "collections": dict(sorted(counts.items())), "entries": rows}
    return json.dumps(registry, indent=1, ensure_ascii=False) + "\n"


def check(root: Path = ROOT) -> list[str]:
    entries, errors = load(root)
    errors += validate(entries)
    index = root / INDEX_PATH
    if not index.is_file() or index.read_text(encoding="utf-8") != render_index(entries, root):
        errors.append(f"{INDEX_PATH} is missing or stale; run: python scripts/knowledge_lib.py index")
    registry = root / REGISTRY_PATH
    if not registry.is_file() or registry.read_text(encoding="utf-8") != render_registry(entries, root):
        errors.append(f"{REGISTRY_PATH} is missing or stale; run: python scripts/knowledge_lib.py index")
    return errors


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else "check"
    entries, errors = load()
    if command == "index":
        if errors:
            print("\n".join(errors)); return 1
        (ROOT / INDEX_PATH).write_text(render_index(entries), encoding="utf-8")
        (ROOT / REGISTRY_PATH).write_text(render_registry(entries), encoding="utf-8")
        print(f"wrote {INDEX_PATH} and {REGISTRY_PATH} ({len(entries)} entries + component grammars)")
        return 0
    problems = check()
    if problems:
        print("Knowledge validation failed:")
        print("\n".join(f"- {p}" for p in problems))
        return 1
    counts: dict[str, int] = {}
    for data in entries.values():
        counts[data["kind"]] = counts.get(data["kind"], 0) + 1
    print("Knowledge validation passed: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
