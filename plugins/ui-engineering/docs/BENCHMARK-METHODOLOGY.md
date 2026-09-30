# Benchmark Methodology

## Intended comparison

The paired benchmark compares two AI runs: (A) the same agent without UI/UX plugin context and (B) the agent with this plugin. Each case uses the same request, starter fixture, initial file hash, environment, permissions, and time budget. The manifest requests three repetitions per arm. Two reviewers should review outputs blind to arm before any quality score is reported.

The runner in `development/paired_benchmark.py` accepts explicit command argv arrays. Each arm receives its own copy of the starter fixture. It records the input hash, final hash, command, stdout/stderr, changed file inventory, exit state, and run directory. Use `{workspace}` and `{request}` placeholders in argv. Commands are never inferred or silently launched.

Example invocation after providing approved agent commands:

```powershell
python development/paired_benchmark.py `
  --manifest development/tier3-benchmark-manifest.json `
  --baseline-command-json '["agent-cli","run","--prompt","{request}","--cwd","{workspace}"]' `
  --plugin-command-json '["agent-cli","run","--prompt","{request}","--plugin","ui-engineering","--cwd","{workspace}"]' `
  --output development/benchmark-runs/paired-run-001
```

The example command line is an interface illustration; it has not been executed and is not benchmark evidence. Configure the actual agent executable and plugin context explicitly before a scored run.

## Dimensions

Review requirement coverage, preservation, scope control, responsive quality, accessibility, interaction quality, visual consistency, and regression count. Report each dimension and reviewer disagreement separately. Do not collapse results into a single score without a predeclared weighting rule. Keep per-case/per-repetition results and report variance.

## Blocking and integrity rules

The runner reports `BLOCKED_MISSING_FIXTURE`, `BLOCKED_NO_ARM_COMMAND`, `BLOCKED_INCOMPLETE_ARMS`, and `TIMEOUT` explicitly. It only marks a pair ready for blind review after both arms complete all configured repetitions. `READY_FOR_BLIND_REVIEW` is not a quality pass. Static pipeline smoke runs and unit tests are not baseline AI runs. No scores are published while fixtures, arms, or blind review are missing.

Current fixture inventory and the actual blocked run are documented in `BENCHMARK_REPORT.md` and `../../../development/benchmark-runs/tier3-paired-blocked-v3/paired-benchmark-report.json`.
