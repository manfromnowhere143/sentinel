#!/usr/bin/env python3
"""Iteration 122 verifier for support-core taxonomy documentation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

COMPLETE_VERDICT = "SUPPORT_CORE_TAXONOMY_DOCUMENTATION_COMPLETE"
INFRA_NULL_VERDICT = "SUPPORT_CORE_TAXONOMY_DOCUMENTATION_INFRA_NULL"
ITER121_VERDICT = "HUGSIM_SUPPORT_CORE_TWO_TRACK_SYNTHESIS_COMPLETE"
BOUNDARY_PHRASE = (
    "descriptive support-core taxonomy only; no repair, actor-causality, threshold-value, "
    "transfer upgrade, safety, deployment, robustness, benchmark, population-rate, "
    "HD-Score-invariance, real-world behavior, first-responder behavior, acquisition-value, "
    "retuning, production, or commercial claim"
)
NOTE_PATH = Path("docs/research/SUPPORT_CORE_TWO_TRACK_TAXONOMY_2026-07-14.md")
REPORT_PATH = Path("docs/REPORT.md")
MANUSCRIPT_PATH = Path("docs/paper/MANUSCRIPT.md")
ITER121_RESULT_PATH = Path("experiments/iter121_hugsim_support_core_two_track_synthesis/RESULT.md")
ITER121_REPORT_PATH = Path(
    "experiments/iter121_hugsim_support_core_two_track_synthesis/proof-synthesis/"
    "support_core_two_track_synthesis_report.json"
)
ITERATION_SLUGS = tuple(
    f"iter{index}_hugsim_support_core_{suffix}"
    for index, suffix in (
        (112, "batch_execution"),
        (113, "actor_match_audit"),
        (114, "mismatch_geometry_decomposition"),
        (115, "monitor_set_ordering"),
        (116, "collision_actor_timeline"),
        (117, "event_window_decomposition"),
        (118, "object_lifecycle"),
        (119, "loss_replacement_audit"),
        (120, "selected_fire_object_lifecycle"),
        (121, "two_track_synthesis"),
    )
)


def read_text(path: Path) -> tuple[str, list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return "", [f"missing-or-empty:{path}"]
    try:
        return path.read_text(), []
    except OSError as exc:
        return "", [f"read-failed:{path}:{exc}"]


def read_json(path: Path) -> tuple[dict[str, Any], list[str]]:
    text, problems = read_text(path)
    if problems:
        return {}, problems
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        return {}, [f"json-decode-failed:{path}:{exc}"]
    if not isinstance(data, dict):
        return {}, [f"json-not-dict:{path}"]
    return data, []


def contains_all(text: str, required: tuple[str, ...] | list[str]) -> list[str]:
    normalized_text = " ".join(text.split())
    missing: list[str] = []
    for item in required:
        normalized_item = " ".join(item.split())
        if normalized_item in normalized_text:
            continue
        if item == BOUNDARY_PHRASE and boundary_superset_present(normalized_text):
            continue
        missing.append(item)
    return missing


def boundary_superset_present(normalized_text: str) -> bool:
    required_terms = (
        "descriptive support-core taxonomy only",
        "no repair",
        "actor-causality",
        "threshold-value",
        "transfer upgrade",
        "safety",
        "deployment",
        "robustness",
        "benchmark",
        "population-rate",
        "HD-Score-invariance",
        "real-world behavior",
        "first-responder behavior",
        "acquisition-value",
        "retuning",
        "production",
        "commercial claim",
    )
    return all(term in normalized_text for term in required_terms)


def check_doc(label: str, text: str, required: tuple[str, ...] | list[str]) -> dict[str, Any]:
    missing = contains_all(text, required)
    return {
        "label": label,
        "required": list(required),
        "missing": missing,
        "passed": not missing,
    }


def choose_verdict(problems: list[str], checks: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if problems or any(not check["passed"] for check in checks):
        return INFRA_NULL_VERDICT
    if summary.get("iter121_verdict") != ITER121_VERDICT:
        return INFRA_NULL_VERDICT
    if summary.get("two_track_split_count") != 8:
        return INFRA_NULL_VERDICT
    if summary.get("selected_never_supported_count") != 8:
        return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(repo_root: Path) -> dict[str, Any]:
    problems: list[str] = []
    repo_root = repo_root.resolve()
    iter121_report, report_problems = read_json(repo_root / ITER121_REPORT_PATH)
    problems.extend(report_problems)

    note_text, note_problems = read_text(repo_root / NOTE_PATH)
    report_text, tech_report_problems = read_text(repo_root / REPORT_PATH)
    manuscript_text, manuscript_problems = read_text(repo_root / MANUSCRIPT_PATH)
    result_text, result_problems = read_text(repo_root / ITER121_RESULT_PATH)
    problems.extend(note_problems)
    problems.extend(tech_report_problems)
    problems.extend(manuscript_problems)
    problems.extend(result_problems)

    summary: dict[str, Any] = {
        "iter121_verdict": iter121_report.get("verdict"),
        "two_track_split_count": None,
        "selected_never_supported_count": None,
    }
    iter121_summary = iter121_report.get("summary")
    if isinstance(iter121_summary, dict):
        summary["two_track_split_count"] = iter121_summary.get("two_track_split_count")
        selected_counts = iter121_summary.get("selected_lifecycle_counts")
        if isinstance(selected_counts, dict):
            summary["selected_never_supported_count"] = selected_counts.get(
                "selected_never_supported_before_collision"
            )
    else:
        problems.append("iter121-summary-not-dict")

    note_required = [*ITERATION_SLUGS, BOUNDARY_PHRASE, "8/8", "support-core two-track taxonomy"]
    surface_required = [
        str(NOTE_PATH.name),
        "iter121_hugsim_support_core_two_track_synthesis",
        BOUNDARY_PHRASE,
    ]
    checks = [
        check_doc("iter121-result-verdict", result_text, [ITER121_VERDICT]),
        check_doc("mechanism-note", note_text, note_required),
        check_doc("technical-report", report_text, surface_required),
        check_doc("manuscript", manuscript_text, surface_required),
    ]
    verdict = choose_verdict(problems, checks, summary)
    return {
        "iteration": 122,
        "inputs": {
            "iter121_result": str(ITER121_RESULT_PATH),
            "iter121_report": str(ITER121_REPORT_PATH),
            "mechanism_note": str(NOTE_PATH),
            "technical_report": str(REPORT_PATH),
            "manuscript": str(MANUSCRIPT_PATH),
        },
        "summary": summary,
        "checks": checks,
        "problems": problems,
        "verdict": verdict,
        "claim_boundary": BOUNDARY_PHRASE,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 122 - support-core taxonomy documentation verifier",
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
            "experiments/iter122_support_core_taxonomy_documentation/proof-docs/"
            "support_core_taxonomy_documentation_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter122_support_core_taxonomy_documentation/proof-docs/"
            "support_core_taxonomy_documentation.md"
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
