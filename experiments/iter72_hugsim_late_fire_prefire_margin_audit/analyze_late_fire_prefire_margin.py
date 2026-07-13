#!/usr/bin/env python3
"""Iteration 72 HUGSIM late-fire prefire margin audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any


ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER70_VERDICT = "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE"
FIXED_ROWS = (
    ("both_distinct_extreme", "scene-0138-extreme-00"),
    ("ttc_medium_a", "scene-0071-medium-01"),
)

ITER71_MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "iter71_hugsim_surface_silent_margin_audit"
    / "analyze_surface_silent_margin.py"
)
SPEC = importlib.util.spec_from_file_location("iter71_surface_silent_margin", ITER71_MODULE_PATH)
assert SPEC is not None
surface_margin = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(surface_margin)


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter70_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]], list[str]]:
    problems: list[str] = []
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter70_report.get("verdict") != ITER70_VERDICT:
        problems.append(f"iter70-verdict-not-{ITER70_VERDICT}")
    if iter59_report.get("infra_problems"):
        problems.append(f"iter59-infra-problems:{iter59_report.get('infra_problems')}")
    if iter70_report.get("infra_problems"):
        problems.append(f"iter70-infra-problems:{iter70_report.get('infra_problems')}")
    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter70_index = surface_margin.index_rows(iter70_report.get("episodes"), "iter70", problems)
    rows: list[dict[str, Any]] = []
    for key in FIXED_ROWS:
        row59 = iter59_index.get(key)
        row70 = iter70_index.get(key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{key}")
            continue
        if row70 is None:
            problems.append(f"missing-iter70-row:{key}")
            continue
        if row59.get("support_label") != "post_collision_fire":
            problems.append(f"iter59-support-not-post-collision-fire:{key}:{row59.get('support_label')}")
        if row70.get("structural_label") != "foreground_present_late_fire":
            problems.append(f"iter70-structural-label-mismatch:{key}:{row70.get('structural_label')}")
        if row70.get("problems"):
            problems.append(f"iter70-row-problems:{key}:{row70.get('problems')}")
        report = row70.get("report")
        if isinstance(report, dict):
            first_fg = row59.get("first_foreground_ts")
            first_fire = row59.get("first_fire_ts")
            if report.get("first_foreground_ts") != first_fg:
                problems.append(f"first-foreground-mismatch:{key}:{report.get('first_foreground_ts')}!={first_fg}")
            if report.get("first_fire_ts") != first_fire:
                problems.append(f"first-fire-mismatch:{key}:{report.get('first_fire_ts')}!={first_fire}")
        rows.append(row59)
    actual_keys = [surface_margin.row_key(row) for row in rows]
    if actual_keys != list(FIXED_ROWS):
        problems.append(f"fixed-row-order-mismatch:{actual_keys}")
    return rows, iter70_index, problems


def row_label(summary: dict[str, Any]) -> str:
    if int(summary.get("pre_foreground_object_rows") or 0) == 0:
        return "late_fire_prefire_no_object_rows"
    if int(summary.get("active_ttc_frames") or 0) > 0 or int(summary.get("active_cpa_frames") or 0) > 0:
        return "late_fire_prefire_active_crossing_inconsistent"
    if int(summary.get("near_ttc_frames") or 0) > 0:
        return "late_fire_prefire_near_ttc_margin"
    if int(summary.get("near_cpa_frames") or 0) > 0:
        return "late_fire_prefire_near_cpa_margin"
    return "late_fire_prefire_far_margin"


def analyze_row(row: dict[str, Any]) -> dict[str, Any]:
    problems: list[str] = []
    first_foreground_ts = surface_margin.number(row.get("first_foreground_ts"), "first_foreground_ts", problems)
    first_fire_ts = surface_margin.number(row.get("first_fire_ts"), "first_fire_ts", problems)
    episode_dir = row.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        summary: dict[str, Any] = {}
    elif first_foreground_ts is None:
        summary = {}
    else:
        summary, scan_problems = surface_margin.scan_pre_foreground_log(
            Path(episode_dir) / "sentinel_iter48_decisions.jsonl",
            first_foreground_ts,
        )
        problems.extend(scan_problems)
    if summary.get("pre_foreground_fired_frames"):
        problems.append(f"pre-foreground-fired-frames:{summary['pre_foreground_fired_frames']}")
    fire_delay_s = None
    if first_foreground_ts is not None and first_fire_ts is not None:
        fire_delay_s = first_fire_ts - first_foreground_ts
        if fire_delay_s <= 0:
            problems.append(f"not-late-fire:{fire_delay_s}")
    label = row_label(summary) if not problems else "late_fire_prefire_active_crossing_inconsistent"
    return {
        "audit_id": row.get("audit_id"),
        "scenario": row.get("scenario"),
        "first_foreground_ts": row.get("first_foreground_ts"),
        "first_fire_ts": row.get("first_fire_ts"),
        "fire_delay_s": fire_delay_s,
        "episode_dir": row.get("episode_dir"),
        "row_label": label,
        "summary": summary,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or len(rows) != len(FIXED_ROWS) or any(row.get("problems") for row in rows):
        return "HUGSIM_LATE_FIRE_PREFIRE_MARGIN_BLOCKED"
    if any(row.get("row_label") == "late_fire_prefire_active_crossing_inconsistent" for row in rows):
        return "HUGSIM_LATE_FIRE_PREFIRE_ACTIVE_INCONSISTENT_BLOCKED"
    return "HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE"


def build_report(iter59_report_path: Path, iter70_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter70_report, problems70 = surface_margin.load_report(iter70_report_path, "iter70-report")
    infra_problems.extend(problems59)
    infra_problems.extend(problems70)
    selected_rows: list[dict[str, Any]] = []
    if not infra_problems:
        selected_rows, _iter70_index, source_problems = crosscheck_sources(iter59_report, iter70_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_row(row) for row in selected_rows]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 72,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter70_report": str(iter70_report_path),
        },
        "fixed_rows": [{"audit_id": audit_id, "scenario": scenario} for audit_id, scenario in FIXED_ROWS],
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "target_rows": len(selected_rows),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "near_margin_rows": sum(
                row.get("row_label") in {"late_fire_prefire_near_ttc_margin", "late_fire_prefire_near_cpa_margin"}
                for row in rows
            ),
            "far_margin_rows": sum(row.get("row_label") == "late_fire_prefire_far_margin" for row in rows),
            "no_object_rows": sum(row.get("row_label") == "late_fire_prefire_no_object_rows" for row in rows),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "two-row descriptive late-fire prefire margin audit only; no actor-causality, repair, "
            "threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 72 - HUGSIM late-fire prefire margin audit",
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
    lines.extend([
        "",
        "## Rows",
        "",
        "| audit id | scenario | label | delay | min valid TTC | TTC margin | min CPA | CPA margin | problems |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ])
    for row in report["episodes"]:
        summary = row["summary"]
        lines.append(
            f"| `{row['audit_id']}` | `{row['scenario']}` | `{row['row_label']}` | "
            f"`{row.get('fire_delay_s')}` | `{summary.get('min_valid_ttc_s')}` | "
            f"`{summary.get('closest_ttc_margin_s')}` | `{summary.get('min_cpa_m')}` | "
            f"`{summary.get('closest_cpa_margin_m')}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter59_report: Path, iter70_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter59_report, iter70_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter59-report",
        type=Path,
        default=Path("experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json"),
    )
    parser.add_argument(
        "--iter70-report",
        type=Path,
        default=Path("experiments/iter70_hugsim_structural_timing_audit/proof-structural/structural_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter72_hugsim_late_fire_prefire_margin_audit/proof-prefire/prefire_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter72_hugsim_late_fire_prefire_margin_audit/proof-prefire/prefire.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter59_report, args.iter70_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
