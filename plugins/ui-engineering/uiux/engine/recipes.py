"""Code recipe suggestions: rank the React + Tailwind / Next.js recipes for each section of a UI map.

Registry: knowledge/code-recipes/index.json. A recipe fits a section when its roles include the section's role and it
replaces the default-banlist signals map_ui_structure found there. Motion recipes respect the dependency policy: a
library already installed is reused; otherwise one library is proposed only with ``allow_motion_library`` (Elevate /
Reimagine), and without it the recipe's CSS fallback is offered. Nothing is installed.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from uiux.core.resources import get_package_root

RECIPES_DIR = "knowledge/code-recipes"
_LIBRARY_PACKAGES = {"motion": ("motion", "framer-motion"), "gsap": ("gsap",)}
_REACT_FRAMEWORKS = ("nextjs", "next", "react", "remix", "gatsby", "vite-react", None, "")


def load_index(root: Path | None = None) -> dict[str, Any]:
    root = root or get_package_root()
    return json.loads((root / RECIPES_DIR / "index.json").read_text(encoding="utf-8"))


def _library_status(deps: list[str], existing: set[str], allow: bool, sanctioned: str | None) -> tuple[str, str | None]:
    """(available | needs_install | css_fallback, library to install)."""
    for dep in deps:
        if not any(pkg in existing for pkg in _LIBRARY_PACKAGES.get(dep, (dep,))):
            if allow and dep == sanctioned:
                return "needs_install", dep
            return "css_fallback", None
    return "available", None


def _entry(recipe: dict[str, Any], root: Path, include_code: bool, score: float, why: list[str],
           status: str = "available", install: str | None = None) -> dict[str, Any]:
    out = {"id": recipe["id"], "title": recipe["title"], "kind": recipe["kind"],
           "file": f"{RECIPES_DIR}/{recipe['file']}", "score": round(score, 2), "why": why,
           "signature_moves": recipe["signature_moves"], "client": recipe["client"], "status": status}
    if install:
        out["install"] = f"npm install {install}"
    if status == "css_fallback" and recipe.get("css_fallback"):
        out["css_fallback"] = recipe["css_fallback"]
    if recipe.get("notes"):
        out["notes"] = recipe["notes"]
    if include_code:
        out["code"] = (root / RECIPES_DIR / recipe["file"]).read_text(encoding="utf-8")
    return out


def suggest(ui_map: dict[str, Any] | None = None, roles: list[str] | None = None, banlist: list[str] | None = None,
            allow_motion_library: bool = False, existing_dependencies: list[str] | None = None,
            include_code: bool = False, limit: int = 2, root: Path | None = None) -> dict[str, Any]:
    root = root or get_package_root()
    index = load_index(root)
    recipes = index["recipes"]
    existing = set(existing_dependencies or [])
    if ui_map and ui_map.get("motion_library"):
        existing.add(str(ui_map["motion_library"]).lower())
    installed = next((lib for lib, pkgs in _LIBRARY_PACKAGES.items() if any(p in existing for p in pkgs)), None)
    sanctioned = installed or ("motion" if allow_motion_library else None)

    sections: list[dict[str, Any]] = []
    if ui_map:
        for route in ui_map.get("routes", []):
            page_ids = {h["id"] for h in route.get("page_banlist", [])}
            for s in route.get("sections", []):
                sections.append({"route": route["path"], "section_id": s["id"], "role": s["role"],
                                 "component": s.get("component"), "file": s.get("file"),
                                 "banlist": sorted({h["id"] for h in s.get("banlist", [])}), "page_banlist": page_ids})
    else:
        for role in roles or []:
            sections.append({"route": None, "section_id": role, "role": role, "component": None, "file": None,
                             "banlist": sorted(set(banlist or [])), "page_banlist": set()})

    out_sections, unmatched = [], []
    for sec in sections:
        if sec["role"] in ("navigation", "footer", "sidebar"):
            continue  # app shell: protected under Elevate
        ranked = []
        for recipe in recipes:
            if recipe["kind"] != "section" or sec["role"] not in recipe["roles"]:
                continue
            fixes = [b for b in sec["banlist"] if b in recipe["replaces"]]
            page_fixes = [b for b in sorted(sec["page_banlist"]) if b in recipe["replaces"]]
            score = 3 + 2 * len(fixes) + len(page_fixes) - 0.25 * recipe["roles"].index(sec["role"])
            why = [f"fits role '{sec['role']}'"]
            if fixes:
                why.append("replaces " + ", ".join(fixes))
            if page_fixes:
                why.append("reduces page signals " + ", ".join(page_fixes))
            ranked.append(_entry(recipe, root, include_code, score, why))
        ranked.sort(key=lambda r: (-r["score"], r["id"]))
        entry = {k: v for k, v in sec.items() if k != "page_banlist"}
        entry["candidates"] = ranked[:max(1, limit)]
        (out_sections if ranked else unmatched).append(entry)

    all_ids = {b for sec in sections for b in sec["banlist"]} | {b for sec in sections for b in sec["page_banlist"]}
    roles_present = {sec["role"] for sec in sections}
    motion = []
    for recipe in recipes:
        if recipe["kind"] not in ("motion", "surface"):
            continue
        fits = sorted(roles_present & set(recipe["roles"]))
        fixes = sorted(all_ids & set(recipe["replaces"]))
        if not fits:
            continue
        status, install = _library_status(recipe["dependencies"], existing, allow_motion_library, sanctioned)
        why = [f"fits {', '.join(fits)}"] + (["replaces " + ", ".join(fixes)] if fixes else [])
        motion.append(_entry(recipe, root, include_code, len(fits) + 2 * len(fixes), why, status, install))
    motion.sort(key=lambda r: (-r["score"], r["id"]))

    tokens = [_entry(r, root, include_code, 10, ["apply first: derived brand scale, radii, elevation and motion tokens"])
              for r in recipes if r["kind"] == "tokens"]
    framework = (ui_map or {}).get("framework")
    notes = []
    if framework not in _REACT_FRAMEWORKS:
        notes.append(f"Recipes are React + Tailwind; for '{framework}' port the composition and utility classes.")
    if sanctioned and not installed and any(m["status"] == "needs_install" for m in motion):
        notes.append(f"One motion library is sanctioned: propose `npm install {sanctioned}` to the user; do not install it.")
    if not allow_motion_library and not installed:
        notes.append("No motion library allowed or installed: motion recipes fall back to their CSS variants.")
    return {"stacks": index["stacks"], "tokens": tokens, "sections": out_sections, "motion": motion,
            "unmatched_sections": [{"route": u["route"], "section_id": u["section_id"], "role": u["role"]}
                                   for u in unmatched],
            "motion_library": sanctioned, "notes": notes}
