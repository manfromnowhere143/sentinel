#!/usr/bin/env python3
"""Iteration 131 verifier for the post-Iter130 mission alignment audit."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

COMPLETE_VERDICT = "POST_ITER130_MISSION_ALIGNMENT_AUDIT_COMPLETE"
INFRA_NULL_VERDICT = "POST_ITER130_MISSION_ALIGNMENT_AUDIT_INFRA_NULL"
ITER130_VERDICT = "SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_COMPLETE"
BOUNDARY_PHRASE = (
    "This audit authorizes no reserved path creation, generated scenario artifact, scenario "
    "generation, execution-slot selection, GPU launch, HUGSIM run, learning/update step, repair, "
    "actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, "
    "benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder "
    "behavior, acquisition-value, retuning, production, commercial claim, or claim that Sentinel "
    "matches or exceeds Tesla, Mobileye, SpaceX, Waymo, NVIDIA, or any current frontier "
    "autonomy stack."
)
AUDIT_NOTE_PATH = Path(
    "docs/research/SENTINEL_POST_ITER130_MISSION_ALIGNMENT_AUDIT_2026-07-14.md"
)
README_PATH = Path("README.md")
NEXT_PHASE_PATH = Path("docs/NEXT_PHASE.md")
CONTINUITY_PATH = Path("CONTINUITY.md")
HANDOFF_PATH = Path("HANDOFF.md")
FRONTIER_MEMORY_PATH = Path("docs/research/FRONTIER_ALIGNMENT_MEMORY_2026-07-13.md")
ITER130_RESULT_PATH = Path("experiments/iter130_support_core_artifact_schema_preflight/RESULT.md")
ITER130_REPORT_PATH = Path(
    "experiments/iter130_support_core_artifact_schema_preflight/proof-schema/"
    "support_core_artifact_schema_preflight_report.json"
)
ITER130_NOTE_PATH = Path(
    "docs/research/SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_2026-07-14.md"
)
REQUIRED_SECTIONS = (
    "## Source Refresh",
    "## Alignment Verdict",
    "## Claim Hierarchy",
    "## Defensible Strengths",
    "## Reviewer Attack Surface",
    "## Freshness Fixes",
    "## Accuracy Improvements",
    "## Claim Boundary",
)
SOURCE_ANCHORS = (
    "https://www.mobileye.com/blog/diagnosing-the-long-tail-how-mobileye-turns-edge-cases-into-targeted-training/",
    "https://www.mobileye.com/blog/adas-regulations-overview-what-every-automaker-needs-to-know/",
    "https://www.tesla.com/support/fsd/v14-trial",
    "https://arxiv.org/abs/2607.03755",
    "https://arxiv.org/abs/2606.06996",
)
DEFAULT_PROOF_DIR = Path("experiments/iter131_post_iter130_mission_alignment_audit/proof-audit")
DEFAULT_REPORT_PATH = DEFAULT_PROOF_DIR / "post_iter130_mission_alignment_audit_report.json"
DEFAULT_MARKDOWN_PATH = DEFAULT_PROOF_DIR / "post_iter130_mission_alignment_audit.md"
DEFAULT_COMMAND_PATH = DEFAULT_PROOF_DIR / "verify_post_iter130_mission_alignment_audit.command.txt"


def read_text(path: Path) -> tuple[str, list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return "", [f"missing-or-empty:{path}"]
    try:
        return path.read_text(), []
    except OSError as exc:
        return "", [f"read-failed:{path}:{exc}"]


def read_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-or-empty:{path}"]
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"read-json-failed:{path}:{exc}"]
    if not isinstance(data, dict):
        return {}, [f"json-not-dict:{path}"]
    return data, []


def normalize(text: str) -> str:
    return " ".join(text.split())


def missing_items(text: str, required: tuple[str, ...] | list[str]) -> list[str]:
    normalized = normalize(text)
    missing: list[str] = []
    for item in required:
        if normalize(item) not in normalized:
            missing.append(item)
    return missing


def check(label: str, text: str, required: tuple[str, ...] | list[str]) -> dict[str, Any]:
    missing = missing_items(text, required)
    return {"label": label, "required": list(required), "missing": missing, "passed": not missing}


def current_through_at_least(text: str, minimum_iteration: int) -> bool:
    matches = [int(value) for value in re.findall(r"current through iteration (\d+)", text)]
    return bool(matches) and max(matches) >= minimum_iteration


def check_readme_freshness(text: str) -> dict[str, Any]:
    missing: list[str] = []
    if not current_through_at_least(text, 130):
        missing.append("current through iteration 130 or newer")
    for item in (
        "iter130_support_core_artifact_schema_preflight",
        "SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_2026-07-14.md",
    ):
        if item not in text:
            missing.append(item)
    required = [
        "current through iteration 130 or newer",
        "iter130_support_core_artifact_schema_preflight",
        "SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_2026-07-14.md",
    ]
    return {"label": "readme-current-through-130", "required": required, "missing": missing, "passed": not missing}


def check_iter130_report(report: dict[str, Any]) -> dict[str, Any]:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    missing: list[str] = []
    expected = {
        "artifact_reservation_count": 10,
        "reserved_relative_path_count": 30,
        "schema_spec_count": 3,
        "schema_binding_count": 30,
        "true_authorization_count": 0,
        "existing_bound_path_count": 0,
        "duplicate_reserved_path_count": 0,
        "bad_schema_reference_count": 0,
        "forbidden_key_count": 0,
    }
    if report.get("verdict") != ITER130_VERDICT:
        missing.append(f"verdict={ITER130_VERDICT}")
    for key, value in expected.items():
        if summary.get(key) != value:
            missing.append(f"{key}={value}")
    return {
        "label": "iter130-report-counts",
        "required": [f"{key}={value}" for key, value in expected.items()],
        "missing": missing,
        "passed": not missing,
    }


def choose_verdict(problems: list[str], checks: list[dict[str, Any]]) -> str:
    if problems or any(not item["passed"] for item in checks):
        return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    problems: list[str] = []
    audit_text, audit_problems = read_text(repo_root / AUDIT_NOTE_PATH)
    readme_text, readme_problems = read_text(repo_root / README_PATH)
    next_phase_text, next_phase_problems = read_text(repo_root / NEXT_PHASE_PATH)
    continuity_text, continuity_problems = read_text(repo_root / CONTINUITY_PATH)
    handoff_text, handoff_problems = read_text(repo_root / HANDOFF_PATH)
    memory_text, memory_problems = read_text(repo_root / FRONTIER_MEMORY_PATH)
    iter130_result_text, iter130_result_problems = read_text(repo_root / ITER130_RESULT_PATH)
    iter130_report, iter130_report_problems = read_json(repo_root / ITER130_REPORT_PATH)
    iter130_note_text, iter130_note_problems = read_text(repo_root / ITER130_NOTE_PATH)
    problems.extend(audit_problems)
    problems.extend(readme_problems)
    problems.extend(next_phase_problems)
    problems.extend(continuity_problems)
    problems.extend(handoff_problems)
    problems.extend(memory_problems)
    problems.extend(iter130_result_problems)
    problems.extend(iter130_report_problems)
    problems.extend(iter130_note_problems)

    checks = [
        check("audit-note-sections", audit_text, REQUIRED_SECTIONS),
        check("audit-note-boundary", audit_text, [BOUNDARY_PHRASE]),
        check("audit-note-source-anchors", audit_text, SOURCE_ANCHORS),
        check(
            "audit-note-claim-hierarchy",
            audit_text,
            [
                "Proven empirical result",
                "Published nulls",
                "Mechanism evidence",
                "Design/preflight artifact",
                "Iterations 125-130 are design/preflight artifacts",
            ],
        ),
        check(
            "audit-note-improvement-lanes",
            audit_text,
            [
                "schema-instance creation preflight",
                "one-page claim ledger",
                "mission/rulebook boundary",
                "candidate generation, execution, analysis, and monitor update as separate hypotheses",
            ],
        ),
        check(
            "audit-note-frontier-niche",
            audit_text,
            [
                "runtime monitoring, failure localization",
                "safety evidence ledger around opaque planners",
                "not a full autonomy stack",
            ],
        ),
        check_readme_freshness(readme_text),
        check(
            "next-phase-post-130",
            next_phase_text,
            [
                "SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_2026-07-14.md",
                "schema-instance creation preflight",
                "iteration 130 freezes `3` artifact-type schemas",
            ],
        ),
        check(
            "continuity-post-130",
            continuity_text,
            [
                "SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_COMPLETE",
                "no reserved path creation",
                "no generated artifact",
            ],
        ),
        check(
            "handoff-post-130",
            handoff_text,
            [
                "Newest completed experiment: experiments/iter130_support_core_artifact_schema_preflight/RESULT.md",
                "GPU_RUN_STATE=IDLE_NO_DOCKER_CONTAINERS",
            ],
        ),
        check(
            "frontier-memory-post-130",
            memory_text,
            [
                "Post-iteration-130 update",
                "SUPPORT_CORE_SOURCE_POOL_MUTATION_PREFLIGHT_2026-07-14.md",
                "SUPPORT_CORE_ARTIFACT_NAMING_PREFLIGHT_2026-07-14.md",
                "SUPPORT_CORE_ARTIFACT_SCHEMA_PREFLIGHT_2026-07-14.md",
                "authorize no reserved path creation",
            ],
        ),
        check("iter130-result-present", iter130_result_text, [ITER130_VERDICT]),
        check_iter130_report(iter130_report),
        check(
            "iter130-note-boundary",
            iter130_note_text,
            [
                "authorizes no reserved path creation",
                "schema contracts",
                "Binding Counts",
            ],
        ),
    ]
    return {
        "iteration": 131,
        "inputs": {
            "audit_note": str(AUDIT_NOTE_PATH),
            "readme": str(README_PATH),
            "next_phase": str(NEXT_PHASE_PATH),
            "continuity": str(CONTINUITY_PATH),
            "handoff": str(HANDOFF_PATH),
            "frontier_memory": str(FRONTIER_MEMORY_PATH),
            "iter130_result": str(ITER130_RESULT_PATH),
            "iter130_report": str(ITER130_REPORT_PATH),
            "iter130_note": str(ITER130_NOTE_PATH),
        },
        "summary": {
            "check_count": len(checks),
            "passed_check_count": sum(item["passed"] for item in checks),
            "problem_count": len(problems),
            "source_anchor_count": len(SOURCE_ANCHORS),
        },
        "checks": checks,
        "problems": problems,
        "verdict": choose_verdict(problems, checks),
        "claim_boundary": BOUNDARY_PHRASE,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 131 - post-Iter130 mission alignment audit verifier",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Checks", ""])
    for item in report["checks"]:
        lines.append(f"- `{item['label']}`: `{'pass' if item['passed'] else 'fail'}`")
        if item["missing"]:
            lines.append(f"  - missing: `{item['missing']}`")
    if report["problems"]:
        lines.extend(["", "## Problems", ""])
        lines.extend(f"- `{problem}`" for problem in report["problems"])
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def write_command(path: Path) -> None:
    command = (
        "python3 experiments/iter131_post_iter130_mission_alignment_audit/"
        "verify_post_iter130_mission_alignment_audit.py\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(command)


def run_verifier(repo_root: Path, out: Path, markdown_out: Path, command_out: Path) -> dict[str, Any]:
    report = build_report(repo_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    write_command(command_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, default=DEFAULT_REPORT_PATH)
    parser.add_argument("--markdown-out", type=Path, default=DEFAULT_MARKDOWN_PATH)
    parser.add_argument("--command-out", type=Path, default=DEFAULT_COMMAND_PATH)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_verifier(args.repo_root, args.out, args.markdown_out, args.command_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
