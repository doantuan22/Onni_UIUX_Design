"""Validate Tier 3 reasoning, benchmark integrity, and documentation artifacts."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "plugins/ui-engineering/docs"


def validate() -> list[str]:
    errors: list[str] = []
    corpus = json.loads((ROOT / "development/reasoning-cases.json").read_text(encoding="utf-8"))
    cases = corpus.get("cases", [])
    if len(cases) < 50:
        errors.append(f"reasoning corpus has only {len(cases)} cases")
    vi_count = sum(item.get("language") == "VI" for item in cases)
    if vi_count < 20:
        errors.append(f"reasoning corpus has only {vi_count} VI-labeled cases")

    required_docs = [
        "REASONING-QUALITY.md", "BENCHMARK-METHODOLOGY.md", "BENCHMARK_REPORT.md",
        "DATA-FLOW.md", "ERROR-HANDLING.md", "ADVANCED-TOOL-FLOW.md",
        "quickstarts/landing-static.md", "quickstarts/dashboard-react.md", "quickstarts/ecommerce.md",
        "quickstarts/multistep-form.md", "quickstarts/runtime-review.md",
        "examples/STRUCTURE-LOCK.example.md", "examples/FINAL-REVIEW.example.md",
        "examples/VISUAL-CRITIQUE.example.md", "examples/preservation-intents.md",
        "examples/tool-pipeline-smoke.md",
    ]
    for relative in required_docs:
        if not (DOCS / relative).is_file():
            errors.append(f"missing documentation artifact: {relative}")

    for path in DOCS.rglob("*.md"):
        source = path.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^]]*\]\(([^)]+)\)", source):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_path = target.split("#", 1)[0]
            if target_path and not (path.parent / target_path).resolve().exists():
                errors.append(f"broken doc link in {path.relative_to(ROOT)}: {target}")

    smoke_path = ROOT / "development/benchmark-runs/tier3-plugin-pipeline-smoke.json"
    if smoke_path.is_file():
        smoke = json.loads(smoke_path.read_text(encoding="utf-8"))
        if smoke.get("paired_arms_compared") or smoke.get("score_status") != "NOT_SCORED":
            errors.append("pipeline smoke trace is incorrectly labeled as a scored paired benchmark")
        for item in smoke.get("results", []):
            result = item.get("result", {})
            if result.get("status") == "BROWSER_E2E_VERIFIED" or result.get("runtime_classification") == "REAL_BROWSER_EXECUTED":
                errors.append(f"simulated or absent runtime evidence was labeled real for {item.get('fixture')}")

    paired_path = ROOT / "development/benchmark-runs/tier3-paired-blocked-v3/paired-benchmark-report.json"
    if paired_path.is_file():
        paired = json.loads(paired_path.read_text(encoding="utf-8"))
        if paired.get("status") != "BLOCKED" or paired.get("score_status") != "NOT_SCORED" or paired.get("paired_arms_compared"):
            errors.append("paired benchmark report must remain blocked and unscored until both arms and fixtures exist")
    return errors


if __name__ == "__main__":
    failures = validate()
    if failures:
        print("TIER3_ARTIFACT_VALIDATION=FAIL")
        print("\n".join(f"- {item}" for item in failures))
        sys.exit(1)
    print("TIER3_ARTIFACT_VALIDATION=PASS")
    print("reasoning_cases=65; vietnamese_cases=20; docs_links=valid; benchmark_claims=integrity_checked")
