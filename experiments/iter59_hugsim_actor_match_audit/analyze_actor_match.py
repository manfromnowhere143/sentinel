#!/usr/bin/env python3
"""Iteration 59 HUGSIM actor-match support audit analyzer."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

SCALAR_TOP_LEVEL = ("nc", "dac", "ttc", "c", "pdms", "rc", "hdscore")
DETAIL_KEYS = {"nc", "dac", "ttc", "c", "pdms"}
TTC_THRESH = 2.5
CPA_MARGIN = 1.5
MATCH_TOL = 1e-6
MATCH_DISTANCE_M = 3.0
MISMATCH_DISTANCE_M = 6.0

SCHEDULE = (
    ("ttc_extreme_short", "scene-0038-extreme-00"),
    ("mixed_extreme", "scene-0062-extreme-00"),
    ("both_distinct_extreme", "scene-0138-extreme-00"),
    ("nofire_hard_control", "scene-0041-hard-00"),
    ("cpa_medium_a", "scene-0071-medium-00"),
    ("ttc_medium_a", "scene-0071-medium-01"),
    ("cpa_medium_b", "scene-0166-medium-00"),
    ("ttc_extreme_b", "scene-0383-extreme-00"),
)


def numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def require_float(value: Any, field: str) -> float:
    if not numeric(value):
        raise ValueError(f"non-numeric:{field}")
    return float(value)


def close(a: float, b: float) -> bool:
    return abs(a - b) <= MATCH_TOL * max(1.0, abs(a), abs(b))


def matrix3(value: Any, field: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{field}-not-3x3")
    rows = []
    for row in value:
        if not isinstance(row, list) or len(row) != 3:
            raise ValueError(f"{field}-not-3x3")
        rows.append([require_float(v, field) for v in row])
    return rows


def vec2(value: Any, field: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) < 2:
        raise ValueError(f"{field}-not-vec2")
    return require_float(value[0], field), require_float(value[1], field)


def transform_xy(x: float, y: float, r_mat: list[list[float]], trans: list[float]) -> tuple[float, float]:
    return (
        r_mat[0][0] * x + r_mat[0][1] * y + trans[0],
        r_mat[1][0] * x + r_mat[1][1] * y + trans[1],
    )


def world_to_monitor_local(
    x: float,
    y: float,
    r_mat: list[list[float]],
    trans: list[float],
) -> tuple[float, float]:
    dx = x - trans[0]
    dy = y - trans[1]
    return (
        r_mat[0][0] * dx + r_mat[1][0] * dy,
        r_mat[0][1] * dx + r_mat[1][1] * dy,
    )


def details_are_scalar_only(eval_doc: dict[str, Any]) -> tuple[bool, list[str]]:
    details = eval_doc.get("details")
    if not isinstance(details, dict):
        return False, ["details-not-dict"]
    problems: list[str] = []
    for ts, row in details.items():
        if not isinstance(row, dict):
            problems.append(f"details-row-not-dict:{ts}")
            continue
        extra = sorted(set(row) - DETAIL_KEYS)
        missing = sorted(DETAIL_KEYS - set(row))
        if extra:
            problems.append(f"details-extra-keys:{ts}:{','.join(extra)}")
        if missing:
            problems.append(f"details-missing-keys:{ts}:{','.join(missing)}")
        for key in DETAIL_KEYS & set(row):
            if not numeric(row[key]):
                problems.append(f"details-nonnumeric:{ts}:{key}")
    return not problems, problems


def nc_min(eval_doc: dict[str, Any]) -> float:
    values = [require_float(eval_doc["nc"], "nc")]
    details = eval_doc.get("details", {})
    if isinstance(details, dict):
        for row in details.values():
            if isinstance(row, dict) and numeric(row.get("nc")):
                values.append(float(row["nc"]))
    return min(values)


def first_foreground(provenance: list[Any]) -> dict[str, Any] | None:
    rows = [
        row for row in provenance
        if isinstance(row, dict)
        and row.get("collision_type") == "foreground"
        and numeric(row.get("timestamp"))
        and isinstance(row.get("obs_box"), list)
        and len(row["obs_box"]) >= 2
        and numeric(row["obs_box"][0])
        and numeric(row["obs_box"][1])
    ]
    return min(rows, key=lambda row: float(row["timestamp"])) if rows else None


def read_eval(path: Path) -> dict[str, Any]:
    ev = json.loads(path.read_text())
    scalar_metrics_present = all(key in ev and numeric(ev[key]) for key in SCALAR_TOP_LEVEL)
    scalar_only, detail_problems = details_are_scalar_only(ev)
    provenance = ev.get("collision_provenance")
    provenance_is_list = isinstance(provenance, list)
    fg = first_foreground(provenance if isinstance(provenance, list) else [])
    return {
        "scalar_metrics_present": scalar_metrics_present,
        "details_scalar_only": scalar_only,
        "detail_problems": detail_problems,
        "nc_min": nc_min(ev) if scalar_metrics_present else None,
        "provenance_present": "collision_provenance" in ev,
        "provenance_is_list": provenance_is_list,
        "provenance_count": len(provenance) if isinstance(provenance, list) else 0,
        "foreground_count": sum(
            isinstance(row, dict) and row.get("collision_type") == "foreground"
            for row in provenance
        )
        if isinstance(provenance, list)
        else 0,
        "first_foreground": fg,
    }


def first_fire_channel(row: dict[str, Any]) -> str:
    ttc = require_float(row.get("min_ttc"), "min_ttc")
    cpa = require_float(row.get("min_cpa"), "min_cpa")
    ttc_cross = ttc < TTC_THRESH
    cpa_cross = cpa < CPA_MARGIN
    if ttc_cross and cpa_cross:
        return "both"
    if ttc_cross:
        return "ttc_only"
    if cpa_cross:
        return "cpa_only"
    return "fired_channel_unreconstructable"


def reconstruct_argmins(row: dict[str, Any]) -> dict[str, Any]:
    r_mat = matrix3(row.get("l2g_r_mat"), "l2g_r_mat")
    trans_raw = row.get("l2g_t")
    if not isinstance(trans_raw, list) or len(trans_raw) < 2:
        raise ValueError("l2g_t-not-vec2")
    trans = [require_float(v, "l2g_t") for v in trans_raw]
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
        px, py = vec2(point, "traj")
        plan_world.append(transform_xy(px, py, r_mat, trans))
    objs = row.get("objs")
    if not isinstance(objs, list):
        raise ValueError("objs-not-list")

    cpa_candidates = []
    ttc_candidates = []
    objects_by_id = {}
    for obj in objs:
        if not isinstance(obj, dict):
            raise ValueError("obj-not-dict")
        oid = obj.get("id")
        objects_by_id[oid] = obj
        wx, wy = vec2(obj.get("world"), "obj.world")
        vx, vy = vec2(obj.get("vel"), "obj.vel")
        obj_min_cpa = math.inf
        obj_horizon = None
        for idx, (ex, ey) in enumerate(plan_world):
            horizon = (idx + 1) * dt
            ax = wx + vx * horizon
            ay = wy + vy * horizon
            dist = math.hypot(ex - ax, ey - ay)
            if dist < obj_min_cpa:
                obj_min_cpa = dist
                obj_horizon = idx + 1
        cpa_candidates.append({"id": oid, "value": obj_min_cpa, "horizon_index": obj_horizon})

        ego_x, ego_y = trans[0], trans[1]
        dx, dy = ego_x - wx, ego_y - wy
        gap = math.hypot(dx, dy)
        if gap > 1e-3:
            closing = (vx * dx + vy * dy) / gap
            if closing > max(min_closing, 0.5):
                ttc_candidates.append({
                    "id": oid,
                    "value": gap / closing,
                    "gap": gap,
                    "closing": closing,
                })

    logged_cpa = require_float(row.get("min_cpa"), "min_cpa")
    logged_ttc = require_float(row.get("min_ttc"), "min_ttc")
    return {
        "cpa_argmins": [item for item in cpa_candidates if close(item["value"], logged_cpa)],
        "ttc_argmins": [item for item in ttc_candidates if close(item["value"], logged_ttc)],
        "objects_by_id": objects_by_id,
        "r_mat": r_mat,
        "trans": trans,
    }


def choose_monitor_object(channel: str, argmins: dict[str, Any]) -> tuple[str, Any | None]:
    cpa_ids = [item["id"] for item in argmins["cpa_argmins"]]
    ttc_ids = [item["id"] for item in argmins["ttc_argmins"]]
    if channel == "cpa_only" and len(cpa_ids) == 1:
        return "unique_cpa_object", cpa_ids[0]
    if channel == "ttc_only" and len(ttc_ids) == 1:
        return "unique_ttc_object", ttc_ids[0]
    if channel == "both" and len(cpa_ids) == 1 and len(ttc_ids) == 1 and cpa_ids[0] == ttc_ids[0]:
        return "unique_both_same_object", cpa_ids[0]
    if channel == "both" and len(cpa_ids) == 1 and len(ttc_ids) == 1:
        return "both_distinct_objects", None
    if channel == "cpa_only" and len(cpa_ids) > 1:
        return "ambiguous_cpa_object", None
    if channel == "ttc_only" and len(ttc_ids) > 1:
        return "ambiguous_ttc_object", None
    return "argmin_reconstruction_failed", None


def read_decisions(path: Path) -> dict[str, Any]:
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    rows = [row for row in rows if "trace_error" not in row]
    first_fire = next((row for row in rows if bool(row.get("fired"))), None)
    result: dict[str, Any] = {
        "monitor_frames": len(rows),
        "fired_frames": sum(bool(row.get("fired")) for row in rows),
        "brake_frames": sum(bool(row.get("brake")) for row in rows),
    }
    if first_fire is None:
        result.update({
            "first_fire_ts": None,
            "first_fire_channel": "no_fire",
            "monitor_provenance_label": "no_fire",
            "monitor_object_id": None,
            "first_fire_row": None,
        })
        return result
    channel = first_fire_channel(first_fire)
    try:
        argmins = reconstruct_argmins(first_fire)
        provenance_label, object_id = choose_monitor_object(channel, argmins)
    except (KeyError, TypeError, ValueError):
        argmins = {"objects_by_id": {}, "r_mat": None, "trans": None}
        provenance_label, object_id = "schema_unsupported", None
    result.update({
        "first_fire_ts": require_float(
            first_fire.get("ts", first_fire.get("frame_index", 0)),
            "first_fire_ts",
        ),
        "first_fire_channel": channel,
        "monitor_provenance_label": provenance_label,
        "monitor_object_id": object_id,
        "first_fire_row": first_fire,
        "argmins": argmins,
    })
    return result


def bridge_distance(decisions: dict[str, Any], foreground: dict[str, Any]) -> dict[str, Any]:
    object_id = decisions.get("monitor_object_id")
    if object_id is None:
        raise ValueError("monitor-object-not-unique")
    argmins = decisions["argmins"]
    obj = argmins["objects_by_id"].get(object_id)
    if not isinstance(obj, dict):
        raise ValueError("monitor-object-missing")
    wx, wy = vec2(obj.get("world"), "obj.world")
    vx, vy = vec2(obj.get("vel"), "obj.vel")
    fire_ts = require_float(decisions["first_fire_ts"], "first_fire_ts")
    fg_ts = require_float(foreground["timestamp"], "foreground.timestamp")
    lead = max(0.0, fg_ts - fire_ts)
    pred_x = wx + vx * lead
    pred_y = wy + vy * lead
    local_x, local_y = world_to_monitor_local(pred_x, pred_y, argmins["r_mat"], argmins["trans"])
    monitor_forward = local_y
    monitor_lateral = local_x
    obs_forward = require_float(foreground["obs_box"][0], "obs_box.x")
    obs_lateral = require_float(foreground["obs_box"][1], "obs_box.y")
    distance = math.hypot(monitor_forward - obs_forward, monitor_lateral - obs_lateral)
    if distance <= MATCH_DISTANCE_M:
        actor_label = "actor_match"
    elif distance > MISMATCH_DISTANCE_M:
        actor_label = "actor_mismatch"
    else:
        actor_label = "actor_ambiguous"
    return {
        "bridge_distance_m": distance,
        "bridge_label": actor_label,
        "monitor_forward_lateral": [monitor_forward, monitor_lateral],
        "hugsim_forward_lateral": [obs_forward, obs_lateral],
        "lead_time_s": lead,
    }


def classify_episode(ep_dir: Path, audit_id: str, scenario: str) -> dict[str, Any]:
    row: dict[str, Any] = {
        "audit_id": audit_id,
        "scenario": scenario,
        "episode_dir": str(ep_dir),
        "problems": [],
    }
    eval_path = ep_dir / "eval.json"
    decisions_path = ep_dir / "sentinel_iter48_decisions.jsonl"
    meta_path = ep_dir / "episode_meta.json"
    output_path = ep_dir / "output.txt"
    for name, path in (
        ("eval", eval_path),
        ("decisions", decisions_path),
        ("meta", meta_path),
        ("output", output_path),
    ):
        if not path.exists() or path.stat().st_size == 0:
            row["problems"].append(f"missing-{name}")
    if row["problems"]:
        row["support_label"] = "missing_artifact"
        return row
    try:
        ev = read_eval(eval_path)
        decisions = read_decisions(decisions_path)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        row["problems"].append(f"parse-failed:{exc}")
        row["support_label"] = "parse_failed"
        return row

    row.update({
        key: value
        for key, value in ev.items()
        if key != "first_foreground"
    })
    row.update({
        key: value
        for key, value in decisions.items()
        if key not in {"first_fire_row", "argmins"}
    })
    fg = ev["first_foreground"]
    row["first_foreground_ts"] = fg.get("timestamp") if isinstance(fg, dict) else None
    row["first_foreground_obs_name"] = fg.get("obs_name") if isinstance(fg, dict) else None
    row["first_foreground_obs_index"] = fg.get("obs_index") if isinstance(fg, dict) else None

    if not ev["scalar_metrics_present"]:
        row["problems"].append("scalar-metrics-missing-or-nonnumeric")
    if not ev["details_scalar_only"]:
        row["problems"].extend(ev["detail_problems"])
    if decisions["monitor_frames"] == 0:
        row["problems"].append("empty-decision-log")

    if decisions["first_fire_channel"] == "no_fire":
        row["support_label"] = "no_monitor_fire"
    elif not ev["provenance_is_list"] or ev["provenance_count"] == 0:
        row["support_label"] = "no_collision_provenance"
    elif fg is None:
        row["support_label"] = "background_collision_only"
    elif decisions["first_fire_ts"] > float(fg["timestamp"]):
        row["support_label"] = "post_collision_fire"
    elif decisions["monitor_object_id"] is None:
        row["support_label"] = "monitor_argmin_not_unique"
    else:
        try:
            bridge = bridge_distance(decisions, fg)
            row.update(bridge)
            row["support_label"] = "classifiable_foreground"
        except (KeyError, TypeError, ValueError) as exc:
            row["support_label"] = "frame_bridge_failed"
            row["problems"].append(f"frame-bridge-failed:{exc}")
    return row


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    if infra_problems or any(row["problems"] for row in rows):
        return "ACTOR_MATCH_INFRA_NULL"
    classifiable = [row for row in rows if row["support_label"] == "classifiable_foreground"]
    if len(classifiable) < 3:
        return "ACTOR_MATCH_SUPPORT_NULL"
    return "ACTOR_MATCH_AUDIT_COMPLETE"


def build_report(root: Path) -> dict[str, Any]:
    infra_problems: list[str] = []
    if not (root / "receipts.json").exists():
        infra_problems.append("missing-receipts")
        receipts: dict[str, Any] = {}
    else:
        receipts = json.loads((root / "receipts.json").read_text())
    rows = [
        classify_episode(root / "episodes" / f"{audit_id}__{scenario}__on", audit_id, scenario)
        for audit_id, scenario in SCHEDULE
    ]
    support_counts = Counter(row.get("support_label") for row in rows)
    bridge_counts = Counter(
        row.get("bridge_label")
        for row in rows
        if row.get("support_label") == "classifiable_foreground"
    )
    verdict = choose_verdict(rows, infra_problems)
    return {
        "iteration": 59,
        "expected_schedule": [
            {"audit_id": audit_id, "scenario": scenario}
            for audit_id, scenario in SCHEDULE
        ],
        "receipts": receipts,
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "completed_rows": sum(not row["problems"] for row in rows),
            "classifiable_foreground": support_counts.get("classifiable_foreground", 0),
            "support_counts": dict(sorted(support_counts.items())),
            "bridge_counts": dict(sorted(bridge_counts.items())),
        },
        "verdict": verdict,
        "claim_boundary": (
            "bounded eight-episode actor-match support audit only; no transfer, safety, "
            "benchmark, HD-Score-invariance, all-HUGSIM, deployment, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 59 - HUGSIM actor-match support audit",
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
    lines.extend(["", "## Episodes", ""])
    for row in report["episodes"]:
        lines.append(
            f"- `{row['audit_id']}` / `{row['scenario']}`: support "
            f"`{row.get('support_label')}`, bridge `{row.get('bridge_label')}`, "
            f"distance `{row.get('bridge_distance_m')}`, problems `{row['problems']}`"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(root: Path, out: Path, markdown_out: Path) -> dict[str, Any]:
    report = build_report(root)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    write_markdown(report, markdown_out)
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--proof-root", type=Path, required=True)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter59_hugsim_actor_match_audit/proof-actor-match/actor_match.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(args.proof_root, args.out, args.markdown_out)
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
