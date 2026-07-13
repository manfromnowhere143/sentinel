#!/usr/bin/env python3
"""Iteration 78 HUGSIM support-object ranking audit."""

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
ITER75_VERDICT = "HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE"
ITER76_VERDICT = "HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE"
ITER77_VERDICT = "HUGSIM_EVENT_SET_FOREGROUND_SUPPORT_MIXED_COMPLETE"
CPA_BORDERLINE_M = 3.0
TTC_BORDERLINE_S = 5.0
FIXED_EVENTS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "role": "pre",
        "object_id": 9,
        "iter77_row_label": "pre_set_foreground_ambiguous",
        "support_band": "ambiguous",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "pre",
        "object_id": 10,
        "iter77_row_label": "both_sets_foreground_match",
        "support_band": "match",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "active",
        "object_id": 10,
        "iter77_row_label": "both_sets_foreground_match",
        "support_band": "match",
    },
)


def _load_module(relative_path: str, module_name: str) -> Any:
    repo = Path(__file__).resolve().parents[2]
    module_path = repo / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-module:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SWITCH = _load_module(
    "experiments/iter76_hugsim_switch_foreground_bridge/analyze_switch_foreground_bridge.py",
    "iter76_switch_foreground_bridge",
)
ITER62 = _load_module(
    "experiments/iter62_nontrigger_ranking_audit/analyze_nontrigger_ranking.py",
    "iter62_nontrigger_ranking",
)
surface_margin = SWITCH.surface_margin


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def channel_thresholds(row: dict[str, Any], problems: list[str]) -> tuple[float | None, float | None]:
    params = row.get("params")
    if not isinstance(params, dict):
        problems.append("params-missing")
        return None, None
    cpa_margin = surface_margin.number(params.get("cpa_margin"), "cpa_margin", problems)
    ttc_thresh = surface_margin.number(params.get("ttc_thresh"), "ttc_thresh", problems)
    return cpa_margin, ttc_thresh


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter70_report: dict[str, Any],
    iter72_report: dict[str, Any],
    iter73_report: dict[str, Any],
    iter74_report: dict[str, Any],
    iter75_report: dict[str, Any],
    iter76_report: dict[str, Any],
    iter77_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter70": (iter70_report, ITER70_VERDICT),
        "iter72": (iter72_report, ITER72_VERDICT),
        "iter73": (iter73_report, ITER73_VERDICT),
        "iter74": (iter74_report, ITER74_VERDICT),
        "iter75": (iter75_report, ITER75_VERDICT),
        "iter76": (iter76_report, ITER76_VERDICT),
        "iter77": (iter77_report, ITER77_VERDICT),
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
    iter75_index = surface_margin.index_rows(iter75_report.get("episodes"), "iter75", problems)
    iter76_index = surface_margin.index_rows(iter76_report.get("episodes"), "iter76", problems)
    iter77_index = surface_margin.index_rows(iter77_report.get("episodes"), "iter77", problems)

    selected: list[dict[str, Any]] = []
    for event in FIXED_EVENTS:
        key = (event["audit_id"], event["scenario"])
        row59 = iter59_index.get(key)
        row70 = iter70_index.get(key)
        row72 = iter72_index.get(key)
        row73 = iter73_index.get(key)
        row74 = iter74_index.get(key)
        row75 = iter75_index.get(key)
        row76 = iter76_index.get(key)
        row77 = iter77_index.get(key)
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
        if row75 is None or row75.get("row_label") != "object_switch_cross_channel_handoff":
            problems.append(f"iter75-object-switch-row-missing:{key}")
        if row76 is None or row76.get("row_label") != "no_foreground_bridge_support":
            problems.append(f"iter76-no-support-row-missing:{key}")
        if row77 is None or row77.get("row_label") != event["iter77_row_label"]:
            problems.append(f"iter77-row-label-mismatch:{key}:{None if row77 is None else row77.get('row_label')}")
            continue
        event_set = row77.get(f"{event['role']}_event_set")
        if not isinstance(event_set, dict):
            problems.append(f"iter77-event-set-missing:{key}:{event['role']}")
            continue
        best = event_set.get("best_variant")
        if not isinstance(best, dict):
            problems.append(f"iter77-best-variant-missing:{key}:{event['role']}")
            continue
        if not same_object_id(best.get("object_id"), event["object_id"]):
            problems.append(f"iter77-object-mismatch:{key}:{event['role']}:{best.get('object_id')}")
        if event_set.get("distance_band") != event["support_band"]:
            problems.append(f"iter77-band-mismatch:{key}:{event['role']}:{event_set.get('distance_band')}")
        selected.append({"event": event, "iter59": row59, "iter75": row75, "iter77": row77})
    if len(selected) != len(FIXED_EVENTS):
        problems.append(f"fixed-event-count-mismatch:{len(selected)}")
    return selected, problems


