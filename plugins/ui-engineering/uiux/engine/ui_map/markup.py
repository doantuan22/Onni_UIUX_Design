"""Tolerant, dependency-free parser for JSX/TSX and HTML-like templates (Vue, Svelte, Astro, HTML).

It recovers the element tree a component renders — tags, literal attributes, text, expression slots and whether
an element is rendered from a list (``.map``) or conditionally — which is what the UI map needs. It is not a
compiler: unsupported syntax degrades to fewer nodes, never to an exception.

Node shapes::

    {"type": "element", "tag": str, "attrs": {name: str | {"expr": str}}, "children": [...],
     "line": int, "repeated": bool, "conditional": bool}
    {"type": "text", "text": str}
    {"type": "expr", "expr": str}
"""
from __future__ import annotations

import re
from typing import Any

VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
_NAME = re.compile(r"[A-Za-z_$][\w.$:-]*")
_ATTR_NAME = re.compile(r"[^\s=/>{}\"']+")
_JSX_PREV = set("(,=:?[{};&|!>") | {""}
_KEYWORDS_BEFORE_JSX = ("return", "yield", "default", "case", "else", "await")
_MAX_NODES = 20_000
_ENTITIES = {"&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'", "&apos;": "'", "&nbsp;": " "}


class _Budget(Exception):
    pass


