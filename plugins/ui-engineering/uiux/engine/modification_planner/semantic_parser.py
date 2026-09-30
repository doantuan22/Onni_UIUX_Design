"""Semantic Negation & Action-Scoped Permission Parser.

Accurately distinguishes:
- mentioned: bool (action concept is present in user request)
- requested: bool (action is affirmatively desired)
- prohibited: bool (action is explicitly forbidden or negated)
- explicitly_allowed: bool (action has explicit authorized override)

Precedence Rule:
Explicit prohibition ALWAYS takes precedence over positive keywords.
"""
from __future__ import annotations

import re
from typing import Any

# Sensitive action categories
ACTION_REDESIGN = "redesign"
ACTION_PALETTE = "palette_change"
ACTION_NAVIGATION = "navigation_change"
ACTION_BRAND = "brand_change"
ACTION_STRUCTURE = "structure_change"
ACTION_FRAMEWORK = "framework_migration"
ACTION_LIBRARY = "library_replacement"
ACTION_DEPENDENCY = "dependency_addition"

SENSITIVE_ACTIONS = (
    ACTION_REDESIGN,
    ACTION_PALETTE,
    ACTION_NAVIGATION,
    ACTION_BRAND,
    ACTION_STRUCTURE,
    ACTION_FRAMEWORK,
    ACTION_LIBRARY,
    ACTION_DEPENDENCY,
)

# Negation terms in English and Vietnamese
# Vocabulary includes:
# Vietnamese: không, không được, tuyệt đối không, đừng, không muốn, không thay,
#             giữ nguyên, bảo toàn, không redesign, không đổi, giữ, cấm, chớ
# English: no, not, don't, do not, never, without changing, keep existing,
#          keep current, preserve, must not, keep, without replacing, prohibit
NEGATION_PREFIXES = (
    # Vietnamese (accented and unaccented)
    r"không\s+được",
    r"khong\s+duoc",
    r"tuyệt\s+đối\s+không",
    r"tuyet\s+doi\s+khong",
    r"không\s+muốn",
    r"khong\s+muon",
    r"không\s+thay\s+đổi",
    r"khong\s+thay\s+doi",
    r"không\s+thay",
    r"khong\s+thay",
    r"không\s+đổi",
    r"khong\s+doi",
    r"không\s+redesign",
    r"khong\s+redesign",
    r"không\s+xây\s+lại",
    r"khong\s+xay\s+lai",
    r"không\s+chuyển",
    r"khong\s+chuyen",
    r"không\s+thêm",
    r"khong\s+them",
    r"không\s+cần",
    r"khong\s+can",
    r"giữ\s+nguyên",
    r"giu\s+nguyen",
    r"giữ\s+lại",
    r"giu\s+lai",
    r"bảo\s+toàn",
    r"bao\s+toan",
    r"đừng",
    r"dung",
    r"cấm",
    r"cam",
    r"chớ",
    r"cho",
    r"không",
    r"khong",
    # English
    r"do\s+not",
    r"don't",
    r"does\s+not",
    r"doesn't",
    r"must\s+not",
    r"should\s+not",
    r"cannot",
    r"can't",
    r"never",
    r"without\s+changing",
    r"without\s+replacing",
    r"without\s+modifying",
    r"without\s+altering",
    r"keep\s+existing",
    r"keep\s+current",
    r"keep\s+the\s+current",
    r"keep\s+the\s+existing",
    r"keep",
    r"preserve",
    r"lock",
    r"no",
    r"not",
)

NEGATION_REGEX = re.compile(
    r"\b(?:" + "|".join(NEGATION_PREFIXES) + r")\b",
    re.IGNORECASE,
)

