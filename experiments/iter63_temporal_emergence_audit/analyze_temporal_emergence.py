#!/usr/bin/env python3
"""Iteration 63 temporal emergence audit analyzer."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER61_VERDICT = "OBJECT_SURFACE_NONTRIGGER_MATCH_COMPLETE"
ITER62_VERDICT = "MATCHED_OBJECT_SUBTHRESHOLD_COMPLETE"
TARGET_AUDIT_ID = "ttc_extreme_b"
TARGET_SCENARIO = "scene-0383-extreme-00"
TARGET_OBJECT_ID = 16
TRIGGER_OBJECT_ID = 1
CPA_MARGIN = 1.5
TTC_THRESH = 2.5
CPA_BORDERLINE = 3.0
TTC_BORDERLINE = 5.0
TIME_TOL = 1e-9


def _load_iter59_module() -> Any:
    repo = Path(__file__).resolve().parents[2]
    module_path = repo / "experiments" / "iter59_hugsim_actor_match_audit" / "analyze_actor_match.py"
    spec = importlib.util.spec_from_file_location("iter59_actor_match", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-iter59-analyzer:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ITER59 = _load_iter59_module()


def require_float(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f"non-numeric:{field}")
    return float(value)


def load_report(path: Path, label: str) -> tuple[dict[str, Any], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return {}, [f"missing-{label}:{path}"]
    try:
        report = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return {}, [f"parse-{label}-failed:{exc}"]
    if not isinstance(report, dict):
        return {}, [f"{label}-not-dict"]
    return report, []


def crosscheck_reports(
    iter59_report: dict[str, Any],
    iter61_report: dict[str, Any],
    iter62_report: dict[str, Any],
) -> list[str]:
    problems: list[str] = []
    if iter59_report.get("verdict") != ITER59_VERDICT:
        problems.append(f"iter59-verdict-not-{ITER59_VERDICT}")
    if iter61_report.get("verdict") != ITER61_VERDICT:
        problems.append(f"iter61-verdict-not-{ITER61_VERDICT}")
    if iter62_report.get("verdict") != ITER62_VERDICT:
        problems.append(f"iter62-verdict-not-{ITER62_VERDICT}")

    target = iter62_report.get("target")
    if not isinstance(target, dict):
        problems.append("iter62-target-not-dict")
    else:
        if target.get("audit_id") != TARGET_AUDIT_ID or target.get("scenario") != TARGET_SCENARIO:
            problems.append(f"iter62-target-mismatch:{target.get('audit_id')}/{target.get('scenario')}")
        if target.get("matched_object_id") != TARGET_OBJECT_ID:
            problems.append(f"iter62-matched-object-not-{TARGET_OBJECT_ID}:{target.get('matched_object_id')}")
        if target.get("trigger_object_id") != TRIGGER_OBJECT_ID:
            problems.append(f"iter62-trigger-object-not-{TRIGGER_OBJECT_ID}:{target.get('trigger_object_id')}")
    if iter62_report.get("matched_object_label") != "matched_object_subthreshold":
        problems.append(f"iter62-label-not-subthreshold:{iter62_report.get('matched_object_label')}")

    episodes61 = iter61_report.get("episodes")
    if not isinstance(episodes61, list):
        problems.append("iter61-episodes-not-list")
    else:
        matched_rows = [
            row for row in episodes61
            if isinstance(row, dict) and row.get("row_label") == "nontrigger_object_match"
        ]
        if len(matched_rows) != 1:
            problems.append(f"iter61-nontrigger-match-count-{len(matched_rows)}")
        elif (
            matched_rows[0].get("audit_id") != TARGET_AUDIT_ID
            or matched_rows[0].get("scenario") != TARGET_SCENARIO
        ):
            problems.append(
                f"iter61-target-mismatch:{matched_rows[0].get('audit_id')}/{matched_rows[0].get('scenario')}"
            )
    return problems


def target_paths(proof_root: Path) -> dict[str, Path]:
    ep_dir = proof_root / "episodes" / f"{TARGET_AUDIT_ID}__{TARGET_SCENARIO}__on"
    return {
        "eval": ep_dir / "eval.json",
        "decisions": ep_dir / "sentinel_iter48_decisions.jsonl",
    }


def first_foreground_timestamp(eval_path: Path) -> float:
    doc = json.loads(eval_path.read_text())
    provenance = doc.get("collision_provenance")
    if not isinstance(provenance, list):
        raise ValueError("collision-provenance-not-list")
    timestamps: list[float] = []
    for row in provenance:
        if (
            isinstance(row, dict)
            and row.get("collision_type") == "foreground"
            and isinstance(row.get("obs_box"), list)
            and len(row["obs_box"]) >= 2
        ):
            try:
                require_float(row["obs_box"][0], "obs_box.x")
                require_float(row["obs_box"][1], "obs_box.y")
                timestamps.append(require_float(row.get("timestamp"), "foreground.timestamp"))
            except (TypeError, ValueError):
                continue
    if not timestamps:
        raise ValueError("eligible-foreground-missing")
    return min(timestamps)


def read_decision_rows(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict) and "trace_error" not in row:
            rows.append(row)
    return rows


def object_metric_for_row(row: dict[str, Any], object_id: int) -> dict[str, Any] | None:
    objs = row.get("objs")
    if not isinstance(objs, list):
        raise ValueError("objs-not-list")
    matches = [obj for obj in objs if isinstance(obj, dict) and obj.get("id") == object_id]
    if not matches:
        return None
    if len(matches) != 1:
        raise ValueError(f"object-{object_id}-duplicate")
    obj = matches[0]

    r_mat = ITER59.matrix3(row.get("l2g_r_mat"), "l2g_r_mat")
    trans_raw = row.get("l2g_t")
    if not isinstance(trans_raw, list) or len(trans_raw) < 2:
        raise ValueError("l2g_t-not-vec2")
    trans = [require_float(value, "l2g_t") for value in trans_raw]
    params = row.get("params")
    if not isinstance(params, dict):
        raise ValueError("params-not-dict")
    dt = require_float(params.get("dt"), "params.dt")
    min_closing = require_float(params.get("min_closing"), "params.min_closing")
    traj = row.get("traj")
    if not isinstance(traj, list) or not traj:
        raise ValueError("traj-not-list")
    plan_world = []
    for point in traj:
        px, py = ITER59.vec2(point, "traj")
        plan_world.append(ITER59.transform_xy(px, py, r_mat, trans))

    wx, wy = ITER59.vec2(obj.get("world"), "obj.world")
    vx, vy = ITER59.vec2(obj.get("vel"), "obj.vel")
    min_cpa = math.inf
    cpa_horizon_index = None
    for idx, (ego_x, ego_y) in enumerate(plan_world):
        horizon = (idx + 1) * dt
        ax = wx + vx * horizon
        ay = wy + vy * horizon
        dist = math.hypot(ego_x - ax, ego_y - ay)
        if dist < min_cpa:
            min_cpa = dist
            cpa_horizon_index = idx + 1

    ego_x, ego_y = trans[0], trans[1]
    dx, dy = ego_x - wx, ego_y - wy
    gap = math.hypot(dx, dy)
    closing = None
    ttc = None
    if gap > 1e-3:
        closing_value = (vx * dx + vy * dy) / gap
        if closing_value > max(min_closing, 0.5):
            closing = closing_value
            ttc = gap / closing_value
    cpa_cross = min_cpa < CPA_MARGIN
    ttc_cross = ttc is not None and ttc < TTC_THRESH
    cpa_borderline = not cpa_cross and min_cpa < CPA_BORDERLINE
    ttc_borderline = not ttc_cross and ttc is not None and ttc < TTC_BORDERLINE
    return {
        "score": obj.get("score"),
        "world": [wx, wy],
        "velocity": [vx, vy],
        "min_cpa": min_cpa,
        "cpa_horizon_index": cpa_horizon_index,
        "gap": gap,
        "closing": closing,
        "ttc": ttc,
        "cpa_cross": cpa_cross,
        "ttc_cross": ttc_cross,
        "hazard_cross": cpa_cross or ttc_cross,
        "cpa_borderline": cpa_borderline,
        "ttc_borderline": ttc_borderline,
        "borderline": cpa_borderline or ttc_borderline,
    }


def analyze_temporal_window(proof_root: Path) -> tuple[dict[str, Any], list[str]]:
    problems: list[str] = []
    paths = target_paths(proof_root)
    for label in ("eval", "decisions"):
        path = paths[label]
        if not path.exists() or path.stat().st_size == 0:
            problems.append(f"missing-{label}")
    if problems:
        return {}, problems
    try:
        foreground_ts = first_foreground_timestamp(paths["eval"])
        rows = read_decision_rows(paths["decisions"])
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return {}, [f"parse-failed:{exc}"]

    frames: list[dict[str, Any]] = []
    contact_frames: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        try:
            ts = require_float(row.get("ts", row.get("frame_index")), "row.ts")
        except (TypeError, ValueError):
            problems.append(f"row-{idx}-ts-invalid")
            continue
        bucket = "pre_contact" if ts < foreground_ts - TIME_TOL else "contact" if abs(ts - foreground_ts) <= TIME_TOL else "post_contact"
        if bucket == "post_contact":
            continue
        try:
            metric = object_metric_for_row(row, TARGET_OBJECT_ID)
        except (KeyError, TypeError, ValueError) as exc:
            problems.append(f"row-{idx}-metric-failed:{exc}")
            continue
        record: dict[str, Any] = {
            "frame_index": row.get("frame_index", idx),
            "ts": ts,
            "bucket": bucket,
            "object_present": metric is not None,
            "fired": bool(row.get("fired")),
            "brake": bool(row.get("brake")),
        }
        if metric is not None:
            record.update(metric)
        if bucket == "pre_contact":
            frames.append(record)
        else:
            contact_frames.append(record)
    if problems:
        return {}, problems

    present_frames = [frame for frame in frames if frame["object_present"]]
    hazard_frames = [frame for frame in present_frames if frame.get("hazard_cross")]
    borderline_frames = [frame for frame in present_frames if frame.get("borderline")]
    if hazard_frames:
        label = "pre_contact_hazard_cross"
    elif borderline_frames:
        label = "pre_contact_borderline_only"
    elif len(present_frames) >= 2:
        label = "visible_never_hazard"
    else:
        label = "insufficient_temporal_support"

    return {
        "first_foreground_ts": foreground_ts,
        "row_label": label,
        "pre_contact_frame_count": len(frames),
        "present_frame_count": len(present_frames),
        "absent_frame_count": sum(not frame["object_present"] for frame in frames),
        "hazard_frame_count": len(hazard_frames),
        "borderline_frame_count": len(borderline_frames),
        "first_present_ts": present_frames[0]["ts"] if present_frames else None,
        "last_present_ts": present_frames[-1]["ts"] if present_frames else None,
        "first_hazard_ts": hazard_frames[0]["ts"] if hazard_frames else None,
        "first_borderline_ts": borderline_frames[0]["ts"] if borderline_frames else None,
        "min_cpa": min((frame["min_cpa"] for frame in present_frames), default=None),
        "min_ttc": min((frame["ttc"] for frame in present_frames if frame.get("ttc") is not None), default=None),
        "frames": frames,
        "contact_frames": contact_frames,
    }, []


def choose_verdict(label: str | None, infra_problems: list[str], row_problems: list[str]) -> str:
    if infra_problems or row_problems or label is None:
        return "TEMPORAL_EMERGENCE_INFRA_NULL"
    if label == "pre_contact_hazard_cross":
        return "TEMPORAL_HAZARD_EMERGED_COMPLETE"
    if label == "pre_contact_borderline_only":
        return "TEMPORAL_BORDERLINE_NULL"
    if label == "visible_never_hazard":
        return "TEMPORAL_VISIBLE_NEVER_HAZARD_COMPLETE"
    if label == "insufficient_temporal_support":
        return "TEMPORAL_SUPPORT_NULL"
    return "TEMPORAL_EMERGENCE_INFRA_NULL"


def build_report(
    proof_root: Path,
    iter59_report_path: Path,
    iter61_report_path: Path,
    iter62_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    if not proof_root.exists():
        infra_problems.append(f"missing-proof-root:{proof_root}")
    iter59_report, problems59 = load_report(iter59_report_path, "iter59-report")
    iter61_report, problems61 = load_report(iter61_report_path, "iter61-report")
    iter62_report, problems62 = load_report(iter62_report_path, "iter62-report")
    infra_problems.extend(problems59)
    infra_problems.extend(problems61)
    infra_problems.extend(problems62)
    if not problems59 and not problems61 and not problems62:
        infra_problems.extend(crosscheck_reports(iter59_report, iter61_report, iter62_report))

    temporal: dict[str, Any] = {}
    row_problems: list[str] = []
    if not infra_problems:
        temporal, row_problems = analyze_temporal_window(proof_root)
    verdict = choose_verdict(temporal.get("row_label"), infra_problems, row_problems)
    return {
        "iteration": 63,
        "inputs": {
            "iter59_proof_root": str(proof_root),
            "iter59_report": str(iter59_report_path),
            "iter61_report": str(iter61_report_path),
            "iter62_report": str(iter62_report_path),
        },
        "target": {
            "audit_id": TARGET_AUDIT_ID,
            "scenario": TARGET_SCENARIO,
            "object_id": TARGET_OBJECT_ID,
            "trigger_object_id": TRIGGER_OBJECT_ID,
        },
        "infra_problems": infra_problems,
        "row_problems": row_problems,
        "temporal": temporal,
        "summary": {
            "row_label": temporal.get("row_label"),
            "first_foreground_ts": temporal.get("first_foreground_ts"),
            "pre_contact_frame_count": temporal.get("pre_contact_frame_count"),
            "present_frame_count": temporal.get("present_frame_count"),
            "hazard_frame_count": temporal.get("hazard_frame_count"),
            "borderline_frame_count": temporal.get("borderline_frame_count"),
            "first_hazard_ts": temporal.get("first_hazard_ts"),
            "first_borderline_ts": temporal.get("first_borderline_ts"),
            "min_cpa": temporal.get("min_cpa"),
            "min_ttc": temporal.get("min_ttc"),
        },
        "verdict": verdict,
        "claim_boundary": (
            "one-object temporal hazard-surface audit only; no transfer, safety, deployment, "
            "benchmark, actor-causality, repair, population, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 63 - temporal emergence audit",
        "",
        f"Verdict: `{report['verdict']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in report["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    if report["infra_problems"] or report["row_problems"]:
        lines.extend(["", "## Problems", ""])
        lines.extend(f"- `{problem}`" for problem in report["infra_problems"])
        lines.extend(f"- `{problem}`" for problem in report["row_problems"])
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    proof_root: Path,
    iter59_report: Path,
    iter61_report: Path,
    iter62_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(proof_root, iter59_report, iter61_report, iter62_report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--iter59-proof-root",
        type=Path,
        default=Path("experiments/iter59_hugsim_actor_match_audit/proof-actor-match"),
    )
    parser.add_argument(
        "--iter59-report",
        type=Path,
        default=Path("experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json"),
    )
    parser.add_argument(
        "--iter61-report",
        type=Path,
        default=Path("experiments/iter61_monitor_object_surface_audit/proof-object-surface/object_surface_report.json"),
    )
    parser.add_argument(
        "--iter62-report",
        type=Path,
        default=Path("experiments/iter62_nontrigger_ranking_audit/proof-ranking/nontrigger_ranking_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter63_temporal_emergence_audit/proof-temporal/temporal_emergence_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter63_temporal_emergence_audit/proof-temporal/temporal_emergence.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_proof_root,
        args.iter59_report,
        args.iter61_report,
        args.iter62_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
