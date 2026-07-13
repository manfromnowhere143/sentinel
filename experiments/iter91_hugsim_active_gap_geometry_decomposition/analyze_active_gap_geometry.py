#!/usr/bin/env python3
"""Iteration 91 HUGSIM active-gap geometry decomposition."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER90_VERDICT = "HUGSIM_ACTIVE_SURFACE_PROVENANCE_GAP_COMPLETE"
EXPECTED_ITER90_LABELS = {
    "active_surface_absent_bridge_supported_nonactive": 2,
    "active_surface_present_no_bridge_supported": 1,
}


def _load_module(relative_path: str, module_name: str) -> Any:
    repo = Path(__file__).resolve().parents[2]
    module_path = repo / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-module:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ITER90 = _load_module(
    "experiments/iter90_hugsim_active_surface_provenance_gap/analyze_active_surface_provenance_gap.py",
    "iter90_active_surface_provenance_gap",
)
ITER89 = ITER90.ITER89
ITER85 = ITER90.ITER85
ITER80 = ITER90.ITER80
SWITCH = ITER90.SWITCH
surface_margin = ITER90.surface_margin
FIXED_ROWS = ITER90.FIXED_ROWS


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def bridge_supported(bridge: dict[str, Any]) -> bool:
    return ITER90.bridge_supported(bridge)


def event_index(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return ITER90.event_index(rows, label, problems)


def joint_class(metric: dict[str, Any], bridge: dict[str, Any]) -> str:
    return ITER90.joint_class(metric, bridge)


def compact_bridge_geometry(bridge: dict[str, Any]) -> dict[str, Any]:
    best = bridge.get("best_variant")
    geometry = {
        "distance_band": bridge.get("distance_band"),
        "best_distance_m": bridge.get("best_distance_m"),
        "best_variant": None,
    }
    if isinstance(best, dict):
        geometry["best_variant"] = {
            "foreground_timestamp": best.get("foreground_timestamp"),
            "foreground_obs_index": best.get("foreground_obs_index"),
            "foreground_obs_name": best.get("foreground_obs_name"),
            "temporal_source": best.get("temporal_source"),
            "axis_order": best.get("axis_order"),
            "forward_sign": best.get("forward_sign"),
            "lateral_sign": best.get("lateral_sign"),
            "monitor_forward_lateral": best.get("monitor_forward_lateral"),
            "hugsim_forward_lateral": best.get("hugsim_forward_lateral"),
            "lead_time_s": best.get("lead_time_s"),
            "distance_m": best.get("distance_m"),
        }
    return geometry


def compact_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    metric = candidate.get("metric") or {}
    return {
        "object_id": candidate.get("object_id"),
        "joint_class": candidate.get("joint_class"),
        "state": metric.get("state"),
        "min_cpa": metric.get("min_cpa"),
        "cpa_rank": metric.get("cpa_rank"),
        "ttc": metric.get("ttc"),
        "ttc_rank": metric.get("ttc_rank"),
        "gap": metric.get("gap"),
        "closing": metric.get("closing"),
        "score": metric.get("score"),
        "active_cpa_margin_m": metric.get("active_cpa_margin_m"),
        "active_ttc_margin_s": metric.get("active_ttc_margin_s"),
        "bridge_geometry": compact_bridge_geometry(candidate.get("bridge") or {}),
    }


def active_surface_margin_key(candidate: dict[str, Any]) -> tuple[int, float, float, float, str]:
    metric = candidate.get("metric") or {}
    state_rank = {"active": 0, "borderline": 1, "subthreshold": 2}.get(str(metric.get("state")), 3)
    cpa_margin = metric.get("active_cpa_margin_m")
    ttc_margin = metric.get("active_ttc_margin_s")
    cpa_rank = metric.get("cpa_rank")
    return (
        state_rank,
        float(cpa_margin) if finite_number(cpa_margin) else math.inf,
        float(ttc_margin) if finite_number(ttc_margin) else math.inf,
        float(cpa_rank) if finite_number(cpa_rank) else math.inf,
        str(candidate.get("object_id")),
    )


def classify_row(candidates: list[dict[str, Any]], problems: list[str]) -> str:
    if problems or not candidates:
        return "active_gap_geometry_insufficient"
    active = [candidate for candidate in candidates if (candidate.get("metric") or {}).get("state") == "active"]
    bridge = [candidate for candidate in candidates if bridge_supported(candidate.get("bridge") or {})]
    active_bridge = [
        candidate
        for candidate in active
        if bridge_supported(candidate.get("bridge") or {})
    ]
    bridge_nonactive = [
        candidate
        for candidate in bridge
        if (candidate.get("metric") or {}).get("state") != "active"
    ]
    if active_bridge:
        return "path_provenance_coincident"
    if not bridge:
        return "geometry_no_bridge_support"
    if not active:
        return "provenance_near_path_inactive"
    if active and bridge_nonactive:
        return "path_active_provenance_far_with_bridge_nonactive"
    return "active_gap_geometry_insufficient"


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter90_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter59_report.get("infra_problems"):
        problems.append(f"iter59-infra-problems:{iter59_report.get('infra_problems')}")
    if iter90_report.get("verdict") != ITER90_VERDICT:
        problems.append(f"iter90-verdict-not-{ITER90_VERDICT}")
    if iter90_report.get("infra_problems"):
        problems.append(f"iter90-infra-problems:{iter90_report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter90_index = event_index(iter90_report.get("events"), "iter90", problems)
    if len(iter90_index) != len(FIXED_ROWS):
        problems.append(f"iter90-event-count-mismatch:{len(iter90_index)}")
    label_counts = Counter(row.get("row_label") for row in iter90_report.get("events", []))
    if dict(label_counts) != EXPECTED_ITER90_LABELS:
        problems.append(f"iter90-label-counts-mismatch:{dict(label_counts)}")
    summary = iter90_report.get("summary") or {}
    if int(summary.get("active_bridge_supported_total", -1)) != 0:
        problems.append("iter90-active-bridge-supported-total-not-zero")

    selected: list[dict[str, Any]] = []
    for target in FIXED_ROWS:
        row_key = (target["audit_id"], target["scenario"])
        event_key = (target["audit_id"], target["scenario"], target["role"])
        row59 = iter59_index.get(row_key)
        row90 = iter90_index.get(event_key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{row_key}")
            continue
        if row90 is None:
            problems.append(f"missing-iter90-event:{event_key}")
            continue
        if row90.get("problems"):
            problems.append(f"iter90-event-problems:{event_key}:{row90.get('problems')}")
        if not same_object_id(row90.get("support_object_id"), target["support_object_id"]):
            problems.append(f"iter90-support-object-mismatch:{event_key}:{row90.get('support_object_id')}")
        replay_ts = surface_margin.number(row90.get("replay_ts"), f"iter90.replay_ts:{event_key}", problems)
        if replay_ts is not None and not math.isclose(replay_ts, float(target["replay_ts"]), abs_tol=1e-6):
            problems.append(f"iter90-replay-ts-mismatch:{event_key}:{replay_ts}")
        if row90.get("replay_alignment") != target["alignment"]:
            problems.append(f"iter90-alignment-mismatch:{event_key}:{row90.get('replay_alignment')}")
        if int(row90.get("active_bridge_supported_count", -1)) != 0:
            problems.append(f"iter90-active-bridge-count-not-zero:{event_key}")
        selected.append({"target": target, "iter59": row59, "iter90": row90})
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
                best = bridge.get("best_variant")
                if not isinstance(best, dict):
                    problems.append(f"candidate-best-variant-missing:{object_id}")
                    continue
                candidate = {
                    "object_id": object_id,
                    "metric": metric,
                    "bridge": bridge,
                    "joint_class": joint_class(metric, bridge),
                }
                candidates.append(candidate)

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
    nearest_active_by_bridge = min(
        active_candidates,
        key=lambda item: ((item.get("bridge") or {}).get("best_distance_m", math.inf), str(item.get("object_id"))),
        default=None,
    )
    nearest_bridge_by_surface = min(bridge_candidates, key=active_surface_margin_key, default=None)
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
        "nearest_active_by_bridge": compact_candidate(nearest_active_by_bridge) if nearest_active_by_bridge else None,
        "nearest_bridge_by_surface": compact_candidate(nearest_bridge_by_surface)
        if nearest_bridge_by_surface
        else None,
        "row_label": label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_ROWS)
        or any(row.get("problems") for row in rows)
        or "active_gap_geometry_insufficient" in labels
    ):
        return "HUGSIM_ACTIVE_GAP_GEOMETRY_BLOCKED"
    if "path_provenance_coincident" in labels:
        return "HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_COINCIDENT_COMPLETE"
    if (
        all(
            label in {
                "provenance_near_path_inactive",
                "path_active_provenance_far_with_bridge_nonactive",
            }
            for label in labels
        )
        and "provenance_near_path_inactive" in labels
        and "path_active_provenance_far_with_bridge_nonactive" in labels
        and sum(int(row.get("active_bridge_supported_count", 0)) for row in rows) == 0
    ):
        return "HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE"
    return "HUGSIM_ACTIVE_GAP_GEOMETRY_MIXED_COMPLETE"


def build_report(iter59_report_path: Path, iter90_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter90_report, problems90 = surface_margin.load_report(iter90_report_path, "iter90-report")
    infra_problems.extend(problems59 + problems90)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter59_report, iter90_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_target(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 91,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter90_report": str(iter90_report_path),
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
            "bridge_supported_nonactive_total": sum(
                int(row.get("bridge_supported_nonactive_count", 0)) for row in rows
            ),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "three-row descriptive active-gap geometry decomposition only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, real-world behavior, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 91 - HUGSIM active-gap geometry decomposition",
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
        "| audit id | event | replay ts | active | bridge-supported | active+bridge | nearest active bridge band | nearest active bridge distance | nearest bridge state | nearest bridge distance | label | problems |",
        "|---|---|---:|---:|---:|---:|---|---:|---|---:|---|---|",
    ])
    for row in report["events"]:
        active = row.get("nearest_active_by_bridge") or {}
        active_bridge = active.get("bridge_geometry") or {}
        bridge = row.get("nearest_bridge_by_surface") or {}
        bridge_geometry = bridge.get("bridge_geometry") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{row.get('replay_ts')}` | "
            f"`{row.get('active_object_count')}` | `{row.get('bridge_supported_count')}` | "
            f"`{row.get('active_bridge_supported_count')}` | `{active_bridge.get('distance_band')}` | "
            f"`{active_bridge.get('best_distance_m')}` | `{bridge.get('state')}` | "
            f"`{bridge_geometry.get('best_distance_m')}` | `{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter59_report: Path, iter90_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter59_report, iter90_report)
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
        "--iter90-report",
        type=Path,
        default=Path(
            "experiments/iter90_hugsim_active_surface_provenance_gap/proof-gap/"
            "active_surface_provenance_gap_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter91_hugsim_active_gap_geometry_decomposition/proof-geometry/"
            "active_gap_geometry_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter91_hugsim_active_gap_geometry_decomposition/proof-geometry/"
            "active_gap_geometry.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter59_report, args.iter90_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
