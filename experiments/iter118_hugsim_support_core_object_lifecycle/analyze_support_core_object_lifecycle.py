#!/usr/bin/env python3
"""Iteration 118 HUGSIM support-core support-object lifecycle audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER117_VERDICT = "HUGSIM_SUPPORT_CORE_EVENT_WINDOW_COMPLETE"
COMPLETE_VERDICT = "HUGSIM_SUPPORT_CORE_OBJECT_LIFECYCLE_COMPLETE"
INFRA_NULL_VERDICT = "HUGSIM_SUPPORT_CORE_OBJECT_LIFECYCLE_INFRA_NULL"
EXPECTED_ROW_COUNT = 8
SUPPORT_M = 6.0
INVALID_TTC_SENTINEL = 1e8


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


def finite_ttc(value: Any) -> bool:
    return numeric(value) and float(value) < INVALID_TTC_SENTINEL


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


def frame_phase(ts: float, first_fire_ts: float) -> str:
    if ts < first_fire_ts:
        return "pre_fire"
    if ts == first_fire_ts:
        return "at_fire"
    return "post_fire_pre_collision"


def slot_dir(proof_root: Path, row: dict[str, Any]) -> Path:
    return proof_root / f"{row['slot_id']}__{row['scenario']}__on"


def read_decision_rows(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [row for row in rows if isinstance(row, dict) and "trace_error" not in row]


def frame_ts(frame: dict[str, Any]) -> float:
    return ITER59.require_float(frame.get("ts", frame.get("frame_index", 0)), "frame.ts")


def surface_state(frame: dict[str, Any]) -> str:
    params = frame.get("params")
    if not isinstance(params, dict):
        raise ValueError("frame-params-not-dict")
    min_cpa = ITER59.require_float(frame.get("min_cpa"), "min_cpa")
    min_ttc = ITER59.require_float(frame.get("min_ttc"), "min_ttc")
    cpa_margin = ITER59.require_float(params.get("cpa_margin"), "cpa_margin")
    ttc_thresh = ITER59.require_float(params.get("ttc_thresh"), "ttc_thresh")
    if min_cpa <= cpa_margin or (finite_ttc(min_ttc) and min_ttc <= ttc_thresh):
        return "active"
    if min_cpa <= 3.0 or (finite_ttc(min_ttc) and min_ttc <= 5.0):
        return "borderline"
    return "far"


def object_distances_for_frame(
    frame: dict[str, Any],
    foreground: dict[str, Any],
    foreground_ts: float,
) -> list[dict[str, Any]]:
    ts = frame_ts(frame)
    lead = foreground_ts - ts
    r_mat = ITER59.matrix3(frame.get("l2g_r_mat"), "l2g_r_mat")
    trans_raw = frame.get("l2g_t")
    if not isinstance(trans_raw, list) or len(trans_raw) < 2:
        raise ValueError("l2g_t-not-vec2")
    trans = [ITER59.require_float(v, "l2g_t") for v in trans_raw]
    objs = frame.get("objs")
    if not isinstance(objs, list) or not objs:
        raise ValueError(f"frame-objs-not-list-or-empty:{ts}")
    obs_forward = ITER59.require_float(foreground["obs_box"][0], "obs_box.x")
    obs_lateral = ITER59.require_float(foreground["obs_box"][1], "obs_box.y")
    rows: list[dict[str, Any]] = []
    for obj in objs:
        if not isinstance(obj, dict):
            raise ValueError("obj-not-dict")
        wx, wy = ITER59.vec2(obj.get("world"), "obj.world")
        vx, vy = ITER59.vec2(obj.get("vel"), "obj.vel")
        pred_x = wx + vx * lead
        pred_y = wy + vy * lead
        local_x, local_y = ITER59.world_to_monitor_local(pred_x, pred_y, r_mat, trans)
        monitor_forward = local_y
        monitor_lateral = local_x
        rows.append(
            {
                "object_id": obj.get("id"),
                "distance_m": math.hypot(monitor_forward - obs_forward, monitor_lateral - obs_lateral),
                "monitor_forward_m": monitor_forward,
                "monitor_lateral_m": monitor_lateral,
            }
        )
    return sorted(rows, key=lambda item: (float(item["distance_m"]), str(item["object_id"])))


def find_object(objects: list[dict[str, Any]], object_id: Any) -> dict[str, Any] | None:
    for obj in objects:
        if obj.get("object_id") == object_id:
            return obj
    return None


def measure_frame(
    frame: dict[str, Any],
    foreground: dict[str, Any],
    foreground_ts: float,
    first_fire_ts: float,
) -> dict[str, Any]:
    distances = object_distances_for_frame(frame, foreground, foreground_ts)
    nearest = distances[0]
    ts = frame_ts(frame)
    return {
        "ts": ts,
        "frame_index": frame.get("frame_index"),
        "phase": frame_phase(ts, first_fire_ts),
        "surface_state": surface_state(frame),
        "nearest_object_id": nearest["object_id"],
        "nearest_distance_m": nearest["distance_m"],
        "nearest_actor_support": float(nearest["distance_m"]) <= SUPPORT_M,
        "object_distances": distances,
    }


def lifecycle_label(
    first_support_phase: str,
    object_present_at_fire: bool | None,
    object_supported_at_fire: bool | None,
    active_same_object_count: int,
    active_different_object_count: int,
) -> str:
    if first_support_phase == "never_before_collision":
        return "never_supported_reference"
    if first_support_phase == "pre_fire":
        if object_present_at_fire is False:
            return "pre_fire_object_absent_at_fire"
        if object_supported_at_fire is True:
            return "pre_fire_object_still_supported_at_fire"
        return "pre_fire_object_drifted_outside_support_at_fire"
    if active_same_object_count > 0:
        return "post_fire_support_only_same_object_active_support"
    if active_different_object_count > 0:
        return "post_fire_support_only_different_object_active_support"
    return "post_fire_support_only_far_support"


def _max_ts(frames: list[dict[str, Any]], key: str = "ts") -> float | None:
    values = [float(frame[key]) for frame in frames if numeric(frame.get(key))]
    return max(values) if values else None


def _min_ts(frames: list[dict[str, Any]], key: str = "ts") -> float | None:
    values = [float(frame[key]) for frame in frames if numeric(frame.get(key))]
    return min(values) if values else None


def _distance_at(frames: list[dict[str, Any]], ts: float | None) -> float | None:
    if ts is None:
        return None
    for frame in frames:
        if frame.get("ts") == ts:
            return frame.get("object_distance_m")
    return None


def classify_row(iter117_row: dict[str, Any], proof_root: Path) -> dict[str, Any]:
    problems: list[str] = []
    if iter117_row.get("problems"):
        problems.append(f"iter117-row-problems:{iter117_row.get('problems')!r}")
    row_label = iter117_row.get("row_label")
    if not isinstance(row_label, str):
        problems.append(f"iter117-row-label-missing:{row_label!r}")
    first_support_phase = iter117_row.get("first_support_phase")
    if not isinstance(first_support_phase, str):
        problems.append(f"iter117-first-support-phase-missing:{first_support_phase!r}")
    ep_dir = slot_dir(proof_root, iter117_row)
    eval_path = ep_dir / "eval.json"
    decisions_path = ep_dir / "sentinel_iter48_decisions.jsonl"
    if not eval_path.exists() or eval_path.stat().st_size == 0:
        problems.append(f"missing-eval:{eval_path}")
    if not decisions_path.exists() or decisions_path.stat().st_size == 0:
        problems.append(f"missing-decisions:{decisions_path}")
    if problems:
        return {
            "slot_index": iter117_row.get("slot_index"),
            "slot_id": iter117_row.get("slot_id"),
            "scenario": iter117_row.get("scenario"),
            "run": iter117_row.get("run"),
            "problems": problems,
        }

    try:
        eval_doc = ITER59.read_eval(eval_path)
        decisions = ITER59.read_decisions(decisions_path)
        decision_rows = read_decision_rows(decisions_path)
        foreground = eval_doc["first_foreground"]
        if not isinstance(foreground, dict):
            raise ValueError("first-foreground-missing")
        first_fire_ts = ITER59.require_float(decisions["first_fire_ts"], "first_fire_ts")
        foreground_ts = ITER59.require_float(foreground["timestamp"], "foreground.timestamp")
        considered = [
            row for row in decision_rows
            if numeric(row.get("ts", row.get("frame_index", 0)))
            and float(row.get("ts", row.get("frame_index", 0))) <= foreground_ts
        ]
        if not considered:
            raise ValueError("no-decision-frame-before-foreground")
        frame_rows = [measure_frame(row, foreground, foreground_ts, first_fire_ts) for row in considered]
        first_fire_frame = next((frame for frame in frame_rows if frame["ts"] == first_fire_ts), None)
        if first_fire_frame is None:
            raise ValueError(f"first-fire-frame-missing:{first_fire_ts}")
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return {
            "slot_index": iter117_row.get("slot_index"),
            "slot_id": iter117_row.get("slot_id"),
            "scenario": iter117_row.get("scenario"),
            "run": iter117_row.get("run"),
            "problems": [f"parse-or-reconstruct-failed:{exc}"],
        }

    first_support_object_id = iter117_row.get("first_support_object_id")
    if first_support_phase == "never_before_collision":
        return {
            "slot_index": iter117_row.get("slot_index"),
            "slot_id": iter117_row.get("slot_id"),
            "scenario": iter117_row.get("scenario"),
            "run": iter117_row.get("run"),
            "first_fire_ts": first_fire_ts,
            "first_foreground_ts": foreground_ts,
            "first_support_phase": first_support_phase,
            "first_support_object_id": None,
            "lifecycle_label": "never_supported_reference",
            "first_fire_surface_state": first_fire_frame["surface_state"],
            "object_present_at_fire": None,
            "object_supported_at_fire": None,
            "active_support_same_object_count": 0,
            "active_support_different_object_count": 0,
            "problems": [],
        }
    if first_support_object_id is None:
        return {
            "slot_index": iter117_row.get("slot_index"),
            "slot_id": iter117_row.get("slot_id"),
            "scenario": iter117_row.get("scenario"),
            "run": iter117_row.get("run"),
            "problems": ["first-support-object-missing-for-supported-row"],
        }

    object_frames: list[dict[str, Any]] = []
    for frame in frame_rows:
        obj = find_object(frame["object_distances"], first_support_object_id)
        if obj is None:
            continue
        object_frames.append(
            {
                "ts": frame["ts"],
                "phase": frame["phase"],
                "surface_state": frame["surface_state"],
                "object_distance_m": obj["distance_m"],
                "object_actor_support": float(obj["distance_m"]) <= SUPPORT_M,
            }
        )
    if not object_frames:
        return {
            "slot_index": iter117_row.get("slot_index"),
            "slot_id": iter117_row.get("slot_id"),
            "scenario": iter117_row.get("scenario"),
            "run": iter117_row.get("run"),
            "problems": [f"first-support-object-never-present:{first_support_object_id!r}"],
        }

    fire_obj = find_object(first_fire_frame["object_distances"], first_support_object_id)
    object_present_at_fire = fire_obj is not None
    object_distance_at_fire = fire_obj.get("distance_m") if fire_obj else None
    object_supported_at_fire = bool(fire_obj and float(fire_obj["distance_m"]) <= SUPPORT_M)
    object_support_frames = [frame for frame in object_frames if frame["object_actor_support"]]
    before_or_at_fire = [frame for frame in object_frames if float(frame["ts"]) <= first_fire_ts]
    support_before_or_at_fire = [
        frame for frame in object_support_frames
        if float(frame["ts"]) <= first_fire_ts
    ]
    active_support_frames = [
        frame for frame in frame_rows
        if frame["nearest_actor_support"] and frame["surface_state"] == "active"
    ]
    active_same = sum(frame["nearest_object_id"] == first_support_object_id for frame in active_support_frames)
    active_different = sum(frame["nearest_object_id"] != first_support_object_id for frame in active_support_frames)
    label = lifecycle_label(
        str(first_support_phase),
        object_present_at_fire,
        object_supported_at_fire,
        active_same,
        active_different,
    )
    last_presence_before_fire_ts = _max_ts(before_or_at_fire)
    last_support_before_fire_ts = _max_ts(support_before_or_at_fire)
    last_presence_ts = _max_ts(object_frames)
    last_support_ts = _max_ts(object_support_frames)
    return {
        "slot_index": iter117_row.get("slot_index"),
        "slot_id": iter117_row.get("slot_id"),
        "scenario": iter117_row.get("scenario"),
        "run": iter117_row.get("run"),
        "first_fire_ts": first_fire_ts,
        "first_foreground_ts": foreground_ts,
        "first_support_phase": first_support_phase,
        "first_support_ts": iter117_row.get("first_support_ts"),
        "first_support_object_id": first_support_object_id,
        "first_fire_surface_state": first_fire_frame["surface_state"],
        "lifecycle_label": label,
        "object_first_presence_ts": _min_ts(object_frames),
        "object_last_presence_before_or_at_fire_ts": last_presence_before_fire_ts,
        "object_last_presence_ts": last_presence_ts,
        "object_last_support_before_or_at_fire_ts": last_support_before_fire_ts,
        "object_last_support_ts": last_support_ts,
        "object_last_presence_before_or_at_fire_distance_m": _distance_at(
            before_or_at_fire,
            last_presence_before_fire_ts,
        ),
        "object_last_support_before_or_at_fire_distance_m": _distance_at(
            support_before_or_at_fire,
            last_support_before_fire_ts,
        ),
        "object_distance_at_fire_m": object_distance_at_fire,
        "object_present_at_fire": object_present_at_fire,
        "object_supported_at_fire": object_supported_at_fire,
        "object_presence_frame_count": len(object_frames),
        "object_support_frame_count": len(object_support_frames),
        "object_support_before_or_at_fire_count": len(support_before_or_at_fire),
        "active_support_same_object_count": active_same,
        "active_support_different_object_count": active_different,
        "active_support_frame_count": len(active_support_frames),
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
    if sum(summary.get("lifecycle_label_counts", {}).values()) != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    required = (
        "lifecycle_label",
        "active_support_same_object_count",
        "active_support_different_object_count",
    )
    for row in rows:
        for key in required:
            if key not in row:
                return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(iter117_report_path: Path, proof_root: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter117_report, report_problems = load_json(iter117_report_path, "iter117-report")
    infra_problems.extend(report_problems)
    rows: list[dict[str, Any]] = []
    if not infra_problems:
        require_equal(infra_problems, "iter117-verdict", iter117_report.get("verdict"), ITER117_VERDICT)
        event_rows = iter117_report.get("event_window_rows")
        if not isinstance(event_rows, list):
            infra_problems.append("iter117-event-window-rows-not-list")
            event_rows = []
        require_equal(infra_problems, "iter117-row-count", len(event_rows), EXPECTED_ROW_COUNT)
    if not infra_problems:
        rows = [classify_row(row, proof_root) for row in iter117_report["event_window_rows"] if isinstance(row, dict)]

    clean_rows = [row for row in rows if not row.get("problems")]
    labels = Counter(row.get("lifecycle_label") for row in clean_rows)
    summary = {
        "row_count": len(rows),
        "problem_row_count": sum(bool(row.get("problems")) for row in rows),
        "lifecycle_label_counts": _dict_counts(labels),
        "supported_row_count": sum(row.get("first_support_phase") != "never_before_collision" for row in clean_rows),
        "object_present_at_fire_count": sum(row.get("object_present_at_fire") is True for row in clean_rows),
        "object_supported_at_fire_count": sum(row.get("object_supported_at_fire") is True for row in clean_rows),
        "active_support_same_object_count": sum(
            int(row.get("active_support_same_object_count", 0)) for row in clean_rows
        ),
        "active_support_different_object_count": sum(
            int(row.get("active_support_different_object_count", 0)) for row in clean_rows
        ),
        "object_presence_frame_count": _minmax(clean_rows, "object_presence_frame_count"),
        "object_support_frame_count": _minmax(clean_rows, "object_support_frame_count"),
        "object_support_before_or_at_fire_count": _minmax(clean_rows, "object_support_before_or_at_fire_count"),
        "object_distance_at_fire_m": _minmax(clean_rows, "object_distance_at_fire_m"),
    }
    verdict = choose_verdict(infra_problems, rows, summary)
    return {
        "iteration": 118,
        "inputs": {
            "iter117_report": str(iter117_report_path),
            "proof_root": str(proof_root),
            "iter59_analyzer": "experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py",
        },
        "infra_problems": infra_problems,
        "lifecycle_rows": rows,
        "summary": summary,
        "verdict": verdict,
        "claim_boundary": (
            "descriptive support-core support-object lifecycle audit of eight committed rows only; "
            "no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, "
            "benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder "
            "behavior, acquisition-value, retuning, production, or commercial claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 118 - HUGSIM support-core support-object lifecycle audit",
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
            "| slot | scenario | run | label | object | present at fire | support at fire | same active | diff active | last support <= fire |",
            "|---:|---|---:|---|---:|---|---|---:|---:|---:|",
        ]
    )
    for row in report["lifecycle_rows"]:
        lines.append(
            f"| `{row.get('slot_index')}` | `{row.get('scenario')}` | `{row.get('run')}` | "
            f"`{row.get('lifecycle_label')}` | `{row.get('first_support_object_id')}` | "
            f"`{row.get('object_present_at_fire')}` | `{row.get('object_supported_at_fire')}` | "
            f"`{row.get('active_support_same_object_count')}` | "
            f"`{row.get('active_support_different_object_count')}` | "
            f"`{row.get('object_last_support_before_or_at_fire_ts')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter117_report: Path, proof_root: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter117_report, proof_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter117-report",
        type=Path,
        default=Path(
            "experiments/iter117_hugsim_support_core_event_window_decomposition/proof-event-window/"
            "support_core_event_window_report.json"
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
            "experiments/iter118_hugsim_support_core_object_lifecycle/proof-lifecycle/"
            "support_core_object_lifecycle_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter118_hugsim_support_core_object_lifecycle/proof-lifecycle/"
            "support_core_object_lifecycle.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter117_report, args.proof_root, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
