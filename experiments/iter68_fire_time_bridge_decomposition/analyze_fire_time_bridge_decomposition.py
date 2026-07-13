#!/usr/bin/env python3
"""Iteration 68 fire-time bridge decomposition audit analyzer."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER61_VERDICT = "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE"
ITER64_VERDICT = "UNSUPPORTED_TEMPORAL_MATCH_COMPLETE"
ITER65_VERDICT = "TEMPORAL_ALIGNMENT_SUBTHRESHOLD_COMPLETE"
ITER66_VERDICT = "MATCHED_OBJECT_TIMELINE_MIXED_COMPLETE"
ITER67_VERDICT = "TRIGGER_TARGET_SAME_AND_SPLIT_COMPLETE"
EXPECTED_TARGETS = (
    {"audit_id": "ttc_extreme_short", "scenario": "scene-0038-extreme-00", "trigger_object_id": 2},
    {"audit_id": "cpa_medium_b", "scenario": "scene-0166-medium-00", "trigger_object_id": 1},
)
MATCH_DISTANCE_M = 3.0
AMBIGUOUS_DISTANCE_M = 6.0
TIME_TOL = 1e-9


def require_float(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f"non-numeric:{field}")
    return float(value)


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


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


def distance_label(distance: float | None) -> str:
    if distance is None:
        return "missing"
    if distance <= MATCH_DISTANCE_M:
        return "match"
    if distance <= AMBIGUOUS_DISTANCE_M:
        return "ambiguous"
    return "no_support"


def row_identity(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("audit_id")), str(row.get("scenario"))


def expected_rows() -> list[tuple[str, str]]:
    return [(target["audit_id"], target["scenario"]) for target in EXPECTED_TARGETS]


def crosscheck_reports(
    iter59_report: dict[str, Any],
    iter61_report: dict[str, Any],
    iter64_report: dict[str, Any],
    iter65_report: dict[str, Any],
    iter66_report: dict[str, Any],
    iter67_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected = expected_rows()
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter61_report.get("verdict") != ITER61_VERDICT:
        problems.append(f"iter61-verdict-not-{ITER61_VERDICT}")
    if iter64_report.get("verdict") != ITER64_VERDICT:
        problems.append(f"iter64-verdict-not-{ITER64_VERDICT}")
    if iter65_report.get("verdict") != ITER65_VERDICT:
        problems.append(f"iter65-verdict-not-{ITER65_VERDICT}")
    if iter66_report.get("verdict") != ITER66_VERDICT:
        problems.append(f"iter66-verdict-not-{ITER66_VERDICT}")
    if iter67_report.get("verdict") != ITER67_VERDICT:
        problems.append(f"iter67-verdict-not-{ITER67_VERDICT}")

    episodes61 = iter61_report.get("episodes")
    if isinstance(episodes61, list):
        rows61 = [
            row for row in episodes61
            if isinstance(row, dict) and row.get("row_label") == "no_monitor_object_support"
        ]
        identities61 = [row_identity(row) for row in rows61]
        if identities61 != expected:
            problems.append(f"iter61-no-support-identity-mismatch:{identities61}")
    else:
        problems.append("iter61-episodes-not-list")

    for label, report in (("iter64", iter64_report), ("iter65", iter65_report), ("iter66", iter66_report)):
        episodes = report.get("episodes")
        if not isinstance(episodes, list):
            problems.append(f"{label}-episodes-not-list")
            continue
        identities = [row_identity(row) for row in episodes if isinstance(row, dict)]
        if identities != expected:
            problems.append(f"{label}-identity-mismatch:{identities}")

    episodes67 = iter67_report.get("episodes")
    if not isinstance(episodes67, list):
        problems.append("iter67-episodes-not-list")
        return [], problems
    rows67 = [row for row in episodes67 if isinstance(row, dict)]
    identities67 = [row_identity(row) for row in rows67]
    if identities67 != expected:
        problems.append(f"iter67-identity-mismatch:{identities67}")
    for row, target in zip(rows67, EXPECTED_TARGETS, strict=False):
        if not same_object_id(row.get("trigger_object_id"), target["trigger_object_id"]):
            problems.append(f"iter67-trigger-mismatch:{row_identity(row)}:{row.get('trigger_object_id')}")
        for surface_name in ("trigger_surface", "first_fire_trigger_surface"):
            surface = row.get(surface_name)
            if not isinstance(surface, dict):
                problems.append(f"iter67-{surface_name}-missing:{row_identity(row)}")
            elif not isinstance(surface.get("best_variant"), dict):
                problems.append(f"iter67-{surface_name}-best-variant-missing:{row_identity(row)}")
    return rows67, problems


def compare_time(event_ts: float, reference_ts: float) -> str:
    if event_ts < reference_ts - TIME_TOL:
        return "before"
    if abs(event_ts - reference_ts) <= TIME_TOL:
        return "same"
    return "after"


def vector_delta(fire_variant: dict[str, Any], best_variant: dict[str, Any]) -> dict[str, Any]:
    fire_monitor = fire_variant.get("monitor_forward_lateral")
    best_monitor = best_variant.get("monitor_forward_lateral")
    fire_hugsim = fire_variant.get("hugsim_forward_lateral")
    best_hugsim = best_variant.get("hugsim_forward_lateral")
    out: dict[str, Any] = {}
    if isinstance(fire_monitor, list) and isinstance(best_monitor, list) and len(fire_monitor) >= 2 and len(best_monitor) >= 2:
        out["monitor_forward_delta"] = require_float(best_monitor[0], "best.monitor.forward") - require_float(
            fire_monitor[0],
            "fire.monitor.forward",
        )
        out["monitor_lateral_delta"] = require_float(best_monitor[1], "best.monitor.lateral") - require_float(
            fire_monitor[1],
            "fire.monitor.lateral",
        )
    if isinstance(fire_hugsim, list) and isinstance(best_hugsim, list) and len(fire_hugsim) >= 2 and len(best_hugsim) >= 2:
        out["hugsim_forward_delta"] = require_float(best_hugsim[0], "best.hugsim.forward") - require_float(
            fire_hugsim[0],
            "fire.hugsim.forward",
        )
        out["hugsim_lateral_delta"] = require_float(best_hugsim[1], "best.hugsim.lateral") - require_float(
            fire_hugsim[1],
            "fire.hugsim.lateral",
        )
    return out


def analyze_row(row: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {
        "audit_id": row.get("audit_id"),
        "scenario": row.get("scenario"),
        "trigger_object_id": row.get("trigger_object_id"),
        "problems": [],
    }
    trigger_surface = row.get("trigger_surface")
    fire_surface = row.get("first_fire_trigger_surface")
    if not isinstance(trigger_surface, dict) or not isinstance(fire_surface, dict):
        result["problems"].append("surface-missing")
        result["row_label"] = "fire_gap_decomposition_insufficient"
        return result
    trigger_best = trigger_surface.get("best_variant")
    fire_best = fire_surface.get("best_variant")
    if not isinstance(trigger_best, dict) or not isinstance(fire_best, dict):
        result["problems"].append("best-variant-missing")
        result["row_label"] = "fire_gap_decomposition_insufficient"
        return result

    first_fire_ts = require_float(row.get("first_fire_ts"), "first_fire_ts")
    full_distance = require_float(trigger_surface.get("best_distance_m"), "trigger.best_distance_m")
    fire_distance = require_float(fire_surface.get("best_distance_m"), "fire.best_distance_m")
    full_label = distance_label(full_distance)
    fire_label = distance_label(fire_distance)
    best_decision_ts = require_float(trigger_best.get("decision_ts"), "trigger.best.decision_ts")
    best_foreground_ts = require_float(trigger_best.get("foreground_timestamp"), "trigger.best.foreground_timestamp")
    fire_foreground_ts = require_float(fire_best.get("foreground_timestamp"), "fire.best.foreground_timestamp")
    relation = compare_time(best_decision_ts, first_fire_ts)

    if fire_label != "no_support":
        label = "fire_gap_decomposition_insufficient"
        result["problems"].append(f"first-fire-trigger-not-no-support:{fire_label}")
    elif full_label != "match":
        label = "fire_gap_no_full_window_match"
    elif relation == "before":
        label = "fire_gap_best_before_fire"
    elif relation == "after":
        label = "fire_gap_best_after_fire"
    else:
        label = "fire_gap_best_at_fire"

    result.update({
        "row_label": label,
        "first_fire_ts": first_fire_ts,
        "fire_time_distance_m": fire_distance,
        "fire_time_distance_label": fire_label,
        "full_window_best_distance_m": full_distance,
        "full_window_best_distance_label": full_label,
        "distance_improvement_m": fire_distance - full_distance,
        "best_decision_ts": best_decision_ts,
        "best_decision_relative_to_fire": relation,
        "decision_delta_s": best_decision_ts - first_fire_ts,
        "best_foreground_ts": best_foreground_ts,
        "fire_time_foreground_ts": fire_foreground_ts,
        "foreground_delta_s": best_foreground_ts - fire_foreground_ts,
        "best_temporal_source": trigger_best.get("temporal_source"),
        "fire_time_temporal_source": fire_best.get("temporal_source"),
        "best_lead_time_s": trigger_best.get("lead_time_s"),
        "fire_time_lead_time_s": fire_best.get("lead_time_s"),
        "trigger_best_variant": trigger_best,
        "fire_time_best_variant": fire_best,
        "vector_delta": vector_delta(fire_best, trigger_best),
    })
    return result


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or len(rows) != 2 or any(row.get("problems") for row in rows):
        return "FIRE_TIME_BRIDGE_DECOMPOSITION_BLOCKED"
    labels = [row.get("row_label") for row in rows]
    if any(label == "fire_gap_decomposition_insufficient" for label in labels):
        return "FIRE_TIME_BRIDGE_DECOMPOSITION_BLOCKED"
    if "fire_gap_best_before_fire" in labels and "fire_gap_best_after_fire" in labels:
        return "FIRE_TIME_BRIDGE_GAP_TEMPORAL_SPLIT_COMPLETE"
    if labels == ["fire_gap_best_before_fire", "fire_gap_best_before_fire"]:
        return "FIRE_TIME_BRIDGE_GAP_ALL_BEFORE_COMPLETE"
    if labels == ["fire_gap_best_after_fire", "fire_gap_best_after_fire"]:
        return "FIRE_TIME_BRIDGE_GAP_ALL_AFTER_COMPLETE"
    if labels == ["fire_gap_no_full_window_match", "fire_gap_no_full_window_match"]:
        return "FIRE_TIME_BRIDGE_GAP_NO_MATCH_COMPLETE"
    return "FIRE_TIME_BRIDGE_DECOMPOSITION_BLOCKED"


def build_report(
    iter59_report_path: Path,
    iter61_report_path: Path,
    iter64_report_path: Path,
    iter65_report_path: Path,
    iter66_report_path: Path,
    iter67_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = load_report(iter59_report_path, "iter59-report")
    iter61_report, problems61 = load_report(iter61_report_path, "iter61-report")
    iter64_report, problems64 = load_report(iter64_report_path, "iter64-report")
    iter65_report, problems65 = load_report(iter65_report_path, "iter65-report")
    iter66_report, problems66 = load_report(iter66_report_path, "iter66-report")
    iter67_report, problems67 = load_report(iter67_report_path, "iter67-report")
    infra_problems.extend(problems59)
    infra_problems.extend(problems61)
    infra_problems.extend(problems64)
    infra_problems.extend(problems65)
    infra_problems.extend(problems66)
    infra_problems.extend(problems67)
    iter67_rows: list[dict[str, Any]] = []
    if not infra_problems:
        iter67_rows, crosscheck_problems = crosscheck_reports(
            iter59_report,
            iter61_report,
            iter64_report,
            iter65_report,
            iter66_report,
            iter67_report,
        )
        infra_problems.extend(crosscheck_problems)

    rows = [] if infra_problems else [analyze_row(row) for row in iter67_rows]
    label_counts = Counter(row.get("row_label") for row in rows if row.get("row_label"))
    verdict = choose_verdict(rows, infra_problems)
    return {
        "iteration": 68,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter61_report": str(iter61_report_path),
            "iter64_report": str(iter64_report_path),
            "iter65_report": str(iter65_report_path),
            "iter66_report": str(iter66_report_path),
            "iter67_report": str(iter67_report_path),
        },
        "expected_targets": list(EXPECTED_TARGETS),
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "target_rows": len(iter67_rows),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "before_fire_rows": sum(row.get("row_label") == "fire_gap_best_before_fire" for row in rows),
            "after_fire_rows": sum(row.get("row_label") == "fire_gap_best_after_fire" for row in rows),
            "median_distance_improvement_m": (
                sorted(row["distance_improvement_m"] for row in rows if not row.get("problems"))[len(rows) // 2]
                if rows and all(not row.get("problems") for row in rows)
                else None
            ),
        },
        "verdict": verdict,
        "claim_boundary": (
            "two-row fire-time bridge decomposition audit only; no transfer, safety, deployment, "
            "benchmark, actor-causality, repair, population, HD-Score-invariance, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 68 - fire-time bridge decomposition audit",
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
    lines.extend(["", "## Rows", ""])
    for row in report["episodes"]:
        lines.append(
            f"- `{row['audit_id']}` / `{row['scenario']}` / trigger `{row.get('trigger_object_id')}`: "
            f"label `{row.get('row_label')}`, fire distance `{row.get('fire_time_distance_m')}`, "
            f"best distance `{row.get('full_window_best_distance_m')}`, best decision "
            f"`{row.get('best_decision_ts')}` ({row.get('best_decision_relative_to_fire')}), "
            f"improvement `{row.get('distance_improvement_m')}`, problems `{row.get('problems')}`"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter61_report: Path,
    iter64_report: Path,
    iter65_report: Path,
    iter66_report: Path,
    iter67_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter61_report, iter64_report, iter65_report, iter66_report, iter67_report)
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
        "--iter61-report",
        type=Path,
        default=Path("experiments/iter61_monitor_object_surface_audit/proof-object-surface/object_surface_report.json"),
    )
    parser.add_argument(
        "--iter64-report",
        type=Path,
        default=Path(
            "experiments/iter64_unsupported_temporal_surface_audit/proof-unsupported-temporal/"
            "unsupported_temporal_report.json"
        ),
    )
    parser.add_argument(
        "--iter65-report",
        type=Path,
        default=Path("experiments/iter65_temporal_alignment_audit/proof-alignment/temporal_alignment_report.json"),
    )
    parser.add_argument(
        "--iter66-report",
        type=Path,
        default=Path("experiments/iter66_matched_object_timeline_audit/proof-timeline/timeline_report.json"),
    )
    parser.add_argument(
        "--iter67-report",
        type=Path,
        default=Path("experiments/iter67_trigger_target_bridge_audit/proof-trigger-target/trigger_target_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter68_fire_time_bridge_decomposition/proof-fire-time/fire_time_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter68_fire_time_bridge_decomposition/proof-fire-time/fire_time.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_report,
        args.iter61_report,
        args.iter64_report,
        args.iter65_report,
        args.iter66_report,
        args.iter67_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
