#!/usr/bin/env python3
"""Iteration 121 HUGSIM support-core two-track synthesis."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any

ITER118_VERDICT = "HUGSIM_SUPPORT_CORE_OBJECT_LIFECYCLE_COMPLETE"
ITER119_VERDICT = "HUGSIM_SUPPORT_CORE_LOSS_REPLACEMENT_COMPLETE"
ITER120_VERDICT = "HUGSIM_SUPPORT_CORE_SELECTED_FIRE_OBJECT_COMPLETE"
COMPLETE_VERDICT = "HUGSIM_SUPPORT_CORE_TWO_TRACK_SYNTHESIS_COMPLETE"
INFRA_NULL_VERDICT = "HUGSIM_SUPPORT_CORE_TWO_TRACK_SYNTHESIS_INFRA_NULL"
EXPECTED_ROW_COUNT = 8
TWO_TRACK_SUPPORT_LABELS = {
    "pre_fire_object_absent_at_fire",
    "pre_fire_object_drifted_outside_support_at_fire",
    "post_fire_support_only_different_object_active_support",
    "post_fire_support_only_far_support",
    "never_supported_reference",
}


def load_json(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-{label}:{path}"]
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"read-{label}-failed:{path}:{exc}"]
    if not isinstance(data, dict):
        return {}, [f"{label}-not-dict"]
    return data, []


def require_equal(problems: list[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        problems.append(f"{label}-mismatch:{actual!r}!={expected!r}")


def synthesis_label(support_label: str, replacement_label: str, selected_label: str) -> str:
    if selected_label != "selected_never_supported_before_collision":
        return "two_track_other"
    if support_label == "pre_fire_object_absent_at_fire":
        if replacement_label == "pre_fire_lost_absent_selected_nearest":
            return "two_track_pre_support_lost_absent_selected_nearest"
        if replacement_label == "pre_fire_lost_absent_selected_not_nearest":
            return "two_track_pre_support_lost_absent_selected_not_nearest"
    if (
        support_label == "pre_fire_object_drifted_outside_support_at_fire"
        and replacement_label == "pre_fire_drifted_selected_not_nearest"
    ):
        return "two_track_pre_support_drifted_selected_not_nearest"
    if support_label.startswith("post_fire_support_only") and replacement_label == "post_fire_support_selected_nearest":
        return "two_track_post_fire_support_selected_nearest"
    if (
        support_label == "never_supported_reference"
        and replacement_label == "never_supported_reference_selected_nearest"
    ):
        return "two_track_never_supported_selected_nearest"
    return "two_track_other"


def _dict_counts(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def _row_map(rows: list[Any], label: str, problems: list[str]) -> dict[Any, dict[str, Any]]:
    out: dict[Any, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append(f"{label}-row-not-dict")
            continue
        slot_id = row.get("slot_id")
        if slot_id in out:
            problems.append(f"{label}-duplicate-slot:{slot_id!r}")
            continue
        out[slot_id] = row
    return out


def classify_row(row118: dict[str, Any], row119: dict[str, Any], row120: dict[str, Any]) -> dict[str, Any]:
    problems: list[str] = []
    for key in ("slot_id", "scenario", "run"):
        if row119.get(key) != row118.get(key):
            problems.append(f"iter119-{key}-mismatch:{row119.get(key)!r}!={row118.get(key)!r}")
        if row120.get(key) != row118.get(key):
            problems.append(f"iter120-{key}-mismatch:{row120.get(key)!r}!={row118.get(key)!r}")
    for label, row in (("iter118", row118), ("iter119", row119), ("iter120", row120)):
        if row.get("problems"):
            problems.append(f"{label}-row-problems:{row.get('problems')!r}")
    support_label = row118.get("lifecycle_label")
    replacement = row119.get("replacement_label")
    selected = row120.get("selected_lifecycle_label")
    if not isinstance(support_label, str):
        problems.append(f"support-label-missing:{support_label!r}")
    if not isinstance(replacement, str):
        problems.append(f"replacement-label-missing:{replacement!r}")
    if not isinstance(selected, str):
        problems.append(f"selected-label-missing:{selected!r}")
    if problems:
        return {
            "slot_index": row118.get("slot_index"),
            "slot_id": row118.get("slot_id"),
            "scenario": row118.get("scenario"),
            "run": row118.get("run"),
            "problems": problems,
        }
    two_track = selected == "selected_never_supported_before_collision" and support_label in TWO_TRACK_SUPPORT_LABELS
    label = synthesis_label(support_label, replacement, selected)
    return {
        "slot_index": row118.get("slot_index"),
        "slot_id": row118.get("slot_id"),
        "scenario": row118.get("scenario"),
        "run": row118.get("run"),
        "support_lifecycle_label": support_label,
        "replacement_label": replacement,
        "selected_lifecycle_label": selected,
        "selected_rank_by_collision_distance": row119.get("selected_rank_by_collision_distance"),
        "selected_is_fire_nearest": row119.get("selected_is_fire_nearest"),
        "fire_minus_last_support_s": row119.get("fire_minus_last_support_s"),
        "fire_minus_last_presence_s": row119.get("fire_minus_last_presence_s"),
        "selected_before_collision_closest_distance_m": row120.get("selected_before_collision_closest_distance_m"),
        "two_track_split": two_track,
        "synthesis_label": label,
        "problems": [],
    }


def choose_verdict(infra_problems: list[str], rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if infra_problems or any(row.get("problems") for row in rows):
        return INFRA_NULL_VERDICT
    if summary.get("row_count") != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    if sum(summary.get("synthesis_label_counts", {}).values()) != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    for row in rows:
        if "two_track_split" not in row or "synthesis_label" not in row:
            return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(iter118_report_path: Path, iter119_report_path: Path, iter120_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    report118, problems118 = load_json(iter118_report_path, "iter118-report")
    report119, problems119 = load_json(iter119_report_path, "iter119-report")
    report120, problems120 = load_json(iter120_report_path, "iter120-report")
    infra_problems.extend(problems118)
    infra_problems.extend(problems119)
    infra_problems.extend(problems120)
    rows: list[dict[str, Any]] = []
    if not infra_problems:
        require_equal(infra_problems, "iter118-verdict", report118.get("verdict"), ITER118_VERDICT)
        require_equal(infra_problems, "iter119-verdict", report119.get("verdict"), ITER119_VERDICT)
        require_equal(infra_problems, "iter120-verdict", report120.get("verdict"), ITER120_VERDICT)
        rows118 = report118.get("lifecycle_rows")
        rows119 = report119.get("replacement_rows")
        rows120 = report120.get("selected_lifecycle_rows")
        if not isinstance(rows118, list):
            infra_problems.append("iter118-lifecycle-rows-not-list")
            rows118 = []
        if not isinstance(rows119, list):
            infra_problems.append("iter119-replacement-rows-not-list")
            rows119 = []
        if not isinstance(rows120, list):
            infra_problems.append("iter120-selected-lifecycle-rows-not-list")
            rows120 = []
        require_equal(infra_problems, "iter118-row-count", len(rows118), EXPECTED_ROW_COUNT)
        require_equal(infra_problems, "iter119-row-count", len(rows119), EXPECTED_ROW_COUNT)
        require_equal(infra_problems, "iter120-row-count", len(rows120), EXPECTED_ROW_COUNT)
    if not infra_problems:
        map119 = _row_map(report119["replacement_rows"], "iter119", infra_problems)
        map120 = _row_map(report120["selected_lifecycle_rows"], "iter120", infra_problems)
        for row118 in report118["lifecycle_rows"]:
            if not isinstance(row118, dict):
                infra_problems.append("iter118-row-not-dict")
                continue
            slot_id = row118.get("slot_id")
            row119 = map119.get(slot_id)
            row120 = map120.get(slot_id)
            if row119 is None or row120 is None:
                infra_problems.append(f"joined-row-missing:{slot_id!r}")
                continue
            rows.append(classify_row(row118, row119, row120))

    clean_rows = [row for row in rows if not row.get("problems")]
    summary = {
        "row_count": len(rows),
        "problem_row_count": sum(bool(row.get("problems")) for row in rows),
        "synthesis_label_counts": _dict_counts(Counter(row.get("synthesis_label") for row in clean_rows)),
        "two_track_split_count": sum(row.get("two_track_split") is True for row in clean_rows),
        "support_lifecycle_counts": _dict_counts(Counter(row.get("support_lifecycle_label") for row in clean_rows)),
        "replacement_label_counts": _dict_counts(Counter(row.get("replacement_label") for row in clean_rows)),
        "selected_lifecycle_counts": _dict_counts(Counter(row.get("selected_lifecycle_label") for row in clean_rows)),
        "selected_is_fire_nearest_count": sum(row.get("selected_is_fire_nearest") is True for row in clean_rows),
        "selected_not_fire_nearest_count": sum(row.get("selected_is_fire_nearest") is False for row in clean_rows),
    }
    verdict = choose_verdict(infra_problems, rows, summary)
    return {
        "iteration": 121,
        "inputs": {
            "iter118_report": str(iter118_report_path),
            "iter119_report": str(iter119_report_path),
            "iter120_report": str(iter120_report_path),
        },
        "infra_problems": infra_problems,
        "synthesis_rows": rows,
        "summary": summary,
        "verdict": verdict,
        "claim_boundary": (
            "descriptive support-core two-track synthesis of committed reports only; no repair, "
            "actor-causality, threshold-value, transfer, safety, deployment, robustness, benchmark, "
            "population-rate, HD-Score-invariance, real-world behavior, first-responder behavior, "
            "acquisition-value, retuning, production, or commercial claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 121 - HUGSIM support-core two-track synthesis",
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
            "## Rows",
            "",
            "| slot | scenario | run | synthesis | support lifecycle | replacement | selected lifecycle | two-track |",
            "|---:|---|---:|---|---|---|---|---|",
        ]
    )
    for row in report["synthesis_rows"]:
        lines.append(
            f"| `{row.get('slot_index')}` | `{row.get('scenario')}` | `{row.get('run')}` | "
            f"`{row.get('synthesis_label')}` | `{row.get('support_lifecycle_label')}` | "
            f"`{row.get('replacement_label')}` | `{row.get('selected_lifecycle_label')}` | "
            f"`{row.get('two_track_split')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter118_report: Path,
    iter119_report: Path,
    iter120_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter118_report, iter119_report, iter120_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter118-report",
        type=Path,
        default=Path(
            "experiments/iter118_hugsim_support_core_object_lifecycle/proof-lifecycle/"
            "support_core_object_lifecycle_report.json"
        ),
    )
    parser.add_argument(
        "--iter119-report",
        type=Path,
        default=Path(
            "experiments/iter119_hugsim_support_core_loss_replacement_audit/proof-replacement/"
            "support_core_loss_replacement_report.json"
        ),
    )
    parser.add_argument(
        "--iter120-report",
        type=Path,
        default=Path(
            "experiments/iter120_hugsim_support_core_selected_fire_object_lifecycle/proof-selected/"
            "selected_fire_object_lifecycle_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter121_hugsim_support_core_two_track_synthesis/proof-synthesis/"
            "support_core_two_track_synthesis_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter121_hugsim_support_core_two_track_synthesis/proof-synthesis/"
            "support_core_two_track_synthesis.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter118_report,
        args.iter119_report,
        args.iter120_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
