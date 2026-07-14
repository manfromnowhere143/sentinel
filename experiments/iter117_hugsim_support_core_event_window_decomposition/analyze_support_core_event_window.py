#!/usr/bin/env python3
"""Iteration 117 HUGSIM support-core event-window decomposition."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER115_VERDICT = "HUGSIM_SUPPORT_CORE_MONITOR_SET_ORDERING_COMPLETE"
ITER116_VERDICT = "HUGSIM_SUPPORT_CORE_COLLISION_ACTOR_TIMELINE_COMPLETE"
COMPLETE_VERDICT = "HUGSIM_SUPPORT_CORE_EVENT_WINDOW_COMPLETE"
INFRA_NULL_VERDICT = "HUGSIM_SUPPORT_CORE_EVENT_WINDOW_INFRA_NULL"
EXPECTED_ROW_COUNT = 8
SUPPORT_M = 6.0
CPA_BORDERLINE_M = 3.0
TTC_BORDERLINE_S = 5.0
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


def surface_state(frame: dict[str, Any]) -> dict[str, Any]:
    params = frame.get("params")
    if not isinstance(params, dict):
        raise ValueError("frame-params-not-dict")
    min_cpa = ITER59.require_float(frame.get("min_cpa"), "min_cpa")
    min_ttc_raw = ITER59.require_float(frame.get("min_ttc"), "min_ttc")
    cpa_margin = ITER59.require_float(params.get("cpa_margin"), "cpa_margin")
    ttc_thresh = ITER59.require_float(params.get("ttc_thresh"), "ttc_thresh")
    ttc_valid = finite_ttc(min_ttc_raw)
    ttc_value = min_ttc_raw if ttc_valid else None
    cpa_active = min_cpa <= cpa_margin
    ttc_active = bool(ttc_valid and min_ttc_raw <= ttc_thresh)
    cpa_borderline = min_cpa <= CPA_BORDERLINE_M
    ttc_borderline = bool(ttc_valid and min_ttc_raw <= TTC_BORDERLINE_S)
    if cpa_active or ttc_active:
        state = "active"
    elif cpa_borderline or ttc_borderline:
        state = "borderline"
    else:
        state = "far"
    return {
        "surface_state": state,
        "min_cpa": min_cpa,
        "min_ttc_raw": min_ttc_raw,
        "min_ttc_valid_s": ttc_value,
        "cpa_margin": cpa_margin,
        "ttc_thresh": ttc_thresh,
        "active_cpa_margin_m": min_cpa - cpa_margin,
        "active_ttc_margin_s": (min_ttc_raw - ttc_thresh) if ttc_valid else None,
        "cpa_active": cpa_active,
        "ttc_active": ttc_active,
        "cpa_borderline_registered": cpa_borderline,
        "ttc_borderline_registered": ttc_borderline,
        "fired": bool(frame.get("fired")),
        "brake": bool(frame.get("brake")),
    }


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


def measure_frame(
    frame: dict[str, Any],
    foreground: dict[str, Any],
    foreground_ts: float,
    first_fire_ts: float,
) -> dict[str, Any]:
    distances = object_distances_for_frame(frame, foreground, foreground_ts)
    nearest = distances[0]
    ts = frame_ts(frame)
    surface = surface_state(frame)
    return {
        "ts": ts,
        "frame_index": frame.get("frame_index"),
        "phase": frame_phase(ts, first_fire_ts),
        "object_count": len(distances),
        "nearest_object_id": nearest["object_id"],
        "nearest_distance_m": nearest["distance_m"],
        "nearest_monitor_forward_m": nearest["monitor_forward_m"],
        "nearest_monitor_lateral_m": nearest["monitor_lateral_m"],
        "actor_support": float(nearest["distance_m"]) <= SUPPORT_M,
        "object_distances": distances,
        **surface,
    }


def find_frame_by_ts(frames: list[dict[str, Any]], ts: float) -> dict[str, Any] | None:
    for frame in frames:
        if frame_ts(frame) == ts:
            return frame
    return None


def find_object(objects: list[dict[str, Any]], object_id: Any) -> dict[str, Any] | None:
    for obj in objects:
        if obj.get("object_id") == object_id:
            return obj
    return None


def compact_event(event: dict[str, Any] | None) -> dict[str, Any] | None:
    if event is None:
        return None
    return {
        "ts": event.get("ts"),
        "frame_index": event.get("frame_index"),
        "phase": event.get("phase"),
        "surface_state": event.get("surface_state"),
        "fired": event.get("fired"),
        "brake": event.get("brake"),
        "min_cpa": event.get("min_cpa"),
        "min_ttc_valid_s": event.get("min_ttc_valid_s"),
        "nearest_object_id": event.get("nearest_object_id"),
        "nearest_distance_m": event.get("nearest_distance_m"),
        "object_count": event.get("object_count"),
        "actor_support": event.get("actor_support"),
    }


def support_surface_counts(frames: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(frame["surface_state"] for frame in frames if frame.get("actor_support"))
    return {key: counter[key] for key in ("active", "borderline", "far") if counter[key]}


def support_phase_counts(frames: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(frame["phase"] for frame in frames if frame.get("actor_support"))
    return {key: counter[key] for key in ("pre_fire", "at_fire", "post_fire_pre_collision") if counter[key]}


def row_label(first_support_phase: str, pre_fire_supports: list[dict[str, Any]]) -> str:
    if first_support_phase == "never_before_collision":
        return "never_supported_before_collision"
    if first_support_phase == "post_fire_pre_collision":
        return "post_fire_support_only"
    if any(frame["surface_state"] == "active" for frame in pre_fire_supports):
        return "pre_fire_support_surface_active"
    if any(frame["surface_state"] == "borderline" for frame in pre_fire_supports):
        return "pre_fire_support_surface_borderline_only"
    return "pre_fire_support_surface_far_only"


def classify_row(iter115_row: dict[str, Any], iter116_row: dict[str, Any], proof_root: Path) -> dict[str, Any]:
    problems: list[str] = []
    slot_id = iter115_row.get("slot_id")
    if iter115_row.get("problems"):
        problems.append(f"iter115-row-problems:{iter115_row.get('problems')!r}")
    combined = iter115_row.get("combined_label")
    if not isinstance(combined, str) or not combined.startswith("whole_set_mismatch"):
        problems.append(f"combined-label-not-whole-set-mismatch:{combined!r}")
    for key in ("slot_id", "scenario", "run"):
        if iter116_row.get(key) != iter115_row.get(key):
            problems.append(f"iter116-{key}-mismatch:{iter116_row.get(key)!r}!={iter115_row.get(key)!r}")
    if iter116_row.get("problems"):
        problems.append(f"iter116-row-problems:{iter116_row.get('problems')!r}")
    first_support_phase = iter116_row.get("first_support_phase")
    if not isinstance(first_support_phase, str):
        problems.append(f"iter116-first-support-phase-missing:{first_support_phase!r}")
    selected_object_id = iter115_row.get("selected_object_id")
    ep_dir = slot_dir(proof_root, iter115_row)
    eval_path = ep_dir / "eval.json"
    decisions_path = ep_dir / "sentinel_iter48_decisions.jsonl"
    if not eval_path.exists() or eval_path.stat().st_size == 0:
        problems.append(f"missing-eval:{eval_path}")
    if not decisions_path.exists() or decisions_path.stat().st_size == 0:
        problems.append(f"missing-decisions:{decisions_path}")
    if problems:
        return {
            "slot_index": iter115_row.get("slot_index"),
            "slot_id": slot_id,
            "scenario": iter115_row.get("scenario"),
            "run": iter115_row.get("run"),
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
        considered_raw = [
            row for row in decision_rows
            if numeric(row.get("ts", row.get("frame_index", 0)))
            and float(row.get("ts", row.get("frame_index", 0))) <= foreground_ts
        ]
        if not considered_raw:
            raise ValueError("no-decision-frame-before-foreground")
        first_fire_raw = find_frame_by_ts(considered_raw, first_fire_ts)
        if first_fire_raw is None:
            raise ValueError(f"first-fire-frame-missing:{first_fire_ts}")
        frame_rows = [
            measure_frame(row, foreground, foreground_ts, first_fire_ts)
            for row in considered_raw
        ]
        first_fire_event = next(row for row in frame_rows if row["ts"] == first_fire_ts)
        foreground_event = next((row for row in frame_rows if row["ts"] == foreground_ts), None)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return {
            "slot_index": iter115_row.get("slot_index"),
            "slot_id": slot_id,
            "scenario": iter115_row.get("scenario"),
            "run": iter115_row.get("run"),
            "problems": [f"parse-or-reconstruct-failed:{exc}"],
        }

    support_frames = [frame for frame in frame_rows if frame["actor_support"]]
    pre_fire_supports = [frame for frame in support_frames if frame["phase"] == "pre_fire"]
    first_support_event = None
    if first_support_phase != "never_before_collision":
        first_support_ts = iter116_row.get("first_support_ts")
        if not numeric(first_support_ts):
            return {
                "slot_index": iter115_row.get("slot_index"),
                "slot_id": slot_id,
                "scenario": iter115_row.get("scenario"),
                "run": iter115_row.get("run"),
                "problems": [f"iter116-first-support-ts-invalid:{first_support_ts!r}"],
            }
        first_support_event = next((frame for frame in frame_rows if frame["ts"] == float(first_support_ts)), None)
        if first_support_event is None:
            return {
                "slot_index": iter115_row.get("slot_index"),
                "slot_id": slot_id,
                "scenario": iter115_row.get("scenario"),
                "run": iter115_row.get("run"),
                "problems": [f"first-support-frame-missing:{first_support_ts!r}"],
            }

    first_support_object_id = first_support_event.get("nearest_object_id") if first_support_event else None
    first_support_at_fire = (
        find_object(first_fire_event["object_distances"], first_support_object_id)
        if first_support_object_id is not None
        else None
    )
    support_object_present_at_fire = first_support_at_fire is not None if first_support_object_id is not None else None
    fire_nearest_object_id = first_fire_event["nearest_object_id"]
    support_same_as_selected = (
        first_support_object_id == selected_object_id if first_support_object_id is not None else None
    )
    support_same_as_fire_nearest = (
        first_support_object_id == fire_nearest_object_id if first_support_object_id is not None else None
    )
    label = row_label(str(first_support_phase), pre_fire_supports)
    fire_minus_support_s = (
        first_fire_ts - float(first_support_event["ts"]) if first_support_event is not None else None
    )
    return {
        "slot_index": iter115_row.get("slot_index"),
        "slot_id": slot_id,
        "scenario": iter115_row.get("scenario"),
        "run": iter115_row.get("run"),
        "first_fire_ts": first_fire_ts,
        "first_foreground_ts": foreground_ts,
        "selected_object_id": selected_object_id,
        "first_support_phase": first_support_phase,
        "first_support_ts": first_support_event.get("ts") if first_support_event else None,
        "first_support_object_id": first_support_object_id,
        "fire_minus_first_support_s": fire_minus_support_s,
        "row_label": label,
        "support_phase_counts": support_phase_counts(frame_rows),
        "support_surface_counts": support_surface_counts(frame_rows),
        "pre_fire_support_surface_counts": support_surface_counts(pre_fire_supports),
        "support_frame_count": len(support_frames),
        "pre_fire_support_frame_count": len(pre_fire_supports),
        "first_support_event": compact_event(first_support_event),
        "first_fire_event": compact_event(first_fire_event),
        "first_foreground_event": compact_event(foreground_event),
        "fire_nearest_object_id": fire_nearest_object_id,
        "fire_nearest_distance_m": first_fire_event["nearest_distance_m"],
        "support_object_present_at_fire": support_object_present_at_fire,
        "support_object_distance_at_fire_m": first_support_at_fire.get("distance_m") if first_support_at_fire else None,
        "support_object_same_as_selected": support_same_as_selected,
        "support_object_same_as_fire_nearest": support_same_as_fire_nearest,
        "problems": [],
    }


def _dict_counts(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def _minmax(rows: list[dict[str, Any]], key: str) -> dict[str, float | None]:
    values = [float(row[key]) for row in rows if numeric(row.get(key))]
    if not values:
        return {"min": None, "max": None}
    return {"min": min(values), "max": max(values)}


def _aggregate_nested_counts(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        nested = row.get(key)
        if isinstance(nested, dict):
            for nested_key, value in nested.items():
                if isinstance(value, int):
                    counter[str(nested_key)] += value
    return _dict_counts(counter)


def _join_rows(iter115_rows: list[Any], iter116_rows: list[Any], infra_problems: list[str]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    joined: list[tuple[dict[str, Any], dict[str, Any]]] = []
    iter116_by_slot = {
        row.get("slot_id"): row
        for row in iter116_rows
        if isinstance(row, dict) and row.get("slot_id") is not None
    }
    if len(iter116_by_slot) != len(iter116_rows):
        infra_problems.append("iter116-slot-ids-not-unique")
    for row in iter115_rows:
        if not isinstance(row, dict):
            infra_problems.append("iter115-row-not-dict")
            continue
        slot_id = row.get("slot_id")
        match = iter116_by_slot.get(slot_id)
        if not isinstance(match, dict):
            infra_problems.append(f"iter116-row-missing-for-slot:{slot_id!r}")
            continue
        joined.append((row, match))
    return joined


def choose_verdict(infra_problems: list[str], rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if infra_problems or any(row.get("problems") for row in rows):
        return INFRA_NULL_VERDICT
    if summary.get("row_count") != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    if sum(summary.get("row_label_counts", {}).values()) != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    required = (
        "row_label",
        "support_phase_counts",
        "support_surface_counts",
        "first_fire_event",
        "support_object_present_at_fire",
        "support_object_same_as_selected",
        "support_object_same_as_fire_nearest",
    )
    for row in rows:
        for key in required:
            if key not in row:
                return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(iter115_report_path: Path, iter116_report_path: Path, proof_root: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter115_report, iter115_problems = load_json(iter115_report_path, "iter115-report")
    iter116_report, iter116_problems = load_json(iter116_report_path, "iter116-report")
    infra_problems.extend(iter115_problems)
    infra_problems.extend(iter116_problems)
    rows: list[dict[str, Any]] = []
    if not infra_problems:
        require_equal(infra_problems, "iter115-verdict", iter115_report.get("verdict"), ITER115_VERDICT)
        require_equal(infra_problems, "iter116-verdict", iter116_report.get("verdict"), ITER116_VERDICT)
        iter115_rows = iter115_report.get("ordering_rows")
        iter116_rows = iter116_report.get("timeline_rows")
        if not isinstance(iter115_rows, list):
            infra_problems.append("iter115-ordering-rows-not-list")
            iter115_rows = []
        if not isinstance(iter116_rows, list):
            infra_problems.append("iter116-timeline-rows-not-list")
            iter116_rows = []
        require_equal(infra_problems, "iter115-row-count", len(iter115_rows), EXPECTED_ROW_COUNT)
        require_equal(infra_problems, "iter116-row-count", len(iter116_rows), EXPECTED_ROW_COUNT)
    if not infra_problems:
        joined = _join_rows(iter115_report["ordering_rows"], iter116_report["timeline_rows"], infra_problems)
        if not infra_problems:
            rows = [classify_row(iter115_row, iter116_row, proof_root) for iter115_row, iter116_row in joined]

    clean_rows = [row for row in rows if not row.get("problems")]
    row_labels = Counter(row.get("row_label") for row in clean_rows)
    first_support_surface = Counter(
        row.get("first_support_event", {}).get("surface_state")
        for row in clean_rows
        if isinstance(row.get("first_support_event"), dict)
    )
    first_fire_surface = Counter(
        row.get("first_fire_event", {}).get("surface_state")
        for row in clean_rows
        if isinstance(row.get("first_fire_event"), dict)
    )
    summary = {
        "row_count": len(rows),
        "problem_row_count": sum(bool(row.get("problems")) for row in rows),
        "row_label_counts": _dict_counts(row_labels),
        "first_support_surface_state_counts": _dict_counts(first_support_surface),
        "first_fire_surface_state_counts": _dict_counts(first_fire_surface),
        "support_phase_counts": _aggregate_nested_counts(clean_rows, "support_phase_counts"),
        "support_surface_counts": _aggregate_nested_counts(clean_rows, "support_surface_counts"),
        "support_object_present_at_fire_count": sum(
            row.get("support_object_present_at_fire") is True for row in clean_rows
        ),
        "support_object_same_as_selected_count": sum(
            row.get("support_object_same_as_selected") is True for row in clean_rows
        ),
        "support_object_same_as_fire_nearest_count": sum(
            row.get("support_object_same_as_fire_nearest") is True for row in clean_rows
        ),
        "support_frame_count": _minmax(clean_rows, "support_frame_count"),
        "pre_fire_support_frame_count": _minmax(clean_rows, "pre_fire_support_frame_count"),
        "fire_minus_first_support_s": _minmax(clean_rows, "fire_minus_first_support_s"),
        "support_object_distance_at_fire_m": _minmax(clean_rows, "support_object_distance_at_fire_m"),
        "fire_nearest_distance_m": _minmax(clean_rows, "fire_nearest_distance_m"),
    }
    verdict = choose_verdict(infra_problems, rows, summary)
    return {
        "iteration": 117,
        "inputs": {
            "iter115_report": str(iter115_report_path),
            "iter116_report": str(iter116_report_path),
            "proof_root": str(proof_root),
            "iter59_analyzer": "experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py",
        },
        "infra_problems": infra_problems,
        "event_window_rows": rows,
        "summary": summary,
        "verdict": verdict,
        "claim_boundary": (
            "descriptive support-core event-window decomposition of eight committed rows only; "
            "no repair, actor-causality, threshold-value, transfer, safety, deployment, robustness, "
            "benchmark, population-rate, HD-Score-invariance, real-world behavior, first-responder "
            "behavior, acquisition-value, retuning, production, or commercial claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 117 - HUGSIM support-core event-window decomposition",
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
            "| slot | scenario | run | label | first support | support surface | fire surface | support at fire | same selected | same nearest |",
            "|---:|---|---:|---|---|---|---|---|---|---|",
        ]
    )
    for row in report["event_window_rows"]:
        first_support = row.get("first_support_event")
        first_support_state = first_support.get("surface_state") if isinstance(first_support, dict) else None
        first_fire = row.get("first_fire_event")
        first_fire_state = first_fire.get("surface_state") if isinstance(first_fire, dict) else None
        lines.append(
            f"| `{row.get('slot_index')}` | `{row.get('scenario')}` | `{row.get('run')}` | "
            f"`{row.get('row_label')}` | `{row.get('first_support_phase')}` | "
            f"`{first_support_state}` | `{first_fire_state}` | "
            f"`{row.get('support_object_present_at_fire')}` | "
            f"`{row.get('support_object_same_as_selected')}` | "
            f"`{row.get('support_object_same_as_fire_nearest')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter115_report: Path,
    iter116_report: Path,
    proof_root: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter115_report, iter116_report, proof_root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter115-report",
        type=Path,
        default=Path(
            "experiments/iter115_hugsim_support_core_monitor_set_ordering/proof-ordering/"
            "support_core_monitor_set_ordering_report.json"
        ),
    )
    parser.add_argument(
        "--iter116-report",
        type=Path,
        default=Path(
            "experiments/iter116_hugsim_support_core_collision_actor_timeline/proof-timeline/"
            "support_core_collision_actor_timeline_report.json"
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
            "experiments/iter117_hugsim_support_core_event_window_decomposition/proof-event-window/"
            "support_core_event_window_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter117_hugsim_support_core_event_window_decomposition/proof-event-window/"
            "support_core_event_window.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter115_report, args.iter116_report, args.proof_root, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
