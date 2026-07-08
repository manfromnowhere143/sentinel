#!/usr/bin/env python3
"""Build the iteration-31 bridge-centroid direction and replay row manifests.

This script is offline-only. It reads the committed iteration-29 extraction
proof and iteration-30 localization report, validates the registered inputs,
then writes the fit-only benign-centroid direction required by the iter31
pre-registration. It does not contact gcloud, a GPU, NeuroNCAP, or UniAD.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
ITER29 = ROOT / "experiments/iter29_trainval_risk_support_atlas"
ITER30 = ROOT / "experiments/iter30_full_trainval_lowdiv_localization"
ITER31 = ROOT / "experiments/iter31_full_trainval_bridge_intervention"
JOIN_KEY = ("scene", "sample_index", "timestamp_us")
ALLOWED_ITER30_VERDICT = "LOCALIZATION_PASS_SUCCESSOR_PREREG_AUTHORIZED"


def load_iter30_module():
    script = ITER30 / "analyze_localization.py"
    spec = importlib.util.spec_from_file_location("iter30_localization", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def default_extract_parts() -> list[Path]:
    return sorted((ITER29 / "proof-full-extract").glob("sentinel_e29_stage1.jsonl.gz.part-*"))


def key_tuple(row: dict) -> tuple:
    return tuple(row[name] for name in JOIN_KEY)


def label_name(row: dict) -> str:
    return "eligible_lowdiv" if int(row["label"]) == 1 else "benign_control"


def stable_row(row: dict) -> dict:
    return {
        "scene": row["scene"],
        "split": row["split"],
        "sample_index": int(row["sample_index"]),
        "timestamp_us": int(row["timestamp_us"]),
        "label": int(row["label"]),
        "label_name": label_name(row),
        "baseline_closest_gap": float(row["closest_gap"]),
        "baseline_endpoint_spread": float(row["endpoint_spread"]),
    }


def sorted_rows(rows: list[dict]) -> list[dict]:
    return sorted(rows, key=key_tuple)


def array_digest(module, *arrays: np.ndarray) -> str:
    return module.array_digest(*arrays)


def derive_direction(module, rows: list[dict]) -> tuple[dict, dict[str, np.ndarray]]:
    fit_rows = [row for row in rows if row["split"] == "fit"]
    fit_pos = [row for row in fit_rows if int(row["label"]) == 1]
    fit_benign = [row for row in fit_rows if int(row["label"]) == 0]
    if not fit_pos or not fit_benign:
        raise ValueError(
            f"fit split must contain both classes, got pos={len(fit_pos)} benign={len(fit_benign)}"
        )

    x_fit = np.vstack([module.internal_features(row) for row in fit_rows]).astype(np.float64)
    y_fit = np.asarray([int(row["label"]) for row in fit_rows], dtype=np.int64)
    fit_mean = x_fit.mean(axis=0)
    fit_std = x_fit.std(axis=0)
    keep = fit_std > 1e-12
    if not np.any(keep):
        raise ValueError("all bridge features are constant on fit split")

    x_std = (x_fit[:, keep] - fit_mean[keep]) / fit_std[keep]
    mu_pos_std = x_std[y_fit == 1].mean(axis=0)
    mu_benign_std = x_std[y_fit == 0].mean(axis=0)
    direction_std_keep = mu_benign_std - mu_pos_std

    direction_raw = np.zeros(x_fit.shape[1], dtype=np.float64)
    direction_std_full = np.zeros(x_fit.shape[1], dtype=np.float64)
    direction_raw[keep] = direction_std_keep * fit_std[keep]
    direction_std_full[keep] = direction_std_keep

    digest = array_digest(
        module,
        direction_raw.astype(np.float32),
        fit_mean.astype(np.float32),
        fit_std.astype(np.float32),
        keep.astype(np.uint8),
    )
    artifact = {
        "stage": "iter31_full_trainval_bridge_intervention",
        "source": "fit_split_benign_centroid_minus_eligible_lowdiv_centroid",
        "feature_order": "flatten(sdc_traj_query_last) || flatten(sdc_track_query)",
        "feature_count": int(x_fit.shape[1]),
        "sdc_traj_query_last_values": 1536,
        "sdc_track_query_values": 256,
        "fit_rows": int(len(fit_rows)),
        "fit_eligible_lowdiv_rows": int(len(fit_pos)),
        "fit_benign_control_rows": int(len(fit_benign)),
        "dropped_dimension_count": int((~keep).sum()),
        "kept_dimension_count": int(keep.sum()),
        "direction_std_l2": float(np.linalg.norm(direction_std_keep)),
        "direction_raw_l2": float(np.linalg.norm(direction_raw)),
        "direction_and_fit_stats_sha256": digest,
        "constant_dimension_indices": np.flatnonzero(~keep).astype(int).tolist(),
        "direction_raw": direction_raw.astype(float).tolist(),
    }
    arrays = {
        "fit_mean": fit_mean,
        "fit_std": fit_std,
        "keep": keep,
        "direction_raw": direction_raw,
        "direction_std": direction_std_full,
    }
    return artifact, arrays


def validate_inputs(module, args: argparse.Namespace) -> tuple[list[dict], dict]:
    parts = [Path(part) for part in args.extract_part]
    if not parts:
        raise SystemExit("no extraction part files found")
    hash_report = module.validate_hashes(parts, Path(args.gt), Path(args.sha256s))
    report_failures = module.validate_reports(Path(args.s0_report), Path(args.label_atlas_report))
    task_rows, build_report, _meta = module.build_rows(parts, Path(args.gt))
    failures = module.s0_failures(hash_report, report_failures, build_report)

    iter30_report = json.loads(Path(args.iter30_report).read_text())
    if iter30_report.get("verdict") != ALLOWED_ITER30_VERDICT:
        failures.append(
            "iter30_verdict="
            f"{iter30_report.get('verdict')} != {ALLOWED_ITER30_VERDICT}"
        )
    if iter30_report.get("s0_pass") is not True:
        failures.append("iter30_s0_not_pass")
    if iter30_report.get("s1_pass") is not True:
        failures.append("iter30_s1_not_pass")
    if iter30_report.get("s2_pass") is not True:
        failures.append("iter30_s2_not_pass")

    return task_rows, {
        "hash_validation": hash_report,
        "build_report": build_report,
        "iter30_report": {
            "path": str(Path(args.iter30_report)),
            "verdict": iter30_report.get("verdict"),
            "s0_pass": iter30_report.get("s0_pass"),
            "s1_pass": iter30_report.get("s1_pass"),
            "s2_pass": iter30_report.get("s2_pass"),
        },
        "s0_failures": failures,
    }


def make_replay_manifests(rows: list[dict]) -> dict[str, list[dict]]:
    calibration_pos = [
        stable_row(row)
        for row in rows
        if row["split"] == "calibration" and int(row["label"]) == 1
    ]
    calibration_benign = [
        stable_row(row)
        for row in rows
        if row["split"] == "calibration" and int(row["label"]) == 0
    ]
    calibration_pos = sorted(calibration_pos, key=key_tuple)
    calibration_benign = sorted(calibration_benign, key=key_tuple)

    manifests = {
        "canary": calibration_pos[:6] + calibration_benign[:6],
        "calibration": [
            stable_row(row)
            for row in rows
            if row["split"] == "calibration" and int(row["label"]) in (0, 1)
        ],
        "heldout": [
            stable_row(row)
            for row in rows
            if row["split"] == "heldout" and int(row["label"]) in (0, 1)
        ],
    }
    for name, records in list(manifests.items()):
        manifests[name] = sorted(records, key=key_tuple)
    return manifests


def write_json(path: Path, payload: dict | list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main() -> int:
    module = load_iter30_module()
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract-part", action="append")
    parser.add_argument(
        "--gt",
        default=str(ITER29 / "proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz"),
    )
    parser.add_argument(
        "--s0-report",
        default=str(ITER29 / "proof-full-extract/s0_integrity_report.json"),
    )
    parser.add_argument(
        "--label-atlas-report",
        default=str(ITER29 / "proof-full-extract/label_atlas_report.json"),
    )
    parser.add_argument(
        "--sha256s",
        default=str(ITER29 / "proof-full-extract/sha256s.txt"),
    )
    parser.add_argument(
        "--iter30-report",
        default=str(ITER30 / "proof-localization/localization_report.json"),
    )
    parser.add_argument("--out-dir", default=str(ITER31 / "proof-direction"))
    args = parser.parse_args()

    if args.extract_part is None:
        args.extract_part = [str(path) for path in default_extract_parts()]

    rows, input_report = validate_inputs(module, args)
    if input_report["s0_failures"]:
        out_dir = Path(args.out_dir)
        write_json(
            out_dir / "direction_input_failure.json",
            {
                "stage": "iter31_full_trainval_bridge_intervention",
                "verdict": "INFRASTRUCTURE_OR_DATA_NULL_STOP_BEFORE_DIRECTION",
                "command_line": " ".join(sys.argv),
                **input_report,
            },
        )
        print(json.dumps(input_report, indent=2, sort_keys=True))
        return 2

    direction, arrays = derive_direction(module, rows)
    manifests = make_replay_manifests(rows)
    out_dir = Path(args.out_dir)
    write_json(out_dir / "direction.json", direction)
    write_json(out_dir / "replay_manifest_canary.json", manifests["canary"])
    write_json(out_dir / "replay_manifest_calibration.json", manifests["calibration"])
    write_json(out_dir / "replay_manifest_heldout.json", manifests["heldout"])

    report = {
        "stage": "iter31_full_trainval_bridge_intervention",
        "command_line": " ".join(sys.argv),
        **input_report,
        "direction": {
            key: direction[key]
            for key in (
                "feature_count",
                "fit_rows",
                "fit_eligible_lowdiv_rows",
                "fit_benign_control_rows",
                "dropped_dimension_count",
                "kept_dimension_count",
                "direction_std_l2",
                "direction_raw_l2",
                "direction_and_fit_stats_sha256",
            )
        },
        "direction_raw_min": float(np.min(arrays["direction_raw"])),
        "direction_raw_max": float(np.max(arrays["direction_raw"])),
        "replay_manifest_counts": {name: len(records) for name, records in manifests.items()},
        "verdict": "DIRECTION_ARTIFACT_WRITTEN_REPLAY_NOT_LAUNCHED",
        "claim_boundary": (
            "This artifact prepares the frozen iter31 direction and replay manifests only. "
            "It does not run a model, select an alpha, touch iteration-12 frames, score a "
            "selector, run closed loop, or make a safety claim."
        ),
    }
    write_json(out_dir / "direction_report.json", report)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
