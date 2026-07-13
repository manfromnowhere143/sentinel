#!/usr/bin/env python3
"""Iteration 74 HUGSIM late-fire delay-barrier audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER70_VERDICT = "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE"
ITER72_VERDICT = "HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE"
ITER73_VERDICT = "HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE"
TIME_TOL = 1e-9
TTC_NEAR_MARGIN_S = 1.0
CPA_NEAR_MARGIN_M = 1.5
INVALID_TTC_SENTINEL = 1e8
FIXED_ROWS = (
    ("both_distinct_extreme", "scene-0138-extreme-00"),
    ("ttc_medium_a", "scene-0071-medium-01"),
)
INCONSISTENT_LABELS = {
    "preforeground_active_inconsistent",
    "no_preforeground_near_inconsistent",
    "missing_postcontact_active_inconsistent",
    "delay_barrier_insufficient",
}

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


def first_active_channels(first_ttc_ts: float | None, first_cpa_ts: float | None) -> tuple[float | None, list[str]]:
    candidates = [ts for ts in (first_ttc_ts, first_cpa_ts) if ts is not None]
    if not candidates:
        return None, []
    first_ts = min(candidates)
    channels: list[str] = []
    if first_ttc_ts is not None and abs(first_ttc_ts - first_ts) <= TIME_TOL:
        channels.append("ttc")
    if first_cpa_ts is not None and abs(first_cpa_ts - first_ts) <= TIME_TOL:
        channels.append("cpa")
    return first_ts, channels


def update_closest_positive(
    current_margin: float | None,
    current_ts: float | None,
    current_value: float | None,
    *,
    margin: float,
    ts: float,
    value: float,
) -> tuple[float | None, float | None, float | None]:
    if margin <= 0:
        return current_margin, current_ts, current_value
    if current_margin is None or margin < current_margin:
        return margin, ts, value
    return current_margin, current_ts, current_value


def scan_delay_barrier(path: Path, foreground_ts: float) -> tuple[dict[str, Any], list[str]]:
    problems: list[str] = []
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-decision-log:{path}"]
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        return {}, [f"read-decision-log-failed:{path}:{exc}"]

    monitor_frames = 0
    pre_foreground_frames = 0
    object_rows = 0
    pre_foreground_object_rows = 0
    fired_frames = 0
    first_fire_ts: float | None = None
    ttc_thresh_values: set[float] = set()
    cpa_margin_values: set[float] = set()
    first_active_ttc_ts: float | None = None
    first_active_cpa_ts: float | None = None
    pre_active_ttc = False
    pre_active_cpa = False
    pre_near_ttc = False
    pre_near_cpa = False
    closest_pre_ttc_margin: float | None = None
    closest_pre_ttc_ts: float | None = None
    closest_pre_ttc_value: float | None = None
    closest_pre_cpa_margin: float | None = None
    closest_pre_cpa_ts: float | None = None
    closest_pre_cpa_value: float | None = None

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
        is_pre_foreground = ts < foreground_ts
        if is_pre_foreground:
            pre_foreground_frames += 1
        if bool(row.get("fired")):
            fired_frames += 1
            first_fire_ts = first_min(first_fire_ts, ts)
        objs = row.get("objs")
        if isinstance(objs, list) and objs:
            object_rows += 1
            if is_pre_foreground:
                pre_foreground_object_rows += 1

        row_ttc = surface_margin.number(row.get("min_ttc"), f"min_ttc:{line_no}", problems)
        row_cpa = surface_margin.number(row.get("min_cpa"), f"min_cpa:{line_no}", problems)

        if row_ttc is not None and math.isfinite(row_ttc) and row_ttc < INVALID_TTC_SENTINEL:
            ttc_margin = row_ttc - ttc_thresh
            ttc_active = row_ttc <= ttc_thresh
            if ttc_active:
                first_active_ttc_ts = first_min(first_active_ttc_ts, ts)
                pre_active_ttc = pre_active_ttc or is_pre_foreground
            elif is_pre_foreground:
                if 0 < ttc_margin <= TTC_NEAR_MARGIN_S:
                    pre_near_ttc = True
                closest_pre_ttc_margin, closest_pre_ttc_ts, closest_pre_ttc_value = update_closest_positive(
                    closest_pre_ttc_margin,
                    closest_pre_ttc_ts,
                    closest_pre_ttc_value,
                    margin=ttc_margin,
                    ts=ts,
                    value=row_ttc,
                )
        if row_cpa is not None and math.isfinite(row_cpa):
            cpa_margin_delta = row_cpa - cpa_margin
            cpa_active = row_cpa <= cpa_margin
            if cpa_active:
                first_active_cpa_ts = first_min(first_active_cpa_ts, ts)
                pre_active_cpa = pre_active_cpa or is_pre_foreground
            elif is_pre_foreground:
                if 0 < cpa_margin_delta <= CPA_NEAR_MARGIN_M:
                    pre_near_cpa = True
                closest_pre_cpa_margin, closest_pre_cpa_ts, closest_pre_cpa_value = update_closest_positive(
                    closest_pre_cpa_margin,
                    closest_pre_cpa_ts,
                    closest_pre_cpa_value,
                    margin=cpa_margin_delta,
                    ts=ts,
                    value=row_cpa,
                )

    if len(ttc_thresh_values) > 1:
        problems.append(f"ttc-thresh-varies:{sorted(ttc_thresh_values)}")
    if len(cpa_margin_values) > 1:
        problems.append(f"cpa-margin-varies:{sorted(cpa_margin_values)}")
    if monitor_frames == 0:
        problems.append("empty-decision-log")

    first_active_ts, active_channels = first_active_channels(first_active_ttc_ts, first_active_cpa_ts)
    near_channels = []
    if pre_near_ttc:
        near_channels.append("ttc")
    if pre_near_cpa:
        near_channels.append("cpa")
    return {
        "monitor_frames": monitor_frames,
        "pre_foreground_frames": pre_foreground_frames,
        "object_rows": object_rows,
        "pre_foreground_object_rows": pre_foreground_object_rows,
        "fired_frames": fired_frames,
        "first_fire_ts": first_fire_ts,
        "pre_foreground_active_ttc": pre_active_ttc,
        "pre_foreground_active_cpa": pre_active_cpa,
        "pre_foreground_active_any": pre_active_ttc or pre_active_cpa,
        "pre_foreground_near_ttc": pre_near_ttc,
        "pre_foreground_near_cpa": pre_near_cpa,
        "pre_foreground_near_channels": near_channels,
        "closest_pre_ttc_margin_s": closest_pre_ttc_margin,
        "closest_pre_ttc_ts": closest_pre_ttc_ts,
        "closest_pre_ttc_value_s": closest_pre_ttc_value,
        "closest_pre_cpa_margin_m": closest_pre_cpa_margin,
        "closest_pre_cpa_ts": closest_pre_cpa_ts,
        "closest_pre_cpa_value_m": closest_pre_cpa_value,
        "first_active_ttc_ts": first_active_ttc_ts,
        "first_active_cpa_ts": first_active_cpa_ts,
        "first_active_ts": first_active_ts,
        "first_active_channels": active_channels,
        "first_active_relation_to_foreground": relation_to_foreground(first_active_ts, foreground_ts),
        "first_active_offset_s": None if first_active_ts is None else first_active_ts - foreground_ts,
        "ttc_thresh": next(iter(ttc_thresh_values)) if len(ttc_thresh_values) == 1 else None,
        "cpa_margin": next(iter(cpa_margin_values)) if len(cpa_margin_values) == 1 else None,
    }, problems


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter70_report: dict[str, Any],
    iter72_report: dict[str, Any],
    iter73_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter70": (iter70_report, ITER70_VERDICT),
        "iter72": (iter72_report, ITER72_VERDICT),
        "iter73": (iter73_report, ITER73_VERDICT),
    }
    for label, (report, verdict) in expected_verdicts.items():
        if report.get("verdict") != verdict:
            problems.append(f"{label}-verdict-not-{verdict}")
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter70_index = surface_margin.index_rows(iter70_report.get("episodes"), "iter70", problems)
    iter72_index = surface_margin.index_rows(iter72_report.get("episodes"), "iter72", problems)
    iter73_index = surface_margin.index_rows(iter73_report.get("episodes"), "iter73", problems)

    selected: list[dict[str, Any]] = []
    for audit_id, scenario in FIXED_ROWS:
        key = (audit_id, scenario)
        row59 = iter59_index.get(key)
        row70 = iter70_index.get(key)
        row72 = iter72_index.get(key)
        row73 = iter73_index.get(key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{key}")
            continue
        if row70 is None:
            problems.append(f"missing-iter70-row:{key}")
            continue
        if row72 is None:
            problems.append(f"missing-iter72-row:{key}")
            continue
        if row73 is None:
            problems.append(f"missing-iter73-row:{key}")
            continue
        if row70.get("structural_label") != "foreground_present_late_fire":
            problems.append(f"iter70-structural-label-mismatch:{key}:{row70.get('structural_label')}")
        if row70.get("problems"):
            problems.append(f"iter70-row-problems:{key}:{row70.get('problems')}")
        if row72.get("row_label") not in {
            "late_fire_prefire_near_ttc_margin",
            "late_fire_prefire_near_cpa_margin",
        }:
            problems.append(f"iter72-label-mismatch:{key}:{row72.get('row_label')}")
        if row73.get("row_label") != "late_prefire_near_postcontact_active":
            problems.append(f"iter73-label-mismatch:{key}:{row73.get('row_label')}")
        selected.append(row59)

    actual = [(row.get("audit_id"), row.get("scenario")) for row in selected]
    if actual != list(FIXED_ROWS):
        problems.append(f"fixed-row-order-mismatch:{actual}")
    return selected, problems


def classify(timeline: dict[str, Any], problems: list[str]) -> str:
    if problems:
        return "delay_barrier_insufficient"
    if timeline.get("pre_foreground_active_any"):
        return "preforeground_active_inconsistent"
    near_channels = set(timeline.get("pre_foreground_near_channels") or [])
    active_channels = set(timeline.get("first_active_channels") or [])
    if not near_channels:
        return "no_preforeground_near_inconsistent"
    if timeline.get("first_active_relation_to_foreground") != "after" or not active_channels:
        return "missing_postcontact_active_inconsistent"
    if len(near_channels) == 2:
        return "dual_near_late_activation"
    if near_channels & active_channels:
        return "same_channel_late_activation"
    if near_channels.isdisjoint(active_channels):
        return "cross_channel_late_activation"
    return "delay_barrier_insufficient"


def analyze_row(row: dict[str, Any]) -> dict[str, Any]:
    problems: list[str] = []
    first_foreground_ts = surface_margin.number(row.get("first_foreground_ts"), "first_foreground_ts", problems)
    episode_dir = row.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        timeline: dict[str, Any] = {}
    elif first_foreground_ts is None:
        problems.append("first-foreground-missing")
        timeline = {}
    else:
        timeline, timeline_problems = scan_delay_barrier(
            Path(episode_dir) / "sentinel_iter48_decisions.jsonl",
            first_foreground_ts,
        )
        problems.extend(timeline_problems)
    row_label = classify(timeline, problems)
    return {
        "audit_id": row.get("audit_id"),
        "scenario": row.get("scenario"),
        "first_foreground_ts": row.get("first_foreground_ts"),
        "first_fire_ts": row.get("first_fire_ts"),
        "row_label": row_label,
        "timeline": timeline,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_ROWS)
        or any(row.get("problems") for row in rows)
        or any(label in INCONSISTENT_LABELS for label in labels)
    ):
        return "HUGSIM_LATE_FIRE_DELAY_BLOCKED"
    if labels.count("cross_channel_late_activation") == len(FIXED_ROWS):
        return "HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE"
    return "HUGSIM_LATE_FIRE_DELAY_MIXED_COMPLETE"


def build_report(
    iter59_report_path: Path,
    iter70_report_path: Path,
    iter72_report_path: Path,
    iter73_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter70_report, problems70 = surface_margin.load_report(iter70_report_path, "iter70-report")
    iter72_report, problems72 = surface_margin.load_report(iter72_report_path, "iter72-report")
    iter73_report, problems73 = surface_margin.load_report(iter73_report_path, "iter73-report")
    infra_problems.extend(problems59 + problems70 + problems72 + problems73)

    selected_rows: list[dict[str, Any]] = []
    if not infra_problems:
        selected_rows, source_problems = crosscheck_sources(
            iter59_report,
            iter70_report,
            iter72_report,
            iter73_report,
        )
        infra_problems.extend(source_problems)

    rows = [] if infra_problems else [analyze_row(row) for row in selected_rows]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 74,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter70_report": str(iter70_report_path),
            "iter72_report": str(iter72_report_path),
            "iter73_report": str(iter73_report_path),
        },
        "fixed_rows": [{"audit_id": audit_id, "scenario": scenario} for audit_id, scenario in FIXED_ROWS],
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "target_rows": len(selected_rows),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "cross_channel_late_activation_rows": sum(
                row.get("row_label") == "cross_channel_late_activation" for row in rows
            ),
            "same_channel_late_activation_rows": sum(
                row.get("row_label") == "same_channel_late_activation" for row in rows
            ),
            "dual_near_late_activation_rows": sum(
                row.get("row_label") == "dual_near_late_activation" for row in rows
            ),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "two-row descriptive delay-barrier audit only; no actor-causality, repair, "
            "threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 74 - HUGSIM late-fire delay barrier audit",
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
        (
            "| audit id | scenario | label | pre near channels | first active channels | "
            "first active offset | closest pre TTC margin | closest pre CPA margin | problems |"
        ),
        "|---|---|---|---|---|---:|---:|---:|---|",
    ])
    for row in report["episodes"]:
        timeline = row["timeline"]
        lines.append(
            f"| `{row['audit_id']}` | `{row['scenario']}` | `{row['row_label']}` | "
            f"`{timeline.get('pre_foreground_near_channels')}` | "
            f"`{timeline.get('first_active_channels')}` | "
            f"`{timeline.get('first_active_offset_s')}` | "
            f"`{timeline.get('closest_pre_ttc_margin_s')}` | "
            f"`{timeline.get('closest_pre_cpa_margin_m')}` | "
            f"`{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter70_report: Path,
    iter72_report: Path,
    iter73_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter70_report, iter72_report, iter73_report)
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
        "--iter72-report",
        type=Path,
        default=Path("experiments/iter72_hugsim_late_fire_prefire_margin_audit/proof-prefire/prefire_report.json"),
    )
    parser.add_argument(
        "--iter73-report",
        type=Path,
        default=Path("experiments/iter73_hugsim_margin_transition_audit/proof-transition/transition_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter74_hugsim_late_fire_delay_barrier/proof-delay/delay_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter74_hugsim_late_fire_delay_barrier/proof-delay/delay.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_report,
        args.iter70_report,
        args.iter72_report,
        args.iter73_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
