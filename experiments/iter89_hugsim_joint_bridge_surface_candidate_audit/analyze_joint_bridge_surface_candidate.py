#!/usr/bin/env python3
"""Iteration 89 HUGSIM joint bridge/surface candidate audit."""

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
ITER87_VERDICT = "HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE"
ITER88_VERDICT = "HUGSIM_BRIDGE_SURFACE_MARGIN_RESIDUAL_SPLIT_COMPLETE"
SUPPORTED_BANDS = {"match", "ambiguous"}
FIXED_ROWS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "role": "pre",
        "support_object_id": 9,
        "replay_ts": 5.5,
        "alignment": "exact_bridge_ts",
        "iter88_label": "bridge_surface_ttc_borderline_cpa_far",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "pre",
        "support_object_id": 10,
        "replay_ts": 4.0,
        "alignment": "exact_bridge_ts",
        "iter88_label": "bridge_surface_no_finite_ttc_cpa_far",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "active",
        "support_object_id": 10,
        "replay_ts": 5.75,
        "alignment": "nearest_before_bridge_ts",
        "iter88_label": "bridge_surface_no_finite_ttc_cpa_far",
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


ITER87 = _load_module(
    "experiments/iter87_hugsim_interval_bridge_time_surface_replay/"
    "analyze_interval_bridge_time_surface_replay.py",
    "iter87_interval_bridge_time_surface_replay",
)
ITER85 = ITER87.ITER85
ITER80 = ITER85.ITER80
SWITCH = ITER87.SWITCH
surface_margin = ITER87.surface_margin


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def bridge_supported(bridge: dict[str, Any]) -> bool:
    return bridge.get("distance_band") in SUPPORTED_BANDS


