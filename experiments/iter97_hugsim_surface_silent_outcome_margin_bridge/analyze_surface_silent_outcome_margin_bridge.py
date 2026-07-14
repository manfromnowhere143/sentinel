#!/usr/bin/env python3
"""Iteration 97 HUGSIM surface-silent outcome margin bridge."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER70_VERDICT = "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE"
ITER71_VERDICT = "HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE"
ITER73_VERDICT = "HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE"

FIXED_ROWS = (
    {"audit_id": "mixed_extreme", "scenario": "scene-0062-extreme-00"},
    {"audit_id": "nofire_hard_control", "scenario": "scene-0041-hard-00"},
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


def positive_or_none(value: Any) -> bool:
    return value is None or (finite_number(value) and float(value) > 0)


def crosscheck_sources(
    iter70_report: dict[str, Any],
    iter71_report: dict[str, Any],
    iter73_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], list[dict[str, Any]]], dict[tuple[str, str], list[dict[str, Any]]], list[str]]:
    problems: list[str] = []
    if iter70_report.get("verdict") != ITER70_VERDICT:
        problems.append(f"iter70-verdict-not-{ITER70_VERDICT}")
    if iter71_report.get("verdict") != ITER71_VERDICT:
        problems.append(f"iter71-verdict-not-{ITER71_VERDICT}")
    if iter73_report.get("verdict") != ITER73_VERDICT:
        problems.append(f"iter73-verdict-not-{ITER73_VERDICT}")
    for label, report in (("iter70", iter70_report), ("iter71", iter71_report), ("iter73", iter73_report)):
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter70_index = index_rows(iter70_report.get("episodes"), "iter70", problems)
    iter71_index = index_rows(iter71_report.get("episodes"), "iter71", problems)
    iter73_index = index_rows(iter73_report.get("episodes"), "iter73", problems)
    selected: list[dict[str, Any]] = []
    for target in FIXED_ROWS:
        key = (target["audit_id"], target["scenario"])
        row70 = exactly_one(iter70_index, key, "iter70", problems)
        row71 = exactly_one(iter71_index, key, "iter71", problems)
        row73 = exactly_one(iter73_index, key, "iter73", problems)
        if row70 is None or row71 is None or row73 is None:
            continue
        if row70.get("structural_label") != "foreground_present_surface_silent":
            problems.append(f"iter70-structural-label-mismatch:{key}:{row70.get('structural_label')}")
        if row70.get("iter59_support_label") != "no_monitor_fire":
            problems.append(f"iter70-support-label-mismatch:{key}:{row70.get('iter59_support_label')}")
        if row70.get("pre_or_at_foreground_fire") is not False:
            problems.append(f"iter70-pre-or-at-foreground-fire-not-false:{key}:{row70.get('pre_or_at_foreground_fire')}")
        if row71.get("row_label") != "surface_silent_far_margin":
            problems.append(f"iter71-label-mismatch:{key}:{row71.get('row_label')}")
        if row73.get("row_label") != "silent_far_never_active":
            problems.append(f"iter73-label-mismatch:{key}:{row73.get('row_label')}")
        selected.append(row70)
    if len(selected) != len(FIXED_ROWS):
        problems.append(f"fixed-row-count-mismatch:{len(selected)}")
    return selected, iter71_index, iter73_index, problems


def classify_row(measurements: dict[str, Any], problems: list[str]) -> str:
    if problems:
        return "surface_silent_outcome_margin_insufficient"
    base = (
        measurements["structural_label"] == "foreground_present_surface_silent"
        and measurements["iter70_first_fire_ts"] is None
        and measurements["iter70_fired_frames"] == 0
        and measurements["iter71_row_label"] == "surface_silent_far_margin"
        and measurements["iter71_active_cpa_frames"] == 0
        and measurements["iter71_active_ttc_frames"] == 0
        and measurements["iter73_row_label"] == "silent_far_never_active"
        and measurements["iter73_first_active_relation_to_foreground"] == "never"
        and measurements["iter73_pre_foreground_near_any"] is False
    )
    if not base:
        return "surface_silent_outcome_margin_mixed"
    first_near_offset = measurements["iter73_first_near_offset_s"]
    if finite_number(first_near_offset) and float(first_near_offset) > 0:
        return "surface_silent_far_never_active_post_foreground_near"
    if first_near_offset is None:
        return "surface_silent_far_never_active_no_near"
    return "surface_silent_outcome_margin_mixed"


def analyze_row(
    row70: dict[str, Any],
    iter71_index: dict[tuple[str, str], list[dict[str, Any]]],
    iter73_index: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    problems: list[str] = []
    key = (str(row70.get("audit_id")), str(row70.get("scenario")))
    row71 = iter71_index[key][0]
    row73 = iter73_index[key][0]
    report70 = row70.get("report") if isinstance(row70.get("report"), dict) else {}
    decision_log70 = row70.get("decision_log") if isinstance(row70.get("decision_log"), dict) else {}
    summary71 = row71.get("summary") if isinstance(row71.get("summary"), dict) else {}
    timeline73 = row73.get("timeline") if isinstance(row73.get("timeline"), dict) else {}
    if not summary71:
        problems.append("iter71-summary-missing")
    if not timeline73:
        problems.append("iter73-timeline-missing")
    closest_cpa_margin = summary71.get("closest_cpa_margin_m")
    closest_ttc_margin = summary71.get("closest_ttc_margin_s")
    if not finite_number(closest_cpa_margin) or float(closest_cpa_margin) <= 0:
        problems.append(f"iter71-closest-cpa-margin-not-positive:{closest_cpa_margin}")
    if not positive_or_none(closest_ttc_margin):
        problems.append(f"iter71-closest-ttc-margin-not-positive-or-null:{closest_ttc_margin}")
    measurements = {
        "structural_label": row70.get("structural_label"),
        "iter59_support_label": row70.get("iter59_support_label"),
        "first_foreground_ts": report70.get("first_foreground_ts"),
        "foreground_count": report70.get("foreground_count"),
        "iter70_first_fire_ts": report70.get("first_fire_ts"),
        "iter70_fired_frames": decision_log70.get("fired_frames"),
        "iter70_pre_or_at_foreground_fire": row70.get("pre_or_at_foreground_fire"),
        "iter71_row_label": row71.get("row_label"),
        "iter71_closest_cpa_margin_m": closest_cpa_margin,
        "iter71_closest_ttc_margin_s": closest_ttc_margin,
        "iter71_active_cpa_frames": summary71.get("active_cpa_frames"),
        "iter71_active_ttc_frames": summary71.get("active_ttc_frames"),
        "iter71_pre_foreground_fired_frames": summary71.get("pre_foreground_fired_frames"),
        "iter73_row_label": row73.get("row_label"),
        "iter73_first_near_offset_s": timeline73.get("first_near_offset_s"),
        "iter73_first_active_offset_s": timeline73.get("first_active_offset_s"),
        "iter73_first_active_relation_to_foreground": timeline73.get("first_active_relation_to_foreground"),
        "iter73_pre_foreground_near_any": timeline73.get("pre_foreground_near_any"),
        "iter73_pre_foreground_near_cpa": timeline73.get("pre_foreground_near_cpa"),
        "iter73_pre_foreground_near_ttc": timeline73.get("pre_foreground_near_ttc"),
    }
    label = classify_row(measurements, problems)
    return {
        "audit_id": row70.get("audit_id"),
        "scenario": row70.get("scenario"),
        "measurements": measurements,
        "row_label": label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_ROWS)
        or any(row.get("problems") for row in rows)
        or "surface_silent_outcome_margin_insufficient" in labels
    ):
        return "HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_BLOCKED"
    post_near = labels.count("surface_silent_far_never_active_post_foreground_near")
    no_near = labels.count("surface_silent_far_never_active_no_near")
    if post_near + no_near == len(rows) and post_near >= 1:
        return "HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_BRIDGE_COMPLETE"
    if no_near == len(rows):
        return "HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_NO_NEAR_COMPLETE"
    return "HUGSIM_SURFACE_SILENT_OUTCOME_MARGIN_MIXED_COMPLETE"


def build_report(iter70_report_path: Path, iter71_report_path: Path, iter73_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter70_report, problems70 = load_report(iter70_report_path, "iter70-report")
    iter71_report, problems71 = load_report(iter71_report_path, "iter71-report")
    iter73_report, problems73 = load_report(iter73_report_path, "iter73-report")
    infra_problems.extend(problems70 + problems71 + problems73)
    selected: list[dict[str, Any]] = []
    iter71_index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    iter73_index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    if not infra_problems:
        selected, iter71_index, iter73_index, source_problems = crosscheck_sources(iter70_report, iter71_report, iter73_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_row(row, iter71_index, iter73_index) for row in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 97,
        "inputs": {
            "iter70_report": str(iter70_report_path),
            "iter71_report": str(iter71_report_path),
            "iter73_report": str(iter73_report_path),
        },
        "fixed_rows": list(FIXED_ROWS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_rows": len(selected),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "surface_silent_rows": sum(
                row.get("measurements", {}).get("structural_label") == "foreground_present_surface_silent"
                for row in rows
            ),
            "zero_fire_rows": sum(row.get("measurements", {}).get("iter70_fired_frames") == 0 for row in rows),
            "far_margin_rows": sum(row.get("measurements", {}).get("iter71_row_label") == "surface_silent_far_margin" for row in rows),
            "never_active_rows": sum(row.get("measurements", {}).get("iter73_first_active_relation_to_foreground") == "never" for row in rows),
            "post_foreground_near_rows": sum(
                finite_number(row.get("measurements", {}).get("iter73_first_near_offset_s"))
                and float(row["measurements"]["iter73_first_near_offset_s"]) > 0
                for row in rows
            ),
            "pre_foreground_near_rows": sum(
                row.get("measurements", {}).get("iter73_pre_foreground_near_any") is True for row in rows
            ),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "two-row descriptive surface-silent outcome/margin bridge only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, "
            "population-rate, HD-Score-invariance, commercial-value, real-world behavior, "
            "first-responder behavior, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 97 - HUGSIM surface-silent outcome margin bridge",
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
            "| audit id | foreground | CPA margin | TTC margin | near offset | active relation | label | problems |",
            "|---|---:|---:|---|---:|---|---|---|",
        ]
    )
    for row in report["events"]:
        measurements = row.get("measurements") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{measurements.get('first_foreground_ts')}` | "
            f"`{measurements.get('iter71_closest_cpa_margin_m')}` | "
            f"`{measurements.get('iter71_closest_ttc_margin_s')}` | "
            f"`{measurements.get('iter73_first_near_offset_s')}` | "
            f"`{measurements.get('iter73_first_active_relation_to_foreground')}` | "
            f"`{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter70_report: Path, iter71_report: Path, iter73_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter70_report, iter71_report, iter73_report)
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
        "--iter71-report",
        type=Path,
        default=Path("experiments/iter71_hugsim_surface_silent_margin_audit/proof-margin/margin_report.json"),
    )
    parser.add_argument(
        "--iter73-report",
        type=Path,
        default=Path("experiments/iter73_hugsim_margin_transition_audit/proof-transition/transition_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter97_hugsim_surface_silent_outcome_margin_bridge/proof-silent-outcome/"
            "surface_silent_outcome_margin_bridge_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter97_hugsim_surface_silent_outcome_margin_bridge/proof-silent-outcome/"
            "surface_silent_outcome_margin_bridge.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter70_report, args.iter71_report, args.iter73_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
