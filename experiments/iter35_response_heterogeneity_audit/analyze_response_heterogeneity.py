#!/usr/bin/env python3
"""Audit row-level response heterogeneity in the iteration-33 calibration grid.

This script is offline-only. It reads committed iteration-33 calibration proof
artifacts plus the committed iteration-34 audit report, then tests whether the
failed global bridge-centroid direction has an actionable pre-declared
baseline-geometry stratum.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import sys
from collections.abc import Callable, Iterable
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ITER33 = ROOT / "experiments/iter33_prefix_preserving_bridge_intervention"
ITER34 = ROOT / "experiments/iter34_direction_specificity_audit"
ITER35 = ROOT / "experiments/iter35_response_heterogeneity_audit"
PROOF33 = ITER33 / "proof-calibration"
PROOF34 = ITER34 / "proof-audit"
PROOF35 = ITER35 / "proof-audit"
ALPHAS = (0.0, 0.25, 0.5, 0.75, 1.0)
ALPHA_TAGS = {
    0.0: "0p00",
    0.25: "0p25",
    0.5: "0p50",
    0.75: "0p75",
    1.0: "1p00",
}
EXPECTED_ITER33_VERDICT = "CALIBRATION_NULL_NO_USABLE_ALPHA"
EXPECTED_ITER34_VERDICT = "DIRECTION_AUDIT_NULL_NO_DOSE_RESPONSE"
EXPECTED_ROWS = 2452
EXPECTED_LABEL_COUNTS = {"eligible_lowdiv": 108, "benign_control": 2344}
CLAIM_BOUNDARY = (
    "Post-result offline audit only: no alpha selection, heldout replay, iteration-12 scoring, "
    "selector evaluation, closed-loop work, deployment language, safety claim, or same-direction "
    "scale-only successor is authorized."
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
    return percentile(list(values), 50.0)


def percentile(values: list[float], pct: float) -> float:
    xs = sorted(float(value) for value in values)
    if not xs:
        return float("nan")
    if len(xs) == 1:
        return xs[0]
    pos = (len(xs) - 1) * pct / 100.0
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    frac = pos - lo
    return xs[lo] * (1.0 - frac) + xs[hi] * frac


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


def fraction(values: list[bool]) -> float:
    return sum(1 for value in values if value) / len(values) if values else float("nan")


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


def baseline_covariates(row: dict, metric: dict) -> dict:
    return {
        "object_count": len(row.get("objs", [])),
        "original_endpoint_spread": metric["original_endpoint_spread"],
        "original_best_candidate_gap": metric["original_best_candidate_gap"],
        "original_executed_gap": metric["original_executed_gap"],
    }


def read_alpha_metrics(module, alpha: float) -> tuple[dict, dict[tuple, dict], dict[tuple, dict]]:
    parts = alpha_log_parts(alpha)
    if not parts:
        raise FileNotFoundError(f"no split calibration log parts found for alpha={alpha}")

    non_reset_rows = 0
    context_only_rows = 0
    duplicate_target_keys = 0
    metrics_by_key: dict[tuple, dict] = {}
    covariates_by_key: dict[tuple, dict] = {}
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
        if alpha == 0.0:
            covariates_by_key[key] = baseline_covariates(row, metric)

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
    return summary, metrics_by_key, covariates_by_key


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
        "sha256s_file_sha256": sha256_file(PROOF33 / "sha256s.txt"),
        "unsplit_sha256s_path": str((PROOF33 / "unsplit_sha256s.txt").relative_to(ROOT)),
        "unsplit_sha256s_file_sha256": sha256_file(PROOF33 / "unsplit_sha256s.txt"),
        "checked": checked,
        "unsplit_record_count": len(unsplit_recorded),
        "failures": failures,
    }


def report_cell_by_alpha(calibration_report: dict) -> dict[float, dict]:
    return {float(cell["alpha"]): cell for cell in calibration_report.get("cells", [])}


def s0_failures(
    iter33_report: dict,
    iter34_report: dict,
    summaries: dict[float, dict],
    key_sets: dict[float, set],
    hash_report: dict,
) -> list[str]:
    failures = list(hash_report["failures"])
    if iter34_report.get("verdict") != EXPECTED_ITER34_VERDICT:
        failures.append(f"iter34_verdict={iter34_report.get('verdict')} != {EXPECTED_ITER34_VERDICT}")
    if iter34_report.get("s0_pass") is not True:
        failures.append("iter34_s0_pass_not_true")
    if iter33_report.get("verdict") != EXPECTED_ITER33_VERDICT:
        failures.append(f"iter33_verdict={iter33_report.get('verdict')} != {EXPECTED_ITER33_VERDICT}")
    if iter33_report.get("prefix_replay_integrity_pass") is not True:
        failures.append("iter33_prefix_replay_integrity_pass_not_true")

    report_cells = report_cell_by_alpha(iter33_report)
    if sorted(report_cells) != list(ALPHAS):
        failures.append(f"iter33_report_alphas={sorted(report_cells)} != {list(ALPHAS)}")

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


def slope_records(
    per_alpha_metrics: dict[float, dict[tuple, dict]],
    covariates_by_key: dict[tuple, dict],
) -> list[dict]:
    records = []
    xs = list(ALPHAS)
    for key, base in per_alpha_metrics[0.0].items():
        spread_values = [per_alpha_metrics[alpha][key]["endpoint_spread_delta"] for alpha in ALPHAS]
        gap_values = [per_alpha_metrics[alpha][key]["best_candidate_gap_delta"] for alpha in ALPHAS]
        alpha_one = per_alpha_metrics[1.0][key]
        records.append(
            {
                "key": {"scene": key[0], "sample_index": key[1], "timestamp_us": key[2]},
                "label_name": base["label_name"],
                "endpoint_spread_slope": linear_fit(xs, spread_values)["slope"],
                "best_candidate_gap_slope": linear_fit(xs, gap_values)["slope"],
                "alpha1_endpoint_spread_delta": alpha_one["endpoint_spread_delta"],
                "alpha1_best_candidate_gap_delta": alpha_one["best_candidate_gap_delta"],
                "alpha1_executed_endpoint_displacement": alpha_one["executed_endpoint_displacement"],
                "alpha1_benign_crossed_danger": bool(alpha_one["benign_crossed_danger"]),
                "alpha1_benign_collapsed_lowdiv": bool(alpha_one["benign_collapsed_lowdiv"]),
                "baseline": covariates_by_key[key],
            }
        )
    return records


def evaluate_s1(records: list[dict]) -> dict:
    eligible = [row for row in records if row["label_name"] == "eligible_lowdiv"]
    slopes = [row["endpoint_spread_slope"] for row in eligible]
    positive = sum(1 for slope in slopes if slope >= 0.05)
    negative = sum(1 for slope in slopes if slope < 0.0)
    slope_width = percentile(slopes, 75.0) - percentile(slopes, 25.0)

    failures = []
    if positive < 20:
        failures.append(f"eligible_spread_slope_ge_0p05_rows={positive} < 20")
    if negative < 20:
        failures.append(f"eligible_spread_slope_lt_0_rows={negative} < 20")
    if slope_width < 0.05:
        failures.append(f"eligible_spread_slope_iqr={slope_width:.6f} < 0.05")

    return {
        "pass": not failures,
        "failures": failures,
        "eligible_rows": len(eligible),
        "eligible_spread_slope_ge_0p05_rows": positive,
        "eligible_spread_slope_lt_0_rows": negative,
        "eligible_spread_slope_median": median(slopes),
        "eligible_spread_slope_p25": percentile(slopes, 25.0),
        "eligible_spread_slope_p75": percentile(slopes, 75.0),
        "eligible_spread_slope_iqr": slope_width,
    }


StratumPredicate = Callable[[dict], bool]


def frozen_strata() -> list[tuple[str, str, StratumPredicate]]:
    return [
        ("executed_danger", "original_executed_gap < 4.5", lambda row: row["original_executed_gap"] < 4.5),
        (
            "executed_not_danger",
            "original_executed_gap >= 4.5",
            lambda row: row["original_executed_gap"] >= 4.5,
        ),
        (
            "best_candidate_danger",
            "original_best_candidate_gap < 4.5",
            lambda row: row["original_best_candidate_gap"] < 4.5,
        ),
        (
            "best_candidate_safe",
            "original_best_candidate_gap >= 6.0",
            lambda row: row["original_best_candidate_gap"] >= 6.0,
        ),
        ("very_low_spread", "original_endpoint_spread <= 1.0", lambda row: row["original_endpoint_spread"] <= 1.0),
        (
            "near_lowdiv_threshold",
            "1.0 < original_endpoint_spread <= 1.5",
            lambda row: 1.0 < row["original_endpoint_spread"] <= 1.5,
        ),
        ("single_object", "object_count == 1", lambda row: row["object_count"] == 1),
        ("multi_object", "object_count >= 2", lambda row: row["object_count"] >= 2),
    ]


def stratum_summary(name: str, definition: str, rows: list[dict], predicate: StratumPredicate) -> dict:
    selected = [row for row in rows if predicate(row["baseline"])]
    eligible = [row for row in selected if row["label_name"] == "eligible_lowdiv"]
    benign = [row for row in selected if row["label_name"] == "benign_control"]
    eligible_spread_slopes = [row["endpoint_spread_slope"] for row in eligible]
    eligible_gap_slopes = [row["best_candidate_gap_slope"] for row in eligible]
    eligible_alpha1_spread = [row["alpha1_endpoint_spread_delta"] for row in eligible]
    benign_disp = [row["alpha1_executed_endpoint_displacement"] for row in benign]
    benign_danger = [row["alpha1_benign_crossed_danger"] for row in benign]
    benign_collapse = [row["alpha1_benign_collapsed_lowdiv"] for row in benign]

    eligible_nonnegative_fraction = fraction([slope >= 0.0 for slope in eligible_spread_slopes])
    eligible_alpha1_fraction = fraction([value > 0.25 for value in eligible_alpha1_spread])
    benign_danger_fraction = fraction(benign_danger)
    benign_collapse_fraction = fraction(benign_collapse)
    benign_median_disp = median(benign_disp)
    benign_p95_disp = percentile(benign_disp, 95.0)

    failures = []
    if len(eligible) < 24:
        failures.append(f"eligible_support={len(eligible)} < 24")
    if len(benign) < 100:
        failures.append(f"benign_support={len(benign)} < 100")
    if eligible_nonnegative_fraction < 0.85:
        failures.append(f"eligible_nonnegative_spread_slope_fraction={eligible_nonnegative_fraction:.6f} < 0.85")
    if median(eligible_spread_slopes) < 0.08:
        failures.append(f"eligible_median_spread_slope={median(eligible_spread_slopes):.6f} < 0.08")
    if median(eligible_gap_slopes) < 0.0:
        failures.append(f"eligible_median_best_gap_slope={median(eligible_gap_slopes):.6f} < 0.00")
    if eligible_alpha1_fraction < 0.25:
        failures.append(f"eligible_alpha1_spread_delta_gt_0p25_fraction={eligible_alpha1_fraction:.6f} < 0.25")
    if benign_median_disp > 0.50:
        failures.append(f"benign_alpha1_median_executed_displacement={benign_median_disp:.6f} > 0.50")
    if benign_p95_disp > 2.00:
        failures.append(f"benign_alpha1_p95_executed_displacement={benign_p95_disp:.6f} > 2.00")
    if benign_danger_fraction > 0.05:
        failures.append(f"benign_alpha1_danger_cross_fraction={benign_danger_fraction:.6f} > 0.05")
    if benign_collapse_fraction > 0.05:
        failures.append(f"benign_alpha1_lowdiv_collapse_fraction={benign_collapse_fraction:.6f} > 0.05")

    return {
        "name": name,
        "definition": definition,
        "pass": not failures,
        "failures": failures,
        "eligible_support": len(eligible),
        "benign_support": len(benign),
        "eligible_nonnegative_spread_slope_fraction": eligible_nonnegative_fraction,
        "eligible_median_spread_slope": median(eligible_spread_slopes),
        "eligible_median_best_gap_slope": median(eligible_gap_slopes),
        "eligible_alpha1_spread_delta_gt_0p25_fraction": eligible_alpha1_fraction,
        "benign_alpha1_median_executed_displacement": benign_median_disp,
        "benign_alpha1_p95_executed_displacement": benign_p95_disp,
        "benign_alpha1_danger_cross_fraction": benign_danger_fraction,
        "benign_alpha1_lowdiv_collapse_fraction": benign_collapse_fraction,
    }


def evaluate_s2(records: list[dict]) -> dict:
    strata = [
        stratum_summary(name, definition, records, predicate)
        for name, definition, predicate in frozen_strata()
    ]
    passing = [stratum["name"] for stratum in strata if stratum["pass"]]
    return {
        "pass": bool(passing),
        "passing_strata": passing,
        "strata": strata,
        "failures": [] if passing else ["no_frozen_stratum_passed_all_actionability_bars"],
    }


def verdict(s0_pass: bool, s1: dict | None, s2: dict | None) -> str:
    if not s0_pass:
        return "INFRASTRUCTURE_NULL_S0_ARTIFACT_OR_ROW_INTEGRITY"
    if s1 is not None and not s1["pass"]:
        return "HETEROGENEITY_NULL_UNIFORM_OR_TOO_NARROW_RESPONSE"
    if s2 is not None and not s2["pass"]:
        return "HETEROGENEITY_NULL_NO_ACTIONABLE_STRATUM"
    return "HETEROGENEITY_PASS_CONDITIONED_SUCCESSOR_PREREG_AUTHORIZED"


def build_report() -> dict:
    module = load_iter33_analyzer()
    iter33_report_path = PROOF33 / "calibration_report.json"
    iter34_report_path = PROOF34 / "direction_specificity_report.json"
    iter33_report = json.loads(iter33_report_path.read_text(encoding="utf-8"))
    iter34_report = json.loads(iter34_report_path.read_text(encoding="utf-8"))

    required_paths = [iter33_report_path, PROOF33 / "unsplit_sha256s.txt"]
    for alpha in ALPHAS:
        required_paths.extend(alpha_log_parts(alpha))
    hash_report = validate_recorded_hashes(required_paths)

    summaries = {}
    per_alpha_metrics = {}
    key_sets = {}
    covariates_by_key = {}
    for alpha in ALPHAS:
        summary, metrics_by_key, covariates = read_alpha_metrics(module, alpha)
        summaries[alpha] = summary
        per_alpha_metrics[alpha] = metrics_by_key
        key_sets[alpha] = set(metrics_by_key)
        if alpha == 0.0:
            covariates_by_key = covariates

    s0 = s0_failures(iter33_report, iter34_report, summaries, key_sets, hash_report)
    records = slope_records(per_alpha_metrics, covariates_by_key) if not s0 else []
    s1 = evaluate_s1(records) if not s0 else None
    s2 = evaluate_s2(records) if s1 is not None and s1["pass"] else None
    final_verdict = verdict(not s0, s1, s2)

    return {
        "schema_version": "sentinel.iter35_response_heterogeneity_audit.report.v1",
        "experiment_id": "iter35_response_heterogeneity_audit",
        "verdict": final_verdict,
        "status": "pass" if final_verdict.endswith("AUTHORIZED") else "null",
        "command_line": " ".join(sys.argv),
        "provider_api_calls": 0,
        "provider_spend_usd": 0.0,
        "cloud_or_gpu_used": False,
        "local_cpu_only": True,
        "submitted_model_mutated": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "source_iter33_report": str(iter33_report_path.relative_to(ROOT)),
        "source_iter34_report": str(iter34_report_path.relative_to(ROOT)),
        "source_iter34_report_sha256": sha256_file(iter34_report_path),
        "artifact_hash_validation": hash_report,
        "s0_pass": not s0,
        "s0_failures": s0,
        "s1": s1,
        "s2": s2,
        "alpha_summaries": [summaries[alpha] for alpha in ALPHAS],
        "target_key_counts": {str(alpha): len(key_sets[alpha]) for alpha in ALPHAS},
        "next_authorized_action": (
            "publish RESULT.md from this report; no GPU/gcloud work, heldout replay, iteration-12 "
            "scoring, selector evaluation, closed-loop work, deployment language, or safety claim "
            "is authorized"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(PROOF35 / "response_heterogeneity_report.json"))
    args = parser.parse_args()

    report = build_report()
    write_json(Path(args.out), report)
    print(f"iter35 response heterogeneity audit: {report['verdict']}")
    print(f"s0_pass={str(report['s0_pass']).lower()}")
    if report["s1"] is not None:
        print(f"s1_pass={str(report['s1']['pass']).lower()}")
    if report["s2"] is not None:
        print(f"s2_pass={str(report['s2']['pass']).lower()}")
        print("passing_strata=" + ",".join(report["s2"]["passing_strata"]))
    print(f"out={args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
