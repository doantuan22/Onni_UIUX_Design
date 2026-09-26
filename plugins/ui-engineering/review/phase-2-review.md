# Phase 2 review loop

Run after rendered output is available:

```text
Implement → self review → browser review → responsive review → accessibility review
→ classify → fix → review again
```

Use `PHASE-2-REVIEW.md`, `VISUAL-REVIEW.md`, and `ACCESSIBILITY-REVIEW.md` as applicable. Check Design Direction/System/Tokens, component and implementation mapping, selected viewports, required states, Page Spec compliance, and Structure Lock compliance. Classify visual findings as `BLOCKER`, `MAJOR`, `MINOR`, or `POLISH`.

Run at most three automatic visual-refinement iterations. A non-structural failure returns to `PHASE_2`; a structural/business/semantic mismatch is a blocker, requires a rollback request, and returns to `PHASE_1`. A pass requires no unresolved blocker and authorizes the final quality gate.

When inspiration, typography or motion were in scope, the review also applies the added [craft review](../skills/visual-language/craft-review.md) lenses and the codes in [typography-review](../skills/typography/typography-review.md) and [motion-review](../knowledge/motion/motion-review.md).
