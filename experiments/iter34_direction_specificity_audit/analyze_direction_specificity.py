#!/usr/bin/env python3
"""Audit iteration-33 calibration response specificity.

This script is offline-only. It reads committed iteration-33 calibration proof
artifacts and asks whether the failed global bridge-centroid direction shows a
target-specific, safety-aligned dose response that could justify a future
same-direction successor pre-registration.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
ITER33 = ROOT / "experiments/iter33_prefix_preserving_bridge_intervention"
ITER34 = ROOT / "experiments/iter34_direction_specificity_audit"
PROOF33 = ITER33 / "proof-calibration"
PROOF34 = ITER34 / "proof-audit"
ALPHAS = (0.0, 0.25, 0.5, 0.75, 1.0)
ALPHA_TAGS = {
    0.0: "0p00",
    0.25: "0p25",
    0.5: "0p50",
    0.75: "0p75",
    1.0: "1p00",
}
EXPECTED_VERDICT = "CALIBRATION_NULL_NO_USABLE_ALPHA"
EXPECTED_ROWS = 2452
EXPECTED_LABEL_COUNTS = {"eligible_lowdiv": 108, "benign_control": 2344}
CLAIM_BOUNDARY = (
    "Post-result audit only: no alpha selection, heldout replay, iteration-12 scoring, "
    "selector evaluation, closed-loop work, deployment language, or safety claim is authorized."
)


def load_iter33_analyzer():
    script = ITER33 / "analyze_intervention.py"
    spec = importlib.util.spec_from_file_location("iter33_analyze_intervention", script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_sha256s(path: Path) -> dict[str, str]:
    records = {}
    if not path.exists():
        return records
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split(maxsplit=1)
        records[rel] = digest
    return records


def alpha_log_parts(alpha: float) -> list[Path]:
    tag = ALPHA_TAGS[alpha]
    return sorted(PROOF33.glob(f"sentinel_e33_calibration_alpha{tag}.jsonl.gz.part-*"))


def key_of_metric(row: dict) -> tuple[str, int, int]:
    return (str(row["scene"]), int(row["sample_index"]), int(row["timestamp_us"]))


def median(values: Iterable[float]) -> float:
    xs = sorted(float(value) for value in values)
    if not xs:
        return float("nan")
    mid = len(xs) // 2
    if len(xs) % 2:
        return xs[mid]
    return (xs[mid - 1] + xs[mid]) / 2.0


def pearson(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return float("nan")
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    x_dev = [x - x_mean for x in xs]
    y_dev = [y - y_mean for y in ys]
    x_var = sum(x * x for x in x_dev)
    y_var = sum(y * y for y in y_dev)
    if x_var == 0.0 or y_var == 0.0:
        return float("nan")
    return sum(x * y for x, y in zip(x_dev, y_dev)) / math.sqrt(x_var * y_var)


def linear_fit(xs: list[float], ys: list[float]) -> dict[str, float]:
    if len(xs) != len(ys) or len(xs) < 2:
        return {"slope": float("nan"), "intercept": float("nan")}
    x_mean = sum(xs) / len(xs)
    y_mean = sum(ys) / len(ys)
    denom = sum((x - x_mean) ** 2 for x in xs)
    if denom == 0.0:
        return {"slope": float("nan"), "intercept": float("nan")}
    slope = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, ys)) / denom
    return {"slope": slope, "intercept": y_mean - slope * x_mean}


def alpha_needed_for_target(fit: dict[str, float], target: float) -> float:
    slope = fit["slope"]
    if not math.isfinite(slope) or slope <= 0.0:
        return float("inf")
    return (target - fit["intercept"]) / slope


def summarize_metrics(module, alpha: float, metrics_by_key: dict[tuple, dict]) -> dict:
    rows = list(metrics_by_key.values())
    eligible = module.summarize_label(rows, "eligible_lowdiv")
    benign = module.summarize_label(rows, "benign_control")
    return {
        "alpha": alpha,
        "rows": len(rows),
        "error_rows": sum(1 for row in rows if row.get("error")),
        "eligible_lowdiv": eligible,
        "benign_control": benign,
    }


def read_alpha_metrics(module, alpha: float) -> tuple[dict, dict[tuple, dict]]:
    parts = alpha_log_parts(alpha)
    if not parts:
        raise FileNotFoundError(f"no split calibration log parts found for alpha={alpha}")

    non_reset_rows = 0
    context_only_rows = 0
    duplicate_target_keys = 0
    metrics_by_key: dict[tuple, dict] = {}
    for row in module.iter_jsonl(parts):
        if row.get("reset"):
            continue
        non_reset_rows += 1
        if not bool(row.get("target_row", False)):
            context_only_rows += 1
            continue
        metric = module.row_metrics(row)
        key = key_of_metric(metric)
        if key in metrics_by_key:
            duplicate_target_keys += 1
        metrics_by_key[key] = metric

    summary = summarize_metrics(module, alpha, metrics_by_key)
    summary.update(
        {
            "log_parts": [str(path.relative_to(ROOT)) for path in parts],
            "non_reset_rows": non_reset_rows,
            "target_rows": len(metrics_by_key),
            "context_only_rows": context_only_rows,
            "duplicate_target_keys": duplicate_target_keys,
        }
    )
    return summary, metrics_by_key


def validate_recorded_hashes(paths: list[Path]) -> dict:
    recorded = parse_sha256s(PROOF33 / "sha256s.txt")
    unsplit_recorded = parse_sha256s(PROOF33 / "unsplit_sha256s.txt")
    checked = {}
    failures = []
    for path in paths:
        rel = str(path.relative_to(ROOT))
        expected = recorded.get(rel)
        if expected is None:
            failures.append(f"missing recorded sha256 for {rel}")
            continue
        observed = sha256_file(path)
        checked[rel] = {"expected": expected, "observed": observed, "match": observed == expected}
        if observed != expected:
            failures.append(f"sha256 mismatch for {rel}")
    return {
        "sha256s_path": str((PROOF33 / "sha256s.txt").relative_to(ROOT)),
        "unsplit_sha256s_path": str((PROOF33 / "unsplit_sha256s.txt").relative_to(ROOT)),
        "checked": checked,
        "unsplit_record_count": len(unsplit_recorded),
        "failures": failures,
    }


def report_cell_by_alpha(calibration_report: dict) -> dict[float, dict]:
    cells = {}
    for cell in calibration_report.get("cells", []):
        cells[float(cell["alpha"])] = cell
    return cells


def s0_failures(calibration_report: dict, summaries: dict[float, dict], key_sets: dict[float, set], hash_report: dict) -> list[str]:
    failures = list(hash_report["failures"])
    if calibration_report.get("verdict") != EXPECTED_VERDICT:
        failures.append(f"verdict={calibration_report.get('verdict')} != {EXPECTED_VERDICT}")
    if calibration_report.get("prefix_replay_integrity_pass") is not True:
        failures.append("prefix_replay_integrity_pass_not_true")

    report_cells = report_cell_by_alpha(calibration_report)
    if sorted(report_cells) != list(ALPHAS):
        failures.append(f"report_alphas={sorted(report_cells)} != {list(ALPHAS)}")

    reference_keys = None
    for alpha in ALPHAS:
        if alpha not in summaries:
            failures.append(f"missing_summary_alpha={alpha}")
            continue
        summary = summaries[alpha]
        if summary["rows"] != EXPECTED_ROWS:
            failures.append(f"alpha={alpha} rows={summary['rows']} != {EXPECTED_ROWS}")
        if summary["target_rows"] != EXPECTED_ROWS:
            failures.append(f"alpha={alpha} target_rows={summary['target_rows']} != {EXPECTED_ROWS}")
        if summary["error_rows"] != 0:
            failures.append(f"alpha={alpha} error_rows={summary['error_rows']} != 0")
        for label, expected in EXPECTED_LABEL_COUNTS.items():
            observed = summary[label]["rows"]
            if observed != expected:
                failures.append(f"alpha={alpha} {label}_rows={observed} != {expected}")
            gross = summary[label]["gross_validity_failures"]
            if gross != 0:
                failures.append(f"alpha={alpha} {label}_gross_validity_failures={gross} != 0")
        if summary["duplicate_target_keys"] != 0:
            failures.append(f"alpha={alpha} duplicate_target_keys={summary['duplicate_target_keys']} != 0")

        if alpha in report_cells:
            report_cell = report_cells[alpha]
            if report_cell.get("rows") != EXPECTED_ROWS:
                failures.append(f"report alpha={alpha} rows={report_cell.get('rows')} != {EXPECTED_ROWS}")
            for label, expected in EXPECTED_LABEL_COUNTS.items():
                observed = report_cell.get(label, {}).get("rows")
                if observed != expected:
                    failures.append(f"report alpha={alpha} {label}_rows={observed} != {expected}")

        keys = key_sets.get(alpha, set())
        if reference_keys is None:
            reference_keys = keys
        elif keys != reference_keys:
            failures.append(f"alpha={alpha} target_keys_mismatch")
    return failures


def row_slope_fraction(
    per_alpha_metrics: dict[float, dict[tuple, dict]],
    label_name: str,
    metric_name: str,
    minimum_slope: float,
) -> dict:
    reference_keys = [
        key
        for key, row in per_alpha_metrics[0.0].items()
        if row.get("label_name") == label_name
    ]
    passing = 0
    slopes = []
    xs = list(ALPHAS)
    for key in reference_keys:
        ys = [per_alpha_metrics[alpha][key][metric_name] for alpha in ALPHAS]
        slope = linear_fit(xs, ys)["slope"]
        slopes.append(slope)
        if slope >= minimum_slope:
            passing += 1
    return {
        "rows": len(reference_keys),
        "passing_rows": passing,
        "fraction": passing / len(reference_keys) if reference_keys else float("nan"),
        "median_slope": median(slopes),
    }


def evaluate_s1(cells: list[dict], per_alpha_metrics: dict[float, dict[tuple, dict]]) -> dict:
    alpha_values = [float(cell["alpha"]) for cell in cells]
    eligible_medians = [
        cell["eligible_lowdiv"]["median_endpoint_spread_delta"]
        for cell in cells
    ]
    nonzero_eligible_medians = [
        cell["eligible_lowdiv"]["median_endpoint_spread_delta"]
        for cell in cells
        if float(cell["alpha"]) > 0.0
    ]
    slope_fraction = row_slope_fraction(
        per_alpha_metrics,
        "eligible_lowdiv",
        "endpoint_spread_delta",
        0.0,
    )
    alpha_one = next(cell for cell in cells if float(cell["alpha"]) == 1.0)
    alpha_one_fraction = alpha_one["eligible_lowdiv"]["fraction_endpoint_spread_delta_gt_0p25"]
    corr = pearson(alpha_values, eligible_medians)

    failures = []
    if not all(b > a for a, b in zip(nonzero_eligible_medians, nonzero_eligible_medians[1:])):
        failures.append("eligible_nonzero_median_endpoint_spread_delta_not_strictly_increasing")
    if not math.isfinite(corr) or corr < 0.95:
        failures.append(f"eligible_alpha_pearson={corr:.6f} < 0.95")
    if slope_fraction["fraction"] < 0.70:
        failures.append(f"eligible_nonnegative_slope_fraction={slope_fraction['fraction']:.6f} < 0.70")
    if alpha_one_fraction < 0.10:
        failures.append(f"alpha1_eligible_fraction_endpoint_spread_delta_gt_0p25={alpha_one_fraction:.6f} < 0.10")

    return {
        "pass": not failures,
        "failures": failures,
        "eligible_median_endpoint_spread_delta_by_alpha": dict(zip((str(a) for a in alpha_values), eligible_medians)),
        "eligible_alpha_pearson": corr,
        "eligible_nonnegative_endpoint_spread_slope": slope_fraction,
        "alpha1_eligible_fraction_endpoint_spread_delta_gt_0p25": alpha_one_fraction,
    }


def evaluate_s2(cells: list[dict]) -> dict:
    alpha_one = next(cell for cell in cells if float(cell["alpha"]) == 1.0)
    eligible = alpha_one["eligible_lowdiv"]
    benign = alpha_one["benign_control"]
    eligible_medians = [
        cell["eligible_lowdiv"]["median_endpoint_spread_delta"]
        for cell in cells
    ]
    fit = linear_fit([float(cell["alpha"]) for cell in cells], eligible_medians)
    needed_alpha = alpha_needed_for_target(fit, 0.25)
    predicted_benign_p95 = benign["p95_executed_endpoint_displacement"] * needed_alpha
    ratio = (
        eligible["median_endpoint_spread_delta"] / benign["median_endpoint_spread_delta"]
        if benign["median_endpoint_spread_delta"] != 0.0
        else float("inf")
    )
    nonzero_gap_pass_count = sum(
        1
        for cell in cells
        if float(cell["alpha"]) > 0.0
        and cell["eligible_lowdiv"]["median_best_candidate_gap_delta"] >= 0.0
    )

    failures = []
    if eligible["median_endpoint_spread_delta"] < 0.10:
        failures.append(
            "alpha1_eligible_median_endpoint_spread_delta="
            f"{eligible['median_endpoint_spread_delta']:.6f} < 0.10"
        )
    if ratio < 1.50:
        failures.append(f"alpha1_eligible_to_benign_spread_ratio={ratio:.6f} < 1.50")
    if eligible["median_best_candidate_gap_delta"] < 0.0:
        failures.append(
            "alpha1_eligible_median_best_candidate_gap_delta="
            f"{eligible['median_best_candidate_gap_delta']:.6f} < 0.00"
        )
    if nonzero_gap_pass_count < 3:
        failures.append(f"nonzero_gap_nonnegative_cells={nonzero_gap_pass_count} < 3")
    if needed_alpha > 2.0:
        failures.append(f"least_squares_alpha_needed_for_0p25={needed_alpha:.6f} > 2.00")
    if predicted_benign_p95 > 2.0:
        failures.append(f"predicted_benign_p95_at_needed_alpha={predicted_benign_p95:.6f} > 2.00")

    return {
        "pass": not failures,
        "failures": failures,
        "alpha1_eligible_median_endpoint_spread_delta": eligible["median_endpoint_spread_delta"],
        "alpha1_benign_median_endpoint_spread_delta": benign["median_endpoint_spread_delta"],
        "alpha1_eligible_to_benign_spread_ratio": ratio,
        "alpha1_eligible_median_best_candidate_gap_delta": eligible["median_best_candidate_gap_delta"],
        "nonzero_gap_nonnegative_cells": nonzero_gap_pass_count,
        "eligible_endpoint_spread_linear_fit": fit,
        "least_squares_alpha_needed_for_0p25": needed_alpha,
        "alpha1_benign_p95_executed_endpoint_displacement": benign["p95_executed_endpoint_displacement"],
        "predicted_benign_p95_at_needed_alpha": predicted_benign_p95,
    }


def verdict(s0_pass: bool, s1: dict | None, s2: dict | None) -> str:
    if not s0_pass:
        return "INFRASTRUCTURE_NULL_S0_ARTIFACT_OR_ROW_INTEGRITY"
    if s1 is not None and not s1["pass"]:
        return "DIRECTION_AUDIT_NULL_NO_DOSE_RESPONSE"
    if s2 is not None and not s2["pass"]:
        return "DIRECTION_SPECIFICITY_NULL_NO_SCALE_ONLY_SUCCESSOR"
    return "DIRECTION_SPECIFICITY_PASS_SUCCESSOR_PREREG_AUTHORIZED"


def build_report() -> dict:
    module = load_iter33_analyzer()
    calibration_report_path = PROOF33 / "calibration_report.json"
    calibration_report = json.loads(calibration_report_path.read_text(encoding="utf-8"))
    required_paths = [calibration_report_path, PROOF33 / "sha256s.txt", PROOF33 / "unsplit_sha256s.txt"]
    for alpha in ALPHAS:
        required_paths.extend(alpha_log_parts(alpha))
    hash_report = validate_recorded_hashes(required_paths)

    summaries = {}
    per_alpha_metrics = {}
    key_sets = {}
    for alpha in ALPHAS:
        summary, metrics_by_key = read_alpha_metrics(module, alpha)
        summaries[alpha] = summary
        per_alpha_metrics[alpha] = metrics_by_key
        key_sets[alpha] = set(metrics_by_key)

    s0 = s0_failures(calibration_report, summaries, key_sets, hash_report)
    cells = [summaries[alpha] for alpha in ALPHAS]
    s1 = evaluate_s1(cells, per_alpha_metrics) if not s0 else None
    s2 = evaluate_s2(cells) if s1 is not None and s1["pass"] else None
    final_verdict = verdict(not s0, s1, s2)

    return {
        "schema_version": "sentinel.iter34_direction_specificity_audit.report.v1",
        "experiment_id": "iter34_direction_specificity_audit",
        "verdict": final_verdict,
        "status": "pass" if final_verdict.endswith("AUTHORIZED") else "null",
        "command_line": " ".join(sys.argv),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "submitted_model_mutated": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_iter33_report": str(calibration_report_path.relative_to(ROOT)),
        "artifact_hash_validation": hash_report,
        "s0_pass": not s0,
        "s0_failures": s0,
        "s1": s1,
        "s2": s2,
        "alpha_summaries": cells,
        "target_key_counts": {str(alpha): len(key_sets[alpha]) for alpha in ALPHAS},
        "next_authorized_action": (
            "publish RESULT.md from this report; no heldout, iteration-12, selector, closed-loop, "
            "deployment, or safety work is authorized"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(PROOF34 / "direction_specificity_report.json"))
    args = parser.parse_args()

    report = build_report()
    write_json(Path(args.out), report)
    print(f"iter34 direction specificity audit: {report['verdict']}")
    print(f"s0_pass={str(report['s0_pass']).lower()}")
    if report["s1"] is not None:
        print(f"s1_pass={str(report['s1']['pass']).lower()}")
    if report["s2"] is not None:
        print(f"s2_pass={str(report['s2']['pass']).lower()}")
    print(f"out={args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
