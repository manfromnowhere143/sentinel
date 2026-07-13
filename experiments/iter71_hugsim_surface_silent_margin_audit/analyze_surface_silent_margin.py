#!/usr/bin/env python3
"""Iteration 71 HUGSIM surface-silent margin audit."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER70_VERDICT = "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE"
FIXED_ROWS = (
    ("mixed_extreme", "scene-0062-extreme-00"),
    ("nofire_hard_control", "scene-0041-hard-00"),
)
TTC_NEAR_MARGIN_S = 1.0
CPA_NEAR_MARGIN_M = 1.5
INVALID_TTC_SENTINEL = 1e8


def load_report(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-{label}:{path}"]
    try:
        report = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"parse-{label}-failed:{exc}"]
    if not isinstance(report, dict):
        return {}, [f"{label}-not-dict"]
    return report, []


def row_key(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("audit_id")), str(row.get("scenario"))


def index_rows(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str], dict[str, Any]]:
    if not isinstance(rows, list):
        problems.append(f"{label}-rows-not-list")
        return {}
    out: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append(f"{label}-row-not-dict")
            continue
        key = row_key(row)
        if key in out:
            problems.append(f"{label}-duplicate-row:{key}")
            continue
        out[key] = row
    return out


def number(value: Any, field: str, problems: list[str]) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        problems.append(f"non-numeric-{field}:{value}")
        return None
    return float(value)


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
    iter59_index = index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter70_index = index_rows(iter70_report.get("episodes"), "iter70", problems)
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
        if row59.get("support_label") != "no_monitor_fire":
            problems.append(f"iter59-support-not-no-monitor-fire:{key}:{row59.get('support_label')}")
        if row70.get("structural_label") != "foreground_present_surface_silent":
            problems.append(f"iter70-structural-label-mismatch:{key}:{row70.get('structural_label')}")
        if row70.get("problems"):
            problems.append(f"iter70-row-problems:{key}:{row70.get('problems')}")
        rows.append(row59)
    actual_keys = [row_key(row) for row in rows]
    if actual_keys != list(FIXED_ROWS):
        problems.append(f"fixed-row-order-mismatch:{actual_keys}")
    return rows, iter70_index, problems


def scan_pre_foreground_log(path: Path, first_foreground_ts: float) -> tuple[dict[str, Any], list[str]]:
    problems: list[str] = []
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-decision-log:{path}"]
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        return {}, [f"read-decision-log-failed:{path}:{exc}"]

    frame_count = 0
    object_row_count = 0
    active_ttc_frames = 0
    active_cpa_frames = 0
    near_ttc_frames = 0
    near_cpa_frames = 0
    fired_frames = 0
    ttc_thresh_values: set[float] = set()
    cpa_margin_values: set[float] = set()
    min_ttc_raw: float | None = None
    min_valid_ttc: float | None = None
    min_cpa: float | None = None
    closest_ttc_margin: float | None = None
    closest_cpa_margin: float | None = None
    closest_ttc_ts: float | None = None
    closest_cpa_ts: float | None = None

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
        ts = number(row.get("ts", row.get("frame_index")), f"ts:{line_no}", problems)
        if ts is None or ts >= first_foreground_ts:
            continue
        params = row.get("params")
        if not isinstance(params, dict):
            problems.append(f"params-missing:{path}:{line_no}")
            continue
        ttc_thresh = number(params.get("ttc_thresh"), f"ttc_thresh:{line_no}", problems)
        cpa_margin = number(params.get("cpa_margin"), f"cpa_margin:{line_no}", problems)
        if ttc_thresh is None or cpa_margin is None:
            continue
        ttc_thresh_values.add(ttc_thresh)
        cpa_margin_values.add(cpa_margin)
        frame_count += 1
        fired_frames += int(bool(row.get("fired")))
        objs = row.get("objs")
        if isinstance(objs, list) and objs:
            object_row_count += 1
        min_ttc = number(row.get("min_ttc"), f"min_ttc:{line_no}", problems)
        min_cpa_row = number(row.get("min_cpa"), f"min_cpa:{line_no}", problems)
        if min_ttc is not None:
            min_ttc_raw = min_ttc if min_ttc_raw is None else min(min_ttc_raw, min_ttc)
            if min_ttc < INVALID_TTC_SENTINEL:
                min_valid_ttc = min_ttc if min_valid_ttc is None else min(min_valid_ttc, min_ttc)
                ttc_margin = min_ttc - ttc_thresh
                if closest_ttc_margin is None or ttc_margin < closest_ttc_margin:
                    closest_ttc_margin = ttc_margin
                    closest_ttc_ts = ts
                active_ttc_frames += int(min_ttc <= ttc_thresh)
                near_ttc_frames += int(0 < ttc_margin <= TTC_NEAR_MARGIN_S)
        if min_cpa_row is not None:
            min_cpa = min_cpa_row if min_cpa is None else min(min_cpa, min_cpa_row)
            cpa_margin_delta = min_cpa_row - cpa_margin
            if closest_cpa_margin is None or cpa_margin_delta < closest_cpa_margin:
                closest_cpa_margin = cpa_margin_delta
                closest_cpa_ts = ts
            active_cpa_frames += int(min_cpa_row <= cpa_margin)
            near_cpa_frames += int(0 < cpa_margin_delta <= CPA_NEAR_MARGIN_M)

    if len(ttc_thresh_values) > 1:
        problems.append(f"ttc-thresh-varies:{sorted(ttc_thresh_values)}")
    if len(cpa_margin_values) > 1:
        problems.append(f"cpa-margin-varies:{sorted(cpa_margin_values)}")
    if frame_count == 0:
        problems.append("no-pre-foreground-frames")
    return {
        "pre_foreground_monitor_frames": frame_count,
        "pre_foreground_object_rows": object_row_count,
        "pre_foreground_fired_frames": fired_frames,
        "ttc_thresh": next(iter(ttc_thresh_values)) if len(ttc_thresh_values) == 1 else None,
        "cpa_margin": next(iter(cpa_margin_values)) if len(cpa_margin_values) == 1 else None,
        "min_ttc_raw_s": min_ttc_raw,
        "min_valid_ttc_s": min_valid_ttc,
        "min_cpa_m": min_cpa,
        "closest_ttc_margin_s": closest_ttc_margin,
        "closest_ttc_ts": closest_ttc_ts,
        "closest_cpa_margin_m": closest_cpa_margin,
        "closest_cpa_ts": closest_cpa_ts,
        "active_ttc_frames": active_ttc_frames,
        "active_cpa_frames": active_cpa_frames,
        "near_ttc_frames": near_ttc_frames,
        "near_cpa_frames": near_cpa_frames,
    }, problems


def row_label(summary: dict[str, Any]) -> str:
    if int(summary.get("pre_foreground_object_rows") or 0) == 0:
        return "surface_silent_no_object_rows"
    if int(summary.get("active_ttc_frames") or 0) > 0 or int(summary.get("active_cpa_frames") or 0) > 0:
        return "surface_silent_active_crossing_inconsistent"
    if int(summary.get("near_ttc_frames") or 0) > 0:
        return "surface_silent_near_ttc_margin"
    if int(summary.get("near_cpa_frames") or 0) > 0:
        return "surface_silent_near_cpa_margin"
    return "surface_silent_far_margin"


def analyze_row(row: dict[str, Any]) -> dict[str, Any]:
    problems: list[str] = []
    first_foreground_ts = number(row.get("first_foreground_ts"), "first_foreground_ts", problems)
    episode_dir = row.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        summary: dict[str, Any] = {}
    elif first_foreground_ts is None:
        summary = {}
    else:
        summary, scan_problems = scan_pre_foreground_log(
            Path(episode_dir) / "sentinel_iter48_decisions.jsonl",
            first_foreground_ts,
        )
        problems.extend(scan_problems)
    if summary.get("pre_foreground_fired_frames"):
        problems.append(f"pre-foreground-fired-frames:{summary['pre_foreground_fired_frames']}")
    label = row_label(summary) if not problems else "surface_silent_active_crossing_inconsistent"
    return {
        "audit_id": row.get("audit_id"),
        "scenario": row.get("scenario"),
        "first_foreground_ts": row.get("first_foreground_ts"),
        "foreground_count": row.get("foreground_count"),
        "episode_dir": row.get("episode_dir"),
        "row_label": label,
        "summary": summary,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or len(rows) != len(FIXED_ROWS) or any(row.get("problems") for row in rows):
        return "HUGSIM_SURFACE_SILENT_MARGIN_BLOCKED"
    if any(row.get("row_label") == "surface_silent_active_crossing_inconsistent" for row in rows):
        return "HUGSIM_SURFACE_SILENT_ACTIVE_INCONSISTENT_BLOCKED"
    return "HUGSIM_SURFACE_SILENT_MARGIN_COMPLETE"


def build_report(iter59_report_path: Path, iter70_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = load_report(iter59_report_path, "iter59-report")
    iter70_report, problems70 = load_report(iter70_report_path, "iter70-report")
    infra_problems.extend(problems59)
    infra_problems.extend(problems70)
    selected_rows: list[dict[str, Any]] = []
    if not infra_problems:
        selected_rows, _iter70_index, source_problems = crosscheck_sources(iter59_report, iter70_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_row(row) for row in selected_rows]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 71,
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
                row.get("row_label") in {"surface_silent_near_ttc_margin", "surface_silent_near_cpa_margin"}
                for row in rows
            ),
            "far_margin_rows": sum(row.get("row_label") == "surface_silent_far_margin" for row in rows),
            "no_object_rows": sum(row.get("row_label") == "surface_silent_no_object_rows" for row in rows),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "two-row descriptive surface-silent margin audit only; no actor-causality, repair, "
            "threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 71 - HUGSIM surface-silent margin audit",
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
        "| audit id | scenario | label | min valid TTC | TTC margin | min CPA | CPA margin | problems |",
        "|---|---|---|---:|---:|---:|---:|---|",
    ])
    for row in report["episodes"]:
        summary = row["summary"]
        lines.append(
            f"| `{row['audit_id']}` | `{row['scenario']}` | `{row['row_label']}` | "
            f"`{summary.get('min_valid_ttc_s')}` | `{summary.get('closest_ttc_margin_s')}` | "
            f"`{summary.get('min_cpa_m')}` | `{summary.get('closest_cpa_margin_m')}` | "
            f"`{row.get('problems')}` |"
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
        default=Path("experiments/iter71_hugsim_surface_silent_margin_audit/proof-margin/margin_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter71_hugsim_surface_silent_margin_audit/proof-margin/margin.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter59_report, args.iter70_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
