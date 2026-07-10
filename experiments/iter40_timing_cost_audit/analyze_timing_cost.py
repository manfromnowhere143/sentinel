#!/usr/bin/env python3
"""Iteration 40 timing and intervention-cost audit over committed evidence only."""

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
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
CONTACT_M = 2.0
CLASSES = ("stationary", "frontal", "side")

FROZEN_INPUTS = [
    "experiments/iter39_external_validity_claim_audit/RESULT.md",
    "experiments/full14_power/RESULT.md",
    "experiments/full14_power/proof/analysis_output.txt",
    "experiments/full14_power/proof/p14-runs.tar.gz",
    "experiments/full14_power/proof/sentinel-power14-merged.log",
    "experiments/full14_power/proof/sentinel_p14_best.jsonl.gz.part-aa",
    "experiments/full14_power/proof/sentinel_p14_best.jsonl.gz.part-ab",
    "experiments/full14_power/proof/sentinel_p14_off.jsonl.gz.part-aa",
    "experiments/full14_power/proof/sentinel_p14_off.jsonl.gz.part-ab",
    "experiments/full14_power/proof/sentinel_p14_off.jsonl.gz.part-ac",
    "experiments/verification/README.md",
    "experiments/verification/analyze_safety_case.py",
    "experiments/verification/proof_v20.txt",
    "experiments/verification/evidence/jsonl/sentinel_i8_union.jsonl.gz",
    "experiments/verification/evidence/jsonl/sentinel_i8_off.jsonl.gz",
    "experiments/verification/evidence/runs/i8-union.tar.gz",
    "experiments/verification/evidence/runs/i8-off.tar.gz",
    "experiments/verification/evidence/logs/sentinel-i8.log",
    "experiments/iter15_latch_release/RESULT.md",
    "docs/REPORT.md",
    "docs/paper/MANUSCRIPT.md",
    "README.md",
]


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


def parse_decision_blocks(path: Path) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    with gzip.open(path, "rt") as f:
        for line in f:
            row = json.loads(line)
            if row.get("reset"):
                cur = {"reset_run": row.get("run"), "frames": [], "brakes": []}
                blocks.append(cur)
                continue
            if cur is None:
                continue
            if "brake" in row:
                row = dict(row)
                row["after_frame"] = len(cur["frames"]) - 1
                cur["brakes"].append(row)
            elif "ts" in row:
                cur["frames"].append(row)
    return blocks


def decision_log_stats(path: Path) -> dict[str, Any]:
    rows = resets = frames = brake_rows = 0
    with gzip.open(path, "rt") as f:
        for line in f:
            rows += 1
            row = json.loads(line)
            if row.get("reset"):
                resets += 1
            else:
                frames += 1
                if "brake" in row:
                    brake_rows += 1
    return {"rows": rows, "resets": resets, "frames": frames, "brake_rows": brake_rows}


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


def metric_paths(tar: tarfile.TarFile, tag: str) -> list[str]:
    prefix = f"{tag}/"
    return [name for name in tar.getnames() if name.startswith(prefix) and name.endswith("/metrics.json")]


def pairs_from_metrics(paths: list[str]) -> list[str]:
    return sorted({"/".join(path.split("/")[:2]) for path in paths})


def path_len_from_poses(poses: dict[str, Any]) -> float:
    points = [(matrix[0][3], matrix[1][3]) for _, matrix in sorted(poses.items(), key=lambda item: int(item[0]))]
    return sum(math.hypot(points[i + 1][0] - points[i][0], points[i + 1][1] - points[i][1]) for i in range(len(points) - 1))