def event_index(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return ITER87.event_index(rows, label, problems)


def compact_metric(metric: dict[str, Any] | None) -> dict[str, Any] | None:
    return ITER85.compact_metric(metric)


def compact_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    metric = candidate.get("metric") or {}
    bridge = candidate.get("bridge") or {}
    return {
        "object_id": candidate.get("object_id"),
        "joint_class": candidate.get("joint_class"),
        "state": metric.get("state"),
        "min_cpa": metric.get("min_cpa"),
        "cpa_rank": metric.get("cpa_rank"),
        "ttc": metric.get("ttc"),
        "ttc_rank": metric.get("ttc_rank"),
        "bridge_band": bridge.get("distance_band"),
        "bridge_best_distance_m": bridge.get("best_distance_m"),
    }


def joint_class(metric: dict[str, Any], bridge: dict[str, Any]) -> str:
    supported = bridge_supported(bridge)
    state = metric.get("state")
    if supported and state == "active":
        return "active_bridge_supported"
    if supported and state == "borderline":
        return "borderline_bridge_supported"
    if supported and state == "subthreshold":
        return "subthreshold_bridge_supported"
    if not supported and state == "active":
        return "active_no_bridge_support"
    if not supported and state == "borderline":
        return "borderline_no_bridge_support"
    return "subthreshold_no_bridge_support"


def classify_row(
    candidates: list[dict[str, Any]],
    support_candidate: dict[str, Any] | None,
    problems: list[str],
) -> str:
    if problems:
        return "joint_bridge_surface_candidate_insufficient"
    if not candidates or support_candidate is None:
        return "joint_bridge_surface_candidate_insufficient"
    if any(candidate.get("joint_class") == "active_bridge_supported" for candidate in candidates):
        return "active_bridge_candidate_present"
    if not any(bridge_supported(candidate.get("bridge") or {}) for candidate in candidates):
        return "no_bridge_supported_candidate"
    if (
        bridge_supported(support_candidate.get("bridge") or {})
        and (support_candidate.get("metric") or {}).get("state") == "borderline"
    ):
        return "no_active_bridge_candidate_support_borderline"
    if (
        bridge_supported(support_candidate.get("bridge") or {})
        and (support_candidate.get("metric") or {}).get("state") == "subthreshold"
    ):
        return "no_active_bridge_candidate_support_subthreshold"
    return "joint_bridge_surface_candidate_insufficient"


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter85_report: dict[str, Any],
    iter87_report: dict[str, Any],
    iter88_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter85": (iter85_report, ITER85_VERDICT),
        "iter87": (iter87_report, ITER87_VERDICT),
        "iter88": (iter88_report, ITER88_VERDICT),
    }
    for label, (report, verdict) in expected_verdicts.items():
        if report.get("verdict") != verdict:
            problems.append(f"{label}-verdict-not-{verdict}")
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter85_index = event_index(iter85_report.get("events"), "iter85", problems)
    iter87_index = event_index(iter87_report.get("events"), "iter87", problems)
    iter88_index = event_index(iter88_report.get("events"), "iter88", problems)
    if len(iter85_index) != len(FIXED_ROWS):
        problems.append(f"iter85-event-count-mismatch:{len(iter85_index)}")
    if len(iter87_index) != len(FIXED_ROWS):
        problems.append(f"iter87-event-count-mismatch:{len(iter87_index)}")
    if len(iter88_index) != len(FIXED_ROWS):
        problems.append(f"iter88-event-count-mismatch:{len(iter88_index)}")

    selected: list[dict[str, Any]] = []
    for target in FIXED_ROWS:
        row_key = (target["audit_id"], target["scenario"])
        event_key = (target["audit_id"], target["scenario"], target["role"])
        row59 = iter59_index.get(row_key)
        row85 = iter85_index.get(event_key)
        row87 = iter87_index.get(event_key)
        row88 = iter88_index.get(event_key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{row_key}")
            continue
        if row85 is None:
            problems.append(f"missing-iter85-event:{event_key}")
            continue
        if row87 is None:
            problems.append(f"missing-iter87-event:{event_key}")
            continue
        if row88 is None:
            problems.append(f"missing-iter88-event:{event_key}")
            continue
        for report_label, row in (("iter85", row85), ("iter87", row87), ("iter88", row88)):
            if row.get("problems"):
                problems.append(f"{report_label}-event-problems:{event_key}:{row.get('problems')}")
            if not same_object_id(row.get("support_object_id"), target["support_object_id"]):
                problems.append(
                    f"{report_label}-support-object-mismatch:{event_key}:{row.get('support_object_id')}"
                )
        if bridge_supported(row85.get("selected_bridge") or {}):
            problems.append(f"iter85-selected-bridge-supported:{event_key}")
        if not bridge_supported(row85.get("support_bridge") or {}):
            problems.append(f"iter85-support-bridge-not-supported:{event_key}")
        selection = row87.get("selection")
        if not isinstance(selection, dict):
            problems.append(f"iter87-selection-not-dict:{event_key}")
        else:
            replay_ts = surface_margin.number(selection.get("replay_ts"), f"iter87.replay_ts:{event_key}", problems)
            if replay_ts is not None and not math.isclose(replay_ts, float(target["replay_ts"]), abs_tol=1e-6):
                problems.append(f"iter87-replay-ts-mismatch:{event_key}:{replay_ts}")
            if selection.get("alignment") != target["alignment"]:
                problems.append(f"iter87-alignment-mismatch:{event_key}:{selection.get('alignment')}")
        if row88.get("row_label") != target["iter88_label"]:
            problems.append(f"iter88-label-mismatch:{event_key}:{row88.get('row_label')}")
        selected.append({"target": target, "iter59": row59, "iter85": row85, "iter87": row87, "iter88": row88})
    if len(selected) != len(FIXED_ROWS):
        problems.append(f"fixed-row-count-mismatch:{len(selected)}")
    return selected, problems


def analyze_target(item: dict[str, Any]) -> dict[str, Any]:
    target = item["target"]
    row59 = item["iter59"]
    problems: list[str] = []
    replay_ts = surface_margin.number(target.get("replay_ts"), "target.replay_ts", problems)
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

    replay_row = SWITCH.find_decision_row(decision_rows, replay_ts, "replay", problems) if replay_ts is not None else None
    candidates: list[dict[str, Any]] = []
    support_candidate: dict[str, Any] | None = None
    if replay_row is not None and replay_ts is not None:
        objs = replay_row.get("objs")
        if not isinstance(objs, list):
            problems.append("replay-objs-not-list")
        else:
            for obj in objs:
                if not isinstance(obj, dict):
                    problems.append("replay-obj-not-dict")
                    continue
                object_id = obj.get("id")
                metric = ITER85.metric_with_horizon_timing(replay_row, object_id, replay_ts, "candidate", problems)
                if metric is None:
                    continue
                bridge = ITER85.object_bridge(replay_row, replay_ts, obj, "candidate", provenance_rows, problems)
                candidate = {
                    "object_id": object_id,
                    "metric": metric,
                    "bridge": bridge,
                    "joint_class": joint_class(metric, bridge),
                }
                candidates.append(candidate)
                if same_object_id(object_id, target["support_object_id"]):
                    support_candidate = candidate
    label = classify_row(candidates, support_candidate, problems)
    joint_counts = Counter(candidate.get("joint_class") for candidate in candidates)
    return {
        "audit_id": target["audit_id"],
        "scenario": target["scenario"],
        "event_role": target["role"],
        "support_object_id": target["support_object_id"],
        "replay_ts": replay_ts,
        "replay_alignment": target["alignment"],
        "object_count": len(candidates),
        "joint_class_counts": dict(sorted(joint_counts.items())),
        "active_bridge_supported_count": joint_counts.get("active_bridge_supported", 0),
        "bridge_supported_count": sum(1 for candidate in candidates if bridge_supported(candidate.get("bridge") or {})),
        "support_candidate": compact_candidate(support_candidate) if support_candidate is not None else None,
        "top_bridge_candidates": [
            compact_candidate(candidate)
            for candidate in sorted(
                (candidate for candidate in candidates if bridge_supported(candidate.get("bridge") or {})),
                key=lambda item: (
                    (item.get("bridge") or {}).get("best_distance_m", math.inf),
                    str(item.get("object_id")),
                ),
            )[:5]
        ],
        "row_label": label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_ROWS)
        or any(row.get("problems") for row in rows)
        or "joint_bridge_surface_candidate_insufficient" in labels
    ):
        return "HUGSIM_JOINT_BRIDGE_SURFACE_CANDIDATE_BLOCKED"
    if "active_bridge_candidate_present" in labels:
        return "HUGSIM_JOINT_BRIDGE_SURFACE_ACTIVE_CANDIDATE_PRESENT_COMPLETE"
    if (
        all(
            label in {
                "no_active_bridge_candidate_support_borderline",
                "no_active_bridge_candidate_support_subthreshold",
            }
            for label in labels
        )
        and "no_active_bridge_candidate_support_borderline" in labels
        and "no_active_bridge_candidate_support_subthreshold" in labels
    ):
        return "HUGSIM_JOINT_BRIDGE_SURFACE_NO_ACTIVE_CANDIDATE_SPLIT_COMPLETE"
    return "HUGSIM_JOINT_BRIDGE_SURFACE_CANDIDATE_MIXED_COMPLETE"


