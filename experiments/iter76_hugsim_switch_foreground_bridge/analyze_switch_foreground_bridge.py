#!/usr/bin/env python3
"""Iteration 76 HUGSIM switch foreground bridge audit."""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

ITER59_VERDICT = "ACTOR_MATCH_AUDIT_COMPLETE"
ITER70_VERDICT = "HUGSIM_STRUCTURAL_TIMING_TAXONOMY_COMPLETE"
ITER72_VERDICT = "HUGSIM_LATE_FIRE_PREFIRE_MARGIN_COMPLETE"
ITER73_VERDICT = "HUGSIM_MARGIN_TRANSITION_SPLIT_COMPLETE"
ITER74_VERDICT = "HUGSIM_LATE_FIRE_CROSS_CHANNEL_DELAY_COMPLETE"
ITER75_VERDICT = "HUGSIM_CROSS_CHANNEL_OBJECT_SWITCH_COMPLETE"
MATCH_DISTANCE_M = 3.0
AMBIGUOUS_DISTANCE_M = 6.0
TIME_TOL = 1e-9
FIXED_ROWS = (
    ("both_distinct_extreme", "scene-0138-extreme-00"),
    ("ttc_medium_a", "scene-0071-medium-01"),
)


def _load_module(relative_path: str, module_name: str) -> Any:
    repo = Path(__file__).resolve().parents[2]
    module_path = repo / relative_path
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot-load-module:{module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


surface_margin = _load_module(
    "experiments/iter71_hugsim_surface_silent_margin_audit/analyze_surface_silent_margin.py",
    "iter71_surface_silent_margin",
)
ITER59 = _load_module(
    "experiments/iter59_hugsim_actor_match_audit/analyze_actor_match.py",
    "iter59_actor_match",
)


def same_object_id(left: Any, right: Any) -> bool:
    return str(left) == str(right)


def row_identity(row: dict[str, Any]) -> tuple[str, str]:
    return str(row.get("audit_id")), str(row.get("scenario"))


def require_float(value: Any, field: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
        raise ValueError(f"non-numeric:{field}")
    return float(value)


def load_decision_rows(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not path.exists() or path.stat().st_size == 0:
        return [], [f"missing-decision-log:{path}"]
    rows: list[dict[str, Any]] = []
    problems: list[str] = []
    try:
        lines = path.read_text().splitlines()
    except OSError as exc:
        return [], [f"read-decision-log-failed:{path}:{exc}"]
    for line_no, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            problems.append(f"bad-json-line:{line_no}:{exc}")
            continue
        if isinstance(row, dict) and "trace_error" not in row:
            rows.append(row)
    if not rows:
        problems.append("empty-decision-log")
    return rows, problems


def find_decision_row(rows: list[dict[str, Any]], ts: float, label: str, problems: list[str]) -> dict[str, Any] | None:
    matches: list[dict[str, Any]] = []
    for idx, row in enumerate(rows):
        row_ts = surface_margin.number(row.get("ts", row.get("frame_index")), f"{label}.ts:{idx}", problems)
        if row_ts is not None and abs(row_ts - ts) <= TIME_TOL:
            matches.append(row)
    if len(matches) != 1:
        problems.append(f"{label}-row-count-{len(matches)}-for-ts-{ts}")
        return None
    return matches[0]


def select_object(row: dict[str, Any], object_id: Any, label: str, problems: list[str]) -> dict[str, Any] | None:
    objs = row.get("objs")
    if not isinstance(objs, list):
        problems.append(f"{label}-objs-not-list")
        return None
    matches = [obj for obj in objs if isinstance(obj, dict) and same_object_id(obj.get("id"), object_id)]
    if len(matches) != 1:
        problems.append(f"{label}-object-count-{len(matches)}:{object_id}")
        return None
    return matches[0]


def load_foregrounds(eval_path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    if not eval_path.exists() or eval_path.stat().st_size == 0:
        return [], [f"missing-eval:{eval_path}"]
    try:
        doc = json.loads(eval_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return [], [f"read-eval-failed:{eval_path}:{exc}"]
    provenance = doc.get("collision_provenance")
    if not isinstance(provenance, list):
        return [], ["collision-provenance-not-list"]
    rows: list[dict[str, Any]] = []
    for item in provenance:
        if not isinstance(item, dict) or item.get("collision_type") != "foreground":
            continue
        obs_box = item.get("obs_box")
        if not isinstance(obs_box, list) or len(obs_box) < 2:
            continue
        try:
            timestamp = require_float(item.get("timestamp"), "foreground.timestamp")
            require_float(obs_box[0], "foreground.obs_box.x")
            require_float(obs_box[1], "foreground.obs_box.y")
        except ValueError:
            continue
        rows.append(item | {"timestamp": timestamp})
    if not rows:
        return [], ["eligible-foregrounds-missing"]
    return sorted(rows, key=lambda row: float(row["timestamp"])), []


def bridge_variants(
    event_row: dict[str, Any],
    event_ts: float,
    obj: dict[str, Any],
    object_role: str,
    foreground: dict[str, Any],
) -> list[dict[str, Any]]:
    r_mat = ITER59.matrix3(event_row.get("l2g_r_mat"), "event.l2g_r_mat")
    trans_raw = event_row.get("l2g_t")
    if not isinstance(trans_raw, list) or len(trans_raw) < 2:
        raise ValueError("event.l2g_t-not-vec2")
    trans = [require_float(value, "event.l2g_t") for value in trans_raw]
    wx, wy = ITER59.vec2(obj.get("world"), "obj.world")
    vx, vy = ITER59.vec2(obj.get("vel"), "obj.vel")
    fg_ts = require_float(foreground.get("timestamp"), "foreground.timestamp")
    obs_box = foreground.get("obs_box")
    if not isinstance(obs_box, list) or len(obs_box) < 2:
        raise ValueError("foreground.obs_box-not-vec2")
    obs_forward = require_float(obs_box[0], "foreground.obs_box.x")
    obs_lateral = require_float(obs_box[1], "foreground.obs_box.y")
    lead = max(0.0, fg_ts - event_ts)

    variants: list[dict[str, Any]] = []
    for temporal_source, (px, py) in (
        ("event_row", (wx, wy)),
        ("propagated_to_foreground", (wx + vx * lead, wy + vy * lead)),
    ):
        local_x, local_y = ITER59.world_to_monitor_local(px, py, r_mat, trans)
        for axis_order, (base_forward, base_lateral) in (
            ("yx", (local_y, local_x)),
            ("xy", (local_x, local_y)),
        ):
            for forward_sign in (-1, 1):
                for lateral_sign in (-1, 1):
                    monitor_forward = forward_sign * base_forward
                    monitor_lateral = lateral_sign * base_lateral
                    distance = math.hypot(monitor_forward - obs_forward, monitor_lateral - obs_lateral)
                    variants.append({
                        "object_id": obj.get("id"),
                        "object_role": object_role,
                        "event_ts": event_ts,
                        "foreground_timestamp": fg_ts,
                        "foreground_obs_index": foreground.get("obs_index"),
                        "foreground_obs_name": foreground.get("obs_name"),
                        "temporal_source": temporal_source,
                        "axis_order": axis_order,
                        "forward_sign": forward_sign,
                        "lateral_sign": lateral_sign,
                        "monitor_forward_lateral": [monitor_forward, monitor_lateral],
                        "hugsim_forward_lateral": [obs_forward, obs_lateral],
                        "lead_time_s": lead,
                        "distance_m": distance,
                    })
    return variants


def best_variant(variants: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not variants:
        return None
    return min(
        variants,
        key=lambda item: (
            item["distance_m"],
            str(item["object_id"]),
            item["foreground_timestamp"],
            item["temporal_source"],
            item["axis_order"],
            item["forward_sign"],
            item["lateral_sign"],
        ),
    )


def distance_band(distance: float | None) -> str:
    if distance is None:
        return "missing"
    if distance <= MATCH_DISTANCE_M:
        return "match"
    if distance <= AMBIGUOUS_DISTANCE_M:
        return "ambiguous"
    return "no_support"


def compact_variant(variant: dict[str, Any] | None) -> dict[str, Any] | None:
    if variant is None:
        return None
    fields = (
        "object_id",
        "object_role",
        "event_ts",
        "foreground_timestamp",
        "foreground_obs_index",
        "foreground_obs_name",
        "temporal_source",
        "axis_order",
        "forward_sign",
        "lateral_sign",
        "monitor_forward_lateral",
        "hugsim_forward_lateral",
        "lead_time_s",
        "distance_m",
    )
    return {field: variant[field] for field in fields}


def crosscheck_sources(
    iter59_report: dict[str, Any],
    iter70_report: dict[str, Any],
    iter72_report: dict[str, Any],
    iter73_report: dict[str, Any],
    iter74_report: dict[str, Any],
    iter75_report: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    problems: list[str] = []
    expected_verdicts = {
        "iter59": (iter59_report, ITER59_VERDICT),
        "iter70": (iter70_report, ITER70_VERDICT),
        "iter72": (iter72_report, ITER72_VERDICT),
        "iter73": (iter73_report, ITER73_VERDICT),
        "iter74": (iter74_report, ITER74_VERDICT),
        "iter75": (iter75_report, ITER75_VERDICT),
    }
    for label, (report, verdict) in expected_verdicts.items():
        if report.get("verdict") != verdict:
            problems.append(f"{label}-verdict-not-{verdict}")
        if report.get("infra_problems"):
            problems.append(f"{label}-infra-problems:{report.get('infra_problems')}")

    iter59_index = surface_margin.index_rows(iter59_report.get("episodes"), "iter59", problems)
    iter70_index = surface_margin.index_rows(iter70_report.get("episodes"), "iter70", problems)
    iter72_index = surface_margin.index_rows(iter72_report.get("episodes"), "iter72", problems)
    iter73_index = surface_margin.index_rows(iter73_report.get("episodes"), "iter73", problems)
    iter74_index = surface_margin.index_rows(iter74_report.get("episodes"), "iter74", problems)
    iter75_index = surface_margin.index_rows(iter75_report.get("episodes"), "iter75", problems)

    selected: list[dict[str, Any]] = []
    for key in FIXED_ROWS:
        row59 = iter59_index.get(key)
        row70 = iter70_index.get(key)
        row72 = iter72_index.get(key)
        row73 = iter73_index.get(key)
        row74 = iter74_index.get(key)
        row75 = iter75_index.get(key)
        if row59 is None:
            problems.append(f"missing-iter59-row:{key}")
            continue
        if row70 is None or row70.get("structural_label") != "foreground_present_late_fire":
            problems.append(f"iter70-late-fire-missing:{key}")
        if row72 is None or row72.get("row_label") not in {
            "late_fire_prefire_near_ttc_margin",
            "late_fire_prefire_near_cpa_margin",
        }:
            problems.append(f"iter72-near-row-missing:{key}")
        if row73 is None or row73.get("row_label") != "late_prefire_near_postcontact_active":
            problems.append(f"iter73-late-transition-missing:{key}")
        if row74 is None or row74.get("row_label") != "cross_channel_late_activation":
            problems.append(f"iter74-cross-channel-row-missing:{key}")
        if row75 is None or row75.get("row_label") != "object_switch_cross_channel_handoff":
            problems.append(f"iter75-object-switch-row-missing:{key}")
            continue
        selected.append({"iter59": row59, "iter75": row75})

    actual = [row_identity(item["iter59"]) for item in selected]
    if actual != list(FIXED_ROWS):
        problems.append(f"fixed-row-order-mismatch:{actual}")
    return selected, problems


def classify(pre_band: str, active_band: str, problems: list[str]) -> str:
    if problems or pre_band == "missing" or active_band == "missing":
        return "switch_foreground_bridge_insufficient"
    if pre_band == "match" and active_band == "match":
        return "both_objects_foreground_match"
    if active_band == "match":
        return "active_object_foreground_match"
    if pre_band == "match":
        return "pre_object_foreground_match"
    if pre_band == "ambiguous" and active_band == "ambiguous":
        return "both_objects_foreground_ambiguous"
    if active_band == "ambiguous" and pre_band == "no_support":
        return "active_object_foreground_ambiguous"
    if pre_band == "ambiguous" and active_band == "no_support":
        return "pre_object_foreground_ambiguous"
    if pre_band == "no_support" and active_band == "no_support":
        return "no_foreground_bridge_support"
    return "switch_foreground_bridge_insufficient"


def analyze_event(
    row: dict[str, Any],
    event_ts: float,
    object_id: Any,
    role: str,
    foregrounds: list[dict[str, Any]],
    problems: list[str],
) -> dict[str, Any]:
    obj = select_object(row, object_id, role, problems)
    if obj is None:
        return {"object_id": object_id, "event_ts": event_ts, "role": role, "best_variant": None, "distance_band": "missing"}
    variants: list[dict[str, Any]] = []
    try:
        for foreground in foregrounds:
            variants.extend(bridge_variants(row, event_ts, obj, role, foreground))
    except (KeyError, TypeError, ValueError) as exc:
        problems.append(f"{role}-bridge-failed:{exc}")
    best = best_variant(variants)
    distance = best["distance_m"] if best is not None else None
    return {
        "object_id": object_id,
        "event_ts": event_ts,
        "role": role,
        "evaluated_variant_count": len(variants),
        "best_variant": compact_variant(best),
        "best_distance_m": distance,
        "distance_band": distance_band(distance),
    }


def analyze_row(item: dict[str, Any]) -> dict[str, Any]:
    row59 = item["iter59"]
    row75 = item["iter75"]
    problems: list[str] = []
    episode_dir = row59.get("episode_dir")
    if not isinstance(episode_dir, str) or not episode_dir:
        problems.append("episode-dir-missing")
        rows: list[dict[str, Any]] = []
        foregrounds: list[dict[str, Any]] = []
    else:
        ep_dir = Path(episode_dir)
        rows, row_problems = load_decision_rows(ep_dir / "sentinel_iter48_decisions.jsonl")
        foregrounds, foreground_problems = load_foregrounds(ep_dir / "eval.json")
        problems.extend(row_problems + foreground_problems)

    pre_objects = row75.get("pre_objects")
    active_objects = row75.get("active_objects")
    pre_ts = surface_margin.number(row75.get("pre_ts"), "pre_ts", problems)
    active_ts = surface_margin.number(row75.get("active_ts"), "active_ts", problems)
    if not isinstance(pre_objects, dict) or not isinstance(pre_objects.get("object_ids"), list):
        problems.append("pre-objects-missing")
        pre_object_id = None
    elif len(pre_objects["object_ids"]) != 1:
        problems.append(f"pre-object-count:{pre_objects.get('object_ids')}")
        pre_object_id = None
    else:
        pre_object_id = pre_objects["object_ids"][0]
    if not isinstance(active_objects, dict) or not isinstance(active_objects.get("object_ids"), list):
        problems.append("active-objects-missing")
        active_object_id = None
    elif len(active_objects["object_ids"]) != 1:
        problems.append(f"active-object-count:{active_objects.get('object_ids')}")
        active_object_id = None
    else:
        active_object_id = active_objects["object_ids"][0]

    pre_row = find_decision_row(rows, pre_ts, "pre", problems) if pre_ts is not None else None
    active_row = find_decision_row(rows, active_ts, "active", problems) if active_ts is not None else None
    pre_event: dict[str, Any] = {}
    active_event: dict[str, Any] = {}
    if pre_row is not None and pre_ts is not None and pre_object_id is not None:
        pre_event = analyze_event(pre_row, pre_ts, pre_object_id, "pre", foregrounds, problems)
    if active_row is not None and active_ts is not None and active_object_id is not None:
        active_event = analyze_event(active_row, active_ts, active_object_id, "active", foregrounds, problems)
    pre_band = pre_event.get("distance_band", "missing")
    active_band = active_event.get("distance_band", "missing")
    row_label = classify(str(pre_band), str(active_band), problems)
    pre_distance = pre_event.get("best_distance_m")
    active_distance = active_event.get("best_distance_m")
    distance_delta = None
    if isinstance(pre_distance, (int, float)) and isinstance(active_distance, (int, float)):
        distance_delta = float(active_distance) - float(pre_distance)
    return {
        "audit_id": row59.get("audit_id"),
        "scenario": row59.get("scenario"),
        "foreground_count": len(foregrounds),
        "pre_event": pre_event,
        "active_event": active_event,
        "active_minus_pre_distance_m": distance_delta,
        "row_label": row_label,
        "problems": problems,
    }


def choose_verdict(rows: list[dict[str, Any]], infra_problems: list[str]) -> str:
    labels = [row.get("row_label") for row in rows]
    if (
        infra_problems
        or len(rows) != len(FIXED_ROWS)
        or any(row.get("problems") for row in rows)
        or "switch_foreground_bridge_insufficient" in labels
    ):
        return "HUGSIM_SWITCH_FOREGROUND_BRIDGE_BLOCKED"
    if "active_object_foreground_match" in labels:
        return "HUGSIM_SWITCH_FOREGROUND_ACTIVE_MATCH_COMPLETE"
    if "pre_object_foreground_match" in labels:
        return "HUGSIM_SWITCH_FOREGROUND_PRE_MATCH_COMPLETE"
    return "HUGSIM_SWITCH_FOREGROUND_BOTH_OR_AMBIGUOUS_COMPLETE"


def build_report(
    iter59_report_path: Path,
    iter70_report_path: Path,
    iter72_report_path: Path,
    iter73_report_path: Path,
    iter74_report_path: Path,
    iter75_report_path: Path,
) -> dict[str, Any]:
    infra_problems: list[str] = []
    iter59_report, problems59 = surface_margin.load_report(iter59_report_path, "iter59-report")
    iter70_report, problems70 = surface_margin.load_report(iter70_report_path, "iter70-report")
    iter72_report, problems72 = surface_margin.load_report(iter72_report_path, "iter72-report")
    iter73_report, problems73 = surface_margin.load_report(iter73_report_path, "iter73-report")
    iter74_report, problems74 = surface_margin.load_report(iter74_report_path, "iter74-report")
    iter75_report, problems75 = surface_margin.load_report(iter75_report_path, "iter75-report")
    infra_problems.extend(problems59 + problems70 + problems72 + problems73 + problems74 + problems75)

    selected: list[dict[str, Any]] = []
    if not infra_problems:
        selected, source_problems = crosscheck_sources(
            iter59_report,
            iter70_report,
            iter72_report,
            iter73_report,
            iter74_report,
            iter75_report,
        )
        infra_problems.extend(source_problems)
    rows = [] if infra_problems else [analyze_row(item) for item in selected]
    label_counts = Counter(row.get("row_label") for row in rows)
    return {
        "iteration": 76,
        "inputs": {
            "iter59_report": str(iter59_report_path),
            "iter70_report": str(iter70_report_path),
            "iter72_report": str(iter72_report_path),
            "iter73_report": str(iter73_report_path),
            "iter74_report": str(iter74_report_path),
            "iter75_report": str(iter75_report_path),
        },
        "fixed_rows": [{"audit_id": audit_id, "scenario": scenario} for audit_id, scenario in FIXED_ROWS],
        "infra_problems": infra_problems,
        "episodes": rows,
        "summary": {
            "target_rows": len(selected),
            "evaluated_rows": sum(not row.get("problems") for row in rows),
            "row_label_counts": dict(sorted(label_counts.items())),
            "active_object_match_rows": sum(row.get("row_label") == "active_object_foreground_match" for row in rows),
            "pre_object_match_rows": sum(row.get("row_label") == "pre_object_foreground_match" for row in rows),
            "no_support_rows": sum(row.get("row_label") == "no_foreground_bridge_support" for row in rows),
        },
        "verdict": choose_verdict(rows, infra_problems),
        "claim_boundary": (
            "two-row descriptive foreground-bridge audit only; no actor-causality, repair, "
            "threshold-value, transfer, safety, deployment, robustness, benchmark, population, "
            "HD-Score-invariance, commercial-value, or retuning claim"
        ),
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Iteration 76 - HUGSIM switch foreground bridge audit",
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
        "## Rows",
        "",
        "| audit id | scenario | label | pre id | pre distance | active id | active distance | delta active-pre | problems |",
        "|---|---|---|---:|---:|---:|---:|---:|---|",
    ])
    for row in report["episodes"]:
        pre = row.get("pre_event", {})
        active = row.get("active_event", {})
        lines.append(
            f"| `{row['audit_id']}` | `{row['scenario']}` | `{row['row_label']}` | "
            f"`{pre.get('object_id')}` | `{pre.get('best_distance_m')}` | "
            f"`{active.get('object_id')}` | `{active.get('best_distance_m')}` | "
            f"`{row.get('active_minus_pre_distance_m')}` | `{row.get('problems')}` |"
        )
    lines.extend(["", "## Boundary", "", report["claim_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


def run_analysis(
    iter59_report: Path,
    iter70_report: Path,
    iter72_report: Path,
    iter73_report: Path,
    iter74_report: Path,
    iter75_report: Path,
    out: Path,
    markdown_out: Path,
) -> dict[str, Any]:
    report = build_report(iter59_report, iter70_report, iter72_report, iter73_report, iter74_report, iter75_report)
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
        "--iter70-report",
        type=Path,
        default=Path("experiments/iter70_hugsim_structural_timing_audit/proof-structural/structural_report.json"),
    )
    parser.add_argument(
        "--iter72-report",
        type=Path,
        default=Path("experiments/iter72_hugsim_late_fire_prefire_margin_audit/proof-prefire/prefire_report.json"),
    )
    parser.add_argument(
        "--iter73-report",
        type=Path,
        default=Path("experiments/iter73_hugsim_margin_transition_audit/proof-transition/transition_report.json"),
    )
    parser.add_argument(
        "--iter74-report",
        type=Path,
        default=Path("experiments/iter74_hugsim_late_fire_delay_barrier/proof-delay/delay_report.json"),
    )
    parser.add_argument(
        "--iter75-report",
        type=Path,
        default=Path("experiments/iter75_hugsim_cross_channel_object_handoff/proof-handoff/handoff_report.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("experiments/iter76_hugsim_switch_foreground_bridge/proof-bridge/bridge_report.json"),
    )
    parser.add_argument(
        "--markdown-out",
        type=Path,
        default=Path("experiments/iter76_hugsim_switch_foreground_bridge/proof-bridge/bridge.md"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_analysis(
        args.iter59_report,
        args.iter70_report,
        args.iter72_report,
        args.iter73_report,
        args.iter74_report,
        args.iter75_report,
        args.out,
        args.markdown_out,
    )
    print(json.dumps({"verdict": report["verdict"], "summary": report["summary"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
