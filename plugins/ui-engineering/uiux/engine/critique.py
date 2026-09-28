"""Visual critique scoring: merge an independent critic's rubric scores with measured gates and decide the loop.

Rules and rubric: review/visual-critique.md. Inputs are the critic's JSON critiques (after, optionally before), the
diff_ui_maps result, run_runtime capture manifests (layout_probe / motion_probe) and accessibility scans. The result
is ``pass``, ``iterate`` (with a short ``next_focus``) or ``stop`` (iteration budget spent or no progress).
"""
from __future__ import annotations

from typing import Any

WEIGHTS = {"hierarchy": 0.18, "composition": 0.16, "typography": 0.14, "color_surfaces": 0.12,
           "distinctiveness": 0.14, "craft": 0.12, "responsiveness": 0.08, "motion": 0.06}
SEVERITIES = ("blocker", "major", "minor")
ELEVATED = ("elevate", "reimagine")
KEY_DIMENSIONS = ("hierarchy", "composition", "distinctiveness")


class CritiqueError(ValueError):
    pass


def validate_critique(critique: Any, label: str) -> dict[str, Any]:
    if not isinstance(critique, dict):
        raise CritiqueError(f"{label}: critique must be an object")
    scores = critique.get("scores")
    if not isinstance(scores, dict):
        raise CritiqueError(f"{label}: 'scores' must be an object with the rubric dimensions")
    missing = [d for d in WEIGHTS if d not in scores]
    if missing:
        raise CritiqueError(f"{label}: missing dimensions {missing} (use null for motion when out of scope)")
    for dim, entry in scores.items():
        if dim not in WEIGHTS:
            raise CritiqueError(f"{label}: unknown dimension '{dim}'")
        if entry is None:
            if dim != "motion":
                raise CritiqueError(f"{label}: only 'motion' may be null")
            continue
        if not isinstance(entry, dict) or not isinstance(entry.get("score"), (int, float)) \
                or isinstance(entry.get("score"), bool) or not 1 <= entry["score"] <= 5:
            raise CritiqueError(f"{label}: {dim}.score must be a number 1..5")
        if not str(entry.get("evidence", "")).strip():
            raise CritiqueError(f"{label}: {dim} needs evidence (section, viewport, what is visible)")
    for issue in critique.get("issues", []) or []:
        if not isinstance(issue, dict) or issue.get("severity") not in SEVERITIES:
            raise CritiqueError(f"{label}: every issue needs severity blocker|major|minor")
    return critique


def weighted(critique: dict[str, Any]) -> float:
    active = {d: e["score"] for d, e in critique["scores"].items() if e is not None}
    total = sum(WEIGHTS[d] for d in active)
    return round(sum(WEIGHTS[d] * s for d, s in active.items()) / total, 2)


