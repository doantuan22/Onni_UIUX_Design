"""Structured request interpretation for P2.

This module deliberately does not call a model. Its deterministic parser is an
honestly labeled fallback; a host coding agent can use the emitted structured
context without exposing or persisting hidden chain-of-thought.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Literal, NotRequired, TypedDict

FieldState = Literal["EXPLICIT", "INFERRED", "UNKNOWN"]
ReasoningMode = Literal["SEMANTIC", "MODEL_ASSISTED", "HEURISTIC_FALLBACK"]


class SemanticField(TypedDict):
    value: Any
    state: FieldState
    evidence_refs: list[str]
    reason: str


class SemanticRequirement(TypedDict):
    schema_version: int
    goal: SemanticField
    task_type: SemanticField
    scope: SemanticField
    target_surfaces: SemanticField
    explicit_requirements: list[SemanticField]
    explicit_constraints: list[SemanticField]
    preservation_intent: SemanticField
    redesign_intent: SemanticField
    visual_intent: SemanticField
    responsive_intent: SemanticField
    accessibility_intent: SemanticField
    interaction_intent: SemanticField
    framework_constraints: SemanticField
    must_keep: list[SemanticField]
    must_change: list[SemanticField]
    must_not_change: list[SemanticField]
    permission_intent: dict[str, Any]
    concerns: list[str]
    ambiguities: list[dict[str, str]]
    language: str
    confidence: Literal["HIGH", "MEDIUM", "LOW"]
    reasoning_mode: ReasoningMode
    evidence_refs: list[str]
    knowledge_refs: list[str]
    rationale: list[str]
    reasoning_context: NotRequired[dict[str, Any]]


def _fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower())
    # Vietnamese đ is not a combining-mark variant of d, so fold it explicitly.
    decomposed = decomposed.replace("đ", "d")
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _field(value: Any = None, state: FieldState = "UNKNOWN", reason: str = "") -> SemanticField:
    return {"value": value, "state": state, "evidence_refs": ["user_request"] if state == "EXPLICIT" else [], "reason": reason}


def detect_language(text: str) -> str:
    """Small request-language detector for English, Vietnamese, mixed and other."""
    if not text or not text.strip():
        return "OTHER"
    folded = _fold(text)
    vietnamese_cues = re.findall(r"\b(?:lam dep|dep hon|hien dai hon|nang cap|giao dien|giu nguyen|khong doi|thiet ke|dap di lam lai|toan bo|sua|trang|bo cuc|mau sac|tong mau|khong|duoc phep|co the|dung|dong bo|tro nang|truc tiep|phan|danh sach|san pham|dung cham|toi uu|dien thoai|khong can|neu can|nhung|va|cho|chi)\b", folded)
    # Count semantic English instruction words, not shared technical nouns such as
    # checkout, dashboard, button, mobile, form, or framework.
    english_cues = re.findall(r"\b(?:improve|modernize|upgrade|redesign|rebuild|keep|preserve|without|change|allow|fix|only|entire|while|but|unless|don't|do not|should|must|make|build|create|add|repair|audit|review|check|inspect|update|standardize|enhance|polish|touch)\b", folded)
    if vietnamese_cues and english_cues:
        return "MIXED"
    if vietnamese_cues or re.search(r"[ăâđêôơưáàảãạấầẩẫậắằẳẵặéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ]", text.lower()):
        return "VI"
    if english_cues:
        return "EN"
    return "OTHER"


def _contains(text: str, *patterns: str) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def _known_targets(text: str, ui_context: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Match explicit request targets to P0 route/page/component graph entries."""
    context = ui_context or {}
    graph = context.get("ui_map") or context.get("ui_graph") or context.get("routes") or context.get("pages") or []
    if isinstance(graph, dict):
        graph = graph.get("routes", graph.get("pages", []))
    if not isinstance(graph, list):
        graph = []
    folded = _fold(text)
    matched: list[dict[str, Any]] = []
    selected = context.get("selected_surface") or context.get("selected_page") or context.get("current_route")
    if isinstance(selected, (str, dict)):
        selected_name = selected if isinstance(selected, str) else (selected.get("name") or selected.get("path") or selected.get("route") or "")
        selected_route = selected if isinstance(selected, str) else (selected.get("path") or selected.get("route") or selected_name)
        if selected_name:
            return [{"name": str(selected_name), "route": str(selected_route), "kind": "selected_surface"}]
    for item in graph:
        if isinstance(item, str):
            label, route, kind = item, item, "page"
        elif isinstance(item, dict):
            label = str(item.get("name") or item.get("label") or item.get("path") or item.get("route") or "")
            route = str(item.get("path") or item.get("route") or label)
            kind = str(item.get("type") or item.get("kind") or ("page" if route.startswith("/") else "component"))
        else:
            continue
        token = _fold(label.rsplit("/", 1)[-1].replace("-", " ").replace("_", " "))
        aliases = {"product": ("product listing", "product page", "danh sach san pham", "trang san pham", "bo loc san pham"),
            "products": ("product listing", "product page", "danh sach san pham", "trang san pham", "bo loc san pham"),
            "shop": ("product listing", "danh sach san pham", "bo loc san pham"),
            "landing": ("landing page", "trang landing", "trang chu"),
            "home": ("landing page", "trang landing", "trang chu")}
        alias_match = any(re.search(r"(?<!\w)" + re.escape(alias) + r"(?!\w)", folded) for alias in aliases.get(token, ()))
        if token and (re.search(r"(?<!\w)" + re.escape(token) + r"(?!\w)", folded) or alias_match):
            matched.append({"name": label, "route": route, "kind": kind})
    # Prefer the most specific graph label while preserving multiple disjoint targets.
    return list({(x["name"], x["route"]): x for x in matched}.values())


