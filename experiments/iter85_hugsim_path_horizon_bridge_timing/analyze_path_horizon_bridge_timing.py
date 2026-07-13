#!/usr/bin/env python3
"""Iteration 85 HUGSIM path-horizon/provenance-timing decomposition."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER80_VERDICT = "HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE"
ITER83_VERDICT = "HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE"
ITER84_VERDICT = "HUGSIM_SELECTED_SURFACE_SUPPORT_BRIDGE_SPLIT_COMPLETE"
SUPPORTED_BANDS = {"match", "ambiguous"}
FIXED_EVENTS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "role": "pre",
        "event_ts": 5.0,
        "selected_object_id": 5,
        "support_object_id": 9,
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "pre",
        "event_ts": 2.5,
        "selected_object_id": 6,
        "support_object_id": 10,
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "active",
        "event_ts": 5.0,
        "selected_object_id": 24,
        "support_object_id": 10,
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


ITER84 = _load_module(
    "experiments/iter84_hugsim_selected_support_arbitration/"
    "analyze_selected_support_arbitration.py",
    "iter84_selected_support_arbitration",
)
ITER80 = ITER84.ITER80
ITER83 = ITER84.ITER83
SWITCH = ITER84.SWITCH
surface_margin = ITER84.surface_margin


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def rank_better(left: Any, right: Any) -> bool:
    return finite_number(left) and finite_number(right) and float(left) < float(right)


def bridge_supported(bridge: dict[str, Any]) -> bool:
    return bridge.get("distance_band") in SUPPORTED_BANDS


def bridge_rank(bridge: dict[str, Any]) -> int:
    return {"missing": -1, "no_support": 0, "ambiguous": 1, "match": 2}.get(str(bridge.get("distance_band")), -1)


def event_index(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return ITER84.event_index(rows, label, problems)


def object_index(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str], dict[str, Any]]:
    return ITER84.object_index(rows, label, problems)


def compact_metric(metric: dict[str, Any] | None) -> dict[str, Any] | None:
    if metric is None:
        return None
    keys = (
        "object_id",
        "state",
        "min_cpa",
        "cpa_rank",
        "cpa_horizon_index",
        "cpa_horizon_time_s",
        "cpa_horizon_offset_s",
        "cpa_horizon_global_ts",
        "ttc",
        "ttc_rank",
        "gap",
        "closing",
        "score",
        "active_cpa_margin_m",
        "active_ttc_margin_s",
        "borderline_cpa_margin_m",
        "borderline_ttc_margin_s",
        "cpa_active_logged_threshold",
        "ttc_active_logged_threshold",
        "cpa_borderline_registered",
        "ttc_borderline_registered",
    )
    return {key: metric.get(key) for key in keys}


def bridge_timing(bridge: dict[str, Any]) -> dict[str, Any]:
    best = bridge.get("best_variant")
    event_ts = bridge.get("event_ts")
    if not isinstance(best, dict):
        return {
            "provenance_timestamp": None,
            "provenance_event_offset_s": None,
            "provenance_lead_time_s": None,
            "temporal_source": None,
            "timing_label": "no_provenance_timing",
        }
    timestamp = best.get("foreground_timestamp")
    offset = None
    if finite_number(timestamp) and finite_number(event_ts):
        offset = float(timestamp) - float(event_ts)
    if offset is None:
        timing_label = "no_provenance_timing"
    elif offset > 0:
        timing_label = "provenance_after_event"
    elif offset < 0:
        timing_label = "provenance_before_event"
    else:
        timing_label = "provenance_at_event"
    return {
        "provenance_timestamp": timestamp if finite_number(timestamp) else None,
        "provenance_event_offset_s": offset,
        "provenance_lead_time_s": best.get("lead_time_s"),
        "temporal_source": best.get("temporal_source"),
        "timing_label": timing_label,
    }


def compact_bridge(bridge: dict[str, Any]) -> dict[str, Any]:
    compact = ITER84.compact_bridge(bridge)
    return compact | bridge_timing(bridge)


def object_bridge(
    event_row: dict[str, Any],
    event_ts: float,
    obj: dict[str, Any],
    role: str,
    provenance_rows: list[dict[str, Any]],
    problems: list[str],
) -> dict[str, Any]:
    return ITER84.object_bridge(event_row, event_ts, obj, role, provenance_rows, problems)


def add_horizon_timing(
    metric: dict[str, Any] | None,
    event_row: dict[str, Any],
    event_ts: float,
    role: str,
    problems: list[str],
) -> dict[str, Any] | None:
    if metric is None:
        return None
    params = event_row.get("params")
    if not isinstance(params, dict):
        problems.append(f"{role}-params-not-dict")
        return metric
    dt = surface_margin.number(params.get("dt"), f"{role}.params.dt", problems)
    cpa_horizon_index = metric.get("cpa_horizon_index")
    if dt is None or not finite_number(cpa_horizon_index):
        problems.append(f"{role}-cpa-horizon-timing-missing:{metric.get('object_id')}")
        return metric
    horizon_time = float(cpa_horizon_index) * float(dt)
    metric["cpa_horizon_time_s"] = horizon_time
    metric["cpa_horizon_offset_s"] = horizon_time - event_ts
    metric["cpa_horizon_global_ts"] = event_ts + horizon_time
    return metric


def metric_with_horizon_timing(
    event_row: dict[str, Any],
    object_id: Any,
    event_ts: float,
    role: str,
    problems: list[str],
) -> dict[str, Any] | None:
    metric = ITER83.metric_with_margins(event_row, object_id, problems)
    return add_horizon_timing(metric, event_row, event_ts, role, problems)


def timing_comparisons(
    selected_metric: dict[str, Any],
    support_metric: dict[str, Any],
    selected_bridge: dict[str, Any],
    support_bridge: dict[str, Any],
) -> dict[str, bool]:
    selected_offset = selected_metric.get("cpa_horizon_offset_s")
    support_offset = support_metric.get("cpa_horizon_offset_s")
    selected_closer = (
        finite_number(selected_offset)
        and finite_number(support_offset)
        and abs(float(selected_offset)) < abs(float(support_offset))
    )
    return {
        "selected_lower_cpa": rank_better(selected_metric.get("min_cpa"), support_metric.get("min_cpa")),
        "selected_better_cpa_rank": rank_better(selected_metric.get("cpa_rank"), support_metric.get("cpa_rank")),
        "selected_earlier_cpa_horizon": rank_better(
            selected_metric.get("cpa_horizon_index"),
            support_metric.get("cpa_horizon_index"),
        ),
        "selected_horizon_closer_to_event": selected_closer,
        "support_better_bridge": bridge_rank(support_bridge) > bridge_rank(selected_bridge),
        "selected_no_support_support_supported": (
            not bridge_supported(selected_bridge) and bridge_supported(support_bridge)
        ),
    }


def classify_row(
    selected_state: str | None,
    support_state: str | None,
    selected_metric: dict[str, Any] | None,
    support_metric: dict[str, Any] | None,
    selected_bridge: dict[str, Any],
    support_bridge: dict[str, Any],
    comparisons: dict[str, bool],
    problems: list[str],
) -> str:
    if problems:
        return "path_horizon_bridge_timing_insufficient"
    selected_supported = bridge_supported(selected_bridge)
    support_supported = bridge_supported(support_bridge)
    if selected_supported and support_supported:
        return "selected_and_support_both_bridge_supported"
    if selected_state == "subthreshold" or support_state in {"active", "borderline"}:
        return "support_surface_or_selected_subthreshold"
    selected_horizon = selected_metric.get("cpa_horizon_index") if selected_metric else None
    support_horizon = support_metric.get("cpa_horizon_index") if support_metric else None
    split_present = (
        selected_state in {"active", "borderline"}
        and support_state == "subthreshold"
        and not selected_supported
        and support_supported
        and finite_number(selected_horizon)
        and finite_number(support_horizon)
    )
    if split_present:
        if comparisons.get("selected_lower_cpa") and comparisons.get("selected_better_cpa_rank"):
            return "path_horizon_support_bridge_timing_split"
        return "path_horizon_support_bridge_no_horizon_advantage"
    return "path_horizon_bridge_timing_insufficient"


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter80_report: dict[str, Any],
    iter83_report: dict[str, Any],
    iter84_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter80": (iter80_report, ITER80_VERDICT),
        "iter83": (iter83_report, ITER83_VERDICT),
        "iter84": (iter84_report, ITER84_VERDICT),
    }
    for label, (report, verdict) in expected_verdicts.items():
        if report.get("verdict") != verdict:
            problems.append(f"{label}-verdict-not-{verdict}")
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter80_index = event_index(iter80_report.get("events"), "iter80", problems)
    iter83_index = object_index(iter83_report.get("objects"), "iter83", problems)
    iter84_index = event_index(iter84_report.get("events"), "iter84", problems)
    if len(iter80_index) != len(FIXED_EVENTS):
        problems.append(f"iter80-event-count-mismatch:{len(iter80_index)}")
    if len(iter83_index) != 2:
        problems.append(f"iter83-object-count-mismatch:{len(iter83_index)}")
    if len(iter84_index) != len(FIXED_EVENTS):
        problems.append(f"iter84-event-count-mismatch:{len(iter84_index)}")

    selected: list[dict[str, Any]] = []
    for event in FIXED_EVENTS:
        row_key = (event["audit_id"], event["scenario"])
        event_key = (event["audit_id"], event["scenario"], event["role"])
        row59 = iter59_index.get(row_key)
        row80 = iter80_index.get(event_key)
        row83 = iter83_index.get(row_key)
        row84 = iter84_index.get(event_key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{row_key}")
            continue
        if row80 is None:
            problems.append(f"missing-iter80-event:{event_key}")
            continue
        if row83 is None:
            problems.append(f"missing-iter83-object:{row_key}")
            continue
        if row84 is None:
            problems.append(f"missing-iter84-event:{event_key}")
            continue

        if row80.get("problems"):
            problems.append(f"iter80-event-problems:{event_key}:{row80.get('problems')}")
        if row83.get("problems"):
            problems.append(f"iter83-object-problems:{row_key}:{row83.get('problems')}")
        if row84.get("problems"):
            problems.append(f"iter84-event-problems:{event_key}:{row84.get('problems')}")
        if row80.get("row_label") != "selected_all_provenance_no_support":
            problems.append(f"iter80-selected-provenance-label-mismatch:{event_key}:{row80.get('row_label')}")
        if row84.get("row_label") != "selected_surface_support_bridge_split":
            problems.append(f"iter84-label-mismatch:{event_key}:{row84.get('row_label')}")
        if row84.get("selected_state") not in {"active", "borderline"}:
            problems.append(f"iter84-selected-state-not-surface:{event_key}:{row84.get('selected_state')}")
        if row84.get("support_state") != "subthreshold":
            problems.append(f"iter84-support-state-not-subthreshold:{event_key}:{row84.get('support_state')}")

        for row_label, row in (("iter80", row80), ("iter84", row84)):
            if not same_object_id(row.get("selected_object_id"), event["selected_object_id"]):
                problems.append(f"{row_label}-selected-object-mismatch:{event_key}:{row.get('selected_object_id')}")
            if not same_object_id(row.get("support_object_id"), event["support_object_id"]):
                problems.append(f"{row_label}-support-object-mismatch:{event_key}:{row.get('support_object_id')}")
            event_ts = surface_margin.number(row.get("event_ts"), f"{row_label}.event_ts", problems)
            if event_ts is not None and not math.isclose(event_ts, float(event["event_ts"]), abs_tol=1e-6):
                problems.append(f"{row_label}-event-ts-mismatch:{event_key}:{event_ts}")

        if not same_object_id(row83.get("support_object_id"), event["support_object_id"]):
            problems.append(f"iter83-support-object-mismatch:{row_key}:{row83.get('support_object_id')}")

        selected_bridge = row84.get("selected_bridge")
        support_bridge = row84.get("support_bridge")
        if not isinstance(selected_bridge, dict):
            problems.append(f"iter84-selected-bridge-not-dict:{event_key}")
        elif bridge_supported(selected_bridge):
            problems.append(f"iter84-selected-bridge-supported:{event_key}:{selected_bridge.get('distance_band')}")
        if not isinstance(support_bridge, dict):
            problems.append(f"iter84-support-bridge-not-dict:{event_key}")
        elif not bridge_supported(support_bridge):
            problems.append(f"iter84-support-bridge-not-supported:{event_key}:{support_bridge.get('distance_band')}")

        selected.append({"event": event, "iter59": row59, "iter80": row80, "iter83": row83, "iter84": row84})
    if len(selected) != len(FIXED_EVENTS):
        problems.append(f"fixed-event-count-mismatch:{len(selected)}")
    return selected, problems


def analyze_event(item: dict[str, Any]) -> dict[str, Any]:
    event = item["event"]
    row59 = item["iter59"]
    role = str(event["role"])
    problems: list[str] = []
    event_ts = surface_margin.number(event.get("event_ts"), "event.event_ts", problems)
    episode_dir = row59.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        decision_rows: list[dict[str, Any]] = []
        provenance_rows: list[dict[str, Any]] = []
    else:
        ep_dir = Path(episode_dir)
        decision_rows, row_problems = SWITCH.load_decision_rows(ep_dir / "sentinel_iter48_decisions.jsonl")
        provenance_rows = ITER80.load_all_provenance(ep_dir / "eval.json", problems)
        problems.extend(row_problems)

    event_row = SWITCH.find_decision_row(decision_rows, event_ts, role, problems) if event_ts is not None else None
    selected_metric: dict[str, Any] | None = None
    support_metric: dict[str, Any] | None = None
    selected_bridge: dict[str, Any] = {"distance_band": "missing"}
    support_bridge: dict[str, Any] = {"distance_band": "missing"}
    comparisons: dict[str, bool] = {}
    selected_state: str | None = None
    support_state: str | None = None
    if event_row is not None and event_ts is not None:
        selected_metric = metric_with_horizon_timing(
            event_row,
            event["selected_object_id"],
            event_ts,
            "selected",
            problems,
        )
        support_metric = metric_with_horizon_timing(
            event_row,
            event["support_object_id"],
            event_ts,
            "support",
            problems,
        )
        selected_obj = SWITCH.select_object(event_row, event["selected_object_id"], "selected", problems)
        support_obj = SWITCH.select_object(event_row, event["support_object_id"], "support", problems)
        if selected_metric is not None:
            selected_state = selected_metric.get("state")
        if support_metric is not None:
            support_state = support_metric.get("state")
        if selected_obj is not None:
            selected_bridge = object_bridge(event_row, event_ts, selected_obj, "selected", provenance_rows, problems)
        if support_obj is not None:
            support_bridge = object_bridge(event_row, event_ts, support_obj, "support", provenance_rows, problems)
        if selected_metric is not None and support_metric is not None:
            comparisons = timing_comparisons(selected_metric, support_metric, selected_bridge, support_bridge)

    row_label = classify_row(
        selected_state,
        support_state,
        selected_metric,
        support_metric,
        selected_bridge,
        support_bridge,
        comparisons,
        problems,
    )
    return {
        "audit_id": event["audit_id"],
        "scenario": event["scenario"],
        "event_role": role,
        "event_ts": event_ts,
        "selected_object_id": event["selected_object_id"],
        "support_object_id": event["support_object_id"],
        "selected_state": selected_state,
        "support_state": support_state,
        "selected_metric": compact_metric(selected_metric),
        "support_metric": compact_metric(support_metric),
        "selected_bridge": compact_bridge(selected_bridge),
        "support_bridge": compact_bridge(support_bridge),
        "timing_comparisons": comparisons,
        "row_label": row_label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_EVENTS)
        or any(row.get("problems") for row in rows)
        or "path_horizon_bridge_timing_insufficient" in labels
    ):
        return "HUGSIM_PATH_HORIZON_BRIDGE_TIMING_BLOCKED"
    if all(label == "path_horizon_support_bridge_timing_split" for label in labels):
        return "HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE"
    if (
        "path_horizon_support_bridge_no_horizon_advantage" in labels
        and "path_horizon_support_bridge_timing_split" not in labels
    ):
        return "HUGSIM_PATH_HORIZON_BRIDGE_TIMING_NO_ADVANTAGE_COMPLETE"
    return "HUGSIM_PATH_HORIZON_BRIDGE_TIMING_MIXED_COMPLETE"


def build_report(
    iter59_report_path: Path,
    iter80_report_path: Path,
    iter83_report_path: Path,
    iter84_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter80_report, problems80 = surface_margin.load_report(iter80_report_path, "iter80-report")
    iter83_report, problems83 = surface_margin.load_report(iter83_report_path, "iter83-report")
    iter84_report, problems84 = surface_margin.load_report(iter84_report_path, "iter84-report")
    infra_problems.extend(problems59 + problems80 + problems83 + problems84)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter59_report, iter80_report, iter83_report, iter84_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_event(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    comparison_counts: Counter[str] = Counter()
    support_timing_counts: Counter[str] = Counter()
    for row in rows:
        for key, value in (row.get("timing_comparisons") or {}).items():
            if value:
                comparison_counts[key] += 1
        support_timing = (row.get("support_bridge") or {}).get("timing_label")
        if support_timing is not None:
            support_timing_counts[str(support_timing)] += 1
    return {
        "iteration": 85,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter80_report": str(iter80_report_path),
            "iter83_report": str(iter83_report_path),
            "iter84_report": str(iter84_report_path),
        },
        "fixed_events": list(FIXED_EVENTS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_events": len(selected),
            "evaluated_events": sum(not row.get("problems") for row in rows),
            "event_label_counts": dict(sorted(label_counts.items())),
            "selected_bridge_supported_events": sum(bridge_supported(row.get("selected_bridge") or {}) for row in rows),
            "support_bridge_supported_events": sum(bridge_supported(row.get("support_bridge") or {}) for row in rows),
            "timing_comparison_counts": dict(sorted(comparison_counts.items())),
            "support_bridge_timing_counts": dict(sorted(support_timing_counts.items())),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "three-row descriptive path-horizon/provenance-timing decomposition only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, real-world behavior, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 85 - HUGSIM path-horizon/provenance-timing decomposition",
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
        "| audit id | event | selected id | selected state | selected CPA | selected horizon | selected bridge | support id | support state | support CPA | support horizon | support bridge | support timing | comparisons | label | problems |",
        "|---|---|---:|---|---:|---:|---|---:|---|---:|---:|---|---|---|---|---|",
    ])
    for row in report["events"]:
        selected_metric = row.get("selected_metric") or {}
        support_metric = row.get("support_metric") or {}
        selected_bridge = row.get("selected_bridge") or {}
        support_bridge = row.get("support_bridge") or {}
        comparisons = [key for key, value in (row.get("timing_comparisons") or {}).items() if value]
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{row['selected_object_id']}` | "
            f"`{row.get('selected_state')}` | `{selected_metric.get('min_cpa')}` | "
            f"`{selected_metric.get('cpa_horizon_index')}` / "
            f"`{selected_metric.get('cpa_horizon_time_s')}` | `{selected_bridge.get('distance_band')}` | "
            f"`{row['support_object_id']}` | `{row.get('support_state')}` | "
            f"`{support_metric.get('min_cpa')}` | `{support_metric.get('cpa_horizon_index')}` / "
            f"`{support_metric.get('cpa_horizon_time_s')}` | `{support_bridge.get('distance_band')}` | "
            f"`{support_bridge.get('timing_label')}` / "
            f"`{support_bridge.get('provenance_event_offset_s')}` | `{comparisons}` | "
            f"`{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter80_report: Path,
    iter83_report: Path,
    iter84_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter80_report, iter83_report, iter84_report)
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
        "--iter80-report",
        type=Path,
        default=Path(
            "experiments/iter80_hugsim_selected_all_provenance_bridge/proof-all-provenance/"
            "all_provenance_report.json"
        ),
    )
    parser.add_argument(
        "--iter83-report",
        type=Path,
        default=Path(
            "experiments/iter83_hugsim_bridge_supported_surface_miss_decomposition/proof-surface-miss/"
            "surface_miss_report.json"
        ),
    )
    parser.add_argument(
        "--iter84-report",
        type=Path,
        default=Path(
            "experiments/iter84_hugsim_selected_support_arbitration/proof-arbitration/"
            "arbitration_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter85_hugsim_path_horizon_bridge_timing/proof-timing/"
            "path_horizon_bridge_timing_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter85_hugsim_path_horizon_bridge_timing/proof-timing/"
            "path_horizon_bridge_timing.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_report,
        args.iter80_report,
        args.iter83_report,
        args.iter84_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
