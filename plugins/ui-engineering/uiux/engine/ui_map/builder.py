"""UI map builder: route -> layout shell -> page -> ordered sections -> components, with roles, content inventory,
layout pattern, motion, banlist signals and used tokens. Also diffs two maps (before/after a visual change).

Static, read-only and dependency-free. Focus: React/Next.js (JSX/TSX) with Tailwind; Vue, Svelte, Astro and plain HTML
templates get the same treatment with less precision. Rules: workflows/ambition-levels.md (Elevate procedure step 1).
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any

from uiux.engine.repo_intelligence.profile import build_repo_profile
from uiux.engine.repo_intelligence.scanner import RepositorySnapshot
from uiux.engine.ui_map import literals, markup, signals
from uiux.engine.ui_map.markup import class_string

SCHEMA_VERSION = 1
SOURCE_SUFFIXES = (".tsx", ".jsx", ".ts", ".js", ".mjs", ".vue", ".svelte", ".astro", ".html", ".htm")
RESOLVE_SUFFIXES = (".tsx", ".jsx", ".ts", ".js", ".vue", ".svelte", ".astro", ".mjs")
SLOT_TAGS = {"Outlet", "RouterView", "router-view", "NuxtPage", "slot", "Routes", "Switch", "Component"}
SLOT_EXPRS = {"children", "props.children", "this.props.children", "@render children()", "render children()"}
WRAPPER_TAGS = {"", "Fragment", "React.Fragment", "main", "html", "body", "template", "Suspense", "ErrorBoundary",
                "StrictMode", "React.StrictMode", "Layout", "div", "Container"}
INLINE_TAGS = {"h1", "h2", "h3", "h4", "h5", "h6", "p", "a", "button", "img", "span", "ul", "ol", "Image", "Link",
               "Button", "small", "strong", "em", "br", "hr", "label", "input"}
ICON_PACKAGES = re.compile(r"lucide|heroicons|react-icons|@tabler/icons|phosphor|radix-ui/react-icons|iconify|"
                           r"@mui/icons|fontawesome|feather|remixicon")
_IMPORT = re.compile(
    r"import\s+(?:type\s+)?(?:(?P<default>[\w$]+)\s*,?\s*)?(?:\*\s+as\s+(?P<ns>[\w$]+)\s*)?"
    r"(?:\{(?P<named>[^}]*)\})?\s*from\s*['\"](?P<spec>[^'\"]+)['\"]")
_DYNAMIC = re.compile(r"(?:const|let)\s+([\w$]+)\s*=\s*(?:dynamic|lazy|React\.lazy|defineAsyncComponent)\s*\(\s*"
                      r"(?:\(\s*\)\s*=>\s*)?import\(\s*['\"]([^'\"]+)['\"]")


# ---------------------------------------------------------------------------------------------- source index
class SourceIndex:
    def __init__(self, snapshot: RepositorySnapshot) -> None:
        self.snapshot = snapshot
        self.files = set(snapshot.files)
        self.cache: dict[str, dict[str, Any]] = {}
        self.aliases = self._aliases()
        self.unparsed: list[str] = []

    def _aliases(self) -> list[tuple[str, list[str]]]:
        aliases: list[tuple[str, list[str]]] = []
        for name in ("tsconfig.json", "jsconfig.json"):
            text = self.snapshot.read_text(name)
            if not text:
                continue
            text = re.sub(r"//[^\n]*|/\*.*?\*/", "", text, flags=re.S)
            text = re.sub(r",\s*([}\]])", r"\1", text)
            try:
                opts = json.loads(text).get("compilerOptions", {}) or {}
            except ValueError:
                continue
            base = str(opts.get("baseUrl", ".")).strip("./") if opts.get("baseUrl") not in (None, ".", "./") else ""
            for key, targets in (opts.get("paths") or {}).items():
                prefix = key.rstrip("*")
                aliases.append((prefix, [str(PurePosixPath(base) / t.rstrip("*").lstrip("./")) if base else
                                         t.rstrip("*").lstrip("./") for t in targets]))
        aliases += [("@/", ["src/", ""]), ("~/", ["src/", ""]), ("@components/", ["src/components/", "components/"]),
                    ("$lib/", ["src/lib/"])]
        return aliases

    def resolve(self, spec: str, from_file: str) -> str | None:
        candidates: list[str] = []
        if spec.startswith("."):
            candidates.append(str(PurePosixPath(from_file).parent / spec))
        else:
            for prefix, targets in self.aliases:
                if spec.startswith(prefix):
                    candidates += [t + spec[len(prefix):] for t in targets]
        for cand in candidates:
            norm = _normpath(cand)
            if norm in self.files and norm.endswith(SOURCE_SUFFIXES):
                return norm
            for suffix in RESOLVE_SUFFIXES:
                if norm + suffix in self.files:
                    return norm + suffix
            for suffix in RESOLVE_SUFFIXES:
                if f"{norm}/index{suffix}" in self.files:
                    return f"{norm}/index{suffix}"
        return None

    def parsed(self, path: str) -> dict[str, Any]:
        if path in self.cache:
            return self.cache[path]
        text = self.snapshot.read_text(path)
        suffix = PurePosixPath(path).suffix.lstrip(".")
        result = markup.parse_source(text, suffix)
        if result["errors"]:
            self.unparsed.append(path)
        imports: dict[str, dict[str, str]] = {}
        for m in _IMPORT.finditer(text):
            spec = m.group("spec")
            if m.group("default"):
                imports[m.group("default")] = {"spec": spec, "name": "default"}
            if m.group("ns"):
                imports[m.group("ns")] = {"spec": spec, "name": "*"}
            for part in (m.group("named") or "").split(","):
                part = part.strip().replace("type ", "")
                if not part:
                    continue
                original, _, alias = part.partition(" as ")
                imports[(alias or original).strip()] = {"spec": spec, "name": original.strip()}
        for m in _DYNAMIC.finditer(text):
            imports[m.group(1)] = {"spec": m.group(2), "name": "default"}
        result["imports"] = imports
        result["text"] = text
        result["consts"] = literals.module_constants(text) if suffix in ("tsx", "jsx", "ts", "js", "mjs") else {}
        self.cache[path] = result
        return result

    def component_defaults(self, path: str, name: str | None) -> dict[str, Any]:
        """Literal defaults from a component's destructured props: ``function X({ id = "faq", n = 3 })``."""
        text = self.parsed(path)["text"]
        names = [name] if name and name not in ("default", "*") else []
        names += [c["name"] for c in self.parsed(path)["components"] if c["default"]]
        for comp in names:
            m = re.search(rf"(?:function\s+{re.escape(comp)}\s*(?:<[^>]*>)?\s*\(|const\s+{re.escape(comp)}\s*=\s*(?:\w+\()?\s*\()"
                          r"\s*\{", text)
            if not m:
                continue
            depth, i = 1, m.end()
            while i < len(text) and depth:
                depth += {"{": 1, "}": -1}.get(text[i], 0)
                i += 1
            body = text[m.end():i - 1]
            defaults: dict[str, Any] = {}
            for dm in re.finditer(r"([A-Za-z_$][\w$]*)\s*=\s*", body):
                value, _ = literals.parse_literal(body, dm.end())
                if isinstance(value, (str, int, float, list)) and not isinstance(value, bool):
                    defaults[dm.group(1)] = value
            return defaults
        return {}

    def component_roots(self, path: str, name: str | None) -> list[dict]:
        parsed = self.parsed(path)
        comps = parsed["components"]
        if not comps:
            return parsed["roots"]
        chosen = None
        if name and name not in ("default", "*"):
            chosen = next((c for c in comps if c["name"] == name), None)
        if chosen is None:
            chosen = next((c for c in comps if c["default"]), None) or comps[-1]
        return chosen["roots"]


