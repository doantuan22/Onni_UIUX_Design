# Evaluation framework

Evals test skill behavior—not visual taste or model ranking. They are agent-agnostic and evaluate routing, context efficiency, artifact lifecycle, phase boundaries, lock compliance, business safety, review/loop behavior, traceability, and completion correctness.

Run manually by giving an agent one scenario plus its fixture, then record a result with [result-template.md](result-template.md). Use `SMOKE` after small routing/contract changes, `CORE` for workflow behavior, `EXECUTION` for E21–E28 after execution-layer changes, and `FULL` before broader releases. Run `python scripts/validate_skill.py` to validate scenario metadata, links, IDs, and repository contracts; it is not an agent-performance runner.

To add a scenario, copy the required YAML-shaped fields in an existing scenario, assign a unique `E##` ID, name its fixture, expected route/context/artifacts, forbidden behavior, and observable success/failure conditions. Record `agent`, `model`, and `version` only as result metadata, not a leaderboard.

Design quality evals E65–E80 judge the rendered outcome rather than agent behavior; see [quality/README.md](quality/README.md). Resolver behavior is pinned by the profiles in `resolver-scenarios/` and `python tests/test_knowledge.py` (schema, references, retrieval, scenario expectations, diversity). The benchmark preparation is in [docs/benchmark-protocol.md](../../../development/docs/benchmark-protocol.md).
