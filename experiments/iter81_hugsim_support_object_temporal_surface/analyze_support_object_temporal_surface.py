#!/usr/bin/env python3
"""Iteration 81 HUGSIM support-object temporal surface audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER78_VERDICT = "HUGSIM_SUPPORT_OBJECT_RANKING_MIXED_COMPLETE"
ITER79_VERDICT = "HUGSIM_SELECTED_ACTIVE_SUPPORT_SUBTHRESHOLD_COMPLETE"
ITER80_VERDICT = "HUGSIM_SELECTED_ALL_PROVENANCE_NO_SUPPORT_COMPLETE"
TIME_TOL = 1e-9
FIXED_SUPPORT_OBJECTS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "support_object_id": 9,
        "support_events": (
            {
                "role": "pre",
                "event_ts": 5.0,
                "selected_object_id": 5,
                "support_band": "ambiguous",
            },
        ),
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "support_object_id": 10,
        "support_events": (
            {
                "role": "pre",
                "event_ts": 2.5,
                "selected_object_id": 6,
                "support_band": "match",
            },
            {
                "role": "active",
                "event_ts": 5.0,
                "selected_object_id": 24,
                "support_band": "match",
            },
        ),
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


ITER80 = _load_module(
    "experiments/iter80_hugsim_selected_all_provenance_bridge/analyze_selected_all_provenance_bridge.py",
    "iter80_selected_all_provenance_bridge",
)
ITER79 = ITER80.ITER79
ITER78 = ITER79.ITER78
ITER62 = ITER79.ITER62
SWITCH = ITER80.SWITCH
surface_margin = ITER80.surface_margin


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def event_index(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    if not isinstance(rows, list):
        problems.append(f"{label}-events-not-list")
        return {}
    index: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            problems.append(f"{label}-event-not-dict")
            continue
        audit_id = row.get("audit_id")
        scenario = row.get("scenario")
        role = row.get("event_role")
        if not isinstance(audit_id, str) or not isinstance(scenario, str) or not isinstance(role, str):
            problems.append(f"{label}-event-key-missing:{row}")
            continue
        key = (audit_id, scenario, role)
        if key in index:
            problems.append(f"duplicate-{label}-event:{key}")
        index[key] = row
    return index


def first_foreground_ts(eval_path: Path, problems: list[str]) -> float | None:
    foregrounds, foreground_problems = SWITCH.load_foregrounds(eval_path)
    problems.extend(foreground_problems)
    timestamps = [
        foreground.get("timestamp")
        for foreground in foregrounds
        if isinstance(foreground.get("timestamp"), (int, float)) and not isinstance(foreground.get("timestamp"), bool)
    ]
    if not timestamps:
        problems.append("first-foreground-missing")
        return None
    return float(min(timestamps))


def relative_time(event_ts: float | None, reference_ts: float | None) -> str:
    if event_ts is None:
        return "none"
    if reference_ts is None:
        return "reference_missing"
    if event_ts < reference_ts - TIME_TOL:
        return "before"
    if abs(event_ts - reference_ts) <= TIME_TOL:
        return "same"
    return "after"


def compact_frame(frame: dict[str, Any] | None) -> dict[str, Any] | None:
    if frame is None:
        return None
    keys = (
        "frame_index",
        "ts",
        "relative_to_first_foreground",
        "state",
        "min_cpa",
        "ttc",
        "cpa_rank",
        "ttc_rank",
        "cpa_active_logged_threshold",
        "ttc_active_logged_threshold",
        "cpa_borderline_registered",
        "ttc_borderline_registered",
    )
    return {key: frame.get(key) for key in keys}


def crosscheck_event(
    event: dict[str, Any],
    iter78_event: dict[str, Any] | None,
    iter79_event: dict[str, Any] | None,
    iter80_event: dict[str, Any] | None,
    event_key: tuple[str, str, str],
    problems: list[str],
) -> dict[str, Any]:
    if iter78_event is None:
        problems.append(f"missing-iter78-event:{event_key}")
        iter78_event = {}
    if iter79_event is None:
        problems.append(f"missing-iter79-event:{event_key}")
        iter79_event = {}
    if iter80_event is None:
        problems.append(f"missing-iter80-event:{event_key}")
        iter80_event = {}

    if iter78_event.get("row_label") != "support_object_nonselected_subthreshold":
        problems.append(f"iter78-row-label-mismatch:{event_key}:{iter78_event.get('row_label')}")
    if iter78_event.get("problems"):
        problems.append(f"iter78-event-problems:{event_key}:{iter78_event.get('problems')}")
    if not same_object_id(iter78_event.get("support_object_id"), event["support_object_id"]):
        problems.append(f"iter78-support-object-mismatch:{event_key}:{iter78_event.get('support_object_id')}")
    if not same_object_id(iter78_event.get("selected_object_id"), event["selected_object_id"]):
        problems.append(f"iter78-selected-object-mismatch:{event_key}:{iter78_event.get('selected_object_id')}")
    if iter78_event.get("support_band") != event["support_band"]:
        problems.append(f"iter78-support-band-mismatch:{event_key}:{iter78_event.get('support_band')}")
    event_ts = surface_margin.number(iter78_event.get("event_ts"), "iter78.event_ts", problems)
    if event_ts is not None and not math.isclose(event_ts, float(event["event_ts"]), abs_tol=1e-6):
        problems.append(f"iter78-event-ts-mismatch:{event_key}:{event_ts}")

    if iter79_event.get("problems"):
        problems.append(f"iter79-event-problems:{event_key}:{iter79_event.get('problems')}")
    if not same_object_id(iter79_event.get("support_object_id"), event["support_object_id"]):
        problems.append(f"iter79-support-object-mismatch:{event_key}:{iter79_event.get('support_object_id')}")
    if not same_object_id(iter79_event.get("selected_object_id"), event["selected_object_id"]):
        problems.append(f"iter79-selected-object-mismatch:{event_key}:{iter79_event.get('selected_object_id')}")
    if iter79_event.get("support_state") != "subthreshold":
        problems.append(f"iter79-support-state-mismatch:{event_key}:{iter79_event.get('support_state')}")

    if iter80_event.get("problems"):
        problems.append(f"iter80-event-problems:{event_key}:{iter80_event.get('problems')}")
    if not same_object_id(iter80_event.get("support_object_id"), event["support_object_id"]):
        problems.append(f"iter80-support-object-mismatch:{event_key}:{iter80_event.get('support_object_id')}")
    if not same_object_id(iter80_event.get("selected_object_id"), event["selected_object_id"]):
        problems.append(f"iter80-selected-object-mismatch:{event_key}:{iter80_event.get('selected_object_id')}")
    if iter80_event.get("row_label") != "selected_all_provenance_no_support":
        problems.append(f"iter80-row-label-mismatch:{event_key}:{iter80_event.get('row_label')}")
    return {
        "role": event["role"],
        "event_ts": event["event_ts"],
        "selected_object_id": event["selected_object_id"],
        "support_band": event["support_band"],
        "iter78_row_label": iter78_event.get("row_label"),
        "iter79_support_state": iter79_event.get("support_state"),
        "iter80_row_label": iter80_event.get("row_label"),
    }


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter78_report: dict[str, Any],
    iter79_report: dict[str, Any],
    iter80_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter78": (iter78_report, ITER78_VERDICT),
        "iter79": (iter79_report, ITER79_VERDICT),
        "iter80": (iter80_report, ITER80_VERDICT),
    }
    for label, (report, verdict) in expected_verdicts.items():
        if report.get("verdict") != verdict:
            problems.append(f"{label}-verdict-not-{verdict}")
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter78_index = event_index(iter78_report.get("events"), "iter78", problems)
    iter79_index = event_index(iter79_report.get("events"), "iter79", problems)
    iter80_index = event_index(iter80_report.get("events"), "iter80", problems)

    selected: list[dict[str, Any]] = []
    expected_event_count = sum(len(target["support_events"]) for target in FIXED_SUPPORT_OBJECTS)
    if len(iter78_index) != expected_event_count:
        problems.append(f"iter78-event-count-mismatch:{len(iter78_index)}")
    if len(iter79_index) != expected_event_count:
        problems.append(f"iter79-event-count-mismatch:{len(iter79_index)}")
    if len(iter80_index) != expected_event_count:
        problems.append(f"iter80-event-count-mismatch:{len(iter80_index)}")

    for target in FIXED_SUPPORT_OBJECTS:
        row_key = (target["audit_id"], target["scenario"])
        row59 = iter59_index.get(row_key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{row_key}")
            continue
        support_events: list[dict[str, Any]] = []
        for event in target["support_events"]:
            fixed_event = {
                "audit_id": target["audit_id"],
                "scenario": target["scenario"],
                "support_object_id": target["support_object_id"],
                **event,
            }
            event_key = (target["audit_id"], target["scenario"], event["role"])
            support_events.append(
                crosscheck_event(
                    fixed_event,
                    iter78_index.get(event_key),
                    iter79_index.get(event_key),
                    iter80_index.get(event_key),
                    event_key,
                    problems,
                )
            )
        selected.append({"target": target, "iter59": row59, "support_events": support_events})
    if len(selected) != len(FIXED_SUPPORT_OBJECTS):
        problems.append(f"fixed-object-count-mismatch:{len(selected)}")
    return selected, problems


def state_for_metric(metric: dict[str, Any]) -> str:
    if metric.get("cpa_active_logged_threshold") or metric.get("ttc_active_logged_threshold"):
        return "active"
    if metric.get("cpa_borderline_registered") or metric.get("ttc_borderline_registered"):
        return "borderline"
    return "subthreshold"


def metric_for_object(row: dict[str, Any], object_id: Any, problems: list[str]) -> dict[str, Any] | None:
    try:
        object_metrics = ITER62.object_metrics(row)
    except (KeyError, TypeError, ValueError) as exc:
        problems.append(f"object-metrics-failed:{exc}")
        return None
    matches = [metric for metric in object_metrics if same_object_id(metric.get("object_id"), object_id)]
    if len(matches) > 1:
        problems.append(f"support-object-duplicate:{object_id}")
        return None
    if not matches:
        return None
    cpa_margin, ttc_thresh = ITER78.channel_thresholds(row, problems)
    metric, state = ITER79.augment_metric(matches[0], cpa_margin, ttc_thresh)
    if metric is None or state is None:
        return None
    metric["state"] = state
    return metric


def analyze_target(item: dict[str, Any]) -> dict[str, Any]:
    target = item["target"]
    row59 = item["iter59"]
    support_events = item["support_events"]
    object_id = target["support_object_id"]
    problems: list[str] = []
    episode_dir = row59.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        decision_rows: list[dict[str, Any]] = []
        foreground_ts = None
    else:
        ep_dir = Path(episode_dir)
        decision_rows, row_problems = SWITCH.load_decision_rows(ep_dir / "sentinel_iter48_decisions.jsonl")
        foreground_ts = first_foreground_ts(ep_dir / "eval.json", problems)
        problems.extend(row_problems)

    frames: list[dict[str, Any]] = []
    for idx, row in enumerate(decision_rows):
        ts = surface_margin.number(row.get("ts", row.get("frame_index")), f"decision.ts:{idx}", problems)
        if ts is None:
            continue
        metric = metric_for_object(row, object_id, problems)
        record: dict[str, Any] = {
            "frame_index": row.get("frame_index", idx),
            "ts": ts,
            "relative_to_first_foreground": relative_time(ts, foreground_ts),
            "object_present": metric is not None,
            "fired": bool(row.get("fired")),
            "brake": bool(row.get("brake")),
        }
        if metric is not None:
            record.update(metric)
        frames.append(record)

    present_frames = [frame for frame in frames if frame["object_present"]]
    active_frames = [frame for frame in present_frames if frame.get("state") == "active"]
    borderline_frames = [frame for frame in present_frames if frame.get("state") == "borderline"]
    first_active_ts = active_frames[0]["ts"] if active_frames else None
    first_borderline_ts = borderline_frames[0]["ts"] if borderline_frames else None
    finite_ttc = [
        frame["ttc"]
        for frame in present_frames
        if isinstance(frame.get("ttc"), (int, float)) and not isinstance(frame.get("ttc"), bool)
    ]
    event_timing = []
    for event in support_events:
        event_timing.append(
            event
            | {
                "first_active_relative_to_event": relative_time(first_active_ts, float(event["event_ts"])),
                "first_borderline_relative_to_event": relative_time(first_borderline_ts, float(event["event_ts"])),
            }
        )

    if problems:
        row_label = "support_object_temporal_insufficient"
    elif active_frames:
        row_label = "support_object_ever_active"
    elif borderline_frames:
        row_label = "support_object_borderline_only"
    elif present_frames:
        row_label = "support_object_visible_never_surface"
    else:
        row_label = "support_object_temporal_insufficient"

    return {
        "audit_id": target["audit_id"],
        "scenario": target["scenario"],
        "support_object_id": object_id,
        "first_foreground_ts": foreground_ts,
        "support_events": event_timing,
        "decision_frame_count": len(frames),
        "present_frame_count": len(present_frames),
        "absent_frame_count": sum(not frame["object_present"] for frame in frames),
        "active_frame_count": len(active_frames),
        "borderline_frame_count": len(borderline_frames),
        "first_present_ts": present_frames[0]["ts"] if present_frames else None,
        "last_present_ts": present_frames[-1]["ts"] if present_frames else None,
        "first_active_ts": first_active_ts,
        "first_borderline_ts": first_borderline_ts,
        "first_active_relative_to_first_foreground": relative_time(first_active_ts, foreground_ts),
        "first_borderline_relative_to_first_foreground": relative_time(first_borderline_ts, foreground_ts),
        "min_cpa": min((frame["min_cpa"] for frame in present_frames), default=None),
        "min_finite_ttc": min(finite_ttc) if finite_ttc else None,
        "first_active_frame": compact_frame(active_frames[0] if active_frames else None),
        "first_borderline_frame": compact_frame(borderline_frames[0] if borderline_frames else None),
        "best_cpa_frame": compact_frame(min(present_frames, key=lambda frame: frame["min_cpa"]) if present_frames else None),
        "best_ttc_frame": compact_frame(
            min(
                (
                    frame
                    for frame in present_frames
                    if isinstance(frame.get("ttc"), (int, float)) and not isinstance(frame.get("ttc"), bool)
                ),
                key=lambda frame: frame["ttc"],
                default=None,
            )
        ),
        "row_label": row_label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_SUPPORT_OBJECTS)
        or any(row.get("problems") for row in rows)
        or "support_object_temporal_insufficient" in labels
    ):
        return "HUGSIM_SUPPORT_OBJECT_TEMPORAL_BLOCKED"
    if "support_object_ever_active" in labels:
        return "HUGSIM_SUPPORT_OBJECT_EVER_ACTIVE_COMPLETE"
    if "support_object_borderline_only" in labels:
        return "HUGSIM_SUPPORT_OBJECT_BORDERLINE_ONLY_COMPLETE"
    if all(label == "support_object_visible_never_surface" for label in labels):
        return "HUGSIM_SUPPORT_OBJECT_VISIBLE_NEVER_SURFACE_COMPLETE"
    return "HUGSIM_SUPPORT_OBJECT_TEMPORAL_MIXED_COMPLETE"


def build_report(
    iter59_report_path: Path,
    iter78_report_path: Path,
    iter79_report_path: Path,
    iter80_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter78_report, problems78 = surface_margin.load_report(iter78_report_path, "iter78-report")
    iter79_report, problems79 = surface_margin.load_report(iter79_report_path, "iter79-report")
    iter80_report, problems80 = surface_margin.load_report(iter80_report_path, "iter80-report")
    infra_problems.extend(problems59 + problems78 + problems79 + problems80)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter59_report, iter78_report, iter79_report, iter80_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_target(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 81,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter78_report": str(iter78_report_path),
            "iter79_report": str(iter79_report_path),
            "iter80_report": str(iter80_report_path),
        },
        "fixed_support_objects": list(FIXED_SUPPORT_OBJECTS),
        "infra_problems": infra_problems,
        "objects": rows,
        "summary": {
            "target_objects": len(selected),
            "evaluated_objects": sum(not row.get("problems") for row in rows),
            "object_label_counts": dict(sorted(label_counts.items())),
            "ever_active_objects": sum(row.get("row_label") == "support_object_ever_active" for row in rows),
            "borderline_only_objects": sum(
                row.get("row_label") == "support_object_borderline_only" for row in rows
            ),
            "visible_never_surface_objects": sum(
                row.get("row_label") == "support_object_visible_never_surface" for row in rows
            ),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "two-object descriptive temporal surface audit only; no actor-causality, repair, "
            "threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 81 - HUGSIM support-object temporal surface audit",
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
        "## Objects",
        "",
        "| audit id | support id | label | present frames | active frames | borderline frames | first active | first borderline | min cpa | min ttc | problems |",
        "|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ])
    for row in report["objects"]:
        lines.append(
            f"| `{row['audit_id']}` | `{row['support_object_id']}` | `{row['row_label']}` | "
            f"`{row['present_frame_count']}` | `{row['active_frame_count']}` | "
            f"`{row['borderline_frame_count']}` | `{row.get('first_active_ts')}` | "
            f"`{row.get('first_borderline_ts')}` | `{row.get('min_cpa')}` | "
            f"`{row.get('min_finite_ttc')}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter78_report: Path,
    iter79_report: Path,
    iter80_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter78_report, iter79_report, iter80_report)
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
        "--iter78-report",
        type=Path,
        default=Path("experiments/iter78_hugsim_support_object_ranking/proof-ranking/ranking_report.json"),
    )
    parser.add_argument(
        "--iter79-report",
        type=Path,
        default=Path("experiments/iter79_hugsim_selected_surface_decomposition/proof-selected/selected_report.json"),
    )
    parser.add_argument(
        "--iter80-report",
        type=Path,
        default=Path("experiments/iter80_hugsim_selected_all_provenance_bridge/proof-all-provenance/all_provenance_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter81_hugsim_support_object_temporal_surface/proof-temporal/temporal_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter81_hugsim_support_object_temporal_surface/proof-temporal/temporal.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_report,
        args.iter78_report,
        args.iter79_report,
        args.iter80_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
