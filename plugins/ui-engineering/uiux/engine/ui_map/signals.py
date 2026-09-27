"""Section signals for the UI map: content inventory, role classification, layout pattern, banlist hits.

Banlist ids mirror knowledge/visual-language/anti-slop/default-banlist.md; they are review signals (a recorded
reason may keep an item), not violations.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any

from uiux.engine.ui_map.markup import class_string, text_of, walk

HEADING_TAGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}
LINK_TAGS = {"a", "Link", "NavLink", "RouterLink", "router-link", "nuxt-link", "NuxtLink"}
FIELD_TAGS = {"input", "select", "textarea", "Input", "Select", "Textarea", "Checkbox", "Switch", "RadioGroup",
              "Combobox", "DatePicker"}
MEDIA_TAGS = {"img", "Image", "picture", "video", "iframe", "NuxtImg", "enhanced:img"}
LANDMARK_TAGS = {"header", "nav", "main", "footer", "aside", "section", "article", "form"}
LAYOUT_CLASS = re.compile(
    r"^(?:[a-z0-9]+:)*(?:grid|flex|inline-flex|grid-cols-\S+|col-span-\S+|row-span-\S+|flex-(?:row|col)\S*|order-\S+|"
    r"text-(?:center|left|right)|max-w-\S+|mx-auto|items-\S+|justify-\S+|self-\S+|place-\S+|absolute|relative|"
    r"sticky|fixed|basis-\S+|w-(?:full|screen|1/2|1/3|2/3)|aspect-\S+|columns-\S+|overflow-\S+|-?m[tblrxy]?-\S+)$")
_EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿✨⭐]")
_PRICE = re.compile(r"(?:[$€£¥₫]\s?\d|\d\s?(?:[$€£₫]|usd|vnd|đ)\b|/\s?(?:mo|month|year|yr|tháng|năm)\b)", re.I)
_ROUND_STAT = re.compile(r"\b\d+(?:[.,]\d+)?\s?(?:[kKmMbB]\+?|\+|%)(?=\s|$)|\b24/7\b|99\.9+%")
_HYPE = re.compile(r"\b(?:unlock the power|supercharge|seamless(?:ly)?|revolutioni[sz]e|next[- ]gen(?:eration)?|"
                   r"effortless(?:ly)?|game[- ]chang|cutting[- ]edge|elevate your|take .{0,20} to the next level)\b",
                   re.I)


# ---------------------------------------------------------------------------------------------- helpers
def elements(nodes: list[dict]) -> list[dict]:
    return [n for n in nodes if n.get("type") == "element"]


def expanded_children(node: dict) -> list[dict]:
    """Children of an element, or the rendered roots of an expanded custom component."""
    if node.get("expanded") is not None:
        return node["expanded"] + node.get("children", [])
    return node.get("children", [])


def walk_expanded(nodes: list[dict], depth: int = 0):
    for node in nodes:
        yield node, depth
        if node.get("type") == "element":
            yield from walk_expanded(expanded_children(node), depth + 1)
            for value in node.get("attrs", {}).values():
                if isinstance(value, dict) and value.get("elements"):
                    yield from walk_expanded(value["elements"], depth + 1)


def label_of(node: dict) -> str:
    attrs = node.get("attrs", {})
    for key in ("aria-label", "title", "alt", "label", "placeholder"):
        if isinstance(attrs.get(key), str) and attrs[key].strip():
            return attrs[key].strip()[:80]
    text = " ".join(t["text"] for t, _ in walk_expanded(expanded_children(node)) if t.get("type") == "text")
    if text:
        return text[:80]
    exprs = [t["expr"] for t, _ in walk_expanded(expanded_children(node)) if t.get("type") == "expr"]
    return ("{" + exprs[0] + "}")[:80] if exprs else ""


def _is_button(tag: str) -> bool:
    return tag == "button" or tag.endswith("Button") or tag in ("Button", "IconButton", "v-btn")


def effective_root(node: dict) -> dict:
    """The element a custom component actually renders when it has a single root (``<Hero/>`` -> its <section>)."""
    seen = 0
    while node.get("expanded") is not None and seen < 6:
        roots = elements(node["expanded"])
        if len(roots) != 1:
            break
        node = roots[0]
        seen += 1
    return node


def all_classes(nodes: list[dict], limit: int = 4000, weight_repeated: int = 1) -> list[str]:
    """Class names in the subtree; elements rendered from a list count ``weight_repeated`` times."""
    out: list[str] = []
    stack = [(n, False) for n in nodes]
    while stack:
        node, in_list = stack.pop()
        if node.get("type") != "element":
            continue
        in_list = in_list or bool(node.get("repeated"))
        out.extend(class_string(node).split() * (weight_repeated if in_list else 1))
        if len(out) > limit:
            break
        stack.extend((k, in_list) for k in expanded_children(node))
        for value in node.get("attrs", {}).values():
            if isinstance(value, dict) and value.get("elements"):
                stack.extend((k, in_list) for k in value["elements"])
    return out


# ---------------------------------------------------------------------------------------------- inventory
def inventory(section: dict) -> dict[str, Any]:
    """Content inventory of a section: the preservation contract for Elevate."""
    headings, texts, actions, media, fields, exprs, repeated = [], [], [], [], [], [], []
    icons = 0
    tables = charts = forms = 0
    static_groups: Counter = Counter()
    for node, _ in walk_expanded([section]):
        kind = node.get("type")
        if kind == "expr":
            exprs.append(node["expr"])
            continue
        if kind != "element":
            continue
        tag = node["tag"]
        attrs = node.get("attrs", {})
        low = tag.lower()
        if tag in HEADING_TAGS or attrs.get("role") == "heading":
            headings.append({"level": HEADING_TAGS.get(tag, 2), "text": label_of(node)})
        elif low in ("p", "blockquote", "li", "dd", "figcaption") and label_of(node):
            texts.append(label_of(node))
        if low in {t.lower() for t in LINK_TAGS} or _is_button(tag):
            href = attrs.get("href") or attrs.get("to")
            actions.append({"kind": "button" if _is_button(tag) else "link", "label": label_of(node),
                            "href": href if isinstance(href, str) else (("{" + href["expr"] + "}") if isinstance(href, dict) else None)})
        if tag in MEDIA_TAGS:
            src = attrs.get("src")
            media.append({"tag": tag, "alt": attrs.get("alt") if isinstance(attrs.get("alt"), str) else None,
                          "src": src if isinstance(src, str) else None})
        if low == "svg" or node.get("icon") or tag.endswith("Icon") or tag.lower().endswith(".icon"):
            icons += 1
        if tag in FIELD_TAGS:
            name = attrs.get("name") or attrs.get("id") or attrs.get("placeholder") or attrs.get("type")
            fields.append({"tag": tag, "name": name if isinstance(name, str) else None,
                           "type": attrs.get("type") if isinstance(attrs.get("type"), str) else None})
        if low == "form":
            forms += 1
        if low == "table" or "Table" in tag or "DataGrid" in tag:
            tables += 1
        if "Chart" in tag or tag in ("LineChart", "BarChart", "AreaChart", "PieChart", "ResponsiveContainer"):
            charts += 1
        if node.get("repeated"):
            repeated.append({"tag": tag, "component": node.get("component")})
        kids = elements(expanded_children(node))
        if len(kids) >= 3:
            for key, count in Counter(k["tag"] for k in kids).items():
                if count >= 3 and key not in ("div", "span", "br"):
                    static_groups[key] = max(static_groups[key], count)
    return {
        "headings": headings[:20],
        "text_blocks": len(texts),
        "text_samples": texts[:3],
        "actions": actions[:20],
        "media": media[:12],
        "icons": icons,
        "fields": fields[:20],
        "forms": forms,
        "tables": tables,
        "charts": charts,
        "repeated": repeated[:10],
        "static_groups": dict(static_groups),
        "data_bindings": exprs[:8],
    }


def fingerprint(inv: dict[str, Any]) -> list[str]:
    """Normalized content items used to prove that a visual change kept the content."""
    items = [f"h{h['level']}:{_norm(h['text'])}" for h in inv["headings"] if h["text"]]
    items += [f"{a['kind']}:{_norm(a['label'])}" for a in inv["actions"] if a["label"]]
    items += [f"field:{_norm(str(f['name']))}" for f in inv["fields"] if f["name"]]
    items += [f"media:{_norm(m['alt'] or m['src'] or m['tag'])}" for m in inv["media"]]
    return sorted(set(items))


def _norm(text: str) -> str:
    return " ".join(str(text).lower().split())[:80]


# ---------------------------------------------------------------------------------------------- roles
_ROLE_KEYWORDS = [
    ("navigation", r"nav(?:bar|igation)?|menu|topbar|header"),
    ("hero", r"hero|banner|jumbotron|intro|masthead|splash"),
    ("social-proof", r"logo(?:s|cloud|wall)?|client|partner|trusted|brands|customers|sponsor"),
    ("stats", r"stat(?:s|istic)?|metric|number|kpi|counter"),
    ("features", r"feature|benefit|service|capabilit|why|advantage|bento"),
    ("steps", r"step|how-?it-?works|process|workflow|timeline|journey|onboard"),
    ("pricing", r"pricing|price|plan|tier|subscription"),
    ("testimonials", r"testimonial|review|quote|feedback|social"),
    ("faq", r"faq|question|accordion|help"),
    ("cta", r"cta|call-?to-?action|get-?started|signup|sign-?up|join|download|contact-?us"),
    ("newsletter", r"newsletter|subscribe"),
    ("team", r"team|member|people|founder|about"),
    ("gallery", r"gallery|showcase|portfolio|work|case-?stud|carousel|slider"),
    ("blog", r"blog|post|article|news|insight|changelog"),
    ("data-table", r"table|grid-?view|datagrid|list-?view|records"),
    ("dashboard-metrics", r"chart|graph|analytics|overview|summary|kpi"),
    ("form", r"form|contact|checkout|login|register|settings|profile"),
    ("sidebar", r"sidebar|drawer|aside"),
    ("footer", r"footer"),
]


def classify_role(section: dict, inv: dict[str, Any], position: int, total: int) -> dict[str, Any]:
    tag = section["tag"]
    attrs = section.get("attrs", {})
    names = " ".join(filter(None, [section.get("component") or "", tag,
                                   attrs.get("id") if isinstance(attrs.get("id"), str) else "",
                                   attrs.get("aria-label") if isinstance(attrs.get("aria-label"), str) else "",
                                   class_string(section)]))
    names = re.sub(r"(?<=[a-z])(?=[A-Z])", "-", names).lower()
    heading_text = " ".join(h["text"] for h in inv["headings"][:2]).lower()
    all_text = heading_text + " " + " ".join(inv["text_samples"]).lower()
    scores: Counter = Counter()
    evidence: dict[str, list[str]] = {}

    def add(role: str, points: float, why: str) -> None:
        scores[role] += points
        evidence.setdefault(role, []).append(why)

    for role, pattern in _ROLE_KEYWORDS:
        if re.search(rf"(?:^|[\s_/-])(?:{pattern})", names):
            add(role, 3, f"name/id/class mentions {role}")
        if re.search(rf"\b(?:{pattern})", heading_text):
            add(role, 1, "heading wording")
    low = tag.lower()
    if low == "nav":
        add("navigation", 4, "<nav>")
    if low == "header":
        add("navigation", 2 if inv["actions"] and len(inv["headings"]) <= 1 else 0, "<header> with links")
    if low == "footer":
        add("footer", 5, "<footer>")
    if low == "aside":
        add("sidebar", 3, "<aside>")
    if any(h["level"] == 1 for h in inv["headings"]):
        add("hero", 2.5 if position <= 1 else 1, "contains h1")
    if _PRICE.search(all_text) or sum(bool(_PRICE.search(t)) for t in inv["text_samples"]) >= 1:
        add("pricing", 2, "price-like text")
    if any(t.startswith("“") or t.startswith('"') for t in inv["text_samples"]):
        add("testimonials", 1, "quoted text")
    if inv["forms"] or len(inv["fields"]) >= 2:
        add("form", 2 + len(inv["fields"]) * 0.3, "form fields")
    if len(inv["fields"]) == 1 and inv["actions"]:
        add("newsletter", 1.5, "single field + action")
    if inv["tables"]:
        add("data-table", 3, "table")
    if inv["charts"]:
        add("dashboard-metrics", 3, "chart")
    if len(inv["media"]) >= 6:
        add("gallery", 2, f"{len(inv['media'])} images")
    if (inv["repeated"] or inv["static_groups"]) and len(inv["headings"]) >= 3:
        add("features", 1, "repeated items with headings")
    if position == total - 1 and inv["actions"] and len(inv["headings"]) <= 2 and inv["text_blocks"] <= 2 \
            and not scores.get("footer"):
        add("cta", 1.5, "closing section with actions")
    if 0 < len(inv["headings"]) <= 2 and 1 <= len(inv["actions"]) <= 3 and inv["text_blocks"] <= 2 and position > 0:
        add("cta", 0.5, "short heading + actions")
    if not scores:
        return {"role": "content", "confidence": 0.3, "evidence": ["no specific signal"]}
    role, score = scores.most_common(1)[0]
    confidence = round(min(0.95, 0.35 + score * 0.12), 2)
    return {"role": role, "confidence": confidence, "evidence": evidence[role][:4]}


# ---------------------------------------------------------------------------------------------- pattern
def layout_signature(section: dict, levels: int = 3) -> list[str]:
    """Layout-relevant classes of the section root and its first levels (composition fingerprint)."""
    sig: set[str] = set()
    for node, depth in walk_expanded([section]):
        if depth > levels or node.get("type") != "element":
            continue
        sig.update(c for c in class_string(node).split() if LAYOUT_CLASS.match(c))
        if node.get("repeated"):
            sig.add(f"repeat:{node.get('component') or node['tag']}")
    return sorted(sig)


def describe_pattern(section: dict, inv: dict[str, Any], sig: list[str]) -> dict[str, Any]:
    classes = set(sig)
    shallow = " ".join(class_string(n) for n, d in walk_expanded([section]) if d <= 2 and n.get("type") == "element")
    cols = [int(m) for m in re.findall(r"grid-cols-(\d+)", " ".join(classes))]
    two_up = any(re.search(r"(?:md|lg|xl):grid-cols-2$", c) for c in classes) or \
        any(re.search(r"(?:md|lg|xl):flex-row", c) for c in classes)
    repeated_count = 3 if inv["repeated"] else max(inv["static_groups"].values(), default=0)
    centered = bool(re.search(r"(?:^|\s)text-center(?:\s|$)", shallow))
    traits = []
    if centered:
        traits.append("centered")
    if cols:
        traits.append(f"{max(cols)}-column grid")
    if two_up and (inv["media"] or inv["fields"]):
        traits.append("split (text + media/form)")
    if repeated_count >= 3 and cols:
        traits.append("equal cards" if not any(c.startswith(("col-span", "lg:col-span", "md:col-span", "row-span"))
                                             for c in classes) else "varied spans")
    if any("sticky" in c for c in classes):
        traits.append("sticky element")
    if any(c.startswith(("absolute", "-mt", "-mb")) for c in classes):
        traits.append("layered/overlap")
    if not traits:
        traits.append("stacked")
    root_classes = class_string(effective_root(section)).split()
    padding = next((c for c in root_classes if re.match(r"(?:[a-z]+:)?py-\S+$", c)), None)
    return {"summary": ", ".join(traits), "centered": centered, "columns": max(cols) if cols else 1,
            "vertical_padding": padding, "full_bleed": any(c.startswith("bg-") for c in root_classes)
            and not any(c.startswith("max-w") for c in root_classes)}


# ---------------------------------------------------------------------------------------------- banlist
def banlist_hits(section: dict, inv: dict[str, Any], role: str, pattern: dict[str, Any]) -> list[dict[str, str]]:
    classes = all_classes([section], weight_repeated=3)
    joined = " ".join(classes)
    texts = " ".join([h["text"] for h in inv["headings"]] + inv["text_samples"] + [a["label"] for a in inv["actions"]])
    hits: list[dict[str, str]] = []

    def hit(item: str, evidence: str) -> None:
        hits.append({"id": item, "evidence": evidence[:120]})

    if re.search(r"\b(?:from|via)-(?:indigo|purple|violet|fuchsia)-\d+", joined) and \
            re.search(r"\b(?:to|via)-(?:pink|purple|fuchsia|blue|violet|rose)-\d+", joined):
        hit("purple-gradient", "from-indigo/purple … to-pink/blue gradient")
    if "bg-clip-text" in classes and "text-transparent" in classes:
        hit("gradient-text", "bg-clip-text text-transparent")
    if re.search(r"\bblur-(?:2xl|3xl|\[\d{2,}px\])", joined) and "rounded-full" in classes:
        hit("blur-blobs", "blurred rounded-full shapes")
    if sum(1 for c in classes if "backdrop-blur" in c) >= 2 and role not in ("navigation",):
        hit("glass-everywhere", "backdrop-blur on several elements")
    radius = [c for c in classes if re.match(r"(?:[a-z]+:)?rounded-(?:2xl|3xl)$", c)]
    shadow = [c for c in classes if re.match(r"(?:[a-z]+:)?shadow-(?:lg|xl|2xl)$", c)]
    if len(radius) >= 3 and len(shadow) >= 3:
        hit("uniform-radius-shadow", f"{len(radius)}× {radius[0]} with {shadow[0]}")
    if pattern["columns"] in (3, 4) and "equal cards" in pattern["summary"] and \
            (inv["icons"] >= 3 or re.search(r"rounded-(?:full|xl|lg)\s[^\"]*bg-\w+(?:-\d+)?/(?:10|20)", joined)):
        hit("equal-icon-cards", f"{pattern['columns']}-column equal cards with icons")
    if role == "hero" and pattern["centered"] and len(inv["actions"]) >= 2 and not inv["media"]:
        hit("centered-hero", "centered hero, twin actions, no product visual")
    if re.search(r"hover:scale-(?:10[5-9]|110)", joined):
        hit("hover-scale", "hover:scale-105+")
    if re.search(r"\banimate-(?:pulse|bounce|ping)\b", joined):
        hit("infinite-decor", "animate-pulse/bounce/ping")
    if _EMOJI.search(texts):
        hit("emoji-icons", _EMOJI.search(texts).group(0))
    if re.search(r"\btext-(?:gray|slate|zinc|neutral|stone)-(?:300|400)\b", joined) and inv["text_blocks"]:
        hit("low-contrast-body", "text-gray-300/400 body copy")
    if re.search(r"shadow-\[0_0_\d+px|shadow-(?:cyan|fuchsia|purple|pink|violet)-\d+", joined):
        hit("neon-glow", "glow shadow")
    if _HYPE.search(texts):
        hit("hype-copy", _HYPE.search(texts).group(0))
    if role in ("stats", "hero", "social-proof") and len(_ROUND_STAT.findall(texts)) >= 2:
        hit("round-number-stats", ", ".join(_ROUND_STAT.findall(texts)[:3]))
    return hits


def page_banlist_hits(sections: list[dict[str, Any]]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    content = [s for s in sections if s["role"] not in ("navigation", "footer", "sidebar")]
    if len(content) >= 4:
        centered = sum(1 for s in content if s["pattern"]["centered"])
        if centered / len(content) >= 0.75:
            hits.append({"id": "centered-everything", "evidence": f"{centered}/{len(content)} sections centered"})
        paddings = [s["pattern"]["vertical_padding"] for s in content if s["pattern"]["vertical_padding"]]
        if len(paddings) >= 4 and len(set(paddings)) == 1:
            hits.append({"id": "uniform-rhythm", "evidence": f"{paddings[0]} on {len(paddings)} sections"})
    reveal = sum(1 for s in content if s.get("motion", {}).get("reveal_on_scroll"))
    if len(content) >= 3 and reveal >= max(3, int(len(content) * 0.8)):
        hits.append({"id": "fade-up-everything", "evidence": f"scroll reveal on {reveal}/{len(content)} sections"})
    return hits


def motion_signals(section: dict) -> dict[str, Any]:
    tags = Counter()
    reveal = False
    classes = all_classes([section])
    for node, _ in walk_expanded([section]):
        if node.get("type") != "element":
            continue
        tag = node["tag"]
        attrs = node.get("attrs", {})
        if tag.startswith(("motion.", "m.", "Motion")) or "AnimatePresence" in tag:
            tags["motion"] += 1
        if "whileInView" in attrs or "data-aos" in attrs or "v-motion" in attrs or attrs.get("data-animate"):
            reveal = True
        if any(k in attrs for k in ("ref",)) and "gsap" in str(attrs):
            tags["gsap"] += 1
    return {
        "library_elements": dict(tags),
        "reveal_on_scroll": reveal,
        "css_animations": sorted({c for c in classes if c.startswith(("animate-", "transition", "duration-"))})[:8],
        "reduced_motion_classes": any(c.startswith("motion-reduce:") or c.startswith("motion-safe:") for c in classes),
    }
