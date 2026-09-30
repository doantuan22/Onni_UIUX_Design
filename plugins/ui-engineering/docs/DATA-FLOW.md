# Reasoning Data Flow

```mermaid
flowchart TD
    U[User request] --> P0[P0 repository and UI map]
    U --> P2[P2 semantic requirement parser]
    P0 --> P2
    P1[P1 knowledge plan and references] --> P2
    P2 --> G[Deterministic preservation and scope guards]
    P0 --> G
    G --> D[Diagnosis with evidence or UNKNOWN state]
    P1 --> S[Strategy and bounded recommendations]
    D --> S
    G --> S
    S --> M[Modification plan and execution chunks]
    M --> A[Host agent applies approved changes]
    A --> V[Validation handoff and runtime evidence]
    V --> R[Critic / completion gate]
```

The `SemanticRequirement` is an internal structured interpretation. Its evidence references point to the request or supplied project/knowledge records; they do not embed large source files. The plan exposes a short rationale and does not persist chain-of-thought. The active parser mode is `HEURISTIC_FALLBACK`; there is no provider call in core.

The deterministic preservation guard remains authoritative for L1/L2/L3, protected properties, and granular redesign/palette/layout authorization. An unknown target is not promoted to a project-wide target. The planning stage returns chunks for the host agent; the smoke harness did not apply those chunks or claim that it did.

Real local traces are stored in `development/benchmark-runs/tier3-plugin-pipeline-smoke.json`. They stop at runtime verification because browser capability is undeclared.
