#!/usr/bin/env python3
"""Build the iteration-37 track-query direction and offline receipts.

This script is offline-only. It reads committed iteration-29/30/33/36
artifacts, derives the fit-only benign-centroid direction over
``sdc_track_query`` alone, and verifies inherited prefix manifests before any
GPU replay is eligible.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
ITER29 = ROOT / "experiments/iter29_trainval_risk_support_atlas"
ITER30 = ROOT / "experiments/iter30_full_trainval_lowdiv_localization"
ITER32 = ROOT / "experiments/iter32_prefix_replay_baseline_recovery"
ITER33 = ROOT / "experiments/iter33_prefix_preserving_bridge_intervention"
ITER36 = ROOT / "experiments/iter36_bridge_site_decomposition"
ITER37 = ROOT / "experiments/iter37_track_query_site_intervention"
OUT = ITER37 / "proof-direction"

EXPECTED_ITER30_STATUS = "LOCALIZATION_PASS_SUCCESSOR_PREREG_AUTHORIZED"
EXPECTED_ITER32_STATUS = "BASELINE_RECOVERY_PASS_S1_PREFIX_REPLAY"
EXPECTED_ITER33_STATUS = "CALIBRATION_NULL_NO_USABLE_ALPHA"
EXPECTED_ITER36_STATUS = "BRIDGE_SITE_PASS_SITE_SPECIFIC_PREREG_AUTHORIZED"
EXPECTED_TRACK_FEATURE_COUNT = 256
EXPECTED_ITER32_MODEL_TARGET_SHA = "2495f9a1dc4d7f7544673cd4dc25c1283977087a0018b37e76184a2b3c0b611e"
EXPECTED_ITER32_GT_TARGET_SHA = "5064a3177c7918712fa56533b897e50a7d731f516d17a9ca6241ef67296050c7"
EXPECTED_PREFIX = {
    "canary": {
        "path": ITER33 / "proof-prefix/prefix_manifest_canary.json",
        "scenes": 3,
        "prefix_replay_rows": 44,
        "target_rows": 12,
        "context_only_rows": 32,
        "eligible_lowdiv": 6,
        "benign_control": 6,
    },
    "calibration": {
        "path": ITER33 / "proof-prefix/prefix_manifest_calibration.json",
        "scenes": 121,
        "prefix_replay_rows": 4293,
        "target_rows": 2452,
        "context_only_rows": 1841,
        "eligible_lowdiv": 108,
        "benign_control": 2344,
    },
    "heldout": {
        "path": ITER33 / "proof-prefix/prefix_manifest_heldout.json",
        "scenes": 122,
        "prefix_replay_rows": 4283,
        "target_rows": 2403,
        "context_only_rows": 1880,
        "eligible_lowdiv": 158,
        "benign_control": 2245,
    },
}


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


def load_status(result_path: Path) -> str | None:
    text = result_path.read_text(encoding="utf-8")
    match = re.search(r"^Status:\s*`([^`]+)`", text, flags=re.MULTILINE)
    return match.group(1) if match else None


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, payload: dict | list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def array_digest(module, *arrays: np.ndarray) -> str:
    return module.array_digest(*arrays)


def track_features(row: dict) -> np.ndarray:
    return np.asarray(row["sdc_track_query"], dtype=np.float64).ravel()


def derive_direction(
    module,
    rows: list[dict],
    expected_feature_count: int | None = None,
) -> tuple[dict, dict[str, np.ndarray]]:
    fit_rows = [row for row in rows if row["split"] == "fit"]
    fit_pos = [row for row in fit_rows if int(row["label"]) == 1]
    fit_benign = [row for row in fit_rows if int(row["label"]) == 0]
    if not fit_pos or not fit_benign:
        raise ValueError(
            f"fit split must contain both classes, got pos={len(fit_pos)} benign={len(fit_benign)}"
        )

    x_fit = np.vstack([track_features(row) for row in fit_rows]).astype(np.float64)
    y_fit = np.asarray([int(row["label"]) for row in fit_rows], dtype=np.int64)
    if expected_feature_count is not None and x_fit.shape[1] != expected_feature_count:
        raise ValueError(
            f"track_query feature_count={x_fit.shape[1]} != {expected_feature_count}"
        )

    fit_mean = x_fit.mean(axis=0)
    fit_std = x_fit.std(axis=0)
    keep = fit_std > 1e-12
    if not np.any(keep):
        raise ValueError("all track-query features are constant on fit split")

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
        "stage": "iter37_track_query_site_intervention",
        "source": "fit_split_track_query_benign_centroid_minus_eligible_lowdiv_centroid",
        "feature_order": "flatten(sdc_track_query)",
        "target_site": "track_query",
        "feature_count": int(x_fit.shape[1]),
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


def prefix_manifest_receipt(name: str, spec: dict) -> tuple[dict, list[str]]:
    path = spec["path"]
    rows = json.loads(path.read_text(encoding="utf-8"))
    scenes = {row["scene"] for row in rows}
    target_rows = [row for row in rows if row.get("target_row")]
    label_counts = {}
    for row in target_rows:
        label = row.get("source_label_name", "")
        label_counts[label] = label_counts.get(label, 0) + 1
    receipt = {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha256_file(path),
        "scenes": len(scenes),
        "prefix_replay_rows": len(rows),
        "target_rows": len(target_rows),
        "context_only_rows": len(rows) - len(target_rows),
        "target_label_counts": dict(sorted(label_counts.items())),
    }
    failures = []
    for key in ("scenes", "prefix_replay_rows", "target_rows", "context_only_rows"):
        if receipt[key] != spec[key]:
            failures.append(f"{name}:{key}={receipt[key]} != {spec[key]}")
    for label in ("eligible_lowdiv", "benign_control"):
        if receipt["target_label_counts"].get(label, 0) != spec[label]:
            failures.append(f"{name}:{label}={receipt['target_label_counts'].get(label, 0)} != {spec[label]}")
    return receipt, failures


def prerequisite_report(args: argparse.Namespace) -> tuple[dict, list[str]]:
    failures = []
    statuses = {
        "iter30_result_status": load_status(ITER30 / "RESULT.md"),
        "iter32_result_status": load_status(ITER32 / "RESULT.md"),
        "iter33_result_status": load_status(ITER33 / "RESULT.md"),
        "iter36_result_status": load_status(ITER36 / "RESULT.md"),
    }
    expected = {
        "iter30_result_status": EXPECTED_ITER30_STATUS,
        "iter32_result_status": EXPECTED_ITER32_STATUS,
        "iter33_result_status": EXPECTED_ITER33_STATUS,
        "iter36_result_status": EXPECTED_ITER36_STATUS,
    }
    for key, value in statuses.items():
        if value != expected[key]:
            failures.append(f"{key}={value} != {expected[key]}")

    iter32_report = json.loads(Path(args.iter32_report).read_text(encoding="utf-8"))
    if iter32_report.get("s1_prefix_replay_pass") is not True:
        failures.append("iter32_s1_prefix_replay_pass_not_true")
    if iter32_report.get("model_target_repeat_hashes") != [
        EXPECTED_ITER32_MODEL_TARGET_SHA,
        EXPECTED_ITER32_MODEL_TARGET_SHA,
    ]:
        failures.append(f"iter32_model_target_repeat_hashes={iter32_report.get('model_target_repeat_hashes')}")
    if iter32_report.get("gt_target_repeat_hashes") != [
        EXPECTED_ITER32_GT_TARGET_SHA,
        EXPECTED_ITER32_GT_TARGET_SHA,
    ]:
        failures.append(f"iter32_gt_target_repeat_hashes={iter32_report.get('gt_target_repeat_hashes')}")

    iter33_canary = json.loads(Path(args.iter33_canary_report).read_text(encoding="utf-8"))
    if iter33_canary.get("s0_canary_pass") is not True:
        failures.append("iter33_s0_canary_pass_not_true")

    iter36_report = json.loads(Path(args.iter36_report).read_text(encoding="utf-8"))
    if "track_query" not in iter36_report.get("s2", {}).get("passing_sites", []):
        failures.append("iter36_track_query_not_passing_site")

    prefix_receipts = {}
    for name, spec in EXPECTED_PREFIX.items():
        receipt, receipt_failures = prefix_manifest_receipt(name, spec)
        prefix_receipts[name] = receipt
        failures.extend(receipt_failures)

    return {
        **statuses,
        "iter32_baseline_recovery": {
            "path": str(Path(args.iter32_report).relative_to(ROOT)),
            "s1_prefix_replay_pass": iter32_report.get("s1_prefix_replay_pass"),
            "model_target_repeat_hashes": iter32_report.get("model_target_repeat_hashes"),
            "gt_target_repeat_hashes": iter32_report.get("gt_target_repeat_hashes"),
        },
        "iter33_canary": {
            "path": str(Path(args.iter33_canary_report).relative_to(ROOT)),
            "s0_canary_pass": iter33_canary.get("s0_canary_pass"),
        },
        "iter36_track_query": {
            "path": str(Path(args.iter36_report).relative_to(ROOT)),
            "passing_sites": iter36_report.get("s2", {}).get("passing_sites", []),
        },
        "prefix_manifests": prefix_receipts,
    }, failures


def validate_inputs(module, args: argparse.Namespace) -> tuple[list[dict], dict]:
    parts = [Path(part) for part in args.extract_part]
    hash_report = module.validate_hashes(parts, Path(args.gt), Path(args.sha256s))
    report_failures = module.validate_reports(Path(args.s0_report), Path(args.label_atlas_report))
    task_rows, build_report, _meta = module.build_rows(parts, Path(args.gt))
    failures = module.s0_failures(hash_report, report_failures, build_report)
    prerequisites, prerequisite_failures = prerequisite_report(args)
    failures.extend(prerequisite_failures)
    return task_rows, {
        "hash_validation": hash_report,
        "build_report": build_report,
        "prerequisites": prerequisites,
        "s0_failures": failures,
    }


def main() -> int:
    module = load_iter30_module()
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract-part", action="append")
    parser.add_argument("--gt", default=str(ITER29 / "proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz"))
    parser.add_argument("--s0-report", default=str(ITER29 / "proof-full-extract/s0_integrity_report.json"))
    parser.add_argument("--label-atlas-report", default=str(ITER29 / "proof-full-extract/label_atlas_report.json"))
    parser.add_argument("--sha256s", default=str(ITER29 / "proof-full-extract/sha256s.txt"))
    parser.add_argument("--iter32-report", default=str(ITER32 / "proof-prefix/baseline_recovery_report.json"))
    parser.add_argument("--iter33-canary-report", default=str(ITER33 / "proof-canary/canary_report.json"))
    parser.add_argument("--iter36-report", default=str(ITER36 / "proof-audit/bridge_site_decomposition_report.json"))
    parser.add_argument("--out-dir", default=str(OUT))
    args = parser.parse_args()

    if args.extract_part is None:
        args.extract_part = [str(path) for path in default_extract_parts()]

    out_dir = Path(args.out_dir)
    rows, input_report = validate_inputs(module, args)
    if input_report["s0_failures"]:
        write_json(
            out_dir / "direction_input_failure.json",
            {
                "stage": "iter37_track_query_site_intervention",
                "verdict": "INFRASTRUCTURE_OR_DATA_NULL_STOP_BEFORE_DIRECTION",
                "command_line": " ".join(sys.argv),
                **input_report,
            },
        )
        print(json.dumps(input_report, indent=2, sort_keys=True))
        return 2

    direction, arrays = derive_direction(
        module,
        rows,
        expected_feature_count=EXPECTED_TRACK_FEATURE_COUNT,
    )
    write_json(out_dir / "track_query_direction.json", direction)
    report = {
        "stage": "iter37_track_query_site_intervention",
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
        "direction_path": str((out_dir / "track_query_direction.json").relative_to(ROOT)),
        "direction_file_sha256": sha256_file(out_dir / "track_query_direction.json"),
        "verdict": "TRACK_QUERY_DIRECTION_ARTIFACT_WRITTEN_REPLAY_NOT_LAUNCHED",
        "claim_boundary": (
            "This artifact prepares the frozen iter37 track-query direction and prerequisite "
            "receipts only. It does not run a model, select an alpha, touch iteration-12 frames, "
            "score a selector, run closed loop, or make a safety claim."
        ),
    }
    write_json(out_dir / "direction_report.json", report)
    (out_dir / "build_track_direction.command.txt").write_text(" ".join(sys.argv) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
