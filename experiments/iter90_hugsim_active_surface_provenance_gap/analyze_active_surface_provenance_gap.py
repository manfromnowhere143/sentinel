#!/usr/bin/env python3
"""Iteration 90 HUGSIM active-surface/provenance gap audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER87_VERDICT = "HUGSIM_INTERVAL_BRIDGE_TIME_SURFACE_REPLAY_MIXED_COMPLETE"
ITER89_VERDICT = "HUGSIM_JOINT_BRIDGE_SURFACE_NO_ACTIVE_CANDIDATE_SPLIT_COMPLETE"
FIXED_ROWS = (
    {
        "audit_id": "both_distinct_extreme",
        "scenario": "scene-0138-extreme-00",
        "role": "pre",
        "support_object_id": 9,
        "replay_ts": 5.5,
        "alignment": "exact_bridge_ts",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "pre",
        "support_object_id": 10,
        "replay_ts": 4.0,
        "alignment": "exact_bridge_ts",
    },
    {
        "audit_id": "ttc_medium_a",
        "scenario": "scene-0071-medium-01",
        "role": "active",
        "support_object_id": 10,
        "replay_ts": 5.75,
        "alignment": "nearest_before_bridge_ts",
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


ITER89 = _load_module(
    "experiments/iter89_hugsim_joint_bridge_surface_candidate_audit/"
    "analyze_joint_bridge_surface_candidate.py",
    "iter89_joint_bridge_surface_candidate",
)
ITER87 = ITER89.ITER87
ITER85 = ITER89.ITER85
ITER80 = ITER89.ITER80
SWITCH = ITER89.SWITCH
surface_margin = ITER89.surface_margin


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def bridge_supported(bridge: dict[str, Any]) -> bool:
    return ITER89.bridge_supported(bridge)


def event_index(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return ITER89.event_index(rows, label, problems)


def compact_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    return ITER89.compact_candidate(candidate)


def joint_class(metric: dict[str, Any], bridge: dict[str, Any]) -> str:
    return ITER89.joint_class(metric, bridge)


def classify_row(candidates: list[dict[str, Any]], problems: list[str]) -> str:
    if problems or not candidates:
        return "active_surface_provenance_gap_insufficient"
    active = [candidate for candidate in candidates if (candidate.get("metric") or {}).get("state") == "active"]
    bridge = [candidate for candidate in candidates if bridge_supported(candidate.get("bridge") or {})]
    active_bridge = [
        candidate
        for candidate in candidates
        if (candidate.get("metric") or {}).get("state") == "active"
        and bridge_supported(candidate.get("bridge") or {})
    ]
    bridge_nonactive = [
        candidate
        for candidate in bridge
        if (candidate.get("metric") or {}).get("state") != "active"
    ]
    if active_bridge:
        return "active_surface_bridge_supported_present"
    if not bridge:
        return "active_surface_no_bridge_support"
    if not active:
        return "active_surface_absent_bridge_supported_nonactive"
    if active and bridge_nonactive:
        return "active_surface_present_no_bridge_supported"
    return "active_surface_provenance_gap_insufficient"


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter87_report: dict[str, Any],
    iter89_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter87": (iter87_report, ITER87_VERDICT),
        "iter89": (iter89_report, ITER89_VERDICT),
    }
    for label, (report, verdict) in expected_verdicts.items():
        if report.get("verdict") != verdict:
            problems.append(f"{label}-verdict-not-{verdict}")
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter87_index = event_index(iter87_report.get("events"), "iter87", problems)
    iter89_index = event_index(iter89_report.get("events"), "iter89", problems)
    if len(iter87_index) != len(FIXED_ROWS):
        problems.append(f"iter87-event-count-mismatch:{len(iter87_index)}")
    if len(iter89_index) != len(FIXED_ROWS):
        problems.append(f"iter89-event-count-mismatch:{len(iter89_index)}")
    if int((iter89_report.get("summary") or {}).get("active_bridge_candidate_events", -1)) != 0:
        problems.append("iter89-active-bridge-candidate-events-not-zero")

    selected: list[dict[str, Any]] = []
    for target in FIXED_ROWS:
        row_key = (target["audit_id"], target["scenario"])
        event_key = (target["audit_id"], target["scenario"], target["role"])
        row59 = iter59_index.get(row_key)
        row87 = iter87_index.get(event_key)
        row89 = iter89_index.get(event_key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{row_key}")
            continue
        if row87 is None:
            problems.append(f"missing-iter87-event:{event_key}")
            continue
        if row89 is None:
            problems.append(f"missing-iter89-event:{event_key}")
            continue
        if row87.get("problems"):
            problems.append(f"iter87-event-problems:{event_key}:{row87.get('problems')}")
        if row89.get("problems"):
            problems.append(f"iter89-event-problems:{event_key}:{row89.get('problems')}")
        for report_label, row in (("iter87", row87), ("iter89", row89)):
            if not same_object_id(row.get("support_object_id"), target["support_object_id"]):
                problems.append(
                    f"{report_label}-support-object-mismatch:{event_key}:{row.get('support_object_id')}"
                )
        selection = row87.get("selection")
        if not isinstance(selection, dict):
            problems.append(f"iter87-selection-not-dict:{event_key}")
        else:
            replay_ts = surface_margin.number(selection.get("replay_ts"), f"iter87.replay_ts:{event_key}", problems)
            if replay_ts is not None and not math.isclose(replay_ts, float(target["replay_ts"]), abs_tol=1e-6):
                problems.append(f"iter87-replay-ts-mismatch:{event_key}:{replay_ts}")
            if selection.get("alignment") != target["alignment"]:
                problems.append(f"iter87-alignment-mismatch:{event_key}:{selection.get('alignment')}")
        iter89_replay_ts = surface_margin.number(row89.get("replay_ts"), f"iter89.replay_ts:{event_key}", problems)
        if iter89_replay_ts is not None and not math.isclose(
            iter89_replay_ts, float(target["replay_ts"]), abs_tol=1e-6
        ):
            problems.append(f"iter89-replay-ts-mismatch:{event_key}:{iter89_replay_ts}")
        if row89.get("replay_alignment") != target["alignment"]:
            problems.append(f"iter89-alignment-mismatch:{event_key}:{row89.get('replay_alignment')}")
        if int(row89.get("active_bridge_supported_count", -1)) != 0:
            problems.append(f"iter89-active-bridge-count-not-zero:{event_key}")
        selected.append({"target": target, "iter59": row59, "iter87": row87, "iter89": row89})
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

    active_candidates = [candidate for candidate in candidates if (candidate.get("metric") or {}).get("state") == "active"]
    bridge_candidates = [candidate for candidate in candidates if bridge_supported(candidate.get("bridge") or {})]
    active_bridge_candidates = [
        candidate
        for candidate in active_candidates
        if bridge_supported(candidate.get("bridge") or {})
    ]
    bridge_nonactive_candidates = [
        candidate
        for candidate in bridge_candidates
        if (candidate.get("metric") or {}).get("state") != "active"
    ]
    active_no_bridge_candidates = [
        candidate
        for candidate in active_candidates
        if not bridge_supported(candidate.get("bridge") or {})
    ]
    label = classify_row(candidates, problems)
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
        "active_object_count": len(active_candidates),
        "bridge_supported_count": len(bridge_candidates),
        "active_bridge_supported_count": len(active_bridge_candidates),
        "bridge_supported_nonactive_count": len(bridge_nonactive_candidates),
        "active_no_bridge_count": len(active_no_bridge_candidates),
        "support_candidate": compact_candidate(support_candidate) if support_candidate is not None else None,
        "active_candidates": [compact_candidate(candidate) for candidate in active_candidates],
        "bridge_supported_candidates": [
            compact_candidate(candidate)
            for candidate in sorted(
                bridge_candidates,
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
        or "active_surface_provenance_gap_insufficient" in labels
    ):
        return "HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_BLOCKED"
    if "active_surface_bridge_supported_present" in labels:
        return "HUGSIM_ACTIVE_SURFACE_BRIDGE_SUPPORTED_PRESENT_COMPLETE"
    if (
        all(
            label in {
                "active_surface_absent_bridge_supported_nonactive",
                "active_surface_present_no_bridge_supported",
            }
            for label in labels
        )
        and "active_surface_absent_bridge_supported_nonactive" in labels
        and "active_surface_present_no_bridge_supported" in labels
        and sum(int(row.get("active_bridge_supported_count", 0)) for row in rows) == 0
    ):
        return "HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_COMPLETE"
    return "HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_MIXED_COMPLETE"


def build_report(
    iter59_report_path: Path,
    iter87_report_path: Path,
    iter89_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter87_report, problems87 = surface_margin.load_report(iter87_report_path, "iter87-report")
    iter89_report, problems89 = surface_margin.load_report(iter89_report_path, "iter89-report")
    infra_problems.extend(problems59 + problems87 + problems89)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter59_report, iter87_report, iter89_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_target(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 90,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter87_report": str(iter87_report_path),
            "iter89_report": str(iter89_report_path),
        },
        "fixed_rows": list(FIXED_ROWS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_rows": len(selected),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "active_object_events": sum(int(row.get("active_object_count", 0)) > 0 for row in rows),
            "active_object_total": sum(int(row.get("active_object_count", 0)) for row in rows),
            "bridge_supported_object_total": sum(int(row.get("bridge_supported_count", 0)) for row in rows),
            "active_bridge_supported_total": sum(int(row.get("active_bridge_supported_count", 0)) for row in rows),
            "active_no_bridge_total": sum(int(row.get("active_no_bridge_count", 0)) for row in rows),
            "bridge_supported_nonactive_total": sum(
                int(row.get("bridge_supported_nonactive_count", 0)) for row in rows
            ),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "three-row descriptive active-surface/provenance gap audit only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, real-world behavior, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 90 - HUGSIM active-surface provenance gap audit",
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
        "| audit id | event | replay ts | objects | active | bridge-supported | active+bridge | active/no-bridge | bridge/non-active | label | problems |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ])
    for row in report["events"]:
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{row.get('replay_ts')}` | "
            f"`{row.get('object_count')}` | `{row.get('active_object_count')}` | "
            f"`{row.get('bridge_supported_count')}` | `{row.get('active_bridge_supported_count')}` | "
            f"`{row.get('active_no_bridge_count')}` | `{row.get('bridge_supported_nonactive_count')}` | "
            f"`{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter87_report: Path,
    iter89_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter87_report, iter89_report)
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
        "--iter87-report",
        type=Path,
        default=Path(
            "experiments/iter87_hugsim_interval_bridge_time_surface_replay/proof-interval/"
            "interval_bridge_time_surface_replay_report.json"
        ),
    )
    parser.add_argument(
        "--iter89-report",
        type=Path,
        default=Path(
            "experiments/iter89_hugsim_joint_bridge_surface_candidate_audit/proof-candidates/"
            "joint_bridge_surface_candidate_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter90_hugsim_active_surface_provenance_gap/proof-gap/"
            "active_surface_provenance_gap_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter90_hugsim_active_surface_provenance_gap/proof-gap/"
            "active_surface_provenance_gap.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter59_report, args.iter87_report, args.iter89_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