# Action keywords mapping
ACTION_KEYWORDS: dict[str, list[str]] = {
    ACTION_REDESIGN: [
        r"redesign\s+toàn\s+bộ",
        r"full\s+redesign",
        r"rebuild\s+entire",
        r"rebuild\s+all",
        r"rebuild\s+from\s+scratch",
        r"rebuild",
        r"overhaul\s+all",
        r"redesign\s+page",
        r"page\s+redesign",
        r"redesign\s+this\s+page",
        r"redesign\s+dashboard",
        r"redesign",
        r"xây\s+lại\s+từ\s+đầu",
        r"xây\s+lại\s+toàn\s+bộ",
        r"xây\s+lại",
        r"thiết\s+kế\s+lại\s+toàn\s+bộ",
        r"thiết\s+kế\s+lại",
    ],
    ACTION_PALETTE: [
        r"palette",
        r"color\s+palette",
        r"color\s+scheme",
        r"brand\s+colors?",
        r"primary\s+colors?",
        r"secondary\s+colors?",
        r"theme\s+colors?",
        r"recolor",
        r"change\s+(?:the\s+)?(?:theme\s+|global\s+)?colors?",
        r"change\s+palette",
        r"bảng\s+màu",
        r"hệ\s+màu",
        r"tông\s+màu",
        r"màu\s+thương\s+hiệu",
        r"thay\s+(?:đổi\s+)?(?:bảng\s+)?màu",
        r"đổi\s+(?:bảng\s+)?màu",
    ],
    ACTION_NAVIGATION: [
        r"navigation\s+model",
        r"navigation",
        r"nav\s+model",
        r"routes?",
        r"navbar",
        r"menu\s+structure",
        r"global\s+nav",
        r"điều\s+hướng",
    ],
    ACTION_BRAND: [
        r"brand\s+identity",
        r"brand",
        r"logo",
        r"thương\s+hiệu",
    ],
    ACTION_STRUCTURE: [
        r"ui\s+structure",
        r"page\s+structure",
        r"layout\s+structure",
        r"dom\s+structure",
        r"structure",
        r"kiến\s+trúc\s+giao\s+diện",
        r"cấu\s+trúc",
    ],
    ACTION_FRAMEWORK: [
        r"framework",
        r"migrate\s+framework",
        r"replace\s+framework",
        r"chuyển\s+framework",
    ],
    ACTION_LIBRARY: [
        r"ui\s+library",
        r"styling\s+library",
        r"thư\s+viện\s+ui",
    ],
    ACTION_DEPENDENCY: [
        r"new\s+dependencies",
        r"new\s+dependency",
        r"install\s+package",
        r"thêm\s+thư\s+viện",
    ],
}

# Prohibition keywords mapping (broader tokens for catching negative constraints)
ACTION_PROHIBITION_KEYWORDS: dict[str, list[str]] = {
    ACTION_PALETTE: [
        r"colors?",
        r"color\s+palette",
        r"palette",
        r"bảng\s+màu",
        r"tông\s+màu",
        r"màu\s+sắc",
        r"màu",
        r"brand\s+colors?",
    ],
    ACTION_REDESIGN: [
        r"redesign",
        r"rebuild",
        r"overhaul",
        r"thiết\s+kế\s+lại",
        r"xây\s+lại",
    ],
    ACTION_STRUCTURE: [
        r"structure",
        r"layout",
        r"cấu\s+trúc",
        r"bố\s+cục",
    ],
    ACTION_NAVIGATION: [
        r"navigation",
        r"nav",
        r"navbar",
        r"routes?",
        r"điều\s+hướng",
    ],
    ACTION_BRAND: [
        r"brand",
        r"thương\s+hiệu",
        r"logo",
    ],
    ACTION_FRAMEWORK: [
        r"framework",
        r"react",
        r"vue",
        r"svelte",
        r"angular",
    ],
}

# Clause splitters
CLAUSE_SPLITTERS = re.compile(
    r"[;,.\n]|\b(?:but\s+not|but|however|except|yet|although|nhưng|tuy\s+nhiên|ngoại\s+trừ|trừ\s+khi|song)\b",
    re.IGNORECASE,
)


def split_into_clauses(text: str) -> list[str]:
    """Split text into manageable semantic clauses."""
    raw_clauses = CLAUSE_SPLITTERS.split(text)
    return [c.strip() for c in raw_clauses if c.strip()]


