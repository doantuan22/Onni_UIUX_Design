"""Knowledge registry: the single query surface for all design knowledge.

Callers ask for styles, layouts, screens, motion, interactions, effects, recipes, graphics, technologies or
components by collection/kind/category/id/text and never need to know which file holds an entry. Backed by the
generated ``registry.json`` (see ``uiux.knowledge.catalog.render_registry``).
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from uiux.core import resources
from uiux.core.errors import RegistryError
from uiux.core.registry import load_json

COLLECTIONS = ("styles", "layouts", "screens", "motion", "interactions", "effects", "recipes", "graphics",
               "technologies", "components", "domains", "frameworks")


class KnowledgeLookupError(KeyError):
    pass


@lru_cache(maxsize=1)
def _registry() -> dict:
    data = load_json(resources.get_knowledge_registry_path(), "knowledge")
    if not isinstance(data.get("entries"), list) or not isinstance(data.get("collections"), dict):
        raise RegistryError("knowledge registry needs 'entries' and 'collections'", registry="knowledge")
    return data


def reset() -> None:
    _registry.cache_clear()


def collections() -> dict[str, int]:
    """Collection name -> number of entries."""
    return dict(_registry()["collections"])


def query(collection: str | None = None, kind: str | None = None, category: str | None = None,
          ids: list[str] | None = None, text: str | None = None) -> list[dict]:
    """Registry rows (id, kind, collection, category, name, file, line, summary) matching every given filter."""
    if collection is not None and collection not in COLLECTIONS:
        raise KnowledgeLookupError(f"unknown collection {collection!r}; expected one of {', '.join(COLLECTIONS)}")
    wanted = set(ids or [])
    needle = text.lower() if text else None
    rows = []
    for row in _registry()["entries"]:
        if collection and row["collection"] != collection:
            continue
        if kind and row["kind"] != kind:
            continue
        if category and row["category"] != category:
            continue
        if wanted and row["id"] not in wanted:
            continue
        if needle and needle not in f"{row['id']} {row['name']} {row['summary']}".lower():
            continue
        rows.append(dict(row))
    if wanted:
        missing = wanted - {row["id"] for row in rows}
        if missing:
            raise KnowledgeLookupError(f"unknown knowledge ids: {', '.join(sorted(missing))}")
    return rows


def locate(ident: str) -> dict:
    """Registry row for one id."""
    return query(ids=[ident])[0]


def read(ident: str) -> str:
    """Source text of one entry: its YAML block for catalog entries, the whole grammar file for components."""
    row = locate(ident)
    path = resources.resolve(row["file"])
    text = path.read_text(encoding="utf-8")
    if row["kind"] == "component":
        return text
    lines = text.splitlines()
    start = row["line"] - 1
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("```")), len(lines))
    return "\n".join(lines[start:end]) + "\n"


def get(ident: str) -> dict:
    """Parsed entry (catalog entries) or document row with content (components)."""
    row = locate(ident)
    if row["kind"] == "component":
        return {**row, "content": read(ident)}
    from uiux.knowledge import catalog  # internal parser; imported lazily to keep registry lookups cheap

    data = catalog.parse_block(read(ident), f"{row['file']}:{row['line']}")
    return {**data, "_file": row["file"], "_line": row["line"]}


def source_file(ident: str) -> Path:
    return resources.resolve(locate(ident)["file"])
