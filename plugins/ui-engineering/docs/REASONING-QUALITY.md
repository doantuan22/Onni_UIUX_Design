# Reasoning Quality

## What the planner produces

P2 exposes a structured `SemanticRequirement` record before the existing scope, preservation, diagnosis, strategy, and plan stages. The record distinguishes explicit, inferred, and unknown fields; carries user request evidence references; and returns a short rationale plus `reasoning_context`. It does not store hidden chain-of-thought.

Fields include goal, task type, scope, target surfaces, requirements, constraints, preservation intent, redesign and granular palette/layout permissions, responsive/accessibility/interaction intent, framework constraints, `must_keep`/`must_change`/`must_not_change`, concerns, ambiguities, language, and confidence.

## Reasoning source and trust boundary

Current mode is always `HEURISTIC_FALLBACK`. The module uses normalized phrases and repository surface names. It does not call an LLM or claim model reasoning. `SEMANTIC` and `MODEL_ASSISTED` are reserved enum values, not active modes. Confidence describes cue coverage only; it is not a probability of correctness.

P0 route/component evidence grounds surface selection. P1 knowledge may supply references and bounded guidance. P2 interpretation cannot grant a permission that the deterministic preservation guard did not authorize. Unknown and ambiguous targets remain unknown; they must not be silently converted into global scope.

## Language and compound requests

The corpus contains 65 authored request cases, including 20 labeled Vietnamese and mixed-language examples. Accent folding includes Vietnamese `đ`. The evaluator checks structured properties rather than exact diagnosis prose. Compound requests retain independent concerns such as responsive behavior, consistency, interaction, accessibility, and preservation.

Run the corpus with:

```powershell
$env:PYTHONPATH = 'plugins/ui-engineering'
python -m unittest discover -s tests -p 'test_reasoning_quality.py'
```

Results on 2026-09-30: 7 tests pass, including all structured assertions across the 65 cases. This is heuristic parser coverage, not an LLM reasoning benchmark.

## Known boundaries

Phrase rules can miss paraphrases, sarcasm, domain shorthand, and complex negation. Accent-insensitive matching can conflate words. An inferred selected surface is not equivalent to an explicit target. The host agent must inspect P0/P1 artifacts and ask for missing information when scope remains ambiguous. See `development/reasoning-cases.json` and `tests/test_reasoning_quality.py` for the current evaluation set.
