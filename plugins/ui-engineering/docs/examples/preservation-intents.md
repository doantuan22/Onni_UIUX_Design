# Preservation Intent Examples

The entries below are direct outputs of the structured parser tests, not implementation outcomes. They illustrate permission interpretation only.

| Corpus case | Parsed result | Safety implication |
|---|---|---|
| EN-07: “Modernize the landing page without changing its colors” | Palette preserved; redesign `NOT_AUTHORIZED` | Visual improvement does not imply permission to redesign or recolor |
| VI-02: “Thiết kế lại toàn bộ dashboard, có thể đổi màu và bố cục.” | Redesign explicitly allowed; palette and layout permissions are separate | Permission remains limited to the named dashboard target |
| TASK-09: “Standardize button variants across the app without a global redesign” | Global redesign prohibited | Component consistency work does not widen change scope |

Validated by `tests/test_reasoning_quality.py`; these are parser evaluations, not a user project execution.
