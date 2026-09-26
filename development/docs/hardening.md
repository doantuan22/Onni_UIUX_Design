# Hardening layer

The hardening layer sits between routing and Phase execution. Its purpose is stable, economical decisions: Level 0 core context before phase/domain/deep context; artifact discovery and reuse before creation; active/locked version resolution before edits; impact analysis before important changes; and scope/phase guards before execution.

Artifacts use one active version per type and the precedence `LOCKED > ACTIVE > DRAFT > SUPERSEDED`. `VALIDATED`, `NEEDS_REVIEW`, `STALE`, and `INVALID` describe whether an artifact may be reused. A lock is immutable to Phase 2. Upstream change triggers impact analysis and marks affected downstream artifacts for review or stale rather than silently reusing them.

Reviews track delta and issue fingerprints. Three is the normal automatic iteration maximum; two consecutive no-progress iterations require strategy change or `BLOCKED`. A blocked record states reason, issue, phase, last valid artifact, rollback, and missing input/tool/decision. Completion needs gate evidence, scope coverage, valid artifacts, no blocker, and no unresolved major issue.

Small tasks use a fast path—scope, minimal artifact check, relevant rules, execute, targeted review. Large work is batched around active shared artifacts, summaries, open issues, and a cross-batch consistency review. See [workflow/execution-contract.md](../../plugins/ui-engineering/workflows/execution-contract.md), [reference-loading.md](../../plugins/ui-engineering/workflows/reference-loading.md), [change-impact.md](../../plugins/ui-engineering/workflows/change-impact.md), and [chunking-strategy.md](../../plugins/ui-engineering/workflows/chunking-strategy.md).