def _normpath(path: str) -> str:
    parts: list[str] = []
    for part in path.replace("\\", "/").split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if parts:
                parts.pop()
            continue
        parts.append(part)
    return "/".join(parts)


def _pascal(tag: str) -> str:
    return "".join(p.capitalize() for p in tag.split("-")) if "-" in tag else tag


# ---------------------------------------------------------------------------------------------- expansion
_MAP_EXPR = re.compile(
    r"^\s*([A-Za-z_$][\w$]*(?:\s*\??\.\s*[A-Za-z_$][\w$]*)*)\s*\??\.\s*map\s*\(\s*(?:async\s*)?"
    r"(?:\(\s*(?:([A-Za-z_$][\w$]*)|\{([^}]*)\})\s*(?:,\s*([A-Za-z_$][\w$]*))?\s*(?::[^)]*)?\)|([A-Za-z_$][\w$]*))\s*=>")
_MAX_LIST_COPIES = 12


def _scope_for_item(scope: dict[str, Any], m: re.Match, item: Any, index: int) -> dict[str, Any]:
    inner = dict(scope)
    name = m.group(2) or m.group(5)
    if name:
        inner[name] = item
    elif m.group(3) and isinstance(item, dict):
        for part in m.group(3).split(","):
            key, _, alias = part.strip().partition(":")
            key = key.split("=")[0].strip()
            if key:
                inner[(alias or key).split("=")[0].strip()] = item.get(key, literals.UNKNOWN)
    if m.group(4):
        inner[m.group(4)] = index
    return inner


