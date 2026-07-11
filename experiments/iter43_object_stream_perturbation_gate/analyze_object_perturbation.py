#!/usr/bin/env python3
"""Iteration 43 offline object-stream perturbation gate analyzer.

Reuses the committed iteration-42 replay implementation (frame_support/replay_block) for every
replay. Perturbations touch only the logged objs/scores/effective object identities, per the
frozen grid and seed in HYPOTHESIS.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import subprocess
import sys
from importlib import util as importlib_util
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ITER42_DIR = ROOT / "experiments/iter42_exact_trace_replay_support"
ITER42_ANALYZER = ITER42_DIR / "analyze_trace_replay.py"
TRACE_PATH = ITER42_DIR / "proof-trace/sentinel_iter42_trace.jsonl.gz"
TRACE_SHA256 = "8c43726c94a8870d40518b97bf5b74a7b88517a661c16291dd8408a61eb97f4d"

SEED = "iter43-object-stream-perturbation-v1"

# Frozen grid: (family, level_label, parameter).
GRID: list[tuple[str, str, float]] = [
    ("jitter", "sigma_0p05", 0.05),
    ("jitter", "sigma_0p10", 0.10),
    ("jitter", "sigma_0p25", 0.25),
    ("jitter", "sigma_0p50", 0.50),
    ("jitter", "sigma_1p00", 1.00),
    ("dropout", "p_0p05", 0.05),
    ("dropout", "p_0p10", 0.10),
    ("dropout", "p_0p20", 0.20),
    ("score", "f_0p90", 0.90),
    ("score", "f_0p80", 0.80),
    ("score", "f_0p60", 0.60),
    ("churn", "p_0p05", 0.05),
    ("churn", "p_0p10", 0.10),
    ("churn", "p_0p20", 0.20),
]
MILD_CELLS = {
    ("jitter", "sigma_0p05"),
    ("jitter", "sigma_0p10"),
    ("dropout", "p_0p05"),
    ("score", "f_0p90"),
    ("churn", "p_0p05"),
}
DETERMINISM_GUARD_CELL = ("jitter", "sigma_0p25")

ONLINE = {
    "frames": 6474,
    "resets": 400,
    "brake_frames": 1205,
    "release_frames": 156,
    "intervention_episodes": 230,
    "non_intervention_episodes": 170,
}
BARS = {
    "retention_min": 219,
    "new_interventions_max": 8,
    "median_delay_max_frames": 1.0,
    "delay_gt2_fraction_max": 0.10,
    "brake_total_min": 1025,
    "brake_total_max": 1385,
}


def load_iter42_module():
    spec = importlib_util.spec_from_file_location("iter42_trace_replay", ITER42_ANALYZER)
    assert spec is not None and spec.loader is not None
    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def uniform_from_hash(*parts: Any) -> float:
    payload = "|".join(str(part) for part in parts)
    raw = int.from_bytes(hashlib.sha256(payload.encode()).digest()[:8], "big")
    return (raw + 1) / 2**64  # in (0, 1], safe for log()


def gaussian_from_hash(*parts: Any) -> float:
    u1 = uniform_from_hash(*parts, "u1")
    u2 = uniform_from_hash(*parts, "u2")
    return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)


def considered_objects(frame: dict[str, Any]) -> list[tuple[list[float], Any, Any]]:
    """Materialize the (object, score, effective id) triples the rule considers."""
    objs = frame.get("objs") or []
    scores = frame.get("scores") or []
    ids = frame.get("object_ids") or []
    triples = []
    for i in range(min(len(objs), len(scores))):
        oid = ids[i] if i < len(ids) else f"idx_{i}"
        triples.append((list(objs[i]), scores[i], oid))
    return triples


def perturb_frame(
    frame: dict[str, Any],
    family: str | None,
    level: str,
    param: float,
    cls: str,
    scenario: str,
) -> dict[str, Any]:
    run = frame.get("run")
    fidx = frame.get("frame_index")
    objs: list[list[float]] = []
    scores: list[Any] = []
    ids: list[Any] = []
    for i, (obj, score, oid) in enumerate(considered_objects(frame)):
        key = (SEED, family, level, cls, scenario, run, fidx, i)
        if family == "dropout" and uniform_from_hash(*key, "drop") < param:
            continue
        if family == "jitter":
            obj[0] = float(obj[0]) + param * gaussian_from_hash(*key, "x")
            obj[1] = float(obj[1]) + param * gaussian_from_hash(*key, "y")
        elif family == "score" and score is not None:
            score = float(score) * param
        elif family == "churn" and uniform_from_hash(*key, "churn") < param:
            oid = f"churn_{cls}_{scenario}_{run}_{fidx}_{i}"
        objs.append(obj)
        scores.append(score)
        ids.append(oid)
    return {**frame, "objs": objs, "scores": scores, "object_ids": ids}


def perturb_block(
    block: dict[str, Any],
    family: str | None,
    level: str,
    param: float,
    cls: str,
    scenario: str,
) -> dict[str, Any]:
    return {
        "frames": [perturb_frame(frame, family, level, param, cls, scenario) for frame in block["frames"]]
    }


def online_block_facts(block: dict[str, Any]) -> dict[str, Any]:
    first_brake = None
    brakes = 0
    for frame in block["frames"]:
        if frame.get("brake") is True:
            brakes += 1
            if first_brake is None:
                first_brake = int(frame["frame_index"])
    return {"brake_frames": brakes, "first_brake": first_brake}


def replay_metrics(
    module: Any,
    blocks: list[dict[str, Any]],
    pair_labels: list[tuple[str, str]],
    family: str | None,
    level: str,
    param: float,
) -> dict[str, Any]:
    retained = 0
    lost = 0
    new_interventions = 0
    delays: list[int] = []
    total_brakes = 0
    total_releases = 0
    brake_flips = 0
    fired_flips = 0
    for block_index, block in enumerate(blocks):
        cls, scenario = pair_labels[block_index]
        perturbed = perturb_block(block, family, level, param, cls, scenario)
        replayed = module.replay_block(perturbed)
        online = online_block_facts(block)
        first_brake = None
        block_brakes = 0
        for frame, replay in zip(block["frames"], replayed):
            if replay["brake"]:
                block_brakes += 1
                if first_brake is None:
                    first_brake = int(replay["frame_index"])
            if replay["release"]:
                total_releases += 1
            if bool(frame.get("brake")) != replay["brake"]:
                brake_flips += 1
            if bool(frame.get("fired")) != replay["fired"]:
                fired_flips += 1
        total_brakes += block_brakes
        if online["first_brake"] is not None:
            if first_brake is not None:
                retained += 1
                delays.append(first_brake - online["first_brake"])
            else:
                lost += 1
        elif first_brake is not None:
            new_interventions += 1
    median_delay = statistics.median(delays) if delays else None
    delay_gt2_fraction = (sum(1 for d in delays if d > 2) / len(delays)) if delays else None
    return {
        "family": family,
        "level": level,
        "param": param,
        "retained_interventions": retained,
        "lost_interventions": lost,
        "new_interventions": new_interventions,
        "median_first_brake_delay_frames": median_delay,
        "delay_gt2_fraction": delay_gt2_fraction,
        "brake_frames": total_brakes,
        "release_frames": total_releases,
        "brake_flips": brake_flips,
        "fired_flips": fired_flips,
    }


def classify_cell(metrics: dict[str, Any]) -> dict[str, Any]:
    failed: list[str] = []
    if metrics["retained_interventions"] < BARS["retention_min"]:
        failed.append(
            f"retention={metrics['retained_interventions']}/{ONLINE['intervention_episodes']}"
            f" < {BARS['retention_min']}"
        )
    if metrics["new_interventions"] > BARS["new_interventions_max"]:
        failed.append(
            f"new_interventions={metrics['new_interventions']}/{ONLINE['non_intervention_episodes']}"
            f" > {BARS['new_interventions_max']}"
        )
    if metrics["median_first_brake_delay_frames"] is None:
        failed.append("median_delay_undefined_no_retained_interventions")
    elif metrics["median_first_brake_delay_frames"] > BARS["median_delay_max_frames"]:
        failed.append(
            f"median_delay={metrics['median_first_brake_delay_frames']}"
            f" > {BARS['median_delay_max_frames']}"
        )
    if metrics["delay_gt2_fraction"] is None:
        failed.append("delay_gt2_fraction_undefined_no_retained_interventions")
    elif metrics["delay_gt2_fraction"] > BARS["delay_gt2_fraction_max"]:
        failed.append(
            f"delay_gt2_fraction={metrics['delay_gt2_fraction']:.6f}"
            f" > {BARS['delay_gt2_fraction_max']}"
        )
    if not BARS["brake_total_min"] <= metrics["brake_frames"] <= BARS["brake_total_max"]:
        failed.append(
            f"brake_frames={metrics['brake_frames']} outside"
            f" [{BARS['brake_total_min']}, {BARS['brake_total_max']}]"
        )
    return {"classification": "STABLE" if not failed else "FRAGILE", "failed_bars": failed}


def evaluate_s1(module: Any, blocks: list[dict[str, Any]], pair_labels: list[tuple[str, str]]) -> dict[str, Any]:
    """Zero-strength identity through the perturbation-capable input path."""
    failures: list[str] = []
    total_brakes = total_releases = interventions = mismatches = 0
    for block_index, block in enumerate(blocks):
        cls, scenario = pair_labels[block_index]
        perturbed = perturb_block(block, None, "zero", 0.0, cls, scenario)
        replayed = module.replay_block(perturbed)
        block_brakes = 0
        for frame, replay in zip(block["frames"], replayed):
            for key in ("fired", "brake", "release", "post_braking", "post_clear"):
                if frame.get(key) != replay[key]:
                    mismatches += 1
                    if len(failures) < 12:
                        failures.append(f"block_{block_index}_frame_{frame.get('frame_index')}:{key}")
                    break
            if replay["brake"]:
                block_brakes += 1
            if replay["release"]:
                total_releases += 1
        total_brakes += block_brakes
        if block_brakes:
            interventions += 1
    for key, actual in (
        ("brake_frames", total_brakes),
        ("release_frames", total_releases),
        ("intervention_episodes", interventions),
    ):
        if actual != ONLINE[key]:
            failures.append(f"zero_strength_{key}={actual} != {ONLINE[key]}")
    if len(blocks) != ONLINE["resets"]:
        failures.append(f"blocks={len(blocks)} != {ONLINE['resets']}")
    frames = sum(len(block["frames"]) for block in blocks)
    if frames != ONLINE["frames"]:
        failures.append(f"frames={frames} != {ONLINE['frames']}")
    return {
        "pass": mismatches == 0 and not failures,
        "mismatched_frames": mismatches,
        "failures": failures,
        "zero_strength_brake_frames": total_brakes,
        "zero_strength_release_frames": total_releases,
        "zero_strength_intervention_episodes": interventions,
    }


def evaluate_s0(tracked: set[str]) -> dict[str, Any]:
    required = [
        "experiments/iter43_object_stream_perturbation_gate/HYPOTHESIS.md",
        "experiments/iter43_object_stream_perturbation_gate/analyze_object_perturbation.py",
        "tests/test_iter43_object_perturbation.py",
        "experiments/iter42_exact_trace_replay_support/analyze_trace_replay.py",
        "experiments/iter42_exact_trace_replay_support/proof-trace/sentinel_iter42_trace.jsonl.gz",
        "experiments/iter42_exact_trace_replay_support/RESULT.md",
    ]
    failures: list[str] = []
    for rel in required:
        if rel not in tracked:
            failures.append(f"untracked_required_path:{rel}")
        if not (ROOT / rel).exists():
            failures.append(f"missing_required_path:{rel}")
    result_text = (ITER42_DIR / "RESULT.md").read_text(errors="replace")
    if "TRACE_REPLAY_SUPPORT_PASS" not in result_text:
        failures.append("iter42_verdict_not_TRACE_REPLAY_SUPPORT_PASS")
    trace_sha = sha256_file(TRACE_PATH)
    if trace_sha != TRACE_SHA256:
        failures.append(f"trace_sha256={trace_sha} != {TRACE_SHA256}")
    return {"pass": not failures, "failures": failures, "trace_sha256_before": trace_sha}


def git_tracked_paths() -> set[str]:
    result = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return set(result.stdout.splitlines())


def summary_hash(metrics: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(metrics, sort_keys=True).encode()).hexdigest()


def build_report() -> dict[str, Any]:
    module = load_iter42_module()
    s0 = evaluate_s0(git_tracked_paths())
    report: dict[str, Any] = {
        "seed": SEED,
        "command_line": " ".join(sys.argv),
        "bars": BARS,
        "online_reference": ONLINE,
        "mild_cells": sorted(f"{family}:{level}" for family, level in MILD_CELLS),
        "s0": s0,
        "claim_boundary": (
            "Iteration 43 measures replay decision-flip sensitivity of the released-union monitor "
            "rule on the frozen iteration-42 trace. It is not sensor/camera degradation, not "
            "closed-loop (consequences of changed decisions are not observable offline), and not a "
            "benchmark, selector, deployment, or safety claim."
        ),
    }
    if not s0["pass"]:
        report["verdict"] = "OBJECT_PERTURBATION_STATIC_NULL"
        return report

    blocks = module.parse_trace_blocks(TRACE_PATH)
    pair_labels = [module.PAIR_ORDER[block_index // 20] for block_index in range(len(blocks))]
    logged_ids_present = any(
        frame.get("object_ids") for block in blocks for frame in block["frames"]
    )
    report["logged_ids_present"] = logged_ids_present

    s1 = evaluate_s1(module, blocks, pair_labels)
    report["s1"] = s1
    if not s1["pass"]:
        report["verdict"] = "OBJECT_PERTURBATION_IDENTITY_NULL"
        report["trace_sha256_after"] = sha256_file(TRACE_PATH)
        return report

    cells: list[dict[str, Any]] = []
    guard_hashes: list[str] = []
    for family, level, param in GRID:
        metrics = replay_metrics(module, blocks, pair_labels, family, level, param)
        metrics.update(classify_cell(metrics))
        metrics["mild"] = (family, level) in MILD_CELLS
        cells.append(metrics)
        if (family, level) == DETERMINISM_GUARD_CELL:
            guard_hashes.append(summary_hash({k: v for k, v in metrics.items() if k != "mild"}))
            repeat = replay_metrics(module, blocks, pair_labels, family, level, param)
            repeat.update(classify_cell(repeat))
            guard_hashes.append(summary_hash(repeat))
    report["cells"] = cells
    report["determinism_guard"] = {
        "cell": f"{DETERMINISM_GUARD_CELL[0]}:{DETERMINISM_GUARD_CELL[1]}",
        "hashes": guard_hashes,
        "pass": len(guard_hashes) == 2 and guard_hashes[0] == guard_hashes[1],
    }
    report["trace_sha256_after"] = sha256_file(TRACE_PATH)
    if report["trace_sha256_after"] != TRACE_SHA256:
        report["verdict"] = "OBJECT_PERTURBATION_STATIC_NULL"
        report["s0"]["failures"].append("trace_mutated_during_analysis")
        return report
    if not report["determinism_guard"]["pass"]:
        report["verdict"] = "OBJECT_PERTURBATION_DETERMINISM_NULL"
        return report

    mild_fragile = [
        f"{cell['family']}:{cell['level']}"
        for cell in cells
        if cell["mild"] and cell["classification"] == "FRAGILE"
    ]
    report["mild_fragile_cells"] = mild_fragile
    report["verdict"] = (
        "OBJECT_PERTURBATION_MILD_STABLE_PASS" if not mild_fragile else "OBJECT_PERTURBATION_MILD_FRAGILE"
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default=str(
            ROOT
            / "experiments/iter43_object_stream_perturbation_gate/proof-perturbation/object_perturbation_report.json"
        ),
    )
    args = parser.parse_args()
    report = build_report()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"verdict": report["verdict"], "out": str(out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
