#!/usr/bin/env python3
"""Iteration 75 HUGSIM cross-channel object handoff audit."""

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
ITER74_VERDICT = "HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE"
TIME_TOL = 1e-9
MATCH_TOL = 1e-6
TTC_NEAR_MARGIN_S = 1.0
CPA_NEAR_MARGIN_M = 1.5
FIXED_ROWS = (
    ("both_distinct_extreme", "scene-0138-extreme-00"),
    ("ttc_medium_a", "scene-0071-medium-01"),
)
BLOCKING_LABELS = {"cross_channel_object_handoff_insufficient", "cross_channel_source_inconsistent"}


def _load_module(relative_path: str, module_name: str) -> Any:
    repo = Path(__file__).resolve().parents[2]
    module_path = repo / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-module:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


surface_margin = _load_module(
    "experiments/iter71_hugsim_surface_silent_margin_audit/analyze_surface_silent_margin.py",
    "iter71_surface_silent_margin",
)
ITER62 = _load_module(
    "experiments/iter62_nontrigger_ranking_audit/analyze_nontrigger_ranking.py",
    "iter62_nontrigger_ranking",
)


def close(left: float, right: float, *, tol: float = MATCH_TOL) -> bool:
    return abs(left - right) <= tol * max(1.0, abs(left), abs(right))


def row_identity(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("audit_id")), str(row.get("scenario"))


def load_decision_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return [], [f"missing-decision-log:{path}"]
    rows: list[dict[str, Any]] = []
    problems: list[str] = []
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        return [], [f"read-decision-log-failed:{path}:{exc}"]
    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(f"bad-json-line:{line_no}:{exc}")
            continue
        if isinstance(row, dict) and "trace_error" not in row:
            rows.append(row)
    if not rows:
        problems.append("empty-decision-log")
    return rows, problems


def find_decision_row(rows: list[dict[str, Any]], ts: float, label: str, problems: list[str]) -> dict[str, Any] | None:
    matches: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        row_ts = surface_margin.number(row.get("ts", row.get("frame_index")), f"{label}.ts:{idx}", problems)
        if row_ts is not None and abs(row_ts - ts) <= TIME_TOL:
            matches.append(row)
    if len(matches) != 1:
        problems.append(f"{label}-row-count-{len(matches)}-for-ts-{ts}")
        return None
    return matches[0]


def channel_threshold(row: dict[str, Any], channel: str, problems: list[str]) -> float | None:
    params = row.get("params")
    if not isinstance(params, dict):
        problems.append("params-missing")
        return None
    key = "ttc_thresh" if channel == "ttc" else "cpa_margin"
    return surface_margin.number(params.get(key), key, problems)


def metric_value(metric: dict[str, Any], channel: str) -> float | None:
    value = metric.get("ttc") if channel == "ttc" else metric.get("min_cpa")
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        return None
    return float(value)


def logged_channel_value(row: dict[str, Any], channel: str, problems: list[str]) -> float | None:
    key = "min_ttc" if channel == "ttc" else "min_cpa"
    value = surface_margin.number(row.get(key), key, problems)
    if value is None or not math.isfinite(value):
        return None
    return value


