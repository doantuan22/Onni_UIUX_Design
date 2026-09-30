"""Reproducible paired-arm UI benchmark runner.

Arm commands are supplied explicitly as JSON argv arrays. This runner never
pretends an API/unit-test pipeline is an AI baseline or generated implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _tree_files(root: Path) -> dict[str, str]:
    files: dict[str, str] = {}
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if any(part in {".git", "node_modules", ".next", "dist", "build", "__pycache__"} for part in path.parts):
            continue
        files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return files


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for name, file_hash in sorted(_tree_files(root).items()):
        digest.update(name.encode("utf-8"))
        digest.update(file_hash.encode("ascii"))
    return digest.hexdigest()


def _changed_files(before: dict[str, str], after: dict[str, str]) -> list[str]:
    return sorted(name for name in set(before) | set(after) if before.get(name) != after.get(name))


def run_paired_benchmark(manifest_path: Path, output_dir: Path, baseline_argv: list[str] | None,
                         plugin_argv: list[str] | None, *, repetitions: int | None = None) -> dict[str, Any]:
    manifest_path = manifest_path.resolve()
    repo_root = manifest_path.parents[1]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    arm_commands = {"baseline": baseline_argv, "plugin": plugin_argv}
    repeats = repetitions or int(manifest["pairing_contract"].get("repetitions_per_arm", 1))
    report: dict[str, Any] = {
        "schema_version": 1,
        "benchmark_id": manifest.get("benchmark_id"),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "RUNNING",
        "score_status": "NOT_SCORED",
        "paired_arms_compared": False,
        "contract": manifest.get("pairing_contract", {}),
        "results": [],
    }

    for case in manifest.get("cases", []):
        fixture_value = case.get("fixture")
        fixture = (repo_root / fixture_value).resolve() if fixture_value else None
        fixture_exists = bool(fixture and fixture.is_dir() and repo_root in fixture.parents)
        if not fixture_exists:
            report["results"].append({"case_id": case["id"], "status": "BLOCKED_MISSING_FIXTURE",
                                       "archetype": case.get("archetype"), "framework": case.get("framework"),
                                       "detail": "A complete fixture directory for this case is unavailable."})
            continue

        initial_files = _tree_files(fixture)
        initial_hash = _tree_digest(fixture)
        case_result: dict[str, Any] = {"case_id": case["id"], "status": "RUNNING", "fixture": fixture_value,
            "request": case["request"], "initial_fixture_sha256": initial_hash, "arms": {}}
        for arm_name in ("baseline", "plugin"):
            command = arm_commands[arm_name]
            if not command:
                case_result["arms"][arm_name] = {"status": "BLOCKED_NO_ARM_COMMAND"}
                continue
            for repetition in range(1, repeats + 1):
                workspace = output_dir / "workspaces" / case["id"] / arm_name / f"run-{repetition}"
                if workspace.exists():
                    raise FileExistsError(f"Benchmark workspace already exists; choose a fresh --output path: {workspace}")
                workspace.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(fixture, workspace)
                copied_hash = _tree_digest(workspace)
                if copied_hash != initial_hash:
                    raise RuntimeError(f"Fixture copy hash mismatch for {case['id']} {arm_name} run {repetition}")
                argv = [part.replace("{workspace}", str(workspace)).replace("{request}", case["request"])
                        for part in command]
                try:
                    result = subprocess.run(argv, cwd=workspace, capture_output=True, text=True,
                        timeout=int(manifest["pairing_contract"].get("same_time_budget_seconds", 1800)), check=False)
                    run_status = "COMPLETED" if result.returncode == 0 else "FAILED"
                    stdout, stderr, returncode = result.stdout, result.stderr, result.returncode
                except subprocess.TimeoutExpired as exc:
                    run_status, stdout, stderr, returncode = "TIMEOUT", exc.stdout or "", exc.stderr or "", None
                run_dir = output_dir / "runs" / case["id"] / arm_name / f"run-{repetition}"
                run_dir.mkdir(parents=True, exist_ok=True)
                (run_dir / "stdout.txt").write_text(stdout, encoding="utf-8")
                (run_dir / "stderr.txt").write_text(stderr, encoding="utf-8")
                (run_dir / "command.json").write_text(json.dumps(argv, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                arm = case_result["arms"].setdefault(arm_name, {"runs": []})
                final_files = _tree_files(workspace)
                arm["runs"].append({"repetition": repetition, "status": run_status, "returncode": returncode,
                    "initial_fixture_sha256": copied_hash, "final_workspace_sha256": _tree_digest(workspace),
                    "changed_files": _changed_files(initial_files, final_files), "artifact_dir": str(run_dir)})
        baseline = case_result["arms"].get("baseline", {}).get("runs", [])
        plugin = case_result["arms"].get("plugin", {}).get("runs", [])
        if baseline and plugin and all(x["status"] == "COMPLETED" for x in baseline + plugin):
            case_result["status"] = "READY_FOR_BLIND_REVIEW"
        else:
            case_result["status"] = "BLOCKED_INCOMPLETE_ARMS"
        report["results"].append(case_result)

    complete = bool(report["results"]) and all(item["status"] == "READY_FOR_BLIND_REVIEW" for item in report["results"])
    report["paired_arms_compared"] = complete
    report["status"] = "READY_FOR_BLIND_REVIEW" if complete else "BLOCKED"
    report["score_status"] = "AWAITING_BLIND_REVIEW" if complete else "NOT_SCORED"
    report_path = output_dir / "paired-benchmark-report.json"
    report["report_path"] = str(report_path)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _argv(value: str | None) -> list[str] | None:
    if value is None:
        return None
    decoded = json.loads(value)
    if not isinstance(decoded, list) or not decoded or not all(isinstance(part, str) for part in decoded):
        raise ValueError("Each arm command must be a non-empty JSON array of strings.")
    return decoded


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("tier3-benchmark-manifest.json"))
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("benchmark-runs") / "paired")
    parser.add_argument("--baseline-command-json", help='argv JSON; supports {workspace} and {request}')
    parser.add_argument("--plugin-command-json", help='argv JSON; supports {workspace} and {request}')
    parser.add_argument("--repetitions", type=int)
    args = parser.parse_args(argv)
    report = run_paired_benchmark(args.manifest, args.output, _argv(args.baseline_command_json),
        _argv(args.plugin_command_json), repetitions=args.repetitions)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report["status"] == "READY_FOR_BLIND_REVIEW" else 2


if __name__ == "__main__":
    sys.exit(main())
