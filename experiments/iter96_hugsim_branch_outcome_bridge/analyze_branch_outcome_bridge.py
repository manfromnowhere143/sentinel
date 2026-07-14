#!/usr/bin/env python3
"""Iteration 96 HUGSIM branch taxonomy outcome bridge."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER70_VERDICT = "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE"
ITER94_VERDICT = "HUGSIM_ACTIVE_ROW_SURFACE_MARGIN_ARBITRATION_COMPLETE"
ITER95_VERDICT = "HUGSIM_NONACTIVE_SURFACE_BRANCH_ARBITRATION_SPLIT_COMPLETE"

PROVENANCE_TTC_LABEL = "nonactive_surface_provenance_ttc_borderline_over_path_cpa"
PATH_CPA_LABEL = "nonactive_surface_path_cpa_over_provenance_bridge"
ACTIVE_CPA_LABEL = "active_row_cpa_margin_overrides_provenance"

FIXED_ROWS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "expected_iter95_labels": [PROVENANCE_TTC_LABEL],
        "expected_iter94_labels": [],
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "expected_iter95_labels": [PATH_CPA_LABEL],
        "expected_iter94_labels": [ACTIVE_CPA_LABEL],
    },
)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def load_report(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-{label}:{path}"]
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"read-{label}-failed:{path}:{exc}"]
    if not isinstance(data, dict):
        return {}, [f"{label}-not-dict"]
    return data, []


def row_key(row: dict[str, Any]) -> tuple[Any, Any]:
    return (row.get("audit_id"), row.get("scenario"))


def index_rows(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    if not isinstance(rows, list):
        problems.append(f"{label}-rows-not-list")
        return {}
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append(f"{label}-row-not-dict")
            continue
        audit_id, scenario = row_key(row)
        if not isinstance(audit_id, str) or not isinstance(scenario, str):
            problems.append(f"{label}-row-key-missing:{row}")
            continue
        index.setdefault((audit_id, scenario), []).append(row)
    return index


def exactly_one(index: dict[tuple[str, str], list[dict[str, Any]]], key: tuple[str, str], label: str, problems: list[str]) -> dict[str, Any] | None:
    rows = index.get(key, [])
    if len(rows) != 1:
        problems.append(f"{label}-row-count:{key}:{len(rows)}")
        return None
    row = rows[0]
    if row.get("problems"):
        problems.append(f"{label}-row-problems:{key}:{row.get('problems')}")
    return row


def close_to(left: Any, right: float, abs_tol: float = 1e-9) -> bool:
    return finite_number(left) and math.isclose(float(left), right, abs_tol=abs_tol)


def branch_labels(rows: list[dict[str, Any]]) -> list[str]:
    return [str(row.get("row_label")) for row in rows]


def crosscheck_sources(
    iter70_report: dict[str, Any],
    iter94_report: dict[str, Any],
    iter95_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]], dict[tuple[str, str], list[dict[str, Any]]], list[str]]:
    problems: list[str] = []
    if iter70_report.get("verdict") != ITER70_VERDICT:
        problems.append(f"iter70-verdict-not-{ITER70_VERDICT}")
    if iter94_report.get("verdict") != ITER94_VERDICT:
        problems.append(f"iter94-verdict-not-{ITER94_VERDICT}")
    if iter95_report.get("verdict") != ITER95_VERDICT:
        problems.append(f"iter95-verdict-not-{ITER95_VERDICT}")
    for label, report in (("iter70", iter70_report), ("iter94", iter94_report), ("iter95", iter95_report)):
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter70_index = index_rows(iter70_report.get("episodes"), "iter70", problems)
    iter94_index = index_rows(iter94_report.get("events"), "iter94", problems)
    iter95_index = index_rows(iter95_report.get("events"), "iter95", problems)
    selected: list[dict[str, Any]] = []
    for target in FIXED_ROWS:
        key = (target["audit_id"], target["scenario"])
        row70 = exactly_one(iter70_index, key, "iter70", problems)
        if row70 is None:
            continue
        if row70.get("structural_label") != "foreground_present_late_fire":
            problems.append(f"iter70-structural-label-mismatch:{key}:{row70.get('structural_label')}")
        if row70.get("iter59_support_label") != "post_collision_fire":
            problems.append(f"iter70-support-label-mismatch:{key}:{row70.get('iter59_support_label')}")
        if row70.get("pre_or_at_foreground_fire") is not False:
            problems.append(f"iter70-pre-or-at-foreground-fire-not-false:{key}:{row70.get('pre_or_at_foreground_fire')}")
        if not close_to(row70.get("fire_minus_foreground_s"), 1.75):
            problems.append(f"iter70-fire-minus-foreground-mismatch:{key}:{row70.get('fire_minus_foreground_s')}")

        actual_iter95_labels = branch_labels(iter95_index.get(key, []))
        if actual_iter95_labels != target["expected_iter95_labels"]:
            problems.append(f"iter95-labels-mismatch:{key}:{actual_iter95_labels}")
        actual_iter94_labels = branch_labels(iter94_index.get(key, []))
        if actual_iter94_labels != target["expected_iter94_labels"]:
            problems.append(f"iter94-labels-mismatch:{key}:{actual_iter94_labels}")
        for source_label, rows in (("iter94", iter94_index.get(key, [])), ("iter95", iter95_index.get(key, []))):
            for row in rows:
                if row.get("problems"):
                    problems.append(f"{source_label}-row-problems:{key}:{row.get('problems')}")
        selected.append(row70)
    if len(selected) != len(FIXED_ROWS):
        problems.append(f"fixed-row-count-mismatch:{len(selected)}")
    return selected, iter94_index, iter95_index, problems


def classify_row(row70: dict[str, Any], branches: list[str], problems: list[str]) -> str:
    if problems:
        return "late_fire_branch_outcome_insufficient"
    late_fire = row70.get("structural_label") == "foreground_present_late_fire"
    no_pre_fire = row70.get("pre_or_at_foreground_fire") is False
    has_provenance = PROVENANCE_TTC_LABEL in branches
    has_path = PATH_CPA_LABEL in branches or ACTIVE_CPA_LABEL in branches
    if late_fire and no_pre_fire and has_provenance:
        return "late_fire_with_provenance_ttc_branch"
    if late_fire and no_pre_fire and has_path and not has_provenance:
        return "late_fire_with_path_cpa_branch"
    return "late_fire_branch_outcome_mixed"


def analyze_row(
    row70: dict[str, Any],
    iter94_index: dict[tuple[str, str], list[dict[str, Any]]],
    iter95_index: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    problems: list[str] = []
    key = (str(row70.get("audit_id")), str(row70.get("scenario")))
    branches = branch_labels(iter95_index.get(key, [])) + branch_labels(iter94_index.get(key, []))
    report = row70.get("report") if isinstance(row70.get("report"), dict) else {}
    decision_log = row70.get("decision_log") if isinstance(row70.get("decision_log"), dict) else {}
    first_foreground_ts = report.get("first_foreground_ts")
    first_fire_ts = report.get("first_fire_ts")
    fire_minus_foreground_s = row70.get("fire_minus_foreground_s")
    if not finite_number(first_foreground_ts):
        problems.append(f"first-foreground-ts-not-finite:{first_foreground_ts}")
    if not finite_number(first_fire_ts):
        problems.append(f"first-fire-ts-not-finite:{first_fire_ts}")
    if not close_to(fire_minus_foreground_s, 1.75):
        problems.append(f"fire-minus-foreground-mismatch:{fire_minus_foreground_s}")
    first_fire_channel = report.get("first_fire_channel")
    if first_fire_channel not in {"ttc_only", "cpa_only", "both"}:
        problems.append(f"first-fire-channel-unexpected:{first_fire_channel}")
    if row70.get("pre_or_at_foreground_fire") is not False:
        problems.append(f"pre-or-at-foreground-fire-not-false:{row70.get('pre_or_at_foreground_fire')}")
    if decision_log.get("pre_or_at_foreground_fire_frames") != 0:
        problems.append(f"pre-or-at-foreground-fire-frames-not-zero:{decision_log.get('pre_or_at_foreground_fire_frames')}")
    label = classify_row(row70, branches, problems)
    return {
        "audit_id": row70.get("audit_id"),
        "scenario": row70.get("scenario"),
        "structural_label": row70.get("structural_label"),
        "iter59_support_label": row70.get("iter59_support_label"),
        "first_foreground_ts": first_foreground_ts,
        "first_fire_ts": first_fire_ts,
        "fire_minus_foreground_s": fire_minus_foreground_s,
        "first_fire_channel": first_fire_channel,
        "pre_or_at_foreground_fire": row70.get("pre_or_at_foreground_fire"),
        "pre_or_at_foreground_fire_frames": decision_log.get("pre_or_at_foreground_fire_frames"),
        "branch_labels": branches,
        "branch_label_count": len(branches),
        "has_provenance_ttc_branch": PROVENANCE_TTC_LABEL in branches,
        "has_path_cpa_branch": PATH_CPA_LABEL in branches,
        "has_active_cpa_branch": ACTIVE_CPA_LABEL in branches,
        "row_label": label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_ROWS)
        or any(row.get("problems") for row in rows)
        or "late_fire_branch_outcome_insufficient" in labels
    ):
        return "HUGSIM_BRANCH_TAXONOMY_OUTCOME_BRIDGE_BLOCKED"
    provenance_count = labels.count("late_fire_with_provenance_ttc_branch")
    path_count = labels.count("late_fire_with_path_cpa_branch")
    if provenance_count == 1 and path_count == 1:
        return "HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_OUTCOME_BRIDGE_COMPLETE"
    if provenance_count == len(rows):
        return "HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_PROVENANCE_ONLY_COMPLETE"
    if path_count == len(rows):
        return "HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_PATH_ONLY_COMPLETE"
    return "HUGSIM_BRANCH_TAXONOMY_LATE_FIRE_MIXED_OTHER_COMPLETE"


def build_report(iter70_report_path: Path, iter94_report_path: Path, iter95_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter70_report, problems70 = load_report(iter70_report_path, "iter70-report")
    iter94_report, problems94 = load_report(iter94_report_path, "iter94-report")
    iter95_report, problems95 = load_report(iter95_report_path, "iter95-report")
    infra_problems.extend(problems70 + problems94 + problems95)
    selected: list[dict[str, Any]] = []
    iter94_index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    iter95_index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    if not infra_problems:
        selected, iter94_index, iter95_index, source_problems = crosscheck_sources(iter70_report, iter94_report, iter95_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_row(row, iter94_index, iter95_index) for row in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 96,
        "inputs": {
            "iter70_report": str(iter70_report_path),
            "iter94_report": str(iter94_report_path),
            "iter95_report": str(iter95_report_path),
        },
        "fixed_rows": list(FIXED_ROWS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_rows": len(selected),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "late_fire_rows": sum(row.get("structural_label") == "foreground_present_late_fire" for row in rows),
            "no_pre_foreground_fire_rows": sum(row.get("pre_or_at_foreground_fire") is False for row in rows),
            "provenance_ttc_branch_rows": sum(row.get("has_provenance_ttc_branch") is True for row in rows),
            "path_cpa_branch_rows": sum(
                row.get("has_path_cpa_branch") is True or row.get("has_active_cpa_branch") is True for row in rows
            ),
            "active_cpa_branch_rows": sum(row.get("has_active_cpa_branch") is True for row in rows),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "two-row descriptive branch-taxonomy/outcome bridge only; no actor-causality, repair, "
            "threshold-value, transfer, safety, deployment, robustness, benchmark, population-rate, "
            "HD-Score-invariance, commercial-value, real-world behavior, first-responder behavior, "
            "or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 96 - HUGSIM branch taxonomy outcome bridge",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    if report["infra_problems"]:
        lines.extend(["", "## Infrastructure Problems", ""])
        lines.extend(f"- `{problem}`" for problem in report["infra_problems"])
    lines.extend(
        [
            "",
            "## Events",
            "",
            "| audit id | first foreground | first fire | delta | channel | branches | label | problems |",
            "|---|---:|---:|---:|---|---|---|---|",
        ]
    )
    for row in report["events"]:
        lines.append(
            f"| `{row['audit_id']}` | `{row.get('first_foreground_ts')}` | `{row.get('first_fire_ts')}` | "
            f"`{row.get('fire_minus_foreground_s')}` | `{row.get('first_fire_channel')}` | "
            f"`{row.get('branch_labels')}` | `{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter70_report: Path, iter94_report: Path, iter95_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter70_report, iter94_report, iter95_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter70-report",
        type=Path,
        default=Path("experiments/iter70_hugsim_structural_timing_audit/proof-structural/structural_report.json"),
    )
    parser.add_argument(
        "--iter94-report",
        type=Path,
        default=Path(
            "experiments/iter94_hugsim_active_row_surface_margin_arbitration/proof-margin/"
            "active_row_surface_margin_arbitration_report.json"
        ),
    )
    parser.add_argument(
        "--iter95-report",
        type=Path,
        default=Path(
            "experiments/iter95_hugsim_nonactive_surface_branch_arbitration/proof-branch/"
            "nonactive_surface_branch_arbitration_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter96_hugsim_branch_outcome_bridge/proof-outcome/"
            "branch_outcome_bridge_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter96_hugsim_branch_outcome_bridge/proof-outcome/"
            "branch_outcome_bridge.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter70_report, args.iter94_report, args.iter95_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