def responsible_objects(
    row: dict[str, Any],
    channel: str,
    mode: str,
    label: str,
    problems: list[str],
) -> dict[str, Any]:
    threshold = channel_threshold(row, channel, problems)
    if threshold is None:
        return {"channel": channel, "object_ids": [], "problem": "threshold-missing"}
    try:
        metrics = ITER62.object_metrics(row)
    except (KeyError, TypeError, ValueError) as exc:
        problems.append(f"{label}-object-metrics-failed:{exc}")
        return {"channel": channel, "object_ids": [], "problem": str(exc)}

    valid_metrics = [(metric, metric_value(metric, channel)) for metric in metrics]
    valid_metrics = [(metric, value) for metric, value in valid_metrics if value is not None]
    if not valid_metrics:
        problems.append(f"{label}-{channel}-no-valid-object-metric")
        return {"channel": channel, "object_ids": [], "object_metrics": metrics}

    min_value = min(value for _metric, value in valid_metrics)
    object_metrics = [
        metric | {"channel_value": value}
        for metric, value in valid_metrics
        if close(value, min_value)
    ]
    object_ids = [metric.get("object_id") for metric in object_metrics]
    margin = min_value - threshold
    logged_value = logged_channel_value(row, channel, problems)
    if logged_value is not None and not close(logged_value, min_value):
        problems.append(f"{label}-{channel}-logged-min-mismatch:{logged_value}:{min_value}")
    if mode == "near":
        near_limit = TTC_NEAR_MARGIN_S if channel == "ttc" else CPA_NEAR_MARGIN_M
        if not (0 < margin <= near_limit):
            problems.append(f"{label}-{channel}-not-near-margin:{margin}")
    elif mode == "active":
        if min_value > threshold:
            problems.append(f"{label}-{channel}-not-active-margin:{margin}")
    else:
        problems.append(f"{label}-bad-mode:{mode}")
    return {
        "channel": channel,
        "mode": mode,
        "threshold": threshold,
        "min_value": min_value,
        "margin": margin,
        "object_ids": object_ids,
        "object_metrics": object_metrics,
    }


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter70_report: dict[str, Any],
    iter72_report: dict[str, Any],
    iter73_report: dict[str, Any],
    iter74_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter70": (iter70_report, ITER70_VERDICT),
        "iter72": (iter72_report, ITER72_VERDICT),
        "iter73": (iter73_report, ITER73_VERDICT),
        "iter74": (iter74_report, ITER74_VERDICT),
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
    iter74_index = surface_margin.index_rows(iter74_report.get("episodes"), "iter74", problems)

    selected: list[dict[str, Any]] = []
    for key in FIXED_ROWS:
        row59 = iter59_index.get(key)
        row70 = iter70_index.get(key)
        row72 = iter72_index.get(key)
        row73 = iter73_index.get(key)
        row74 = iter74_index.get(key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{key}")
            continue
        if row70 is None or row70.get("structural_label") != "foreground_present_late_fire":
            problems.append(f"iter70-late-fire-missing:{key}")
        if row72 is None or row72.get("row_label") not in {
            "late_fire_prefire_near_ttc_margin",
            "late_fire_prefire_near_cpa_margin",
        }:
            problems.append(f"iter72-near-row-missing:{key}")
        if row73 is None or row73.get("row_label") != "late_prefire_near_postcontact_active":
            problems.append(f"iter73-late-transition-missing:{key}")
        if row74 is None or row74.get("row_label") != "cross_channel_late_activation":
            problems.append(f"iter74-cross-channel-row-missing:{key}")
            continue
        selected.append({"iter59": row59, "iter74": row74})

    actual = [row_identity(item["iter59"]) for item in selected]
    if actual != list(FIXED_ROWS):
        problems.append(f"fixed-row-order-mismatch:{actual}")
    return selected, problems


def classify(pre_objects: dict[str, Any], active_objects: dict[str, Any], active_channels: list[str], problems: list[str]) -> str:
    if problems:
        return "cross_channel_object_handoff_insufficient"
    pre_ids = {str(object_id) for object_id in pre_objects.get("object_ids", [])}
    active_ids = {str(object_id) for object_id in active_objects.get("object_ids", [])}
    if not pre_ids or not active_ids:
        return "cross_channel_object_handoff_insufficient"
    if len(active_channels) != 1 or len(pre_ids) > 1 or len(active_ids) > 1:
        return "multiobject_cross_channel_handoff"
    if pre_ids == active_ids:
        return "same_object_cross_channel_handoff"
    return "object_switch_cross_channel_handoff"


def analyze_row(item: dict[str, Any]) -> dict[str, Any]:
    row59 = item["iter59"]
    row74 = item["iter74"]
    problems: list[str] = []
    timeline = row74.get("timeline")
    if not isinstance(timeline, dict):
        problems.append("iter74-timeline-missing")
        timeline = {}
    pre_channels = timeline.get("pre_foreground_near_channels")
    active_channels = timeline.get("first_active_channels")
    if not isinstance(pre_channels, list) or len(pre_channels) != 1:
        problems.append(f"pre-channel-count:{pre_channels}")
        pre_channel = None
    else:
        pre_channel = str(pre_channels[0])
    if not isinstance(active_channels, list) or len(active_channels) != 1:
        problems.append(f"active-channel-count:{active_channels}")
        active_channel = None
    else:
        active_channel = str(active_channels[0])
    if pre_channel == active_channel and pre_channel is not None:
        problems.append(f"not-cross-channel:{pre_channel}")

    pre_ts_key = f"closest_pre_{pre_channel}_ts" if pre_channel in {"ttc", "cpa"} else ""
    active_ts_key = f"first_active_{active_channel}_ts" if active_channel in {"ttc", "cpa"} else ""
    pre_ts = surface_margin.number(timeline.get(pre_ts_key), pre_ts_key or "pre_ts", problems) if pre_ts_key else None
    active_ts = (
        surface_margin.number(timeline.get(active_ts_key), active_ts_key or "active_ts", problems)
        if active_ts_key
        else None
    )

    episode_dir = row59.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        rows: list[dict[str, Any]] = []
    else:
        rows, read_problems = load_decision_rows(Path(episode_dir) / "sentinel_iter48_decisions.jsonl")
        problems.extend(read_problems)

    pre_row = find_decision_row(rows, pre_ts, "pre", problems) if pre_ts is not None else None
    active_row = find_decision_row(rows, active_ts, "active", problems) if active_ts is not None else None
    pre_objects: dict[str, Any] = {}
    active_objects: dict[str, Any] = {}
    if pre_row is not None and pre_channel is not None:
        pre_objects = responsible_objects(pre_row, pre_channel, "near", "pre", problems)
    if active_row is not None and active_channel is not None:
        active_objects = responsible_objects(active_row, active_channel, "active", "active", problems)

    row_label = classify(pre_objects, active_objects, list(active_channels or []), problems)
    return {
        "audit_id": row59.get("audit_id"),
        "scenario": row59.get("scenario"),
        "pre_channel": pre_channel,
        "pre_ts": pre_ts,
        "pre_objects": pre_objects,
        "active_channel": active_channel,
        "active_ts": active_ts,
        "active_objects": active_objects,
        "row_label": row_label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_ROWS)
        or any(row.get("problems") for row in rows)
        or any(label in BLOCKING_LABELS for label in labels)
    ):
        return "HUGSIM_CROSS_CHANNEL_OBJECT_HANDOFF_BLOCKED"
    if labels.count("object_switch_cross_channel_handoff") == len(FIXED_ROWS):
        return "HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE"
    if labels.count("same_object_cross_channel_handoff") == len(FIXED_ROWS):
        return "HUGSIM_CROSS_CHANNEL_SAME_OBJECT_COMPLETE"
    return "HUGSIM_CROSS_CHANNEL_OBJECT_HANDOFF_MIXED_COMPLETE"


