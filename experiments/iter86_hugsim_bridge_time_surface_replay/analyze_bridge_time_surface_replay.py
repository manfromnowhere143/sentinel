#!/usr/bin/env python3
"""Iteration 86 HUGSIM bridge-time support-surface replay."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER81_VERDICT = "HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE"
ITER83_VERDICT = "HUGSIM_BRIDGE_SUPPORTED_SURFACE_MISS_MIXED_COMPLETE"
ITER85_VERDICT = "HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE"
SUPPORTED_BANDS = {"match", "ambiguous"}
FIXED_ROWS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "role": "pre",
        "event_ts": 5.0,
        "support_object_id": 9,
        "support_bridge_band": "ambiguous",
        "bridge_ts": 5.5,
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "pre",
        "event_ts": 2.5,
        "support_object_id": 10,
        "support_bridge_band": "match",
        "bridge_ts": 4.0,
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "active",
        "event_ts": 5.0,
        "support_object_id": 10,
        "support_bridge_band": "match",
        "bridge_ts": 6.0,
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


ITER85 = _load_module(
    "experiments/iter85_hugsim_path_horizon_bridge_timing/analyze_path_horizon_bridge_timing.py",
    "iter85_path_horizon_bridge_timing",
)
SWITCH = ITER85.SWITCH
surface_margin = ITER85.surface_margin


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def event_index(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return ITER85.event_index(rows, label, problems)


def object_index(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str], dict[str, Any]]:
    return ITER85.object_index(rows, label, problems)


def bridge_supported(bridge: dict[str, Any]) -> bool:
    return bridge.get("distance_band") in SUPPORTED_BANDS


def compact_metric(metric: dict[str, Any] | None) -> dict[str, Any] | None:
    return ITER85.compact_metric(metric)


def metric_at_row(
    row: dict[str, Any],
    ts: float,
    object_id: Any,
    role: str,
    problems: list[str],
) -> dict[str, Any] | None:
    metric = ITER85.metric_with_horizon_timing(row, object_id, ts, role, problems)
    return metric


def state_transition(event_metric: dict[str, Any] | None, bridge_metric: dict[str, Any] | None) -> dict[str, Any]:
    event_state = event_metric.get("state") if isinstance(event_metric, dict) else None
    bridge_state = bridge_metric.get("state") if isinstance(bridge_metric, dict) else None
    event_cpa = event_metric.get("min_cpa") if isinstance(event_metric, dict) else None
    bridge_cpa = bridge_metric.get("min_cpa") if isinstance(bridge_metric, dict) else None
    event_rank = event_metric.get("cpa_rank") if isinstance(event_metric, dict) else None
    bridge_rank = bridge_metric.get("cpa_rank") if isinstance(bridge_metric, dict) else None
    return {
        "event_state": event_state,
        "bridge_state": bridge_state,
        "state_transition": f"{event_state}->{bridge_state}",
        "min_cpa_delta_m": float(bridge_cpa) - float(event_cpa) if finite_number(event_cpa) and finite_number(bridge_cpa) else None,
        "finite_ttc_transition": (
            f"{finite_number(event_metric.get('ttc'))}->{finite_number(bridge_metric.get('ttc'))}"
            if isinstance(event_metric, dict) and isinstance(bridge_metric, dict)
            else None
        ),
        "cpa_rank_delta": int(bridge_rank) - int(event_rank) if finite_number(event_rank) and finite_number(bridge_rank) else None,
    }


def classify_row(
    event_metric: dict[str, Any] | None,
    bridge_metric: dict[str, Any] | None,
    problems: list[str],
) -> str:
    if problems:
        return "bridge_time_surface_replay_insufficient"
    if event_metric is None:
        return "bridge_time_surface_replay_insufficient"
    if bridge_metric is None:
        return "support_bridge_time_object_missing"
    if event_metric.get("state") != "subthreshold":
        return "bridge_time_surface_replay_insufficient"
    if bridge_metric.get("state") in {"active", "borderline"}:
        return "support_bridge_time_surface_arrival"
    if bridge_metric.get("state") == "subthreshold":
        return "support_bridge_time_surface_miss"
    return "bridge_time_surface_replay_insufficient"


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter81_report: dict[str, Any],
    iter83_report: dict[str, Any],
    iter85_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter81": (iter81_report, ITER81_VERDICT),
        "iter83": (iter83_report, ITER83_VERDICT),
        "iter85": (iter85_report, ITER85_VERDICT),
    }
    for label, (report, verdict) in expected_verdicts.items():
        if report.get("verdict") != verdict:
            problems.append(f"{label}-verdict-not-{verdict}")
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter81_index = object_index(iter81_report.get("objects"), "iter81", problems)
    iter83_index = object_index(iter83_report.get("objects"), "iter83", problems)
    iter85_index = event_index(iter85_report.get("events"), "iter85", problems)
    if len(iter81_index) != 2:
        problems.append(f"iter81-object-count-mismatch:{len(iter81_index)}")
    if len(iter83_index) != 2:
        problems.append(f"iter83-object-count-mismatch:{len(iter83_index)}")
    if len(iter85_index) != len(FIXED_ROWS):
        problems.append(f"iter85-event-count-mismatch:{len(iter85_index)}")

    selected: list[dict[str, Any]] = []
    for target in FIXED_ROWS:
        row_key = (target["audit_id"], target["scenario"])
        event_key = (target["audit_id"], target["scenario"], target["role"])
        row59 = iter59_index.get(row_key)
        row81 = iter81_index.get(row_key)
        row83 = iter83_index.get(row_key)
        row85 = iter85_index.get(event_key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{row_key}")
            continue
        if row81 is None:
            problems.append(f"missing-iter81-object:{row_key}")
            continue
        if row83 is None:
            problems.append(f"missing-iter83-object:{row_key}")
            continue
        if row85 is None:
            problems.append(f"missing-iter85-event:{event_key}")
            continue

        if row81.get("problems"):
            problems.append(f"iter81-object-problems:{row_key}:{row81.get('problems')}")
        if row83.get("problems"):
            problems.append(f"iter83-object-problems:{row_key}:{row83.get('problems')}")
        if row85.get("problems"):
            problems.append(f"iter85-event-problems:{event_key}:{row85.get('problems')}")
        for row_label, row in (("iter81", row81), ("iter83", row83), ("iter85", row85)):
            if not same_object_id(row.get("support_object_id"), target["support_object_id"]):
                problems.append(f"{row_label}-support-object-mismatch:{event_key}:{row.get('support_object_id')}")
        if row85.get("row_label") != "path_horizon_support_bridge_timing_split":
            problems.append(f"iter85-label-mismatch:{event_key}:{row85.get('row_label')}")
        if row85.get("support_state") != "subthreshold":
            problems.append(f"iter85-support-state-not-subthreshold:{event_key}:{row85.get('support_state')}")
        if bridge_supported(row85.get("selected_bridge") or {}):
            problems.append(f"iter85-selected-bridge-supported:{event_key}")
        support_bridge = row85.get("support_bridge")
        if not isinstance(support_bridge, dict):
            problems.append(f"iter85-support-bridge-not-dict:{event_key}")
        elif not bridge_supported(support_bridge):
            problems.append(f"iter85-support-bridge-not-supported:{event_key}:{support_bridge.get('distance_band')}")
        else:
            if support_bridge.get("distance_band") != target["support_bridge_band"]:
                problems.append(
                    f"iter85-support-bridge-band-mismatch:{event_key}:{support_bridge.get('distance_band')}"
                )
            bridge_ts = surface_margin.number(
                support_bridge.get("provenance_timestamp"),
                f"iter85.support_bridge.provenance_timestamp:{event_key}",
                problems,
            )
            if bridge_ts is not None and not math.isclose(bridge_ts, float(target["bridge_ts"]), abs_tol=1e-6):
                problems.append(f"iter85-bridge-ts-mismatch:{event_key}:{bridge_ts}")
            if support_bridge.get("timing_label") != "provenance_after_event":
                problems.append(f"iter85-support-timing-not-after-event:{event_key}:{support_bridge.get('timing_label')}")
        event_ts = surface_margin.number(row85.get("event_ts"), f"iter85.event_ts:{event_key}", problems)
        if event_ts is not None and not math.isclose(event_ts, float(target["event_ts"]), abs_tol=1e-6):
            problems.append(f"iter85-event-ts-mismatch:{event_key}:{event_ts}")
        selected.append({"target": target, "iter59": row59, "iter81": row81, "iter83": row83, "iter85": row85})
    if len(selected) != len(FIXED_ROWS):
        problems.append(f"fixed-row-count-mismatch:{len(selected)}")
    return selected, problems


def analyze_target(item: dict[str, Any]) -> dict[str, Any]:
    target = item["target"]
    row59 = item["iter59"]
    problems: list[str] = []
    episode_dir = row59.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        decision_rows: list[dict[str, Any]] = []
    else:
        decision_rows, row_problems = SWITCH.load_decision_rows(Path(episode_dir) / "sentinel_iter48_decisions.jsonl")
        problems.extend(row_problems)

    event_ts = surface_margin.number(target.get("event_ts"), "target.event_ts", problems)
    bridge_ts = surface_margin.number(target.get("bridge_ts"), "target.bridge_ts", problems)
    event_row = SWITCH.find_decision_row(decision_rows, event_ts, "event", problems) if event_ts is not None else None
    bridge_row = SWITCH.find_decision_row(decision_rows, bridge_ts, "bridge", problems) if bridge_ts is not None else None

    event_metric = None
    bridge_metric = None
    if event_row is not None and event_ts is not None:
        event_metric = metric_at_row(event_row, event_ts, target["support_object_id"], "event_support", problems)
    if bridge_row is not None and bridge_ts is not None:
        bridge_metric = metric_at_row(bridge_row, bridge_ts, target["support_object_id"], "bridge_support", problems)
    transition = state_transition(event_metric, bridge_metric)
    label = classify_row(event_metric, bridge_metric, problems)
    return {
        "audit_id": target["audit_id"],
        "scenario": target["scenario"],
        "event_role": target["role"],
        "event_ts": event_ts,
        "bridge_ts": bridge_ts,
        "support_object_id": target["support_object_id"],
        "support_bridge_band": target["support_bridge_band"],
        "event_metric": compact_metric(event_metric),
        "bridge_metric": compact_metric(bridge_metric),
        "transition": transition,
        "row_label": label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_ROWS)
        or any(row.get("problems") for row in rows)
        or "bridge_time_surface_replay_insufficient" in labels
    ):
        return "HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED"
    if all(label == "support_bridge_time_surface_arrival" for label in labels):
        return "HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_ARRIVAL_COMPLETE"
    if all(label == "support_bridge_time_surface_miss" for label in labels):
        return "HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_MISS_COMPLETE"
    if "support_bridge_time_surface_arrival" in labels and "support_bridge_time_surface_miss" in labels:
        return "HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE"
    return "HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED"


def build_report(
    iter59_report_path: Path,
    iter81_report_path: Path,
    iter83_report_path: Path,
    iter85_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter81_report, problems81 = surface_margin.load_report(iter81_report_path, "iter81-report")
    iter83_report, problems83 = surface_margin.load_report(iter83_report_path, "iter83-report")
    iter85_report, problems85 = surface_margin.load_report(iter85_report_path, "iter85-report")
    infra_problems.extend(problems59 + problems81 + problems83 + problems85)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter59_report, iter81_report, iter83_report, iter85_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_target(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    transition_counts = Counter((row.get("transition") or {}).get("state_transition") for row in rows)
    return {
        "iteration": 86,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter81_report": str(iter81_report_path),
            "iter83_report": str(iter83_report_path),
            "iter85_report": str(iter85_report_path),
        },
        "fixed_rows": list(FIXED_ROWS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_rows": len(selected),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "state_transition_counts": {
                str(key): value for key, value in sorted(transition_counts.items()) if key is not None
            },
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "three-row descriptive bridge-time support-surface replay only; no actor-causality, repair, "
            "threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, real-world behavior, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 86 - HUGSIM bridge-time support-surface replay",
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
        "| audit id | event | support id | event ts | bridge ts | event state | bridge state | event CPA | bridge CPA | transition | label | problems |",
        "|---|---|---:|---:|---:|---|---|---:|---:|---|---|---|",
    ])
    for row in report["events"]:
        event_metric = row.get("event_metric") or {}
        bridge_metric = row.get("bridge_metric") or {}
        transition = row.get("transition") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{row['support_object_id']}` | "
            f"`{row.get('event_ts')}` | `{row.get('bridge_ts')}` | "
            f"`{event_metric.get('state')}` | `{bridge_metric.get('state')}` | "
            f"`{event_metric.get('min_cpa')}` | `{bridge_metric.get('min_cpa')}` | "
            f"`{transition.get('state_transition')}` | `{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter81_report: Path,
    iter83_report: Path,
    iter85_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter81_report, iter83_report, iter85_report)
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
        "--iter81-report",
        type=Path,
        default=Path(
            "experiments/iter81_hugsim_support_object_temporal_surface/proof-temporal/"
            "temporal_report.json"
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
        "--iter85-report",
        type=Path,
        default=Path(
            "experiments/iter85_hugsim_path_horizon_bridge_timing/proof-timing/"
            "path_horizon_bridge_timing_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter86_hugsim_bridge_time_surface_replay/proof-bridge-time/"
            "bridge_time_surface_replay_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter86_hugsim_bridge_time_surface_replay/proof-bridge-time/"
            "bridge_time_surface_replay.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_report,
        args.iter81_report,
        args.iter83_report,
        args.iter85_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
