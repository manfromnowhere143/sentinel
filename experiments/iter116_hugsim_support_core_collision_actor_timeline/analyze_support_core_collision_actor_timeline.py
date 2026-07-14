#!/usr/bin/env python3
"""Iteration 116 HUGSIM support-core collision-actor timeline audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER115_VERDICT = "HUGSIM_SUPPORT_CORE_MONITOR_SET_ORDERING_COMPLETE"
COMPLETE_VERDICT = "HUGSIM_SUPPORT_CORE_COLLISION_ACTOR_TIMELINE_COMPLETE"
INFRA_NULL_VERDICT = "HUGSIM_SUPPORT_CORE_COLLISION_ACTOR_TIMELINE_INFRA_NULL"
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


def nearest_object_for_frame(frame: dict[str, Any], foreground: dict[str, Any], foreground_ts: float) -> dict[str, Any]:
    ts = ITER59.require_float(frame.get("ts", frame.get("frame_index", 0)), "frame.ts")
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
    candidates: list[dict[str, Any]] = []
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
        candidates.append(
            {
                "object_id": obj.get("id"),
                "distance_m": math.hypot(monitor_forward - obs_forward, monitor_lateral - obs_lateral),
                "monitor_forward_m": monitor_forward,
                "monitor_lateral_m": monitor_lateral,
            }
        )
    candidates.sort(key=lambda item: (float(item["distance_m"]), str(item["object_id"])))
    nearest = candidates[0]
    return {
        "ts": ts,
        "frame_index": frame.get("frame_index"),
        "object_count": len(candidates),
        "nearest_object_id": nearest["object_id"],
        "nearest_distance_m": nearest["distance_m"],
        "nearest_monitor_forward_m": nearest["monitor_forward_m"],
        "nearest_monitor_lateral_m": nearest["monitor_lateral_m"],
    }


def _phase_min(frames: list[dict[str, Any]], phase: str) -> float | None:
    values = [float(frame["nearest_distance_m"]) for frame in frames if frame.get("phase") == phase]
    return min(values) if values else None


def classify_row(iter115_row: dict[str, Any], proof_root: Path) -> dict[str, Any]:
    problems: list[str] = []
    if iter115_row.get("problems"):
        problems.append(f"iter115-row-problems:{iter115_row.get('problems')!r}")
    combined = iter115_row.get("combined_label")
    if not isinstance(combined, str) or not combined.startswith("whole_set_mismatch"):
        problems.append(f"combined-label-not-whole-set-mismatch:{combined!r}")
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
            "slot_id": iter115_row.get("slot_id"),
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
        considered = [
            row for row in decision_rows
            if numeric(row.get("ts", row.get("frame_index", 0)))
            and float(row.get("ts", row.get("frame_index", 0))) <= foreground_ts
        ]
        if not considered:
            raise ValueError("no-decision-frame-before-foreground")
        frame_rows: list[dict[str, Any]] = []
        for frame in considered:
            nearest = nearest_object_for_frame(frame, foreground, foreground_ts)
            phase = frame_phase(float(nearest["ts"]), first_fire_ts)
            nearest.update(
                {
                    "phase": phase,
                    "actor_support": float(nearest["nearest_distance_m"]) <= SUPPORT_M,
                }
            )
            frame_rows.append(nearest)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return {
            "slot_index": iter115_row.get("slot_index"),
            "slot_id": iter115_row.get("slot_id"),
            "scenario": iter115_row.get("scenario"),
            "run": iter115_row.get("run"),
            "problems": [f"parse-or-reconstruct-failed:{exc}"],
        }

    support_frames = [frame for frame in frame_rows if frame["actor_support"]]
    first_support = min(support_frames, key=lambda frame: float(frame["ts"])) if support_frames else None
    best = min(frame_rows, key=lambda frame: float(frame["nearest_distance_m"]))
    phase_counts = Counter(frame["phase"] for frame in frame_rows)
    support_phase_counts = Counter(frame["phase"] for frame in support_frames)
    return {
        "slot_index": iter115_row.get("slot_index"),
        "slot_id": iter115_row.get("slot_id"),
        "scenario": iter115_row.get("scenario"),
        "run": iter115_row.get("run"),
        "first_fire_ts": first_fire_ts,
        "first_foreground_ts": foreground_ts,
        "considered_frame_count": len(frame_rows),
        "phase_frame_counts": dict(sorted(phase_counts.items())),
        "support_frame_count": len(support_frames),
        "support_phase_counts": dict(sorted(support_phase_counts.items())),
        "first_support_phase": first_support["phase"] if first_support else "never_before_collision",
        "first_support_ts": first_support["ts"] if first_support else None,
        "first_support_distance_m": first_support["nearest_distance_m"] if first_support else None,
        "first_support_object_id": first_support["nearest_object_id"] if first_support else None,
        "best_phase": best["phase"],
        "best_ts": best["ts"],
        "best_distance_m": best["nearest_distance_m"],
        "best_object_id": best["nearest_object_id"],
        "pre_fire_min_distance_m": _phase_min(frame_rows, "pre_fire"),
        "at_fire_min_distance_m": _phase_min(frame_rows, "at_fire"),
        "post_fire_pre_collision_min_distance_m": _phase_min(frame_rows, "post_fire_pre_collision"),
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
    if sum(summary.get("first_support_phase_counts", {}).values()) != EXPECTED_ROW_COUNT:
        return INFRA_NULL_VERDICT
    return COMPLETE_VERDICT


def build_report(iter115_report_path: Path, proof_root: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter115_report, report_problems = load_json(iter115_report_path, "iter115-report")
    infra_problems.extend(report_problems)
    rows: list[dict[str, Any]] = []
    if not infra_problems:
        require_equal(infra_problems, "iter115-verdict", iter115_report.get("verdict"), ITER115_VERDICT)
        ordering_rows = iter115_report.get("ordering_rows")
        if not isinstance(ordering_rows, list):
            infra_problems.append("iter115-ordering-rows-not-list")
            ordering_rows = []
        require_equal(infra_problems, "iter115-row-count", len(ordering_rows), EXPECTED_ROW_COUNT)
    if not infra_problems:
        rows = [classify_row(row, proof_root) for row in iter115_report["ordering_rows"] if isinstance(row, dict)]

    first_support_counts = Counter(row.get("first_support_phase") for row in rows if not row.get("problems"))
    best_phase_counts = Counter(row.get("best_phase") for row in rows if not row.get("problems"))
    support_any_count = sum(row.get("first_support_phase") != "never_before_collision" for row in rows)
    summary = {
        "row_count": len(rows),
        "problem_row_count": sum(bool(row.get("problems")) for row in rows),
        "support_any_count": support_any_count,
        "first_support_phase_counts": _dict_counts(first_support_counts),
        "best_phase_counts": _dict_counts(best_phase_counts),
        "support_frame_count": _minmax(rows, "support_frame_count"),
        "considered_frame_count": _minmax(rows, "considered_frame_count"),
        "best_distance_m": _minmax(rows, "best_distance_m"),
        "pre_fire_min_distance_m": _minmax(rows, "pre_fire_min_distance_m"),
        "at_fire_min_distance_m": _minmax(rows, "at_fire_min_distance_m"),
        "post_fire_pre_collision_min_distance_m": _minmax(rows, "post_fire_pre_collision_min_distance_m"),
    }
    verdict = choose_verdict(infra_problems, rows, summary)
    return {
        "iteration": 116,
        "inputs": {
            "iter115_report": str(iter115_report_path),
            "proof_root": str(proof_root),
            "iter59_analyzer": "experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py",
        },
        "infra_problems": infra_problems,
        "timeline_rows": rows,
        "summary": summary,
        "verdict": verdict,
        "claim_boundary": (
            "descriptive collision-actor monitor-set timeline audit of eight committed support-core "
            "rows only; no repair, actor-causality, threshold-value, transfer, safety, deployment, "
            "robustness, benchmark, population-rate, HD-Score-invariance, real-world behavior, "
            "first-responder behavior, acquisition-value, retuning, production, or commercial claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 116 - HUGSIM support-core collision-actor timeline audit",
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
            "| slot | scenario | run | first support | support frames | best phase | best m | best id | frames |",
            "|---:|---|---:|---|---:|---|---:|---|---:|",
        ]
    )
    for row in report["timeline_rows"]:
        lines.append(
            f"| `{row.get('slot_index')}` | `{row.get('scenario')}` | `{row.get('run')}` | "
            f"`{row.get('first_support_phase')}` | `{row.get('support_frame_count')}` | "
            f"`{row.get('best_phase')}` | `{row.get('best_distance_m')}` | "
            f"`{row.get('best_object_id')}` | `{row.get('considered_frame_count')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(iter115_report: Path, proof_root: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(iter115_report, proof_root)
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
        "--proof-root",
        type=Path,
        default=Path("experiments/iter112_hugsim_support_core_batch_execution/proof-execution"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(
            "experiments/iter116_hugsim_support_core_collision_actor_timeline/proof-timeline/"
            "support_core_collision_actor_timeline_report.json"
        ),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path(
            "experiments/iter116_hugsim_support_core_collision_actor_timeline/proof-timeline/"
            "support_core_collision_actor_timeline.md"
        ),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.iter115_report, args.proof_root, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
