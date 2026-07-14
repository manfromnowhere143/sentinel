#!/usr/bin/env python3
"""Iteration 119 HUGSIM support-core support-loss and replacement audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER117_VERDICT = "HUGSIM_SUPPORT_CORE_EVENT_WINDOW_COMPLETE"
ITER118_VERDICT = "HUGSIM_SUPPORT_CORE_OBJECT_LIFECYCLE_COMPLETE"
COMPLETE_VERDICT = "HUGSIM_SUPPORT_CORE_LOSS_REPLACEMENT_COMPLETE"
INFRA_NULL_VERDICT = "HUGSIM_SUPPORT_CORE_LOSS_REPLACEMENT_INFRA_NULL"
EXPECTED_ROW_COUNT = 8
SUPPORT_M = 6.0


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


def slot_dir(proof_root: Path, row: dict[str, Any]) -> Path:
    return proof_root / f"{row['slot_id']}__{row['scenario']}__on"


def read_decision_rows(path: Path) -> list[dict[str, Any]]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    return [row for row in rows if isinstance(row, dict) and "trace_error" not in row]


def frame_ts(frame: dict[str, Any]) -> float:
    return ITER59.require_float(frame.get("ts", frame.get("frame_index", 0)), "frame.ts")


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


def selected_rank(objects: list[dict[str, Any]], selected_object_id: Any) -> int | None:
    for index, obj in enumerate(objects, start=1):
        if obj.get("object_id") == selected_object_id:
            return index
    return None


def replacement_label(
    first_support_phase: str,
    object_present_at_fire: bool | None,
    selected_is_nearest: bool,
) -> str:
    if first_support_phase == "never_before_collision":
        return "never_supported_reference_selected_nearest" if selected_is_nearest else (
            "never_supported_reference_selected_not_nearest"
        )
    if first_support_phase == "post_fire_pre_collision":
        return "post_fire_support_selected_nearest" if selected_is_nearest else (
            "post_fire_support_selected_not_nearest"
        )
    if object_present_at_fire:
        return "pre_fire_drifted_selected_nearest" if selected_is_nearest else (
            "pre_fire_drifted_selected_not_nearest"
        )
    return "pre_fire_lost_absent_selected_nearest" if selected_is_nearest else (
        "pre_fire_lost_absent_selected_not_nearest"
    )


def gap(first_fire_ts: float, event_ts: Any) -> float | None:
    if not numeric(event_ts):
        return None
    return first_fire_ts - float(event_ts)


def classify_row(event_row: dict[str, Any], lifecycle_row: dict[str, Any], proof_root: Path) -> dict[str, Any]:
    problems: list[str] = []
    for key in ("slot_id", "scenario", "run"):
        if event_row.get(key) != lifecycle_row.get(key):
            problems.append(f"lifecycle-{key}-mismatch:{lifecycle_row.get(key)!r}!={event_row.get(key)!r}")
    if event_row.get("problems"):
        problems.append(f"iter117-row-problems:{event_row.get('problems')!r}")
    if lifecycle_row.get("problems"):
        problems.append(f"iter118-row-problems:{lifecycle_row.get('problems')!r}")
    selected_object_id = event_row.get("selected_object_id")
    if selected_object_id is None:
        problems.append("selected-object-missing")
    first_support_phase = lifecycle_row.get("first_support_phase")
    if not isinstance(first_support_phase, str):
        problems.append(f"first-support-phase-missing:{first_support_phase!r}")
    ep_dir = slot_dir(proof_root, event_row)
    eval_path = ep_dir / "eval.json"
    decisions_path = ep_dir / "sentinel_iter48_decisions.jsonl"
    if not eval_path.exists() or eval_path.stat().st_size == 0:
        problems.append(f"missing-eval:{eval_path}")
    if not decisions_path.exists() or decisions_path.stat().st_size == 0:
        problems.append(f"missing-decisions:{decisions_path}")
    if problems:
        return {
            "slot_index": event_row.get("slot_index"),
            "slot_id": event_row.get("slot_id"),
            "scenario": event_row.get("scenario"),
            "run": event_row.get("run"),
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
        first_fire_frame = next(
            (
                row for row in decision_rows
                if numeric(row.get("ts", row.get("frame_index", 0)))
                and float(row.get("ts", row.get("frame_index", 0))) == first_fire_ts
            ),
            None,
        )
        if first_fire_frame is None:
            raise ValueError(f"first-fire-frame-missing:{first_fire_ts}")
        distances = object_distances_for_frame(first_fire_frame, foreground, foreground_ts)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return {
            "slot_index": event_row.get("slot_index"),
            "slot_id": event_row.get("slot_id"),
            "scenario": event_row.get("scenario"),
            "run": event_row.get("run"),
            "problems": [f"parse-or-reconstruct-failed:{exc}"],
        }

    selected = find_object(distances, selected_object_id)
    if selected is None:
        return {
            "slot_index": event_row.get("slot_index"),
            "slot_id": event_row.get("slot_id"),
            "scenario": event_row.get("scenario"),
            "run": event_row.get("run"),
            "problems": [f"selected-object-absent-at-fire:{selected_object_id!r}"],
        }
    nearest = distances[0]
    first_support_object_id = lifecycle_row.get("first_support_object_id")
    first_support_at_fire = (
        find_object(distances, first_support_object_id)
        if first_support_object_id is not None
        else None
    )
    rank = selected_rank(distances, selected_object_id)
    if rank is None:
        return {
            "slot_index": event_row.get("slot_index"),
            "slot_id": event_row.get("slot_id"),
            "scenario": event_row.get("scenario"),
            "run": event_row.get("run"),
            "problems": [f"selected-rank-missing:{selected_object_id!r}"],
        }
    selected_is_nearest = selected_object_id == nearest["object_id"]
    label = replacement_label(
        str(first_support_phase),
        lifecycle_row.get("object_present_at_fire"),
        selected_is_nearest,
    )
    fire_minus_last_support = gap(first_fire_ts, lifecycle_row.get("object_last_support_before_or_at_fire_ts"))
    fire_minus_last_presence = gap(first_fire_ts, lifecycle_row.get("object_last_presence_before_or_at_fire_ts"))
    return {
        "slot_index": event_row.get("slot_index"),
        "slot_id": event_row.get("slot_id"),
        "scenario": event_row.get("scenario"),
        "run": event_row.get("run"),
        "first_fire_ts": first_fire_ts,
        "first_foreground_ts": foreground_ts,
        "first_support_phase": first_support_phase,
        "first_support_object_id": first_support_object_id,
        "first_support_object_present_at_fire": lifecycle_row.get("object_present_at_fire"),
        "first_support_object_distance_at_fire_m": (
            first_support_at_fire.get("distance_m") if first_support_at_fire else None
        ),
        "fire_minus_last_support_s": fire_minus_last_support,
        "fire_minus_last_presence_s": fire_minus_last_presence,
        "fire_nearest_object_id": nearest["object_id"],
        "fire_nearest_distance_m": nearest["distance_m"],
        "fire_nearest_is_first_support_object": nearest["object_id"] == first_support_object_id,
        "selected_object_id": selected_object_id,
        "selected_distance_m": selected["distance_m"],
        "selected_rank_by_collision_distance": rank,
        "selected_is_fire_nearest": selected_is_nearest,
        "replacement_label": label,
        "fire_object_count": len(distances),
        "top3_fire_object_distances": distances[:3],
        "problems": [],
    }


def _dict_counts(counter: Counter[Any]) -> dict[str, int]:
    return {str(key): counter[key] for key in sorted(counter, key=str)}


def _minmax(rows: list[dict[str, Any]], key: str) -> dict[str, float | None]:
    values = [float(row[key]) for row in rows if numeric(row.get(key))]
    if not values:
        return {"min": None, "max": None}
    return {"min": min(values), "max": max(values)}


def _join_rows(
    event_rows: list[Any],
    lifecycle_rows: list[Any],
    infra_problems: list[str],
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    lifecycle_by_slot = {
        row.get("slot_id"): row
        for row in lifecycle_rows
        if isinstance(row, dict) and row.get("slot_id") is not None
    }
    if len(lifecycle_by_slot) != len(lifecycle_rows):
        infra_problems.append("iter118-slot-ids-not-unique")
    joined: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for row in event_rows:
        if not isinstance(row, dict):
            infra_problems.append("iter117-row-not-dict")
            continue
        slot_id = row.get("slot_id")
        match = lifecycle_by_slot.get(slot_id)
        if not isinstance(match, dict):
            infra_problems.append(f"iter118-row-missing-for-slot:{slot_id!r}")
            continue
        joined.append((row, match))
    return joined


def choose_verdict(infra_problems: list[str], rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    if infra_problems or any(row.get("problems") for row in rows):
        return INFRA_NULL_VERDICT
    if summary.get("row_count") != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    if sum(summary.get("replacement_label_counts", {}).values()) != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    required = (
        "replacement_label",
        "selected_rank_by_collision_distance",
        "fire_nearest_object_id",
        "fire_nearest_distance_m",
        "fire_minus_last_support_s",
        "fire_minus_last_presence_s",
    )
    for row in rows:
        for key in required:
            if key not in row:
                return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(iter117_report_path: Path, iter118_report_path: Path, proof_root: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter117_report, iter117_problems = load_json(iter117_report_path, "iter117-report")
    iter118_report, iter118_problems = load_json(iter118_report_path, "iter118-report")
    infra_problems.extend(iter117_problems)
    infra_problems.extend(iter118_problems)
    rows: list[dict[str, Any]] = []
    if not infra_problems:
        require_equal(infra_problems, "iter117-verdict", iter117_report.get("verdict"), ITER117_VERDICT)
        require_equal(infra_problems, "iter118-verdict", iter118_report.get("verdict"), ITER118_VERDICT)
        event_rows = iter117_report.get("event_window_rows")
        lifecycle_rows = iter118_report.get("lifecycle_rows")
        if not isinstance(event_rows, list):
            infra_problems.append("iter117-event-window-rows-not-list")
            event_rows = []
        if not isinstance(lifecycle_rows, list):
            infra_problems.append("iter118-lifecycle-rows-not-list")
            lifecycle_rows = []
        require_equal(infra_problems, "iter117-row-count", len(event_rows), EXPECTED_ROW_COUNT)
        require_equal(infra_problems, "iter118-row-count", len(lifecycle_rows), EXPECTED_ROW_COUNT)
    if not infra_problems:
        joined = _join_rows(iter117_report["event_window_rows"], iter118_report["lifecycle_rows"], infra_problems)
        if not infra_problems:
            rows = [classify_row(event_row, lifecycle_row, proof_root) for event_row, lifecycle_row in joined]

    clean_rows = [row for row in rows if not row.get("problems")]
    labels = Counter(row.get("replacement_label") for row in clean_rows)
    summary = {
        "row_count": len(rows),
        "problem_row_count": sum(bool(row.get("problems")) for row in rows),
        "replacement_label_counts": _dict_counts(labels),
        "selected_is_fire_nearest_count": sum(row.get("selected_is_fire_nearest") is True for row in clean_rows),
        "selected_not_fire_nearest_count": sum(row.get("selected_is_fire_nearest") is False for row in clean_rows),
        "fire_nearest_is_first_support_object_count": sum(
            row.get("fire_nearest_is_first_support_object") is True for row in clean_rows
        ),
        "fire_minus_last_support_s": _minmax(clean_rows, "fire_minus_last_support_s"),
        "fire_minus_last_presence_s": _minmax(clean_rows, "fire_minus_last_presence_s"),
        "fire_nearest_distance_m": _minmax(clean_rows, "fire_nearest_distance_m"),
        "selected_distance_m": _minmax(clean_rows, "selected_distance_m"),
        "selected_rank_by_collision_distance": _minmax(clean_rows, "selected_rank_by_collision_distance"),
        "first_support_object_distance_at_fire_m": _minmax(clean_rows, "first_support_object_distance_at_fire_m"),
    }
    verdict = choose_verdict(infra_problems, rows, summary)
    return {
        "iteration": 119,
        "inputs": {
            "iter117_report": str(iter117_report_path),
            "iter118_report": str(iter118_report_path),
            "proof_root": str(proof_root),
            "iter59_analyzer": "experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py",
        },
        "infra_problems": infra_problems,
        "replacement_rows": rows,
        "summary": summary,
        "verdict": verdict,
        "claim_boundary": (
            "descriptive support-core support-loss and first-fire replacement audit of eight "
            "committed rows only; no repair, actor-causality, threshold-value, transfer, safety, "
            "deployment, robustness, benchmark, population-rate, HD-Score-invariance, real-world "
            "behavior, first-responder behavior, acquisition-value, retuning, production, or "
            "commercial claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 119 - HUGSIM support-core support-loss and replacement audit",
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
            "| slot | scenario | run | label | support object | last support gap | last presence gap | fire nearest | selected | rank |",
            "|---:|---|---:|---|---:|---:|---:|---|---|---:|",
        ]
    )
    for row in report["replacement_rows"]:
        lines.append(
            f"| `{row.get('slot_index')}` | `{row.get('scenario')}` | `{row.get('run')}` | "
            f"`{row.get('replacement_label')}` | `{row.get('first_support_object_id')}` | "
            f"`{row.get('fire_minus_last_support_s')}` | `{row.get('fire_minus_last_presence_s')}` | "
            f"`{row.get('fire_nearest_object_id')}` / `{row.get('fire_nearest_distance_m')}` | "
            f"`{row.get('selected_object_id')}` / `{row.get('selected_distance_m')}` | "
            f"`{row.get('selected_rank_by_collision_distance')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter117_report: Path,
    iter118_report: Path,
    proof_root: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter117_report, iter118_report, proof_root)
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
        "--iter118-report",
        type=Path,
        default=Path(
            "experiments/iter118_hugsim_support_core_object_lifecycle/proof-lifecycle/"
            "support_core_object_lifecycle_report.json"
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
            "experiments/iter119_hugsim_support_core_loss_replacement_audit/proof-replacement/"
            "support_core_loss_replacement_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter119_hugsim_support_core_loss_replacement_audit/proof-replacement/"
            "support_core_loss_replacement.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter117_report,
        args.iter118_report,
        args.proof_root,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
