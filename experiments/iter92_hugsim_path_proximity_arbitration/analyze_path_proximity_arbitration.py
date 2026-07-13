#!/usr/bin/env python3
"""Iteration 92 HUGSIM path-proximity/provenance arbitration audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER91_VERDICT = "HUGSIM_ACTIVE_GAP_PATH_PROVENANCE_DECOMPOSITION_COMPLETE"
EXPECTED_ITER91_LABELS = {
    "provenance_near_path_inactive": 2,
    "path_active_provenance_far_with_bridge_nonactive": 1,
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


ITER91 = _load_module(
    "experiments/iter91_hugsim_active_gap_geometry_decomposition/analyze_active_gap_geometry.py",
    "iter91_active_gap_geometry",
)
ITER90 = ITER91.ITER90
ITER85 = ITER91.ITER85
ITER80 = ITER91.ITER80
SWITCH = ITER91.SWITCH
surface_margin = ITER91.surface_margin
FIXED_ROWS = ITER91.FIXED_ROWS


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def bridge_supported(bridge: dict[str, Any]) -> bool:
    return ITER91.bridge_supported(bridge)


def event_index(rows: Any, label: str, problems: list[str]) -> dict[tuple[str, str, str], dict[str, Any]]:
    return ITER91.event_index(rows, label, problems)


def joint_class(metric: dict[str, Any], bridge: dict[str, Any]) -> str:
    return ITER91.joint_class(metric, bridge)


def compact_candidate(candidate: dict[str, Any] | None) -> dict[str, Any] | None:
    if candidate is None:
        return None
    return ITER91.compact_candidate(candidate)


def path_best_key(candidate: dict[str, Any]) -> tuple[float, float, str]:
    metric = candidate.get("metric") or {}
    cpa_rank = metric.get("cpa_rank")
    min_cpa = metric.get("min_cpa")
    return (
        float(cpa_rank) if finite_number(cpa_rank) else math.inf,
        float(min_cpa) if finite_number(min_cpa) else math.inf,
        str(candidate.get("object_id")),
    )


def provenance_best_key(candidate: dict[str, Any]) -> tuple[float, float, str]:
    metric = candidate.get("metric") or {}
    bridge = candidate.get("bridge") or {}
    cpa_rank = metric.get("cpa_rank")
    distance = bridge.get("best_distance_m")
    return (
        float(distance) if finite_number(distance) else math.inf,
        float(cpa_rank) if finite_number(cpa_rank) else math.inf,
        str(candidate.get("object_id")),
    )


def surface_best_key(candidate: dict[str, Any]) -> tuple[int, float, float, float, str]:
    return ITER91.active_surface_margin_key(candidate)


def classify_row(
    path_best: dict[str, Any] | None,
    provenance_best: dict[str, Any] | None,
    problems: list[str],
) -> str:
    if problems or path_best is None or provenance_best is None:
        return "path_proximity_arbitration_insufficient"
    same = same_object_id(path_best.get("object_id"), provenance_best.get("object_id"))
    path_metric = path_best.get("metric") or {}
    provenance_metric = provenance_best.get("metric") or {}
    path_bridge = path_best.get("bridge") or {}
    path_state = path_metric.get("state")
    provenance_state = provenance_metric.get("state")
    path_supported = bridge_supported(path_bridge)

    if same:
        if path_state == "active" and path_supported:
            return "path_provenance_same_active"
        return "path_provenance_same_nonactive"
    if path_state == "active" and not path_supported and provenance_state != "active":
        return "path_best_active_no_bridge"
    if not path_supported and provenance_state != "active":
        return "path_best_no_bridge_provenance_best_nonactive"
    if path_supported and path_state != "active":
        return "path_best_bridge_supported_nonactive"
    return "path_proximity_arbitration_insufficient"


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter91_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter59_report.get("infra_problems"):
        problems.append(f"iter59-infra-problems:{iter59_report.get('infra_problems')}")
    if iter91_report.get("verdict") != ITER91_VERDICT:
        problems.append(f"iter91-verdict-not-{ITER91_VERDICT}")
    if iter91_report.get("infra_problems"):
        problems.append(f"iter91-infra-problems:{iter91_report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter91_index = event_index(iter91_report.get("events"), "iter91", problems)
    if len(iter91_index) != len(FIXED_ROWS):
        problems.append(f"iter91-event-count-mismatch:{len(iter91_index)}")
    label_counts = Counter(row.get("row_label") for row in iter91_report.get("events", []))
    if dict(label_counts) != EXPECTED_ITER91_LABELS:
        problems.append(f"iter91-label-counts-mismatch:{dict(label_counts)}")
    summary = iter91_report.get("summary") or {}
    if int(summary.get("active_bridge_supported_total", -1)) != 0:
        problems.append("iter91-active-bridge-supported-total-not-zero")

    selected: list[dict[str, Any]] = []
    for target in FIXED_ROWS:
        row_key = (target["audit_id"], target["scenario"])
        event_key = (target["audit_id"], target["scenario"], target["role"])
        row59 = iter59_index.get(row_key)
        row91 = iter91_index.get(event_key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{row_key}")
            continue
        if row91 is None:
            problems.append(f"missing-iter91-event:{event_key}")
            continue
        if row91.get("problems"):
            problems.append(f"iter91-event-problems:{event_key}:{row91.get('problems')}")
        if not same_object_id(row91.get("support_object_id"), target["support_object_id"]):
            problems.append(f"iter91-support-object-mismatch:{event_key}:{row91.get('support_object_id')}")
        replay_ts = surface_margin.number(row91.get("replay_ts"), f"iter91.replay_ts:{event_key}", problems)
        if replay_ts is not None and not math.isclose(replay_ts, float(target["replay_ts"]), abs_tol=1e-6):
            problems.append(f"iter91-replay-ts-mismatch:{event_key}:{replay_ts}")
        if row91.get("replay_alignment") != target["alignment"]:
            problems.append(f"iter91-alignment-mismatch:{event_key}:{row91.get('replay_alignment')}")
        if int(row91.get("active_bridge_supported_count", -1)) != 0:
            problems.append(f"iter91-active-bridge-count-not-zero:{event_key}")
        selected.append({"target": target, "iter59": row59, "iter91": row91})
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
                if not isinstance(bridge.get("best_variant"), dict):
                    problems.append(f"candidate-best-variant-missing:{object_id}")
                    continue
                candidates.append({
                    "object_id": object_id,
                    "metric": metric,
                    "bridge": bridge,
                    "joint_class": joint_class(metric, bridge),
                })

    path_candidates = [
        candidate
        for candidate in candidates
        if finite_number((candidate.get("metric") or {}).get("cpa_rank"))
    ]
    bridge_candidates = [candidate for candidate in candidates if bridge_supported(candidate.get("bridge") or {})]
    path_best = min(path_candidates, key=path_best_key, default=None)
    provenance_best = min(bridge_candidates, key=provenance_best_key, default=None)
    surface_best = min(candidates, key=surface_best_key, default=None)
    label = classify_row(path_best, provenance_best, problems)
    return {
        "audit_id": target["audit_id"],
        "scenario": target["scenario"],
        "event_role": target["role"],
        "support_object_id": target["support_object_id"],
        "replay_ts": replay_ts,
        "replay_alignment": target["alignment"],
        "object_count": len(candidates),
        "bridge_supported_count": len(bridge_candidates),
        "path_best": compact_candidate(path_best),
        "provenance_best": compact_candidate(provenance_best),
        "surface_best": compact_candidate(surface_best),
        "path_provenance_same_object": (
            same_object_id(path_best.get("object_id"), provenance_best.get("object_id"))
            if path_best is not None and provenance_best is not None
            else None
        ),
        "row_label": label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_ROWS)
        or any(row.get("problems") for row in rows)
        or "path_proximity_arbitration_insufficient" in labels
    ):
        return "HUGSIM_PATH_PROXIMITY_ARBITRATION_BLOCKED"
    if "path_provenance_same_active" in labels:
        return "HUGSIM_PATH_PROXIMITY_ARBITRATION_ACTIVE_COINCIDENT_COMPLETE"
    split_labels = {
        "path_best_no_bridge_provenance_best_nonactive",
        "path_best_bridge_supported_nonactive",
        "path_best_active_no_bridge",
        "path_provenance_same_nonactive",
    }
    if all(label in split_labels for label in labels) and len(set(labels)) >= 2:
        return "HUGSIM_PATH_PROXIMITY_ARBITRATION_SPLIT_COMPLETE"
    return "HUGSIM_PATH_PROXIMITY_ARBITRATION_MIXED_COMPLETE"


def build_report(iter59_report_path: Path, iter91_report_path: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter91_report, problems91 = surface_margin.load_report(iter91_report_path, "iter91-report")
    infra_problems.extend(problems59 + problems91)
    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(iter59_report, iter91_report)
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_target(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    same_count = sum(row.get("path_provenance_same_object") is True for row in rows)
    return {
        "iteration": 92,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter91_report": str(iter91_report_path),
        },
        "fixed_rows": list(FIXED_ROWS),
        "infra_problems": infra_problems,
        "events": rows,
        "summary": {
            "target_rows": len(selected),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "path_provenance_same_object_events": same_count,
            "path_provenance_different_object_events": len(rows) - same_count,
            "bridge_supported_object_total": sum(int(row.get("bridge_supported_count", 0)) for row in rows),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "three-row descriptive path-proximity/provenance arbitration audit only; no actor-causality, "
            "repair, threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, real-world behavior, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 92 - HUGSIM path-proximity arbitration audit",
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
        "| audit id | event | replay ts | path best | path state | path bridge | provenance best | provenance state | provenance distance | same object | label | problems |",
        "|---|---|---:|---:|---|---|---:|---|---:|---|---|---|",
    ])
    for row in report["events"]:
        path_best = row.get("path_best") or {}
        path_bridge = path_best.get("bridge_geometry") or {}
        provenance_best = row.get("provenance_best") or {}
        provenance_bridge = provenance_best.get("bridge_geometry") or {}
        lines.append(
            f"| `{row['audit_id']}` | `{row['event_role']}` | `{row.get('replay_ts')}` | "
            f"`{path_best.get('object_id')}` | `{path_best.get('state')}` | "
            f"`{path_bridge.get('distance_band')}` | `{provenance_best.get('object_id')}` | "
            f"`{provenance_best.get('state')}` | `{provenance_bridge.get('best_distance_m')}` | "
            f"`{row.get('path_provenance_same_object')}` | `{row['row_label']}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter59_report: Path, iter91_report: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter59_report, iter91_report)
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
        "--iter91-report",
        type=Path,
        default=Path(
            "experiments/iter91_hugsim_active_gap_geometry_decomposition/proof-geometry/"
            "active_gap_geometry_report.json"
        ),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter92_hugsim_path_proximity_arbitration/proof-arbitration/"
            "path_proximity_arbitration_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter92_hugsim_path_proximity_arbitration/proof-arbitration/"
            "path_proximity_arbitration.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter59_report, args.iter91_report, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