def interp_xy(ts_list: list[int], xy_list: list[tuple[float, float]], t: int) -> tuple[float, float]:
    if t <= ts_list[0]:
        return xy_list[0]
    for (t0, p0), (t1, p1) in zip(zip(ts_list, xy_list), zip(ts_list[1:], xy_list[1:])):
        if t0 <= t <= t1:
            scale = (t - t0) / (t1 - t0) if t1 > t0 else 0.0
            return (p0[0] + (p1[0] - p0[0]) * scale, p0[1] + (p1[1] - p0[1]) * scale)
    return xy_list[-1]


def contact_ts_gt(actors: list[dict[str, Any]], ego: dict[str, Any], contact_m: float = CONTACT_M) -> int | None:
    ets = sorted(int(ts) for ts in ego)
    if len(ets) < 2:
        return None
    exy = [(ego[str(ts)][0][3], ego[str(ts)][1][3]) for ts in ets]
    best_min = float("inf")
    best_contact: int | None = None
    for actor in actors:
        ats = [int(ts) for ts in actor.get("timestamps", [])]
        poses = actor.get("poses", [])
        if len(ats) < 2 or len(ats) != len(poses):
            continue
        axy = [(pose[0][3], pose[1][3]) for pose in poses]
        lo, hi = max(ats[0], ets[0]), min(ats[-1], ets[-1])
        if hi <= lo:
            continue
        t = lo
        first_contact = None
        min_dist = float("inf")
        while t <= hi:
            ax, ay = interp_xy(ats, axy, t)
            ex, ey = interp_xy(ets, exy, t)
            dist = math.hypot(ax - ex, ay - ey)
            min_dist = min(min_dist, dist)
            if dist < contact_m and first_contact is None:
                first_contact = t
            t += 100_000
        if min_dist < best_min:
            best_min = min_dist
            best_contact = first_contact
    return best_contact


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = round((len(ordered) - 1) * q)
    return ordered[idx]


def summarize(values: list[float]) -> dict[str, Any]:
    return {
        "n": len(values),
        "min": min(values) if values else None,
        "p05": percentile(values, 0.05),
        "median": percentile(values, 0.50),
        "p95": percentile(values, 0.95),
        "max": max(values) if values else None,
    }