def _eval_attr(value: Any, scope: dict[str, Any]) -> Any:
    """Literal value of an attribute for prop passing (strings stay strings; ``{expr}`` is evaluated)."""
    if isinstance(value, str):
        return value
    if value is True:
        return True
    if isinstance(value, dict) and "expr" in value:
        return literals.literal_of(value["expr"], scope)
    return literals.UNKNOWN


def expand(index: SourceIndex, nodes: list[dict], file: str, depth: int, max_depth: int, stack: tuple[str, ...],
           usage: Counter, scope: dict[str, Any] | None = None) -> list[dict]:
    """Copy ``nodes`` and inline the rendered roots of locally resolvable custom components.

    ``scope`` carries literal values (module constants, props, ``.map`` items) so text and attributes that come from
    data are materialized: ``{plan.name}`` becomes the plan's name, one copy per literal list item.
    """
    parsed = index.parsed(file)
    local = {c["name"] for c in parsed["components"]}
    if scope is None:
        scope = dict(parsed.get("consts", {}))
    out: list[dict] = []
    for node in nodes:
        if node.get("type") == "expr":
            text = literals.as_text(literals.literal_of(node["expr"], scope))
            out.append({"type": "text", "text": text} if text is not None else dict(node))
            continue
        if node.get("type") != "element":
            out.append(dict(node))
            continue
        m = _MAP_EXPR.match(node.get("source_expr", "")) if node.get("repeated") else None
        items = literals.resolve_path(re.sub(r"\s+", "", m.group(1)), scope) if m else literals.UNKNOWN
        if m and isinstance(items, list) and items:
            for i, item in enumerate(items[:_MAX_LIST_COPIES]):
                copy = _expand_element(index, node, file, depth, max_depth, stack, usage,
                                       _scope_for_item(scope, m, item, i), parsed, local)
                copy["list_item"] = i
                out.append(copy)
            continue
        out.append(_expand_element(index, node, file, depth, max_depth, stack, usage, scope, parsed, local))
    return out


def _expand_element(index: SourceIndex, node: dict, file: str, depth: int, max_depth: int, stack: tuple[str, ...],
                    usage: Counter, scope: dict[str, Any], parsed: dict[str, Any], local: set[str]) -> dict:
    new = {k: v for k, v in node.items() if k not in ("children", "attrs")}
    new["attrs"] = {}
    for key, value in node["attrs"].items():
        if isinstance(value, dict) and value.get("elements"):
            value = dict(value, elements=expand(index, value["elements"], file, depth, max_depth, stack, usage, scope))
        elif isinstance(value, dict) and "expr" in value:
            text = literals.as_text(literals.literal_of(value["expr"], scope))
            if text is not None:
                value = text
        new["attrs"][key] = value
    new["children"] = expand(index, node["children"], file, depth, max_depth, stack, usage, scope)
    tag = node["tag"]
    head = _pascal(tag.split(".")[0])
    if head[:1].isupper():
        imp = parsed["imports"].get(head)
        target, name = None, None
        if imp:
            target = index.resolve(imp["spec"], file)
            name = imp["name"] if "." not in tag else tag.split(".", 1)[1]
            if target is None:
                new["library"] = imp["spec"]
                if ICON_PACKAGES.search(imp["spec"]):
                    new["icon"] = True
        elif head in local:
            target, name = file, head
        if target:
            new["component"] = tag
            new["file"] = target
            usage[(tag, target)] += 1
            key = f"{target}#{name}"
            if depth < max_depth and key not in stack:
                roots = index.component_roots(target, name)
                props = {k: _eval_attr(v, scope) for k, v in node["attrs"].items() if k != "..."}
                child_scope = dict(index.parsed(target).get("consts", {}))
                child_scope.update(index.component_defaults(target, name))
                child_scope.update({k: v for k, v in props.items() if v is not literals.UNKNOWN})
                child_scope["props"] = props
                new["expanded"] = expand(index, roots, target, depth + 1, max_depth, stack + (key,), usage,
                                         child_scope)
    return new