class MarkupParser:
    def __init__(self, text: str, markup: bool = False) -> None:
        self.s = text
        self.n = len(text)
        self.markup = markup
        self.nodes = 0
        self.errors: list[str] = []
        self._line_starts = [0] + [m.end() for m in re.finditer(r"\n", text)]

    # ------------------------------------------------------------------ helpers
    def line_of(self, pos: int) -> int:
        lo, hi = 0, len(self._line_starts) - 1
        while lo < hi:
            mid = (lo + hi + 1) // 2
            if self._line_starts[mid] <= pos:
                lo = mid
            else:
                hi = mid - 1
        return lo + 1

    def _count(self) -> None:
        self.nodes += 1
        if self.nodes > _MAX_NODES:
            raise _Budget()

    def _skip_string(self, i: int) -> int:
        quote = self.s[i]
        i += 1
        while i < self.n:
            c = self.s[i]
            if c == "\\":
                i += 2
                continue
            if c == quote:
                return i + 1
            if c == "\n" and quote != "`":
                return i + 1
            if quote == "`" and c == "$" and i + 1 < self.n and self.s[i + 1] == "{":
                _, i = self.scan_code(i + 2, stop_at_brace=True)
                continue
            i += 1
        return self.n

    def _prev_significant(self, i: int) -> str:
        j = i - 1
        while j >= 0 and self.s[j] in " \t\r\n":
            j -= 1
        if j < 0:
            return ""
        if self.s[j].isalpha():
            k = j
            while k >= 0 and (self.s[k].isalnum() or self.s[k] in "_$"):
                k -= 1
            word = self.s[k + 1:j + 1]
            return "kw" if word in _KEYWORDS_BEFORE_JSX else "ident"
        return self.s[j]

    def _looks_like_jsx(self, i: int) -> bool:
        nxt = self.s[i + 1] if i + 1 < self.n else ""
        if not (nxt.isalpha() or nxt == ">"):
            return False
        prev = self._prev_significant(i)
        return prev == "kw" or prev in _JSX_PREV

    # ------------------------------------------------------------------ code mode
    def scan_code(self, i: int, stop_at_brace: bool = False) -> tuple[list[dict], int]:
        """Scan JS/TS code, collecting JSX elements; with ``stop_at_brace`` stop after the matching ``}``."""
        found: list[dict] = []
        depth = 0
        while i < self.n:
            c = self.s[i]
            if c == "/" and i + 1 < self.n and self.s[i + 1] == "/":
                nl = self.s.find("\n", i)
                i = self.n if nl < 0 else nl + 1
            elif c == "/" and i + 1 < self.n and self.s[i + 1] == "*":
                end = self.s.find("*/", i + 2)
                i = self.n if end < 0 else end + 2
            elif c in "'\"`":
                i = self._skip_string(i)
            elif c == "{":
                depth += 1
                i += 1
            elif c == "}":
                if stop_at_brace and depth == 0:
                    return found, i + 1
                depth = max(0, depth - 1)
                i += 1
            elif c == "<" and self._looks_like_jsx(i):
                node, i = self.parse_element(i)
                if node is not None:
                    found.append(node)
            else:
                i += 1
        return found, i

    # ------------------------------------------------------------------ elements
    def _read_braced(self, i: int) -> tuple[str, list[dict], int]:
        """``i`` points at ``{``; return raw expression text, JSX found inside, index after ``}``."""
        start = i + 1
        if self.markup:
            depth, j = 1, start
            while j < self.n and depth:
                if self.s[j] == "{":
                    depth += 1
                elif self.s[j] == "}":
                    depth -= 1
                j += 1
            return self.s[start:j - 1], [], j
        found, j = self.scan_code(start, stop_at_brace=True)
        return self.s[start:max(start, j - 1)], found, j

    def _parse_attrs(self, i: int) -> tuple[dict[str, Any], int, bool]:
        attrs: dict[str, Any] = {}
        while i < self.n:
            while i < self.n and self.s[i] in " \t\r\n":
                i += 1
            if i >= self.n:
                break
            c = self.s[i]
            if c == ">":
                return attrs, i + 1, False
            if c == "/" and i + 1 < self.n and self.s[i + 1] == ">":
                return attrs, i + 2, True
            if c == "{":
                raw, _, i = self._read_braced(i)
                attrs.setdefault("...", []).append(raw.strip()[:120])
                continue
            m = _ATTR_NAME.match(self.s, i)
            if not m:
                i += 1
                continue
            name, i = m.group(0), m.end()
            while i < self.n and self.s[i] in " \t\r\n":
                i += 1
            if i < self.n and self.s[i] == "=":
                i += 1
                while i < self.n and self.s[i] in " \t\r\n":
                    i += 1
                if i < self.n and self.s[i] in "'\"":
                    end = self.s.find(self.s[i], i + 1)
                    end = self.n if end < 0 else end
                    attrs[name] = self.s[i + 1:end]
                    i = end + 1
                elif i < self.n and self.s[i] == "{":
                    raw, found, i = self._read_braced(i)
                    attrs[name] = {"expr": raw.strip()[:400]}
                    if found:
                        attrs[name]["elements"] = found
                else:
                    m2 = re.compile(r"[^\s>]+").match(self.s, i)
                    if m2:
                        attrs[name] = m2.group(0)
                        i = m2.end()
            else:
                attrs[name] = True
        return attrs, self.n, True

    def parse_element(self, i: int) -> tuple[dict | None, int]:
        self._count()
        start = i
        i += 1
        if i < self.n and self.s[i] == ">":
            tag, i = "", i + 1
            attrs, self_closing = {}, False
        else:
            m = _NAME.match(self.s, i)
            if not m:
                return None, i
            tag, i = m.group(0), m.end()
            # TypeScript generic arrow `<T,>(` is not JSX
            if i < self.n and self.s[i] == "," and not self.markup:
                return None, i
            attrs, i, self_closing = self._parse_attrs(i)
        node: dict[str, Any] = {"type": "element", "tag": tag, "attrs": attrs, "children": [],
                                "line": self.line_of(start), "repeated": False, "conditional": False}
        if self_closing or (self.markup and tag.lower() in VOID_TAGS):
            return node, i
        if self.markup and tag.lower() in ("script", "style"):
            end = self.s.lower().find(f"</{tag.lower()}", i)
            end = self.n if end < 0 else end
            close = self.s.find(">", end)
            return node, self.n if close < 0 else close + 1
        children, i = self._parse_children(i, tag)
        node["children"] = children
        return node, i

    def _parse_children(self, i: int, tag: str) -> tuple[list[dict], int]:
        children: list[dict] = []
        text_start = i
        while i < self.n:
            c = self.s[i]
            if c == "<":
                self._flush_text(children, text_start, i)
                if self.s.startswith("</", i):
                    m = _NAME.match(self.s, i + 2)
                    closing = m.group(0) if m else ""
                    close = self.s.find(">", i)
                    end = self.n if close < 0 else close + 1
                    if closing == tag or not self.markup or not closing:
                        return children, end
                    # HTML tolerance: an unexpected closing tag closes this element too
                    return children, i
                if self.s.startswith("<!--", i):
                    end = self.s.find("-->", i)
                    i = self.n if end < 0 else end + 3
                elif self.s.startswith("<!", i):
                    end = self.s.find(">", i)
                    i = self.n if end < 0 else end + 1
                else:
                    child, i = self.parse_element(i)
                    if child is not None:
                        children.append(child)
                    else:
                        i += 1
                text_start = i
            elif c == "{":
                self._flush_text(children, text_start, i)
                if self.markup and self.s.startswith("{{", i):
                    end = self.s.find("}}", i)
                    end = self.n if end < 0 else end + 2
                    children.append({"type": "expr", "expr": self.s[i + 2:end - 2].strip()[:120]})
                    i = end
                else:
                    raw, found, i = self._read_braced(i)
                    expr = raw.strip()
                    repeated = bool(re.search(r"\.(?:map|flatMap)\s*\(", expr)) or expr.startswith("#each")
                    conditional = bool(re.search(r"&&|\?|\bif\b|#if", expr))
                    if found:
                        for el in found:
                            el["repeated"] = el["repeated"] or repeated
                            el["conditional"] = el["conditional"] or (conditional and not repeated)
                        children.extend(found)
                    elif expr and not expr.startswith("/*"):
                        children.append({"type": "expr", "expr": expr[:120]})
                text_start = i
            else:
                i += 1
        self._flush_text(children, text_start, i)
        return children, i

    def _flush_text(self, children: list[dict], a: int, b: int) -> None:
        if b <= a:
            return
        text = " ".join(self.s[a:b].split())
        for k, v in _ENTITIES.items():
            text = text.replace(k, v)
        if text:
            children.append({"type": "text", "text": text})


