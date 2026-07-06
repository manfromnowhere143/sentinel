#!/usr/bin/env python3
"""Iteration-22 Stage 1 baseline analysis.

Reads the committed baseline extraction artifacts, computes the frozen Stage 1 labels, fits the
low-capacity collapse probe, runs negative controls, and writes the pre-declared anti-collapse
direction for the calibration-grid intervention replay.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path

import numpy as np


DANGER_GAP = 3.5
SAFE_GAP = 5.0
COLLAPSE_SPREAD = 0.5
HIGH_DIVERSITY_SPREAD = 2.0
H_IMM = 3
PCA_MAX = 16
SEED = 22


def load_jsonl(path: str) -> list[dict]:
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt") as f:
        return [json.loads(line) for line in f if line.strip()]


def sigmoid(z):
    z = np.clip(z, -40.0, 40.0)
    return 1.0 / (1.0 + np.exp(-z))


def auc_score(y, score) -> float:
    y = np.asarray(y, dtype=np.int64)
    score = np.asarray(score, dtype=np.float64)
    pos = int(y.sum())
    neg = int(len(y) - pos)
    if pos == 0 or neg == 0:
        return float("nan")
    order = np.argsort(score, kind="mergesort")
    ranks = np.empty_like(order, dtype=np.float64)
    sorted_scores = score[order]
    i = 0
    while i < len(score):
        j = i + 1
        while j < len(score) and sorted_scores[j] == sorted_scores[i]:
            j += 1
        ranks[order[i:j]] = (i + j - 1) / 2.0 + 1.0
        i = j
    rank_sum_pos = ranks[y == 1].sum()
    return float((rank_sum_pos - pos * (pos + 1) / 2.0) / (pos * neg))


def balanced_accuracy(y, pred) -> float:
    y = np.asarray(y, dtype=np.int64)
    pred = np.asarray(pred, dtype=np.int64)
    tp = int(((y == 1) & (pred == 1)).sum())
    tn = int(((y == 0) & (pred == 0)).sum())
    fp = int(((y == 0) & (pred == 1)).sum())
    fn = int(((y == 1) & (pred == 0)).sum())
    tpr = tp / (tp + fn) if (tp + fn) else float("nan")
    tnr = tn / (tn + fp) if (tn + fp) else float("nan")
    return float((tpr + tnr) / 2.0)


def endpoint_spread(cands) -> float:
    pts = [cand[-1] for cand in cands if cand]
    if len(pts) < 2:
        return 0.0
    return float(max(math.hypot(a[0] - b[0], a[1] - b[1]) for a in pts for b in pts))


def closest_gap(plan, objs, futs) -> float:
    best = float("inf")
    for obj, fut in zip(objs, futs):
        ox, oy = obj[0], obj[1]
        mode = fut[0] if fut else []
        if not mode:
            continue
        for k in range(min(H_IMM, len(plan))):
            px, py = plan[k]
            ax = ox + (mode[k][0] if k < len(mode) else mode[-1][0])
            ay = oy + (mode[k][1] if k < len(mode) else mode[-1][1])
            best = min(best, math.hypot(px - ax, py - ay))
    return best


def scene_number(scene: str) -> float:
    try:
        return float(scene.split("-")[-1])
    except Exception:
        return 0.0


def join_rows(extract_rows: list[dict], gt_rows: list[dict]) -> list[dict]:
    gt_by_ts = {}
    for row in gt_rows:
        ts = row.get("ts")
        if ts in gt_by_ts:
            raise SystemExit(f"duplicate GT timestamp: {ts}")
        gt_by_ts[ts] = row
    joined = []
    for row in extract_rows:
        if row.get("reset"):
            continue
        if "sdc_traj_query_last" not in row:
            row["analysis_error"] = "missing_sdc_traj_query_last"
            joined.append(row)
            continue
        gt = gt_by_ts.get(row.get("ts"))
        if gt is None:
            row = dict(row)
            row["analysis_error"] = "missing_gt"
            joined.append(row)
            continue
        merged = dict(row)
        merged.update({f"gt_{k}": v for k, v in gt.items()})
        joined.append(merged)
    return joined


def annotate(row: dict) -> dict:
    exe_cmd = int(row["command"])
    exe_plan = row["cands"][exe_cmd]
    gap = closest_gap(exe_plan, row.get("objs", []), row.get("futs", []))
    spread = endpoint_spread(row["cands"])
    return {
        "danger_positive": gap < DANGER_GAP,
        "safe_control": gap >= SAFE_GAP,
        "collapse_positive": spread <= COLLAPSE_SPREAD,
        "high_diversity_control": spread >= HIGH_DIVERSITY_SPREAD,
        "eligible_intervention_frame": gap < DANGER_GAP and spread <= COLLAPSE_SPREAD,
        "benign_control_frame": gap >= SAFE_GAP and spread >= HIGH_DIVERSITY_SPREAD,
        "closest_gap": gap,
        "endpoint_spread": spread,
    }


def tensor_feature(row: dict) -> np.ndarray:
    traj = np.array(row["sdc_traj_query_last"], dtype=np.float64)
    track = np.array(row["sdc_track_query"], dtype=np.float64)
    return np.concatenate([traj, track])


def kin_feature(row: dict) -> np.ndarray:
    return np.array(
        [row["gt_speed"], row["gt_yaw_rate"], row["gt_accel"]],
        dtype=np.float64,
    )


def metadata_feature(row: dict, scene_offsets: dict[str, int]) -> np.ndarray:
    scene = row["gt_scene"]
    idx = scene_offsets[scene]
    scene_offsets[scene] += 1
    return np.array([scene_number(scene), float(idx)], dtype=np.float64)


def split_xy(rows: list[dict], feature_fn, split: str):
    xs, ys = [], []
    for row in rows:
        if row["gt_split"] != split:
            continue
        if row["collapse_positive"]:
            xs.append(feature_fn(row))
            ys.append(1)
        elif row["high_diversity_control"]:
            xs.append(feature_fn(row))
            ys.append(0)
    if not xs:
        return np.empty((0, 0), dtype=np.float64), np.array([], dtype=np.float64)
    return np.vstack(xs), np.array(ys, dtype=np.float64)


def standardize_fit(xfit, *others):
    mu = xfit.mean(axis=0)
    sd = xfit.std(axis=0)
    sd[sd < 1e-6] = 1.0
    return (xfit - mu) / sd, [((x - mu) / sd) for x in others], mu, sd


def pca_fit(xfit, *others):
    rank = int(np.linalg.matrix_rank(xfit))
    n_comp = min(PCA_MAX, rank, xfit.shape[0], xfit.shape[1])
    if n_comp <= 0:
        raise SystemExit("PCA rank is zero")
    _, _, vt = np.linalg.svd(xfit, full_matrices=False)
    basis = vt[:n_comp].T
    return xfit @ basis, [x @ basis for x in others], basis


def fit_logistic(x, y, seed: int = SEED):
    rng = np.random.default_rng(seed)
    w = rng.normal(0.0, 0.01, size=x.shape[1])
    b = 0.0
    pos = float(y.sum())
    neg = float(len(y) - pos)
    if pos == 0 or neg == 0:
        raise SystemExit("logistic fit needs both classes")
    weights = np.where(y == 1, len(y) / (2.0 * pos), len(y) / (2.0 * neg))
    denom = weights.sum()
    lr = 0.05
    for step in range(5000):
        p = sigmoid(x @ w + b)
        err = weights * (p - y)
        grad_w = (x.T @ err) / denom + w / max(len(y), 1)
        grad_b = float(err.sum() / denom)
        w -= lr * grad_w
        b -= lr * grad_b
        if step in (1000, 2500):
            lr *= 0.5
    return w, b


def choose_threshold(ycal, pcal):
    best = (-1.0, 0.5)
    for t in np.linspace(0.0, 1.0, 201):
        ba = balanced_accuracy(ycal, pcal >= t)
        if ba > best[0]:
            best = (ba, float(t))
    return best[1], best[0]


def run_probe(rows: list[dict], feature_fn, name: str, shuffle_fit: bool = False):
    xfit, yfit = split_xy(rows, feature_fn, "fit")
    xcal, ycal = split_xy(rows, feature_fn, "calibration")
    xheld, yheld = split_xy(rows, feature_fn, "heldout")
    for label, y in (("fit", yfit), ("calibration", ycal), ("heldout", yheld)):
        if len(y) == 0 or int(y.sum()) == 0 or int(len(y) - y.sum()) == 0:
            raise SystemExit(f"{name} probe lacks both classes on {label} split")
    if shuffle_fit:
        rng = np.random.default_rng(SEED)
        yfit = rng.permutation(yfit)
    xfit_s, (xcal_s, xheld_s), mu, sd = standardize_fit(xfit, xcal, xheld)
    xfit_p, (xcal_p, xheld_p), basis = pca_fit(xfit_s, xcal_s, xheld_s)
    w, b = fit_logistic(xfit_p, yfit)
    pcal = sigmoid(xcal_p @ w + b)
    pheld = sigmoid(xheld_p @ w + b)
    threshold, cal_ba = choose_threshold(ycal, pcal)
    held_pred = pheld >= threshold
    return {
        "name": name,
        "n_fit": int(len(yfit)),
        "n_calibration": int(len(ycal)),
        "n_heldout": int(len(yheld)),
        "fit_positive": int(yfit.sum()),
        "calibration_positive": int(ycal.sum()),
        "heldout_positive": int(yheld.sum()),
        "pca_components": int(basis.shape[1]),
        "threshold": threshold,
        "calibration_balanced_accuracy": cal_ba,
        "heldout_auc": auc_score(yheld, pheld),
        "heldout_balanced_accuracy": balanced_accuracy(yheld, held_pred),
        "coef_norm": float(np.linalg.norm(w)),
        "mu_sha256_placeholder": "reported via full artifact hashes in RESULT",
        "sd_sha256_placeholder": "reported via full artifact hashes in RESULT",
    }


def count_by_split(rows, key):
    out = {}
    for split in ("fit", "calibration", "heldout"):
        vals = [row for row in rows if row["gt_split"] == split]
        out[split] = int(sum(bool(row[key]) for row in vals))
    return out


def count_floor_pass(counts: dict) -> tuple[bool, list[str]]:
    failures = []
    heldout = "heldout"
    requirements = [
        ("collapse_positive", heldout, 30),
        ("high_diversity_control", heldout, 30),
        ("danger_positive", heldout, 30),
        ("safe_control", heldout, 30),
        ("eligible_intervention_frame", heldout, 20),
        ("benign_control_frame", heldout, 20),
    ]
    for key, split, minimum in requirements:
        value = counts[key][split]
        if value < minimum:
            failures.append(f"{key}.{split}={value} < {minimum}")
    return not failures, failures


def write_direction(rows: list[dict], out_dir: Path):
    fit_collapse = [tensor_feature(r) for r in rows if r["gt_split"] == "fit" and r["collapse_positive"]]
    fit_high = [tensor_feature(r) for r in rows if r["gt_split"] == "fit" and r["high_diversity_control"]]
    if not fit_collapse or not fit_high:
        raise SystemExit("cannot write direction without fit collapse/high-diversity rows")
    mean_collapse = np.vstack(fit_collapse).mean(axis=0)
    mean_high = np.vstack(fit_high).mean(axis=0)
    direction = mean_high - mean_collapse
    norm = float(np.linalg.norm(direction))
    if norm <= 1e-9:
        raise SystemExit("direction norm is zero")
    direction /= norm
    first = rows[0]
    traj_len = len(first["sdc_traj_query_last"])
    payload = {
        "source": "iter22 Stage 1 fit split: mean(high_diversity_control) - mean(collapse_positive)",
        "norm_before_normalization": norm,
        "sdc_traj_query_last_shape": first["sdc_traj_query_last_shape"],
        "sdc_track_query_shape": first["sdc_track_query_shape"],
        "sdc_traj_query_last_direction": direction[:traj_len].astype(float).tolist(),
        "sdc_track_query_direction": direction[traj_len:].astype(float).tolist(),
    }
    path = out_dir / "sentinel_e22_direction.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    extract_rows = load_jsonl(args.extract)
    gt_rows = load_jsonl(args.gt)
    joined = join_rows(extract_rows, gt_rows)
    errors = [r for r in joined if r.get("analysis_error") or any(k.endswith("_err") for k in r)]
    rows = [r for r in joined if "sdc_traj_query_last" in r and not r.get("analysis_error")]
    for row in rows:
        row.update(annotate(row))

    scene_offsets: dict[str, int] = {}
    for row in rows:
        scene_offsets.setdefault(row["gt_scene"], 0)
    for row in rows:
        row["_metadata_feature"] = metadata_feature(row, scene_offsets)

    counts = {
        "extract_rows_total": len(extract_rows),
        "gt_rows_total": len(gt_rows),
        "joined_scored_rows": len(rows),
        "error_rows": len(errors),
        "collapse_positive": count_by_split(rows, "collapse_positive"),
        "high_diversity_control": count_by_split(rows, "high_diversity_control"),
        "danger_positive": count_by_split(rows, "danger_positive"),
        "safe_control": count_by_split(rows, "safe_control"),
        "eligible_intervention_frame": count_by_split(rows, "eligible_intervention_frame"),
        "benign_control_frame": count_by_split(rows, "benign_control_frame"),
    }

    s0_counts_ok, count_failures = count_floor_pass(counts)
    if not s0_counts_ok:
        metrics = {
            "counts": counts,
            "s0_count_floor_pass": False,
            "s0_count_floor_failures": count_failures,
            "stage1_verdict": "DATA_NULL_STOP_BEFORE_PROBE_OR_INTERVENTION",
            "claim_boundary": (
                "The frozen split did not meet the Stage 1 minimum count floors. Per the "
                "pre-registration, publish this as a data-null and do not fit probes, write an "
                "activation direction, run the calibration grid, touch iteration-12 frames, or "
                "start closed-loop work."
            ),
        }
        (out_dir / "stage1_baseline_metrics.json").write_text(
            json.dumps(metrics, indent=2, sort_keys=True) + "\n"
        )
        print(json.dumps(metrics, indent=2, sort_keys=True))
        return 0

    probes = [
        run_probe(rows, tensor_feature, "internal_tensor"),
        run_probe(rows, kin_feature, "ego_kinematics"),
        run_probe(rows, lambda r: r["_metadata_feature"], "scene_frame_metadata"),
        run_probe(rows, tensor_feature, "shuffled_label_internal_tensor", shuffle_fit=True),
    ]
    internal_auc = probes[0]["heldout_auc"]
    control_best_auc = max(p["heldout_auc"] for p in probes[1:] if not math.isnan(p["heldout_auc"]))
    s1_pass = (
        internal_auc >= 0.80
        and probes[0]["heldout_balanced_accuracy"] >= 0.70
        and internal_auc - control_best_auc >= 0.10
    )
    direction_path = write_direction(rows, out_dir)
    metrics = {
        "counts": counts,
        "probes": probes,
        "s0_count_floor_pass": True,
        "s1_pass_if_counts_pass": bool(s1_pass),
        "direction_json": str(direction_path),
        "claim_boundary": (
            "Probe success is diagnostic only; the direction artifact authorizes only the "
            "pre-registered calibration-grid replay, not an iteration-12 or closed-loop claim."
        ),
    }
    (out_dir / "stage1_baseline_metrics.json").write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
