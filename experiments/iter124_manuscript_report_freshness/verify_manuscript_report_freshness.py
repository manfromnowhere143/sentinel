#!/usr/bin/env python3
"""Iteration 124 verifier for report/manuscript freshness."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

COMPLETE_VERDICT = "MANUSCRIPT_REPORT_FRESHNESS_COMPLETE"
INFRA_NULL_VERDICT = "MANUSCRIPT_REPORT_FRESHNESS_INFRA_NULL"
BOUNDARY_PHRASE = (
    "descriptive support-core taxonomy only; no repair, actor-causality, threshold-value, "
    "transfer upgrade, safety, deployment, robustness, benchmark, population-rate, "
    "HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, "
    "retuning, production, commercial claim, or frontier-stack-equivalence claim"
)
REPORT_PATH = Path("docs/REPORT.md")
MANUSCRIPT_PATH = Path("docs/paper/MANUSCRIPT.md")
SUPPORT_CORE_NOTE = "SUPPORT_CORE_TWO_TRACK_TAXONOMY_2026-07-14.md"
AUDIT_NOTE = "SENTINEL_MISSION_EVIDENCE_ALIGNMENT_AUDIT_2026-07-14.md"
ITER122_RESULT_PATH = Path("experiments/iter122_support_core_taxonomy_documentation/RESULT.md")
ITER123_RESULT_PATH = Path("experiments/iter123_mission_evidence_alignment_audit/RESULT.md")
STALE_STRINGS = ("updated 2026-07-10", "all nineteen iterations")
REQUIRED_TERMS = (
    "HUGSIM transfer null",
    "support-core taxonomy",
    "MISSION_EVIDENCE_ALIGNMENT_AUDIT_COMPLETE",
    BOUNDARY_PHRASE,
    SUPPORT_CORE_NOTE,
    AUDIT_NOTE,
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
    return [item for item in required if normalize(item) not in normalized]


def present_items(text: str, forbidden: tuple[str, ...] | list[str]) -> list[str]:
    normalized = normalize(text)
    return [item for item in forbidden if normalize(item) in normalized]


def check_required(label: str, text: str, required: tuple[str, ...] | list[str]) -> dict[str, Any]:
    missing = missing_items(text, required)
    return {"label": label, "missing": missing, "unexpected": [], "passed": not missing}


def check_absent(label: str, text: str, forbidden: tuple[str, ...] | list[str]) -> dict[str, Any]:
    unexpected = present_items(text, forbidden)
    return {"label": label, "missing": [], "unexpected": unexpected, "passed": not unexpected}


def choose_verdict(problems: list[str], checks: list[dict[str, Any]]) -> str:
    if problems or any(not check["passed"] for check in checks):
        return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(repo_root: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    problems: list[str] = []
    report_text, report_problems = read_text(repo_root / REPORT_PATH)
    manuscript_text, manuscript_problems = read_text(repo_root / MANUSCRIPT_PATH)
    iter122_text, iter122_problems = read_text(repo_root / ITER122_RESULT_PATH)
    iter123_text, iter123_problems = read_text(repo_root / ITER123_RESULT_PATH)
    problems.extend(report_problems)
    problems.extend(manuscript_problems)
    problems.extend(iter122_problems)
    problems.extend(iter123_problems)

    checks = [
        check_absent("report-stale-markers", report_text, STALE_STRINGS),
        check_absent("manuscript-stale-markers", manuscript_text, STALE_STRINGS),
        check_required("report-required-freshness", report_text, REQUIRED_TERMS),
        check_required("manuscript-required-freshness", manuscript_text, REQUIRED_TERMS),
        check_required("iter122-result", iter122_text, ["SUPPORT_CORE_TAXONOMY_DOCUMENTATION_COMPLETE"]),
        check_required("iter123-result", iter123_text, ["MISSION_EVIDENCE_ALIGNMENT_AUDIT_COMPLETE"]),
    ]
    return {
        "iteration": 124,
        "inputs": {
            "report": str(REPORT_PATH),
            "manuscript": str(MANUSCRIPT_PATH),
            "iter122_result": str(ITER122_RESULT_PATH),
            "iter123_result": str(ITER123_RESULT_PATH),
        },
        "summary": {
            "check_count": len(checks),
            "passed_check_count": sum(check["passed"] for check in checks),
            "problem_count": len(problems),
        },
        "checks": checks,
        "problems": problems,
        "verdict": choose_verdict(problems, checks),
        "claim_boundary": BOUNDARY_PHRASE,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 124 - manuscript/report freshness verifier",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Checks", ""])
    for check in report["checks"]:
        lines.append(f"- `{check['label']}`: `{'pass' if check['passed'] else 'fail'}`")
        if check["missing"]:
            lines.append(f"  - missing: `{check['missing']}`")
        if check["unexpected"]:
            lines.append(f"  - unexpected: `{check['unexpected']}`")
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
            "experiments/iter124_manuscript_report_freshness/proof-freshness/"
            "manuscript_report_freshness_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter124_manuscript_report_freshness/proof-freshness/"
            "manuscript_report_freshness.md"
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
