#!/usr/bin/env python3
"""Iteration 120 HUGSIM selected fire-object backward lifecycle audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER119_VERDICT = "HUGSIM_SUPPORT_CORE_LOSS_REPLACEMENT_COMPLETE"
COMPLETE_VERDICT = "HUGSIM_SUPPORT_CORE_SELECTED_FIRE_OBJECT_COMPLETE"
INFRA_NULL_VERDICT = "HUGSIM_SUPPORT_CORE_SELECTED_FIRE_OBJECT_INFRA_NULL"
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


def slot_dir(proof_root: Path, row: dict[str, Any]) -> Path:
    return proof_root / f"{row['slot_id']}__{row['scenario']}__on"


def read_decision_rows(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [row for row in rows if isinstance(row, dict) and "trace_error" not in row]


def frame_ts(frame: dict[str, Any]) -> float:
    return ITER59.require_float(frame.get("ts", frame.get("frame_index", 0)), "frame.ts")


def frame_phase(ts: float, first_fire_ts: float) -> str:
    if ts < first_fire_ts:
        return "pre_fire"
    if ts == first_fire_ts:
        return "at_fire"
    return "post_fire_pre_collision"


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


def selected_lifecycle_label(pre_support: int, at_fire_support: bool, post_fire_support: int) -> str:
    if at_fire_support:
        return "selected_supported_at_fire"
    if pre_support > 0:
        return "selected_pre_fire_supported_then_lost_by_fire"
    if post_fire_support > 0:
        return "selected_post_fire_support_only"
    return "selected_never_supported_before_collision"


def _minmax(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "max": None}
    return {"min": min(values), "max": max(values)}


def _count_by_phase(frames: list[dict[str, Any]], key: str | None = None) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for frame in frames:
        if key is None or frame.get(key):
            counter[str(frame["phase"])] += 1
    return {phase: counter[phase] for phase in ("pre_fire", "at_fire", "post_fire_pre_collision") if counter[phase]}


def _surface_counts_by_phase(frames: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    outer: dict[str, Counter[str]] = {}
    for frame in frames:
        phase = str(frame["phase"])
        outer.setdefault(phase, Counter())[str(frame["surface_state"])] += 1
    return {
        phase: {state: outer[phase][state] for state in ("active", "borderline", "far") if outer[phase][state]}
        for phase in ("pre_fire", "at_fire", "post_fire_pre_collision")
        if phase in outer
    }


def classify_row(replacement_row: dict[str, Any], proof_root: Path) -> dict[str, Any]:
    problems: list[str] = []
    if replacement_row.get("problems"):
        problems.append(f"iter119-row-problems:{replacement_row.get('problems')!r}")
    selected_object_id = replacement_row.get("selected_object_id")
    if selected_object_id is None:
        problems.append("selected-object-missing")
    ep_dir = slot_dir(proof_root, replacement_row)
    eval_path = ep_dir / "eval.json"
    decisions_path = ep_dir / "sentinel_iter48_decisions.jsonl"
    if not eval_path.exists() or eval_path.stat().st_size == 0:
        problems.append(f"missing-eval:{eval_path}")
    if not decisions_path.exists() or decisions_path.stat().st_size == 0:
        problems.append(f"missing-decisions:{decisions_path}")
    if problems:
        return {
            "slot_index": replacement_row.get("slot_index"),
            "slot_id": replacement_row.get("slot_id"),
            "scenario": replacement_row.get("scenario"),
            "run": replacement_row.get("run"),
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
        selected_frames: list[dict[str, Any]] = []
        for frame in considered:
            ts = frame_ts(frame)
            distances = object_distances_for_frame(frame, foreground, foreground_ts)
            selected = find_object(distances, selected_object_id)
            if selected is None:
                continue
            selected_frames.append(
                {
                    "ts": ts,
                    "frame_index": frame.get("frame_index"),
                    "phase": frame_phase(ts, first_fire_ts),
                    "surface_state": surface_state(frame),
                    "distance_m": selected["distance_m"],
                    "actor_support": float(selected["distance_m"]) <= SUPPORT_M,
                }
            )
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return {
            "slot_index": replacement_row.get("slot_index"),
            "slot_id": replacement_row.get("slot_id"),
            "scenario": replacement_row.get("scenario"),
            "run": replacement_row.get("run"),
            "problems": [f"parse-or-reconstruct-failed:{exc}"],
        }

    if not selected_frames:
        return {
            "slot_index": replacement_row.get("slot_index"),
            "slot_id": replacement_row.get("slot_id"),
            "scenario": replacement_row.get("scenario"),
            "run": replacement_row.get("run"),
            "problems": [f"selected-object-never-present:{selected_object_id!r}"],
        }
    fire_frame = next((frame for frame in selected_frames if frame["ts"] == first_fire_ts), None)
    if fire_frame is None:
        return {
            "slot_index": replacement_row.get("slot_index"),
            "slot_id": replacement_row.get("slot_id"),
            "scenario": replacement_row.get("scenario"),
            "run": replacement_row.get("run"),
            "problems": [f"selected-object-missing-at-fire:{selected_object_id!r}"],
        }
    support_frames = [frame for frame in selected_frames if frame["actor_support"]]
    pre_support = [frame for frame in support_frames if frame["phase"] == "pre_fire"]
    post_support = [frame for frame in support_frames if frame["phase"] == "post_fire_pre_collision"]
    label = selected_lifecycle_label(len(pre_support), bool(fire_frame["actor_support"]), len(post_support))
    pre_fire_frames = [frame for frame in selected_frames if frame["phase"] == "pre_fire"]
    return {
        "slot_index": replacement_row.get("slot_index"),
        "slot_id": replacement_row.get("slot_id"),
        "scenario": replacement_row.get("scenario"),
        "run": replacement_row.get("run"),
        "first_fire_ts": first_fire_ts,
        "first_foreground_ts": foreground_ts,
        "selected_object_id": selected_object_id,
        "selected_is_fire_nearest": replacement_row.get("selected_is_fire_nearest"),
        "selected_rank_by_collision_distance": replacement_row.get("selected_rank_by_collision_distance"),
        "selected_lifecycle_label": label,
        "selected_presence_frame_count": len(selected_frames),
        "selected_first_presence_ts": min(float(frame["ts"]) for frame in selected_frames),
        "selected_last_presence_ts": max(float(frame["ts"]) for frame in selected_frames),
        "selected_first_pre_fire_presence_ts": (
            min(float(frame["ts"]) for frame in pre_fire_frames) if pre_fire_frames else None
        ),
        "selected_support_frame_count": len(support_frames),
        "selected_support_phase_counts": _count_by_phase(selected_frames, "actor_support"),
        "selected_surface_counts_by_phase": _surface_counts_by_phase(selected_frames),
        "selected_pre_fire_closest_distance_m": (
            min(float(frame["distance_m"]) for frame in pre_fire_frames) if pre_fire_frames else None
        ),
        "selected_at_fire_distance_m": fire_frame["distance_m"],
        "selected_before_collision_closest_distance_m": min(float(frame["distance_m"]) for frame in selected_frames),
        "selected_first_support_ts": (
            min(float(frame["ts"]) for frame in support_frames) if support_frames else None
        ),
        "selected_last_support_ts": (
            max(float(frame["ts"]) for frame in support_frames) if support_frames else None
        ),
        "selected_at_fire_support": fire_frame["actor_support"],
        "selected_pre_fire_support_count": len(pre_support),
        "selected_post_fire_support_count": len(post_support),
        "pre_fire_selected_active_frame_count": sum(
            frame["surface_state"] == "active" for frame in pre_fire_frames
        ),
        "pre_fire_selected_borderline_frame_count": sum(
            frame["surface_state"] == "borderline" for frame in pre_fire_frames
        ),
        "pre_fire_selected_far_frame_count": sum(
            frame["surface_state"] == "far" for frame in pre_fire_frames
        ),
        "problems": [],
    }


def _dict_counts(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def _minmax_rows(rows: list[dict[str, Any]], key: str) -> dict[str, float | None]:
    return _minmax([float(row[key]) for row in rows if numeric(row.get(key))])


def _sum_nested_phase_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        nested = row.get(key)
        if isinstance(nested, dict):
            for phase, value in nested.items():
                if isinstance(value, int):
                    counter[str(phase)] += value
    return {phase: counter[phase] for phase in ("pre_fire", "at_fire", "post_fire_pre_collision") if counter[phase]}


def choose_verdict(infra_problems: list[str], rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if infra_problems or any(row.get("problems") for row in rows):
        return INFRA_NULL_VERDICT
    if summary.get("row_count") != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    if sum(summary.get("selected_lifecycle_label_counts", {}).values()) != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    required = (
        "selected_lifecycle_label",
        "selected_support_phase_counts",
        "selected_surface_counts_by_phase",
        "selected_pre_fire_closest_distance_m",
        "selected_at_fire_distance_m",
        "selected_before_collision_closest_distance_m",
    )
    for row in rows:
        for key in required:
            if key not in row:
                return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(iter119_report_path: Path, proof_root: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter119_report, report_problems = load_json(iter119_report_path, "iter119-report")
    infra_problems.extend(report_problems)
    rows: list[dict[str, Any]] = []
    if not infra_problems:
        require_equal(infra_problems, "iter119-verdict", iter119_report.get("verdict"), ITER119_VERDICT)
        replacement_rows = iter119_report.get("replacement_rows")
        if not isinstance(replacement_rows, list):
            infra_problems.append("iter119-replacement-rows-not-list")
            replacement_rows = []
        require_equal(infra_problems, "iter119-row-count", len(replacement_rows), EXPECTED_ROW_COUNT)
    if not infra_problems:
        rows = [classify_row(row, proof_root) for row in iter119_report["replacement_rows"] if isinstance(row, dict)]

    clean_rows = [row for row in rows if not row.get("problems")]
    labels = Counter(row.get("selected_lifecycle_label") for row in clean_rows)
    summary = {
        "row_count": len(rows),
        "problem_row_count": sum(bool(row.get("problems")) for row in rows),
        "selected_lifecycle_label_counts": _dict_counts(labels),
        "selected_support_phase_counts": _sum_nested_phase_counts(clean_rows, "selected_support_phase_counts"),
        "selected_supported_before_fire_count": sum(row.get("selected_pre_fire_support_count", 0) > 0 for row in clean_rows),
        "selected_supported_at_fire_count": sum(row.get("selected_at_fire_support") is True for row in clean_rows),
        "selected_supported_post_fire_count": sum(row.get("selected_post_fire_support_count", 0) > 0 for row in clean_rows),
        "selected_presence_frame_count": _minmax_rows(clean_rows, "selected_presence_frame_count"),
        "selected_support_frame_count": _minmax_rows(clean_rows, "selected_support_frame_count"),
        "selected_pre_fire_closest_distance_m": _minmax_rows(clean_rows, "selected_pre_fire_closest_distance_m"),
        "selected_at_fire_distance_m": _minmax_rows(clean_rows, "selected_at_fire_distance_m"),
        "selected_before_collision_closest_distance_m": _minmax_rows(
            clean_rows,
            "selected_before_collision_closest_distance_m",
        ),
        "pre_fire_selected_active_frame_count": _minmax_rows(clean_rows, "pre_fire_selected_active_frame_count"),
        "pre_fire_selected_borderline_frame_count": _minmax_rows(
            clean_rows,
            "pre_fire_selected_borderline_frame_count",
        ),
        "pre_fire_selected_far_frame_count": _minmax_rows(clean_rows, "pre_fire_selected_far_frame_count"),
    }
    verdict = choose_verdict(infra_problems, rows, summary)
    return {
        "iteration": 120,
        "inputs": {
            "iter119_report": str(iter119_report_path),
            "proof_root": str(proof_root),
            "iter59_analyzer": "experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py",
        },
        "infra_problems": infra_problems,
        "selected_lifecycle_rows": rows,
        "summary": summary,
        "verdict": verdict,
        "claim_boundary": (
            "descriptive support-core selected fire-object backward lifecycle audit of eight "
            "committed rows only; no repair, actor-causality, threshold-value, transfer, safety, "
            "deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world "
            "behavior, first-responder behavior, acquisition-value, retuning, production, or "
            "commercial claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 120 - HUGSIM selected fire-object backward lifecycle audit",
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
            "| slot | scenario | run | label | selected | rank | pre best | fire m | global best | support phases |",
            "|---:|---|---:|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in report["selected_lifecycle_rows"]:
        lines.append(
            f"| `{row.get('slot_index')}` | `{row.get('scenario')}` | `{row.get('run')}` | "
            f"`{row.get('selected_lifecycle_label')}` | `{row.get('selected_object_id')}` | "
            f"`{row.get('selected_rank_by_collision_distance')}` | "
            f"`{row.get('selected_pre_fire_closest_distance_m')}` | "
            f"`{row.get('selected_at_fire_distance_m')}` | "
            f"`{row.get('selected_before_collision_closest_distance_m')}` | "
            f"`{row.get('selected_support_phase_counts')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter119_report: Path, proof_root: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter119_report, proof_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter119-report",
        type=Path,
        default=Path(
            "experiments/iter119_hugsim_support_core_loss_replacement_audit/proof-replacement/"
            "support_core_loss_replacement_report.json"
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
            "experiments/iter120_hugsim_support_core_selected_fire_object_lifecycle/proof-selected/"
            "selected_fire_object_lifecycle_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter120_hugsim_support_core_selected_fire_object_lifecycle/proof-selected/"
            "selected_fire_object_lifecycle.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter119_report, args.proof_root, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
