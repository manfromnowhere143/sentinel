#!/usr/bin/env python3
"""Iteration 70 HUGSIM structural-row timing audit.

Runs offline over committed iteration-59 proof and the iteration-69 taxonomy.
No GPU, live box read, simulator mutation, threshold change, or retuning.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER69_VERDICT = "HUGSIM_MECHANISM_TAXONOMY_COMPLETE"
TIME_TOL = 1e-9
FIXED_STRUCTURAL_ROWS = (
    ("mixed_extreme", "scene-0062-extreme-00", "no_monitor_fire"),
    ("both_distinct_extreme", "scene-0138-extreme-00", "post_collision_fire"),
    ("nofire_hard_control", "scene-0041-hard-00", "no_monitor_fire"),
    ("cpa_medium_a", "scene-0071-medium-00", "background_collision_only"),
    ("ttc_medium_a", "scene-0071-medium-01", "post_collision_fire"),
)
STRUCTURAL_MECHANISMS = {
    "no_monitor_fire",
    "post_collision_fire",
    "background_collision_only",
}
EXPECTED_COMPLETE_LABELS = {
    "foreground_present_surface_silent",
    "foreground_present_late_fire",
    "foreground_absent_background_only",
}


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


def numeric_or_none(value: Any, field: str, problems: list[str]) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        problems.append(f"non-numeric-{field}:{value}")
        return None
    return float(value)


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


def predicate_channel(row: dict[str, Any]) -> str:
    params = row.get("params")
    if not isinstance(params, dict):
        return "unknown"
    ttc_thresh = params.get("ttc_thresh")
    cpa_margin = params.get("cpa_margin")
    min_ttc = row.get("min_ttc")
    min_cpa = row.get("min_cpa")
    if not all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in (ttc_thresh, cpa_margin)):
        return "unknown"
    ttc_cross = isinstance(min_ttc, (int, float)) and not isinstance(min_ttc, bool) and min_ttc <= ttc_thresh
    cpa_cross = isinstance(min_cpa, (int, float)) and not isinstance(min_cpa, bool) and min_cpa <= cpa_margin
    if ttc_cross and cpa_cross:
        return "both"
    if ttc_cross:
        return "ttc_only"
    if cpa_cross:
        return "cpa_only"
    return "unknown"


def read_decision_log(path: Path, first_foreground_ts: float | None) -> tuple[dict[str, Any], list[str]]:
    problems: list[str] = []
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-decision-log:{path}"]
    monitor_frames = 0
    fired_frames = 0
    brake_frames = 0
    first_fire_ts: float | None = None
    first_fire_channel = "no_fire"
    pre_or_at_foreground_fire_frames = 0
    min_ttc: float | None = None
    min_cpa: float | None = None
    object_rows = 0
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        return {}, [f"read-decision-log-failed:{path}:{exc}"]
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
        monitor_frames += 1
        ts = numeric_or_none(row.get("ts", row.get("frame_index")), f"decision-ts:{line_no}", problems)
        fired = bool(row.get("fired"))
        brake = bool(row.get("brake"))
        fired_frames += int(fired)
        brake_frames += int(brake)
        if fired and first_fire_ts is None:
            first_fire_ts = ts
            first_fire_channel = predicate_channel(row)
        if fired and first_foreground_ts is not None and ts is not None and ts <= first_foreground_ts + TIME_TOL:
            pre_or_at_foreground_fire_frames += 1
        row_ttc = row.get("min_ttc")
        if isinstance(row_ttc, (int, float)) and not isinstance(row_ttc, bool) and math.isfinite(row_ttc):
            min_ttc = float(row_ttc) if min_ttc is None else min(min_ttc, float(row_ttc))
        row_cpa = row.get("min_cpa")
        if isinstance(row_cpa, (int, float)) and not isinstance(row_cpa, bool) and math.isfinite(row_cpa):
            min_cpa = float(row_cpa) if min_cpa is None else min(min_cpa, float(row_cpa))
        objs = row.get("objs")
        if isinstance(objs, list) and objs:
            object_rows += 1
    if monitor_frames == 0:
        problems.append(f"empty-decision-log:{path}")
    return {
        "monitor_frames": monitor_frames,
        "fired_frames": fired_frames,
        "brake_frames": brake_frames,
        "first_fire_ts": first_fire_ts,
        "first_fire_channel": first_fire_channel,
        "pre_or_at_foreground_fire_frames": pre_or_at_foreground_fire_frames,
        "min_ttc": min_ttc,
        "min_cpa": min_cpa,
        "object_rows": object_rows,
    }, problems


def same_time(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return left is None and right is None
    if not isinstance(left, (int, float)) or isinstance(left, bool):
        return False
    if not isinstance(right, (int, float)) or isinstance(right, bool):
        return False
    return abs(float(left) - float(right)) <= TIME_TOL


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter69_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[tuple[str, str], dict[str, Any]], list[str]]:
    problems: list[str] = []
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter69_report.get("verdict") != ITER69_VERDICT:
        problems.append(f"iter69-verdict-not-{ITER69_VERDICT}")
    if iter59_report.get("infra_problems"):
        problems.append(f"iter59-infra-problems:{iter59_report.get('infra_problems')}")
    if iter69_report.get("infra_problems"):
        problems.append(f"iter69-infra-problems:{iter69_report.get('infra_problems')}")

    iter59_index = index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter69_index = index_rows(iter69_report.get("episodes"), "iter69", problems)
    selected: list[dict[str, Any]] = []
    for audit_id, scenario, support_label in FIXED_STRUCTURAL_ROWS:
        key = (audit_id, scenario)
        row59 = iter59_index.get(key)
        row69 = iter69_index.get(key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{key}")
            continue
        if row69 is None:
            problems.append(f"missing-iter69-row:{key}")
            continue
        if row59.get("support_label") != support_label:
            problems.append(f"iter59-support-mismatch:{key}:{row59.get('support_label')}!={support_label}")
        if row69.get("mechanism_label") != support_label:
            problems.append(f"iter69-mechanism-mismatch:{key}:{row69.get('mechanism_label')}!={support_label}")
        if row69.get("iter59_support_label") != support_label:
            problems.append(
                f"iter69-iter59-support-mismatch:{key}:{row69.get('iter59_support_label')}!={support_label}"
            )
        if support_label not in STRUCTURAL_MECHANISMS:
            problems.append(f"non-structural-fixed-label:{key}:{support_label}")
        selected.append(row59)
    actual_selected_keys = [(row.get("audit_id"), row.get("scenario"), row.get("support_label")) for row in selected]
    if actual_selected_keys != list(FIXED_STRUCTURAL_ROWS):
        problems.append(f"fixed-row-order-mismatch:{actual_selected_keys}")
    return selected, iter69_index, problems


def classify_structural(row: dict[str, Any], log_summary: dict[str, Any]) -> tuple[str, list[str]]:
    problems: list[str] = []
    support_label = str(row.get("support_label"))
    foreground_count = int(row.get("foreground_count") or 0)
    first_foreground_ts = row.get("first_foreground_ts")
    report_first_fire_ts = row.get("first_fire_ts")
    log_first_fire_ts = log_summary.get("first_fire_ts")
    pre_or_at_fire = int(log_summary.get("pre_or_at_foreground_fire_frames") or 0)

    if support_label == "no_monitor_fire":
        if foreground_count > 0 and first_foreground_ts is not None and log_summary.get("fired_frames") == 0:
            return "foreground_present_surface_silent", problems
        problems.append("no-monitor-fire-row-not-silent-foreground-present")
        return "structural_timing_inconsistent", problems
    if support_label == "post_collision_fire":
        if (
            foreground_count > 0
            and isinstance(first_foreground_ts, (int, float))
            and isinstance(report_first_fire_ts, (int, float))
            and isinstance(log_first_fire_ts, (int, float))
            and float(report_first_fire_ts) > float(first_foreground_ts) + TIME_TOL
            and float(log_first_fire_ts) > float(first_foreground_ts) + TIME_TOL
            and pre_or_at_fire == 0
        ):
            return "foreground_present_late_fire", problems
        problems.append("post-collision-fire-row-not-late-foreground-present")
        return "structural_timing_inconsistent", problems
    if support_label == "background_collision_only":
        if foreground_count == 0 and first_foreground_ts is None:
            return "foreground_absent_background_only", problems
        problems.append("background-row-has-foreground-provenance")
        return "structural_timing_inconsistent", problems
    problems.append(f"unexpected-support-label:{support_label}")
    return "structural_timing_inconsistent", problems


def analyze_row(row: dict[str, Any]) -> dict[str, Any]:
    row_problems: list[str] = []
    first_foreground_ts = numeric_or_none(row.get("first_foreground_ts"), "first_foreground_ts", row_problems)
    episode_dir = row.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        row_problems.append("episode-dir-missing")
        log_summary: dict[str, Any] = {}
    else:
        log_summary, log_problems = read_decision_log(Path(episode_dir) / "sentinel_iter48_decisions.jsonl", first_foreground_ts)
        row_problems.extend(log_problems)

    for field in ("monitor_frames", "fired_frames", "brake_frames"):
        if field in log_summary and row.get(field) != log_summary.get(field):
            row_problems.append(f"{field}-mismatch:{row.get(field)}!={log_summary.get(field)}")
    if log_summary and not same_time(row.get("first_fire_ts"), log_summary.get("first_fire_ts")):
        row_problems.append(f"first-fire-ts-mismatch:{row.get('first_fire_ts')}!={log_summary.get('first_fire_ts')}")
    if log_summary and row.get("first_fire_channel") != log_summary.get("first_fire_channel"):
        row_problems.append(
            f"first-fire-channel-mismatch:{row.get('first_fire_channel')}!={log_summary.get('first_fire_channel')}"
        )

    structural_label, label_problems = classify_structural(row, log_summary)
    row_problems.extend(label_problems)
    first_fire_ts = log_summary.get("first_fire_ts")
    fire_minus_foreground_s = None
    if isinstance(first_fire_ts, (int, float)) and isinstance(first_foreground_ts, (int, float)):
        fire_minus_foreground_s = float(first_fire_ts) - float(first_foreground_ts)
    return {
        "audit_id": row.get("audit_id"),
        "scenario": row.get("scenario"),
        "iter59_support_label": row.get("support_label"),
        "structural_label": structural_label,
        "episode_dir": row.get("episode_dir"),
        "report": {
            "first_fire_ts": row.get("first_fire_ts"),
            "first_fire_channel": row.get("first_fire_channel"),
            "fired_frames": row.get("fired_frames"),
            "brake_frames": row.get("brake_frames"),
            "first_foreground_ts": row.get("first_foreground_ts"),
            "foreground_count": row.get("foreground_count"),
            "monitor_frames": row.get("monitor_frames"),
            "monitor_object_id": row.get("monitor_object_id"),
            "monitor_provenance_label": row.get("monitor_provenance_label"),
        },
        "decision_log": log_summary,
        "fire_minus_foreground_s": fire_minus_foreground_s,
        "pre_or_at_foreground_fire": bool(log_summary.get("pre_or_at_foreground_fire_frames")),
        "problems": row_problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or len(rows) != len(FIXED_STRUCTURAL_ROWS):
        return "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_BLOCKED"
    if any(row.get("problems") for row in rows):
        return "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_BLOCKED"
    labels = {str(row.get("structural_label")) for row in rows}
    if "structural_timing_inconsistent" in labels:
        return "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_BLOCKED"
    if EXPECTED_COMPLETE_LABELS <= labels:
        return "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE"
    return "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_PARTIAL"


def build_report(iter59_report_path: Path, iter69_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = load_report(iter59_report_path, "iter59-report")
    iter69_report, problems69 = load_report(iter69_report_path, "iter69-report")
    infra_problems.extend(problems59)
    infra_problems.extend(problems69)
    selected_rows: list[dict[str, Any]] = []
    if not infra_problems:
        selected_rows, _iter69_index, source_problems = crosscheck_sources(iter59_report, iter69_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_row(row) for row in selected_rows]
    label_counts = Counter(row.get("structural_label") for row in rows)
    verdict = choose_verdict(rows, infra_problems)
    return {
        "iteration": 70,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter69_report": str(iter69_report_path),
        },
        "fixed_rows": [
            {"audit_id": audit_id, "scenario": scenario, "support_label": label}
            for audit_id, scenario, label in FIXED_STRUCTURAL_ROWS
        ],
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "target_rows": len(selected_rows),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "structural_label_counts": dict(sorted(label_counts.items())),
            "surface_silent_rows": sum(
                row.get("structural_label") == "foreground_present_surface_silent" for row in rows
            ),
            "late_fire_rows": sum(row.get("structural_label") == "foreground_present_late_fire" for row in rows),
            "background_only_rows": sum(
                row.get("structural_label") == "foreground_absent_background_only" for row in rows
            ),
        },
        "verdict": verdict,
        "claim_boundary": (
            "five-row structural timing/support audit only; no actor-causality, repair, transfer, "
            "safety, deployment, robustness, benchmark, population, HD-Score-invariance, "
            "commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 70 - HUGSIM structural-row timing audit",
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
        "| audit id | scenario | support | structural label | first foreground | first fire | delta | problems |",
        "|---|---|---|---|---:|---:|---:|---|",
    ])
    for row in report["episodes"]:
        report_fields = row["report"]
        lines.append(
            f"| `{row['audit_id']}` | `{row['scenario']}` | `{row['iter59_support_label']}` | "
            f"`{row['structural_label']}` | `{report_fields.get('first_foreground_ts')}` | "
            f"`{report_fields.get('first_fire_ts')}` | `{row.get('fire_minus_foreground_s')}` | "
            f"`{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter59_report: Path, iter69_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter59_report, iter69_report)
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
        "--iter69-report",
        type=Path,
        default=Path("experiments/iter69_hugsim_mechanism_taxonomy/proof-taxonomy/taxonomy_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter70_hugsim_structural_timing_audit/proof-structural/structural_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter70_hugsim_structural_timing_audit/proof-structural/structural.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter59_report, args.iter69_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
