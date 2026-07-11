#!/usr/bin/env python3
"""Iteration 44 offline velocity temporal-smoothing repair gate analyzer.

Imports the committed iteration-42 replay module (trace parsing, geometry, parameters) and the
committed iteration-43 perturbation module (perturbation layer, seed derivation, stability-bar
classifier). The ONLY registered modification is the object-velocity estimator inside the frame
rule, per the frozen variants and parameters in HYPOTHESIS.md; every other term mirrors the
iteration-42 implementation exactly, enforced by the S1 neutral-identity and S1b seed-paired
equivalence gates.
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
ITER42_ANALYZER = ROOT / "experiments/iter42_exact_trace_replay_support/analyze_trace_replay.py"
ITER43_DIR = ROOT / "experiments/iter43_object_stream_perturbation_gate"
ITER43_ANALYZER = ITER43_DIR / "analyze_object_perturbation.py"
ITER43_REPORT = ITER43_DIR / "proof-perturbation/object_perturbation_report.json"
TRACE_PATH = ROOT / "experiments/iter42_exact_trace_replay_support/proof-trace/sentinel_iter42_trace.jsonl.gz"
TRACE_SHA256 = "8c43726c94a8870d40518b97bf5b74a7b88517a661c16291dd8408a61eb97f4d"

RUN_ID = "iter44-velocity-smoothing-v1"

# Frozen estimator verdict cells: (kind, label, parameter).
ESTIMATOR_CELLS: list[tuple[str, str, float]] = [
    ("fd", "fd_k2", 2),
    ("fd", "fd_k3", 3),
    ("ema", "ema_a0p5", 0.5),
    ("ema", "ema_a0p3", 0.3),
]
# Neutral (raw-equivalent) cells, reserved for the S1/S1b identity gates only.
NEUTRAL_CELLS: list[tuple[str, str, float]] = [
    ("fd", "fd_k1", 1),
    ("ema", "ema_a1p0", 1.0),
]

# Frozen perturbation cells (family, level_label, parameter), reusing the iter43 grid labels.
V2_CELLS: list[tuple[str, str, float]] = [
    ("jitter", "sigma_0p05", 0.05),
    ("jitter", "sigma_0p10", 0.10),
]
V3_CELLS: list[tuple[str, str, float]] = [
    ("dropout", "p_0p05", 0.05),
    ("score", "f_0p90", 0.90),
    ("churn", "p_0p05", 0.05),
]
DOSE_CELLS: list[tuple[str, str, float]] = [
    ("jitter", "sigma_0p25", 0.25),
    ("jitter", "sigma_0p50", 0.50),
    ("jitter", "sigma_1p00", 1.00),
]
DETERMINISM_GUARD = ("fd_k2", "jitter", "sigma_0p10")

FIDELITY_BARS = {
    "retention_min": 225,
    "new_interventions_max": 4,
    "median_delay_max_frames": 1.0,
    "delay_gt2_fraction_max": 0.05,
    "brake_total_min": 1085,
    "brake_total_max": 1325,
}
S1B_FIELDS = (
    "retained_interventions",
    "lost_interventions",
    "new_interventions",
    "median_first_brake_delay_frames",
    "delay_gt2_fraction",
    "brake_frames",
    "release_frames",
    "brake_flips",
    "fired_flips",
)


def load_module(path: Path, name: str):
    spec = importlib_util.spec_from_file_location(name, path)
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


def frame_support_smoothed(
    iter42: Any,
    row: dict[str, Any],
    state: dict[Any, Any],
    kind: str,
    param: float,
) -> tuple[bool, dict[Any, Any], float, float]:
    """Iteration-42 frame rule with ONLY the velocity estimator replaced (see HYPOTHESIS.md)."""
    params = iter42.params_for_row(row)
    e2w = row["ego2world"]
    ts = int(row["ts"])
    plan = [iter42.transform_point(e2w, point) for point in row.get("traj") or []]
    objs = row.get("objs") or []
    scores = row.get("scores") or []
    ids = row.get("object_ids") or []
    min_cpa = 1e9
    min_ttc = 1e9
    ego_wx, ego_wy = float(e2w[0][3]), float(e2w[1][3])
    new_state: dict[Any, Any] = {}
    for i in range(min(len(objs), len(scores))):
        score = scores[i]
        if score is None or float(score) < float(params["SENTINEL_MIN_SCORE"]):
            continue
        ox, oy = float(objs[i][0]), float(objs[i][1])
        if math.hypot(ox, oy) > float(params["SENTINEL_MAXGAP"]):
            continue
        wx, wy = iter42.transform_point(e2w, (ox, oy))
        oid = ids[i] if i < len(ids) else f"idx_{i}"
        avx = avy = 0.0
        if kind == "fd":
            history = state.get(oid) or []
            if history:
                pwx, pwy, pts = history[0]
                dta = (ts - pts) / 1e6
                if dta > 1e-3:
                    avx, avy = (wx - pwx) / dta, (wy - pwy) / dta
            new_state[oid] = (history + [(wx, wy, ts)])[-int(param):]
        elif kind == "ema":
            prev = state.get(oid)
            if prev is None:
                new_state[oid] = (wx, wy, ts, 0.0, 0.0, False)
            else:
                pwx, pwy, pts, pvx, pvy, has_v = prev
                dta = (ts - pts) / 1e6
                if dta > 1e-3:
                    rvx, rvy = (wx - pwx) / dta, (wy - pwy) / dta
                    if has_v:
                        avx = param * rvx + (1.0 - param) * pvx
                        avy = param * rvy + (1.0 - param) * pvy
                    else:
                        avx, avy = rvx, rvy
                    new_state[oid] = (wx, wy, ts, avx, avy, True)
                else:
                    new_state[oid] = (wx, wy, ts, pvx, pvy, has_v)
        else:
            raise ValueError(f"unknown estimator kind: {kind}")
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
    return fired, new_state, min_cpa, min_ttc


def replay_block_smoothed(iter42: Any, block: dict[str, Any], kind: str, param: float) -> list[dict[str, Any]]:
    """Iteration-42 latch/release replay, verbatim, over the smoothed frame rule."""
    state: dict[Any, Any] = {}
    braking = False
    clear = 0
    replay_rows: list[dict[str, Any]] = []
    for frame in block["frames"]:
        params = iter42.params_for_row(frame)
        fired, state, min_cpa, min_ttc = frame_support_smoothed(iter42, frame, state, kind, param)
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


def replay_metrics_smoothed(
    iter42: Any,
    iter43: Any,
    blocks: list[dict[str, Any]],
    pair_labels: list[tuple[str, str]],
    kind: str,
    param: float,
    family: str | None,
    level: str,
    fam_param: float,
) -> dict[str, Any]:
    """Iteration-43 outcome measures, computed for the smoothed rule (optionally perturbed)."""
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
        perturbed = iter43.perturb_block(block, family, level, fam_param, cls, scenario)
        replayed = replay_block_smoothed(iter42, perturbed, kind, param)
        online = iter43.online_block_facts(block)
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
        "estimator": f"{kind}:{param}",
        "family": family,
        "level": level,
        "param": fam_param,
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


def classify_fidelity(metrics: dict[str, Any]) -> dict[str, Any]:
    """V1 baseline-fidelity bars (frozen in HYPOTHESIS.md; stricter than the iter43 bars)."""
    failed: list[str] = []
    if metrics["retained_interventions"] < FIDELITY_BARS["retention_min"]:
        failed.append(
            f"retention={metrics['retained_interventions']}/230 < {FIDELITY_BARS['retention_min']}"
        )
    if metrics["new_interventions"] > FIDELITY_BARS["new_interventions_max"]:
        failed.append(
            f"new_interventions={metrics['new_interventions']}/170"
            f" > {FIDELITY_BARS['new_interventions_max']}"
        )
    if metrics["median_first_brake_delay_frames"] is None:
        failed.append("median_delay_undefined_no_retained_interventions")
    elif metrics["median_first_brake_delay_frames"] > FIDELITY_BARS["median_delay_max_frames"]:
        failed.append(
            f"median_delay={metrics['median_first_brake_delay_frames']}"
            f" > {FIDELITY_BARS['median_delay_max_frames']}"
        )
    if metrics["delay_gt2_fraction"] is None:
        failed.append("delay_gt2_fraction_undefined_no_retained_interventions")
    elif metrics["delay_gt2_fraction"] > FIDELITY_BARS["delay_gt2_fraction_max"]:
        failed.append(
            f"delay_gt2_fraction={metrics['delay_gt2_fraction']:.6f}"
            f" > {FIDELITY_BARS['delay_gt2_fraction_max']}"
        )
    if not FIDELITY_BARS["brake_total_min"] <= metrics["brake_frames"] <= FIDELITY_BARS["brake_total_max"]:
        failed.append(
            f"brake_frames={metrics['brake_frames']} outside"
            f" [{FIDELITY_BARS['brake_total_min']}, {FIDELITY_BARS['brake_total_max']}]"
        )
    return {"classification": "PASS" if not failed else "FAIL", "failed_bars": failed}


def evaluate_s1(
    iter42: Any,
    iter43: Any,
    blocks: list[dict[str, Any]],
    pair_labels: list[tuple[str, str]],
) -> dict[str, Any]:
    """Both neutral estimator cells must reproduce the online decision stream exactly."""
    results: dict[str, Any] = {}
    all_pass = True
    for kind, label, param in NEUTRAL_CELLS:
        failures: list[str] = []
        total_brakes = total_releases = interventions = mismatches = 0
        for block_index, block in enumerate(blocks):
            cls, scenario = pair_labels[block_index]
            perturbed = iter43.perturb_block(block, None, "zero", 0.0, cls, scenario)
            replayed = replay_block_smoothed(iter42, perturbed, kind, param)
            block_brakes = 0
            for frame, replay in zip(block["frames"], replayed):
                for key in ("fired", "brake", "release", "post_braking", "post_clear"):
                    if frame.get(key) != replay[key]:
                        mismatches += 1
                        if len(failures) < 12:
                            failures.append(
                                f"block_{block_index}_frame_{frame.get('frame_index')}:{key}"
                            )
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
            if actual != iter43.ONLINE[key]:
                failures.append(f"{label}_{key}={actual} != {iter43.ONLINE[key]}")
        cell_pass = mismatches == 0 and not failures
        all_pass = all_pass and cell_pass
        results[label] = {
            "pass": cell_pass,
            "mismatched_frames": mismatches,
            "failures": failures,
            "brake_frames": total_brakes,
            "release_frames": total_releases,
            "intervention_episodes": interventions,
        }
    return {"pass": all_pass, "cells": results}


def evaluate_s1b(
    iter42: Any,
    iter43: Any,
    blocks: list[dict[str, Any]],
    pair_labels: list[tuple[str, str]],
) -> dict[str, Any]:
    """Neutral fd_k1 under the iter43 jitter cells must equal the committed iter43 numbers."""
    committed = json.loads(ITER43_REPORT.read_text())
    reference = {
        (cell["family"], cell["level"]): cell
        for cell in committed["cells"]
    }
    failures: list[str] = []
    cells: dict[str, Any] = {}
    for family, level, fam_param in V2_CELLS:
        metrics = replay_metrics_smoothed(
            iter42, iter43, blocks, pair_labels, "fd", 1, family, level, fam_param
        )
        ref = reference[(family, level)]
        diffs = [
            f"{field}: {metrics[field]} != {ref[field]}"
            for field in S1B_FIELDS
            if metrics[field] != ref[field]
        ]
        if diffs:
            failures.append(f"{family}:{level} -> {'; '.join(diffs)}")
        cells[f"{family}:{level}"] = {"metrics": metrics, "mismatched_fields": diffs}
    if committed.get("seed") != iter43.SEED:
        failures.append("committed_report_seed_mismatch")
    return {"pass": not failures, "failures": failures, "cells": cells}


def evaluate_s0(iter43: Any, tracked: set[str]) -> dict[str, Any]:
    required = [
        "experiments/iter44_velocity_smoothing_gate/HYPOTHESIS.md",
        "experiments/iter44_velocity_smoothing_gate/analyze_velocity_smoothing.py",
        "tests/test_iter44_velocity_smoothing.py",
        "experiments/iter42_exact_trace_replay_support/analyze_trace_replay.py",
        "experiments/iter42_exact_trace_replay_support/proof-trace/sentinel_iter42_trace.jsonl.gz",
        "experiments/iter42_exact_trace_replay_support/RESULT.md",
        "experiments/iter43_object_stream_perturbation_gate/analyze_object_perturbation.py",
        "experiments/iter43_object_stream_perturbation_gate/proof-perturbation/object_perturbation_report.json",
        "experiments/iter43_object_stream_perturbation_gate/RESULT.md",
    ]
    failures: list[str] = []
    for rel in required:
        if rel not in tracked:
            failures.append(f"untracked_required_path:{rel}")
        if not (ROOT / rel).exists():
            failures.append(f"missing_required_path:{rel}")
    iter42_result = (ROOT / required[5]).read_text(errors="replace")
    if "TRACE_REPLAY_SUPPORT_PASS" not in iter42_result:
        failures.append("iter42_verdict_not_TRACE_REPLAY_SUPPORT_PASS")
    iter43_result = (ROOT / required[8]).read_text(errors="replace")
    if "OBJECT_PERTURBATION_MILD_FRAGILE" not in iter43_result:
        failures.append("iter43_verdict_not_OBJECT_PERTURBATION_MILD_FRAGILE")
    if iter43.SEED != "iter43-object-stream-perturbation-v1":
        failures.append("iter43_seed_string_changed")
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
    iter42 = load_module(ITER42_ANALYZER, "iter42_trace_replay")
    iter43 = load_module(ITER43_ANALYZER, "iter43_object_perturbation")
    s0 = evaluate_s0(iter43, git_tracked_paths())
    report: dict[str, Any] = {
        "run_id": RUN_ID,
        "perturbation_seed": iter43.SEED,
        "command_line": " ".join(sys.argv),
        "fidelity_bars": FIDELITY_BARS,
        "robustness_bars": iter43.BARS,
        "online_reference": iter43.ONLINE,
        "estimator_cells": [label for _, label, _ in ESTIMATOR_CELLS],
        "s0": s0,
        "claim_boundary": (
            "Iteration 44 measures offline decision-replay behavior of a registered "
            "smoothed-velocity modification of the released-union monitor rule on the frozen "
            "iteration-42 trace. The released union itself is unchanged. This is not "
            "sensor/camera degradation, not closed-loop (consequences of changed decisions are "
            "not observable offline), and not a benchmark, NeuroNCAP-score, selector, "
            "deployment, or safety claim. A pass authorizes only a future closed-loop "
            "pre-registration."
        ),
    }
    if not s0["pass"]:
        report["verdict"] = "VELOCITY_SMOOTHING_STATIC_NULL"
        return report

    blocks = iter42.parse_trace_blocks(TRACE_PATH)
    pair_labels = [iter42.PAIR_ORDER[block_index // 20] for block_index in range(len(blocks))]

    s1 = evaluate_s1(iter42, iter43, blocks, pair_labels)
    report["s1"] = s1
    s1b = evaluate_s1b(iter42, iter43, blocks, pair_labels) if s1["pass"] else None
    report["s1b"] = s1b
    if not s1["pass"] or s1b is None or not s1b["pass"]:
        report["verdict"] = "VELOCITY_SMOOTHING_IDENTITY_NULL"
        report["trace_sha256_after"] = sha256_file(TRACE_PATH)
        return report

    cells: list[dict[str, Any]] = []
    guard_hashes: list[str] = []
    for kind, label, param in ESTIMATOR_CELLS:
        fidelity = replay_metrics_smoothed(
            iter42, iter43, blocks, pair_labels, kind, param, None, "unperturbed", 0.0
        )
        fidelity.update(classify_fidelity(fidelity))
        robustness: list[dict[str, Any]] = []
        for family, level, fam_param in V2_CELLS + V3_CELLS:
            metrics = replay_metrics_smoothed(
                iter42, iter43, blocks, pair_labels, kind, param, family, level, fam_param
            )
            metrics.update(iter43.classify_cell(metrics))
            robustness.append(metrics)
            if (label, family, level) == DETERMINISM_GUARD:
                guard_hashes.append(summary_hash(metrics))
                repeat = replay_metrics_smoothed(
                    iter42, iter43, blocks, pair_labels, kind, param, family, level, fam_param
                )
                repeat.update(iter43.classify_cell(repeat))
                guard_hashes.append(summary_hash(repeat))
        dose: list[dict[str, Any]] = []
        for family, level, fam_param in DOSE_CELLS:
            metrics = replay_metrics_smoothed(
                iter42, iter43, blocks, pair_labels, kind, param, family, level, fam_param
            )
            metrics.update(iter43.classify_cell(metrics))
            dose.append(metrics)
        v2_levels = {(cell["family"], cell["level"]) for cell in robustness
                     if cell["classification"] == "STABLE"}
        v1_pass = fidelity["classification"] == "PASS"
        v2_pass = all((family, level) in v2_levels for family, level, _ in V2_CELLS)
        v3_pass = all((family, level) in v2_levels for family, level, _ in V3_CELLS)
        cells.append(
            {
                "estimator": label,
                "kind": kind,
                "param": param,
                "fidelity": fidelity,
                "v1_pass": v1_pass,
                "robustness": robustness,
                "v2_pass": v2_pass,
                "v3_pass": v3_pass,
                "dose_response": dose,
                "passes_all": v1_pass and v2_pass and v3_pass,
            }
        )
    report["cells"] = cells
    report["determinism_guard"] = {
        "cell": ":".join(DETERMINISM_GUARD),
        "hashes": guard_hashes,
        "pass": len(guard_hashes) == 2 and guard_hashes[0] == guard_hashes[1],
    }
    report["trace_sha256_after"] = sha256_file(TRACE_PATH)
    if report["trace_sha256_after"] != TRACE_SHA256:
        report["verdict"] = "VELOCITY_SMOOTHING_STATIC_NULL"
        report["s0"]["failures"].append("trace_mutated_during_analysis")
        return report
    if not report["determinism_guard"]["pass"]:
        report["verdict"] = "VELOCITY_SMOOTHING_DETERMINISM_NULL"
        return report

    passing = [cell["estimator"] for cell in cells if cell["passes_all"]]
    v2_only = [cell["estimator"] for cell in cells if cell["v2_pass"]]
    report["passing_cells"] = passing
    report["v2_passing_cells"] = v2_only
    if passing:
        report["verdict"] = "VELOCITY_SMOOTHING_REPAIR_PASS"
    elif v2_only:
        report["verdict"] = "VELOCITY_SMOOTHING_TRADEOFF_NULL"
    else:
        report["verdict"] = "VELOCITY_SMOOTHING_NO_REPAIR_NULL"
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        default=str(
            ROOT
            / "experiments/iter44_velocity_smoothing_gate/proof-smoothing/velocity_smoothing_report.json"
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
