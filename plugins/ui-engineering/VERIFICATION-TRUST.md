# Verification trust

Tier 2 adds evidence-aware classification above P4 while reusing the current runtime detector, evidence validators, `.evidence` storage, runtime critic, and repair routing.

## Capability ladder

| Level | Capability | Evidence and claim boundary |
|---|---|---|
| 0 | `SOURCE_DIFF` | P3 ledger, changed files, planned scope, and token baseline. Does not verify rendering. |
| 1 | `STATIC_STRUCTURE` | Readable source syntax, existing framework adapter checks, preservation comparison, and responsive source signals. Responsive signals do not prove rendered behavior. |
| 2 | `BUILD_VALIDATION` | Only detected project scripts (`build`, `typecheck`, `lint`, `test`) using the detected package manager. No invented command or auto-install. |
| 3 | `RUNTIME_DOM` | Existing Playwright runtime evidence for required routes and viewports. |
| 4 | `VISUAL_RENDER` | Existing screenshot evidence and an evidence-backed visual critic result when visual intent is required. |
| 5 | `INTERACTION_A11Y` | Passing task-relevant interaction and accessibility evidence. |

The strategy resolver selects available checks and records unavailable required checks. Missing browser capability enables degraded verification: available static/build checks still run and CHECK returns `PARTIAL` when required rendered checks remain unavailable.

## Execution and verification are separate

`execution_status` reports P3 implementation progress. `verification_status` is one of `NOT_RUN`, `PASS`, `PASS_WITH_WARNINGS`, `PARTIAL`, `FAIL`, or `BLOCKED`. A task is publicly `COMPLETED` only when its required verification is `PASS` or `PASS_WITH_WARNINGS`. Infrastructure absence is `PARTIAL`/`BLOCKED`, not a code `FAIL`.

## Trust levels

- `UNVERIFIED`: verification did not run, evidence is invalid/insufficient, or a blocking issue exists.
- `STATICALLY_VERIFIED`: source/diff and structure checks pass; detected configured build checks run; rendered UI remains unverified.
- `RUNTIME_VERIFIED`: required runtime evidence passes; visual or interaction proof is still missing if requested.
- `MULTIMODAL_VERIFIED`: all contract-required runtime, visual, interaction, accessibility, preservation, and evidence-sufficiency checks pass with provenance.

`trust_ceiling`/`maximum_trust_level` describe environment capability only. `trust_achieved`/`trust_level` describe a specific task and never automatically equal the ceiling.

## Provenance and limitations

Every `verified_claim` carries a claim type, evidence refs, verification level, source, status, and confidence. NO_FAKE_PASS rejects verified claims without evidence and PASS results missing evidence or required checks. Partial and blocked reports explain what was not checked. For example, source responsive classes can produce `STATIC_RESPONSIVE_SIGNAL`; they cannot produce a claim that mobile rendering works.

`doctor` is read-only. It reports the verification ladder and trust ceiling; it does not install Playwright, download browser binaries, or start the project. Use `FIX_ENVIRONMENT` only when stronger verification is required, then resume the same task with its `task_id`.
