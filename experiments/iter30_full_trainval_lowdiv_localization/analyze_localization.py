#!/usr/bin/env python3
"""Iteration-30 full-trainval low-diversity localization gate.

Runs only on committed iteration-29 proof artifacts. It validates hashes/counts
first, then fits the frozen low-capacity probes from HYPOTHESIS.md.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    recall_score,
    roc_auc_score,
)


JOIN_KEY = ("scene", "sample_index", "timestamp_us")
SPLITS = ("fit", "calibration", "heldout")
PRIMARY_COUNTS = {
    "eligible_lowdiv": {"fit": 127, "calibration": 108, "heldout": 158},
    "benign_control": {"fit": 5084, "calibration": 2344, "heldout": 2245},
}
SEED = 30
MAX_HELDOUT_SINGLE_SCENE_FRACTION = 0.25
MIN_HELDOUT_POSITIVE_SCENES = 5
N_BOOTSTRAP = 1000


class ConcatenatedBinaryFiles(io.RawIOBase):
    """Read split binary files as one continuous stream."""

    def __init__(self, paths: list[Path]):
        super().__init__()
        self.paths = paths
        self.index = 0
        self.current = open(paths[0], "rb")

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:
        while self.current is not None:
            n_read = self.current.readinto(buffer)
            if n_read:
                return n_read
            self.current.close()
            self.index += 1
            if self.index >= len(self.paths):
                self.current = None
                return 0
            self.current = open(self.paths[self.index], "rb")
        return 0

    def close(self) -> None:
        if self.current is not None:
            self.current.close()
            self.current = None
        super().close()


def key_of(row: dict) -> tuple:
    return tuple(row.get(k) for k in JOIN_KEY)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_concat(paths: list[Path]) -> str:
    h = hashlib.sha256()
    for path in paths:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                h.update(chunk)
    return h.hexdigest()


def parse_sha256s(path: Path) -> dict[str, str]:
    out = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        digest, rel = line.split(maxsplit=1)
        out[rel] = digest
    return out


def iter_jsonl_gzip_parts(parts: list[Path]):
    raw = ConcatenatedBinaryFiles(parts)
    with raw, gzip.GzipFile(fileobj=io.BufferedReader(raw), mode="rb") as gz:
        with io.TextIOWrapper(gz, encoding="utf-8") as text:
            for line in text:
                if line.strip():
                    yield json.loads(line)


def iter_jsonl_gzip(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def endpoint_spread(cands: list) -> float:
    endpoints = [cand[-1] for cand in cands if cand]
    if len(endpoints) < 2:
        return 0.0
    return float(
        max(
            math.hypot(a[0] - b[0], a[1] - b[1])
            for a in endpoints
            for b in endpoints
        )
    )


def closest_gap(plan: list, objs: list, futs: list) -> float:
    best = float("inf")
    for obj, fut in zip(objs, futs):
        ox, oy = obj[0], obj[1]
        mode = fut[0] if fut else []
        if not mode:
            continue
        for k in range(min(3, len(plan))):
            px, py = plan[k]
            ax = ox + (mode[k][0] if k < len(mode) else mode[-1][0])
            ay = oy + (mode[k][1] if k < len(mode) else mode[-1][1])
            best = min(best, math.hypot(px - ax, py - ay))
    return best


def annotate(row: dict) -> dict:
    gap = closest_gap(row["traj"], row.get("objs", []), row.get("futs", []))
    spread = endpoint_spread(row["cands"])
    danger_4p5 = gap < 4.5
    safe_6p0 = gap >= 6.0
    low_diversity_1p5 = spread <= 1.5
    high_diversity_2p0 = spread >= 2.0
    return {
        "closest_gap": gap,
        "endpoint_spread": spread,
        "danger_4p5": danger_4p5,
        "safe_6p0": safe_6p0,
        "low_diversity_1p5": low_diversity_1p5,
        "high_diversity_2p0": high_diversity_2p0,
        "eligible_lowdiv": danger_4p5 and low_diversity_1p5,
        "benign_control": safe_6p0 and high_diversity_2p0,
    }


def plan_kinematic_features(plan: list) -> list[float]:
    if not plan:
        return [0.0, 0.0, 0.0, 0.0, 0.0]
    p0 = plan[0]
    p2 = plan[min(2, len(plan) - 1)]
    p_end = plan[-1]
    first_step = math.hypot(p0[0], p0[1])
    three_step = math.hypot(p2[0], p2[1])
    if len(plan) >= 2:
        yaw0 = math.atan2(plan[0][1], plan[0][0])
        yaw1 = math.atan2(plan[-1][1] - plan[-2][1], plan[-1][0] - plan[-2][0])
        yaw_change = yaw1 - yaw0
    else:
        yaw_change = 0.0
    return [first_step, three_step, float(p_end[0]), float(p_end[1]), yaw_change]


def internal_features(row: dict) -> np.ndarray:
    traj = np.asarray(row["sdc_traj_query_last"], dtype=np.float32).ravel()
    track = np.asarray(row["sdc_track_query"], dtype=np.float32).ravel()
    return np.concatenate([traj, track]).astype(np.float32)


def array_digest(*arrays: np.ndarray) -> str:
    h = hashlib.sha256()
    for arr in arrays:
        arr = np.ascontiguousarray(arr)
        h.update(str(arr.shape).encode("utf-8"))
        h.update(str(arr.dtype).encode("utf-8"))
        h.update(arr.tobytes())
    return h.hexdigest()


def safe_auc(y_true: np.ndarray, y_score: np.ndarray) -> float:
    if len(set(y_true.tolist())) < 2:
        return float("nan")
    return float(roc_auc_score(y_true, y_score))


def safe_average_precision(y_true: np.ndarray, y_score: np.ndarray) -> float:
    if len(set(y_true.tolist())) < 2:
        return float("nan")
    return float(average_precision_score(y_true, y_score))


def specificity(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    negatives = y_true == 0
    if not np.any(negatives):
        return float("nan")
    return float(np.mean(y_pred[negatives] == 0))


def threshold_candidates(probs: np.ndarray) -> np.ndarray:
    vals = np.unique(probs)
    return np.unique(np.concatenate(([0.0], vals, [1.0])))


def choose_threshold(y_cal: np.ndarray, p_cal: np.ndarray) -> tuple[float, float, int]:
    best_score = -1.0
    best_threshold = 1.0
    tie_count = 0
    for threshold in threshold_candidates(p_cal):
        pred = (p_cal >= threshold).astype(int)
        score = float(balanced_accuracy_score(y_cal, pred))
        if score > best_score + 1e-12:
            best_score = score
            best_threshold = float(threshold)
            tie_count = 1
        elif abs(score - best_score) <= 1e-12:
            tie_count += 1
            if threshold > best_threshold:
                best_threshold = float(threshold)
    return best_threshold, best_score, tie_count


def transform_fit_cal_heldout(
    x_fit: np.ndarray, x_cal: np.ndarray, x_held: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    mu = x_fit.mean(axis=0)
    sd = x_fit.std(axis=0)
    keep = sd > 1e-12
    if not np.any(keep):
        raise ValueError("all features are constant on fit split")
    x_fit_s = (x_fit[:, keep] - mu[keep]) / sd[keep]
    x_cal_s = (x_cal[:, keep] - mu[keep]) / sd[keep]
    x_held_s = (x_held[:, keep] - mu[keep]) / sd[keep]
    rank = int(np.linalg.matrix_rank(x_fit_s))
    n_components = int(min(32, rank, max(1, x_fit_s.shape[0] - 1), x_fit_s.shape[1]))
    pca = PCA(n_components=n_components, whiten=False, svd_solver="full")
    z_fit = pca.fit_transform(x_fit_s)
    z_cal = pca.transform(x_cal_s)
    z_held = pca.transform(x_held_s)
    meta = {
        "input_features": int(x_fit.shape[1]),
        "constant_dropped": int((~keep).sum()),
        "features_after_constant_drop": int(keep.sum()),
        "pca_components": n_components,
        "preprocess_sha256": array_digest(mu, sd, keep.astype(np.uint8), pca.components_),
    }
    return z_fit, z_cal, z_held, meta


def split_arrays(rows: list[dict], feature_fn: Callable[[dict], np.ndarray | list[float]]):
    out = {}
    for split in SPLITS:
        split_rows = [row for row in rows if row["split"] == split]
        out[split] = (
            np.vstack([np.asarray(feature_fn(row), dtype=np.float64) for row in split_rows]),
            np.asarray([row["label"] for row in split_rows], dtype=int),
            [row["scene"] for row in split_rows],
        )
    return out


def run_probe(
    rows: list[dict],
    feature_fn: Callable[[dict], np.ndarray | list[float]],
    name: str,
    *,
    shuffle_fit: bool = False,
) -> dict:
    arrays = split_arrays(rows, feature_fn)
    x_fit, y_fit, _ = arrays["fit"]
    x_cal, y_cal, _ = arrays["calibration"]
    x_held, y_held, held_scenes = arrays["heldout"]
    if shuffle_fit:
        rng = np.random.default_rng(SEED)
        y_model_fit = rng.permutation(y_fit)
    else:
        y_model_fit = y_fit
    z_fit, z_cal, z_held, preprocess = transform_fit_cal_heldout(x_fit, x_cal, x_held)
    model = LogisticRegression(
        C=1.0,
        class_weight="balanced",
        max_iter=10000,
        random_state=SEED,
        solver="lbfgs",
    )
    model.fit(z_fit, y_model_fit)
    p_cal = model.predict_proba(z_cal)[:, 1]
    p_held = model.predict_proba(z_held)[:, 1]
    threshold, cal_ba, tie_count = choose_threshold(y_cal, p_cal)
    pred_held = (p_held >= threshold).astype(int)
    return {
        "name": name,
        "n_fit": int(len(y_fit)),
        "n_calibration": int(len(y_cal)),
        "n_heldout": int(len(y_held)),
        "fit_positive": int(y_fit.sum()),
        "calibration_positive": int(y_cal.sum()),
        "heldout_positive": int(y_held.sum()),
        **preprocess,
        "calibration_threshold": threshold,
        "calibration_threshold_tie_count": int(tie_count),
        "calibration_balanced_accuracy": float(cal_ba),
        "heldout_auc": safe_auc(y_held, p_held),
        "heldout_average_precision": safe_average_precision(y_held, p_held),
        "heldout_balanced_accuracy": float(balanced_accuracy_score(y_held, pred_held)),
        "heldout_recall": float(recall_score(y_held, pred_held, zero_division=0)),
        "heldout_specificity": specificity(y_held, pred_held),
        "model_sha256": array_digest(model.coef_, model.intercept_),
        "heldout_scores": p_held.astype(float).tolist(),
        "heldout_labels": y_held.astype(int).tolist(),
        "heldout_scenes": held_scenes,
    }


def bootstrap_scene_clusters(probe: dict) -> dict:
    y = np.asarray(probe["heldout_labels"], dtype=int)
    p = np.asarray(probe["heldout_scores"], dtype=float)
    scenes = np.asarray(probe["heldout_scenes"], dtype=object)
    unique_scenes = np.unique(scenes)
    rng = np.random.default_rng(SEED)
    aucs = []
    bas = []
    skipped = 0
    threshold = float(probe["calibration_threshold"])
    for _ in range(N_BOOTSTRAP):
        sampled = rng.choice(unique_scenes, size=len(unique_scenes), replace=True)
        indices = np.concatenate([np.where(scenes == scene)[0] for scene in sampled])
        yy = y[indices]
        if len(set(yy.tolist())) < 2:
            skipped += 1
            continue
        pp = p[indices]
        aucs.append(float(roc_auc_score(yy, pp)))
        bas.append(float(balanced_accuracy_score(yy, (pp >= threshold).astype(int))))
    if aucs:
        auc_arr = np.asarray(aucs)
        ba_arr = np.asarray(bas)
        quantiles = {
            "auc_p05": float(np.percentile(auc_arr, 5)),
            "auc_median": float(np.percentile(auc_arr, 50)),
            "auc_p95": float(np.percentile(auc_arr, 95)),
            "balanced_accuracy_p05": float(np.percentile(ba_arr, 5)),
            "balanced_accuracy_median": float(np.percentile(ba_arr, 50)),
            "balanced_accuracy_p95": float(np.percentile(ba_arr, 95)),
        }
    else:
        quantiles = {}
    return {
        "n_resamples": N_BOOTSTRAP,
        "valid_resamples": len(aucs),
        "skipped_single_class_resamples": skipped,
        **quantiles,
    }


def load_gt(gt_path: Path) -> tuple[dict[tuple, dict], dict]:
    gt_by_key = {}
    scene_order: dict[str, dict[str, int]] = {split: {} for split in SPLITS}
    first_ts: dict[str, int] = {}
    last_ts: dict[str, int] = {}
    max_sample: dict[str, int] = defaultdict(int)
    for row in iter_jsonl_gzip(gt_path):
        key = key_of(row)
        gt_by_key[key] = row
        split = row["split"]
        scene = row["scene"]
        if scene not in scene_order[split]:
            scene_order[split][scene] = len(scene_order[split])
        ts = int(row["timestamp_us"])
        first_ts[scene] = min(first_ts.get(scene, ts), ts)
        last_ts[scene] = max(last_ts.get(scene, ts), ts)
        max_sample[scene] = max(max_sample[scene], int(row["sample_index"]))
    meta = {
        "scene_order": scene_order,
        "first_ts": first_ts,
        "last_ts": last_ts,
        "max_sample": dict(max_sample),
    }
    return gt_by_key, meta


def metadata_feature(row: dict) -> list[float]:
    max_scene_ord = max(1, row["split_scene_count"] - 1)
    max_sample = max(1, row["scene_max_sample"])
    scene_span = max(1, row["scene_last_ts"] - row["scene_first_ts"])
    return [
        row["scene_ordinal"] / max_scene_ord,
        row["sample_index"] / max_sample,
        (row["timestamp_us"] - row["scene_first_ts"]) / scene_span,
    ]


def candidate_geometry_feature(row: dict) -> list[float]:
    return [
        float(row["closest_gap"]),
        float(row["endpoint_spread"]),
        float(len(row["cands"])),
        float(len(row.get("objs", []))),
    ]


def validate_reports(s0_report: Path, atlas_report: Path) -> list[str]:
    failures = []
    s0 = json.loads(s0_report.read_text())
    atlas = json.loads(atlas_report.read_text())
    if s0.get("all_s0_integrity_pass") is not True:
        failures.append("iter29_s0_report_not_pass")
    if atlas.get("support_pass") is not True:
        failures.append("iter29_label_atlas_support_not_pass")
    if atlas.get("strict_optional_support_pass") is not False:
        failures.append("iter29_strict_optional_expected_false")
    return failures


def validate_hashes(parts: list[Path], gt: Path, sha256s: Path) -> dict:
    expected = parse_sha256s(sha256s)
    extract_rel = "experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1.jsonl.gz"
    gt_rel = "experiments/iter29_trainval_risk_support_atlas/proof-full-extract/sentinel_e29_stage1_gt.jsonl.gz"
    extract_sha = sha256_concat(parts)
    gt_sha = sha256_file(gt)
    return {
        "extract_concat_sha256": extract_sha,
        "extract_expected_sha256": expected.get(extract_rel),
        "extract_sha256_match": extract_sha == expected.get(extract_rel),
        "gt_sha256": gt_sha,
        "gt_expected_sha256": expected.get(gt_rel),
        "gt_sha256_match": gt_sha == expected.get(gt_rel),
    }


def build_rows(parts: list[Path], gt_path: Path) -> tuple[list[dict], dict, dict]:
    gt_by_key, meta = load_gt(gt_path)
    label_counts = {
        "eligible_lowdiv": {split: 0 for split in SPLITS},
        "benign_control": {split: 0 for split in SPLITS},
        "ambiguous": {split: 0 for split in SPLITS},
    }
    positive_scenes: dict[str, Counter[str]] = {split: Counter() for split in SPLITS}
    task_rows = []
    row_counts = {"extract_rows_total": 0, "extract_nonreset_rows_total": 0, "joined_rows": 0}
    errors: Counter[str] = Counter()
    seen = set()
    for row in iter_jsonl_gzip_parts(parts):
        row_counts["extract_rows_total"] += 1
        if row.get("reset"):
            continue
        row_counts["extract_nonreset_rows_total"] += 1
        key = key_of(row)
        if key in seen:
            errors["duplicate_extract_key"] += 1
            continue
        seen.add(key)
        gt = gt_by_key.get(key)
        if gt is None:
            errors["missing_gt"] += 1
            continue
        split = gt["split"]
        scene = gt["scene"]
        ann = annotate(row)
        row_counts["joined_rows"] += 1
        if ann["eligible_lowdiv"]:
            label = 1
            label_counts["eligible_lowdiv"][split] += 1
            positive_scenes[split][scene] += 1
        elif ann["benign_control"]:
            label = 0
            label_counts["benign_control"][split] += 1
        else:
            label = None
            label_counts["ambiguous"][split] += 1
        if label is None:
            continue
        task_rows.append(
            {
                **row,
                "split": split,
                "scene": scene,
                "sample_index": int(gt["sample_index"]),
                "timestamp_us": int(gt["timestamp_us"]),
                "label": label,
                "closest_gap": ann["closest_gap"],
                "endpoint_spread": ann["endpoint_spread"],
                "scene_ordinal": meta["scene_order"][split][scene],
                "split_scene_count": len(meta["scene_order"][split]),
                "scene_first_ts": meta["first_ts"][scene],
                "scene_last_ts": meta["last_ts"][scene],
                "scene_max_sample": meta["max_sample"][scene],
            }
        )
    for key in set(gt_by_key) - seen:
        if None not in key:
            errors["gt_without_extract"] += 1
    return task_rows, {
        "label_counts": label_counts,
        "positive_scenes": {split: dict(counter) for split, counter in positive_scenes.items()},
        "row_counts": row_counts,
        "errors": dict(errors),
    }, meta


def s0_failures(hash_report: dict, report_failures: list[str], build_report: dict) -> list[str]:
    failures = list(report_failures)
    if not hash_report["extract_sha256_match"]:
        failures.append("extract_concat_sha256_mismatch")
    if not hash_report["gt_sha256_match"]:
        failures.append("gt_sha256_mismatch")
    if build_report["errors"]:
        failures.extend(f"row_error.{k}={v}" for k, v in build_report["errors"].items())
    for label, expected_by_split in PRIMARY_COUNTS.items():
        observed_by_split = build_report["label_counts"][label]
        for split, expected in expected_by_split.items():
            observed = observed_by_split[split]
            if observed != expected:
                failures.append(f"{label}.{split}={observed} != {expected}")
    heldout_positive_scenes = build_report["positive_scenes"]["heldout"]
    if len(heldout_positive_scenes) < MIN_HELDOUT_POSITIVE_SCENES:
        failures.append(
            "eligible_lowdiv.heldout.scene_count="
            f"{len(heldout_positive_scenes)} < {MIN_HELDOUT_POSITIVE_SCENES}"
        )
    heldout_total = sum(heldout_positive_scenes.values())
    if heldout_total:
        max_scene, max_count = max(heldout_positive_scenes.items(), key=lambda item: item[1])
        frac = max_count / heldout_total
        if frac > MAX_HELDOUT_SINGLE_SCENE_FRACTION:
            failures.append(
                f"eligible_lowdiv.heldout.max_scene_fraction={max_scene}:{frac:.3f}"
            )
    return failures


def pass_fail_report(probes: dict, bootstrap: dict) -> tuple[bool, list[str], bool, list[str]]:
    primary = probes["internal_tensor"]
    metadata = probes["metadata_control"]
    kinematic = probes["ego_plan_kinematic_control"]
    shuffled = probes["shuffled_label_internal_control"]
    s1_failures = []
    if primary["heldout_auc"] < 0.80:
        s1_failures.append(f"internal_auc={primary['heldout_auc']:.3f} < 0.800")
    if primary["heldout_average_precision"] < 0.20:
        s1_failures.append(
            f"internal_average_precision={primary['heldout_average_precision']:.3f} < 0.200"
        )
    if primary["heldout_balanced_accuracy"] < 0.70:
        s1_failures.append(
            f"internal_balanced_accuracy={primary['heldout_balanced_accuracy']:.3f} < 0.700"
        )
    if primary["heldout_recall"] < 0.60:
        s1_failures.append(f"internal_recall={primary['heldout_recall']:.3f} < 0.600")
    if primary["heldout_specificity"] < 0.70:
        s1_failures.append(
            f"internal_specificity={primary['heldout_specificity']:.3f} < 0.700"
        )
    if primary["heldout_auc"] - metadata["heldout_auc"] < 0.10:
        s1_failures.append(
            "metadata_auc_gap="
            f"{primary['heldout_auc'] - metadata['heldout_auc']:.3f} < 0.100"
        )
    if primary["heldout_auc"] - kinematic["heldout_auc"] < 0.10:
        s1_failures.append(
            "ego_plan_kinematic_auc_gap="
            f"{primary['heldout_auc'] - kinematic['heldout_auc']:.3f} < 0.100"
        )
    if not 0.40 <= shuffled["heldout_auc"] <= 0.60:
        s1_failures.append(f"shuffled_auc={shuffled['heldout_auc']:.3f} outside [0.400,0.600]")
    if not 0.40 <= shuffled["heldout_balanced_accuracy"] <= 0.60:
        s1_failures.append(
            "shuffled_balanced_accuracy="
            f"{shuffled['heldout_balanced_accuracy']:.3f} outside [0.400,0.600]"
        )

    s2_failures = []
    if bootstrap.get("valid_resamples", 0) < 900:
        s2_failures.append(f"valid_resamples={bootstrap.get('valid_resamples', 0)} < 900")
    if bootstrap.get("auc_p05", float("nan")) < 0.70:
        s2_failures.append(f"auc_p05={bootstrap.get('auc_p05', float('nan')):.3f} < 0.700")
    if bootstrap.get("balanced_accuracy_p05", float("nan")) < 0.62:
        s2_failures.append(
            "balanced_accuracy_p05="
            f"{bootstrap.get('balanced_accuracy_p05', float('nan')):.3f} < 0.620"
        )
    if bootstrap.get("auc_median", float("nan")) < 0.80:
        s2_failures.append(
            f"auc_median={bootstrap.get('auc_median', float('nan')):.3f} < 0.800"
        )
    return not s1_failures, s1_failures, not s2_failures, s2_failures


def analyze(args: argparse.Namespace) -> dict:
    parts = [Path(part) for part in args.extract_part]
    gt = Path(args.gt)
    hash_report = validate_hashes(parts, gt, Path(args.sha256s))
    report_failures = validate_reports(Path(args.s0_report), Path(args.label_atlas_report))
    task_rows, build_report, _meta = build_rows(parts, gt)
    failures = s0_failures(hash_report, report_failures, build_report)
    if failures:
        return {
            "stage": "iter30_full_trainval_lowdiv_localization",
            "command_line": " ".join(sys.argv),
            "hash_validation": hash_report,
            "build_report": build_report,
            "s0_pass": False,
            "s0_failures": failures,
            "verdict": "INFRASTRUCTURE_OR_DATA_NULL_STOP_BEFORE_PROBE",
            "claim_boundary": (
                "Iteration 30 stopped before probe fitting because S0 input/count integrity failed. "
                "No activation direction, intervention, iteration-12 scoring, selector evaluation, "
                "or closed-loop work is authorized."
            ),
        }

    probes = {
        "internal_tensor": run_probe(task_rows, internal_features, "internal_tensor"),
        "metadata_control": run_probe(task_rows, metadata_feature, "metadata_control"),
        "ego_plan_kinematic_control": run_probe(
            task_rows, lambda row: plan_kinematic_features(row["traj"]), "ego_plan_kinematic_control"
        ),
        "shuffled_label_internal_control": run_probe(
            task_rows, internal_features, "shuffled_label_internal_control", shuffle_fit=True
        ),
        "candidate_geometry_positive_control": run_probe(
            task_rows, candidate_geometry_feature, "candidate_geometry_positive_control"
        ),
    }
    bootstrap = bootstrap_scene_clusters(probes["internal_tensor"])
    s1_pass, s1_failures, s2_pass, s2_failures = pass_fail_report(probes, bootstrap)
    if not s1_pass:
        verdict = "DIAGNOSTIC_NULL_STOP_BEFORE_CAUSAL_WORK"
    elif not s2_pass:
        verdict = "ROBUSTNESS_NULL_STOP_BEFORE_CAUSAL_WORK"
    else:
        verdict = "LOCALIZATION_PASS_SUCCESSOR_PREREG_AUTHORIZED"
    return {
        "stage": "iter30_full_trainval_lowdiv_localization",
        "command_line": " ".join(sys.argv),
        "hash_validation": hash_report,
        "build_report": build_report,
        "s0_pass": True,
        "probes": probes,
        "s1_pass": s1_pass,
        "s1_failures": s1_failures,
        "scene_cluster_bootstrap": bootstrap,
        "s2_pass": bool(s1_pass and s2_pass),
        "s2_failures": ([] if not s1_pass else s2_failures),
        "verdict": verdict,
        "claim_boundary": (
            "Probe success is diagnostic only. This result authorizes at most a separate "
            "causal-intervention pre-registration. It does not authorize activation patching, "
            "iteration-12 scoring, selector evaluation, closed-loop evaluation, or a safety claim."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract-part", action="append", required=True)
    parser.add_argument("--gt", required=True)
    parser.add_argument("--s0-report", required=True)
    parser.add_argument("--label-atlas-report", required=True)
    parser.add_argument("--sha256s", required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report = analyze(args)
    (out_dir / "localization_report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
