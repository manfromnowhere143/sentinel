#!/usr/bin/env python3
"""Iteration 42 exact trace replay analyzer."""

from __future__ import annotations

import argparse
import gzip
import json
import math
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TRACE_VERSION = "iter42_exact_trace_v1"
PAIR_ORDER = [
    ("stationary", "0099"),
    ("stationary", "0101"),
    ("stationary", "0103"),
    ("stationary", "0106"),
    ("stationary", "0108"),
    ("stationary", "0278"),
    ("stationary", "0331"),
    ("stationary", "0783"),
    ("stationary", "0796"),
    ("stationary", "0966"),
    ("frontal", "0103"),
    ("frontal", "0106"),
    ("frontal", "0110"),
    ("frontal", "0346"),
    ("frontal", "0923"),
    ("side", "0103"),
    ("side", "0108"),
    ("side", "0110"),
    ("side", "0278"),
    ("side", "0921"),
]
EXPECTED = {
    "pairs": 20,
    "resets": 400,
    "frames": 6474,
    "brake_frames": 1205,
    "release_frames": 156,
    "intervention_episodes": 230,
}
PARAMS = {
    "SENTINEL_MIN_SCORE": 0.3,
    "SENTINEL_MAXGAP": 30.0,
    "SENTINEL_CPA_MARGIN": 1.5,
    "SENTINEL_TTC": 2.5,
    "SENTINEL_MIN_CLOSING": 3.0,
    "SENTINEL_RELEASE_K": 4,
}


def git_tracked_paths(root: Path = ROOT) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return set(result.stdout.splitlines())