def summarize_episodes(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    brake_counts = [ep["brake_frame_count"] for ep in episodes]
    intervention_counts = [ep["brake_frame_count"] for ep in episodes if ep["intervention_episode"]]
    km = sum(ep["ego_distance_m"] for ep in episodes) / 1000.0
    return {
        "episodes": len(episodes),
        "intervention_episodes": sum(1 for ep in episodes if ep["intervention_episode"]),
        "total_brake_frames": sum(brake_counts),
        "ego_distance_m": sum(ep["ego_distance_m"] for ep in episodes),
        "brake_frames_per_km": sum(brake_counts) / max(km, 1e-9),
        "median_brake_frames_per_intervention_episode": percentile(intervention_counts, 0.50),
        "p95_brake_frames_per_intervention_episode": percentile(intervention_counts, 0.95),
    }


def block_first_last_brake_ts(block: dict[str, Any]) -> tuple[int | None, int | None]:
    timestamps: list[int] = []
    frames = block["frames"]
    for brake in block["brakes"]:
        idx = brake.get("after_frame", -1)
        if 0 <= idx < len(frames):
            timestamps.append(int(frames[idx]["ts"]))
    if not timestamps:
        return None, None
    return min(timestamps), max(timestamps)


def build_episode_table(root: Path, best_gz: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    log_path = root / "experiments/full14_power/proof/sentinel-power14-merged.log"
    archive_path = root / "experiments/full14_power/proof/p14-runs.tar.gz"
    pair_order = parse_pair_order(log_path)
    blocks = parse_decision_blocks(best_gz)
    episodes: list[dict[str, Any]] = []
    lead_rows: list[dict[str, Any]] = []

    with tarfile.open(archive_path) as tar:
        for pair_idx, (scenario_class, scenario_id) in enumerate(pair_order):
            for run_index in range(20):
                block = blocks[pair_idx * 20 + run_index]
                first_ts, last_ts = block_first_last_brake_ts(block)
                ego = tar_json(tar, f"p14-best/{scenario_class}-{scenario_id}/run_{run_index}/ego_poses.json")
                metrics = tar_json(tar, f"p14-best/{scenario_class}-{scenario_id}/run_{run_index}/metrics.json")
                off_metrics = tar_json(tar, f"p14-off/{scenario_class}-{scenario_id}/run_{run_index}/metrics.json")
                ego_distance = path_len_from_poses(ego) if ego else 0.0
                brake_count = len(block["brakes"])
                duration = 0.0
                if first_ts is not None and last_ts is not None and last_ts > first_ts:
                    duration = (last_ts - first_ts) / 1e6
                off_collision = None if off_metrics is None else bool(off_metrics.get("any_collide@0.0s"))
                episode = {
                    "scenario_class": scenario_class,
                    "scenario_id": scenario_id,
                    "run_index": run_index,
                    "decision_reset_run": block.get("reset_run"),
                    "decision_frames": len(block["frames"]),
                    "brake_frame_count": brake_count,
                    "intervention_episode": brake_count > 0,
                    "first_brake_timestamp_us": first_ts,
                    "last_brake_timestamp_us": last_ts,
                    "brake_duration_s": duration,
                    "ego_distance_m": ego_distance,
                    "best_metric_present": metrics is not None,
                    "off_metric_present": off_metrics is not None,
                    "off_collision": off_collision,
                }
                episodes.append(episode)

                status = "no_best_brake"
                lead_time = None
                if brake_count > 0:
                    if off_metrics is None:
                        status = "missing_off_run"
                    else:
                        actors = tar_json(tar, f"p14-off/{scenario_class}-{scenario_id}/run_{run_index}/actors.json")
                        off_ego = tar_json(tar, f"p14-off/{scenario_class}-{scenario_id}/run_{run_index}/ego_poses.json")
                        contact = contact_ts_gt(actors or [], off_ego or {})
                        if contact is None:
                            status = "no_off_contact_crossing"
                        elif first_ts is None:
                            status = "malformed"
                        else:
                            status = "measured"
                            lead_time = (contact - first_ts) / 1e6
                lead_rows.append(
                    {
                        "scenario_class": scenario_class,
                        "scenario_id": scenario_id,
                        "run_index": run_index,
                        "status": status,
                        "lead_time_s": lead_time,
                    }
                )

    return {"pair_order": pair_order, "decision_blocks": len(blocks)}, episodes, lead_rows


def evaluate_s0(root: Path, tracked: set[str], best_gz: Path, off_gz: Path) -> dict[str, Any]:
    failures = path_failures(FROZEN_INPUTS, tracked, root)
    analysis = (root / "experiments/full14_power/proof/analysis_output.txt").read_text(errors="replace")
    if "H-P0: PASS" not in analysis:
        failures.append("hp0_not_pass")
    if "side       0921" not in analysis or "(n=19/20)" not in analysis:
        failures.append("side_0921_missing_off_n19_exception_not_recorded")

    with tarfile.open(root / "experiments/full14_power/proof/p14-runs.tar.gz") as tar:
        best_metrics = metric_paths(tar, "p14-best")
        off_metrics = metric_paths(tar, "p14-off")
        best_pairs = pairs_from_metrics(best_metrics)
        off_pairs = pairs_from_metrics(off_metrics)
    if len(best_metrics) != 400:
        failures.append(f"best_metrics_count={len(best_metrics)} != 400")
    if len(off_metrics) != 399:
        failures.append(f"off_metrics_count={len(off_metrics)} != 399")
    if len(best_pairs) != 20:
        failures.append(f"best_pair_count={len(best_pairs)} != 20")
    if len(off_pairs) != 20:
        failures.append(f"off_pair_count={len(off_pairs)} != 20")

    best_stats = decision_log_stats(best_gz)
    off_stats = decision_log_stats(off_gz)
    expected_best = {"resets": 400, "frames": 7835, "brake_rows": 1205}
    for key, expected in expected_best.items():
        if best_stats[key] != expected:
            failures.append(f"best_decision_{key}={best_stats[key]} != {expected}")
    if off_stats["resets"] == 399:
        failures.append("off_decision_resets_look_like_completed_episodes_expected_relaunch_history")

    pair_order = parse_pair_order(root / "experiments/full14_power/proof/sentinel-power14-merged.log")
    blocks = parse_decision_blocks(best_gz)
    if len(pair_order) != 20:
        failures.append(f"best_pair_marker_count={len(pair_order)} != 20")
    if len(blocks) != 400:
        failures.append(f"best_decision_block_count={len(blocks)} != 400")
    else:
        for pair_index in range(20):
            reset_runs = [blocks[pair_index * 20 + run]["reset_run"] for run in range(20)]
            if reset_runs != list(range(20)):
                failures.append(f"best_reset_run_order_pair_{pair_index}={reset_runs}")
                break

    return {
        "pass": not failures,
        "failures": failures,
        "best_decision_log_stats": best_stats,
        "off_decision_log_stats": off_stats,
        "best_metrics_count": len(best_metrics),
        "off_metrics_count": len(off_metrics),
        "best_pair_count": len(best_pairs),
        "off_pair_count": len(off_pairs),
    }


def evaluate_s1(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    if len(episodes) != 400:
        failures.append(f"episode_count={len(episodes)} != 400")
    if sum(1 for ep in episodes if ep["best_metric_present"]) != 400:
        failures.append("not_all_best_metrics_joined")
    if sum(1 for ep in episodes if ep["ego_distance_m"] > 0) != 400:
        failures.append("not_all_best_ego_paths_joined")
    pair_keys = {(ep["scenario_class"], ep["scenario_id"]) for ep in episodes}
    if len(pair_keys) != 20:
        failures.append(f"scenario_pair_count={len(pair_keys)} != 20")
    class_keys = {ep["scenario_class"] for ep in episodes}
    if class_keys != set(CLASSES):
        failures.append(f"class_coverage={sorted(class_keys)} != {list(CLASSES)}")
    off_collision_values = {ep["off_collision"] for ep in episodes}
    if True not in off_collision_values:
        failures.append("missing_off_collision_summary_support")
    if False not in off_collision_values:
        failures.append("missing_off_noncollision_summary_support")

    summary = summarize_episodes(episodes)
    by_class = {
        cls: summarize_episodes([ep for ep in episodes if ep["scenario_class"] == cls])
        for cls in CLASSES
    }
    by_pair = {
        f"{cls}-{sid}": summarize_episodes([ep for ep in episodes if ep["scenario_class"] == cls and ep["scenario_id"] == sid])
        for cls, sid in sorted(pair_keys)
    }
    by_off_collision = {
        str(key): summarize_episodes([ep for ep in episodes if ep["off_collision"] is key])
        for key in (True, False, None)
    }
    return {
        "pass": not failures,
        "failures": failures,
        "overall": summary,
        "by_class": by_class,
        "by_pair": by_pair,
        "by_off_collision": by_off_collision,
    }


def evaluate_s2(lead_rows: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    intervention_rows = [row for row in lead_rows if row["status"] != "no_best_brake"]
    measured = [row for row in lead_rows if row["status"] == "measured"]
    measured_values = [float(row["lead_time_s"]) for row in measured if row["lead_time_s"] is not None]
    measured_classes = {row["scenario_class"] for row in measured}
    if len(measured) < 20:
        failures.append(f"measured_leadtime_episodes={len(measured)} < 20")
    if len(measured_classes) < 2:
        failures.append(f"measured_leadtime_classes={len(measured_classes)} < 2")
    status_counts: dict[str, int] = {}
    excluded_by_class: dict[str, dict[str, int]] = {}
    for row in lead_rows:
        status = str(row["status"])
        status_counts[status] = status_counts.get(status, 0) + 1
        if status != "measured":
            cls = str(row["scenario_class"])
            excluded_by_class.setdefault(cls, {})
            excluded_by_class[cls][status] = excluded_by_class[cls].get(status, 0) + 1
    return {
        "pass": not failures,
        "failures": failures,
        "intervention_rows": len(intervention_rows),
        "measured_rows": len(measured),
        "measured_classes": sorted(measured_classes),
        "status_counts": status_counts,
        "excluded_by_class": excluded_by_class,
        "lead_time_summary_s": summarize(measured_values),
        "negative_lead_time_fraction": (
            sum(1 for value in measured_values if value < 0) / len(measured_values)
            if measured_values
            else None
        ),
    }


def evaluate_s3() -> dict[str, Any]:
    boundaries = [
        "simulation timestamp timing, not wall-clock inference latency",
        "brake-frame count is intervention budget, not passenger comfort or production cost",
        "full14/power safe-progress remains a tight null",
        "sensor degradation, adversarial perturbation, and real-world deployment trade-offs remain untested",
    ]
    return {"pass": True, "boundaries": boundaries, "failures": []}


def verdict(s0: dict[str, Any], s1: dict[str, Any] | None, s2: dict[str, Any] | None, s3: dict[str, Any] | None) -> str:
    if not s0["pass"]:
        return "TIMING_COST_INFRASTRUCTURE_NULL"
    if s1 is None or not s1["pass"]:
        return "TIMING_COST_NULL_COST_COVERAGE_INCOMPLETE"
    if s2 is None or not s2["pass"]:
        return "TIMING_COST_NULL_LEADTIME_COVERAGE_INCOMPLETE"
    if s3 is None or not s3["pass"]:
        return "TIMING_COST_OVERCLAIM_NULL"
    return "TIMING_COST_AUDIT_PASS_SIMULATION_SCOPE"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    tracked = git_tracked_paths(root)
    with tempfile.TemporaryDirectory(prefix="iter40_timing_cost_") as tmp_raw:
        tmp = Path(tmp_raw)
        best_gz = tmp / "sentinel_p14_best.jsonl.gz"
        off_gz = tmp / "sentinel_p14_off.jsonl.gz"
        best_sha = concat_parts(sorted((root / "experiments/full14_power/proof").glob("sentinel_p14_best.jsonl.gz.part-*")), best_gz)
        off_sha = concat_parts(sorted((root / "experiments/full14_power/proof").glob("sentinel_p14_off.jsonl.gz.part-*")), off_gz)

        s0 = evaluate_s0(root, tracked, best_gz, off_gz)
        episodes: list[dict[str, Any]] = []
        lead_rows: list[dict[str, Any]] = []
        if s0["pass"]:
            _, episodes, lead_rows = build_episode_table(root, best_gz)
        s1 = evaluate_s1(episodes) if s0["pass"] else None
        s2 = evaluate_s2(lead_rows) if s1 and s1["pass"] else None
        s3 = evaluate_s3() if s2 and s2["pass"] else None

    return {
        "verdict": verdict(s0, s1, s2, s3),
        "command_line": " ".join(sys.argv),
        "reconstructed_gzip_receipts": {
            "best_sha256": best_sha,
            "off_sha256": off_sha,
        },
        "s0": s0,
        "s1": s1,
        "s2": s2,
        "s3": s3,
        "episodes": episodes,
        "lead_time_rows": lead_rows,
        "claim_boundary": (
            "Decision-log timing is simulation timestamp timing, not wall-clock latency. "
            "Brake frames are an intervention-budget proxy, not passenger comfort, production cost, "
            "or deployment readiness."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--out", default="experiments/iter40_timing_cost_audit/proof-audit/timing_cost_report.json")
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
