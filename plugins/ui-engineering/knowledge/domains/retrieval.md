# Knowledge retrieval

The knowledge base is large on purpose; context use must stay small. **Never read a catalog folder end to end.**

```text
Requirement → Capability Resolver → selected categories → candidate entries → compatibility ranking → composition
```

## Procedure

1. **Declare** the profile (pre-design declaration) from the Design Direction and locked artifacts.
2. **Resolve**: run `scripts/resolve_capabilities.py` (or apply [resolver rules](../../skills/capability-resolver/resolver.md) by hand). The plan's *Retrieval* list names the only catalog files to load.
3. **Load entries, not files, when possible**: find `id: <id>` in the listed file and read that block. [INDEX.md](INDEX.md) maps ids to files; read only the index section for the kind you need.
4. **Load guidance modules by trigger** (Phase 2 router): motion grammar when motion is in scope, performance budget before implementation, accessibility contract for any advanced item.
5. **Expand only on evidence**: if review finds a gap (e.g., a missing interaction), retrieve that one entry. Do not reload categories.

## Category gating by task

| Task | Load | Do not load |
|---|---|---|
| Enterprise dashboard / admin | data-dense/enterprise styles, application layouts, requested screens, M1–M3 motion, productivity interactions, low-cost effects | M4/M5 motion, cinematic/hero layouts, graphics techniques, expressive styles |
| Marketing / landing page | resolved styles, hero + storytelling/grid layouts, M1–M4 (M5 only at visual intensity ≥ 4), resolved effects, recipe anchor | application layouts, screens (unless product UI screens are shown) |
| Editorial / content | editorial styles, editorial grids, text motion, reading-related interactions | M5, particles/shaders, application shells |
| Small component or form | the component grammar, M1 micro motion, relevant interaction entries | styles catalog, layouts, recipes, effects beyond the component |
| Motion-only task | motion grammar, the specific tier file, responsive + reduced motion, performance safety | styles, layouts, recipes |
| Reference-inspired redesign | reference extraction → map observations to catalog ids → retrieve only those entries | full catalogs |

## Verification

`tests/test_knowledge.py` asserts that the resolver's retrieval list for an enterprise dashboard contains no cinematic, scroll or graphics files, and that every retrieval list contains only existing files.
