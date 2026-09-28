"""Static evaluation of JS/TS literals for the UI map.

Content often reaches markup through props (``<Hero title="…" />``), module constants (``const plans = [...]``) and
``.map`` over arrays. This module parses literal values (strings, numbers, booleans, arrays, objects) and resolves
dotted paths against a scope, so the map can report real headings and action labels instead of ``{plan.name}``.
Anything that is not a literal (calls, JSX, template substitutions, identifiers it cannot resolve) becomes UNKNOWN.
"""
from __future__ import annotations

import re
from typing import Any


class _Unknown:
    def __repr__(self) -> str:
        return "UNKNOWN"


UNKNOWN = _Unknown()
_IDENT = re.compile(r"[A-Za-z_$][\w$]*")
_NUMBER = re.compile(r"-?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?")
_MAX_DEPTH = 12


def parse_literal(text: str, pos: int = 0, scope: dict[str, Any] | None = None) -> tuple[Any, int]:
    """Parse one JS value starting at ``pos``; returns (value | UNKNOWN, end index)."""
    return _Parser(text, scope or {}).value(pos, 0)


def literal_of(text: str, scope: dict[str, Any] | None = None) -> Any:
    """Evaluate a whole expression (attribute value or ``{...}`` body); UNKNOWN unless it is fully literal."""
    text = text.strip()
    if not text:
        return UNKNOWN
    value, end = parse_literal(text, 0, scope)
    return value if text[end:].strip().rstrip(";") == "" else UNKNOWN


def module_constants(source: str, limit: int = 40) -> dict[str, Any]:
    """Top-level ``const NAME = <literal>`` values (arrays, objects, strings) of a module."""
    consts: dict[str, Any] = {}
    for m in re.finditer(r"^(?:export\s+)?const\s+([A-Za-z_$][\w$]*)\s*(?::[^=\n]+)?=\s*", source, re.M):
        value, _ = parse_literal(source, m.end(), consts)
        if value is not UNKNOWN and isinstance(value, (list, dict, str, int, float)):
            consts[m.group(1)] = value
            if len(consts) >= limit:
                break
    return consts


def resolve_path(expr: str, scope: dict[str, Any]) -> Any:
    """Resolve ``a``, ``a.b.c``, ``a?.b`` or ``a["b"]`` / ``a[0]`` against ``scope``."""
    expr = expr.strip()
    if not expr or not scope:
        return UNKNOWN
    m = _IDENT.match(expr)
    if not m or m.group(0) not in scope:
        return UNKNOWN
    value = scope[m.group(0)]
    rest = expr[m.end():]
    while rest:
        step = re.match(r"\s*\??\.\s*([A-Za-z_$][\w$]*)|\s*\[\s*(?:\"([^\"]*)\"|'([^']*)'|(\d+))\s*\]", rest)
        if not step:
            return UNKNOWN
        key = step.group(1) or step.group(2) or step.group(3)
        index = step.group(4)
        if isinstance(value, dict) and key is not None and key in value:
            value = value[key]
        elif isinstance(value, list) and index is not None and int(index) < len(value):
            value = value[int(index)]
        else:
            return UNKNOWN
        rest = rest[step.end():]
    return value


def as_text(value: Any) -> str | None:
    if isinstance(value, bool) or value is None or value is UNKNOWN:
        return None
    if isinstance(value, (str, int, float)):
        return str(value)
    return None