# ---------------------------------------------------------------------------------------------- sections
def _is_slot(node: dict) -> bool:
    if node.get("type") == "expr":
        return node["expr"].strip() in SLOT_EXPRS
    return node.get("type") == "element" and node["tag"] in SLOT_TAGS and not node.get("component")


def _has_heading(node: dict) -> bool:
    return any(n.get("type") == "element" and n["tag"] in signals.HEADING_TAGS
               for n in signals.expanded_children(node))


def _is_wrapper(node: dict, depth: int) -> bool:
    if depth > 6 or node.get("type") != "element":
        return False
    tag = node["tag"]
    comp = node.get("component") or ""
    kids = [k for k in signals.expanded_children(node) if k.get("type") == "element" or _is_slot(k)]
    if not kids:
        return False
    if any(_is_slot(k) for k in kids):
        return True
    if tag in ("", "Fragment", "React.Fragment", "main", "html", "body", "template", "Suspense", "ErrorBoundary",
               "StrictMode", "React.StrictMode") or tag.endswith("Provider") or tag.endswith("Providers"):
        return True
    if comp:
        if re.search(r"(?:Layout|Shell|Wrapper|Providers?|Page|View|Screen|Template)$", comp) and len(kids) >= 2:
            return True
        return len(kids) == 1 and node.get("expanded") and _is_wrapper(kids[0], depth + 1)
    if tag in signals.LANDMARK_TAGS or _has_heading(node):
        return False
    if tag in ("div", "Container", "Box", "Stack", "Flex") or tag.endswith("Container"):
        blockish = [k for k in kids if k.get("type") == "element" and (k["tag"] in signals.LANDMARK_TAGS
                    or k.get("component") or k["tag"] in ("div", "Container"))]
        return len(kids) == 1 or len(blockish) >= 2
    return False


def section_candidates(nodes: list[dict], depth: int = 0) -> list[dict]:
    out: list[dict] = []
    group: list[dict] = []

    def flush() -> None:
        if group:
            out.append({"type": "element", "tag": "(group)", "attrs": {}, "children": list(group),
                        "line": group[0].get("line", 0), "repeated": False, "conditional": False})
            group.clear()

    for node in nodes:
        if _is_slot(node):
            flush()
            out.append({"type": "slot"})
            continue
        if node.get("type") != "element":
            continue
        if _is_wrapper(node, depth):
            flush()
            out.extend(section_candidates(signals.expanded_children(node), depth + 1))
        elif node["tag"] in INLINE_TAGS and not node.get("component"):
            group.append(node)
        else:
            flush()
            out.append(node)
    flush()
    return out


