#!/usr/bin/env python3
"""Iteration 41 offline monitor-input degradation gate.

This analyzer intentionally runs only on committed full14/power evidence. It first checks whether
the released-union decision stream can be replayed from committed frame rows plus committed
best-arm ego poses. If that S0 integrity gate fails, perturbations are not evaluated.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import re
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
PERTURBATIONS = ("score_0p50", "range_20m", "dropout_20pct", "jitter_0p25m")

FROZEN_INPUTS = [
    "experiments/iter40_timing_cost_audit/RESULT.md",
    "experiments/iter40_timing_cost_audit/proof-audit/timing_cost_report.json",
    "experiments/full14_power/RESULT.md",
    "experiments/full14_power/proof/analysis_output.txt",
    "experiments/full14_power/proof/p14-runs.tar.gz",
    "experiments/full14_power/proof/sentinel-power14-merged.log",
    "experiments/full14_power/proof/sentinel_p14_best.jsonl.gz.part-aa",
    "experiments/full14_power/proof/sentinel_p14_best.jsonl.gz.part-ab",
    "experiments/iter15_latch_release/server_patch_union_release.py",
    "experiments/iter15_latch_release/RESULT.md",
    "docs/REPORT.md",
    "docs/paper/MANUSCRIPT.md",
    "README.md",
]


@dataclass(frozen=True)
class ReplayParams:
    min_score: float = 0.3
    max_gap: float = 30.0
    cpa_margin: float = 1.5
    ttc_thresh: float = 2.5
    min_closing: float = 3.0
    release_k: int = 4


def git_tracked_paths(root: Path = ROOT) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return set(result.stdout.splitlines())


def path_failures(paths: list[str], tracked: set[str], root: Path = ROOT) -> list[str]:
    failures: list[str] = []
    for rel in paths:
        if not (root / rel).exists():
            failures.append(f"missing_path:{rel}")
        if rel not in tracked:
            failures.append(f"untracked_path:{rel}")
    return failures


def concat_parts(parts: list[Path], out: Path) -> str:
    h = hashlib.sha256()
    with out.open("wb") as dst:
        for part in parts:
            data = part.read_bytes()
            h.update(data)
            dst.write(data)
    return h.hexdigest()


def decision_log_stats(path: Path) -> dict[str, int]:
    rows = resets = frame_rows = brake_rows = release_rows = other_rows = 0
    with gzip.open(path, "rt") as f:
        for line in f:
            rows += 1
            row = json.loads(line)
            if row.get("reset"):
                resets += 1
            elif "ts" in row:
                frame_rows += 1
            elif "brake" in row:
                brake_rows += 1
            elif "release" in row:
                release_rows += 1
            else:
                other_rows += 1
    return {
        "rows": rows,
        "resets": resets,
        "non_reset_rows": rows - resets,
        "frame_rows": frame_rows,
        "brake_rows": brake_rows,
        "release_rows": release_rows,
        "other_rows": other_rows,
    }


def parse_decision_blocks(path: Path) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    with gzip.open(path, "rt") as f:
        for line in f:
            row = json.loads(line)
            if row.get("reset"):
                cur = {"reset_run": row.get("run"), "frames": [], "brakes": [], "releases": []}
                blocks.append(cur)
                continue
            if cur is None:
                continue
            if "ts" in row:
                cur["frames"].append(row)
            elif "brake" in row:
                row = dict(row)
                row["after_frame"] = len(cur["frames"]) - 1
                cur["brakes"].append(row)
            elif "release" in row:
                row = dict(row)
                row["after_frame"] = len(cur["frames"]) - 1
                cur["releases"].append(row)
    return blocks


def parse_pair_order(log_path: Path) -> list[tuple[str, str]]:
    order: list[tuple[str, str]] = []
    for line in log_path.read_text(errors="replace").splitlines():
        match = re.match(r"##### P14PAIR best (\w+) (\d+) #####", line)
        if match:
            order.append((match.group(1), match.group(2)))
    return order


def tar_json(tar: tarfile.TarFile, name: str) -> Any | None:
    try:
        member = tar.extractfile(name)
    except KeyError:
        return None
    if member is None:
        return None
    return json.load(member)


def load_pose_maps(
    archive_path: Path,
    pair_order: list[tuple[str, str]],
) -> dict[tuple[str, str, int], dict[str, Any]]:
    pose_maps: dict[tuple[str, str, int], dict[str, Any]] = {}
    with tarfile.open(archive_path) as tar:
        for scenario_class, scenario_id in pair_order:
            for run_index in range(20):
                name = f"p14-best/{scenario_class}-{scenario_id}/run_{run_index}/ego_poses.json"
                poses = tar_json(tar, name)
                if poses is not None:
                    pose_maps[(scenario_class, scenario_id, run_index)] = poses
    return pose_maps


def episode_key(
    pair_order: list[tuple[str, str]],
    block_index: int,
) -> tuple[str, str, int]:
    scenario_class, scenario_id = pair_order[block_index // 20]
    return scenario_class, scenario_id, block_index % 20


def scenario_key(key: tuple[str, str, int]) -> str:
    return f"{key[0]}-{key[1]}"


def pose_timestamp_coverage(
    blocks: list[dict[str, Any]],
    pair_order: list[tuple[str, str]],
    pose_maps: dict[tuple[str, str, int], dict[str, Any]],
    sample_limit: int = 12,
) -> dict[str, Any]:
    total_frames = 0
    missing = 0
    missing_pose_files = 0
    examples: list[dict[str, Any]] = []
    by_episode: list[dict[str, Any]] = []
    for block_index, block in enumerate(blocks):
        key = episode_key(pair_order, block_index)
        poses = pose_maps.get(key)
        episode_missing = 0
        pose_int_keys = sorted(int(ts) for ts in poses) if poses else []
        if poses is None:
            missing_pose_files += 1
        for frame_index, frame in enumerate(block["frames"]):
            total_frames += 1
            ts = int(frame["ts"])
            if poses is not None and str(ts) in poses:
                continue
            missing += 1
            episode_missing += 1
            if len(examples) < sample_limit:
                nearest = min(pose_int_keys, key=lambda item: abs(item - ts)) if pose_int_keys else None
                examples.append(
                    {
                        "scenario_class": key[0],
                        "scenario_id": key[1],
                        "run_index": key[2],
                        "frame_index": frame_index,
                        "timestamp_us": ts,
                        "nearest_pose_timestamp_us": nearest,
                        "nearest_delta_us": abs(nearest - ts) if nearest is not None else None,
                    }
                )
        if episode_missing:
            by_episode.append(
                {
                    "scenario_class": key[0],
                    "scenario_id": key[1],
                    "run_index": key[2],
                    "missing_exact_timestamps": episode_missing,
                    "frame_rows": len(block["frames"]),
                }
            )
    return {
        "total_frame_rows_checked": total_frames,
        "missing_exact_timestamp_count": missing,
        "missing_exact_timestamp_fraction": missing / total_frames if total_frames else None,
        "missing_pose_files": missing_pose_files,
        "examples": examples,
        "episodes_with_missing_timestamps": len(by_episode),
        "by_episode_sample": by_episode[:sample_limit],
    }


def transform_point(matrix: list[list[float]], point: list[float] | tuple[float, float]) -> tuple[float, float]:
    x, y = float(point[0]), float(point[1])
    return (
        float(matrix[0][0]) * x + float(matrix[0][1]) * y + float(matrix[0][3]),
        float(matrix[1][0]) * x + float(matrix[1][1]) * y + float(matrix[1][3]),
    )


def stable_hash_int(parts: list[Any]) -> int:
    return int(hashlib.sha256("|".join(str(part) for part in parts).encode()).hexdigest(), 16)


def dropout_object(scen: str, run_index: int, frame_index: int, object_index: int) -> bool:
    return (
        stable_hash_int(["iter41", "dropout_20pct", scen, run_index, frame_index, object_index])
        % 100
        < 20
    )


def jitter_offset(scen: str, run_index: int, frame_index: int, object_index: int, axis: str) -> float:
    raw = stable_hash_int(["iter41", "jitter_0p25m", scen, run_index, frame_index, object_index, axis])
    unit = raw / float((1 << 256) - 1)
    return -0.25 + 0.5 * unit


def params_for_mode(mode: str | None) -> ReplayParams:
    if mode == "score_0p50":
        return ReplayParams(min_score=0.50)
    if mode == "range_20m":
        return ReplayParams(max_gap=20.0)
    return ReplayParams()


def perturb_frame(
    frame: dict[str, Any],
    scen: str,
    run_index: int,
    frame_index: int,
    mode: str | None,
) -> tuple[list[list[float]], list[float | None], list[Any]]:
    objs_in = frame.get("objs") or []
    scores_in = frame.get("scores") or []
    ids_in = frame.get("object_ids") or []
    objs: list[list[float]] = []
    scores: list[float | None] = []
    ids: list[Any] = []

    for object_index, obj in enumerate(objs_in):
        if mode == "dropout_20pct" and dropout_object(scen, run_index, frame_index, object_index):
            continue
        new_obj = [float(value) for value in obj]
        if mode == "jitter_0p25m" and len(new_obj) >= 2:
            new_obj[0] += jitter_offset(scen, run_index, frame_index, object_index, "x")
            new_obj[1] += jitter_offset(scen, run_index, frame_index, object_index, "y")
        objs.append(new_obj)
        scores.append(scores_in[object_index] if object_index < len(scores_in) else None)
        if object_index < len(ids_in):
            ids.append(ids_in[object_index])
    return objs, scores, ids


def monitor_fired(
    frame: dict[str, Any],
    pose: list[list[float]],
    track: dict[Any, tuple[float, float, int]],
    params: ReplayParams,
    scen: str,
    run_index: int,
    frame_index: int,
    mode: str | None,
) -> tuple[bool, dict[Any, tuple[float, float, int]], float, float]:
    traj = frame.get("traj") or []
    ego_world_plan = [transform_point(pose, point) for point in traj]
    ego_wx, ego_wy = float(pose[0][3]), float(pose[1][3])
    ts = int(frame["ts"])
    objs, scores, ids = perturb_frame(frame, scen, run_index, frame_index, mode)
    min_cpa = 1e9
    min_ttc = 1e9
    newtrack: dict[Any, tuple[float, float, int]] = {}
    for i in range(min(len(objs), len(scores))):
        score = scores[i]
        if score is None or float(score) < params.min_score:
            continue
        ox, oy = float(objs[i][0]), float(objs[i][1])
        if math.hypot(ox, oy) > params.max_gap:
            continue
        wx, wy = transform_point(pose, (ox, oy))
        oid = ids[i] if i < len(ids) else f"idx_{i}"
        newtrack[oid] = (wx, wy, ts)
        avx = avy = 0.0
        if oid in track:
            pwx, pwy, pts = track[oid]
            dta = (ts - pts) / 1e6
            if dta > 1e-3:
                avx, avy = (wx - pwx) / dta, (wy - pwy) / dta
        for k, (ex, ey) in enumerate(ego_world_plan):
            t = (k + 1) * 0.5
            ax, ay = wx + avx * t, wy + avy * t
            min_cpa = min(min_cpa, math.hypot(ex - ax, ey - ay))
        dx, dy = ego_wx - wx, ego_wy - wy
        gapw = math.hypot(dx, dy)
        if gapw > 1e-3:
            closing = (avx * dx + avy * dy) / gapw
            if closing > max(params.min_closing, 0.5):
                min_ttc = min(min_ttc, gapw / closing)
    fired = min_cpa < params.cpa_margin or min_ttc < params.ttc_thresh
    return fired, newtrack, min_cpa, min_ttc


def replay_episode(
    block: dict[str, Any],
    poses: dict[str, Any],
    scen: str,
    run_index: int,
    mode: str | None = None,
    params: ReplayParams | None = None,
) -> dict[str, Any]:
    params = params or params_for_mode(mode)
    track: dict[Any, tuple[float, float, int]] = {}
    braking = False
    clear = 0
    brake_indices: list[int] = []
    brake_timestamps: list[int] = []

    for frame_index, frame in enumerate(block["frames"]):
        pose = poses[str(int(frame["ts"]))]
        fired, newtrack, _, _ = monitor_fired(
            frame,
            pose,
            track,
            params,
            scen,
            run_index,
            frame_index,
            mode,
        )
        track = newtrack
        if fired:
            braking = True
            clear = 0
        elif braking:
            clear += 1
            if clear >= params.release_k:
                braking = False
                clear = 0
        if braking:
            brake_indices.append(frame_index)
            brake_timestamps.append(int(frame["ts"]))

    return {
        "brake_frame_indices": brake_indices,
        "brake_frame_count": len(brake_indices),
        "intervention_episode": bool(brake_indices),
        "first_brake_frame_index": brake_indices[0] if brake_indices else None,
        "first_brake_timestamp_us": brake_timestamps[0] if brake_timestamps else None,
        "last_brake_timestamp_us": brake_timestamps[-1] if brake_timestamps else None,
    }


def replay_all(
    blocks: list[dict[str, Any]],
    pair_order: list[tuple[str, str]],
    pose_maps: dict[tuple[str, str, int], dict[str, Any]],
    mode: str | None = None,
) -> dict[tuple[str, str, int], dict[str, Any]]:
    replay: dict[tuple[str, str, int], dict[str, Any]] = {}
    for block_index, block in enumerate(blocks):
        key = episode_key(pair_order, block_index)
        replay[key] = replay_episode(block, pose_maps[key], scenario_key(key), key[2], mode)
    return replay


def logged_summaries(
    blocks: list[dict[str, Any]],
    pair_order: list[tuple[str, str]],
) -> dict[tuple[str, str, int], dict[str, Any]]:
    logged: dict[tuple[str, str, int], dict[str, Any]] = {}
    for block_index, block in enumerate(blocks):
        key = episode_key(pair_order, block_index)
        indices = [int(row["after_frame"]) for row in block["brakes"]]
        timestamps = [
            int(block["frames"][idx]["ts"])
            for idx in indices
            if 0 <= idx < len(block["frames"])
        ]
        logged[key] = {
            "brake_frame_indices": indices,
            "brake_frame_count": len(indices),
            "intervention_episode": bool(indices),
            "first_brake_frame_index": indices[0] if indices else None,
            "first_brake_timestamp_us": timestamps[0] if timestamps else None,
            "last_brake_timestamp_us": timestamps[-1] if timestamps else None,
        }
    return logged


def compare_replay_to_logged(
    replay: dict[tuple[str, str, int], dict[str, Any]],
    logged: dict[tuple[str, str, int], dict[str, Any]],
    sample_limit: int = 12,
) -> dict[str, Any]:
    failures: list[str] = []
    mismatches: list[dict[str, Any]] = []
    total_replay = sum(row["brake_frame_count"] for row in replay.values())
    total_logged = sum(row["brake_frame_count"] for row in logged.values())
    replay_interventions = sum(1 for row in replay.values() if row["intervention_episode"])
    logged_interventions = sum(1 for row in logged.values() if row["intervention_episode"])
    if total_replay != 1205:
        failures.append(f"vanilla_replay_brake_frames={total_replay} != 1205")
    if replay_interventions != 230:
        failures.append(f"vanilla_replay_intervention_episodes={replay_interventions} != 230")
    if total_logged != 1205:
        failures.append(f"logged_brake_frames={total_logged} != 1205")
    if logged_interventions != 230:
        failures.append(f"logged_intervention_episodes={logged_interventions} != 230")

    for key, logged_row in logged.items():
        replay_row = replay[key]
        if (
            replay_row["brake_frame_count"] == logged_row["brake_frame_count"]
            and replay_row["first_brake_frame_index"] == logged_row["first_brake_frame_index"]
            and replay_row["brake_frame_indices"] == logged_row["brake_frame_indices"]
        ):
            continue
        if replay_row["brake_frame_count"] != logged_row["brake_frame_count"]:
            failures.append(f"{scenario_key(key)}/run_{key[2]} brake_count_mismatch")
        elif replay_row["first_brake_frame_index"] != logged_row["first_brake_frame_index"]:
            failures.append(f"{scenario_key(key)}/run_{key[2]} first_brake_mismatch")
        else:
            failures.append(f"{scenario_key(key)}/run_{key[2]} brake_index_mismatch")
        if len(mismatches) < sample_limit:
            mismatches.append(
                {
                    "scenario_class": key[0],
                    "scenario_id": key[1],
                    "run_index": key[2],
                    "logged": logged_row,
                    "replay": replay_row,
                }
            )

    return {
        "pass": not failures,
        "failures": failures[:sample_limit],
        "failure_count": len(failures),
        "mismatch_examples": mismatches,
        "logged_brake_frames": total_logged,
        "replay_brake_frames": total_replay,
        "logged_intervention_episodes": logged_interventions,
        "replay_intervention_episodes": replay_interventions,
    }


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = round((len(ordered) - 1) * q)
    return ordered[idx]


def median_intervention_count(rows: list[dict[str, Any]]) -> float | None:
    counts = [float(row["brake_frame_count"]) for row in rows if row["intervention_episode"]]
    return percentile(counts, 0.50)


def build_episode_meta(timing_report: dict[str, Any]) -> dict[tuple[str, str, int], dict[str, Any]]:
    meta: dict[tuple[str, str, int], dict[str, Any]] = {}
    for row in timing_report.get("episodes", []):
        key = (str(row["scenario_class"]), str(row["scenario_id"]), int(row["run_index"]))
        meta[key] = row
    return meta


def measured_lead_rows(timing_report: dict[str, Any]) -> dict[tuple[str, str, int], float]:
    rows: dict[tuple[str, str, int], float] = {}
    for row in timing_report.get("lead_time_rows", []):
        if row.get("status") != "measured":
            continue
        key = (str(row["scenario_class"]), str(row["scenario_id"]), int(row["run_index"]))
        rows[key] = float(row["lead_time_s"])
    return rows


def evaluate_s1_mode(
    mode: str,
    vanilla: dict[tuple[str, str, int], dict[str, Any]],
    perturbed: dict[tuple[str, str, int], dict[str, Any]],
    meta: dict[tuple[str, str, int], dict[str, Any]],
) -> dict[str, Any]:
    keys = [
        key
        for key, row in meta.items()
        if row.get("off_collision") is True and vanilla[key]["intervention_episode"]
    ]
    retained = [key for key in keys if perturbed[key]["intervention_episode"]]
    delays = [
        (perturbed[key]["first_brake_timestamp_us"] - vanilla[key]["first_brake_timestamp_us"])
        / 1e6
        for key in retained
    ]
    vanilla_brakes = sum(vanilla[key]["brake_frame_count"] for key in keys)
    perturbed_brakes = sum(perturbed[key]["brake_frame_count"] for key in keys)
    retained_fraction = len(retained) / len(keys) if keys else None
    large_delay_fraction = (
        (sum(1 for value in delays if value > 1.0) + (len(keys) - len(retained))) / len(keys)
        if keys
        else None
    )
    brake_frame_ratio = perturbed_brakes / vanilla_brakes if vanilla_brakes else None
    failures: list[str] = []
    if not keys:
        failures.append(f"{mode}:s1_empty_collision_intervention_subset")
    if retained_fraction is None or retained_fraction < 0.90:
        failures.append(f"{mode}:retained_fraction={retained_fraction} < 0.90")
    if percentile(delays, 0.50) is None or percentile(delays, 0.50) > 0.50:
        failures.append(f"{mode}:median_first_brake_delay_s={percentile(delays, 0.50)} > 0.50")
    if large_delay_fraction is None or large_delay_fraction > 0.10:
        failures.append(f"{mode}:large_or_lost_delay_fraction={large_delay_fraction} > 0.10")
    if brake_frame_ratio is None or brake_frame_ratio < 0.70:
        failures.append(f"{mode}:brake_frame_ratio={brake_frame_ratio} < 0.70")
    return {
        "pass": not failures,
        "failures": failures,
        "eligible_episodes": len(keys),
        "retained_intervention_episodes": len(retained),
        "retained_fraction": retained_fraction,
        "median_first_brake_delay_s": percentile(delays, 0.50),
        "large_or_lost_delay_fraction": large_delay_fraction,
        "vanilla_brake_frames": vanilla_brakes,
        "perturbed_brake_frames": perturbed_brakes,
        "brake_frame_ratio": brake_frame_ratio,
    }


def evaluate_s1(
    vanilla: dict[tuple[str, str, int], dict[str, Any]],
    perturbations: dict[str, dict[tuple[str, str, int], dict[str, Any]]],
    meta: dict[tuple[str, str, int], dict[str, Any]],
) -> dict[str, Any]:
    by_mode = {
        mode: evaluate_s1_mode(mode, vanilla, perturbations[mode], meta)
        for mode in PERTURBATIONS
    }
    failures = [failure for row in by_mode.values() for failure in row["failures"]]
    return {"pass": not failures, "failures": failures, "by_mode": by_mode}


def evaluate_s2_mode(
    mode: str,
    vanilla: dict[tuple[str, str, int], dict[str, Any]],
    perturbed: dict[tuple[str, str, int], dict[str, Any]],
    meta: dict[tuple[str, str, int], dict[str, Any]],
) -> dict[str, Any]:
    keys = [key for key, row in meta.items() if row.get("off_collision") is False]
    vanilla_no_intervention = [key for key in keys if not vanilla[key]["intervention_episode"]]
    new_interventions = [
        key for key in vanilla_no_intervention if perturbed[key]["intervention_episode"]
    ]
    vanilla_rows = [vanilla[key] for key in keys]
    perturbed_rows = [perturbed[key] for key in keys]
    vanilla_total = sum(row["brake_frame_count"] for row in vanilla_rows)
    perturbed_total = sum(row["brake_frame_count"] for row in perturbed_rows)
    vanilla_median = median_intervention_count(vanilla_rows)
    perturbed_median = median_intervention_count(perturbed_rows)
    new_fraction = len(new_interventions) / len(keys) if keys else None
    total_ratio = perturbed_total / vanilla_total if vanilla_total else (0.0 if not perturbed_total else None)
    failures: list[str] = []
    if not keys:
        failures.append(f"{mode}:s2_empty_off_noncollision_subset")
    if new_fraction is None or new_fraction > 0.05:
        failures.append(f"{mode}:new_intervention_fraction={new_fraction} > 0.05")
    if total_ratio is None or total_ratio > 1.25:
        failures.append(f"{mode}:off_noncollision_brake_frame_ratio={total_ratio} > 1.25")
    if vanilla_median in (None, 0.0):
        median_ok = perturbed_median == vanilla_median
    else:
        median_ok = perturbed_median is not None and perturbed_median <= 1.25 * vanilla_median
    if not median_ok:
        failures.append(
            f"{mode}:median_brake_frames_per_intervention={perturbed_median} "
            f"exceeds vanilla={vanilla_median}"
        )
    return {
        "pass": not failures,
        "failures": failures,
        "eligible_episodes": len(keys),
        "new_interventions_from_vanilla_no_intervention": len(new_interventions),
        "new_intervention_fraction": new_fraction,
        "vanilla_total_brake_frames": vanilla_total,
        "perturbed_total_brake_frames": perturbed_total,
        "total_brake_frame_ratio": total_ratio,
        "vanilla_median_brake_frames_per_intervention": vanilla_median,
        "perturbed_median_brake_frames_per_intervention": perturbed_median,
    }


def evaluate_s2(
    vanilla: dict[tuple[str, str, int], dict[str, Any]],
    perturbations: dict[str, dict[tuple[str, str, int], dict[str, Any]]],
    meta: dict[tuple[str, str, int], dict[str, Any]],
) -> dict[str, Any]:
    by_mode = {
        mode: evaluate_s2_mode(mode, vanilla, perturbations[mode], meta)
        for mode in PERTURBATIONS
    }
    failures = [failure for row in by_mode.values() for failure in row["failures"]]
    return {"pass": not failures, "failures": failures, "by_mode": by_mode}


def evaluate_s3_mode(
    mode: str,
    vanilla: dict[tuple[str, str, int], dict[str, Any]],
    perturbed: dict[tuple[str, str, int], dict[str, Any]],
    measured: dict[tuple[str, str, int], float],
) -> dict[str, Any]:
    retained = [key for key in measured if perturbed[key]["intervention_episode"]]
    deltas: list[float] = []
    perturbed_leads: list[float] = []
    for key in retained:
        vanilla_first = vanilla[key]["first_brake_timestamp_us"]
        perturbed_first = perturbed[key]["first_brake_timestamp_us"]
        contact_ts = vanilla_first + measured[key] * 1e6
        perturbed_lead = (contact_ts - perturbed_first) / 1e6
        perturbed_leads.append(perturbed_lead)
        deltas.append(perturbed_lead - measured[key])
    retained_fraction = len(retained) / len(measured) if measured else None
    negative_delta_fraction = (
        sum(1 for value in deltas if value < -1.0) / len(retained) if retained else None
    )
    negative_lead_fraction = (
        sum(1 for value in perturbed_leads if value < 0.0) / len(retained) if retained else None
    )
    failures: list[str] = []
    if len(measured) != 61:
        failures.append(f"{mode}:measured_leadtime_episodes={len(measured)} != 61")
    if retained_fraction is None or retained_fraction < 0.90:
        failures.append(f"{mode}:retained_leadtime_fraction={retained_fraction} < 0.90")
    if percentile(deltas, 0.50) is None or percentile(deltas, 0.50) < -0.50:
        failures.append(f"{mode}:median_leadtime_delta_s={percentile(deltas, 0.50)} < -0.50")
    if negative_delta_fraction is None or negative_delta_fraction > 0.10:
        failures.append(f"{mode}:delta_lt_minus_1s_fraction={negative_delta_fraction} > 0.10")
    if negative_lead_fraction is None or negative_lead_fraction > 0.10:
        failures.append(f"{mode}:negative_lead_fraction={negative_lead_fraction} > 0.10")
    return {
        "pass": not failures,
        "failures": failures,
        "measured_episodes": len(measured),
        "retained_intervention_episodes": len(retained),
        "retained_fraction": retained_fraction,
        "median_leadtime_delta_s": percentile(deltas, 0.50),
        "delta_lt_minus_1s_fraction": negative_delta_fraction,
        "negative_lead_fraction": negative_lead_fraction,
    }


def evaluate_s3(
    vanilla: dict[tuple[str, str, int], dict[str, Any]],
    perturbations: dict[str, dict[tuple[str, str, int], dict[str, Any]]],
    measured: dict[tuple[str, str, int], float],
) -> dict[str, Any]:
    by_mode = {
        mode: evaluate_s3_mode(mode, vanilla, perturbations[mode], measured)
        for mode in PERTURBATIONS
    }
    failures = [failure for row in by_mode.values() for failure in row["failures"]]
    return {"pass": not failures, "failures": failures, "by_mode": by_mode}


def evaluate_s4() -> dict[str, Any]:
    return {
        "pass": True,
        "failures": [],
        "authorized_successor_only": "separate degraded-sensor closed-loop pre-registration",
        "forbidden_from_iter41": [
            "camera/image degradation claim",
            "UniAD degraded-sensor robustness claim",
            "closed-loop safety claim",
            "selector evaluation",
            "deployment or production readiness language",
            "iteration-38 calibration or heldout claim",
        ],
    }


def evaluate_s0(
    root: Path,
    tracked: set[str],
    best_gz: Path,
    blocks: list[dict[str, Any]],
    pair_order: list[tuple[str, str]],
    timing_report: dict[str, Any],
    pose_maps: dict[tuple[str, str, int], dict[str, Any]],
    pose_load_error: str | None = None,
) -> tuple[dict[str, Any], dict[tuple[str, str, int], dict[str, Any]] | None]:
    failures = path_failures(FROZEN_INPUTS, tracked, root)
    if pose_load_error:
        failures.append(f"pose_archive_load_error:{pose_load_error}")

    analysis_path = root / "experiments/full14_power/proof/analysis_output.txt"
    analysis = analysis_path.read_text(errors="replace") if analysis_path.exists() else ""
    if "H-P0: PASS" not in analysis:
        failures.append("hp0_not_pass")
    if timing_report.get("verdict") != "TIMING_COST_AUDIT_PASS_SIMULATION_SCOPE":
        failures.append(f"iter40_verdict={timing_report.get('verdict')}")

    stats = decision_log_stats(best_gz)
    expected_stats = {"resets": 400, "non_reset_rows": 7835, "brake_rows": 1205}
    for key, expected in expected_stats.items():
        if stats[key] != expected:
            failures.append(f"best_decision_{key}={stats[key]} != {expected}")
    if len(blocks) != 400:
        failures.append(f"best_decision_block_count={len(blocks)} != 400")
    if len(pair_order) != 20:
        failures.append(f"best_pair_marker_count={len(pair_order)} != 20")
    if len(blocks) == 400:
        for pair_index in range(20):
            reset_runs = [blocks[pair_index * 20 + run]["reset_run"] for run in range(20)]
            if reset_runs != list(range(20)):
                failures.append(f"best_reset_run_order_pair_{pair_index}={reset_runs}")
                break

    coverage = (
        pose_timestamp_coverage(blocks, pair_order, pose_maps)
        if len(pair_order) == 20 and len(blocks) == 400
        else {"skipped": "pair_or_block_count_failed"}
    )
    if coverage.get("missing_pose_files", 0):
        failures.append(f"missing_pose_files={coverage['missing_pose_files']}")
    if coverage.get("missing_exact_timestamp_count", 0):
        failures.append(
            "pose_timestamp_exact_miss="
            f"{coverage['missing_exact_timestamp_count']}/"
            f"{coverage['total_frame_rows_checked']}"
        )

    replay_comparison: dict[str, Any] = {"skipped": "s0_pre_replay_failures_present"}
    vanilla_replay: dict[tuple[str, str, int], dict[str, Any]] | None = None
    if not failures:
        vanilla_replay = replay_all(blocks, pair_order, pose_maps)
        replay_comparison = compare_replay_to_logged(
            vanilla_replay,
            logged_summaries(blocks, pair_order),
        )
        if not replay_comparison["pass"]:
            failures.extend(replay_comparison["failures"])

    return (
        {
            "pass": not failures,
            "failures": failures,
            "frozen_input_count": len(FROZEN_INPUTS),
            "best_decision_log_stats": stats,
            "pose_timestamp_coverage": coverage,
            "vanilla_replay_comparison": replay_comparison,
            "no_gpu_or_model_commands_run_by_analyzer": True,
        },
        vanilla_replay,
    )


def verdict(
    s0: dict[str, Any],
    s1: dict[str, Any] | None,
    s2: dict[str, Any] | None,
    s3: dict[str, Any] | None,
    s4: dict[str, Any] | None,
) -> str:
    if not s0["pass"]:
        return "DEGRADATION_GATE_INFRASTRUCTURE_NULL"
    if s1 is None or not s1["pass"]:
        return "DEGRADATION_GATE_NULL_SAFETY_RETENTION_FAIL"
    if s2 is None or not s2["pass"]:
        return "DEGRADATION_GATE_NULL_SELECTIVITY_COST_FAIL"
    if s3 is None or not s3["pass"]:
        return "DEGRADATION_GATE_NULL_LEADTIME_STABILITY_FAIL"
    if s4 is None or not s4["pass"]:
        return "DEGRADATION_GATE_OVERCLAIM_NULL"
    return "DEGRADATION_GATE_PASS_OFFLINE_OBJECT_STREAM_SCOPE"


def replay_report_rows(replay: dict[tuple[str, str, int], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key, value in sorted(replay.items()):
        row = {
            "scenario_class": key[0],
            "scenario_id": key[1],
            "run_index": key[2],
        }
        row.update(value)
        rows.append(row)
    return rows


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    tracked = git_tracked_paths(root)
    timing_report_path = root / "experiments/iter40_timing_cost_audit/proof-audit/timing_cost_report.json"
    timing_report = json.loads(timing_report_path.read_text())

    with tempfile.TemporaryDirectory(prefix="iter41_degradation_gate_") as tmp_raw:
        tmp = Path(tmp_raw)
        best_gz = tmp / "sentinel_p14_best.jsonl.gz"
        proof_dir = root / "experiments/full14_power/proof"
        best_sha = concat_parts(sorted(proof_dir.glob("sentinel_p14_best.jsonl.gz.part-*")), best_gz)
        blocks = parse_decision_blocks(best_gz)
        pair_order = parse_pair_order(proof_dir / "sentinel-power14-merged.log")
        pose_load_error = None
        try:
            pose_maps = load_pose_maps(proof_dir / "p14-runs.tar.gz", pair_order)
        except Exception as exc:  # pragma: no cover - defensive proof artifact reporting
            pose_maps = {}
            pose_load_error = str(exc)

        s0, vanilla_replay = evaluate_s0(
            root,
            tracked,
            best_gz,
            blocks,
            pair_order,
            timing_report,
            pose_maps,
            pose_load_error,
        )

        perturbation_replays: dict[str, dict[tuple[str, str, int], dict[str, Any]]] = {}
        s1 = s2 = s3 = s4 = None
        if s0["pass"] and vanilla_replay is not None:
            perturbation_replays = {
                mode: replay_all(blocks, pair_order, pose_maps, mode) for mode in PERTURBATIONS
            }
            meta = build_episode_meta(timing_report)
            measured = measured_lead_rows(timing_report)
            s1 = evaluate_s1(vanilla_replay, perturbation_replays, meta)
            s2 = evaluate_s2(vanilla_replay, perturbation_replays, meta) if s1["pass"] else None
            s3 = (
                evaluate_s3(vanilla_replay, perturbation_replays, measured)
                if s2 and s2["pass"]
                else None
            )
            s4 = evaluate_s4() if s3 and s3["pass"] else None

    report: dict[str, Any] = {
        "verdict": verdict(s0, s1, s2, s3, s4),
        "command_line": " ".join(sys.argv),
        "reconstructed_gzip_receipts": {"best_sha256": best_sha},
        "s0": s0,
        "s1": s1,
        "s2": s2,
        "s3": s3,
        "s4": s4,
        "perturbation_modes": list(PERTURBATIONS),
        "claim_boundary": (
            "Iteration 41 is an offline replay of logged monitor inputs, not camera/image "
            "degradation, UniAD robustness, closed-loop safety, wall-clock latency, deployment "
            "readiness, or a production-cost result."
        ),
    }
    if vanilla_replay is not None:
        report["vanilla_replay"] = replay_report_rows(vanilla_replay)
    if perturbation_replays:
        report["perturbation_replays"] = {
            mode: replay_report_rows(replay) for mode, replay in perturbation_replays.items()
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument(
        "--out",
        default="experiments/iter41_sensor_input_degradation_gate/proof-audit/"
        "degradation_gate_report.json",
    )
    args = parser.parse_args()
    report = build_report(args)
    out = Path(args.out)
    if not out.is_absolute():
        out = Path(args.root) / out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": report["verdict"], "out": str(out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