def selected_object_id(row75: dict[str, Any], role: str, problems: list[str]) -> Any:
    event_objects = row75.get(f"{role}_objects")
    if not isinstance(event_objects, dict) or not isinstance(event_objects.get("object_ids"), list):
        problems.append(f"{role}-selected-objects-missing")
        return None
    object_ids = event_objects["object_ids"]
    if len(object_ids) != 1:
        problems.append(f"{role}-selected-object-count:{object_ids}")
        return None
    return object_ids[0]


def classify(is_selected: bool, active: bool, borderline: bool, problems: list[str]) -> str:
    if problems:
        return "support_object_ranking_insufficient"
    if is_selected and active:
        return "support_object_selected_active"
    if is_selected:
        return "support_object_selected_subthreshold"
    if active:
        return "support_object_nonselected_active"
    if borderline:
        return "support_object_nonselected_borderline"
    return "support_object_nonselected_subthreshold"


def analyze_event(item: dict[str, Any]) -> dict[str, Any]:
    event = item["event"]
    row59 = item["iter59"]
    row75 = item["iter75"]
    row77 = item["iter77"]
    problems: list[str] = []
    role = str(event["role"])
    event_set = row77.get(f"{role}_event_set")
    event_ts = surface_margin.number(event_set.get("event_ts") if isinstance(event_set, dict) else None, "event_ts", problems)
    episode_dir = row59.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        rows: list[dict[str, Any]] = []
    else:
        rows, row_problems = SWITCH.load_decision_rows(Path(episode_dir) / "sentinel_iter48_decisions.jsonl")
        problems.extend(row_problems)
    event_row = SWITCH.find_decision_row(rows, event_ts, role, problems) if event_ts is not None else None
    metric: dict[str, Any] | None = None
    object_metrics: list[dict[str, Any]] = []
    cpa_margin: float | None = None
    ttc_thresh: float | None = None
    if event_row is not None:
        cpa_margin, ttc_thresh = channel_thresholds(event_row, problems)
        try:
            object_metrics = ITER62.object_metrics(event_row)
        except (KeyError, TypeError, ValueError) as exc:
            problems.append(f"object-metrics-failed:{exc}")
        matches = [row for row in object_metrics if same_object_id(row.get("object_id"), event["object_id"])]
        if len(matches) != 1:
            problems.append(f"support-object-count-{len(matches)}:{event['object_id']}")
        else:
            metric = matches[0]
    selected_id = selected_object_id(row75, role, problems)
    is_selected = selected_id is not None and same_object_id(selected_id, event["object_id"])
    active = False
    borderline = False
    if metric is not None and cpa_margin is not None and ttc_thresh is not None:
        min_cpa = metric.get("min_cpa")
        ttc = metric.get("ttc")
        cpa_active = isinstance(min_cpa, (int, float)) and not isinstance(min_cpa, bool) and min_cpa <= cpa_margin
        ttc_active = isinstance(ttc, (int, float)) and not isinstance(ttc, bool) and math.isfinite(ttc) and ttc <= ttc_thresh
        active = bool(cpa_active or ttc_active)
        cpa_borderline = (
            isinstance(min_cpa, (int, float))
            and not isinstance(min_cpa, bool)
            and not cpa_active
            and min_cpa <= CPA_BORDERLINE_M
        )
        ttc_borderline = (
            isinstance(ttc, (int, float))
            and not isinstance(ttc, bool)
            and math.isfinite(ttc)
            and not ttc_active
            and ttc <= TTC_BORDERLINE_S
        )
        borderline = bool(cpa_borderline or ttc_borderline)
        metric = metric | {
            "cpa_active_logged_threshold": cpa_active,
            "ttc_active_logged_threshold": ttc_active,
            "cpa_borderline_registered": cpa_borderline,
            "ttc_borderline_registered": ttc_borderline,
        }
    row_label = classify(is_selected, active, borderline, problems)
    return {
        "audit_id": event["audit_id"],
        "scenario": event["scenario"],
        "event_role": role,
        "event_ts": event_ts,
        "support_object_id": event["object_id"],
        "support_band": event["support_band"],
        "selected_object_id": selected_id,
        "is_selected_object": is_selected,
        "object_count": len(object_metrics),
        "support_object_metric": metric,
        "row_label": row_label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_EVENTS)
        or any(row.get("problems") for row in rows)
        or "support_object_ranking_insufficient" in labels
    ):
        return "HUGSIM_SUPPORT_OBJECT_RANKING_BLOCKED"
    if "support_object_nonselected_active" in labels:
        return "HUGSIM_SUPPORT_OBJECT_NONSELECTED_ACTIVE_COMPLETE"
    if "support_object_nonselected_borderline" in labels:
        return "HUGSIM_SUPPORT_OBJECT_NONSELECTED_BORDERLINE_COMPLETE"
    return "HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE"


