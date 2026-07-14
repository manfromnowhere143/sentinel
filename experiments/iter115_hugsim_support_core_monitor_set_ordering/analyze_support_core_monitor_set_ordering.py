#!/usr/bin/env python3
"""Iteration 115 HUGSIM support-core monitor-set ordering audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER113_VERDICT = "HUGSIM_SUPPORT_CORE_ACTOR_MATCH_AUDIT_COMPLETE"
ITER114_VERDICT = "HUGSIM_SUPPORT_CORE_MISMATCH_GEOMETRY_COMPLETE"
COMPLETE_VERDICT = "HUGSIM_SUPPORT_CORE_MONITOR_SET_ORDERING_COMPLETE"
INFRA_NULL_VERDICT = "HUGSIM_SUPPORT_CORE_MONITOR_SET_ORDERING_INFRA_NULL"
EXPECTED_ROW_COUNT = 8
MATCH_M = 3.0
MISMATCH_M = 6.0


def load_iter59_module() -> Any:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "iter59_hugsim_actor_match_audit"
        / "analyze_actor_match.py"
    )
    spec = importlib.util.spec_from_file_location("iter59_actor_match", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-iter59-analyzer:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ITER59 = load_iter59_module()


def numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def load_json(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-{label}:{path}"]
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"read-{label}-failed:{path}:{exc}"]
    if not isinstance(data, dict):
        return {}, [f"{label}-not-dict"]
    return data, []


def require_equal(problems: list[str], label: str, actual: Any, expected: Any) -> None:
    if actual != expected:
        problems.append(f"{label}-mismatch:{actual!r}!={expected!r}")


def temporal_label(lead_time_s: float) -> str:
    if lead_time_s <= 0.5:
        return "short_lead"
    if lead_time_s <= 1.5:
        return "medium_lead"
    return "long_lead"


def object_set_label(distance_m: float) -> str:
    if distance_m <= MATCH_M:
        return "nearest_actor_match"
    if distance_m <= MISMATCH_M:
        return "nearest_actor_ambiguous"
    return "nearest_actor_mismatch"


def selection_label(selected_id: Any, nearest_id: Any) -> str:
    if selected_id == nearest_id:
        return "selected_is_nearest"
    return "selected_not_nearest"


def combined_label(nearest_distance_m: float, selected_id: Any, nearest_id: Any) -> str:
    nearest_supported = nearest_distance_m <= MISMATCH_M
    selected_nearest = selected_id == nearest_id
    if not nearest_supported and selected_nearest:
        return "whole_set_mismatch_selected_nearest"
    if not nearest_supported and not selected_nearest:
        return "whole_set_mismatch_selected_not_nearest"
    if nearest_supported and not selected_nearest:
        return "nonselected_collision_candidate_available"
    return "selected_collision_candidate"


def slot_dir(proof_root: Path, row: dict[str, Any]) -> Path:
    return proof_root / f"{row['slot_id']}__{row['scenario']}__on"


def _sort_object_key(item: dict[str, Any]) -> tuple[float, str]:
    return float(item["distance_m"]), str(item["object_id"])


def object_distances(first_fire: dict[str, Any], foreground: dict[str, Any], lead_time_s: float) -> list[dict[str, Any]]:
    r_mat = ITER59.matrix3(first_fire.get("l2g_r_mat"), "l2g_r_mat")
    trans_raw = first_fire.get("l2g_t")
    if not isinstance(trans_raw, list) or len(trans_raw) < 2:
        raise ValueError("l2g_t-not-vec2")
    trans = [ITER59.require_float(v, "l2g_t") for v in trans_raw]
    objs = first_fire.get("objs")
    if not isinstance(objs, list) or not objs:
        raise ValueError("first-fire-objs-not-list")
    obs_forward = ITER59.require_float(foreground["obs_box"][0], "obs_box.x")
    obs_lateral = ITER59.require_float(foreground["obs_box"][1], "obs_box.y")
    rows: list[dict[str, Any]] = []
    for obj in objs:
        if not isinstance(obj, dict):
            raise ValueError("obj-not-dict")
        object_id = obj.get("id")
        wx, wy = ITER59.vec2(obj.get("world"), "obj.world")
        vx, vy = ITER59.vec2(obj.get("vel"), "obj.vel")
        pred_x = wx + vx * lead_time_s
        pred_y = wy + vy * lead_time_s
        local_x, local_y = ITER59.world_to_monitor_local(pred_x, pred_y, r_mat, trans)
        monitor_forward = local_y
        monitor_lateral = local_x
        rows.append(
            {
                "object_id": object_id,
                "monitor_forward_m": monitor_forward,
                "monitor_lateral_m": monitor_lateral,
                "distance_m": math.hypot(monitor_forward - obs_forward, monitor_lateral - obs_lateral),
            }
        )
    return sorted(rows, key=_sort_object_key)


def classify_row(
    iter113_row: dict[str, Any],
    iter114_row: dict[str, Any],
    proof_root: Path,
) -> dict[str, Any]:
    problems: list[str] = []
    slot_id = iter113_row.get("slot_id")
    if iter113_row.get("support_label") != "classifiable_foreground":
        problems.append(f"support-label-not-classifiable:{iter113_row.get('support_label')!r}")
    if iter113_row.get("bridge_label") != "actor_mismatch":
        problems.append(f"bridge-label-not-mismatch:{iter113_row.get('bridge_label')!r}")
    if iter114_row.get("slot_id") != slot_id:
        problems.append(f"iter114-slot-mismatch:{iter114_row.get('slot_id')!r}!={slot_id!r}")
    if iter114_row.get("problems"):
        problems.append(f"iter114-row-problems:{iter114_row.get('problems')!r}")
    selected_id = iter113_row.get("monitor_object_id")
    ep_dir = slot_dir(proof_root, iter113_row)
    eval_path = ep_dir / "eval.json"
    decisions_path = ep_dir / "sentinel_iter48_decisions.jsonl"
    if not eval_path.exists() or eval_path.stat().st_size == 0:
        problems.append(f"missing-eval:{eval_path}")
    if not decisions_path.exists() or decisions_path.stat().st_size == 0:
        problems.append(f"missing-decisions:{decisions_path}")
    if problems:
        return {
            "slot_index": iter113_row.get("slot_index"),
            "slot_id": slot_id,
            "scenario": iter113_row.get("scenario"),
            "run": iter113_row.get("run"),
            "problems": problems,
        }

    try:
        eval_doc = ITER59.read_eval(eval_path)
        decisions = ITER59.read_decisions(decisions_path)
        foreground = eval_doc["first_foreground"]
        first_fire = decisions["first_fire_row"]
        if not isinstance(foreground, dict):
            raise ValueError("first-foreground-missing")
        if not isinstance(first_fire, dict):
            raise ValueError("first-fire-missing")
        fire_ts = ITER59.require_float(decisions["first_fire_ts"], "first_fire_ts")
        foreground_ts = ITER59.require_float(foreground["timestamp"], "foreground.timestamp")
        if fire_ts > foreground_ts:
            raise ValueError(f"first-fire-after-foreground:{fire_ts}>{foreground_ts}")
        if decisions.get("monitor_object_id") != selected_id:
            raise ValueError(
                f"selected-monitor-object-mismatch:{decisions.get('monitor_object_id')!r}!={selected_id!r}"
            )
        lead_time = foreground_ts - fire_ts
        distances = object_distances(first_fire, foreground, lead_time)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return {
            "slot_index": iter113_row.get("slot_index"),
            "slot_id": slot_id,
            "scenario": iter113_row.get("scenario"),
            "run": iter113_row.get("run"),
            "problems": [f"parse-or-reconstruct-failed:{exc}"],
        }

    object_ids = [item["object_id"] for item in distances]
    if selected_id not in object_ids:
        return {
            "slot_index": iter113_row.get("slot_index"),
            "slot_id": slot_id,
            "scenario": iter113_row.get("scenario"),
            "run": iter113_row.get("run"),
            "problems": [f"selected-monitor-object-absent:{selected_id!r}"],
        }
    nearest = distances[0]
    selected_rank = next(index for index, item in enumerate(distances, start=1) if item["object_id"] == selected_id)
    selected_distance = next(item for item in distances if item["object_id"] == selected_id)
    obj_label = object_set_label(float(nearest["distance_m"]))
    sel_label = selection_label(selected_id, nearest["object_id"])
    return {
        "slot_index": iter113_row.get("slot_index"),
        "slot_id": slot_id,
        "scenario": iter113_row.get("scenario"),
        "run": iter113_row.get("run"),
        "design_label": iter113_row.get("design_label"),
        "geometry_label": iter114_row.get("geometry_label"),
        "first_fire_ts": fire_ts,
        "first_foreground_ts": foreground_ts,
        "lead_time_s": lead_time,
        "temporal_label": temporal_label(lead_time),
        "first_fire_object_count": len(distances),
        "selected_object_id": selected_id,
        "selected_rank_by_collision_distance": selected_rank,
        "selected_distance_m": selected_distance["distance_m"],
        "nearest_object_id": nearest["object_id"],
        "nearest_distance_m": nearest["distance_m"],
        "nearest_monitor_forward_m": nearest["monitor_forward_m"],
        "nearest_monitor_lateral_m": nearest["monitor_lateral_m"],
        "object_set_label": obj_label,
        "selection_label": sel_label,
        "combined_label": combined_label(float(nearest["distance_m"]), selected_id, nearest["object_id"]),
        "top3_object_distances": distances[:3],
        "problems": [],
    }


def _dict_counts(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def _minmax(rows: list[dict[str, Any]], key: str) -> dict[str, float | None]:
    values = [float(row[key]) for row in rows if numeric(row.get(key))]
    if not values:
        return {"min": None, "max": None}
    return {"min": min(values), "max": max(values)}


def choose_verdict(infra_problems: list[str], rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if infra_problems or any(row.get("problems") for row in rows):
        return INFRA_NULL_VERDICT
    if summary.get("row_count") != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    if sum(summary.get("combined_label_counts", {}).values()) != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(iter113_report_path: Path, iter114_report_path: Path, proof_root: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter113_report, iter113_problems = load_json(iter113_report_path, "iter113-report")
    iter114_report, iter114_problems = load_json(iter114_report_path, "iter114-report")
    infra_problems.extend(iter113_problems + iter114_problems)
    rows: list[dict[str, Any]] = []
    if not infra_problems:
        require_equal(infra_problems, "iter113-verdict", iter113_report.get("verdict"), ITER113_VERDICT)
        require_equal(infra_problems, "iter114-verdict", iter114_report.get("verdict"), ITER114_VERDICT)
        iter113_rows = iter113_report.get("episodes")
        iter114_rows = iter114_report.get("geometry_rows")
        if not isinstance(iter113_rows, list):
            infra_problems.append("iter113-episodes-not-list")
            iter113_rows = []
        if not isinstance(iter114_rows, list):
            infra_problems.append("iter114-geometry-rows-not-list")
            iter114_rows = []
        require_equal(infra_problems, "iter113-row-count", len(iter113_rows), EXPECTED_ROW_COUNT)
        require_equal(infra_problems, "iter114-row-count", len(iter114_rows), EXPECTED_ROW_COUNT)
    if not infra_problems:
        iter113_by_slot = {row.get("slot_id"): row for row in iter113_report["episodes"] if isinstance(row, dict)}
        iter114_by_slot = {row.get("slot_id"): row for row in iter114_report["geometry_rows"] if isinstance(row, dict)}
        require_equal(
            infra_problems,
            "slot-id-sets",
            sorted(iter113_by_slot),
            sorted(iter114_by_slot),
        )
        if not infra_problems:
            rows = [
                classify_row(iter113_by_slot[slot_id], iter114_by_slot[slot_id], proof_root)
                for slot_id in sorted(iter113_by_slot, key=lambda key: int(iter113_by_slot[key].get("slot_index", 0)))
            ]

    temporal_counts = Counter(row.get("temporal_label") for row in rows if not row.get("problems"))
    object_counts = Counter(row.get("object_set_label") for row in rows if not row.get("problems"))
    selection_counts = Counter(row.get("selection_label") for row in rows if not row.get("problems"))
    combined_counts = Counter(row.get("combined_label") for row in rows if not row.get("problems"))
    summary = {
        "row_count": len(rows),
        "problem_row_count": sum(bool(row.get("problems")) for row in rows),
        "temporal_label_counts": _dict_counts(temporal_counts),
        "object_set_label_counts": _dict_counts(object_counts),
        "selection_label_counts": _dict_counts(selection_counts),
        "combined_label_counts": _dict_counts(combined_counts),
        "lead_time_s": _minmax(rows, "lead_time_s"),
        "nearest_distance_m": _minmax(rows, "nearest_distance_m"),
        "selected_distance_m": _minmax(rows, "selected_distance_m"),
        "first_fire_object_count": _minmax(rows, "first_fire_object_count"),
    }
    verdict = choose_verdict(infra_problems, rows, summary)
    return {
        "iteration": 115,
        "inputs": {
            "iter113_report": str(iter113_report_path),
            "iter114_report": str(iter114_report_path),
            "proof_root": str(proof_root),
            "iter59_analyzer": "experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py",
        },
        "infra_problems": infra_problems,
        "ordering_rows": rows,
        "summary": summary,
        "verdict": verdict,
        "claim_boundary": (
            "descriptive monitor-set ordering audit of eight committed support-core mismatch rows only; "
            "no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, "
            "benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder "
            "behavior, acquisition-value, retuning, production, or commercial claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 115 - HUGSIM support-core monitor-set ordering audit",
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
    lines.extend(
        [
            "",
            "## Rows",
            "",
            "| slot | scenario | run | lead | object-set | selection | combined | nearest id | nearest m | selected rank | objects |",
            "|---:|---|---:|---|---|---|---|---|---:|---:|---:|",
        ]
    )
    for row in report["ordering_rows"]:
        lines.append(
            f"| `{row.get('slot_index')}` | `{row.get('scenario')}` | `{row.get('run')}` | "
            f"`{row.get('temporal_label')}` | `{row.get('object_set_label')}` | "
            f"`{row.get('selection_label')}` | `{row.get('combined_label')}` | "
            f"`{row.get('nearest_object_id')}` | `{row.get('nearest_distance_m')}` | "
            f"`{row.get('selected_rank_by_collision_distance')}` | "
            f"`{row.get('first_fire_object_count')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter113_report: Path,
    iter114_report: Path,
    proof_root: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter113_report, iter114_report, proof_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter113-report",
        type=Path,
        default=Path(
            "experiments/iter113_hugsim_support_core_actor_match_audit/proof-actor-match/"
            "support_core_actor_match_report.json"
        ),
    )
    parser.add_argument(
        "--iter114-report",
        type=Path,
        default=Path(
            "experiments/iter114_hugsim_support_core_mismatch_geometry_decomposition/proof-geometry/"
            "support_core_mismatch_geometry_report.json"
        ),
    )
    parser.add_argument(
        "--proof-root",
        type=Path,
        default=Path("experiments/iter112_hugsim_support_core_batch_execution/proof-execution"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter115_hugsim_support_core_monitor_set_ordering/proof-ordering/"
            "support_core_monitor_set_ordering_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter115_hugsim_support_core_monitor_set_ordering/proof-ordering/"
            "support_core_monitor_set_ordering.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter113_report,
        args.iter114_report,
        args.proof_root,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
