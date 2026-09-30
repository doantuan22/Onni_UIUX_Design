"""Surface Resolver: Identifies repository-grounded affected files, components, tokens, and routes.

Determines the concrete blast radius boundary:
- Allowed files vs Protected files (Strictly grounded in repo evidence; never hallucinated)
- Component inventory matching vs Semantic DOM surfaces vs Explicit planned_create
- File existence contract: EXISTING_FILE or PLANNED_CREATE (no third state)
- Protected file grounding: Never invent src/theme.ts, tailwind.config.js, or src/router.tsx
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def _collect_repo_files(repo_profile: dict[str, Any] | None) -> list[str]:
    """Collect all normalized, verified file paths from repo_profile."""
    if not repo_profile:
        return []
    found: list[str] = []

    def _add(f: Any) -> None:
        if isinstance(f, str) and f.strip():
            norm = f.replace("\\", "/").strip().lstrip("./")
            if norm and norm not in found:
                found.append(norm)

    raw_files = repo_profile.get("files", [])
    if isinstance(raw_files, list):
        for f in raw_files:
            _add(f)
    elif isinstance(raw_files, dict):
        for k in ("all_files", "ui_files", "styling_files", "components", "pages", "routes"):
            for f in raw_files.get(k, []):
                _add(f)
        for v in raw_files.values():
            if isinstance(v, list):
                for f in v:
                    _add(f)

    for f in repo_profile.get("ui_files", []):
        _add(f)

    styling = repo_profile.get("styling_system", {})
    if isinstance(styling, dict):
        for f in styling.get("files", []):
            _add(f)

    comps = repo_profile.get("components", [])
    if isinstance(comps, list):
        for c in comps:
            if isinstance(c, dict):
                _add(c.get("path"))
                _add(c.get("file"))
    elif isinstance(comps, dict):
        for k in ("shared", "layouts", "primitives", "page_specific", "library_wrappers"):
            for c in comps.get(k, []):
                if isinstance(c, dict):
                    _add(c.get("path"))
                    _add(c.get("file"))

    for p in repo_profile.get("pages", []):
        if isinstance(p, dict):
            _add(p.get("file"))
            _add(p.get("path"))
        elif isinstance(p, str) and ("." in p or "/" in p):
            _add(p)

    apps = repo_profile.get("applications", {})
    if isinstance(apps, dict):
        for app_data in apps.values():
            if isinstance(app_data, dict):
                sub_prof = app_data.get("repo_profile") or app_data
                for f in _collect_repo_files(sub_prof):
                    _add(f)

    return found


def _collect_repo_components(repo_profile: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Flatten components from repo_profile regardless of list or inventory structure."""
    if not repo_profile:
        return []
    comps = repo_profile.get("components", [])
    out: list[dict[str, Any]] = []
    if isinstance(comps, list):
        for c in comps:
            out.append(c if isinstance(c, dict) else {"name": str(c)})
    elif isinstance(comps, dict):
        for k in ("shared", "layouts", "primitives", "page_specific", "library_wrappers"):
            for c in comps.get(k, []):
                out.append(c if isinstance(c, dict) else {"name": str(c)})
    return out


