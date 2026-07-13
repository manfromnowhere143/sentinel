#!/usr/bin/env python3
"""Iteration 54 HUGSIM provenance support audit.

Offline support audit over committed iteration-48/49 HUGSIM proof artifacts.
Reconstructs monitor-side first-fire argmin provenance where possible, then checks whether
HUGSIM eval artifacts log collision actor identity well enough for a later actor-match audit.
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PRIMARY_NC_BAR = 1.0
TTC_THRESH = 2.5
CPA_MARGIN = 1.5
EXPECTED_PAIRS_PER_DATASET = 52
MATCH_TOL = 1e-6

CHANNELS = (
    "ttc_only",
    "cpa_only",
    "both",
    "no_fire",
    "fired_channel_unreconstructable",
)
MONITOR_PROVENANCE_LABELS = (
    "no_fire",
    "unique_cpa_object",
    "unique_ttc_object",
    "unique_both_same_object",
    "both_distinct_objects",
    "ambiguous_cpa_object",
    "ambiguous_ttc_object",
    "argmin_reconstruction_failed",
    "schema_unsupported",
)
COLLISION_SUPPORT_LABELS = (
    "collision_actor_supported",
    "collision_actor_not_logged",
)
FIRE_TIMING_LABELS = (
    "no_on_collision",
    "unknown_collision_time",
    "no_fire",
    "post_collision_fire",
    "short_lead_fire",
    "long_lead_fire",
)
PAIR_RE = re.compile(r"^(?P<scenario>.+)__on_r(?P<run>[12])$")
TIER_RE = re.compile(r"-(easy|medium|hard|extreme)-")
ATTACKPLANNER_HARD_SCENARIOS = {"scene-0041-hard-00", "scene-0411-hard-00"}
IDENTITY_KEY_RE = re.compile(
    r"(actor|agent|object|track|token|instance|collision)", re.IGNORECASE,
)


def _numeric(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"non-numeric {field}")
    return float(value)


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= MATCH_TOL * max(1.0, abs(a), abs(b))


def _details_items(ev: dict) -> list[tuple[float, dict]]:
    details = ev.get("details", {})
    if not isinstance(details, dict):
        raise ValueError("details-not-dict")
    out: list[tuple[float, dict]] = []
    for key, row in details.items():
        try:
            t = float(key)
        except ValueError as exc:
            raise ValueError(f"bad-details-time:{key}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"details-row-not-dict:{key}")
        out.append((t, row))
    return sorted(out, key=lambda item: item[0])


def _identity_fields(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if IDENTITY_KEY_RE.search(str(key)) and isinstance(child, (dict, list)):
                found.append(path)
            found.extend(_identity_fields(child, path))
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            found.extend(_identity_fields(child, f"{prefix}[{idx}]"))
    return found


def read_eval(path: Path) -> dict:
    ev = json.loads(path.read_text())
    hdscore = _numeric(ev["hdscore"], "hdscore")
    nc_values = [_numeric(ev["nc"], "nc")]
    first_nc_time = None
    first_nc_source = None
    for t, row in _details_items(ev):
        nc = _numeric(row["nc"], f"details.{t}.nc")
        nc_values.append(nc)
        if first_nc_time is None and nc < PRIMARY_NC_BAR:
            first_nc_time = t
            first_nc_source = "details"
    nc_min = min(nc_values)
    if nc_min < PRIMARY_NC_BAR and first_nc_time is None:
        first_nc_source = "top_level_only"
    identity_fields = sorted(set(_identity_fields(ev)))
    return {
        "hdscore": hdscore,
        "nc_min": nc_min,
        "collision": nc_min < PRIMARY_NC_BAR,
        "first_nc_time": first_nc_time,
        "first_nc_source": first_nc_source,
        "collision_actor_support_label": (
            "collision_actor_supported" if identity_fields else "collision_actor_not_logged"
        ),
        "collision_actor_identity_fields": identity_fields,
        "eval_top_level_keys": sorted(str(key) for key in ev.keys()),
        "eval_detail_keys": sorted({
            str(key)
            for _, row in _details_items(ev)
            for key in row.keys()
        }),
    }


def first_fire_channel(row: dict) -> str:
    ttc = _numeric(row.get("min_ttc"), "min_ttc")
    cpa = _numeric(row.get("min_cpa"), "min_cpa")
    ttc_cross = ttc < TTC_THRESH
    cpa_cross = cpa < CPA_MARGIN
    if ttc_cross and cpa_cross:
        return "both"
    if ttc_cross:
        return "ttc_only"
    if cpa_cross:
        return "cpa_only"
    return "fired_channel_unreconstructable"


def _matrix3(value: Any, field: str) -> list[list[float]]:
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError(f"{field}-not-3x3")
    out = []
    for row in value:
        if not isinstance(row, list) or len(row) != 3:
            raise ValueError(f"{field}-not-3x3")
        out.append([_numeric(v, field) for v in row])
    return out


def _vec2(value: Any, field: str) -> tuple[float, float]:
    if not isinstance(value, list) or len(value) < 2:
        raise ValueError(f"{field}-not-vec2")
    return _numeric(value[0], field), _numeric(value[1], field)


def _transform_xy(x: float, y: float, r_mat: list[list[float]], trans: list[float]) -> tuple[float, float]:
    return (
        r_mat[0][0] * x + r_mat[0][1] * y + trans[0],
        r_mat[1][0] * x + r_mat[1][1] * y + trans[1],
    )


def reconstruct_argmins(row: dict) -> dict:
    r_mat = _matrix3(row.get("l2g_r_mat"), "l2g_r_mat")
    trans_raw = row.get("l2g_t")
    if not isinstance(trans_raw, list) or len(trans_raw) < 2:
        raise ValueError("l2g_t-not-vec2")
    trans = [_numeric(v, "l2g_t") for v in trans_raw]
    params = row.get("params")
    if not isinstance(params, dict):
        raise ValueError("params-not-dict")
    dt = _numeric(params.get("dt"), "params.dt")
    min_closing = _numeric(params.get("min_closing"), "params.min_closing")
    traj = row.get("traj")
    if not isinstance(traj, list) or not traj:
        raise ValueError("traj-not-list")
    plan_world = []
    for point in traj:
        px, py = _vec2(point, "traj")
        plan_world.append(_transform_xy(px, py, r_mat, trans))
    objs = row.get("objs")
    if not isinstance(objs, list):
        raise ValueError("objs-not-list")

    cpa_candidates = []
    ttc_candidates = []
    for obj in objs:
        if not isinstance(obj, dict):
            raise ValueError("obj-not-dict")
        oid = obj.get("id")
        wx, wy = _vec2(obj.get("world"), "obj.world")
        vx, vy = _vec2(obj.get("vel"), "obj.vel")
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
        cpa_candidates.append({
            "id": oid,
            "value": obj_min_cpa,
            "horizon_index": obj_horizon,
        })

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

    logged_cpa = _numeric(row.get("min_cpa"), "min_cpa")
    logged_ttc = _numeric(row.get("min_ttc"), "min_ttc")
    cpa_argmins = [
        item for item in cpa_candidates
        if _close(item["value"], logged_cpa)
    ]
    ttc_argmins = [
        item for item in ttc_candidates
        if _close(item["value"], logged_ttc)
    ]
    return {
        "cpa_argmins": cpa_argmins,
        "ttc_argmins": ttc_argmins,
        "cpa_candidate_min": min((item["value"] for item in cpa_candidates), default=None),
        "ttc_candidate_min": min((item["value"] for item in ttc_candidates), default=None),
    }


def monitor_provenance_label(channel: str, cpa_ids: list[Any], ttc_ids: list[Any]) -> str:
    if channel == "no_fire":
        return "no_fire"
    if channel == "fired_channel_unreconstructable":
        return "argmin_reconstruction_failed"
    if channel == "cpa_only":
        if not cpa_ids:
            return "argmin_reconstruction_failed"
        return "unique_cpa_object" if len(cpa_ids) == 1 else "ambiguous_cpa_object"
    if channel == "ttc_only":
        if not ttc_ids:
            return "argmin_reconstruction_failed"
        return "unique_ttc_object" if len(ttc_ids) == 1 else "ambiguous_ttc_object"
    if channel == "both":
        if not cpa_ids or not ttc_ids:
            return "argmin_reconstruction_failed"
        if len(cpa_ids) > 1:
            return "ambiguous_cpa_object"
        if len(ttc_ids) > 1:
            return "ambiguous_ttc_object"
        return (
            "unique_both_same_object"
            if cpa_ids[0] == ttc_ids[0] else "both_distinct_objects"
        )
    return "schema_unsupported"


def fire_timing_label(row: dict) -> str:
    if not row["on_collision"]:
        return "no_on_collision"
    if row["first_on_nc_time"] is None:
        return "unknown_collision_time"
    if row["first_fire_channel"] == "no_fire":
        return "no_fire"
    first_fire = row["first_fire_ts"]
    if first_fire is None:
        raise ValueError("fire-channel-without-time")
    if first_fire > row["first_on_nc_time"]:
        return "post_collision_fire"
    lead = row["first_on_nc_time"] - first_fire
    if 0.0 <= lead <= 1.0:
        return "short_lead_fire"
    if lead > 1.0:
        return "long_lead_fire"
    raise ValueError(f"negative-lead:{lead}")


def read_decisions(path: Path) -> dict:
    monitor_frames = 0
    fired_frames = 0
    brake_frames = 0
    first_fire_row = None
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if "trace_error" in row:
            continue
        monitor_frames += 1
        fired = bool(row.get("fired"))
        fired_frames += int(fired)
        brake_frames += int(bool(row.get("brake")))
        if fired and first_fire_row is None:
            first_fire_row = row
    if monitor_frames == 0:
        raise ValueError("empty-decision-log")
    if first_fire_row is None:
        return {
            "monitor_frames": monitor_frames,
            "fired_frames": fired_frames,
            "brake_frames": brake_frames,
            "first_fire_ts": None,
            "first_fire_channel": "no_fire",
            "first_fire_frame_index": None,
            "monitor_provenance_label": "no_fire",
            "first_fire_cpa_object_ids": [],
            "first_fire_ttc_object_ids": [],
            "first_fire_cpa_candidate_min": None,
            "first_fire_ttc_candidate_min": None,
            "first_fire_min_cpa": None,
            "first_fire_min_ttc": None,
        }
    try:
        channel = first_fire_channel(first_fire_row)
        argmins = reconstruct_argmins(first_fire_row)
        cpa_ids = [item["id"] for item in argmins["cpa_argmins"]]
        ttc_ids = [item["id"] for item in argmins["ttc_argmins"]]
        provenance = monitor_provenance_label(channel, cpa_ids, ttc_ids)
        cpa_min = argmins["cpa_candidate_min"]
        ttc_min = argmins["ttc_candidate_min"]
    except (KeyError, ValueError, TypeError):
        channel = "fired_channel_unreconstructable"
        cpa_ids = []
        ttc_ids = []
        provenance = "schema_unsupported"
        cpa_min = None
        ttc_min = None
    return {
        "monitor_frames": monitor_frames,
        "fired_frames": fired_frames,
        "brake_frames": brake_frames,
        "first_fire_ts": _numeric(
            first_fire_row.get("ts", first_fire_row.get("frame_index", 0)),
            "first_fire_ts",
        ),
        "first_fire_channel": channel,
        "first_fire_frame_index": int(first_fire_row.get("frame_index", -1)),
        "monitor_provenance_label": provenance,
        "first_fire_cpa_object_ids": cpa_ids,
        "first_fire_ttc_object_ids": ttc_ids,
        "first_fire_cpa_candidate_min": cpa_min,
        "first_fire_ttc_candidate_min": ttc_min,
        "first_fire_min_cpa": (
            first_fire_row.get("min_cpa")
            if isinstance(first_fire_row.get("min_cpa"), (int, float))
            and not isinstance(first_fire_row.get("min_cpa"), bool)
            else None
        ),
        "first_fire_min_ttc": (
            first_fire_row.get("min_ttc")
            if isinstance(first_fire_row.get("min_ttc"), (int, float))
            and not isinstance(first_fire_row.get("min_ttc"), bool)
            else None
        ),
    }


def scenario_tier(scenario: str) -> str:
    match = TIER_RE.search(scenario)
    return match.group(1) if match else "unknown"


def is_attackplanner_scenario(scenario: str) -> bool:
    return "-extreme-" in scenario or scenario in ATTACKPLANNER_HARD_SCENARIOS


def collect_dataset(dataset: str, episodes_root: Path, problems: list[str]) -> list[dict]:
    rows = []
    for on_dir in sorted(episodes_root.iterdir()):
        if not on_dir.is_dir() or "__on_r" not in on_dir.name:
            continue
        match = PAIR_RE.match(on_dir.name)
        if not match:
            problems.append(f"{dataset}:bad-on-dir-name:{on_dir.name}")
            continue
        scenario = match.group("scenario")
        run = int(match.group("run"))
        try:
            on_eval = read_eval(on_dir / "eval.json")
            decisions = read_decisions(on_dir / "sentinel_iter48_decisions.jsonl")
            row = {
                "dataset": dataset,
                "scenario": scenario,
                "run": run,
                "tier": scenario_tier(scenario),
                "attackplanner": is_attackplanner_scenario(scenario),
                "hd_on": on_eval["hdscore"],
                "on_nc_min": on_eval["nc_min"],
                "on_collision": on_eval["collision"],
                "first_on_nc_time": on_eval["first_nc_time"],
                "first_on_nc_source": on_eval["first_nc_source"],
                "collision_actor_support_label": on_eval["collision_actor_support_label"],
                "collision_actor_identity_fields": on_eval["collision_actor_identity_fields"],
                "eval_top_level_keys": on_eval["eval_top_level_keys"],
                "eval_detail_keys": on_eval["eval_detail_keys"],
                **decisions,
            }
            row["first_fire_lead_time"] = (
                row["first_on_nc_time"] - row["first_fire_ts"]
                if row["on_collision"]
                and row["first_on_nc_time"] is not None
                and row["first_fire_ts"] is not None
                else None
            )
            row["fire_timing_label"] = fire_timing_label(row)
            rows.append(row)
        except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
            problems.append(f"{dataset}:{scenario}:r{run}:{exc}")
    if len(rows) != EXPECTED_PAIRS_PER_DATASET:
        problems.append(f"{dataset}:pair-count:{len(rows)}!={EXPECTED_PAIRS_PER_DATASET}")
    return rows


def key_for(row: dict) -> str:
    return f"{row['dataset']}::{row['scenario']}::r{row['run']}"


def check_iter53(rows: list[dict], iter53_report: Path, problems: list[str]) -> dict:
    try:
        report = json.loads(iter53_report.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        problems.append(f"bad-iter53-report:{exc}")
        return {}
    expected_pairs = report.get("pairs", [])
    expected = {key_for(row): row for row in expected_pairs}
    observed = {key_for(row): row for row in rows}
    missing = sorted(set(expected) - set(observed))
    extra = sorted(set(observed) - set(expected))
    if missing:
        problems.append(f"iter53-missing-keys:{missing[:5]}")
    if extra:
        problems.append(f"iter53-extra-keys:{extra[:5]}")
    channel_mismatches = []
    timing_mismatches = []
    for key in sorted(set(expected) & set(observed)):
        want_channel = expected[key].get("first_fire_channel")
        got_channel = observed[key].get("first_fire_channel")
        if want_channel != got_channel:
            channel_mismatches.append(f"{key}:{want_channel}!={got_channel}")
        want_timing = expected[key].get("fire_timing_label")
        got_timing = observed[key].get("fire_timing_label")
        if want_timing != got_timing:
            timing_mismatches.append(f"{key}:{want_timing}!={got_timing}")
    if channel_mismatches:
        problems.append(f"iter53-channel-mismatches:{channel_mismatches[:5]}")
    if timing_mismatches:
        problems.append(f"iter53-timing-mismatches:{timing_mismatches[:5]}")
    return {
        "iter53_pairs": len(expected_pairs),
        "provenance_pairs": len(rows),
        "channel_mismatches": len(channel_mismatches),
        "timing_mismatches": len(timing_mismatches),
    }


def _counter_dict(counter: Counter, names: tuple[str, ...]) -> dict:
    return {name: counter.get(name, 0) for name in names}


def summarize(rows: list[dict]) -> dict:
    on_rows = [row for row in rows if row["on_collision"]]
    pre_fire = [
        row for row in on_rows
        if row["fire_timing_label"] in ("short_lead_fire", "long_lead_fire")
    ]
    channel_x_monitor: dict[str, dict[str, int]] = {}
    by_channel: defaultdict[str, Counter] = defaultdict(Counter)
    for row in rows:
        by_channel[row["first_fire_channel"]][row["monitor_provenance_label"]] += 1
    for channel in CHANNELS:
        channel_x_monitor[channel] = _counter_dict(
            by_channel[channel], MONITOR_PROVENANCE_LABELS,
        )
    collision_support = Counter(row["collision_actor_support_label"] for row in rows)
    on_collision_support = Counter(row["collision_actor_support_label"] for row in on_rows)
    return {
        "pairs": len(rows),
        "on_collision_pairs": len(on_rows),
        "pre_collision_fire_pairs": len(pre_fire),
        "first_fire_channel_counts": _counter_dict(
            Counter(row["first_fire_channel"] for row in rows), CHANNELS,
        ),
        "monitor_provenance_counts": _counter_dict(
            Counter(row["monitor_provenance_label"] for row in rows),
            MONITOR_PROVENANCE_LABELS,
        ),
        "monitor_provenance_on_collision_counts": _counter_dict(
            Counter(row["monitor_provenance_label"] for row in on_rows),
            MONITOR_PROVENANCE_LABELS,
        ),
        "monitor_provenance_pre_collision_fire_counts": _counter_dict(
            Counter(row["monitor_provenance_label"] for row in pre_fire),
            MONITOR_PROVENANCE_LABELS,
        ),
        "first_fire_channel_x_monitor_provenance": channel_x_monitor,
        "collision_actor_support_counts": _counter_dict(
            collision_support, COLLISION_SUPPORT_LABELS,
        ),
        "collision_actor_support_on_collision_counts": _counter_dict(
            on_collision_support, COLLISION_SUPPORT_LABELS,
        ),
        "eval_top_level_keys": sorted({
            key for row in rows for key in row["eval_top_level_keys"]
        }),
        "eval_detail_keys": sorted({
            key for row in rows for key in row["eval_detail_keys"]
        }),
        "collision_actor_identity_fields": sorted({
            field for row in rows for field in row["collision_actor_identity_fields"]
        }),
    }


def grouped_summaries(rows: list[dict]) -> dict:
    by_dataset = {
        dataset: summarize([row for row in rows if row["dataset"] == dataset])
        for dataset in sorted({row["dataset"] for row in rows})
    }
    iter49 = [row for row in rows if row["dataset"] == "iter49_hard_extreme"]
    return {
        "combined": summarize(rows),
        "by_dataset": by_dataset,
        "iter49_attackplanner": {
            "attackplanner": summarize([row for row in iter49 if row["attackplanner"]]),
            "non_attackplanner": summarize([row for row in iter49 if not row["attackplanner"]]),
        },
    }


def choose_verdict(problems: list[str], rows: list[dict]) -> str:
    if problems:
        return "PROVENANCE_SUPPORT_INFRASTRUCTURE_NULL"
    on_rows = [row for row in rows if row["on_collision"]]
    supported = [
        row for row in on_rows
        if row["collision_actor_support_label"] == "collision_actor_supported"
    ]
    if on_rows and len(supported) == len(on_rows):
        return "PROVENANCE_SUPPORT_COMPLETE"
    return "PROVENANCE_SUPPORT_NULL"


def run_analysis(args: argparse.Namespace) -> dict:
    problems: list[str] = []
    rows = []
    rows.extend(collect_dataset(
        "iter48_easy_medium", Path(args.iter48_episodes), problems,
    ))
    rows.extend(collect_dataset(
        "iter49_hard_extreme", Path(args.iter49_episodes), problems,
    ))
    iter53_cross = check_iter53(rows, Path(args.iter53_report), problems)
    verdict = choose_verdict(problems, rows)
    return {
        "verdict": verdict,
        "process_disclosure": {
            "schema_inspection_disclosed_in_hypothesis": True,
            "patch_inspection_disclosed_in_hypothesis": True,
            "no_inferential_surprise_claim": True,
        },
        "constants": {
            "primary_nc_bar": PRIMARY_NC_BAR,
            "ttc_thresh": TTC_THRESH,
            "cpa_margin": CPA_MARGIN,
            "match_tolerance": MATCH_TOL,
        },
        "infrastructure_problems": problems,
        "iter53_cross_check": iter53_cross,
        "summaries": grouped_summaries(rows) if not problems else {},
        "pairs": rows if not problems else [],
    }


def _fmt(value: float | None) -> str:
    return "" if value is None else f"{value:.2f}"


def _ids(values: list[Any]) -> str:
    return ",".join(str(value) for value in values)


def render_markdown(report: dict) -> str:
    lines = [
        "| dataset | scenario | run | tier | attackplanner | ON collision | first ON NC t | "
        "fire timing | first-fire channel | first fire t | monitor provenance | CPA ids | "
        "TTC ids | collision actor support |",
        "|---|---|---:|---|---|---|---:|---|---|---:|---|---|---|---|",
    ]
    for row in report.get("pairs", []):
        lines.append(
            f"| {row['dataset']} | {row['scenario']} | {row['run']} | {row['tier']} | "
            f"{str(row['attackplanner']).lower()} | {str(row['on_collision']).lower()} | "
            f"{_fmt(row['first_on_nc_time'])} | {row['fire_timing_label']} | "
            f"{row['first_fire_channel']} | {_fmt(row['first_fire_ts'])} | "
            f"{row['monitor_provenance_label']} | {_ids(row['first_fire_cpa_object_ids'])} | "
            f"{_ids(row['first_fire_ttc_object_ids'])} | "
            f"{row['collision_actor_support_label']} |"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iter48-episodes", required=True)
    parser.add_argument("--iter49-episodes", required=True)
    parser.add_argument("--iter53-report", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--markdown-out", required=True)
    args = parser.parse_args()
    report = run_analysis(args)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    Path(args.markdown_out).write_text(render_markdown(report) + "\n")
    print(f"iter54 provenance support audit verdict: {report['verdict']}")
    if report["infrastructure_problems"]:
        print(f"infrastructure problems: {report['infrastructure_problems']}")
    else:
        combined = report["summaries"]["combined"]
        print(f"monitor provenance: {combined['monitor_provenance_counts']}")
        print(f"collision actor support: {combined['collision_actor_support_counts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