def build_report(
    iter59_report_path: Path,
    iter85_report_path: Path,
    iter87_report_path: Path,
    iter88_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter85_report, problems85 = surface_margin.load_report(iter85_report_path, "iter85-report")
    iter87_report, problems87 = surface_margin.load_report(iter87_report_path, "iter87-report")
    iter88_report, problems88 = surface_margin.load_report(iter88_report_path, "iter88-report")
    infra_problems.extend(problems59 + problems85 + problems87 + problems88)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter59_report, iter85_report, iter87_report, iter88_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_target(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 89,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter85_report": str(iter85_report_path),
            "iter87_report": str(iter87_report_path),
            "iter88_report": str(iter88_report_path),
        },
        "fixed_rows": list(FIXED_ROWS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_rows": len(selected),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "active_bridge_candidate_events": sum(row.get("active_bridge_supported_count", 0) > 0 for row in rows),
            "bridge_supported_object_total": sum(int(row.get("bridge_supported_count", 0)) for row in rows),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "three-row descriptive joint bridge/surface candidate audit only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, real-world behavior, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 89 - HUGSIM joint bridge/surface candidate audit",
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
        "| audit id | event | replay ts | objects | bridge-supported | active+bridge | support class | support state | support bridge | label | problems |",
        "|---|---|---:|---:|---:|---:|---|---|---|---|---|",
    ])
    for row in report["events"]:
        support = row.get("support_candidate") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{row.get('replay_ts')}` | "
            f"`{row.get('object_count')}` | `{row.get('bridge_supported_count')}` | "
            f"`{row.get('active_bridge_supported_count')}` | `{support.get('joint_class')}` | "
            f"`{support.get('state')}` | `{support.get('bridge_band')}` | "
            f"`{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter85_report: Path,
    iter87_report: Path,
    iter88_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter85_report, iter87_report, iter88_report)
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
        "--iter87-report",
        type=Path,
        default=Path(
            "experiments/iter87_hugsim_interval_bridge_time_surface_replay/proof-interval/"
            "interval_bridge_time_surface_replay_report.json"
        ),
    )
    parser.add_argument(
        "--iter88-report",
        type=Path,
        default=Path(
            "experiments/iter88_hugsim_bridge_surface_margin_residual/proof-residual/"
            "bridge_surface_margin_residual_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter89_hugsim_joint_bridge_surface_candidate_audit/proof-candidates/"
            "joint_bridge_surface_candidate_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter89_hugsim_joint_bridge_surface_candidate_audit/proof-candidates/"
            "joint_bridge_surface_candidate.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_report,
        args.iter85_report,
        args.iter87_report,
        args.iter88_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