def build_report(
    iter59_report_path: Path,
    iter70_report_path: Path,
    iter72_report_path: Path,
    iter73_report_path: Path,
    iter74_report_path: Path,
    iter75_report_path: Path,
    iter76_report_path: Path,
    iter77_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter70_report, problems70 = surface_margin.load_report(iter70_report_path, "iter70-report")
    iter72_report, problems72 = surface_margin.load_report(iter72_report_path, "iter72-report")
    iter73_report, problems73 = surface_margin.load_report(iter73_report_path, "iter73-report")
    iter74_report, problems74 = surface_margin.load_report(iter74_report_path, "iter74-report")
    iter75_report, problems75 = surface_margin.load_report(iter75_report_path, "iter75-report")
    iter76_report, problems76 = surface_margin.load_report(iter76_report_path, "iter76-report")
    iter77_report, problems77 = surface_margin.load_report(iter77_report_path, "iter77-report")
    infra_problems.extend(
        problems59
        + problems70
        + problems72
        + problems73
        + problems74
        + problems75
        + problems76
        + problems77
    )
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(
            iter59_report,
            iter70_report,
            iter72_report,
            iter73_report,
            iter74_report,
            iter75_report,
            iter76_report,
            iter77_report,
        )
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_event(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 78,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter70_report": str(iter70_report_path),
            "iter72_report": str(iter72_report_path),
            "iter73_report": str(iter73_report_path),
            "iter74_report": str(iter74_report_path),
            "iter75_report": str(iter75_report_path),
            "iter76_report": str(iter76_report_path),
            "iter77_report": str(iter77_report_path),
        },
        "fixed_events": list(FIXED_EVENTS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_events": len(selected),
            "evaluated_events": sum(not row.get("problems") for row in rows),
            "event_label_counts": dict(sorted(label_counts.items())),
            "nonselected_active_events": sum(
                row.get("row_label") == "support_object_nonselected_active" for row in rows
            ),
            "nonselected_borderline_events": sum(
                row.get("row_label") == "support_object_nonselected_borderline" for row in rows
            ),
            "selected_events": sum(bool(row.get("is_selected_object")) for row in rows),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "three-event descriptive support-object ranking audit only; no actor-causality, repair, "
            "threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 78 - HUGSIM support-object ranking audit",
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
        "## Events",
        "",
        "| audit id | event | support id | selected id | label | cpa rank | ttc rank | min cpa | ttc | problems |",
        "|---|---|---:|---:|---|---:|---:|---:|---:|---|",
    ])
    for row in report["events"]:
        metric = row.get("support_object_metric") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{row['support_object_id']}` | "
            f"`{row.get('selected_object_id')}` | `{row['row_label']}` | "
            f"`{metric.get('cpa_rank')}` | `{metric.get('ttc_rank')}` | "
            f"`{metric.get('min_cpa')}` | `{metric.get('ttc')}` | `{row.get('problems')}` |"
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
    iter75_report: Path,
    iter76_report: Path,
    iter77_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(
        iter59_report,
        iter70_report,
        iter72_report,
        iter73_report,
        iter74_report,
        iter75_report,
        iter76_report,
        iter77_report,
    )
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
        "--iter75-report",
        type=Path,
        default=Path("experiments/iter75_hugsim_cross_channel_object_handoff/proof-handoff/handoff_report.json"),
    )
    parser.add_argument(
        "--iter76-report",
        type=Path,
        default=Path("experiments/iter76_hugsim_switch_foreground_bridge/proof-bridge/bridge_report.json"),
    )
    parser.add_argument(
        "--iter77-report",
        type=Path,
        default=Path("experiments/iter77_hugsim_event_object_set_bridge/proof-set/set_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter78_hugsim_support_object_ranking/proof-ranking/ranking_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter78_hugsim_support_object_ranking/proof-ranking/ranking.md"),
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
        args.iter75_report,
        args.iter76_report,
        args.iter77_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