def analyze_semantic_requirements(
    request: str,
    *,
    ui_context: dict[str, Any] | None = None,
    knowledge_refs: list[str] | None = None,
    workflow: str | None = None,
) -> SemanticRequirement:
    """Normalize explicit and conservative inferred request concerns.

    Every semantic field has EXPLICIT / INFERRED / UNKNOWN state. Unknowns remain
    unknown; deterministic cues do not grant L3 permission beyond explicit clauses.
    """
    original = (request or "").strip()
    text = _fold(original)
    language = detect_language(original)
    targets = _known_targets(original, ui_context)

    explicit_target_patterns = {
        "checkout": r"\bcheckout\b|\bthanh toan\b|\btrang thanh toan\b",
        "cart": r"\bcart\b|\bgio hang\b|\btrang gio hang\b",
        "product_listing": r"\bproduct listing\b|\blist(?:ing)? of products\b|\b(?:danh sach|bo loc) san pham\b|\btrang san pham\b",
        "landing_page": r"\blanding(?: page)?\b|\btrang chu\b|\btrang landing\b",
        "dashboard": r"\bdashboard\b|\bbang dieu khien\b",
        "search_filter": r"\bsearch(?:ing)? filter\b|\bfilter\b|\bbo loc\b|\btim kiem\b",
        "form": r"\bform\b|\bbieu mau\b|\bdang ky\b|\bdang nhap\b",
        "button": r"\bbuttons?\b|\bnut\b",
    }
    named = [name for name, pattern in explicit_target_patterns.items() if _contains(text, pattern)]
    selected_only = bool(targets and targets[0].get("kind") == "selected_surface")
    if targets:
        target_value: Any = targets
        target_state: FieldState = "INFERRED" if selected_only else "EXPLICIT"
        target_reason = "Used the uniquely selected P0 surface." if selected_only else "Matched explicit request target(s) to the supplied P0 surface graph."
    elif named:
        target_value = [{"name": name, "route": None, "kind": "surface_candidate"} for name in named]
        target_state = "EXPLICIT"
        target_reason = "Explicit target phrase extracted; no matching P0 graph item was supplied."
    else:
        target_value, target_state = [], "UNKNOWN"
        target_reason = "Request does not identify a target surface."

    if _contains(text, r"\b(toan bo|entire|all pages|whole app|toan ung dung)\b") and not named:
        scope = _field("global", "EXPLICIT", "The request explicitly names the whole application or all pages.")
    elif _contains(text, r"\b(button|card|modal|dialog|form|filter|nut|bo loc|thanh phan|component)\b") and not _contains(text, r"\b(redesign|rebuild|thiet ke lai|dap di lam lai)\b"):
        scope = _field("component", "EXPLICIT", "The request names a bounded component-level change.")
    elif targets or named:
        scope = _field("page" if any(x in named for x in ("checkout", "cart", "landing_page", "dashboard", "product_listing")) or targets else "section",
            "INFERRED" if selected_only else "EXPLICIT", "Scope follows the selected P0 surface." if selected_only else "The request names a bounded page or surface.")
    elif _contains(text, r"\b(component|button|card|form|nut|thanh phan)\b"):
        scope = _field("component", "EXPLICIT", "The request names a bounded component.")
    elif _contains(text, r"\b(improve|better|good|dep hon|tot hon|nang cap|modernize|lam dep)\b"):
        scope = _field(None, "UNKNOWN", "A general improvement request does not establish a target scope.")
    else:
        scope = _field(None, "UNKNOWN", "No bounded scope can be established from the request.")

    task_type = "unknown"
    if _contains(text, r"\b(create|add(?: new)?|build|tao moi|tao\b.{0,24}\bmoi|them moi|them trang)\b"):
        task_type = "create"
    elif _contains(text, r"\b(audit|review|inspect|check|validate|kiem tra|danh gia)\b"):
        task_type = "audit"
    elif not _contains(text, r"\b(khong redesign|khong thiet ke lai|do not redesign|no redesign)\b") and _contains(text, r"\b(redesign|rebuild|thiet ke lai|dap di lam lai|xay lai)\b"):
        task_type = "redesign"
    elif _contains(text, r"\b(fix|repair|sua|khac phuc|loi)\b"):
        task_type = "fix"
    elif _contains(text, r"\b(improve|modernize|upgrade|enhance|polish|make (?:this|it) better|better|tot hon|dep hon|nang cap|lam dep|hien dai hon|dong bo|toi uu)\b"):
        task_type = "improve"
    task_field = _field(task_type, "INFERRED", "Task type is a conservative classification hint.") if task_type != "unknown" else _field(None, "UNKNOWN", "No task type cue was detected.")

    preserve_palette = _contains(text, r"\b(giu nguyen|bao toan|preserve|keep|without changing|do not change|don't change|must not change)\b.{0,35}\b(mau|mau sac|tong mau|palette|colors?|brand colors?|thuong hieu)\b", r"\b(khong doi|khong thay doi)\b.{0,24}\b(mau|palette|colors?)\b")
    preserve_brand = _contains(text, r"\b(giu nguyen|bao toan|preserve|keep)\b.{0,35}\b(brand|thuong hieu|identity)\b")
    preserve_framework = _contains(text, r"\b(khong doi|khong thay doi|giu nguyen|keep|preserve|do not change|don't change|must not change)\b.{0,35}\b(framework|stack)\b", r"\bwithout changing\b.{0,20}\bframework\b")
    preserve_desktop = _contains(text, r"\b(giu|preserve|keep)\b.{0,28}\b(desktop|layout desktop|bo cuc desktop)\b", r"\b(khong dung cham|khong sua|khong thay doi)\b.{0,25}\bdesktop\b")
    preserve_structure = _contains(text, r"\b(giu nguyen|bao toan|preserve|keep)\b.{0,30}\b(cau truc|structure)\b", r"\b(khong pha|khong doi|khong thay doi)\b.{0,25}\b(cau truc|structure)\b")
    protect_backend = _contains(text, r"\b(khong sua|khong thay doi|giu nguyen|do not change|don't change|keep|preserve)\b.{0,25}\b(backend|logic|business logic)\b")
    redesign_negated = _contains(text, r"\b(khong redesign|khong thiet ke lai|do not redesign|don't redesign|no redesign|without (?:a )?(?:global )?redesign)\b")
    redesign_explicit = not redesign_negated and _contains(text,
        r"\b(dap di lam lai|thiet ke lai|redesign|rebuild|xay lai tu dau)\b")
    palette_permission = not preserve_palette and _contains(text, r"\b(duoc phep|co the|allow|may)\b.{0,25}\b(doi|thay doi|change|recolor)\b.{0,20}\b(mau|palette|color)\b")
    layout_permission = not preserve_desktop and _contains(text, r"\b(duoc phep|cho phep|co the|allow|may)\b.{0,25}\b(doi|thay doi|change)\b.{0,20}\b(bo cuc|layout|structure)\b")
    if _contains(text, r"\b(giu nguyen cau truc|khong pha cau truc|preserve structure|keep structure)\b"):
        layout_permission = False

    responsive = _contains(text, r"\b(responsive|mobile|tablet|viewport|sua responsive|toi uu mobile|loi mobile|dien thoai)\b")
    accessibility = _contains(text, r"\b(accessibility|a11y|wcag|tro nang|focus(?: visibility| state| order)?|keyboard navigation|contrast|tuong phan|nhan tro nang)\b")
    interaction = _contains(text, r"\b(interaction|interactive|form|search filter|button|nut|focus(?: state| order)?|tab order|keyboard(?: navigation| accessibility)?|multi.step)\b")
    consistency = _contains(text, r"\b(consisten(?:cy|t)|standardize|dong bo|dong nhat)\b")
    visual = _contains(text, r"\b(visual|beautiful|modern|modernize|polish|dep hon|hien dai hon|lam dep|nang cap ui)\b")

    explicit_constraints: list[str] = []
    must_keep: list[str] = []
    must_change: list[str] = []
    must_not_change: list[str] = []
    if preserve_palette:
        must_keep.append("palette")
        must_not_change.append("brand palette")
        explicit_constraints.append("Preserve the current brand colors/palette.")
    if preserve_brand:
        must_keep.append("brand_identity")
        must_not_change.append("brand identity")
    if preserve_framework:
        must_keep.append("framework")
        must_not_change.append("framework")
        explicit_constraints.append("Keep the current framework/stack.")
    if preserve_desktop:
        must_keep.append("desktop_layout")
        must_not_change.append("desktop layout unless required by evidence")
    if preserve_structure:
        must_keep.append("page_structure")
        must_not_change.append("page structure")
        explicit_constraints.append("Preserve the existing page structure.")
    if protect_backend:
        must_keep.append("business_logic")
        must_not_change.append("backend/business logic")
        explicit_constraints.append("Do not modify backend or business logic.")
    if redesign_negated:
        must_not_change.append("global redesign")
    if responsive:
        must_change.append("responsive behavior")
    if consistency:
        must_change.append("component consistency")
    if accessibility:
        must_change.append("accessibility and focus behavior")
    if visual:
        must_change.append("visual presentation within the authorized design freedom")
    if palette_permission:
        must_change.append("palette may change with explicit permission")
    if layout_permission:
        must_change.append("layout may change within the named target")

    concerns = [name for name, present in (("preservation", bool(must_keep)), ("responsive", responsive),
        ("component_consistency", consistency), ("accessibility", accessibility), ("interaction", interaction)) if present]
    ambiguities: list[dict[str, str]] = []
    if not named and not targets:
        if _contains(text, r"\b(better|improve|good|tot hon|lam dep|hien dai hon|nang cap|dong bo)\b"):
            ambiguities.append({"field": "target_surfaces", "reason": "The request is broad but does not name a page/component."})
    if named and len(named) > 1:
        ambiguities.append({"field": "target_surfaces", "reason": "Multiple surfaces are named; confirm whether all are in scope if the P0 graph cannot disambiguate."})

    confidence = "HIGH" if named and (preserve_palette or preserve_framework or preserve_desktop or responsive or accessibility or redesign_explicit) else "MEDIUM" if named or concerns else "LOW"
    if ambiguities:
        confidence = "LOW"
    permission = {
        "redesign": {"value": "EXPLICITLY_ALLOWED" if redesign_explicit else "PROHIBITED" if redesign_negated else "NOT_AUTHORIZED",
            "state": "EXPLICIT" if redesign_explicit or redesign_negated else "UNKNOWN", "target": target_value,
            "evidence_refs": ["user_request"] if redesign_explicit or redesign_negated else [],
            "reason": "Explicit redesign wording is limited to the named target; vague improvement never grants L3."},
        "palette_change": {"value": "EXPLICITLY_ALLOWED" if palette_permission else "PROTECTED" if preserve_palette else "NOT_AUTHORIZED",
            "state": "EXPLICIT" if palette_permission or preserve_palette else "UNKNOWN", "target": target_value,
            "evidence_refs": ["user_request"] if palette_permission or preserve_palette else [],
            "reason": "Palette permission is granular and does not imply architecture/layout permission."},
        "layout_change": {"value": "EXPLICITLY_ALLOWED" if layout_permission else "PROTECTED" if preserve_desktop else "NOT_AUTHORIZED",
            "state": "EXPLICIT" if layout_permission or preserve_desktop else "UNKNOWN", "target": target_value,
            "evidence_refs": ["user_request"] if layout_permission or preserve_desktop else [],
            "reason": "Layout permission remains target-scoped and separate from palette permission."},
    }

    return {
        "schema_version": 1,
        "goal": _field(original, "EXPLICIT", "Verbatim user request; no hidden reasoning is stored."),
        "task_type": task_field,
        "scope": scope,
        "target_surfaces": _field(target_value, target_state, target_reason),
        "explicit_requirements": [_field(x, "EXPLICIT", "Requirement phrase detected in request.") for x in must_change],
        "explicit_constraints": [_field(x, "EXPLICIT", "Constraint phrase detected in request.") for x in explicit_constraints],
    "preservation_intent": _field({"palette": preserve_palette, "brand": preserve_brand,
            "framework": preserve_framework, "desktop_layout": preserve_desktop,
            "page_structure": preserve_structure, "business_logic": protect_backend},
            "EXPLICIT" if any((preserve_palette, preserve_brand, preserve_framework, preserve_desktop, preserve_structure, protect_backend)) else "UNKNOWN",
            "Only explicitly stated preservation constraints are represented as true."),
        "redesign_intent": _field(permission["redesign"], permission["redesign"]["state"], permission["redesign"]["reason"]),
        "visual_intent": _field(visual, "EXPLICIT" if visual else "UNKNOWN", "Explicit visual cue detected." if visual else "No visual intent stated."),
        "responsive_intent": _field(responsive, "EXPLICIT" if responsive else "UNKNOWN", "Responsive concern explicitly named." if responsive else "No responsive requirement stated."),
        "accessibility_intent": _field(accessibility, "EXPLICIT" if accessibility else "UNKNOWN", "Accessibility/focus concern explicitly named." if accessibility else "No accessibility requirement stated."),
        "interaction_intent": _field(interaction, "EXPLICIT" if interaction else "UNKNOWN", "Interaction surface named." if interaction else "No interaction requirement stated."),
        "framework_constraints": _field(["preserve_framework"] if preserve_framework else [], "EXPLICIT" if preserve_framework else "UNKNOWN",
            "Framework preservation was explicitly requested." if preserve_framework else "No framework constraint stated."),
        "must_keep": [_field(x, "EXPLICIT", "Explicit preservation requirement.") for x in must_keep],
        "must_change": [_field(x, "EXPLICIT", "Explicit requested concern.") for x in must_change],
        "must_not_change": [_field(x, "EXPLICIT", "Explicit prohibition or preservation constraint.") for x in must_not_change],
        "permission_intent": permission,
        "concerns": concerns,
        "ambiguities": ambiguities,
        "language": language,
        "confidence": confidence,
        "reasoning_mode": "HEURISTIC_FALLBACK",
        "evidence_refs": ["user_request"] + (["p0:surface_graph"] if targets else []),
        "knowledge_refs": list(knowledge_refs or []),
        "rationale": ["Structured fields represent request evidence and conservative inference only.",
            "Deterministic L1/L2/L3, preservation, framework, scope and PlanningGate guards remain authoritative."],
        "reasoning_context": {"instruction": "Interpret the structured requirement fields against P0 evidence and P1 knowledge; preserve UNKNOWN values, return bounded structured recommendations, and do not override deterministic permissions.",
            "stores_chain_of_thought": False},
    }
