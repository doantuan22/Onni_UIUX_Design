# Visual critique loop

Rendered evidence decides whether a visual change is done, not the diff. The loop captures the page before and
after, lets an independent critic score both against the rubric below, merges that judgement with facts the tools
measure (content preservation, overflow, tap targets, accessibility, motion), and either passes, asks for one more
targeted iteration, or stops and hands the open issues to the user. It is step 6 of the
[Elevate procedure](../workflows/ambition-levels.md#elevate-procedure) and applies to Reimagine work as well.

## Loop

1. **Capture before** (once, before editing): `run_runtime` for the key routes at `mobile`, `tablet` and `desktop`
   with `options: {"full_page": true, "layout_probe": true, "motion_probe": true}`, plus one capture with
   `"reduced_motion": "reduce"`. Keep `map_ui_structure` output as `.uiux/ui-map.json`.
2. **Implement** the direction (recipes, tokens, motion).
3. **Capture after** with the same routes, viewports and options (next `iteration` number); run `accessibility_scan`
   when axe is available; run `map_ui_structure` again and `diff_ui_maps` against the saved map.
4. **Critique** with a critic that did not write the code:
   - Claude Code: delegate to the plugin's **`visual-critic`** subagent ([agents/visual-critic.md](../agents/visual-critic.md)).
     Give it only the screenshot paths (before and after), `DESIGN-DIRECTION.md` and this rubric — not your reasoning
     or the diff. It returns one JSON critique for `before` and one for `after`.
   - Hosts without subagents (Codex, generic MCP): run the critique as a separate step with a fresh context: read
     only the same inputs, score before writing any fix, and do not revise scores afterwards.
5. **Score**: call `score_visual_critique` with both critiques, the `diff_ui_maps` result, the capture manifests
   (`captures`) and the accessibility scans. It returns `pass`, `iterate` or `stop`.
6. **Iterate** on `next_focus` only (the weakest dimension and the blocking issues), recapture the affected routes
   (`recapture_evidence` computes the minimal surface) and score again. At most **two** iterations after the first
   score; stop earlier when the score improves by less than 0.1.
7. **Record** the result in `VISUAL-CRITIQUE.md` ([template](../templates/VISUAL-CRITIQUE.md)); `stop` means the
   remaining issues are reported to the user as open, never hidden.

## Rubric

Score each dimension 1–5 from what is visible in the screenshots. Every score needs evidence: the section, viewport
and what is seen. Scores describe the page, not the effort.

| Dimension | Weight | 1 | 3 | 5 |
|---|---|---|---|---|
| `hierarchy` | 0.18 | No focal point; everything competes | One focal point per viewport, some sections flat | Obvious reading order; each viewport has one clear focus and the primary action is findable in 2 s |
| `composition` | 0.16 | Same template block repeated; centered stacks everywhere | Layout varies by content in some sections | Composition follows content in every section; rhythm and whitespace are deliberate |
| `typography` | 0.14 | One size/weight contrast; long lines; cramped | Clear scale, readable measure | Display/body contrast, comfortable measure, typographic details (tabular numbers, labels) serve the content |
| `color_surfaces` | 0.12 | Off-brand gradients, glows, arbitrary shadows | Brand-consistent, some default surfaces | One coherent surface model; accent reserved for primary actions; depth by role |
| `distinctiveness` | 0.14 | Could be any AI-generated template | Some product-specific moments | Signature moves from the direction are visible and repeated; recognizably this product |
| `craft` | 0.12 | Misalignment, inconsistent spacing, broken states | Mostly aligned and consistent | Pixel-level alignment, consistent spacing scale, polished details and states |
| `responsiveness` | 0.08 | Overflow, clipped content, desktop layout squeezed | Works on mobile, composition unchanged | Mobile has its own intentional composition; no overflow; comfortable targets |
| `motion` | 0.06 | Motion distracts or is broken (stuck states) | Motion is harmless | Motion explains or rewards; reduced-motion capture is complete and still |

`motion` may be `null` when no motion is in scope; its weight is then redistributed.

## Pass criteria

| Ambition | Passes when |
|---|---|
| Elevate / Reimagine | weighted score ≥ 3.6; no dimension < 3; `distinctiveness` ≥ 3.5; no blocker; with a before critique, the weighted score improved by ≥ 0.75 and `hierarchy`, `composition` and `distinctiveness` did not drop |
| Refine | weighted score ≥ 3.0; no blocker; no dimension dropped by more than 0.5 against before |

Measured gates (applied by `score_visual_critique`, independent of the critic):

| Gate | Source | Severity |
|---|---|---|
| Content removed or route missing | `diff_ui_maps.content_preserved` | blocker |
| Horizontal overflow > 0 px | `layout_probe.horizontal_overflow_px` | blocker |
| axe violations | `accessibility_scan` scans | major (blocker when `impacts` lists critical/serious) |
| Elevate bar not met (sections not re-composed) | `diff_ui_maps.elevate_bar` | major (Elevate only) |
| New default-banlist signals | `diff_ui_maps` `banlist_introduced` | major |
| Reduced-motion capture still running infinite animations | `motion_probe` in `reduced_motion` captures | major |
| Interactive targets < 24 px on mobile (more than 3) | `layout_probe.small_targets` | major |
| Text < 12 px (more than 5 elements) | `layout_probe.small_text` | minor |
| No h1 or no primary action above the fold (desktop) | `layout_probe.above_fold` | minor |

## Critique JSON

```json
{
  "schema_version": 1,
  "subject": "after",
  "routes": ["/"],
  "scores": {
    "hierarchy": {"score": 4, "evidence": "desktop hero: headline and product view lead; primary CTA visible above fold"},
    "composition": {"score": 4, "evidence": "..."},
    "typography": {"score": 4, "evidence": "..."},
    "color_surfaces": {"score": 4, "evidence": "..."},
    "distinctiveness": {"score": 3, "evidence": "..."},
    "craft": {"score": 4, "evidence": "..."},
    "responsiveness": {"score": 4, "evidence": "..."},
    "motion": null
  },
  "issues": [
    {"severity": "major", "dimension": "distinctiveness", "where": "/ features, desktop",
     "observation": "bento right column tiles are mostly empty", "fix": "give the mid tiles a visual or merge them"}
  ],
  "signature_moves_seen": ["asymmetric-split", "hairline-system"],
  "content_concerns": []
}
```