def iter_rows(path: Path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def parse_trace_blocks(path: Path) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    cur: dict[str, Any] | None = None
    for row in iter_rows(path):
        if row.get("reset"):
            cur = {"reset_run": row.get("run"), "frames": []}
            blocks.append(cur)
            continue
        if row.get("trace_version") != TRACE_VERSION:
            if cur is not None:
                cur.setdefault("non_trace_rows", []).append(row)
            continue
        if cur is None:
            cur = {"reset_run": None, "frames": []}
            blocks.append(cur)
        cur["frames"].append(row)
    return blocks


def parse_pair_order(log_path: Path) -> list[tuple[str, str]]:
    order: list[tuple[str, str]] = []
    for line in log_path.read_text(errors="replace").splitlines():
        match = re.match(r"##### I42PAIR trace (\w+) (\d+) #####", line)
        if match:
            order.append((match.group(1), match.group(2)))
    return order


def finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def valid_ego2world(matrix: Any) -> bool:
    return (
        isinstance(matrix, list)
        and len(matrix) == 4
        and all(isinstance(row, list) and len(row) == 4 for row in matrix)
        and all(finite_number(value) for row in matrix for value in row)
    )


def transform_point(matrix: list[list[float]], point: list[float] | tuple[float, float]) -> tuple[float, float]:
    x, y = float(point[0]), float(point[1])
    return (
        float(matrix[0][0]) * x + float(matrix[0][1]) * y + float(matrix[0][3]),
        float(matrix[1][0]) * x + float(matrix[1][1]) * y + float(matrix[1][3]),
    )


def params_for_row(row: dict[str, Any]) -> dict[str, float | int]:
    raw = row.get("params") or {}
    params: dict[str, float | int] = {}
    for key, default in PARAMS.items():
        value = raw.get(key, default)
        params[key] = int(value) if key == "SENTINEL_RELEASE_K" else float(value)
    return params


def frame_support(
    row: dict[str, Any],
    track: dict[Any, tuple[float, float, int]],
) -> tuple[bool, dict[Any, tuple[float, float, int]], float, float]:
    params = params_for_row(row)
    e2w = row["ego2world"]
    ts = int(row["ts"])
    plan = [transform_point(e2w, point) for point in row.get("traj") or []]
    objs = row.get("objs") or []
    scores = row.get("scores") or []
    ids = row.get("object_ids") or []
    min_cpa = 1e9
    min_ttc = 1e9
    ego_wx, ego_wy = float(e2w[0][3]), float(e2w[1][3])
    newtrack: dict[Any, tuple[float, float, int]] = {}
    for i in range(min(len(objs), len(scores))):
        score = scores[i]
        if score is None or float(score) < float(params["SENTINEL_MIN_SCORE"]):
            continue
        ox, oy = float(objs[i][0]), float(objs[i][1])
        if math.hypot(ox, oy) > float(params["SENTINEL_MAXGAP"]):
            continue
        wx, wy = transform_point(e2w, (ox, oy))
        oid = ids[i] if i < len(ids) else f"idx_{i}"
        newtrack[oid] = (wx, wy, ts)
        avx = avy = 0.0
        if oid in track:
            pwx, pwy, pts = track[oid]
            dta = (ts - pts) / 1e6
            if dta > 1e-3:
                avx, avy = (wx - pwx) / dta, (wy - pwy) / dta
        for k, (ex, ey) in enumerate(plan):
            t = (k + 1) * 0.5
            ax, ay = wx + avx * t, wy + avy * t
            min_cpa = min(min_cpa, math.hypot(ex - ax, ey - ay))
        dx, dy = ego_wx - wx, ego_wy - wy
        gapw = math.hypot(dx, dy)
        if gapw > 1e-3:
            closing = (avx * dx + avy * dy) / gapw
            if closing > max(float(params["SENTINEL_MIN_CLOSING"]), 0.5):
                min_ttc = min(min_ttc, gapw / closing)
    fired = min_cpa < float(params["SENTINEL_CPA_MARGIN"]) or min_ttc < float(params["SENTINEL_TTC"])
    return fired, newtrack, min_cpa, min_ttc


def replay_block(block: dict[str, Any]) -> list[dict[str, Any]]:
    track: dict[Any, tuple[float, float, int]] = {}
    braking = False
    clear = 0
    replay_rows: list[dict[str, Any]] = []
    for frame in block["frames"]:
        params = params_for_row(frame)
        fired, newtrack, min_cpa, min_ttc = frame_support(frame, track)
        track = newtrack
        release = False
        if fired:
            braking = True
            clear = 0
        elif braking:
            clear += 1
            if clear >= int(params["SENTINEL_RELEASE_K"]):
                braking = False
                clear = 0
                release = True
        replay_rows.append(
            {
                "frame_index": int(frame["frame_index"]),
                "fired": fired,
                "brake": braking,
                "release": release,
                "post_braking": braking,
                "post_clear": clear,
                "min_cpa": min_cpa,
                "min_ttc": min_ttc,
            }
        )
    return replay_rows


def field_failures(row: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for key in ("run", "frame_index", "ts", "traj", "objs", "scores", "ego2world", "params"):
        if key not in row:
            failures.append(f"missing_{key}")
    if "ego2world" in row and not valid_ego2world(row["ego2world"]):
        failures.append("bad_ego2world")
    for key in ("min_cpa", "min_ttc"):
        if key in row and not finite_number(row[key]):
            failures.append(f"bad_{key}")
    if "objs" in row and "scores" in row and len(row.get("objs") or []) < len(row.get("scores") or []):
        failures.append("scores_longer_than_objs")
    params = row.get("params") or {}
    for key, expected in PARAMS.items():
        if key not in params:
            failures.append(f"missing_param_{key}")
        elif abs(float(params[key]) - float(expected)) > 1e-9:
            failures.append(f"param_{key}={params[key]} != {expected}")
    forbidden = ("camera", "image", "sample_token", "scene_token", "lidar_token")
    for key in row:
        if any(token in str(key).lower() for token in forbidden):
            failures.append(f"forbidden_field_{key}")
    return failures


def summarize_blocks(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    frames = [frame for block in blocks for frame in block["frames"]]
    brake_frames = sum(1 for frame in frames if frame.get("brake") is True)
    release_frames = sum(1 for frame in frames if frame.get("release") is True)
    intervention_episodes = sum(1 for block in blocks if any(frame.get("brake") for frame in block["frames"]))
    field_failure_examples: list[dict[str, Any]] = []
    field_failure_count = 0
    for block_index, block in enumerate(blocks):
        for frame in block["frames"]:
            failures = field_failures(frame)
            if failures:
                field_failure_count += 1
                if len(field_failure_examples) < 12:
                    field_failure_examples.append(
                        {
                            "block_index": block_index,
                            "run": frame.get("run"),
                            "frame_index": frame.get("frame_index"),
                            "failures": failures,
                        }
                    )
    return {
        "resets": len(blocks),
        "frames": len(frames),
        "brake_frames": brake_frames,
        "release_frames": release_frames,
        "intervention_episodes": intervention_episodes,
        "field_failure_count": field_failure_count,
        "field_failure_examples": field_failure_examples,
    }


def evaluate_s1(blocks: list[dict[str, Any]], pair_order: list[tuple[str, str]]) -> dict[str, Any]:
    summary = summarize_blocks(blocks)
    failures: list[str] = []
    if pair_order and pair_order != PAIR_ORDER:
        failures.append("pair_order_mismatch")
    if pair_order and len(pair_order) != EXPECTED["pairs"]:
        failures.append(f"pair_count={len(pair_order)} != {EXPECTED['pairs']}")
    for key in ("resets", "frames", "brake_frames", "release_frames", "intervention_episodes"):
        if summary[key] != EXPECTED[key]:
            failures.append(f"{key}={summary[key]} != {EXPECTED[key]}")
    if summary["field_failure_count"]:
        failures.append(f"field_failure_count={summary['field_failure_count']}")
    if len(blocks) == EXPECTED["resets"]:
        for pair_index in range(EXPECTED["pairs"]):
            reset_runs = [blocks[pair_index * 20 + run]["reset_run"] for run in range(20)]
            if reset_runs != list(range(20)):
                failures.append(f"reset_run_order_pair_{pair_index}={reset_runs}")
                break
    return {"pass": not failures, "failures": failures, "summary": summary, "pair_order": pair_order}


def compare_replay(blocks: list[dict[str, Any]]) -> dict[str, Any]:
    failures: list[str] = []
    examples: list[dict[str, Any]] = []
    total_brakes = total_releases = interventions = 0
    for block_index, block in enumerate(blocks):
        replayed = replay_block(block)
        block_brakes = 0
        online_release_indices = []
        replay_release_indices = []
        for frame, replay in zip(block["frames"], replayed):
            if replay["brake"]:
                block_brakes += 1
            if frame.get("release") is True:
                online_release_indices.append(int(frame["frame_index"]))
            if replay["release"]:
                replay_release_indices.append(int(replay["frame_index"]))
            mismatched = [
                key
                for key in ("fired", "brake", "release", "post_braking", "post_clear")
                if frame.get(key) != replay[key]
            ]
            if mismatched:
                failures.append(f"block_{block_index}_frame_{frame.get('frame_index')}:{','.join(mismatched)}")
                if len(examples) < 12:
                    examples.append(
                        {
                            "block_index": block_index,
                            "frame_index": frame.get("frame_index"),
                            "mismatched_fields": mismatched,
                            "online": {key: frame.get(key) for key in mismatched},
                            "replay": {key: replay[key] for key in mismatched},
                        }
                    )
        total_brakes += block_brakes
        total_releases += len(replay_release_indices)
        if block_brakes > 0:
            interventions += 1
        if online_release_indices != replay_release_indices:
            failures.append(f"block_{block_index}_release_indices_mismatch")
    for key, actual in (
        ("brake_frames", total_brakes),
        ("release_frames", total_releases),
        ("intervention_episodes", interventions),
    ):
        if actual != EXPECTED[key]:
            failures.append(f"replay_{key}={actual} != {EXPECTED[key]}")
    return {
        "pass": not failures,
        "failures": failures[:24],
        "failure_count": len(failures),
        "mismatch_examples": examples,
        "replay_brake_frames": total_brakes,
        "replay_release_frames": total_releases,
        "replay_intervention_episodes": interventions,
    }


def evaluate_s0(root: Path, tracked: set[str]) -> dict[str, Any]:
    required = [
        "experiments/iter42_exact_trace_replay_support/HYPOTHESIS.md",
        "experiments/iter42_exact_trace_replay_support/server_patch_union_trace.py",
        "experiments/iter42_exact_trace_replay_support/iter42_trace_run.sh",
        "experiments/iter42_exact_trace_replay_support/analyze_trace_replay.py",
        "tests/test_iter42_trace_replay.py",
    ]
    failures: list[str] = []
    for rel in required:
        if rel not in tracked:
            failures.append(f"untracked_required_path:{rel}")
        if not (root / rel).exists():
            failures.append(f"missing_required_path:{rel}")
    patch = (root / required[1]).read_text(errors="replace")
    run_script = (root / required[2]).read_text(errors="replace")
    for needle in (
        "SENTINEL_MIN_SCORE",
        "SENTINEL_MAXGAP",
        "SENTINEL_CPA_MARGIN",
        "SENTINEL_TTC",
        "SENTINEL_MIN_CLOSING",
        "SENTINEL_RELEASE_K",
        "ego2world",
        "iter42_exact_trace_v1",
    ):
        if needle not in patch:
            failures.append(f"patch_missing_{needle}")
    active_run_script = "\n".join(
        line for line in run_script.splitlines() if not line.lstrip().startswith("#")
    )
    if re.search(r"for arm in .*off", active_run_script):
        failures.append("run_script_mentions_off_arm_loop")
    if "SENTINEL_ENABLED=0" in active_run_script:
        failures.append("run_script_can_disable_sentinel")
    for forbidden in ("PERTURB", "dropout", "jitter", "selector", "heldout"):
        if forbidden.lower() in active_run_script.lower():
            failures.append(f"run_script_forbidden_word:{forbidden}")
    return {"pass": not failures, "failures": failures, "required_paths": required}


def evaluate_s3() -> dict[str, Any]:
    return {
        "pass": True,
        "failures": [],
        "claim_boundary": (
            "Iteration 42 is trace-support evidence only: no perturbation, sensor degradation, "
            "benchmark, selector, deployment, or safety claim is authorized."
        ),
    }


def verdict(
    s0: dict[str, Any],
    s1: dict[str, Any] | None,
    s2: dict[str, Any] | None,
    s3: dict[str, Any] | None,
) -> str:
    if not s0["pass"]:
        return "TRACE_REPLAY_STATIC_OR_PREFLIGHT_NULL"
    if s1 is None or not s1["pass"]:
        return "TRACE_REPLAY_CAPTURE_NULL"
    if s2 is None or not s2["pass"]:
        return "TRACE_REPLAY_IDENTITY_NULL"
    if s3 is None or not s3["pass"]:
        return "TRACE_REPLAY_OVERCLAIM_NULL"
    return "TRACE_REPLAY_SUPPORT_PASS"


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    root = Path(args.root).resolve()
    tracked = git_tracked_paths(root)
    s0 = evaluate_s0(root, tracked)
    s1 = s2 = s3 = None
    blocks: list[dict[str, Any]] = []
    if args.trace:
        blocks = parse_trace_blocks(Path(args.trace))
        pair_order = parse_pair_order(Path(args.log)) if args.log else []
        s1 = evaluate_s1(blocks, pair_order) if s0["pass"] else None
        s2 = compare_replay(blocks) if s1 and s1["pass"] else None
        s3 = evaluate_s3() if s2 and s2["pass"] else None
    return {
        "verdict": verdict(s0, s1, s2, s3),
        "command_line": " ".join(sys.argv),
        "s0": s0,
        "s1": s1,
        "s2": s2,
        "s3": s3,
        "trace_blocks": len(blocks),
        "claim_boundary": (
            "Trace replay support is a substrate result only. It is not degradation robustness, "
            "closed-loop safety, selector evidence, deployment readiness, or production evidence."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--trace", default="")
    parser.add_argument("--log", default="")
    parser.add_argument(
        "--out",
        default="experiments/iter42_exact_trace_replay_support/proof-trace/trace_replay_report.json",
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