def _slug(path: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", path.lower()).strip("-") or "root"


def _is_decorative(node: dict) -> bool:
    """aria-hidden layers and elements without any content (textures, dividers, spacers) are not sections."""
    root = signals.effective_root(node)
    if root.get("attrs", {}).get("aria-hidden") in ("true", True):
        return True
    inv = signals.inventory(node)
    return not any(inv[k] for k in ("headings", "text_blocks", "actions", "media", "fields", "forms", "tables",
                                    "charts", "data_bindings")) and not signals.label_of(node)


def describe_sections(candidates: list[dict], prefix: str) -> list[dict[str, Any]]:
    sections = [c for c in candidates if c.get("type") == "element" and not _is_decorative(c)]
    described = []
    for i, node in enumerate(sections):
        inv = signals.inventory(node)
        role = signals.classify_role(node, inv, i, len(sections))
        sig = signals.layout_signature(node)
        pattern = signals.describe_pattern(node, inv, sig)
        described.append({
            "id": f"{prefix}-s{i + 1}",
            "order": i + 1,
            "role": role["role"],
            "role_confidence": role["confidence"],
            "role_evidence": role["evidence"],
            "component": node.get("component"),
            "file": node.get("file"),
            "tag": node["tag"],
            "line": node.get("line"),
            "conditional": bool(node.get("conditional")),
            "pattern": pattern,
            "layout_signature": sig,
            "classes": class_string(signals.effective_root(node))[:200],
            "content": inv,
            "fingerprint": signals.fingerprint(inv),
            "motion": signals.motion_signals(node),
            "banlist": [],
            "_node": node,
        })
    for entry in described:
        entry["banlist"] = signals.banlist_hits(entry["_node"], entry["content"], entry["role"], entry["pattern"])
    return described


# ---------------------------------------------------------------------------------------------- routes
def _next_layouts(page_file: str, files: set[str]) -> list[str]:
    m = re.search(r"^(.*?(?:^|/)app)/(.*)$", page_file)
    if not m:
        return []
    root, rest = m.group(1), m.group(2)
    parts = rest.split("/")[:-1]
    chain = []
    for i in range(len(parts) + 1):
        base = "/".join([root] + parts[:i])
        for ext in (".tsx", ".jsx", ".js"):
            if f"{base}/layout{ext}" in files:
                chain.append(f"{base}/layout{ext}")
                break
    return chain


def _spa_routes(index: SourceIndex) -> list[dict[str, Any]]:
    """React Router / Vue Router routes: <Route path element={<Page/>}> and {path, element|component} objects."""
    routes: list[dict[str, Any]] = []
    candidates = [f for f in index.snapshot.files if f.endswith((".tsx", ".jsx", ".ts", ".js"))
                  and re.search(r"(?:^|/)(?:src/)?(?:App|main|router|routes?)(?:/index)?\.[jt]sx?$", f, re.I)]
    for file in candidates[:8]:
        parsed = index.parsed(file)
        for node, _ in markup.walk(parsed["roots"]):
            if node.get("type") == "element" and node["tag"] == "Route" and isinstance(node["attrs"].get("path"), str):
                element = node["attrs"].get("element") or node["attrs"].get("component") or node["attrs"].get("Component")
                comp = None
                if isinstance(element, dict):
                    comp = (element.get("elements") or [{}])[0].get("tag") or element.get("expr")
                routes.append({"path": node["attrs"]["path"], "router_file": file, "component": comp})
        for m in re.finditer(r"path:\s*['\"]([^'\"]*)['\"][^{}]*?(?:element:\s*<\s*([\w.]+)|component:\s*([\w.]+)|"
                             r"Component:\s*([\w.]+))", parsed["text"]):
            routes.append({"path": m.group(1) or "/", "router_file": file,
                           "component": m.group(2) or m.group(3) or m.group(4)})
    seen, unique = set(), []
    for r in routes:
        if r["path"] not in seen and r["path"] != "*":
            seen.add(r["path"])
            unique.append(r)
    return unique


def _page_targets(index: SourceIndex, profile: dict[str, Any]) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    files = index.files
    framework = str((profile.get("framework") or {}).get("name") or "")
    spa = [] if framework in ("nextjs", "nuxt", "sveltekit", "astro", "remix") else _spa_routes(index)
    for route in ([] if spa else profile.get("routes", [])):
        src = route.get("source_file") or ""
        if not src.endswith(SOURCE_SUFFIXES) or route.get("page_component") is None:
            continue
        layouts = _next_layouts(src, files)
        if re.search(r"(?:^|/)pages/", src):
            layouts = [f for f in (f"{src.split('pages/')[0]}pages/_app{e}" for e in (".tsx", ".jsx", ".js")) if f in files][:1]
        if route.get("layout") and route["layout"] not in layouts:
            layouts.append(route["layout"])
        targets.append({"path": route["path"], "file": src, "component": None, "layouts": layouts})
    if not targets:
        for r in spa or _spa_routes(index):
            router = index.parsed(r["router_file"])
            comp = (r["component"] or "").split(".")[0]
            imp = router["imports"].get(comp)
            file = index.resolve(imp["spec"], r["router_file"]) if imp else None
            if file is None and comp in {c["name"] for c in router["components"]}:
                file = r["router_file"]
            if file:
                targets.append({"path": r["path"], "file": file, "component": imp["name"] if imp else comp,
                                "layouts": [r["router_file"]]})
    if not targets:
        for cand in ("src/App.tsx", "src/App.jsx", "src/App.vue", "App.tsx", "App.jsx", "src/routes/+page.svelte",
                     "index.html", "src/index.html", "public/index.html"):
            if cand in files:
                targets.append({"path": "/", "file": cand, "component": None, "layouts": []})
                break
    return targets


# ---------------------------------------------------------------------------------------------- tokens
_COLOR_UTIL = re.compile(r"^(?:[a-z0-9-]+:)*(?:bg|text|border|from|via|to|ring|fill|stroke|outline|divide|shadow)-"
                         r"([a-z]+(?:-[a-z]+)?)(?:-(\d{2,3}))?(?:/\d+)?$")
_NEUTRALS = {"gray", "slate", "zinc", "neutral", "stone", "white", "black", "transparent", "current", "inherit"}
_NON_COLORS = {"left", "right", "center", "top", "bottom", "xs", "sm", "md", "lg", "xl", "base", "none", "clip",
               "opacity", "gradient", "cover", "contain", "fixed", "no", "repeat", "x", "y", "t", "b", "l", "r",
               "inner", "solid", "dashed", "dotted", "double", "collapse", "separate", "wrap", "nowrap",
               "balance", "pretty", "ellipsis", "start", "end", "justify", "auto", "full", "screen", "2xl",
               "3xl", "4xl", "5xl", "6xl", "7xl", "8xl", "9xl", "muted", "foreground-muted"}


def used_tokens(all_class_lists: list[list[str]], index: SourceIndex, layout_files: list[str]) -> dict[str, Any]:
    families: Counter = Counter()
    radii: Counter = Counter()
    shadows: Counter = Counter()
    sizes: Counter = Counter()
    fonts: Counter = Counter()
    for classes in all_class_lists:
        for c in classes:
            base = c.split(":")[-1]
            m = _COLOR_UTIL.match(c)
            if m and m.group(1) not in _NON_COLORS and not m.group(1).startswith(("opacity", "[", "clip")):
                families[m.group(1)] += 1
            if base.startswith("rounded"):
                radii[base] += 1
            if re.match(r"shadow(?:-(?:sm|md|lg|xl|2xl|inner|none|\[.+\]))?$", base):
                shadows[base] += 1
            if re.match(r"text-(?:xs|sm|base|lg|[2-9]?xl|\[)", base):
                sizes[base] += 1
            if re.match(r"font-(?:sans|serif|mono|display|heading|body|[a-z]+-sans)$", base):
                fonts[base] += 1
    declared_fonts: list[str] = []
    for file in layout_files + [f for f in index.files if re.search(r"(?:globals|global|index|app|main)\.css$", f)][:4]:
        text = index.snapshot.read_text(file, max_chars=60_000)
        declared_fonts += re.findall(r"import\s*\{([^}]+)\}\s*from\s*['\"]next/font/google['\"]", text)
        declared_fonts += re.findall(r"font-family\s*:\s*([^;]+);", text)[:4]
        declared_fonts += re.findall(r"--font-[\w-]+\s*:\s*([^;]+);", text)[:4]
    hues = [(f, n) for f, n in families.most_common() if f not in _NEUTRALS]
    return {
        "color_families": dict(families.most_common(16)),
        "dominant_hues": [f for f, _ in hues[:4]],
        "radii": dict(radii.most_common(6)),
        "shadows": dict(shadows.most_common(6)),
        "type_sizes": dict(sizes.most_common(10)),
        "font_utilities": dict(fonts.most_common(6)),
        "declared_fonts": sorted({" ".join(f.split())[:80] for f in declared_fonts})[:8],
    }


# ---------------------------------------------------------------------------------------------- public API
def build_ui_map(project: str | Path = ".", options: dict[str, Any] | None = None) -> dict[str, Any]:
    opts = options or {}
    snapshot = RepositorySnapshot(
        workspace_root=project if "files" not in opts else None,
        file_list=opts.get("files"),
        package_json_data=opts.get("package_json"),
        file_contents=opts.get("file_contents"),
    )
    profile = build_repo_profile(snapshot)
    index = SourceIndex(snapshot)
    max_depth = int(opts.get("max_depth", 4))
    wanted = set(opts.get("routes") or [])
    targets = [t for t in _page_targets(index, profile) if not wanted or t["path"] in wanted]
    targets.sort(key=lambda t: (t["path"].count("/"), t["path"]))
    truncated = len(targets) > int(opts.get("max_routes", 30))
    targets = targets[:int(opts.get("max_routes", 30))]

    usage: Counter = Counter()
    shell: dict[str, dict[str, Any]] = {}
    class_lists: list[list[str]] = []
    routes_out: list[dict[str, Any]] = []
    for target in targets:
        for layout in target["layouts"]:
            if layout in shell:
                continue
            roots = expand(index, index.component_roots(layout, None), layout, 0, 2, (), usage)
            cands = section_candidates(roots)
            slot_at = next((i for i, c in enumerate(cands) if c.get("type") == "slot"), len(cands))
            described = describe_sections([c for c in cands if c.get("type") == "element"], _slug(layout))
            before = [d for d, c in zip(described, [c for c in cands if c.get("type") == "element"])
                      if cands.index(c) < slot_at]
            shell[layout] = {
                "file": layout,
                "before_slot": [_shell_entry(d) for d in before],
                "after_slot": [_shell_entry(d) for d in described if d not in before],
                "has_slot": slot_at < len(cands),
            }
            class_lists.append(signals.all_classes(roots))
        roots = expand(index, index.component_roots(target["file"], target["component"]), target["file"], 0,
                       max_depth, (), usage)
        cands = [c for c in section_candidates(roots) if c.get("type") == "element"]
        sections = describe_sections(cands, _slug(target["path"]))
        class_lists.append(signals.all_classes(roots))
        page_hits = signals.page_banlist_hits(sections)
        signal_ids = {h["id"] for s in sections for h in s["banlist"]} | {h["id"] for h in page_hits}
        count = sum(len(s["banlist"]) for s in sections) + len(page_hits)
        for s in sections:
            s.pop("_node", None)
            if opts.get("detail") == "summary":
                s["content"] = {k: s["content"][k] for k in ("headings", "text_blocks", "actions", "media", "fields")}
        routes_out.append({
            "path": target["path"],
            "file": target["file"],
            "layouts": target["layouts"],
            "sections": sections,
            "page_banlist": page_hits,
            "generic_density": {"signals": count, "distinct": sorted(signal_ids),
                                "level": "high" if count >= 4 else "medium" if count >= 2 else "low"},
            "fingerprint": sorted({item for s in sections for item in s["fingerprint"]}),
        })

    components = [{"name": name, "file": file, "uses": n} for (name, file), n in usage.most_common()]
    roles = Counter(s["role"] for r in routes_out for s in r["sections"])
    all_layouts = sorted({l for t in targets for l in t["layouts"]})
    return {
        "schema_version": SCHEMA_VERSION,
        "project": str(project),
        "framework": (profile.get("framework") or {}).get("name"),
        "styling": [s.get("name") for s in (profile.get("styling_system") or {}).get("systems", [])
                    if isinstance(s, dict)] or (profile.get("styling_system") or {}).get("primary"),
        "motion_library": (profile.get("motion_library") or {}).get("name"),
        "ui_library": (profile.get("ui_library") or {}).get("name"),
        "shell": list(shell.values()),
        "routes": routes_out,
        "components": components[:80],
        "tokens": {"declared": profile.get("design_tokens", {}),
                   "used": used_tokens(class_lists, index, all_layouts)},
        "summary": {
            "routes_mapped": len(routes_out),
            "sections": sum(len(r["sections"]) for r in routes_out),
            "roles": dict(roles.most_common()),
            "banlist_signals": sum(r["generic_density"]["signals"] for r in routes_out),
            "high_density_routes": [r["path"] for r in routes_out if r["generic_density"]["level"] == "high"],
        },
        "limits": {"truncated_routes": truncated, "max_depth": max_depth, "unparsed_files": sorted(set(index.unparsed))},
    }


def _shell_entry(section: dict[str, Any]) -> dict[str, Any]:
    return {"role": section["role"], "component": section["component"], "tag": section["tag"],
            "file": section["file"], "actions": [a["label"] for a in section["content"]["actions"]][:12]}


def diff_ui_maps(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    """Compare two UI maps: content preservation (hard) and composition change (the Elevate bar)."""
    b_routes = {r["path"]: r for r in before.get("routes", [])}
    a_routes = {r["path"]: r for r in after.get("routes", [])}
    per_route = []
    content_removed_total = 0
    for path, br in b_routes.items():
        ar = a_routes.get(path)
        if ar is None:
            continue
        removed = sorted(set(br.get("fingerprint", [])) - set(ar.get("fingerprint", [])))
        added = sorted(set(ar.get("fingerprint", [])) - set(br.get("fingerprint", [])))
        content_removed_total += len(removed)
        b_secs, a_secs = br.get("sections", []), ar.get("sections", [])
        matched, changed = 0, 0
        pattern_changes = []
        used: set[int] = set()
        for bs in b_secs:
            best, best_score = None, 0.0
            for j, s in enumerate(a_secs):
                if j in used:
                    continue
                score = _overlap(bs.get("fingerprint", []), s.get("fingerprint", []))
                if bs.get("component") and bs.get("component") == s.get("component"):
                    score += 0.5
                if score > best_score:
                    best, best_score = j, score
            if best is None:
                continue
            used.add(best)
            matched += 1
            s = a_secs[best]
            layout_delta = 1 - _overlap(bs.get("layout_signature", []), s.get("layout_signature", []))
            if layout_delta >= 0.34 or bs.get("pattern", {}).get("summary") != s.get("pattern", {}).get("summary"):
                changed += 1
                pattern_changes.append({"before": bs["id"], "after": s["id"], "role": s.get("role"),
                                        "pattern": [bs.get("pattern", {}).get("summary"), s.get("pattern", {}).get("summary")],
                                        "layout_delta": round(layout_delta, 2)})
        b_ban = sorted({h["id"] for s in b_secs for h in s.get("banlist", [])} | {h["id"] for h in br.get("page_banlist", [])})
        a_ban = sorted({h["id"] for s in a_secs for h in s.get("banlist", [])} | {h["id"] for h in ar.get("page_banlist", [])})
        per_route.append({
            "path": path,
            "content_removed": removed,
            "content_added": added,
            "sections_before": len(b_secs),
            "sections_after": len(a_secs),
            "order_before": [s.get("role") for s in b_secs],
            "order_after": [s.get("role") for s in a_secs],
            "sections_recomposed": changed,
            "recomposition_ratio": round(changed / matched, 2) if matched else 0.0,
            "pattern_changes": pattern_changes,
            "banlist_resolved": sorted(set(b_ban) - set(a_ban)),
            "banlist_introduced": sorted(set(a_ban) - set(b_ban)),
            "banlist_remaining": sorted(set(a_ban) & set(b_ban)),
        })
    routes_removed = sorted(set(b_routes) - set(a_routes))
    ratios = [r["recomposition_ratio"] for r in per_route if r["sections_before"]]
    avg = round(sum(ratios) / len(ratios), 2) if ratios else 0.0
    return {
        "routes_removed": routes_removed,
        "routes_added": sorted(set(a_routes) - set(b_routes)),
        "routes": per_route,
        "content_preserved": not routes_removed and content_removed_total == 0,
        "recomposition_ratio": avg,
        "elevate_bar": {
            "met": avg >= 0.5 and not routes_removed and content_removed_total == 0,
            "rule": "Elevate needs content preserved and at least half of the matched sections re-composed "
                    "(layout signature or pattern changed).",
        },
    }


def _overlap(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def render_markdown(ui_map: dict[str, Any]) -> str:
    """Section inventory tables for CURRENT-UX-MAP.md."""
    lines = ["## Section inventory", ""]
    for shell in ui_map.get("shell", []):
        parts = [f"{e['role']}:{e['component'] or e['tag']}" for e in shell["before_slot"]] + ["{page}"] + \
                [f"{e['role']}:{e['component'] or e['tag']}" for e in shell["after_slot"]]
        lines.append(f"- Shell `{shell['file']}`: " + " → ".join(parts))
    lines.append("")
    for route in ui_map.get("routes", []):
        density = route["generic_density"]
        lines += [f"### `{route['path']}` — `{route['file']}`",
                  f"Generic density: **{density['level']}** ({density['signals']} signals: "
                  f"{', '.join(density['distinct']) or 'none'})", "",
                  "| # | Role | Current pattern | Content inventory | Component/file | Banlist |",
                  "|---|---|---|---|---|---|"]
        for s in route["sections"]:
            c = s["content"]
            inv = "; ".join(filter(None, [
                ", ".join(f"h{h['level']} \"{h['text'][:40]}\"" for h in c["headings"][:3]),
                f"{c['text_blocks']} text" if c.get("text_blocks") else "",
                f"{len(c['actions'])} actions" if c["actions"] else "",
                f"{len(c['media'])} media" if c["media"] else "",
                f"{len(c['fields'])} fields" if c["fields"] else "",
            ]))
            where = f"{s['component'] or s['tag']}" + (f" (`{s['file']}`)" if s.get("file") else "")
            ban = ", ".join(h["id"] for h in s["banlist"]) or "—"
            lines.append(f"| {s['order']} | {s['role']} | {s['pattern']['summary']} | {inv or '—'} | {where} | {ban} |")
        if route["page_banlist"]:
            lines.append("")
            lines.append("Page signals: " + ", ".join(f"{h['id']} ({h['evidence']})" for h in route["page_banlist"]))
        lines.append("")
    used = ui_map.get("tokens", {}).get("used", {})
    if used:
        lines += ["## Tokens in use", "",
                  f"- Dominant hues: {', '.join(used.get('dominant_hues', [])) or 'none detected'}",
                  f"- Fonts: {', '.join(used.get('declared_fonts', [])) or 'default'}",
                  f"- Radii: {', '.join(used.get('radii', {}))}; shadows: {', '.join(used.get('shadows', {}))}"]
    return "\n".join(lines) + "\n"
