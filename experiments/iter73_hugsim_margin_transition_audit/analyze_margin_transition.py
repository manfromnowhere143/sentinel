#!/usr/bin/env python3
"""Iteration 73 HUGSIM structural margin-transition audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER70_VERDICT = "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE"
ITER71_VERDICT = "HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE"
ITER72_VERDICT = "HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE"
TIME_TOL = 1e-9
TTC_NEAR_MARGIN_S = 1.0
CPA_NEAR_MARGIN_M = 1.5
INVALID_TTC_SENTINEL = 1e8
FIXED_ROWS = (
    ("mixed_extreme", "scene-0062-extreme-00", "foreground_present_surface_silent"),
    ("nofire_hard_control", "scene-0041-hard-00", "foreground_present_surface_silent"),
    ("both_distinct_extreme", "scene-0138-extreme-00", "foreground_present_late_fire"),
    ("ttc_medium_a", "scene-0071-medium-01", "foreground_present_late_fire"),
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


def relation_to_foreground(ts: float | None, foreground_ts: float) -> str:
    if ts is None:
        return "never"
    if ts < foreground_ts - TIME_TOL:
        return "before"
    if abs(ts - foreground_ts) <= TIME_TOL:
        return "at"
    return "after"


def first_min(current: float | None, candidate: float | None) -> float | None:
    if candidate is None:
        return current
    if current is None or candidate < current:
        return candidate
    return current


def scan_full_timeline(path: Path, foreground_ts: float) -> tuple[dict[str, Any], list[str]]:
    problems: list[str] = []
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-decision-log:{path}"]
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        return {}, [f"read-decision-log-failed:{path}:{exc}"]

    monitor_frames = 0
    object_rows = 0
    fired_frames = 0
    ttc_thresh_values: set[float] = set()
    cpa_margin_values: set[float] = set()
    first_fire_ts: float | None = None
    first_near_ttc_ts: float | None = None
    first_near_cpa_ts: float | None = None
    first_active_ttc_ts: float | None = None
    first_active_cpa_ts: float | None = None
    first_active_ts: float | None = None
    first_active_channel: str | None = None
    min_valid_ttc: float | None = None
    min_cpa: float | None = None
    closest_ttc_margin: float | None = None
    closest_cpa_margin: float | None = None
    closest_ttc_ts: float | None = None
    closest_cpa_ts: float | None = None
    pre_foreground_near_ttc = False
    pre_foreground_near_cpa = False

    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(f"bad-json-line:{path}:{line_no}:{exc}")
            continue
        if not isinstance(row, dict):
            problems.append(f"decision-row-not-dict:{path}:{line_no}")
            continue
        if "trace_error" in row:
            continue
        ts = surface_margin.number(row.get("ts", row.get("frame_index")), f"ts:{line_no}", problems)
        if ts is None:
            continue
        params = row.get("params")
        if not isinstance(params, dict):
            problems.append(f"params-missing:{path}:{line_no}")
            continue
        ttc_thresh = surface_margin.number(params.get("ttc_thresh"), f"ttc_thresh:{line_no}", problems)
        cpa_margin = surface_margin.number(params.get("cpa_margin"), f"cpa_margin:{line_no}", problems)
        if ttc_thresh is None or cpa_margin is None:
            continue
        ttc_thresh_values.add(ttc_thresh)
        cpa_margin_values.add(cpa_margin)
        monitor_frames += 1
        if bool(row.get("fired")):
            fired_frames += 1
            if first_fire_ts is None:
                first_fire_ts = ts
        objs = row.get("objs")
        if isinstance(objs, list) and objs:
            object_rows += 1
        row_ttc = surface_margin.number(row.get("min_ttc"), f"min_ttc:{line_no}", problems)
        row_cpa = surface_margin.number(row.get("min_cpa"), f"min_cpa:{line_no}", problems)

        ttc_active = False
        cpa_active = False
        if row_ttc is not None and row_ttc < INVALID_TTC_SENTINEL:
            min_valid_ttc = row_ttc if min_valid_ttc is None else min(min_valid_ttc, row_ttc)
            ttc_margin = row_ttc - ttc_thresh
            if closest_ttc_margin is None or ttc_margin < closest_ttc_margin:
                closest_ttc_margin = ttc_margin
                closest_ttc_ts = ts
            ttc_active = row_ttc <= ttc_thresh
            if ttc_active:
                first_active_ttc_ts = first_min(first_active_ttc_ts, ts)
            elif 0 < ttc_margin <= TTC_NEAR_MARGIN_S:
                first_near_ttc_ts = first_min(first_near_ttc_ts, ts)
                pre_foreground_near_ttc = pre_foreground_near_ttc or ts < foreground_ts
        if row_cpa is not None:
            min_cpa = row_cpa if min_cpa is None else min(min_cpa, row_cpa)
            cpa_margin_delta = row_cpa - cpa_margin
            if closest_cpa_margin is None or cpa_margin_delta < closest_cpa_margin:
                closest_cpa_margin = cpa_margin_delta
                closest_cpa_ts = ts
            cpa_active = row_cpa <= cpa_margin
            if cpa_active:
                first_active_cpa_ts = first_min(first_active_cpa_ts, ts)
            elif 0 < cpa_margin_delta <= CPA_NEAR_MARGIN_M:
                first_near_cpa_ts = first_min(first_near_cpa_ts, ts)
                pre_foreground_near_cpa = pre_foreground_near_cpa or ts < foreground_ts
        if (ttc_active or cpa_active) and first_active_ts is None:
            first_active_ts = ts
            if ttc_active and cpa_active:
                first_active_channel = "both"
            elif ttc_active:
                first_active_channel = "ttc"
            else:
                first_active_channel = "cpa"

    if len(ttc_thresh_values) > 1:
        problems.append(f"ttc-thresh-varies:{sorted(ttc_thresh_values)}")
    if len(cpa_margin_values) > 1:
        problems.append(f"cpa-margin-varies:{sorted(cpa_margin_values)}")
    if monitor_frames == 0:
        problems.append("empty-decision-log")
    first_near_ts = min(ts for ts in (first_near_ttc_ts, first_near_cpa_ts) if ts is not None) if (
        first_near_ttc_ts is not None or first_near_cpa_ts is not None
    ) else None
    return {
        "monitor_frames": monitor_frames,
        "object_rows": object_rows,
        "fired_frames": fired_frames,
        "first_fire_ts": first_fire_ts,
        "first_near_ttc_ts": first_near_ttc_ts,
        "first_near_cpa_ts": first_near_cpa_ts,
        "first_near_ts": first_near_ts,
        "first_active_ttc_ts": first_active_ttc_ts,
        "first_active_cpa_ts": first_active_cpa_ts,
        "first_active_ts": first_active_ts,
        "first_active_channel": first_active_channel,
        "first_active_relation_to_foreground": relation_to_foreground(first_active_ts, foreground_ts),
        "first_active_offset_s": None if first_active_ts is None else first_active_ts - foreground_ts,
        "first_near_offset_s": None if first_near_ts is None else first_near_ts - foreground_ts,
        "pre_foreground_near_ttc": pre_foreground_near_ttc,
        "pre_foreground_near_cpa": pre_foreground_near_cpa,
        "pre_foreground_near_any": pre_foreground_near_ttc or pre_foreground_near_cpa,
        "min_valid_ttc_s": min_valid_ttc,
        "min_cpa_m": min_cpa,
        "closest_ttc_margin_s": closest_ttc_margin,
        "closest_ttc_ts": closest_ttc_ts,
        "closest_cpa_margin_m": closest_cpa_margin,
        "closest_cpa_ts": closest_cpa_ts,
        "ttc_thresh": next(iter(ttc_thresh_values)) if len(ttc_thresh_values) == 1 else None,
        "cpa_margin": next(iter(cpa_margin_values)) if len(cpa_margin_values) == 1 else None,
    }, problems


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter70_report: dict[str, Any],
    iter71_report: dict[str, Any],
    iter72_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter70": (iter70_report, ITER70_VERDICT),
        "iter71": (iter71_report, ITER71_VERDICT),
        "iter72": (iter72_report, ITER72_VERDICT),
    }
    for label, (report, verdict) in expected_verdicts.items():
        if report.get("verdict") != verdict:
            problems.append(f"{label}-verdict-not-{verdict}")
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")
    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter70_index = surface_margin.index_rows(iter70_report.get("episodes"), "iter70", problems)
    iter71_index = surface_margin.index_rows(iter71_report.get("episodes"), "iter71", problems)
    iter72_index = surface_margin.index_rows(iter72_report.get("episodes"), "iter72", problems)

    selected: list[dict[str, Any]] = []
    for audit_id, scenario, structural_label in FIXED_ROWS:
        key = (audit_id, scenario)
        row59 = iter59_index.get(key)
        row70 = iter70_index.get(key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{key}")
            continue
        if row70 is None:
            problems.append(f"missing-iter70-row:{key}")
            continue
        if row70.get("structural_label") != structural_label:
            problems.append(f"iter70-structural-label-mismatch:{key}:{row70.get('structural_label')}")
        if row70.get("problems"):
            problems.append(f"iter70-row-problems:{key}:{row70.get('problems')}")
        if structural_label == "foreground_present_surface_silent":
            row71 = iter71_index.get(key)
            if row71 is None:
                problems.append(f"missing-iter71-row:{key}")
            elif row71.get("row_label") != "surface_silent_far_margin":
                problems.append(f"iter71-label-mismatch:{key}:{row71.get('row_label')}")
        elif structural_label == "foreground_present_late_fire":
            row72 = iter72_index.get(key)
            if row72 is None:
                problems.append(f"missing-iter72-row:{key}")
            elif row72.get("row_label") not in {
                "late_fire_prefire_near_ttc_margin",
                "late_fire_prefire_near_cpa_margin",
            }:
                problems.append(f"iter72-label-mismatch:{key}:{row72.get('row_label')}")
        selected.append(row59)
    actual = [(row.get("audit_id"), row.get("scenario")) for row in selected]
    if actual != [(audit_id, scenario) for audit_id, scenario, _label in FIXED_ROWS]:
        problems.append(f"fixed-row-order-mismatch:{actual}")
    return selected, iter70_index, problems


def classify(row: dict[str, Any], row70: dict[str, Any], timeline: dict[str, Any], problems: list[str]) -> str:
    structural_label = row70.get("structural_label")
    relation = timeline.get("first_active_relation_to_foreground")
    if problems:
        return "margin_transition_insufficient"
    if structural_label == "foreground_present_surface_silent":
        if relation == "never":
            return "silent_far_never_active"
        if relation in {"before", "at"}:
            return "silent_active_before_contact_inconsistent"
        return "silent_active_after_contact_inconsistent"
    if structural_label == "foreground_present_late_fire":
        if relation in {"before", "at"}:
            return "late_active_before_contact_inconsistent"
        if relation == "never":
            return "late_no_postcontact_active_inconsistent"
        if timeline.get("pre_foreground_near_any"):
            return "late_prefire_near_postcontact_active"
        return "margin_transition_insufficient"
    return "margin_transition_insufficient"


def analyze_row(row: dict[str, Any], iter70_index: dict[tuple[str, str], dict[str, Any]]) -> dict[str, Any]:
    problems: list[str] = []
    key = surface_margin.row_key(row)
    row70 = iter70_index.get(key, {})
    first_foreground_ts = surface_margin.number(row.get("first_foreground_ts"), "first_foreground_ts", problems)
    episode_dir = row.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        timeline: dict[str, Any] = {}
    elif first_foreground_ts is None:
        problems.append("first-foreground-missing")
        timeline = {}
    else:
        timeline, timeline_problems = scan_full_timeline(
            Path(episode_dir) / "sentinel_iter48_decisions.jsonl",
            first_foreground_ts,
        )
        problems.extend(timeline_problems)
    row_label = classify(row, row70, timeline, problems)
    return {
        "audit_id": row.get("audit_id"),
        "scenario": row.get("scenario"),
        "structural_label": row70.get("structural_label"),
        "first_foreground_ts": row.get("first_foreground_ts"),
        "first_fire_ts": row.get("first_fire_ts"),
        "row_label": row_label,
        "timeline": timeline,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or len(rows) != len(FIXED_ROWS) or any(row.get("problems") for row in rows):
        return "HUGSIM_MARGIN_TRANSITION_BLOCKED"
    labels = [row.get("row_label") for row in rows]
    if labels.count("silent_far_never_active") == 2 and labels.count("late_prefire_near_postcontact_active") == 2:
        return "HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE"
    return "HUGSIM_MARGIN_TRANSITION_MIXED_COMPLETE"


def build_report(
    iter59_report_path: Path,
    iter70_report_path: Path,
    iter71_report_path: Path,
    iter72_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter70_report, problems70 = surface_margin.load_report(iter70_report_path, "iter70-report")
    iter71_report, problems71 = surface_margin.load_report(iter71_report_path, "iter71-report")
    iter72_report, problems72 = surface_margin.load_report(iter72_report_path, "iter72-report")
    infra_problems.extend(problems59 + problems70 + problems71 + problems72)
    selected_rows: list[dict[str, Any]] = []
    iter70_index: dict[tuple[str, str], dict[str, Any]] = {}
    if not infra_problems:
        selected_rows, iter70_index, source_problems = crosscheck_sources(
            iter59_report,
            iter70_report,
            iter71_report,
            iter72_report,
        )
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_row(row, iter70_index) for row in selected_rows]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 73,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter70_report": str(iter70_report_path),
            "iter71_report": str(iter71_report_path),
            "iter72_report": str(iter72_report_path),
        },
        "fixed_rows": [
            {"audit_id": audit_id, "scenario": scenario, "structural_label": label}
            for audit_id, scenario, label in FIXED_ROWS
        ],
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "target_rows": len(selected_rows),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "silent_far_never_active_rows": sum(row.get("row_label") == "silent_far_never_active" for row in rows),
            "late_prefire_near_postcontact_active_rows": sum(
                row.get("row_label") == "late_prefire_near_postcontact_active" for row in rows
            ),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "four-row descriptive margin-transition audit only; no actor-causality, repair, "
            "threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 73 - HUGSIM structural margin transition audit",
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
        "| audit id | scenario | structural | label | first near offset | first active offset | active channel | problems |",
        "|---|---|---|---|---:|---:|---|---|",
    ])
    for row in report["episodes"]:
        timeline = row["timeline"]
        lines.append(
            f"| `{row['audit_id']}` | `{row['scenario']}` | `{row['structural_label']}` | "
            f"`{row['row_label']}` | `{timeline.get('first_near_offset_s')}` | "
            f"`{timeline.get('first_active_offset_s')}` | `{timeline.get('first_active_channel')}` | "
            f"`{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter70_report: Path,
    iter71_report: Path,
    iter72_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter70_report, iter71_report, iter72_report)
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
        "--iter71-report",
        type=Path,
        default=Path("experiments/iter71_hugsim_surface_silent_margin_audit/proof-margin/margin_report.json"),
    )
    parser.add_argument(
        "--iter72-report",
        type=Path,
        default=Path("experiments/iter72_hugsim_late_fire_prefire_margin_audit/proof-prefire/prefire_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter73_hugsim_margin_transition_audit/proof-transition/transition_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter73_hugsim_margin_transition_audit/proof-transition/transition.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_report,
        args.iter70_report,
        args.iter71_report,
        args.iter72_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
