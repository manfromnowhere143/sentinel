#!/usr/bin/env python3
"""Iteration 87 HUGSIM interval bridge-time support-surface replay."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER85_VERDICT = "HUGSIM_PATH_HORIZON_BRIDGE_TIMING_SPLIT_COMPLETE"
ITER86_VERDICT = "HUGSIM_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED"
SUPPORTED_BANDS = {"match", "ambiguous"}
MAX_FALLBACK_OFFSET_S = 0.5
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


ITER86 = _load_module(
    "experiments/iter86_hugsim_bridge_time_surface_replay/analyze_bridge_time_surface_replay.py",
    "iter86_bridge_time_surface_replay",
)
ITER85 = ITER86.ITER85
SWITCH = ITER86.SWITCH
surface_margin = ITER86.surface_margin


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def bridge_supported(bridge: dict[str, Any]) -> bool:
    return bridge.get("distance_band") in SUPPORTED_BANDS


def event_index(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return ITER85.event_index(rows, label, problems)


def compact_metric(metric: dict[str, Any] | None) -> dict[str, Any] | None:
    return ITER85.compact_metric(metric)


def metric_at_row(
    row: dict[str, Any],
    ts: float,
    object_id: Any,
    role: str,
    problems: list[str],
) -> dict[str, Any] | None:
    return ITER85.metric_with_horizon_timing(row, object_id, ts, role, problems)


def decision_ts(row: dict[str, Any], label: str, problems: list[str]) -> float | None:
    return surface_margin.number(row.get("ts", row.get("frame_index")), label, problems)


def select_interval_replay_row(
    rows: list[dict[str, Any]],
    event_ts: float,
    bridge_ts: float,
    role: str,
    problems: list[str],
) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    stamped: list[tuple[float, dict[str, Any]]] = []
    for idx, row in enumerate(rows):
        ts = decision_ts(row, f"{role}.decision.ts:{idx}", problems)
        if ts is not None:
            stamped.append((ts, row))

    exact = [(ts, row) for ts, row in stamped if math.isclose(ts, bridge_ts, abs_tol=1e-6)]
    if len(exact) == 1:
        return exact[0][1], {
            "alignment": "exact_bridge_ts",
            "event_ts": event_ts,
            "bridge_ts": bridge_ts,
            "replay_ts": exact[0][0],
            "bridge_to_replay_offset_s": 0.0,
        }
    if len(exact) > 1:
        problems.append(f"{role}-exact-bridge-row-count-{len(exact)}-for-ts-{bridge_ts}")
        return None, {
            "alignment": "selection_failed",
            "event_ts": event_ts,
            "bridge_ts": bridge_ts,
            "replay_ts": None,
            "bridge_to_replay_offset_s": None,
        }

    candidates = [
        (ts, row)
        for ts, row in stamped
        if ts >= event_ts - 1e-6 and ts <= bridge_ts + 1e-6
    ]
    if not candidates:
        problems.append(f"{role}-no-before-bridge-row-for-ts-{bridge_ts}")
        return None, {
            "alignment": "selection_failed",
            "event_ts": event_ts,
            "bridge_ts": bridge_ts,
            "replay_ts": None,
            "bridge_to_replay_offset_s": None,
        }
    replay_ts, replay_row = max(candidates, key=lambda item: item[0])
    offset = bridge_ts - replay_ts
    if offset <= 1e-6 or offset > MAX_FALLBACK_OFFSET_S + 1e-6:
        problems.append(f"{role}-invalid-before-bridge-offset:{offset}")
        return None, {
            "alignment": "selection_failed",
            "event_ts": event_ts,
            "bridge_ts": bridge_ts,
            "replay_ts": replay_ts,
            "bridge_to_replay_offset_s": offset,
        }
    return replay_row, {
        "alignment": "nearest_before_bridge_ts",
        "event_ts": event_ts,
        "bridge_ts": bridge_ts,
        "replay_ts": replay_ts,
        "bridge_to_replay_offset_s": offset,
    }


def state_transition(event_metric: dict[str, Any] | None, replay_metric: dict[str, Any] | None) -> dict[str, Any]:
    event_state = event_metric.get("state") if isinstance(event_metric, dict) else None
    replay_state = replay_metric.get("state") if isinstance(replay_metric, dict) else None
    event_cpa = event_metric.get("min_cpa") if isinstance(event_metric, dict) else None
    replay_cpa = replay_metric.get("min_cpa") if isinstance(replay_metric, dict) else None
    event_rank = event_metric.get("cpa_rank") if isinstance(event_metric, dict) else None
    replay_rank = replay_metric.get("cpa_rank") if isinstance(replay_metric, dict) else None
    return {
        "event_state": event_state,
        "replay_state": replay_state,
        "state_transition": f"{event_state}->{replay_state}",
        "min_cpa_delta_m": float(replay_cpa) - float(event_cpa) if finite_number(event_cpa) and finite_number(replay_cpa) else None,
        "finite_ttc_transition": (
            f"{finite_number(event_metric.get('ttc'))}->{finite_number(replay_metric.get('ttc'))}"
            if isinstance(event_metric, dict) and isinstance(replay_metric, dict)
            else None
        ),
        "cpa_rank_delta": int(replay_rank) - int(event_rank) if finite_number(event_rank) and finite_number(replay_rank) else None,
    }


def classify_row(
    event_metric: dict[str, Any] | None,
    replay_metric: dict[str, Any] | None,
    problems: list[str],
) -> str:
    if problems:
        return "interval_bridge_time_surface_replay_insufficient"
    if event_metric is None:
        return "interval_bridge_time_surface_replay_insufficient"
    if replay_metric is None:
        return "interval_support_object_missing"
    if event_metric.get("state") != "subthreshold":
        return "interval_bridge_time_surface_replay_insufficient"
    if replay_metric.get("state") in {"active", "borderline"}:
        return "interval_support_surface_arrival"
    if replay_metric.get("state") == "subthreshold":
        return "interval_support_surface_miss"
    return "interval_bridge_time_surface_replay_insufficient"


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter85_report: dict[str, Any],
    iter86_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter85": (iter85_report, ITER85_VERDICT),
        "iter86": (iter86_report, ITER86_VERDICT),
    }
    for label, (report, verdict) in expected_verdicts.items():
        if report.get("verdict") != verdict:
            problems.append(f"{label}-verdict-not-{verdict}")
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter85_index = event_index(iter85_report.get("events"), "iter85", problems)
    iter86_index = event_index(iter86_report.get("events"), "iter86", problems)
    if len(iter85_index) != len(FIXED_ROWS):
        problems.append(f"iter85-event-count-mismatch:{len(iter85_index)}")
    if len(iter86_index) != len(FIXED_ROWS):
        problems.append(f"iter86-event-count-mismatch:{len(iter86_index)}")

    selected: list[dict[str, Any]] = []
    active_block_confirmed = False
    for target in FIXED_ROWS:
        row_key = (target["audit_id"], target["scenario"])
        event_key = (target["audit_id"], target["scenario"], target["role"])
        row59 = iter59_index.get(row_key)
        row85 = iter85_index.get(event_key)
        row86 = iter86_index.get(event_key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{row_key}")
            continue
        if row85 is None:
            problems.append(f"missing-iter85-event:{event_key}")
            continue
        if row86 is None:
            problems.append(f"missing-iter86-event:{event_key}")
            continue
        if row85.get("problems"):
            problems.append(f"iter85-event-problems:{event_key}:{row85.get('problems')}")
        for row_label, row in (("iter85", row85), ("iter86", row86)):
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
                problems.append(f"iter85-support-bridge-band-mismatch:{event_key}:{support_bridge.get('distance_band')}")
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
        if event_key == ("ttc_medium_a", "scene-0071-medium-01", "active"):
            row_problems = row86.get("problems")
            if isinstance(row_problems, list) and "bridge-row-count-0-for-ts-6.0" in row_problems:
                active_block_confirmed = True
        selected.append({"target": target, "iter59": row59, "iter85": row85, "iter86": row86})
    if len(selected) != len(FIXED_ROWS):
        problems.append(f"fixed-row-count-mismatch:{len(selected)}")
    if not active_block_confirmed:
        problems.append("iter86-active-bridge-row-missing-block-not-confirmed")
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
    replay_row = None
    selection = {
        "alignment": "selection_failed",
        "event_ts": event_ts,
        "bridge_ts": bridge_ts,
        "replay_ts": None,
        "bridge_to_replay_offset_s": None,
    }
    if event_ts is not None and bridge_ts is not None:
        replay_row, selection = select_interval_replay_row(
            decision_rows,
            event_ts,
            bridge_ts,
            "replay",
            problems,
        )

    event_metric = None
    replay_metric = None
    if event_row is not None and event_ts is not None:
        event_metric = metric_at_row(event_row, event_ts, target["support_object_id"], "event_support", problems)
    replay_ts = selection.get("replay_ts")
    if replay_row is not None and finite_number(replay_ts):
        replay_metric = metric_at_row(
            replay_row,
            float(replay_ts),
            target["support_object_id"],
            "replay_support",
            problems,
        )
    transition = state_transition(event_metric, replay_metric)
    label = classify_row(event_metric, replay_metric, problems)
    return {
        "audit_id": target["audit_id"],
        "scenario": target["scenario"],
        "event_role": target["role"],
        "event_ts": event_ts,
        "bridge_ts": bridge_ts,
        "support_object_id": target["support_object_id"],
        "support_bridge_band": target["support_bridge_band"],
        "selection": selection,
        "event_metric": compact_metric(event_metric),
        "replay_metric": compact_metric(replay_metric),
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
        or "interval_bridge_time_surface_replay_insufficient" in labels
    ):
        return "HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED"
    if all(label == "interval_support_surface_arrival" for label in labels):
        return "HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_ARRIVAL_COMPLETE"
    if all(label == "interval_support_surface_miss" for label in labels):
        return "HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MISS_COMPLETE"
    if (
        "interval_support_surface_arrival" in labels
        and "interval_support_surface_miss" in labels
        and "interval_support_object_missing" not in labels
    ):
        return "HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE"
    return "HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_BLOCKED"


def build_report(
    iter59_report_path: Path,
    iter85_report_path: Path,
    iter86_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter85_report, problems85 = surface_margin.load_report(iter85_report_path, "iter85-report")
    iter86_report, problems86 = surface_margin.load_report(iter86_report_path, "iter86-report")
    infra_problems.extend(problems59 + problems85 + problems86)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter59_report, iter85_report, iter86_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_target(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    transition_counts = Counter((row.get("transition") or {}).get("state_transition") for row in rows)
    alignment_counts = Counter((row.get("selection") or {}).get("alignment") for row in rows)
    return {
        "iteration": 87,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter85_report": str(iter85_report_path),
            "iter86_report": str(iter86_report_path),
        },
        "fixed_rows": list(FIXED_ROWS),
        "row_selection_rule": {
            "exact_label": "exact_bridge_ts",
            "fallback_label": "nearest_before_bridge_ts",
            "max_fallback_offset_s": MAX_FALLBACK_OFFSET_S,
            "future_after_bridge_rows_allowed": False,
            "interpolation_allowed": False,
        },
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_rows": len(selected),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "state_transition_counts": {
                str(key): value for key, value in sorted(transition_counts.items()) if key is not None
            },
            "replay_alignment_counts": {
                str(key): value for key, value in sorted(alignment_counts.items()) if key is not None
            },
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "three-row descriptive interval bridge-time support-surface replay only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, real-world behavior, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 87 - HUGSIM interval bridge-time support-surface replay",
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
        "| audit id | event | support id | event ts | bridge ts | replay ts | alignment | event state | replay state | event CPA | replay CPA | transition | label | problems |",
        "|---|---|---:|---:|---:|---:|---|---|---|---:|---:|---|---|---|",
    ])
    for row in report["events"]:
        event_metric = row.get("event_metric") or {}
        replay_metric = row.get("replay_metric") or {}
        transition = row.get("transition") or {}
        selection = row.get("selection") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{row['support_object_id']}` | "
            f"`{row.get('event_ts')}` | `{row.get('bridge_ts')}` | `{selection.get('replay_ts')}` | "
            f"`{selection.get('alignment')}` | `{event_metric.get('state')}` | "
            f"`{replay_metric.get('state')}` | `{event_metric.get('min_cpa')}` | "
            f"`{replay_metric.get('min_cpa')}` | `{transition.get('state_transition')}` | "
            f"`{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter85_report: Path,
    iter86_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter85_report, iter86_report)
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
        "--iter85-report",
        type=Path,
        default=Path(
            "experiments/iter85_hugsim_path_horizon_bridge_timing/proof-timing/"
            "path_horizon_bridge_timing_report.json"
        ),
    )
    parser.add_argument(
        "--iter86-report",
        type=Path,
        default=Path(
            "experiments/iter86_hugsim_bridge_time_surface_replay/proof-bridge-time/"
            "bridge_time_surface_replay_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter87_hugsim_interval_bridge_time_surface_replay/proof-interval/"
            "interval_bridge_time_surface_replay_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter87_hugsim_interval_bridge_time_surface_replay/proof-interval/"
            "interval_bridge_time_surface_replay.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter59_report, args.iter85_report, args.iter86_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