class _Parser:
    def __init__(self, s: str, scope: dict[str, Any]) -> None:
        self.s = s
        self.n = len(s)
        self.scope = scope

    def ws(self, i: int) -> int:
        while i < self.n:
            if self.s[i] in " \t\r\n":
                i += 1
            elif self.s.startswith("//", i):
                nl = self.s.find("\n", i)
                i = self.n if nl < 0 else nl + 1
            elif self.s.startswith("/*", i):
                end = self.s.find("*/", i + 2)
                i = self.n if end < 0 else end + 2
            else:
                break
        return i

    def value(self, i: int, depth: int) -> tuple[Any, int]:
        i = self.ws(i)
        if i >= self.n or depth > _MAX_DEPTH:
            return UNKNOWN, i
        c = self.s[i]
        if c in "'\"`":
            return self.string(i)
        if c == "[":
            return self.array(i, depth)
        if c == "{":
            return self.obj(i, depth)
        m = _NUMBER.match(self.s, i)
        if m and (c.isdigit() or c in "-."):
            text = m.group(0)
            return (float(text) if any(ch in text for ch in ".eE") else int(text)), self.tail(m.end())
        m = _IDENT.match(self.s, i)
        if m:
            word = m.group(0)
            if word in ("true", "false"):
                return word == "true", self.tail(m.end())
            if word in ("null", "undefined"):
                return None, self.tail(m.end())
            path = re.compile(r"[A-Za-z_$][\w$]*(?:\s*\??\.\s*[A-Za-z_$][\w$]*)*").match(self.s, i)
            end = path.end()
            j = self.ws(end)
            if j < self.n and self.s[j] in "(<":  # call or generic -> not a literal
                return UNKNOWN, self.skip_expression(i)
            resolved = resolve_path(self.s[i:end], self.scope)
            return resolved, self.tail(end)
        return UNKNOWN, self.skip_expression(i)

    def tail(self, i: int) -> int:
        """Skip TypeScript suffixes (``as const``, ``satisfies X``, ``!``) after a value."""
        j = self.ws(i)
        m = re.compile(r"(?:as\s+const|as\s+[\w.<>\[\]|& ]+|satisfies\s+[\w.<>\[\]|& ]+|!)").match(self.s, j)
        return m.end() if m else i

    def string(self, i: int) -> tuple[Any, int]:
        quote = self.s[i]
        out: list[str] = []
        j = i + 1
        dynamic = False
        while j < self.n:
            c = self.s[j]
            if c == "\\" and j + 1 < self.n:
                out.append({"n": "\n", "t": "\t"}.get(self.s[j + 1], self.s[j + 1]))
                j += 2
                continue
            if c == quote:
                return (UNKNOWN if dynamic else "".join(out)), self.tail(j + 1)
            if quote == "`" and self.s.startswith("${", j):
                dynamic = True
                depth, j = 1, j + 2
                while j < self.n and depth:
                    depth += {"{": 1, "}": -1}.get(self.s[j], 0)
                    j += 1
                continue
            out.append(c)
            j += 1
        return UNKNOWN, self.n

    def array(self, i: int, depth: int) -> tuple[Any, int]:
        items: list[Any] = []
        i += 1
        while True:
            i = self.ws(i)
            if i >= self.n:
                return UNKNOWN, i
            if self.s[i] == "]":
                return items, self.tail(i + 1)
            if self.s.startswith("...", i):
                _, i = self.value(i + 3, depth + 1)
                items.append(UNKNOWN)
            else:
                value, i = self.value(i, depth + 1)
                items.append(value)
            i = self.ws(i)
            if i < self.n and self.s[i] == ",":
                i += 1
            elif i < self.n and self.s[i] != "]":
                i = self.skip_expression(i)
                if i < self.n and self.s[i] == ",":
                    i += 1

    def obj(self, i: int, depth: int) -> tuple[Any, int]:
        out: dict[str, Any] = {}
        i += 1
        while True:
            i = self.ws(i)
            if i >= self.n:
                return UNKNOWN, i
            c = self.s[i]
            if c == "}":
                return out, self.tail(i + 1)
            if self.s.startswith("...", i):
                _, i = self.value(i + 3, depth + 1)
            else:
                if c in "'\"":
                    key, i = self.string(i)
                    key = key if isinstance(key, str) else None
                else:
                    m = re.compile(r"[\w$]+").match(self.s, i)
                    if not m:
                        return UNKNOWN, self.skip_expression(i)
                    key, i = m.group(0), m.end()
                i = self.ws(i)
                if i < self.n and self.s[i] == ":":
                    value, i = self.value(i + 1, depth + 1)
                elif i < self.n and self.s[i] == "(":  # method shorthand
                    value, i = UNKNOWN, self.skip_expression(i)
                else:  # shorthand property `{ title }`
                    value = self.scope.get(key, UNKNOWN) if key else UNKNOWN
                if key is not None:
                    out[key] = value
            i = self.ws(i)
            if i < self.n and self.s[i] == ",":
                i += 1
            elif i < self.n and self.s[i] != "}":
                i = self.skip_expression(i)
                if i < self.n and self.s[i] == ",":
                    i += 1

    def skip_expression(self, i: int) -> int:
        """Skip to the next top-level ``,`` ``]`` ``}`` ``)`` (or ``;``) respecting nesting, strings and JSX."""
        depth = 0
        while i < self.n:
            c = self.s[i]
            if c in "'\"`":
                _, i = self.string(i)
                continue
            if c in "([{":
                depth += 1
            elif c in ")]}":
                if depth == 0:
                    return i
                depth -= 1
            elif c in ",;" and depth == 0:
                return i
            elif c == "<" and i + 1 < self.n and (self.s[i + 1].isalpha() or self.s[i + 1] == ">"):
                # JSX value: skip to the matching close by tag depth
                i = _skip_jsx(self.s, i)
                continue
            i += 1
        return i


def _skip_jsx(s: str, i: int) -> int:
    depth = 0
    n = len(s)
    while i < n:
        if s.startswith("</", i):
            depth -= 1
            end = s.find(">", i)
            i = n if end < 0 else end + 1
            if depth <= 0:
                return i
            continue
        if s[i] == "<" and i + 1 < n and (s[i + 1].isalpha() or s[i + 1] == ">"):
            end = s.find(">", i)
            if end < 0:
                return n
            if s[end - 1] == "/":
                i = end + 1
                if depth == 0:
                    return i
                continue
            depth += 1
            i = end + 1
            continue
        if s[i] in "'\"" and depth == 0:
            return i
        i += 1
    return i