def build_report(
    iter59_report_path: Path,
    iter70_report_path: Path,
    iter72_report_path: Path,
    iter73_report_path: Path,
    iter74_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter70_report, problems70 = surface_margin.load_report(iter70_report_path, "iter70-report")
    iter72_report, problems72 = surface_margin.load_report(iter72_report_path, "iter72-report")
    iter73_report, problems73 = surface_margin.load_report(iter73_report_path, "iter73-report")
    iter74_report, problems74 = surface_margin.load_report(iter74_report_path, "iter74-report")
    infra_problems.extend(problems59 + problems70 + problems72 + problems73 + problems74)

    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(
            iter59_report,
            iter70_report,
            iter72_report,
            iter73_report,
            iter74_report,
        )
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_row(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 75,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter70_report": str(iter70_report_path),
            "iter72_report": str(iter72_report_path),
            "iter73_report": str(iter73_report_path),
            "iter74_report": str(iter74_report_path),
        },
        "fixed_rows": [{"audit_id": audit_id, "scenario": scenario} for audit_id, scenario in FIXED_ROWS],
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "target_rows": len(selected),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "object_switch_rows": sum(row.get("row_label") == "object_switch_cross_channel_handoff" for row in rows),
            "same_object_rows": sum(row.get("row_label") == "same_object_cross_channel_handoff" for row in rows),
            "multiobject_rows": sum(row.get("row_label") == "multiobject_cross_channel_handoff" for row in rows),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "two-row descriptive object-handoff audit only; no actor-causality, repair, "
            "threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 75 - HUGSIM cross-channel object handoff audit",
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
        "| audit id | scenario | label | pre channel | pre ids | active channel | active ids | problems |",
        "|---|---|---|---|---|---|---|---|",
    ])
    for row in report["episodes"]:
        lines.append(
            f"| `{row['audit_id']}` | `{row['scenario']}` | `{row['row_label']}` | "
            f"`{row.get('pre_channel')}` | `{row.get('pre_objects', {}).get('object_ids')}` | "
            f"`{row.get('active_channel')}` | `{row.get('active_objects', {}).get('object_ids')}` | "
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
    iter74_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter70_report, iter72_report, iter73_report, iter74_report)
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
        "--iter74-report",
        type=Path,
        default=Path("experiments/iter74_hugsim_late_fire_delay_barrier/proof-delay/delay_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter75_hugsim_cross_channel_object_handoff/proof-handoff/handoff_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter75_hugsim_cross_channel_object_handoff/proof-handoff/handoff.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_report,
        args.iter70_report,
        args.iter72_report,
        args.iter73_report,
        args.iter74_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
