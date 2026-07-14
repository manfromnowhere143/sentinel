#!/usr/bin/env python3
"""Iteration 127 verifier for the post-Iter126 mission alignment audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

COMPLETE_VERDICT = "POST_ITER126_MISSION_ALIGNMENT_AUDIT_COMPLETE"
INFRA_NULL_VERDICT = "POST_ITER126_MISSION_ALIGNMENT_AUDIT_INFRA_NULL"
ITER126_VERDICT = "SUPPORT_CORE_CANDIDATE_MANIFEST_PREFLIGHT_COMPLETE"
BOUNDARY_PHRASE = (
    "This audit authorizes no scenario-generation execution, GPU launch, HUGSIM run, repair, "
    "actor-causality, threshold-value, transfer upgrade, safety, deployment, robustness, "
    "benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder "
    "behavior, acquisition-value, retuning, production, commercial claim, or claim that Sentinel "
    "matches or exceeds Tesla, Mobileye, SpaceX, Waymo, NVIDIA, or any current frontier "
    "autonomy stack."
)
AUDIT_NOTE_PATH = Path("docs/research/SENTINEL_POST_ITER126_MISSION_ALIGNMENT_AUDIT_2026-07-14.md")
README_PATH = Path("README.md")
NEXT_PHASE_PATH = Path("docs/NEXT_PHASE.md")
FRONTIER_MEMORY_PATH = Path("docs/research/FRONTIER_ALIGNMENT_MEMORY_2026-07-13.md")
ITER126_RESULT_PATH = Path(
    "experiments/iter126_support_core_candidate_manifest_preflight/RESULT.md"
)
MANIFEST_NOTE_PATH = Path(
    "docs/research/SUPPORT_CORE_CANDIDATE_GENERATION_MANIFEST_2026-07-14.md"
)
REQUIRED_SECTIONS = (
    "## Source Refresh",
    "## Alignment Verdict",
    "## Defensible Strengths",
    "## Reviewer Attack Surface",
    "## Freshness Fixes",
    "## Next Bounded Actions",
    "## Claim Boundary",
)
SOURCE_ANCHORS = (
    "https://www.mobileye.com/blog/diagnosing-the-long-tail-how-mobileye-turns-edge-cases-into-targeted-training/",
    "https://www.mobileye.com/blog/adas-regulations-overview-what-every-automaker-needs-to-know/",
    "https://www.tesla.com/support/fsd/v14-trial",
    "https://arxiv.org/abs/2607.03755",
    "https://arxiv.org/abs/2606.06996",
)
DEFAULT_PROOF_DIR = Path("experiments/iter127_post_iter126_mission_alignment_audit/proof-audit")
DEFAULT_REPORT_PATH = DEFAULT_PROOF_DIR / "post_iter126_mission_alignment_audit_report.json"
DEFAULT_MARKDOWN_PATH = DEFAULT_PROOF_DIR / "post_iter126_mission_alignment_audit.md"
DEFAULT_COMMAND_PATH = DEFAULT_PROOF_DIR / "verify_post_iter126_mission_alignment_audit.command.txt"


def read_text(path: Path) -> tuple[str, list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return "", [f"missing-or-empty:{path}"]
    try:
        return path.read_text(), []
    except OSError as exc:
        return "", [f"read-failed:{path}:{exc}"]


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
    memory_text, memory_problems = read_text(repo_root / FRONTIER_MEMORY_PATH)
    iter126_text, iter126_problems = read_text(repo_root / ITER126_RESULT_PATH)
    manifest_note_text, manifest_note_problems = read_text(repo_root / MANIFEST_NOTE_PATH)
    problems.extend(audit_problems)
    problems.extend(readme_problems)
    problems.extend(next_phase_problems)
    problems.extend(memory_problems)
    problems.extend(iter126_problems)
    problems.extend(manifest_note_problems)

    checks = [
        check("audit-note-sections", audit_text, REQUIRED_SECTIONS),
        check("audit-note-boundary", audit_text, [BOUNDARY_PHRASE]),
        check("audit-note-source-anchors", audit_text, SOURCE_ANCHORS),
        check(
            "audit-note-core-terms",
            audit_text,
            [
                "iteration 126",
                "candidate-generation manifest",
                "design/preflight",
                "empirical results",
                "Reviewer Attack Surface",
                "Next Bounded Actions",
            ],
        ),
        check(
            "readme-current-through-126",
            readme_text,
            ["current through iteration 126", "iter126_support_core_candidate_manifest_preflight"],
        ),
        check(
            "next-phase-current-through-126",
            next_phase_text,
            [
                "SUPPORT_CORE_CANDIDATE_GENERATION_MANIFEST_2026-07-14.md",
                "iteration 126",
                "fresh preflight for candidate-source-pool",
            ],
        ),
        check(
            "frontier-memory-post-126",
            memory_text,
            [
                "Post-iteration-126 update",
                "SUPPORT_CORE_CANDIDATE_GENERATION_MANIFEST_2026-07-14.md",
                "Do not treat iteration 122 as the current endpoint",
            ],
        ),
        check("iter126-result-present", iter126_text, [ITER126_VERDICT]),
        check(
            "manifest-note-boundary",
            manifest_note_text,
            ["authorizes no scenario generation", "execution=false", "hugsim_run=false"],
        ),
    ]
    return {
        "iteration": 127,
        "inputs": {
            "audit_note": str(AUDIT_NOTE_PATH),
            "readme": str(README_PATH),
            "next_phase": str(NEXT_PHASE_PATH),
            "frontier_memory": str(FRONTIER_MEMORY_PATH),
            "iter126_result": str(ITER126_RESULT_PATH),
            "manifest_note": str(MANIFEST_NOTE_PATH),
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
        "# Iteration 127 - post-Iter126 mission alignment audit verifier",
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
        "python3 experiments/iter127_post_iter126_mission_alignment_audit/"
        "verify_post_iter126_mission_alignment_audit.py\n"
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