# ---------------------------------------------------------------------- entry points
def _strip_blocks(text: str, tags: tuple[str, ...]) -> str:
    for tag in tags:
        text = re.sub(rf"<{tag}\b[^>]*>.*?</{tag}\s*>", lambda m: "\n" * m.group(0).count("\n"), text,
                      flags=re.S | re.I)
    return text


def parse_source(text: str, kind: str) -> dict[str, Any]:
    """Parse a source file. ``kind`` is the file suffix without dot (tsx, jsx, js, ts, vue, svelte, astro, html)."""
    kind = kind.lower()
    try:
        if kind in ("tsx", "jsx", "js", "ts", "mjs"):
            parser = MarkupParser(text)
            roots, _ = parser.scan_code(0)
            return {"roots": roots, "components": _component_spans(text, roots), "errors": parser.errors}
        if kind == "vue":
            m = re.search(r"<template[^>]*>(.*)</template\s*>", text, re.S | re.I)
            body = m.group(1) if m else ""
            offset = text[:m.start(1)].count("\n") if m else 0
            text = "\n" * offset + body
        elif kind == "svelte":
            text = _strip_blocks(text, ("script", "style"))
        elif kind == "astro":
            text = re.sub(r"^---.*?---", lambda m: "\n" * m.group(0).count("\n"), text, count=1, flags=re.S)
            text = _strip_blocks(text, ("script", "style"))
        else:
            text = _strip_blocks(text, ("script", "style"))
        parser = MarkupParser(text, markup=True)
        roots = parser._parse_children(0, "\0")[0]
        roots = [r for r in roots if r["type"] == "element"]
        return {"roots": roots, "components": [], "errors": parser.errors}
    except (_Budget, RecursionError) as exc:
        return {"roots": [], "components": [], "errors": [f"parse budget exceeded: {type(exc).__name__}"]}


_COMPONENT_DECL = re.compile(
    r"(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+([A-Z]\w*)\s*[<(]"
    r"|(?:export\s+)?(?:const|let)\s+([A-Z]\w*)\s*(?::[^=]+)?=\s*(?:React\.)?(?:memo\(|forwardRef\()?\s*(?:async\s*)?(?:\([^)]*\)|\w+)\s*(?::[^=]+)?=>"
    r"|(?:export\s+)?(?:const|let)\s+([A-Z]\w*)\s*=\s*(?:React\.)?(?:memo|forwardRef)\s*\("
)


def _component_spans(text: str, roots: list[dict]) -> list[dict[str, Any]]:
    """Assign top-level JSX roots to the nearest preceding capitalized component declaration."""
    decls = []
    line_starts = [0] + [m.end() for m in re.finditer(r"\n", text)]
    for m in _COMPONENT_DECL.finditer(text):
        name = m.group(1) or m.group(2) or m.group(3)
        line = 1 + sum(1 for s in line_starts[1:] if s <= m.start())
        decls.append((line, name, "export default" in text[max(0, m.start() - 1):m.start() + 40]
                      or bool(re.search(rf"export\s+default\s+{name}\b", text))))
    components: dict[str, dict[str, Any]] = {}
    for root in roots:
        owner = None
        for line, name, is_default in decls:
            if line <= root["line"]:
                owner = (name, is_default)
        if owner is None:
            continue
        entry = components.setdefault(owner[0], {"name": owner[0], "default": owner[1], "roots": []})
        entry["roots"].append(root)
    return list(components.values())


def walk(nodes: list[dict], depth: int = 0):
    """Yield (node, depth) for every node, depth-first, including elements nested in attribute expressions."""
    for node in nodes:
        yield node, depth
        if node.get("type") == "element":
            yield from walk(node["children"], depth + 1)
            for value in node["attrs"].values():
                if isinstance(value, dict) and value.get("elements"):
                    yield from walk(value["elements"], depth + 1)


def class_string(node: dict) -> str:
    """Literal class names of an element: ``className``/``class`` strings and string literals in cn()/clsx()."""
    parts: list[str] = []
    for key in ("className", "class", ":class", "tw"):
        value = node.get("attrs", {}).get(key)
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, dict):
            parts.extend(re.findall(r"[\"'`]([^\"'`$]*)[\"'`]", value.get("expr", "")))
    return " ".join(" ".join(parts).split())


def text_of(node: dict, limit: int = 400) -> str:
    """Visible literal text inside a node (text children only, depth-first)."""
    out: list[str] = []
    for child, _ in walk(node.get("children", [])):
        if child.get("type") == "text":
            out.append(child["text"])
            if sum(len(t) for t in out) > limit:
                break
    return " ".join(out)[:limit]
