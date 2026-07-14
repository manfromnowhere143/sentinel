#!/usr/bin/env python3
"""Iteration 123 verifier for the mission evidence/alignment audit."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

COMPLETE_VERDICT = "MISSION_EVIDENCE_ALIGNMENT_AUDIT_COMPLETE"
INFRA_NULL_VERDICT = "MISSION_EVIDENCE_ALIGNMENT_AUDIT_INFRA_NULL"
BOUNDARY_PHRASE = (
    "This audit authorizes no repair, actor-causality, threshold-value, transfer upgrade, "
    "safety, deployment, robustness, benchmark, population-rate, HD-Score-invariance, "
    "real-world behavior, first-responder behavior, acquisition-value, retuning, production, "
    "commercial claim, or claim that Sentinel matches or exceeds Tesla, Mobileye, SpaceX, "
    "Waymo, NVIDIA, or any current frontier autonomy stack."
)
AUDIT_NOTE_PATH = Path("docs/research/SENTINEL_MISSION_EVIDENCE_ALIGNMENT_AUDIT_2026-07-14.md")
README_PATH = Path("README.md")
FRONTIER_MEMORY_PATH = Path("docs/research/FRONTIER_ALIGNMENT_MEMORY_2026-07-13.md")
ITER122_RESULT_PATH = Path("experiments/iter122_support_core_taxonomy_documentation/RESULT.md")
SUPPORT_CORE_NOTE = "SUPPORT_CORE_TWO_TRACK_TAXONOMY_2026-07-14.md"
REQUIRED_SECTIONS = (
    "## Source Refresh",
    "## Defensible Strengths",
    "## Reviewer Attack Surface",
    "## Freshness Fixes",
    "## Next Bounded Actions",
    "## Claim Boundary",
)
SOURCE_ANCHORS = (
    "https://www.mobileye.com/blog/diagnosing-the-long-tail-how-mobileye-turns-edge-cases-into-targeted-training/",
    "https://www.mobileye.com/opinion/driving-the-long-tail/",
    "https://www.tesla.com/support/fsd/v14-trial",
    "https://arxiv.org/abs/2607.03755",
    "https://arxiv.org/abs/2606.06996",
    "https://arxiv.org/html/2607.10975v1",
    "https://arxiv.org/html/2607.04953v1",
)


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
        normalized_item = normalize(item)
        if normalized_item in normalized:
            continue
        if item == "current through iteration 122" and current_iteration_freshness_present(normalized):
            continue
        if item == "Later HUGSIM iterations 98-122" and later_hugsim_freshness_present(
            normalized
        ):
            continue
        missing.append(item)
    return missing


def current_iteration_freshness_present(normalized_text: str) -> bool:
    return "current through iteration" in normalized_text


def later_hugsim_freshness_present(normalized_text: str) -> bool:
    return "Later HUGSIM iterations 98-" in normalized_text


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
    memory_text, memory_problems = read_text(repo_root / FRONTIER_MEMORY_PATH)
    iter122_text, iter122_problems = read_text(repo_root / ITER122_RESULT_PATH)
    problems.extend(audit_problems)
    problems.extend(readme_problems)
    problems.extend(memory_problems)
    problems.extend(iter122_problems)

    if "Ninety-three registered iterations" in readme_text or "(93 registered iterations" in readme_text:
        problems.append("readme-stale-iteration-count-present")

    checks = [
        check("audit-note-sections", audit_text, REQUIRED_SECTIONS),
        check("audit-note-boundary", audit_text, [BOUNDARY_PHRASE]),
        check("audit-note-source-anchors", audit_text, SOURCE_ANCHORS),
        check(
            "audit-note-core-terms",
            audit_text,
            [
                "NeuroNCAP",
                "HUGSIM transfer null",
                "support-core taxonomy",
                "Reviewer Attack Surface",
                "Next Bounded Actions",
            ],
        ),
        check(
            "readme-freshness",
            readme_text,
            [
                "current through iteration 122",
                "iter122_support_core_taxonomy_documentation",
                "Later HUGSIM iterations 98-122",
            ],
        ),
        check(
            "frontier-memory-freshness",
            memory_text,
            [
                "Post-iteration-122 update",
                SUPPORT_CORE_NOTE,
                "iteration-84 recommendation as current",
            ],
        ),
        check("iter122-result-present", iter122_text, ["SUPPORT_CORE_TAXONOMY_DOCUMENTATION_COMPLETE"]),
    ]
    return {
        "iteration": 123,
        "inputs": {
            "audit_note": str(AUDIT_NOTE_PATH),
            "readme": str(README_PATH),
            "frontier_memory": str(FRONTIER_MEMORY_PATH),
            "iter122_result": str(ITER122_RESULT_PATH),
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
        "# Iteration 123 - mission evidence/alignment audit verifier",
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


def run_verifier(repo_root: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(repo_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter123_mission_evidence_alignment_audit/proof-audit/"
            "mission_evidence_alignment_audit_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter123_mission_evidence_alignment_audit/proof-audit/"
            "mission_evidence_alignment_audit.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_verifier(args.repo_root, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
