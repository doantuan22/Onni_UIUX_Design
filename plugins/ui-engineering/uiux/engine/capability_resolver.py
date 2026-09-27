"""Design Capability Resolver: requirement profile -> ranked design capabilities with WHY / WHY NOT.

Deterministic and standard-library only. It reads the Design Knowledge System catalogs (see
skills/capability-resolver/README.md) and never installs or fetches anything. Public entry: ``resolve(profile)``
(exposed as ``uiux.api.resolve_capabilities``). Technology resolution lives in ``uiux.engine.technology``,
retrieval in ``uiux.engine.retrieval`` and budgets in ``uiux.engine.performance``; their names are re-exported here
for backward compatibility.

Usage:
    python scripts/resolve_capabilities.py --profile evals/resolver-scenarios/premium-ai-saas.json
    python scripts/resolve_capabilities.py --profile p.json --format md > CAPABILITY-PLAN.md
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from uiux.core import config
from uiux.engine import performance
from uiux.engine.retrieval import retrieval
from uiux.engine.technology import resolve_technology
from uiux.knowledge import catalog as K

INTENSITY_LEVEL = {"low": 1, "medium": 2, "high": 3}
DENSITY_LEVEL = {"low": 1, "medium": 2, "high": 3}
COST_POINTS = performance.cost_points()
EFFECT_BUDGET = performance.effect_budget()
TIER_LEVEL = {"primitive": 0, "M1": 1, "M2": 2, "M3": 3, "M4": 4, "M5": 5}
BASELINE_MOTION = ("motion.m1-press", "motion.m1-focus", "motion.m1-hover")
BASELINE_INTERACTIONS = ("interaction.press-feedback", "interaction.focus-management", "interaction.keyboard-navigation")
MAX_SECTION_LAYOUTS = performance.motion_budget()["max_section_layouts"]
MAX_INTERACTIONS = performance.motion_budget()["max_interactions"]
MAX_MOTION = performance.motion_budget()["max_motion_patterns"]
MAX_HIGH_REGIONS = performance.motion_budget()["max_high_regions"]
# Brand attributes that a style's conveyed attributes contradict (penalized, not banned).
CONFLICTS = {
    "calm": {"energetic", "bold", "loud", "chaotic", "raw", "rebellious"},
    "serious": {"playful", "childish", "unserious"},
    "trustworthy": {"rebellious", "chaotic", "raw"},
    "minimal": {"cluttered", "dense"},
    "luxurious": {"playful", "loud", "raw", "energetic"},
    "efficient": {"cinematic", "immersive"},
    "precise": {"organic", "raw"},
    "friendly": {"intimidating", "cold"},
}


class ProfileError(ValueError):
    code = "INVALID_ARGUMENT"  # error contract code (uiux/core/errors.json)


class KnowledgeBaseError(ProfileError):
    code = "REGISTRY_INVALID"


def _flag(name: str) -> bool:
    return bool(config.get()["feature_flags"][name])


# --------------------------------------------------------------------------- profile
def normalize_profile(raw: dict, entries: dict[str, dict]) -> dict:
    if not isinstance(raw, dict):
        raise ProfileError("profile must be an object")
    p = {
        "id": raw.get("id", "profile"),
        "intent": raw.get("intent", ""),
        "domain": list(raw.get("domain", [])),
        "brand_attributes": list(raw.get("brand_attributes", [])),
        "avoid_attributes": list(raw.get("avoid_attributes", [])),
        "visual_intensity": raw.get("visual_intensity"),
        "interaction_intensity": raw.get("interaction_intensity"),
        "density": raw.get("density"),
        "contexts": list(raw.get("contexts", [])),
        "screens": list(raw.get("screens", [])),
        "content": list(raw.get("content", [])),
        "platform": list(raw.get("platform", ["desktop", "mobile"])),
        "existing_dependencies": list(raw.get("existing_dependencies", [])),
        "allow_new_dependencies": bool(raw.get("allow_new_dependencies", False)),
        "allow_motion_library": bool(raw.get("allow_motion_library", False)),
        "explicit_styles": list(raw.get("explicit_styles", [])),
        "exclude_styles": list(raw.get("exclude_styles", [])),
    }
    checks = [("domain", K.DOMAINS), ("brand_attributes", K.ATTRIBUTES), ("avoid_attributes", K.ATTRIBUTES),
              ("contexts", K.CONTEXTS), ("content", K.CONTENT)]
    for field, vocab in checks:
        unknown = [v for v in p[field] if v not in vocab]
        if unknown:
            raise ProfileError(f"{field} has values outside the controlled vocabulary: {unknown}")
    if not p["domain"] or not p["brand_attributes"] or not p["contexts"]:
        raise ProfileError("domain, brand_attributes and contexts are required (see the pre-design declaration)")
    for field in ("visual_intensity", "interaction_intensity"):
        if not isinstance(p[field], int) or not 1 <= p[field] <= 5:
            raise ProfileError(f"{field} must be an integer 1..5")
    if p["density"] not in K.DENSITY:
        raise ProfileError("density must be low, medium or high")
    for sid in p["screens"] + p["explicit_styles"] + p["exclude_styles"]:
        if sid not in entries:
            raise ProfileError(f"unknown catalog id in profile: {sid}")
    return p


# --------------------------------------------------------------------------- helpers
def _list(value: object) -> list[str]:
    return K._as_list(value)


def _of_kind(entries: dict[str, dict], kind: str) -> list[dict]:
    return [e for i, e in sorted(entries.items()) if e["kind"] == kind]


def _rank(items: list[tuple[float, str, dict]]) -> list[tuple[float, str, dict]]:
    return sorted(items, key=lambda t: (-t[0], t[1]))


# --------------------------------------------------------------------------- styles
def score_style(style: dict, p: dict) -> tuple[float | None, list[str], str]:
    """Return (score or None if rejected, reasons, rejection reason)."""
    sid = style["id"]
    if sid in p["exclude_styles"]:
        return None, [], "excluded by profile"
    if not set(_list(style["contexts"])) & set(p["contexts"]):
        return None, [], f"contexts {style['contexts']} do not include {p['contexts']}"
    if p["density"] not in _list(style["density"]):
        return None, [], f"density {p['density']} outside {style['density']}"
    lo, hi = (int(x) for x in style["intensity"])
    vi = p["visual_intensity"]
    if vi < lo - 1 or vi > hi + 1:
        return None, [], f"visual intensity {vi} far outside [{lo}, {hi}]"
    score, reasons = 0.0, []
    domains = sorted(set(_list(style["domains"])) & set(p["domain"]))
    if domains:
        score += 3 * len(domains); reasons.append(f"domain fit: {', '.join(domains)}")
    conveys = sorted(set(_list(style["conveys"])) & set(p["brand_attributes"]))
    if conveys:
        score += 2 * len(conveys); reasons.append(f"conveys: {', '.join(conveys)}")
    risks = sorted((set(_list(style["perceived_risks"])) | set(_list(style["conveys"]))) & set(p["avoid_attributes"]))
    if risks:
        score -= 4 * len(risks); reasons.append(f"risk of projecting avoided attributes: {', '.join(risks)}")
    conflicts = sorted({c for a in p["brand_attributes"] for c in CONFLICTS.get(a, set())} & set(_list(style["conveys"]))) \
        if _flag("attribute_conflict_penalty") else []
    if conflicts:
        score -= 2 * len(conflicts); reasons.append(f"conveys attributes that conflict with the brand: {', '.join(conflicts)}")
    if lo <= vi <= hi:
        score += 2; reasons.append(f"visual intensity {vi} within [{lo}, {hi}]")
    else:
        score -= 1; reasons.append(f"visual intensity {vi} just outside [{lo}, {hi}]")
    if sid in p["explicit_styles"]:
        score += 10; reasons.append("explicitly requested")
    elif style["default_tell"] == "true" and _flag("anti_homogenization_guard"):
        score -= 2; reasons.append("default-tell penalty (anti-homogenization)")
    return score, reasons, ""


def resolve_styles(entries: dict[str, dict], p: dict) -> dict:
    scored, rejected = [], []
    for style in _of_kind(entries, "style"):
        score, reasons, why_not = score_style(style, p)
        if score is None:
            rejected.append({"id": style["id"], "reason": why_not})
        else:
            scored.append((score, style["id"], {"reasons": reasons}))
    ranked = _rank(scored)
    if not ranked or ranked[0][0] <= 0:
        raise ProfileError("no style scores above zero; the profile lacks usable signals")
    top_score, primary_id, primary_meta = ranked[0]
    primary = entries[primary_id]
    secondary = None
    for score, sid, meta in ranked[1:]:
        if sid in _list(primary["compatible_styles"]) and score >= 1:
            if primary["default_tell"] == "true" and entries[sid]["default_tell"] == "true":
                continue
            secondary = {"id": sid, "score": score, "why": meta["reasons"], "scope": "scoped secondary (one region or layer)"}
            break
    runners = []
    for score, sid, meta in ranked[1:6]:
        if secondary and sid == secondary["id"]:
            continue
        gap = top_score - score
        runners.append({"id": sid, "score": score, "why_not": f"scores {gap:g} below {primary_id}; " + "; ".join(meta["reasons"])})
    return {"primary": {"id": primary_id, "score": top_score, "why": primary_meta["reasons"]},
            "secondary": secondary, "runners_up": runners, "rejected": rejected[:12]}


# --------------------------------------------------------------------------- layouts
def resolve_layouts(entries: dict[str, dict], p: dict, primary: dict, secondary: dict | None, screens: list[dict]) -> dict:
    vi = p["visual_intensity"]
    screen_layouts = {lid for s in screens for lid in _list(s["compatible_layouts"])}
    scored, rejected = [], []
    for layout in _of_kind(entries, "layout"):
        lid = layout["id"]
        if not set(_list(layout["contexts"])) & set(p["contexts"]):
            continue  # silently out of scope: not a candidate for this surface
        missing = [c for c in _list(layout["content_requirements"]) if c not in p["content"]]
        if missing:
            rejected.append({"id": lid, "reason": f"missing required content: {', '.join(missing)}"}); continue
        gap = min(abs(DENSITY_LEVEL[d] - DENSITY_LEVEL[p["density"]]) for d in _list(layout["density"]))
        if gap > 1:
            rejected.append({"id": lid, "reason": f"density {layout['density']} too far from {p['density']}"}); continue
        cost = INTENSITY_LEVEL[layout["motion_cost"]]
        if cost == 3 and vi < 4:
            rejected.append({"id": lid, "reason": f"high motion cost needs visual intensity >= 4 (profile {vi})"}); continue
        score, reasons = 0.0, []
        if primary["id"] in _list(layout["compatible_styles"]):
            score += 4; reasons.append(f"compatible with {primary['id']}")
        if secondary and secondary["id"] in _list(layout["compatible_styles"]):
            score += 2; reasons.append(f"compatible with {secondary['id']}")
        if lid in _list(primary["compatible_patterns"]):
            score += 3; reasons.append(f"listed by {primary['id']} as a pattern")
        if lid in screen_layouts:
            score += 3; reasons.append("fits a requested screen")
        if gap:
            score -= gap; reasons.append("density one level off")
        if cost == 2 and vi < 3:
            score -= 1; reasons.append("medium motion cost at low intensity")
        if layout["default_tell"] == "true" and primary["id"] not in p["explicit_styles"] and _flag("anti_homogenization_guard"):
            score -= 2; reasons.append("default-tell penalty (anti-homogenization)")
        if score <= 0:
            rejected.append({"id": lid, "reason": "no compatibility with the selected styles or screens"}); continue
        scored.append((score, lid, {"category": layout["category"], "reasons": reasons}))
    ranked = _rank(scored)
    selected: list[dict] = []
    marketing = bool({"marketing", "content", "commerce"} & set(p["contexts"]))
    application = "application" in p["contexts"]
    def take(categories: set[str], limit: int, per_category: int) -> None:
        counts: dict[str, int] = {}
        for score, lid, meta in ranked:
            if len([s for s in selected if s["category"] in categories]) >= limit:
                return
            if meta["category"] not in categories or any(s["id"] == lid for s in selected):
                continue
            if counts.get(meta["category"], 0) >= per_category:
                continue
            counts[meta["category"]] = counts.get(meta["category"], 0) + 1
            selected.append({"id": lid, "category": meta["category"], "score": score, "why": meta["reasons"]})
    if marketing:
        take({"hero"}, 1, 1)
        take({"grid", "storytelling"}, MAX_SECTION_LAYOUTS, 2)
    if application:
        take({"application"}, 2, 2)
        take({"grid"}, 1 + (0 if marketing else 1), 1)
    chosen = {s["id"] for s in selected}
    not_chosen = [{"id": lid, "score": score, "why_not": "lower-ranked than selected alternatives in its category"}
                  for score, lid, _ in ranked if lid not in chosen][:6]
    return {"selected": selected, "runners_up": not_chosen, "rejected": rejected[:15]}


# --------------------------------------------------------------------------- motion
def motion_rules(p: dict, primary: dict) -> tuple[set[str], int]:
    vi, ii = p["visual_intensity"], p["interaction_intensity"]
    ceiling = TIER_LEVEL[primary["motion_ceiling"]]
    allowed = {"primitive", "M1", "M2"}
    if ii >= 3 or "application" in p["contexts"]:
        allowed.add("M3")
    if {"marketing", "content"} & set(p["contexts"]) and vi >= 2:
        allowed.add("M4")
    if vi >= 4 and "desktop" in p["platform"] and "marketing" in p["contexts"]:
        allowed.add("M5")
    allowed = {t for t in allowed if TIER_LEVEL[t] <= ceiling}
    max_intensity = 3 if vi >= 4 else 2 if (vi >= 2 or ii >= 3) else 1
    return allowed, max_intensity


def resolve_motion(entries: dict[str, dict], p: dict, primary: dict, secondary: dict | None,
                   layouts: list[dict], screens: list[dict]) -> dict:
    allowed, max_intensity = motion_rules(p, primary)
    order: list[str] = []
    sources = [list(BASELINE_MOTION), _list(primary["recommended_motion"])]
    if secondary:
        sources.append(_list(entries[secondary["id"]]["recommended_motion"]))
    sources += [_list(entries[l["id"]]["compatible_motion"]) for l in layouts]
    sources += [_list(s["key_motion"]) for s in screens]
    for source in sources:
        for mid in source:
            if mid not in order:
                order.append(mid)
    selected, rejected, high_taken = [], [], []
    for mid in order:
        m = entries[mid]
        if m["tier"] not in allowed:
            rejected.append({"id": mid, "reason": f"tier {m['tier']} not allowed (allowed {sorted(allowed)}, style ceiling {primary['motion_ceiling']})"}); continue
        if not set(_list(m["contexts"])) & set(p["contexts"]):
            rejected.append({"id": mid, "reason": f"contexts {m['contexts']} outside profile"}); continue
        if INTENSITY_LEVEL[m["intensity"]] > max_intensity:
            rejected.append({"id": mid, "reason": f"intensity {m['intensity']} exceeds budget for visual {p['visual_intensity']}/interaction {p['interaction_intensity']}"}); continue
        if len(selected) >= MAX_MOTION:
            rejected.append({"id": mid, "reason": f"motion vocabulary capped at {MAX_MOTION} patterns per plan"}); continue
        if m["intensity"] == "high":
            if len(high_taken) >= MAX_HIGH_REGIONS:
                allowance = "one HIGH region" if MAX_HIGH_REGIONS == 1 else f"{MAX_HIGH_REGIONS} HIGH regions"
                rejected.append({"id": mid, "reason": f"motion budget allows {allowance} ({', '.join(high_taken)} already selected)"}); continue
            high_taken.append(mid)
        selected.append({"id": mid, "tier": m["tier"], "intensity": m["intensity"], "serves": _list(m["serves"])})
    return {"allowed_tiers": sorted(allowed, key=TIER_LEVEL.get), "selected": selected, "rejected": rejected}


# --------------------------------------------------------------------------- interactions
def resolve_interactions(entries: dict[str, dict], p: dict, layouts: list[dict], screens: list[dict]) -> dict:
    order: list[str] = list(BASELINE_INTERACTIONS)
    for source in [_list(s["key_interactions"]) for s in screens] + [_list(entries[l["id"]]["interactions"]) for l in layouts]:
        for iid in source:
            if iid not in order:
                order.append(iid)
    selected, rejected = [], []
    for iid in order:
        it = entries[iid]
        if int(it["min_interaction_intensity"]) > p["interaction_intensity"]:
            rejected.append({"id": iid, "reason": f"needs interaction intensity >= {it['min_interaction_intensity']}"}); continue
        if not set(_list(it["contexts"])) & set(p["contexts"]):
            rejected.append({"id": iid, "reason": "context mismatch"}); continue
        if len(selected) >= MAX_INTERACTIONS:
            rejected.append({"id": iid, "reason": "interaction budget reached"}); continue
        selected.append({"id": iid, "category": it["category"]})
    return {"selected": selected, "rejected": rejected}


# --------------------------------------------------------------------------- effects
def resolve_effects(entries: dict[str, dict], p: dict, primary: dict, secondary: dict | None, tell_budget: list[str]) -> dict:
    vi = p["visual_intensity"]
    avoid = set(_list(primary["avoid_effects"]))
    candidates = list(_list(primary["recommended_effects"]))
    from_secondary: set[str] = set()
    if secondary:
        # The secondary style is scoped: it may add low/medium-cost supporting effects only, and its own
        # avoid list constrains its contributions, never the primary style's language.
        sec = entries[secondary["id"]]
        for e in _list(sec["recommended_effects"]):
            if e not in candidates:
                candidates.append(e); from_secondary.add(e)
    limit, used = EFFECT_BUDGET[vi], 0
    selected, rejected, signature = [], [], None
    for eid in candidates:
        e = entries[eid]
        cost = e["performance"]["cost"]
        if eid in avoid:
            rejected.append({"id": eid, "reason": "listed in the primary style's avoid_effects"}); continue
        if eid in from_secondary and COST_POINTS[cost] >= 4:
            rejected.append({"id": eid, "reason": "scoped secondary style may not introduce a high-cost signature effect"}); continue
        if not set(_list(e["recommended_contexts"])) & set(p["contexts"]):
            rejected.append({"id": eid, "reason": "not recommended for these contexts"}); continue
        if COST_POINTS[cost] >= 4 and vi < 4:
            rejected.append({"id": eid, "reason": f"{cost} cost needs visual intensity >= 4"}); continue
        if COST_POINTS[cost] >= 4 and signature:
            rejected.append({"id": eid, "reason": f"one signature effect per page ({signature} already)"}); continue
        if used + COST_POINTS[cost] > limit:
            rejected.append({"id": eid, "reason": f"effect budget {limit} points exceeded"}); continue
        if e["default_tell"] == "true" and primary["id"] not in p["explicit_styles"] and _flag("anti_homogenization_guard"):
            if tell_budget:
                rejected.append({"id": eid, "reason": f"anti-homogenization: default-tell budget used by {tell_budget[0]}"}); continue
            tell_budget.append(eid)
        used += COST_POINTS[cost]
        if COST_POINTS[cost] >= 4:
            signature = eid
        selected.append({"id": eid, "cost": cost})
    if not signature and selected:
        signature = max(selected, key=lambda s: (COST_POINTS[s["cost"]], -candidates.index(s["id"])))["id"]
    return {"selected": selected, "signature": signature, "budget": {"used": used, "limit": limit}, "rejected": rejected}


# --------------------------------------------------------------------------- technology
# --------------------------------------------------------------------------- recipe + retrieval
def resolve_recipe(entries: dict[str, dict], p: dict, plan: dict) -> dict:
    primary = plan["style"]["primary"]["id"]
    secondary = (plan["style"]["secondary"] or {}).get("id")
    layouts = {l["id"] for l in plan["layouts"]["selected"]}
    effects = {e["id"] for e in plan["effects"]["selected"]}
    scored = []
    for r in _of_kind(entries, "recipe"):
        score = 3 * len(set(_list(r["domains"])) & set(p["domain"]))
        score += 4 * (primary in _list(r["styles"])) + 2 * (bool(secondary) and secondary in _list(r["styles"]))
        score += len(layouts & set(_list(r["layouts"]))) + len(effects & set(_list(r["effects"])))
        score += len(set(_list(r["conveys"])) & set(p["brand_attributes"]))
        scored.append((score, r["id"], r))
    score, rid, r = _rank(scored)[0]
    return {"anchor": rid, "score": score, "typography": r["typography"], "surface": r["surface"], "color": r["color"],
            "avoid": r["avoid"], "why": r["why"],
            "not_adopted": sorted((set(_list(r["layouts"])) - layouts) | (set(_list(r["effects"])) - effects))}


def resolve(raw_profile: dict, entries: dict[str, dict] | None = None) -> dict:
    if entries is None:
        entries, errors = K.load()
        if errors:
            raise KnowledgeBaseError("knowledge base failed to load: " + "; ".join(errors[:3]))
    p = normalize_profile(raw_profile, entries)
    screens = [entries[s] for s in p["screens"]]
    styles = resolve_styles(entries, p)
    primary = entries[styles["primary"]["id"]]
    secondary = styles["secondary"]
    tell_budget: list[str] = []
    guard = _flag("anti_homogenization_guard")
    if guard and secondary and entries[secondary["id"]]["default_tell"] == "true" and secondary["id"] not in p["explicit_styles"]:
        tell_budget.append(secondary["id"])
    layouts = resolve_layouts(entries, p, primary, secondary, screens)
    # Anti-homogenization: at most one default-tell item across secondary style, layouts and effects.
    kept = []
    for item in layouts["selected"]:
        if guard and entries[item["id"]]["default_tell"] == "true" and primary["id"] not in p["explicit_styles"]:
            if tell_budget:
                layouts["rejected"].insert(0, {"id": item["id"], "reason": f"anti-homogenization: default-tell budget used by {tell_budget[0]}"})
                continue
            tell_budget.append(item["id"])
        kept.append(item)
    layouts["selected"] = kept
    motion = resolve_motion(entries, p, primary, secondary, layouts["selected"], screens)
    interactions = resolve_interactions(entries, p, layouts["selected"], screens)
    effects = resolve_effects(entries, p, primary, secondary, tell_budget)
    capability_ids = [m["id"] for m in motion["selected"]] + [e["id"] for e in effects["selected"]] + [i["id"] for i in interactions["selected"]]
    technology = resolve_technology(entries, p, capability_ids)
    degraded = {d["id"] for d in technology["degraded"]}
    for section in (motion, effects, interactions):
        moved = [s for s in section["selected"] if s["id"] in degraded]
        section["selected"] = [s for s in section["selected"] if s["id"] not in degraded]
        section["rejected"] += [{"id": s["id"], "reason": "degraded: required technology not available"} for s in moved]
    if effects["signature"] in degraded:
        effects["signature"] = None
    plan = {
        "profile": p,
        "style": styles,
        "layouts": layouts,
        "screens": [{"id": s["id"], "compatible_layouts": _list(s["compatible_layouts"])} for s in screens],
        "motion": motion,
        "interactions": interactions,
        "effects": effects,
        "technology": technology,
    }
    plan["recipe"] = resolve_recipe(entries, p, plan)
    tells = [i for i in [styles["primary"]["id"]] + tell_budget if entries[i]["default_tell"] == "true"]
    plan["guards"] = {"default_tells": tells, "homogenized": len(tells) >= 3}
    plan["retrieval"] = retrieval(entries, plan)
    return plan


# --------------------------------------------------------------------------- rendering
def render_markdown(plan: dict) -> str:
    p, s = plan["profile"], plan["style"]
    lines = [f"# Capability Plan — {p['id']}", "", f"Intent: {p['intent'] or '(not stated)'}", "",
             "## Profile", "", "```json", json.dumps({k: v for k, v in p.items() if k != 'intent'}, indent=2), "```", "",
             "## Style", "", f"- **Primary:** `{s['primary']['id']}` (score {s['primary']['score']:g}) — WHY: {'; '.join(s['primary']['why'])}"]
    if s["secondary"]:
        lines.append(f"- **Secondary ({s['secondary']['scope']}):** `{s['secondary']['id']}` — WHY: {'; '.join(s['secondary']['why'])}")
    lines += [f"- WHY NOT `{r['id']}`: {r['why_not']}" for r in s["runners_up"][:3]]
    lines += ["", "## Layouts", ""]
    lines += [f"- `{l['id']}` ({l['category']}) — WHY: {'; '.join(l['why'])}" for l in plan["layouts"]["selected"]]
    lines += [f"- WHY NOT `{r['id']}`: {r['reason']}" for r in plan["layouts"]["rejected"][:4]]
    if plan["screens"]:
        lines += ["", "## Screens", ""] + [f"- `{x['id']}` → layouts {', '.join(x['compatible_layouts'])}" for x in plan["screens"]]
    lines += ["", "## Motion", "", f"Allowed tiers: {', '.join(plan['motion']['allowed_tiers'])}", ""]
    lines += [f"- `{m['id']}` ({m['tier']}, {m['intensity']}) serves {', '.join(m['serves'])}" for m in plan["motion"]["selected"]]
    lines += [f"- WHY NOT `{r['id']}`: {r['reason']}" for r in plan["motion"]["rejected"][:5]]
    lines += ["", "## Interactions", ""] + [f"- `{i['id']}`" for i in plan["interactions"]["selected"]]
    lines += [f"- WHY NOT `{r['id']}`: {r['reason']}" for r in plan["interactions"]["rejected"][:3]]
    e = plan["effects"]
    lines += ["", "## Effects", "", f"Budget {e['budget']['used']}/{e['budget']['limit']} points; signature: `{e['signature']}`", ""]
    lines += [f"- `{x['id']}` ({x['cost']})" for x in e["selected"]]
    lines += [f"- WHY NOT `{r['id']}`: {r['reason']}" for r in e["rejected"][:5]]
    t = plan["technology"]
    lines += ["", "## Technology", "", f"Technologies: {', '.join(t['technologies'])}",
              f"Reused existing: {', '.join(t['existing_reused']) or 'none'}",
              f"New dependencies: {', '.join(t['new_dependencies']) or 'none'}"]
    lines += [f"- Degraded `{d['id']}`: {d['reason']}" for d in t["degraded"]]
    r = plan["recipe"]
    lines += ["", "## Composition", "", f"Recipe anchor: `{r['anchor']}` — {r['why']}", f"- Typography: {r['typography']}",
              f"- Surface: {r['surface']}", f"- Color: {r['color']}", f"- Avoid: {r['avoid']}",
              f"- Recipe items not adopted: {', '.join(r['not_adopted']) or 'none'}", "",
              "## Guards", "", f"- Default-tell items: {', '.join(plan['guards']['default_tells']) or 'none'}",
              f"- Homogenized: {plan['guards']['homogenized']}", "", "## Retrieval (load only these)", ""]
    lines += [f"- `{f}`" for f in plan["retrieval"]]
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to a legacy code page
    ap = argparse.ArgumentParser(description="Resolve design capabilities from a requirement profile")
    ap.add_argument("--profile", required=True)
    ap.add_argument("--format", choices=("json", "md"), default="json")
    args = ap.parse_args(argv)
    try:
        raw = json.loads(Path(args.profile).read_text(encoding="utf-8"))
        plan = resolve(raw.get("profile", raw))
    except (OSError, json.JSONDecodeError, ProfileError) as exc:
        print(json.dumps({"status": "INVALID_PROFILE", "error": str(exc)}))
        return 3
    print(render_markdown(plan) if args.format == "md" else json.dumps(plan, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
