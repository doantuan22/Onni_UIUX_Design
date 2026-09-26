# Design Knowledge System — developer guide

## What it is

A structured knowledge base plus reasoning tools that give a coding agent a large, explainable design vocabulary. The agent does not just follow a workflow; it knows which styles, layouts, screens, motions, interactions, effects and technologies exist, when each fits, what it costs, and how to combine them into one design language. It must also be able to say **why this** and **why not the alternative** for every choice.

```text
USER REQUIREMENT
  → intent analysis (pre-design declaration)            phase-2/knowledge/composition/anti-homogenization.md
  → Capability Resolver                                  phase-2/capability-resolver/, scripts/resolve_capabilities.py
  → style / layout / screen intelligence                 knowledge/styles, web-patterns, knowledge/screens
  → typography / design system                           phase-2/typography, 03-design-system
  → motion / interaction / effect intelligence           phase-2/motion, knowledge/interactions, knowledge/effects
  → composition intelligence                             knowledge/composition (recipes, premium model)
  → technology resolver + performance budget             05-frontend-implementation
  → implementation
  → runtime evidence                                     scripts/run_browser_execution.py (motion_probe, reduced_motion)
  → visual / motion / interaction evaluation             evals/quality (E65–E80), scripts/analyze_design_quality.py
  → refinement
```

## Modules

| Module | Kind | Where |
|---|---|---|
| Style Intelligence | `style` | `phase-2/knowledge/styles/*.md` |
| Layout Intelligence | `layout` | `phase-2/web-patterns/{hero,grid,storytelling,application}/*.md` |
| Screen Pattern Intelligence | `screen` | `phase-2/knowledge/screens/*.md` |
| Component Intelligence | prose grammars | `phase-2/visual-language/components/` |
| Motion Intelligence | `motion` (tiers primitive, M1–M5) | `phase-2/motion/*.md` + grammar in `motion-principles.md` |
| Interaction Intelligence | `interaction` | `phase-2/knowledge/interactions/*.md` |
| Visual Effect Intelligence | `effect` | `phase-2/knowledge/effects/*.md` |
| Advanced graphics | `graphics` + `technology` | `phase-2/knowledge/graphics/techniques.md`, `05-frontend-implementation/technology-resolver.md` |
| Composition Intelligence | `recipe` + guidance | `phase-2/knowledge/composition/` |
| Capability Resolver | reasoning | `phase-2/capability-resolver/`, `scripts/resolve_capabilities.py` |
| Implementation Intelligence | reasoning | `technology-resolver.md`, `performance-budget.md`, `scripts/detect_capabilities.py` (`design_runtime`) |
| Evaluation | evals + tools | `evals/quality/`, `evals/scenarios/E65–E80`, `scripts/analyze_design_quality.py`, runner probes |

## Schemas and validation

Entries are fenced `yaml` blocks whose first key is `id`. Schemas, vocabularies and format rules: [phase-2/knowledge/schema.md](../../plugins/ui-engineering/knowledge/domains/schema.md). Tools:

```bash
python scripts/knowledge_lib.py check     # parse, schema, vocabularies, references, index freshness
python scripts/knowledge_lib.py index     # regenerate phase-2/knowledge/INDEX.md after edits
python tests/test_knowledge.py            # parser, coverage, PyYAML parity (if installed), resolver scenarios, diversity
python tests/test_quality_analyzer.py     # analyzer fixtures and runtime-probe merging
python scripts/validate_skill.py          # whole-skill validation (includes the knowledge check)
python -m unittest discover -s tests       # full test suite (any working directory: add -t <root>/tests)
```

## Retrieval

Agents never scan catalogs. The resolver's plan lists the only files to load; [INDEX.md](../../plugins/ui-engineering/knowledge/domains/INDEX.md) maps ids to files; entries are read by id. Category gating by task is in [retrieval.md](../../plugins/ui-engineering/knowledge/domains/retrieval.md).

## Capability resolver

Profile → style ranking (domain, conveyed attributes, avoided and conflicting attributes, intensity, default-tell penalty) → layouts (content, density, motion cost, compatibility) → motion (tier gating, one HIGH) → interactions → effects (budget, one signature) → technology (installed → native → authorized library → native fallback → degrade) → recipe anchor → retrieval list. Rules: [resolver.md](../../plugins/ui-engineering/skills/capability-resolver/resolver.md).

## Extending the system

Always: add the entry, run `knowledge_lib.py index`, run the tests, and reference it from at least one style, layout, screen or recipe so the resolver can reach it.

### Add a style

1. Pick the family file in `phase-2/knowledge/styles/` (or add one and list it in `styles/README.md`).
2. Fill every `style` field. Machine fields decide ranking: `domains`, `conveys`, `perceived_risks`, `intensity`, `contexts`, `density`, `motion_ceiling`, `default_tell`.
3. Reference only existing effects, motion, layouts and styles. Add the new style to at least one other style's `compatible_styles` and to relevant layouts' `compatible_styles`.
4. Add or adjust a resolver scenario if the style should win for a product type, then run the diversity tests.

### Add a layout pattern

Add a `layout` entry in the right `web-patterns/` file with honest `content_requirements` (the resolver rejects layouts whose content does not exist), `motion_cost`, `compatible_styles`, `compatible_motion` and `interactions`.

### Add a motion pattern

Add a `motion` entry in the tier file (M1 micro, M2 component, M3 layout, M4 scroll/text, M5 cinematic). `serves` must use the purpose vocabulary; include `reduced_motion`, `responsive`, `interruption`, `performance.cost` and `technology`. M5 entries must have a static fallback.

### Add an effect

Add an `effect` entry with `visual_purpose`, `performance.cost`, accessibility and fallback rules. Mark `default_tell: true` if generated UIs overuse it. Reference it from the styles that recommend or avoid it.

### Add an interaction

Add an `interaction` entry with the full `flow` (input → feedback → state → motion → result), all three `input_methods`, and `min_interaction_intensity`.

### Add a recipe

Add a `recipe` entry in `composition/recipes.md` combining existing ids, with `avoid` and `why`. Recipes are anchors: keep them coherent (one style family, matching intensities, one signature).

### Add a technology

Add a `technology` entry with `packages` (used by `detect_capabilities.py` to detect reuse), `requires_dependency`, `when_to_use`, `when_not_to_use`, fallback and lifecycle.

### Add a vocabulary term

Edit the sets in `scripts/knowledge_lib.py` (`DOMAINS`, `ATTRIBUTES`, `CONTENT`, …) only when an entry or profile genuinely needs it. Update [schema.md](../../plugins/ui-engineering/knowledge/domains/schema.md) and, for attributes, consider `CONFLICTS` in the resolver.

### Add an eval

Behavioral evals: copy an existing scenario's frontmatter (see [evals/README.md](../../plugins/ui-engineering/evals/README.md)). Design-quality evals: add a scenario with Purpose, Input, Evidence, Heuristics, Pass/fail, Limitations and False positives sections; if it has a deterministic signal, extend `analyze_design_quality.py` and add a fixture assertion in `test_quality_analyzer.py`. Update the ID range in `scripts/validate_skill.py` and the suites in `evals/framework.md`.

## Guarantees and non-goals

- No runtime dependency on external websites; no bundled fonts or media; no automatic dependency or browser installation.
- The resolver produces explainable defaults. It does not replace brand guidelines, research or an existing coherent design system (`KEEP` wins).
- Evaluation separates deterministic signals from judgment (`NEEDS_REVIEW`) and runtime-only evidence (`NEEDS_RUNTIME`).
