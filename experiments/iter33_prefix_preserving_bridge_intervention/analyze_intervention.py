#!/usr/bin/env python3
"""Analyze iteration-33 prefix-preserving bridge-intervention replay logs.

The analyzer is intentionally split into pure metric functions plus a small CLI
so calibration/heldout reports can be regenerated from committed JSONL proof.
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
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
ITER29 = ROOT / "experiments/iter29_trainval_risk_support_atlas"
JOIN_KEY = ("scene", "sample_index", "timestamp_us")
DANGER_THRESHOLD_M = 4.5
SAFE_THRESHOLD_M = 6.0
LOW_DIVERSITY_THRESHOLD_M = 1.5
HIGH_DIVERSITY_THRESHOLD_M = 2.0
GROSS_MAX_ABS_COORD_M = 100.0
GROSS_MAX_STEP_M = 20.0
ALPHA_ZERO_BASELINE_TOLERANCE = 1e-5
ALPHA_GRID = (0.0, 0.25, 0.5, 0.75, 1.0)
EXPECTED_ITER32_MODEL_TARGET_SHA = "2495f9a1dc4d7f7544673cd4dc25c1283977087a0018b37e76184a2b3c0b611e"
EXPECTED_ITER32_GT_TARGET_SHA = "5064a3177c7918712fa56533b897e50a7d731f516d17a9ca6241ef67296050c7"
PREFIX_EXPECTED = {
    "canary": {"non_reset_rows": 44, "target_rows": 12, "context_only_rows": 32},
    "calibration": {"non_reset_rows": 4293, "target_rows": 2452, "context_only_rows": 1841},
    "heldout": {"non_reset_rows": 4283, "target_rows": 2403, "context_only_rows": 1880},
}
CALIBRATION_EXPECTED_COUNTS = {"eligible_lowdiv": 108, "benign_control": 2344}
HELDOUT_EXPECTED_COUNTS = {"eligible_lowdiv": 158, "benign_control": 2245}


class ChainedBinaryReader(io.RawIOBase):
    def __init__(self, paths: Iterable[Path]) -> None:
        self.paths = iter(paths)
        self.current = None

    def readable(self) -> bool:
        return True

    def readinto(self, buffer) -> int:
        view = memoryview(buffer)
        total = 0
        while total < len(view):
            if self.current is None:
                try:
                    self.current = next(self.paths).open("rb")
                except StopIteration:
                    break
            read = self.current.readinto(view[total:])
            if read:
                total += read
                break
            self.current.close()
            self.current = None
        return total

    def close(self) -> None:
        if self.current is not None:
            self.current.close()
            self.current = None
        super().close()


def open_text(path: Path):
    if ".gz" in path.suffixes:
        return gzip.open(path, "rt", encoding="utf-8")
    return path.open("rt", encoding="utf-8")


def is_gzip_part(path: Path) -> bool:
    return ".gz" in path.suffixes and any(suffix.startswith(".part-") for suffix in path.suffixes)


def iter_gzip_parts(paths: list[Path]):
    reader = ChainedBinaryReader(sorted(paths))
    with reader:
        with gzip.GzipFile(fileobj=io.BufferedReader(reader), mode="rb") as gz:
            with io.TextIOWrapper(gz, encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        yield json.loads(line)


def iter_jsonl(paths: Iterable[Path]):
    gzip_parts = []
    for path in paths:
        if is_gzip_part(path):
            gzip_parts.append(path)
            continue
        if gzip_parts:
            yield from iter_gzip_parts(gzip_parts)
            gzip_parts = []
        with open_text(path) as f:
            for line in f:
                if line.strip():
                    yield json.loads(line)
    if gzip_parts:
        yield from iter_gzip_parts(gzip_parts)


def canonical_jsonl_sha256(path: Path) -> tuple[str, int]:
    h = hashlib.sha256()
    rows = 0
    with open_text(path) as f:
        for line in f:
            if not line.strip():
                continue
            payload = json.loads(line)
            encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
            h.update(encoded)
            h.update(b"\n")
            rows += 1
    return h.hexdigest(), rows


def canonical_rows_sha256(rows: list[dict]) -> str:
    h = hashlib.sha256()
    for row in rows:
        encoded = json.dumps(row, sort_keys=True, separators=(",", ":")).encode()
        h.update(encoded)
        h.update(b"\n")
    return h.hexdigest()


def key_of(row: dict) -> tuple:
    return (row.get("scene"), int(row.get("sample_index")), int(row.get("timestamp_us")))


def default_iter29_extract_parts() -> list[Path]:
    return sorted((ITER29 / "proof-full-extract").glob("sentinel_e29_stage1.jsonl.gz.part-*"))


def key_label(key: tuple) -> str:
    return f"{key[0]}:{key[1]}:{key[2]}"


def max_abs_nested_delta(a, b) -> float:
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if not math.isfinite(float(a)) or not math.isfinite(float(b)):
            return float("inf")
        return abs(float(a) - float(b))
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        if not a:
            return 0.0
        return max(max_abs_nested_delta(x, y) for x, y in zip(a, b))
    return float("inf")


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


def finite_point(point: list) -> bool:
    if len(point) < 2:
        return False
    return math.isfinite(float(point[0])) and math.isfinite(float(point[1]))


def gross_valid_trajectory(plan: list) -> bool:
    if not plan:
        return False
    for point in plan:
        if not finite_point(point):
            return False
        if abs(float(point[0])) > GROSS_MAX_ABS_COORD_M:
            return False
        if abs(float(point[1])) > GROSS_MAX_ABS_COORD_M:
            return False
    for prev, cur in zip(plan, plan[1:]):
        if math.hypot(float(cur[0]) - float(prev[0]), float(cur[1]) - float(prev[1])) > GROSS_MAX_STEP_M:
            return False
    return True


def gross_valid_row(row: dict) -> bool:
    plans = []
    for name in ("intervened_traj", "original_traj"):
        if name in row:
            plans.append(row[name])
    for name in ("intervened_cands", "original_cands"):
        for cand in row.get(name, []):
            plans.append(cand)
    if not plans:
        plans.append(row.get("traj", []))
        plans.extend(row.get("cands", []))
    return all(gross_valid_trajectory(plan) for plan in plans)


def endpoint_displacement(a: list, b: list) -> float:
    if not a or not b:
        return float("inf")
    return float(math.hypot(float(a[-1][0]) - float(b[-1][0]), float(a[-1][1]) - float(b[-1][1])))


def gap_delta(original: float, intervened: float) -> float:
    if math.isinf(original) and math.isinf(intervened):
        return 0.0
    return intervened - original


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return float("nan")
    xs = sorted(float(v) for v in values)
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * pct / 100.0
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    frac = pos - lo
    return xs[lo] * (1.0 - frac) + xs[hi] * frac


def median(values: list[float]) -> float:
    return percentile(values, 50.0)


def classify(gap: float, spread: float) -> dict:
    return {
        "danger_4p5": gap < DANGER_THRESHOLD_M,
        "safe_6p0": gap >= SAFE_THRESHOLD_M,
        "low_diversity_1p5": spread <= LOW_DIVERSITY_THRESHOLD_M,
        "high_diversity_2p0": spread >= HIGH_DIVERSITY_THRESHOLD_M,
    }


def row_metrics(row: dict) -> dict:
    original_traj = row.get("original_traj", row.get("traj", []))
    original_cands = row.get("original_cands", row.get("cands", []))
    intervened_traj = row.get("intervened_traj", row.get("traj", []))
    intervened_cands = row.get("intervened_cands", row.get("cands", []))
    objs = row.get("objs", [])
    futs = row.get("futs", [])

    original_spread = endpoint_spread(original_cands)
    intervened_spread = endpoint_spread(intervened_cands)
    original_candidate_gaps = [closest_gap(cand, objs, futs) for cand in original_cands]
    intervened_candidate_gaps = [closest_gap(cand, objs, futs) for cand in intervened_cands]
    original_best_gap = max(original_candidate_gaps) if original_candidate_gaps else float("inf")
    intervened_best_gap = max(intervened_candidate_gaps) if intervened_candidate_gaps else float("inf")
    original_executed_gap = closest_gap(original_traj, objs, futs)
    intervened_executed_gap = closest_gap(intervened_traj, objs, futs)
    base_class = classify(original_executed_gap, original_spread)
    int_class = classify(intervened_executed_gap, intervened_spread)

    return {
        "scene": row.get("scene"),
        "split": row.get("split"),
        "sample_index": row.get("sample_index"),
        "timestamp_us": row.get("timestamp_us"),
        "target_row": bool(row.get("target_row", False)),
        "alpha": float(row.get("intervention_alpha", row.get("alpha", 0.0))),
        "label_name": row.get("label_name"),
        "error": bool(row.get("error") or row.get("context_error") or row.get("intervention_error")),
        "gross_valid": gross_valid_row(row),
        "original_endpoint_spread": original_spread,
        "intervened_endpoint_spread": intervened_spread,
        "endpoint_spread_delta": intervened_spread - original_spread,
        "original_best_candidate_gap": original_best_gap,
        "intervened_best_candidate_gap": intervened_best_gap,
        "best_candidate_gap_delta": gap_delta(original_best_gap, intervened_best_gap),
        "original_executed_gap": original_executed_gap,
        "intervened_executed_gap": intervened_executed_gap,
        "executed_gap_delta": gap_delta(original_executed_gap, intervened_executed_gap),
        "executed_endpoint_displacement": endpoint_displacement(original_traj, intervened_traj),
        "benign_crossed_danger": (
            base_class["safe_6p0"] and int_class["danger_4p5"]
        ),
        "benign_collapsed_lowdiv": (
            base_class["high_diversity_2p0"] and int_class["low_diversity_1p5"]
        ),
    }


def summarize_label(metrics: list[dict], label_name: str) -> dict:
    rows = [row for row in metrics if row.get("label_name") == label_name]
    spread_delta = [row["endpoint_spread_delta"] for row in rows]
    best_gap_delta = [row["best_candidate_gap_delta"] for row in rows]
    executed_disp = [row["executed_endpoint_displacement"] for row in rows]
    n = len(rows)
    return {
        "rows": n,
        "gross_validity_failures": sum(1 for row in rows if not row["gross_valid"]),
        "median_endpoint_spread_delta": median(spread_delta),
        "fraction_endpoint_spread_delta_gt_0p25": (
            sum(1 for value in spread_delta if value > 0.25) / n if n else float("nan")
        ),
        "fraction_endpoint_spread_delta_ge_0p25": (
            sum(1 for value in spread_delta if value >= 0.25) / n if n else float("nan")
        ),
        "median_best_candidate_gap_delta": median(best_gap_delta),
        "fraction_best_candidate_gap_delta_lt_neg_0p25": (
            sum(1 for value in best_gap_delta if value < -0.25) / n if n else float("nan")
        ),
        "median_executed_endpoint_displacement": median(executed_disp),
        "p95_executed_endpoint_displacement": percentile(executed_disp, 95.0),
        "danger_cross_count": sum(1 for row in rows if row["benign_crossed_danger"]),
        "danger_cross_fraction": (
            sum(1 for row in rows if row["benign_crossed_danger"]) / n if n else float("nan")
        ),
        "lowdiv_collapse_count": sum(1 for row in rows if row["benign_collapsed_lowdiv"]),
        "lowdiv_collapse_fraction": (
            sum(1 for row in rows if row["benign_collapsed_lowdiv"]) / n if n else float("nan")
        ),
    }


def alpha_cell_summary(metrics: list[dict], alpha: float) -> dict:
    rows = [row for row in metrics if abs(float(row["alpha"]) - alpha) <= 1e-12]
    error_rows = sum(1 for row in rows if row.get("error") or row.get("context_error"))
    eligible = summarize_label(rows, "eligible_lowdiv")
    benign = summarize_label(rows, "benign_control")
    return {
        "alpha": alpha,
        "rows": len(rows),
        "error_rows": error_rows,
        "eligible_lowdiv": eligible,
        "benign_control": benign,
    }


def calibration_eligible(cell: dict) -> tuple[bool, list[str]]:
    alpha = float(cell["alpha"])
    failures = []
    eligible = cell["eligible_lowdiv"]
    benign = cell["benign_control"]
    if alpha == 0.0:
        failures.append("alpha_zero_not_selectable")
    if eligible["rows"] != CALIBRATION_EXPECTED_COUNTS["eligible_lowdiv"]:
        failures.append(
            f"eligible_rows={eligible['rows']} != {CALIBRATION_EXPECTED_COUNTS['eligible_lowdiv']}"
        )
    if benign["rows"] != CALIBRATION_EXPECTED_COUNTS["benign_control"]:
        failures.append(
            f"benign_rows={benign['rows']} != {CALIBRATION_EXPECTED_COUNTS['benign_control']}"
        )
    if cell["error_rows"] != 0:
        failures.append(f"error_rows={cell['error_rows']} != 0")
    if eligible["gross_validity_failures"] != 0 or benign["gross_validity_failures"] != 0:
        failures.append("gross_validity_failures_nonzero")
    if eligible["median_endpoint_spread_delta"] <= 0.25:
        failures.append(
            "eligible_median_endpoint_spread_delta="
            f"{eligible['median_endpoint_spread_delta']:.6f} <= 0.25"
        )
    if eligible["fraction_endpoint_spread_delta_gt_0p25"] < 0.50:
        failures.append(
            "eligible_fraction_endpoint_spread_delta_gt_0p25="
            f"{eligible['fraction_endpoint_spread_delta_gt_0p25']:.6f} < 0.50"
        )
    if eligible["median_best_candidate_gap_delta"] < 0.0:
        failures.append(
            "eligible_median_best_candidate_gap_delta="
            f"{eligible['median_best_candidate_gap_delta']:.6f} < 0.0"
        )
    if benign["median_executed_endpoint_displacement"] > 0.50:
        failures.append(
            "benign_median_executed_endpoint_displacement="
            f"{benign['median_executed_endpoint_displacement']:.6f} > 0.50"
        )
    if benign["p95_executed_endpoint_displacement"] > 2.0:
        failures.append(
            "benign_p95_executed_endpoint_displacement="
            f"{benign['p95_executed_endpoint_displacement']:.6f} > 2.0"
        )
    if benign["danger_cross_fraction"] > 0.05:
        failures.append(f"benign_danger_cross_fraction={benign['danger_cross_fraction']:.6f} > 0.05")
    if benign["lowdiv_collapse_fraction"] > 0.05:
        failures.append(f"benign_lowdiv_collapse_fraction={benign['lowdiv_collapse_fraction']:.6f} > 0.05")
    if benign["median_endpoint_spread_delta"] < -0.25:
        failures.append(
            "benign_median_endpoint_spread_delta="
            f"{benign['median_endpoint_spread_delta']:.6f} < -0.25"
        )
    return not failures, failures


def select_calibration_alpha(cells: list[dict]) -> dict:
    enriched = []
    for cell in cells:
        ok, failures = calibration_eligible(cell)
        enriched.append({**cell, "calibration_eligible": ok, "calibration_failures": failures})
    candidates = [cell for cell in enriched if cell["calibration_eligible"] and cell["alpha"] != 0.0]
    if not candidates:
        return {
            "selected_alpha": None,
            "selected": False,
            "verdict": "CALIBRATION_NULL_NO_USABLE_ALPHA",
            "cells": enriched,
        }
    candidates = sorted(
        candidates,
        key=lambda cell: (
            -cell["eligible_lowdiv"]["median_endpoint_spread_delta"],
            cell["alpha"],
        ),
    )
    selected = candidates[0]
    return {
        "selected_alpha": selected["alpha"],
        "selected": True,
        "verdict": "CALIBRATION_ALPHA_SELECTED",
        "selection_metric": "max eligible median_endpoint_spread_delta on eligible_lowdiv; tie smallest alpha",
        "cells": enriched,
    }


def heldout_bars(metrics: list[dict]) -> dict:
    eligible = summarize_label(metrics, "eligible_lowdiv")
    benign = summarize_label(metrics, "benign_control")
    error_rows = sum(1 for row in metrics if row.get("error"))
    s2_failures = []
    if error_rows != 0:
        s2_failures.append(f"error_rows={error_rows} != 0")
    if eligible["rows"] != HELDOUT_EXPECTED_COUNTS["eligible_lowdiv"]:
        s2_failures.append(
            f"eligible_rows={eligible['rows']} != {HELDOUT_EXPECTED_COUNTS['eligible_lowdiv']}"
        )
    if eligible["gross_validity_failures"] != 0:
        s2_failures.append("eligible_gross_validity_failures_nonzero")
    if eligible["median_endpoint_spread_delta"] < 0.50:
        s2_failures.append(
            f"eligible_median_endpoint_spread_delta={eligible['median_endpoint_spread_delta']:.6f} < 0.50"
        )
    if eligible["fraction_endpoint_spread_delta_ge_0p25"] < 0.60:
        s2_failures.append(
            "eligible_fraction_endpoint_spread_delta_ge_0p25="
            f"{eligible['fraction_endpoint_spread_delta_ge_0p25']:.6f} < 0.60"
        )
    if eligible["median_best_candidate_gap_delta"] < 0.10:
        s2_failures.append(
            f"eligible_median_best_candidate_gap_delta={eligible['median_best_candidate_gap_delta']:.6f} < 0.10"
        )
    if eligible["fraction_best_candidate_gap_delta_lt_neg_0p25"] > 0.25:
        s2_failures.append(
            "eligible_fraction_best_candidate_gap_delta_lt_neg_0p25="
            f"{eligible['fraction_best_candidate_gap_delta_lt_neg_0p25']:.6f} > 0.25"
        )

    s3_failures = []
    if error_rows != 0:
        s3_failures.append(f"error_rows={error_rows} != 0")
    if benign["rows"] != HELDOUT_EXPECTED_COUNTS["benign_control"]:
        s3_failures.append(
            f"benign_rows={benign['rows']} != {HELDOUT_EXPECTED_COUNTS['benign_control']}"
        )
    if benign["gross_validity_failures"] != 0:
        s3_failures.append("benign_gross_validity_failures_nonzero")
    if benign["median_executed_endpoint_displacement"] > 0.50:
        s3_failures.append(
            "benign_median_executed_endpoint_displacement="
            f"{benign['median_executed_endpoint_displacement']:.6f} > 0.50"
        )
    if benign["p95_executed_endpoint_displacement"] > 2.0:
        s3_failures.append(
            f"benign_p95_executed_endpoint_displacement={benign['p95_executed_endpoint_displacement']:.6f} > 2.0"
        )
    if benign["danger_cross_fraction"] > 0.05:
        s3_failures.append(f"benign_danger_cross_fraction={benign['danger_cross_fraction']:.6f} > 0.05")
    if benign["lowdiv_collapse_fraction"] > 0.05:
        s3_failures.append(f"benign_lowdiv_collapse_fraction={benign['lowdiv_collapse_fraction']:.6f} > 0.05")
    if benign["median_endpoint_spread_delta"] < -0.25:
        s3_failures.append(
            f"benign_median_endpoint_spread_delta={benign['median_endpoint_spread_delta']:.6f} < -0.25"
        )
    return {
        "eligible_lowdiv": eligible,
        "benign_control": benign,
        "error_rows": error_rows,
        "s2_pass": not s2_failures,
        "s2_failures": s2_failures,
        "s3_pass": not s3_failures,
        "s3_failures": s3_failures,
    }


def target_rows(rows: list[dict]) -> list[dict]:
    return [row for row in rows if not row.get("reset") and bool(row.get("target_row", False))]


def context_rows(rows: list[dict]) -> list[dict]:
    return [row for row in rows if not row.get("reset") and not bool(row.get("target_row", False))]


def context_contamination_report(rows: list[dict]) -> dict:
    context = context_rows(rows)
    failures = []
    for row in context:
        key = key_label((row.get("scene"), row.get("sample_index", -1), row.get("timestamp_us", -1)))
        alpha = float(row.get("intervention_alpha", row.get("alpha", 0.0)) or 0.0)
        if abs(alpha) > 1e-12:
            failures.append(f"{key}:context_intervention_alpha={alpha} != 0")
        if row.get("intervention_applied") is True:
            failures.append(f"{key}:context_intervention_applied_true")
        if row.get("bridge_sha256_changed") is True:
            failures.append(f"{key}:context_bridge_sha256_changed_true")
    return {
        "context_only_rows": len(context),
        "context_contamination_pass": not failures,
        "context_contamination_failure_count": len(failures),
        "context_contamination_failures": failures[:50],
    }


def run_row_summary(path: Path, stage: str) -> dict:
    rows = [row for row in iter_jsonl([path]) if not row.get("reset")]
    targets = target_rows(rows)
    context = context_rows(rows)
    expected = PREFIX_EXPECTED[stage]
    error_rows = sum(1 for row in rows if row.get("error") or row.get("context_error") or row.get("intervention_error"))
    failures = []
    if len(rows) != expected["non_reset_rows"]:
        failures.append(f"non_reset_rows={len(rows)} != {expected['non_reset_rows']}")
    if len(targets) != expected["target_rows"]:
        failures.append(f"target_rows={len(targets)} != {expected['target_rows']}")
    if len(context) != expected["context_only_rows"]:
        failures.append(f"context_only_rows={len(context)} != {expected['context_only_rows']}")
    if error_rows:
        failures.append(f"error_rows={error_rows} != 0")
    contamination = context_contamination_report(rows)
    if not contamination["context_contamination_pass"]:
        failures.extend(contamination["context_contamination_failures"])
    return {
        "path": str(path),
        "rows": rows,
        "target_rows_data": targets,
        "non_reset_rows": len(rows),
        "target_rows": len(targets),
        "context_only_rows": len(context),
        "error_rows": error_rows,
        "row_count_pass": not failures,
        "row_count_failures": failures,
        **contamination,
    }


def public_run_summary(summary: dict) -> dict:
    return {key: value for key, value in summary.items() if key not in {"rows", "target_rows_data"}}


def target_metrics_from_paths(paths: list[Path], stage: str) -> tuple[list[dict], list[dict]]:
    summaries = [run_row_summary(path, stage) for path in paths]
    rows = []
    for summary in summaries:
        rows.extend(summary["target_rows_data"])
    metrics = [row_metrics(row) for row in rows]
    return summaries, metrics


def analyze_calibration(paths: list[Path]) -> dict:
    summaries, metrics = target_metrics_from_paths(paths, "calibration")
    counts = Counter((round(float(row["alpha"]), 12), row.get("label_name")) for row in metrics)
    cells = [alpha_cell_summary(metrics, alpha) for alpha in ALPHA_GRID]
    selection = select_calibration_alpha(cells)
    prefix_failures = [
        failure
        for summary in summaries
        for failure in summary["row_count_failures"]
    ]
    if prefix_failures:
        for cell in selection["cells"]:
            cell["calibration_eligible"] = False
            cell["calibration_failures"] = [*cell["calibration_failures"], "prefix_replay_integrity_failed"]
        selection["selected_alpha"] = None
        selection["selected"] = False
        selection["verdict"] = "INFRASTRUCTURE_NULL_PREFIX_REPLAY_INTEGRITY_FAIL"
    return {
        "stage": "iter33_calibration_grid",
        "command_line": " ".join(sys.argv),
        "run_summaries": [public_run_summary(summary) for summary in summaries],
        "prefix_replay_integrity_pass": not prefix_failures,
        "prefix_replay_integrity_failures": prefix_failures[:100],
        "metric_scope": "target_row_only",
        "row_counts_by_alpha_label": {f"{alpha}:{label}": count for (alpha, label), count in sorted(counts.items())},
        **selection,
        "claim_boundary": (
            "Calibration selects at most one global alpha using target rows only. It is not a "
            "heldout result, selector score, closed-loop result, deployment result, or safety claim."
        ),
    }


def analyze_heldout(paths: list[Path]) -> dict:
    summaries, metrics = target_metrics_from_paths(paths, "heldout")
    bars = heldout_bars(metrics)
    prefix_failures = [
        failure
        for summary in summaries
        for failure in summary["row_count_failures"]
    ]
    if prefix_failures:
        bars["s2_pass"] = False
        bars["s3_pass"] = False
        bars["s2_failures"] = [*bars["s2_failures"], "prefix_replay_integrity_failed"]
        bars["s3_failures"] = [*bars["s3_failures"], "prefix_replay_integrity_failed"]
        verdict = "INFRASTRUCTURE_NULL_PREFIX_REPLAY_INTEGRITY_FAIL"
    elif not bars["s2_pass"]:
        verdict = "DIAGNOSTIC_BUT_NOT_CAUSAL_NULL"
    elif not bars["s3_pass"]:
        verdict = "CAUSAL_BUT_UNSAFE_OR_NONSPECIFIC_NULL"
    else:
        verdict = "PREFIX_BRIDGE_INTERVENTION_STAGE1_PASS_SUCCESSOR_PREREG_AUTHORIZED"
    return {
        "stage": "iter33_heldout_bridge_intervention",
        "command_line": " ".join(sys.argv),
        "run_summaries": [public_run_summary(summary) for summary in summaries],
        "prefix_replay_integrity_pass": not prefix_failures,
        "prefix_replay_integrity_failures": prefix_failures[:100],
        "metric_scope": "target_row_only",
        **bars,
        "verdict": verdict,
        "claim_boundary": (
            "A pass authorizes only a separate Stage-2 pre-registration. It does not authorize "
            "iteration-12 scoring, selector evaluation, closed-loop work, deployment, or a safety claim."
        ),
    }


def alpha_zero_reference_report(canary_rows: list[dict], reference_rows: list[dict]) -> dict:
    reference_by_key = {key_of(row): row for row in reference_rows if not row.get("reset")}
    alpha_zero_rows = [
        row
        for row in target_rows(canary_rows)
        if abs(float(row.get("intervention_alpha", row.get("alpha", 0.0)))) <= 1e-12
    ]
    failures = []
    max_delta = 0.0
    comparisons = 0
    for row in alpha_zero_rows:
        key = key_of(row)
        reference = reference_by_key.get(key)
        if reference is None:
            failures.append(f"{key_label(key)}:missing_iter29_reference")
            continue
        if row.get("intervention_applied") is not False:
            failures.append(f"{key_label(key)}:alpha_zero_intervention_applied_not_false")
        for canary_field, reference_field in (
            ("intervened_traj", "traj"),
            ("intervened_cands", "cands"),
            ("original_traj", "traj"),
            ("original_cands", "cands"),
        ):
            if canary_field not in row:
                failures.append(f"{key_label(key)}:missing_{canary_field}")
                continue
            delta = max_abs_nested_delta(row[canary_field], reference.get(reference_field))
            max_delta = max(max_delta, delta)
            comparisons += 1
            if delta > ALPHA_ZERO_BASELINE_TOLERANCE:
                failures.append(
                    f"{key_label(key)}:{canary_field}_vs_iter29_{reference_field}_"
                    f"max_abs={delta:.9g}"
                )
    if not alpha_zero_rows:
        failures.append("alpha_zero_rows=0")
    return {
        "alpha_zero_reference_checked": True,
        "alpha_zero_rows": len(alpha_zero_rows),
        "alpha_zero_reference_comparisons": comparisons,
        "alpha_zero_max_abs_coordinate_error": max_delta,
        "alpha_zero_reference_tolerance": ALPHA_ZERO_BASELINE_TOLERANCE,
        "alpha_zero_reference_pass": not failures,
        "alpha_zero_reference_failures": failures[:50],
        "alpha_zero_reference_failure_count": len(failures),
    }


def alpha_key(row: dict) -> str:
    alpha = float(row.get("run_alpha", row.get("intervention_alpha", row.get("alpha", 0.0))) or 0.0)
    return f"{alpha:.2f}".replace(".", "p")


def iter32_model_projection(row: dict) -> dict:
    return {
        "bridge_sha256": row.get("bridge_sha256", row.get("intervened_bridge_sha256")),
        "cands": row.get("cands", row.get("intervened_cands", [])),
        "command": row.get("command"),
        "futs": row.get("futs", []),
        "intervention_alpha": 0.0,
        "intervention_applied": False,
        "intervention_direction_json": "",
        "iter32_patch_mode": "prefix_replay_noop",
        "objs": row.get("objs", []),
        "runner_timestamp": row.get("runner_timestamp"),
        "sample_index": row.get("sample_index"),
        "scene": row.get("scene"),
        "scores": row.get("scores", []),
        "sdc_track_query": row.get("sdc_track_query", []),
        "sdc_track_query_dtype": row.get("sdc_track_query_dtype"),
        "sdc_track_query_shape": row.get("sdc_track_query_shape"),
        "sdc_traj_query_last": row.get("sdc_traj_query_last", []),
        "sdc_traj_query_last_dtype": row.get("sdc_traj_query_last_dtype"),
        "sdc_traj_query_last_shape": row.get("sdc_traj_query_last_shape"),
        "source_label": row.get("source_label"),
        "source_label_name": row.get("source_label_name"),
        "split": row.get("split"),
        "target_row": bool(row.get("target_row")),
        "timestamp_us": row.get("timestamp_us"),
        "traj": row.get("traj", row.get("intervened_traj", [])),
    }


def iter32_gt_projection(row: dict) -> dict:
    return {
        "accel": row.get("accel"),
        "command": row.get("command"),
        "gt_future": row.get("gt_future", []),
        "lat_3s": row.get("lat_3s"),
        "sample_index": row.get("sample_index"),
        "scene": row.get("scene"),
        "source_label": row.get("source_label"),
        "source_label_name": row.get("source_label_name"),
        "speed": row.get("speed"),
        "split": row.get("split"),
        "target_row": bool(row.get("target_row")),
        "timestamp_us": row.get("timestamp_us"),
        "yaw_rate": row.get("yaw_rate"),
    }


def canary_hash_groups(summaries: list[dict], projection) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = defaultdict(list)
    for summary in summaries:
        targets = summary["target_rows_data"]
        if not targets:
            grouped["missing"].append("")
            continue
        key = alpha_key(targets[0])
        projected = [projection(row) for row in targets]
        digest = canonical_rows_sha256(projected)
        summary["target_baseline_projection_sha256"] = digest
        grouped[key].append(digest)
    return grouped


def nonzero_bridge_report(summaries: list[dict]) -> dict:
    failures = []
    changed = 0
    checked = 0
    for summary in summaries:
        for row in summary["target_rows_data"]:
            if abs(float(row.get("run_alpha", row.get("intervention_alpha", 0.0)) or 0.0) - 0.5) > 1e-12:
                continue
            checked += 1
            key = key_label(key_of(row))
            if row.get("intervention_applied") is not True:
                failures.append(f"{key}:alpha0p50_intervention_applied_not_true")
            if row.get("bridge_sha256_changed") is not True:
                failures.append(f"{key}:alpha0p50_bridge_sha256_changed_not_true")
            if row.get("original_bridge_sha256") == row.get("intervened_bridge_sha256"):
                failures.append(f"{key}:alpha0p50_original_and_intervened_bridge_sha_equal")
            else:
                changed += 1
    if checked != 24:
        failures.append(f"alpha0p50_target_rows_checked={checked} != 24")
    return {
        "alpha0p50_target_rows_checked": checked,
        "alpha0p50_changed_bridge_sha_rows": changed,
        "alpha0p50_bridge_change_pass": not failures,
        "alpha0p50_bridge_change_failures": failures[:50],
    }


def analyze_canary(
    paths: list[Path],
    gt_paths: list[Path] | None = None,
    reference_paths: list[Path] | None = None,
) -> dict:
    model_summaries = [run_row_summary(path, "canary") for path in paths]
    model_groups = canary_hash_groups(model_summaries, iter32_model_projection)
    gt_summaries = []
    gt_groups = {}
    if gt_paths:
        gt_summaries = [run_row_summary(path, "canary") for path in gt_paths]
        gt_groups = canary_hash_groups(gt_summaries, iter32_gt_projection)

    failures = [
        failure
        for summary in [*model_summaries, *gt_summaries]
        for failure in summary["row_count_failures"]
    ]
    for label, groups in (("model", model_groups), ("gt", gt_groups)):
        if label == "gt" and not gt_paths:
            continue
        if len(groups.get("0p00", [])) != 2:
            failures.append(f"{label}:alpha0p00_repeat_count={len(groups.get('0p00', []))} != 2")
        if len(set(groups.get("0p00", []))) > 1:
            failures.append(f"{label}:alpha0p00_repeat_hashes_not_equal={groups.get('0p00', [])}")
        if label == "model" and groups.get("0p00", []) != [
            EXPECTED_ITER32_MODEL_TARGET_SHA,
            EXPECTED_ITER32_MODEL_TARGET_SHA,
        ]:
            failures.append(f"model:alpha0p00_hashes={groups.get('0p00', [])}")
        if label == "gt" and groups.get("0p00", []) != [
            EXPECTED_ITER32_GT_TARGET_SHA,
            EXPECTED_ITER32_GT_TARGET_SHA,
        ]:
            failures.append(f"gt:alpha0p00_hashes={groups.get('0p00', [])}")
    if len(model_groups.get("0p50", [])) != 2:
        failures.append(f"model:alpha0p50_repeat_count={len(model_groups.get('0p50', []))} != 2")
    if len(set(model_groups.get("0p50", []))) > 1:
        failures.append(f"model:alpha0p50_repeat_hashes_not_equal={model_groups.get('0p50', [])}")

    reference_report = {"alpha_zero_reference_checked": False}
    if reference_paths is not None:
        canary_rows = [row for summary in model_summaries for row in summary["rows"]]
        reference_rows = list(iter_jsonl(reference_paths))
        reference_report = alpha_zero_reference_report(canary_rows, reference_rows)
        if not reference_report["alpha_zero_reference_pass"]:
            failures.append("alpha_zero_reference_failed")

    bridge_report = nonzero_bridge_report(model_summaries)
    if not bridge_report["alpha0p50_bridge_change_pass"]:
        failures.append("alpha0p50_bridge_change_failed")

    return {
        "stage": "iter33_canary_integrity",
        "command_line": " ".join(sys.argv),
        "metric_scope": "target_row_only_for_hash_and_reference_checks",
        "model_run_summaries": [public_run_summary(summary) for summary in model_summaries],
        "gt_run_summaries": [public_run_summary(summary) for summary in gt_summaries],
        "model_target_baseline_projection_hashes_by_alpha": dict(model_groups),
        "gt_target_baseline_projection_hashes_by_alpha": dict(gt_groups),
        **reference_report,
        **bridge_report,
        "s0_canary_pass": not failures,
        "failure_count": len(failures),
        "failures": failures[:100],
        "claim_boundary": (
            "Canary hashing is an S0 integrity artifact only. Baseline hashes use the iteration-32 "
            "compatible target-row projection so extra iter33 audit metadata cannot hide output drift."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=["canary", "calibration", "heldout"], required=True)
    parser.add_argument("--log", action="append", required=True)
    parser.add_argument("--gt-log", action="append")
    parser.add_argument("--reference-extract-part", action="append")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    paths = [Path(path) for path in args.log]
    if args.stage == "canary":
        if args.reference_extract_part is None:
            reference_paths = default_iter29_extract_parts()
        else:
            reference_paths = [Path(path) for path in args.reference_extract_part]
        gt_paths = [Path(path) for path in args.gt_log] if args.gt_log else None
        report = analyze_canary(paths, gt_paths, reference_paths)
    elif args.stage == "calibration":
        report = analyze_calibration(paths)
    else:
        report = analyze_heldout(paths)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