def _measured_gates(ambition: str, ui_map_diff: dict | None, captures: list[dict], scans: list[dict]) -> list[dict]:
    gates: list[dict[str, Any]] = []

    def gate(gate_id: str, severity: str, passed: bool, detail: str) -> None:
        gates.append({"id": gate_id, "severity": severity, "passed": passed, "detail": detail})

    if ui_map_diff is not None:
        removed = sorted({item for r in ui_map_diff.get("routes", []) for item in r.get("content_removed", [])})
        missing_routes = ui_map_diff.get("routes_removed", [])
        gate("content_preserved", "blocker", bool(ui_map_diff.get("content_preserved")) and not missing_routes,
             "all content and routes kept" if not (removed or missing_routes)
             else f"removed: {', '.join(removed[:6] + missing_routes)}")
        introduced = sorted({b for r in ui_map_diff.get("routes", []) for b in r.get("banlist_introduced", [])})
        gate("no_new_banlist_signals", "major", not introduced,
             "none introduced" if not introduced else ", ".join(introduced))
        if ambition in ELEVATED:
            bar = ui_map_diff.get("elevate_bar", {})
            gate("elevate_bar", "major", bool(bar.get("met")),
                 f"recomposition ratio {ui_map_diff.get('recomposition_ratio', 0)}")
    layout = [c for c in captures if isinstance(c.get("layout_probe"), dict) and "error" not in c["layout_probe"]]
    if layout:
        overflow = [f"{c.get('route')}@{c.get('viewport')}: {c['layout_probe'].get('horizontal_overflow_px', 0)}px"
                    for c in layout if c["layout_probe"].get("horizontal_overflow_px", 0) > 0]
        gate("no_horizontal_overflow", "blocker", not overflow, "none" if not overflow else "; ".join(overflow[:4]))
        tight = [f"{c.get('route')}@{c.get('viewport')}: {c['layout_probe']['small_targets']['count']}"
                 for c in layout if (c.get("width") or 9999) < 640
                 and c["layout_probe"].get("small_targets", {}).get("count", 0) > 3]
        gate("tap_targets", "major", not tight, "ok" if not tight else "; ".join(tight[:4]))
        tiny = [f"{c.get('route')}@{c.get('viewport')}: {c['layout_probe']['small_text']['count']}"
                for c in layout if c["layout_probe"].get("small_text", {}).get("count", 0) > 5]
        gate("legible_text", "minor", not tiny, "ok" if not tiny else "; ".join(tiny[:4]))
        fold = [f"{c.get('route')}@{c.get('viewport')}" for c in layout if (c.get("width") or 0) >= 1024
                and not (c["layout_probe"].get("above_fold", {}).get("h1_visible")
                         and c["layout_probe"].get("above_fold", {}).get("primary_action_visible"))]
        gate("above_the_fold", "minor", not fold, "ok" if not fold else "h1 or primary action below fold: " + ", ".join(fold[:4]))
    reduced = [c for c in captures if c.get("reduced_motion") == "reduce" and isinstance(c.get("motion_probe"), dict)
               and "error" not in c["motion_probe"]]
    if reduced:
        # infinite animations must stop; a static blur (decorative, or a settled blur(0px)) is not motion
        moving = [f"{c.get('route')}@{c.get('viewport')}" for c in reduced
                  if c["motion_probe"].get("animations", {}).get("infinite", 0) > 0]
        gate("reduced_motion_still", "major", not moving,
             "reduced-motion captures are still" if not moving else "still animating: " + ", ".join(moving[:4]))
    scanned = [s for s in scans if s.get("status") == "SCANNED"]
    if scanned:
        with_violations = [s for s in scanned if s.get("violations", 0) > 0]
        severe = [s for s in with_violations if set(s.get("impacts", [])) & {"critical", "serious"}]
        gate("accessibility", "blocker" if severe else "major", not with_violations,
             "no axe violations" if not with_violations else
             "; ".join(f"{s.get('route')}@{s.get('viewport')}: {s.get('violations')}" for s in with_violations[:4]))
    return gates


