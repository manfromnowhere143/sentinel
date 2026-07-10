#!/usr/bin/env python3
"""Audit bridge-site diagnostic localization after the global direction failed.

This script is offline-only. It reads committed iteration-29 extraction rows plus
iteration-30/35 reports, then asks whether a pre-declared bridge subsite carries
enough diagnostic low-diversity signal to justify a future site-specific
intervention pre-registration.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
from sklearn.decomposition import PCA
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    balanced_accuracy_score,
    recall_score,
    roc_auc_score,
)


ROOT = Path(__file__).resolve().parents[2]
ITER29 = ROOT / "experiments/iter29_trainval_risk_support_atlas"
ITER30 = ROOT / "experiments/iter30_full_trainval_lowdiv_localization"
ITER35 = ROOT / "experiments/iter35_response_heterogeneity_audit"
ITER36 = ROOT / "experiments/iter36_bridge_site_decomposition"
PROOF29 = ITER29 / "proof-full-extract"
PROOF30 = ITER30 / "proof-localization"
PROOF35 = ITER35 / "proof-audit"
PROOF36 = ITER36 / "proof-audit"

EXPECTED_ITER30_VERDICT = "LOCALIZATION_PASS_SUCCESSOR_PREREG_AUTHORIZED"
EXPECTED_ITER35_VERDICT = "HETEROGENEITY_NULL_NO_ACTIONABLE_STRATUM"
PRIMARY_COUNTS = {
    "eligible_lowdiv": {"fit": 127, "calibration": 108, "heldout": 158},
    "benign_control": {"fit": 5084, "calibration": 2344, "heldout": 2245},
}
SEED = 36
N_BOOTSTRAP = 500
CLAIM_BOUNDARY = (
    "Offline target-site audit only: no activation patch, direction, alpha, GPU/gcloud work, "
    "heldout replay, iteration-12 scoring, selector evaluation, closed-loop work, deployment "
    "language, or safety claim is authorized."
)


def load_iter30_analyzer():
    script = ITER30 / "analyze_localization.py"
    spec = importlib.util.spec_from_file_location("iter30_analyze_localization", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def default_extract_parts() -> list[Path]:
    return sorted(PROOF29.glob("sentinel_e29_stage1.jsonl.gz.part-*"))


def json_sanitize(value):
    if isinstance(value, dict):
        return {key: json_sanitize(item) for key, item in value.items()}
    if isinstance(value, list):
        return [json_sanitize(item) for item in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    return value


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_sanitize(payload), allow_nan=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def site_definitions() -> dict[str, tuple[str, int, int]]:
    sites = {"all_bridge": ("bridge", 0, 1792)}
    for idx in range(6):
        sites[f"traj_slot_{idx}"] = ("traj", idx * 256, (idx + 1) * 256)
    sites["track_query"] = ("track", 0, 256)
    return sites


def bridge_vector(row: dict) -> np.ndarray:
    traj = np.asarray(row["sdc_traj_query_last"], dtype=np.float64).ravel()
    track = np.asarray(row["sdc_track_query"], dtype=np.float64).ravel()
    return np.concatenate([traj, track])


def site_features(row: dict, site: str) -> np.ndarray:
    definitions = site_definitions()
    if site not in definitions:
        raise KeyError(site)
    kind, start, end = definitions[site]
    if kind == "bridge":
        return bridge_vector(row)
    if kind == "traj":
        traj = np.asarray(row["sdc_traj_query_last"], dtype=np.float64).ravel()
        return traj[start:end]
    track = np.asarray(row["sdc_track_query"], dtype=np.float64).ravel()
    return track[start:end]


def array_digest(*arrays: np.ndarray) -> str:
    import hashlib

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


def split_arrays(rows: list[dict], site: str):
    out = {}
    for split in ("fit", "calibration", "heldout"):
        split_rows = [row for row in rows if row["split"] == split]
        out[split] = (
            np.vstack([site_features(row, site) for row in split_rows]),
            np.asarray([row["label"] for row in split_rows], dtype=int),
            [row["scene"] for row in split_rows],
        )
    return out


def transform_fit_cal_heldout(
    x_fit: np.ndarray,
    x_cal: np.ndarray,
    x_held: np.ndarray,
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


def run_site_probe(rows: list[dict], site: str) -> dict:
    arrays = split_arrays(rows, site)
    x_fit, y_fit, _ = arrays["fit"]
    x_cal, y_cal, _ = arrays["calibration"]
    x_held, y_held, held_scenes = arrays["heldout"]
    z_fit, z_cal, z_held, preprocess = transform_fit_cal_heldout(x_fit, x_cal, x_held)
    model = LogisticRegression(
        C=1.0,
        class_weight="balanced",
        max_iter=2000,
        random_state=SEED,
        solver="lbfgs",
    )
    model.fit(z_fit, y_fit)
    p_cal = model.predict_proba(z_cal)[:, 1]
    p_held = model.predict_proba(z_held)[:, 1]
    threshold, cal_ba, tie_count = choose_threshold(y_cal, p_cal)
    pred_held = (p_held >= threshold).astype(int)
    return {
        "name": site,
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


def compact_probe(probe: dict) -> dict:
    return {key: value for key, value in probe.items() if key not in {"heldout_scores", "heldout_labels", "heldout_scenes"}}


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
    out = {
        "n_resamples": N_BOOTSTRAP,
        "valid_resamples": len(aucs),
        "skipped_single_class_resamples": skipped,
    }
    if aucs:
        auc_arr = np.asarray(aucs)
        ba_arr = np.asarray(bas)
        out.update(
            {
                "auc_p05": float(np.percentile(auc_arr, 5)),
                "auc_median": float(np.percentile(auc_arr, 50)),
                "auc_p95": float(np.percentile(auc_arr, 95)),
                "balanced_accuracy_p05": float(np.percentile(ba_arr, 5)),
                "balanced_accuracy_median": float(np.percentile(ba_arr, 50)),
                "balanced_accuracy_p95": float(np.percentile(ba_arr, 95)),
            }
        )
    return out


def shape_failures(rows: list[dict]) -> list[str]:
    failures = []
    bad_traj = sum(1 for row in rows if len(row.get("sdc_traj_query_last", [])) != 1536)
    bad_track = sum(1 for row in rows if len(row.get("sdc_track_query", [])) != 256)
    if bad_traj:
        failures.append(f"sdc_traj_query_last_bad_length_rows={bad_traj}")
    if bad_track:
        failures.append(f"sdc_track_query_bad_length_rows={bad_track}")
    return failures


def s0_failures(iter30_module, args: argparse.Namespace, task_rows: list[dict], build_report: dict) -> tuple[list[str], dict]:
    extract_parts = [Path(part) for part in args.extract_part]
    hash_report = iter30_module.validate_hashes(extract_parts, Path(args.gt), Path(args.sha256s))
    report_failures = iter30_module.validate_reports(Path(args.s0_report), Path(args.label_atlas_report))
    failures = list(report_failures)
    if not hash_report["extract_sha256_match"]:
        failures.append("extract_concat_sha256_mismatch")
    if not hash_report["gt_sha256_match"]:
        failures.append("gt_sha256_mismatch")
    if build_report["errors"]:
        failures.extend(f"row_error.{key}={value}" for key, value in build_report["errors"].items())
    for label, expected_by_split in PRIMARY_COUNTS.items():
        observed_by_split = build_report["label_counts"][label]
        for split, expected in expected_by_split.items():
            observed = observed_by_split[split]
            if observed != expected:
                failures.append(f"{label}.{split}={observed} != {expected}")
    failures.extend(shape_failures(task_rows))

    iter30_report = json.loads(Path(args.iter30_report).read_text(encoding="utf-8"))
    iter35_report = json.loads(Path(args.iter35_report).read_text(encoding="utf-8"))
    if iter30_report.get("verdict") != EXPECTED_ITER30_VERDICT:
        failures.append(f"iter30_verdict={iter30_report.get('verdict')} != {EXPECTED_ITER30_VERDICT}")
    if iter35_report.get("verdict") != EXPECTED_ITER35_VERDICT:
        failures.append(f"iter35_verdict={iter35_report.get('verdict')} != {EXPECTED_ITER35_VERDICT}")

    return failures, {
        "hash_validation": hash_report,
        "iter30_verdict": iter30_report.get("verdict"),
        "iter35_verdict": iter35_report.get("verdict"),
        "build_report": build_report,
    }


def evaluate_s1(all_bridge: dict) -> dict:
    failures = []
    if all_bridge["heldout_auc"] < 0.93:
        failures.append(f"all_bridge_auc={all_bridge['heldout_auc']:.6f} < 0.93")
    if all_bridge["heldout_average_precision"] < 0.55:
        failures.append(f"all_bridge_average_precision={all_bridge['heldout_average_precision']:.6f} < 0.55")
    if all_bridge["heldout_balanced_accuracy"] < 0.83:
        failures.append(f"all_bridge_balanced_accuracy={all_bridge['heldout_balanced_accuracy']:.6f} < 0.83")
    if all_bridge["heldout_recall"] < 0.80:
        failures.append(f"all_bridge_recall={all_bridge['heldout_recall']:.6f} < 0.80")
    if all_bridge["heldout_specificity"] < 0.80:
        failures.append(f"all_bridge_specificity={all_bridge['heldout_specificity']:.6f} < 0.80")
    return {"pass": not failures, "failures": failures}


def site_metric_failures(site: dict, all_bridge: dict) -> list[str]:
    failures = []
    if site["heldout_auc"] < 0.85:
        failures.append(f"heldout_auc={site['heldout_auc']:.6f} < 0.85")
    if site["heldout_average_precision"] < 0.30:
        failures.append(f"heldout_average_precision={site['heldout_average_precision']:.6f} < 0.30")
    if site["heldout_balanced_accuracy"] < 0.78:
        failures.append(f"heldout_balanced_accuracy={site['heldout_balanced_accuracy']:.6f} < 0.78")
    if site["heldout_recall"] < 0.70:
        failures.append(f"heldout_recall={site['heldout_recall']:.6f} < 0.70")
    if site["heldout_specificity"] < 0.75:
        failures.append(f"heldout_specificity={site['heldout_specificity']:.6f} < 0.75")
    auc_gap = all_bridge["heldout_auc"] - site["heldout_auc"]
    if auc_gap > 0.08:
        failures.append(f"all_bridge_auc_gap={auc_gap:.6f} > 0.08")
    ap_floor = 0.50 * all_bridge["heldout_average_precision"]
    if site["heldout_average_precision"] < ap_floor:
        failures.append(f"average_precision={site['heldout_average_precision']:.6f} < 0.50*all_bridge_ap={ap_floor:.6f}")
    return failures


def bootstrap_failures(bootstrap: dict) -> list[str]:
    failures = []
    if bootstrap.get("auc_p05", float("nan")) < 0.75:
        failures.append(f"bootstrap_auc_p05={bootstrap.get('auc_p05', float('nan')):.6f} < 0.75")
    if bootstrap.get("balanced_accuracy_p05", float("nan")) < 0.65:
        failures.append(
            "bootstrap_balanced_accuracy_p05="
            f"{bootstrap.get('balanced_accuracy_p05', float('nan')):.6f} < 0.65"
        )
    return failures


def evaluate_s2(probes: dict[str, dict], bootstraps: dict[str, dict]) -> dict:
    all_bridge = probes["all_bridge"]
    sites = []
    passing = []
    for name in site_definitions():
        if name == "all_bridge":
            continue
        metric_failures = site_metric_failures(probes[name], all_bridge)
        bootstrap = bootstraps.get(name)
        failures = list(metric_failures)
        if bootstrap is None:
            failures.append("bootstrap_not_run_because_metric_bars_failed")
        else:
            failures.extend(bootstrap_failures(bootstrap))
        passed = not failures
        if passed:
            passing.append(name)
        sites.append(
            {
                "name": name,
                "pass": passed,
                "failures": failures,
                "metrics": compact_probe(probes[name]),
                "bootstrap": bootstrap,
            }
        )
    return {
        "pass": bool(passing),
        "passing_sites": passing,
        "sites": sites,
        "failures": [] if passing else ["no_non_global_site_passed_all_target_site_bars"],
    }


def verdict(s0_pass: bool, s1: dict | None, s2: dict | None) -> str:
    if not s0_pass:
        return "INFRASTRUCTURE_NULL_S0_ARTIFACT_OR_COUNT_INTEGRITY"
    if s1 is not None and not s1["pass"]:
        return "BRIDGE_SITE_NULL_FULL_BRIDGE_REPRODUCTION_FAILED"
    if s2 is not None and not s2["pass"]:
        return "BRIDGE_SITE_NULL_NO_LOCALIZED_TARGET"
    return "BRIDGE_SITE_PASS_SITE_SPECIFIC_PREREG_AUTHORIZED"


def build_report(args: argparse.Namespace) -> dict:
    iter30_module = load_iter30_analyzer()
    extract_parts = [Path(part) for part in args.extract_part]
    task_rows, build_report_data, _meta = iter30_module.build_rows(extract_parts, Path(args.gt))
    s0, s0_report = s0_failures(iter30_module, args, task_rows, build_report_data)
    probes = {}
    bootstraps = {}
    s1 = None
    s2 = None
    if not s0:
        for name in site_definitions():
            probes[name] = run_site_probe(task_rows, name)
        s1 = evaluate_s1(probes["all_bridge"])
        if s1["pass"]:
            for name, probe in probes.items():
                if name == "all_bridge":
                    continue
                if not site_metric_failures(probe, probes["all_bridge"]):
                    bootstraps[name] = bootstrap_scene_clusters(probe)
            s2 = evaluate_s2(probes, bootstraps)

    final_verdict = verdict(not s0, s1, s2)
    return {
        "schema_version": "sentinel.iter36_bridge_site_decomposition.report.v1",
        "experiment_id": "iter36_bridge_site_decomposition",
        "verdict": final_verdict,
        "status": "pass" if final_verdict.endswith("AUTHORIZED") else "null",
        "command_line": " ".join(sys.argv),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "submitted_model_mutated": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "s0_pass": not s0,
        "s0_failures": s0,
        "s0": s0_report,
        "s1": s1,
        "s2": s2,
        "probes": {name: compact_probe(probe) for name, probe in probes.items()},
        "next_authorized_action": (
            "publish RESULT.md from this report; no GPU/gcloud work, heldout replay, iteration-12 "
            "scoring, selector evaluation, closed-loop work, deployment language, safety claim, "
            "direction, or alpha is authorized"
        ),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract-part", action="append")
    parser.add_argument("--gt", default=str(PROOF29 / "sentinel_e29_stage1_gt.jsonl.gz"))
    parser.add_argument("--s0-report", default=str(PROOF29 / "s0_integrity_report.json"))
    parser.add_argument("--label-atlas-report", default=str(PROOF29 / "label_atlas_report.json"))
    parser.add_argument("--sha256s", default=str(PROOF29 / "sha256s.txt"))
    parser.add_argument("--iter30-report", default=str(PROOF30 / "localization_report.json"))
    parser.add_argument("--iter35-report", default=str(PROOF35 / "response_heterogeneity_report.json"))
    parser.add_argument("--out", default=str(PROOF36 / "bridge_site_decomposition_report.json"))
    args = parser.parse_args()
    if args.extract_part is None:
        args.extract_part = [str(path) for path in default_extract_parts()]
    return args


def main() -> int:
    args = parse_args()
    report = build_report(args)
    write_json(Path(args.out), report)
    print(f"iter36 bridge site decomposition: {report['verdict']}")
    print(f"s0_pass={str(report['s0_pass']).lower()}")
    if report["s1"] is not None:
        print(f"s1_pass={str(report['s1']['pass']).lower()}")
    if report["s2"] is not None:
        print(f"s2_pass={str(report['s2']['pass']).lower()}")
        print("passing_sites=" + ",".join(report["s2"]["passing_sites"]))
    print(f"out={args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
