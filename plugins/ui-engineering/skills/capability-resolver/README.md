# Design Capability Resolver

Turns a requirement into **ranked design capabilities** (style, layout, screen, motion, interaction, effect, technology, composition anchor) with explicit **WHY** and **WHY NOT** for each choice. It is the reasoning bridge between intent and the [Design Knowledge System](../../knowledge/domains/README.md), and it is what keeps agents from defaulting to one look.

It runs inside Design Intelligence (Phase 2 step 3), after Design Direction and before Design Inspiration's pattern selection. It never changes the Structure Lock: screens and content come *from* the locked artifacts.

```text
User intent → product/domain → brand attributes (+ avoided attributes) → visual intensity → interaction intensity
→ information density → contexts, screens, content → style candidates → layout candidates → screen patterns
→ motion candidates → interaction candidates → effect candidates → technology selection → composition anchor
```

## How to run it

1. Write the **profile** from the pre-design declaration ([anti-homogenization](../../knowledge/domains/composition/anti-homogenization.md)), locked page types, and content inventory. The profile fields and vocabularies are in [resolver.md](resolver.md#profile).
2. Run the deterministic resolver when Python is available:
   ```bash
   python scripts/resolve_capabilities.py --profile profile.json --format md
   ```
   Without Python, apply the same rules by hand from [resolver.md](resolver.md). The script is the reference implementation of those rules, not a replacement for judgment.
3. Record the result in [CAPABILITY-PLAN.md](../../templates/CAPABILITY-PLAN.md) and review it. Override any choice with a written reason. Overrides are expected when the resolver lacks context (brand guidelines, existing system).
4. Load **only** the files listed under *Retrieval* in the plan ([retrieval.md](../../knowledge/domains/retrieval.md)).

## What it guarantees

| Guarantee | Mechanism |
|---|---|
| Choices follow product signals, not trends | Scores from domain, brand attributes, intensity; penalties for avoided and conflicting attributes |
| No default look | Default-tell penalty; at most one default-tell item per composition unless explicitly requested |
| Content-honest layouts | Layouts requiring missing content (product media, code, data) are rejected |
| Controlled motion | Tier gating by intensity, context and the style's motion ceiling; one HIGH motion region |
| Controlled effects | Point budget by visual intensity; one signature effect; the primary style's avoid list is enforced |
| Simplest technology | Existing dependency, then native platform, then an authorized library; otherwise the capability degrades |
| Explainability | Every selection carries reasons; runners-up and rejections carry why-not reasons |

## Limits

The resolver ranks catalog knowledge; it does not see the brand's visual assets, user research or competitors. Treat its output as a strong, explainable default, and record overrides. Scenario tests in `evals/resolver-scenarios/` pin its behavior (`python tests/test_knowledge.py`).