def parse_action_negation(
    action: str,
    text: str,
    explicit_permissions: dict[str, Any] | None = None,
) -> dict[str, bool]:
    """Parse negation and permission state for a single sensitive action in text.
    
    Returns:
    {
        "mentioned": bool,
        "requested": bool,
        "prohibited": bool,
        "explicitly_allowed": bool,
    }
    """
    perms = explicit_permissions or {}
    patterns = ACTION_KEYWORDS.get(action, [])
    prohib_patterns = ACTION_PROHIBITION_KEYWORDS.get(action, patterns)
    
    mentioned = False
    prohibited = False
    requested = False
    
    clauses = split_into_clauses(text)
    if not clauses:
        clauses = [text]

    for clause in clauses:
        clause_lower = clause.lower()

        # Check for prohibitions in this clause
        for ppat in prohib_patterns:
            pmatch = re.search(r"\b" + ppat + r"\b", clause_lower)
            if pmatch:
                mentioned = True
                pre_text = clause_lower[:pmatch.start()].strip()
                is_negated = False
                for neg in NEGATION_PREFIXES:
                    if re.search(r"\b" + neg + r"(?:\s+\w+){0,4}\s*$", pre_text):
                        is_negated = True
                        break
                    if neg in ("không", "không được", "tuyệt đối không", "đừng", "never", "do not", "don't", "no", "without changing", "keep", "keep current", "keep existing", "preserve", "bảo toàn", "giữ nguyên", "without altering"):
                        if re.search(r"\b" + neg + r"\s+(?:toàn\s+bộ\s+)?(?:\w+\s+){0,3}" + ppat, clause_lower):
                            is_negated = True
                            break
                if is_negated:
                    prohibited = True

        # Check for positive requests in this clause
        for pat in patterns:
            match = re.search(r"\b" + pat + r"\b", clause_lower)
            if match:
                mentioned = True
                start_pos = match.start()
                pre_text = clause_lower[:start_pos].strip()
                is_negated = False
                for neg in NEGATION_PREFIXES:
                    if re.search(r"\b" + neg + r"(?:\s+\w+){0,4}\s*$", pre_text):
                        is_negated = True
                        break
                    if neg in ("không", "không được", "tuyệt đối không", "đừng", "never", "do not", "don't", "no", "without changing", "keep", "keep current", "keep existing", "preserve", "bảo toàn", "giữ nguyên"):
                        if re.search(r"\b" + neg + r"\s+(?:toàn\s+bộ\s+)?(?:\w+\s+){0,3}" + pat, clause_lower):
                            is_negated = True
                            break
                if not is_negated:
                    requested = True

    # Check explicit permission override
    perm_key_map = {
        ACTION_REDESIGN: "allow_architecture_change",
        ACTION_PALETTE: "allow_palette_change",
        ACTION_NAVIGATION: "allow_navigation_change",
        ACTION_BRAND: "allow_brand_change",
        ACTION_STRUCTURE: "allow_layout_change",
        ACTION_FRAMEWORK: "allow_framework_migration",
        ACTION_LIBRARY: "allow_library_replacement",
        ACTION_DEPENDENCY: "allow_new_dependencies",
    }
    key = perm_key_map.get(action, "")
    explicitly_allowed = bool(perms.get(key) or perms.get("explicit_l3_granted"))

    # Precedence: Explicit prohibition ALWAYS defeats weak positive mention
    if prohibited:
        requested = False

    return {
        "mentioned": mentioned,
        "requested": requested and not prohibited,
        "prohibited": prohibited,
        "explicitly_allowed": explicitly_allowed,
    }


def parse_all_semantic_permissions(
    text: str,
    explicit_permissions: dict[str, Any] | None = None,
) -> dict[str, dict[str, bool]]:
    """Parse all sensitive actions and return their full permission model."""
    results: dict[str, dict[str, bool]] = {}
    for action in SENSITIVE_ACTIONS:
        results[action] = parse_action_negation(action, text, explicit_permissions)
    return results


def parse_semantic_constraints(
    text: str,
    explicit_permissions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Parse semantic constraints and return actions map with common alias mappings."""
    actions = parse_all_semantic_permissions(text, explicit_permissions)
    actions["full_redesign"] = actions.get(ACTION_REDESIGN, {})
    actions["structural_redesign"] = actions.get(ACTION_STRUCTURE, {})

    text_lower = text.lower()
    has_layout_req = bool(re.search(r"\b(layout|redesign\s+layout|bố\s+cục)\b", text_lower))
    actions["layout_redesign"] = {
        "mentioned": has_layout_req,
        "requested": has_layout_req and not actions.get(ACTION_STRUCTURE, {}).get("prohibited", False),
        "prohibited": actions.get(ACTION_STRUCTURE, {}).get("prohibited", False),
        "explicitly_allowed": actions.get(ACTION_STRUCTURE, {}).get("explicitly_allowed", False),
    }

    has_refinement = bool(re.search(r"\b(modernize|refine|improve|polish|cải\s+thiện|nâng\s+cấp|làm\s+đẹp)\b", text_lower))
    actions["visual_refinement"] = {
        "mentioned": has_refinement,
        "requested": has_refinement,
        "prohibited": False,
        "explicitly_allowed": True,
    }
    return {"actions": actions, "text": text}