def score(after: dict, before: dict | None = None, ui_map_diff: dict | None = None,
          captures: list[dict] | None = None, accessibility_scans: list[dict] | None = None,
          ambition: str = "elevate", iteration: int = 1, max_iterations: int = 3,
          previous_score: float | None = None) -> dict[str, Any]:
    ambition = (ambition or "elevate").lower()
    after = validate_critique(after, "after")
    if before is not None:
        before = validate_critique(before, "before")
    after_score = weighted(after)
    before_score = weighted(before) if before else None
    dims = {d: (e["score"] if e else None) for d, e in after["scores"].items()}
    before_dims = {d: (e["score"] if e else None) for d, e in before["scores"].items()} if before else {}

    criteria: list[dict[str, Any]] = []

    def crit(crit_id: str, passed: bool, detail: str) -> None:
        criteria.append({"id": crit_id, "passed": passed, "detail": detail})

    low = sorted(d for d, s in dims.items() if s is not None and s < 3)
    if ambition in ELEVATED:
        crit("weighted_score", after_score >= 3.6, f"{after_score} (needs >= 3.6)")
        crit("no_weak_dimension", not low, "all >= 3" if not low else "below 3: " + ", ".join(low))
        crit("distinctiveness", (dims.get("distinctiveness") or 0) >= 3.5, f"{dims.get('distinctiveness')} (needs >= 3.5)")
        if before is not None:
            gain = round(after_score - before_score, 2)
            crit("improvement", gain >= 0.75, f"+{gain} over before (needs >= 0.75)")
            dropped = [d for d in KEY_DIMENSIONS if (dims.get(d) or 0) < (before_dims.get(d) or 0)]
            crit("key_dimensions_held", not dropped, "held" if not dropped else "dropped: " + ", ".join(dropped))
    else:
        crit("weighted_score", after_score >= 3.0, f"{after_score} (needs >= 3.0)")
        if before is not None:
            dropped = [d for d, s in dims.items() if s is not None and before_dims.get(d) is not None
                       and s < before_dims[d] - 0.5]
            crit("no_regression", not dropped, "none" if not dropped else "dropped: " + ", ".join(dropped))

    gates = _measured_gates(ambition, ui_map_diff, captures or [], accessibility_scans or [])
    issues = [dict(i, source="critic") for i in after.get("issues", []) or []]
    issues += [{"severity": g["severity"], "dimension": g["id"], "where": "measured", "observation": g["detail"],
                "fix": "resolve before re-scoring", "source": "gate"} for g in gates if not g["passed"]]
    order = {s: k for k, s in enumerate(SEVERITIES)}
    issues.sort(key=lambda i: (order[i["severity"]], dims.get(i.get("dimension"), 5) or 5))
    blockers = [i for i in issues if i["severity"] == "blocker"]
    failed_gates = [g for g in gates if not g["passed"] and g["severity"] in ("blocker", "major")]
    passed = all(c["passed"] for c in criteria) and not blockers and not failed_gates

    progress = None if previous_score is None else round(after_score - previous_score, 2)
    if passed:
        verdict, reason = "pass", "rubric criteria met and no blocking gate"
    elif iteration >= max_iterations:
        verdict, reason = "stop", f"iteration budget spent ({iteration}/{max_iterations}); report open issues to the user"
    elif progress is not None and progress < 0.1:
        verdict, reason = "stop", f"no material progress ({progress:+}); report open issues to the user"
    else:
        verdict, reason = "iterate", "fix next_focus, recapture the affected routes and score again"

    weakest = sorted((s, d) for d, s in dims.items() if s is not None)[:2]
    focus = [f"{i['severity']}: {i.get('where')} — {i.get('observation')} → {i.get('fix')}" for i in issues[:3]]
    focus += [f"raise {d} (scored {s})" for s, d in weakest if not any(d == i.get("dimension") for i in issues[:3])]
    result = {
        "verdict": verdict,
        "reason": reason,
        "ambition": ambition,
        "iteration": iteration,
        "score": {"after": after_score, "before": before_score,
                  "delta": None if before_score is None else round(after_score - before_score, 2),
                  "progress": progress},
        "dimensions": {d: {"after": dims[d], "before": before_dims.get(d)} for d in WEIGHTS},
        "criteria": criteria,
        "gates": gates,
        "issues": issues[:20],
        "next_focus": focus[:4] if verdict != "pass" else [],
        "signature_moves_seen": after.get("signature_moves_seen", []),
        "content_concerns": after.get("content_concerns", []),
    }
    result["markdown"] = render_markdown(result)
    return result


def render_markdown(result: dict[str, Any]) -> str:
    lines = [f"## Visual critique — iteration {result['iteration']}", "",
             f"Verdict: **{result['verdict']}** — {result['reason']}", "",
             "| Dimension | Before | After |", "|---|---|---|"]
    for dim, vals in result["dimensions"].items():
        lines.append(f"| {dim} | {vals['before'] if vals['before'] is not None else '—'} | "
                     f"{vals['after'] if vals['after'] is not None else '—'} |")
    s = result["score"]
    lines.append(f"| **weighted** | {s['before'] if s['before'] is not None else '—'} | **{s['after']}** |")
    lines += ["", "| Gate | Result |", "|---|---|"]
    lines += [f"| {g['id']} ({g['severity']}) | {'pass' if g['passed'] else 'FAIL'}: {g['detail']} |" for g in result["gates"]]
    if result["next_focus"]:
        lines += ["", "Next focus:"] + [f"- {f}" for f in result["next_focus"]]
    return "\n".join(lines) + "\n"