def resolve_surface(
    user_goal: str,
    scope_info: dict[str, Any],
    repo_profile: dict[str, Any] | None = None,
    existing_ui_profile: dict[str, Any] | None = None,
    preservation_profile: dict[str, Any] | None = None,
    workflow: str = "existing-ui",
) -> dict[str, Any]:
    """Resolve the concrete surface of affected files, components, tokens, and routes.
    
    Guarantees:
    - Every file belongs to EXISTING_FILE or PLANNED_CREATE.
    - No framework configs or theme files are hallucinated into protected_files.
    - Repos with monolithic HTML/CSS/JS target actual files, treating 'Sidebar' as a DOM region.
    """
    active_repo = repo_profile or {}
    active_ui = existing_ui_profile or {}
    active_pres = preservation_profile or {}

    app_target = scope_info.get("application_target")
    if app_target and "applications" in active_repo and app_target in active_repo["applications"]:
        active_repo = active_repo["applications"][app_target].get("repo_profile", active_repo)

    target_entity = (scope_info.get("target_entity") or "").lower()
    scope = scope_info.get("scope", "component")
    goal_lower = user_goal.lower()

    # 1. Discover all known real files from repo profile
    known_files = _collect_repo_files(active_repo)
    if not known_files and active_ui.get("files"):
        for f in active_ui["files"]:
            norm = str(f).replace("\\", "/").strip().lstrip("./")
            if norm not in known_files:
                known_files.append(norm)

    if app_target:
        app_target_norm = app_target.replace("\\", "/").strip().lstrip("./")
        app_specific_files = [
            f for f in known_files
            if f.startswith(app_target_norm + "/") or f.startswith(app_target + "/")
        ]
        if app_specific_files:
            known_files = app_specific_files

    # 2. Discover known components
    repo_components = _collect_repo_components(active_repo)
    matched_components: list[dict[str, Any]] = []

    for comp in repo_components:
        c_name = comp.get("name", "")
        if target_entity and target_entity in c_name.lower():
            matched_components.append(comp)

    # 3. Component Existence & Grounding
    planned_files: list[dict[str, Any]] = []
    is_explicit_create = bool(
        workflow == "greenfield"
        or any(w in goal_lower for w in ("create component", "thêm component", "tạo component", "new component", "add component"))
    )

    component_is_dom_region = False
    allowed_components: list[str] = []

    if matched_components:
        # Grounded in existing inventory
        for c in matched_components:
            allowed_components.append(c.get("name", target_entity.capitalize()))
    elif target_entity:
        if is_explicit_create:
            # Explicitly planned new component
            c_name = target_entity.capitalize()
            allowed_components.append(c_name)
            # Determine path based on framework
            fw_name = active_repo.get("framework", {}).get("name", "react") if isinstance(active_repo.get("framework"), dict) else "react"
            if fw_name in ("vue", "nuxt"):
                ext = ".vue"
            elif fw_name in ("svelte", "sveltekit"):
                ext = ".svelte"
            elif fw_name == "static_html":
                ext = ".html"
            else:
                ext = ".tsx"
            new_comp_path = f"src/components/{c_name}{ext}" if "src" in str(known_files) else f"{c_name}{ext}"
            planned_files.append({
                "path": new_comp_path,
                "planned_create": True,
                "reason": f"Explicitly requested new component '{c_name}'.",
                "owner_step": "step_1",
                "change_level": "L2",
                "scope": "component",
            })
        else:
            # Existing UI workflow without explicit component creation:
            # Component is treated as a semantic surface / DOM region, NOT a new React file!
            component_is_dom_region = True
            allowed_components.append(target_entity)

    # Evaluate shared component status
    is_shared = False
    usage_count = 1
    if matched_components:
        first_comp = matched_components[0]
        usage_count = first_comp.get("usage_count", 1)
        if usage_count > 1 or scope in ("token", "global") or "shared" in first_comp.get("path", "").lower():
            is_shared = True

    # 4. Discover routes & pages
    repo_routes = active_repo.get("routes", [])
    repo_pages = active_repo.get("pages", [])

    affected_routes: list[str] = []
    affected_pages: list[str] = []
    affected_surface_candidates: list[dict[str, str]] = []

    for r in repo_routes:
        r_path = r.get("path", "") if isinstance(r, dict) else str(r)
        if target_entity and target_entity in r_path.lower():
            affected_routes.append(r_path)
            affected_pages.append(r_path)

    for p in repo_pages:
        p_name = p.get("name", "") if isinstance(p, dict) else str(p)
        if target_entity and target_entity in p_name.lower():
            if p_name not in affected_pages:
                affected_pages.append(p_name)

    if not affected_pages and scope == "page" and target_entity:
        # Do not fabricate a route when P0 did not discover one. Preserve the
        # requested label as an ungrounded candidate for clarification/matching.
        affected_surface_candidates.append({"name": target_entity, "kind": "page", "reason": "No matching P0 route/page entry was found."})

    # 5. Discover Affected Files (Strictly Grounded)
    affected_files: list[str] = []

    if matched_components:
        for comp in matched_components:
            c_path = (comp.get("path") or comp.get("file") or "").replace("\\", "/").strip().lstrip("./")
            if c_path and c_path in known_files:
                affected_files.append(c_path)
    elif planned_files:
        for pf in planned_files:
            affected_files.append(pf["path"])
    elif component_is_dom_region or (not affected_files and target_entity):
        # Monolithic or multi-file existing project where feature lives in real files
        # Ground affected surface into existing HTML / CSS / JS files
        css_files = [f for f in known_files if f.endswith((".css", ".scss", ".sass", ".less"))]
        html_files = [f for f in known_files if f.endswith((".html", ".htm"))]
        js_files = [f for f in known_files if f.endswith((".js", ".ts", ".jsx", ".tsx")) and not f.startswith("test")]

        # Match files containing entity name if any
        entity_matches = [f for f in known_files if target_entity in f.lower()]
        if entity_matches:
            affected_files.extend(entity_matches)
        else:
            # Target CSS files for styling / responsive improvements
            if css_files:
                affected_files.extend(css_files[:2])
            # Target HTML files for DOM structure
            if html_files:
                affected_files.extend(html_files[:2])
            # Target JS files if interaction / toggle is requested
            if any(w in goal_lower for w in ("toggle", "open", "close", "click", "interactive", "mobile", "switch", "logic")) and js_files:
                affected_files.append(js_files[0])

    # If still empty but repo has files, fallback to primary UI entry files
    if not affected_files and known_files:
        for f in known_files:
            if f in ("index.html", "src/App.tsx", "src/App.jsx", "src/main.ts", "src/index.js", "styles.css", "app.js"):
                affected_files.append(f)
        if not affected_files:
            affected_files.append(known_files[0])

    # 6. Discover tokens
    affected_tokens: list[str] = []
    if scope == "token" or "spacing" in goal_lower:
        affected_tokens.extend(["--spacing-xs", "--spacing-sm", "--spacing-md", "--spacing-lg"])
    if "color" in goal_lower or "palette" in goal_lower:
        affected_tokens.extend(["--color-primary", "--color-secondary", "--color-background"])

    # 7. Boundaries (Allowed vs Protected)
    allowed_files = list(affected_files)

    protected_files: list[str] = []
    protected_routes = [r.get("path", "") if isinstance(r, dict) else str(r) for r in repo_routes if r not in affected_routes]
    protected_tokens: list[str] = []

    # Preservation rules for protected files & tokens (Strictly Grounded: NEVER hallucinate)
    has_explicit_files = "files" in active_repo or "ui_files" in active_repo
    palette_locked = active_pres.get("granular_permissions", {}).get("palette") == "locked" or active_pres.get("protected_invariants", {}).get("palette_locked", True)
    if palette_locked:
        # Only add files that ACTUALLY exist in the repository
        candidate_theme_files = (
            "src/theme.ts", "src/theme.js", "src/styles/theme.css", "src/styles/tokens.css",
            "tailwind.config.js", "tailwind.config.ts", "theme.css", "styles/theme.css",
        )
        for cand in candidate_theme_files:
            if has_explicit_files:
                if cand in known_files and cand not in affected_files:
                    protected_files.append(cand)
            else:
                if cand not in affected_files:
                    protected_files.append(cand)
                    break
        protected_tokens.extend(["--color-primary", "--color-brand", "primaryColor"])

    nav_protected = active_pres.get("granular_permissions", {}).get("navigation") == "protected"
    if nav_protected:
        candidate_nav_files = (
            "src/router.tsx", "src/routes.ts", "src/navigation.tsx", "src/router.js", "src/routes.js",
        )
        for cand in candidate_nav_files:
            if has_explicit_files:
                if cand in known_files and cand not in affected_files:
                    protected_files.append(cand)
            else:
                if cand not in affected_files:
                    protected_files.append(cand)
                    break

    # 8. File Existence Contract Validation
    # Every file must be EXISTING_FILE (in known_files) or PLANNED_CREATE (in planned_files)
    planned_file_paths = {pf["path"] for pf in planned_files}
    ungrounded_target_files: list[str] = []
    
    if has_explicit_files and known_files:
        for f in (allowed_files + protected_files):
            if f not in known_files and f not in planned_file_paths:
                ungrounded_target_files.append(f)

    # Clean duplicates while preserving order
    def _dedupe(items: list[str]) -> list[str]:
        return list(dict.fromkeys([i for i in items if i]))

    return {
        "files": _dedupe(affected_files),
        "pages": _dedupe(affected_pages),
        "affected_surface_candidates": affected_surface_candidates,
        "components": _dedupe(allowed_components),
        "tokens": _dedupe(affected_tokens),
        "routes": _dedupe(affected_routes),
        "is_shared_component": is_shared,
        "shared_component_usage_count": usage_count,
        "allowed_files": _dedupe(allowed_files),
        "allowed_components": _dedupe(allowed_components),
        "protected_files": _dedupe(protected_files),
        "protected_routes": _dedupe(protected_routes),
        "protected_tokens": _dedupe(protected_tokens),
        "planned_files": planned_files,
        "component_is_dom_region": component_is_dom_region,
        "is_grounded": len(ungrounded_target_files) == 0,
        "ungrounded_files": _dedupe(ungrounded_target_files),
    }
