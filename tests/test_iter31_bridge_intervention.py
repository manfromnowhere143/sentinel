from __future__ import annotations

import gzip
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "experiments/iter31_full_trainval_bridge_intervention/build_direction.py"
ANALYZE = ROOT / "experiments/iter31_full_trainval_bridge_intervention/analyze_intervention.py"
ITER30 = ROOT / "experiments/iter30_full_trainval_lowdiv_localization/analyze_localization.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bridge_row(split: str, label: int, traj_values: list[float], track_values: list[float], index: int):
    return {
        "split": split,
        "label": label,
        "scene": f"scene-{index:04d}",
        "sample_index": index,
        "timestamp_us": 1000 + index,
        "closest_gap": 3.0 if label else 7.0,
        "endpoint_spread": 1.0 if label else 3.0,
        "sdc_traj_query_last": traj_values,
        "sdc_track_query": track_values,
    }


def passing_cell(alpha: float, spread_delta: float):
    return {
        "alpha": alpha,
        "rows": 2452,
        "error_rows": 0,
        "eligible_lowdiv": {
            "rows": 108,
            "gross_validity_failures": 0,
            "median_endpoint_spread_delta": spread_delta,
            "fraction_endpoint_spread_delta_gt_0p25": 0.8,
            "fraction_endpoint_spread_delta_ge_0p25": 0.8,
            "median_best_candidate_gap_delta": 0.1,
            "fraction_best_candidate_gap_delta_lt_neg_0p25": 0.0,
            "median_executed_endpoint_displacement": 0.0,
            "p95_executed_endpoint_displacement": 0.0,
            "danger_cross_fraction": 0.0,
            "lowdiv_collapse_fraction": 0.0,
            "median_endpoint_spread_delta_unused": spread_delta,
        },
        "benign_control": {
            "rows": 2344,
            "gross_validity_failures": 0,
            "median_endpoint_spread_delta": 0.0,
            "fraction_endpoint_spread_delta_gt_0p25": 0.0,
            "fraction_endpoint_spread_delta_ge_0p25": 0.0,
            "median_best_candidate_gap_delta": 0.0,
            "fraction_best_candidate_gap_delta_lt_neg_0p25": 0.0,
            "median_executed_endpoint_displacement": 0.1,
            "p95_executed_endpoint_displacement": 0.2,
            "danger_cross_fraction": 0.0,
            "lowdiv_collapse_fraction": 0.0,
        },
    }


def test_iter31_centroid_direction_uses_fit_rows_only_and_drops_constants():
    build = load_module("iter31_build_direction", BUILD)
    iter30 = load_module("iter30_localization_for_iter31", ITER30)
    rows = [
        bridge_row("fit", 1, [0.0, 0.0], [7.0], 1),
        bridge_row("fit", 1, [0.0, 2.0], [7.0], 2),
        bridge_row("fit", 0, [2.0, 4.0], [7.0], 3),
        bridge_row("fit", 0, [4.0, 6.0], [7.0], 4),
        bridge_row("heldout", 1, [100.0, 100.0], [100.0], 5),
    ]

    direction, arrays = build.derive_direction(iter30, rows)

    assert direction["feature_count"] == 3
    assert direction["fit_rows"] == 4
    assert direction["dropped_dimension_count"] == 1
    assert direction["constant_dimension_indices"] == [2]
    assert arrays["direction_raw"].tolist() == pytest.approx([3.0, 4.0, 0.0])
    assert direction["direction_raw"] == pytest.approx([3.0, 4.0, 0.0])


def test_iter31_replay_manifests_freeze_canary_and_primary_rows():
    build = load_module("iter31_build_direction_manifest", BUILD)
    rows = []
    for idx in range(8):
        rows.append(bridge_row("calibration", 1, [float(idx)], [0.0], 20 - idx))
        rows.append(bridge_row("calibration", 0, [float(idx)], [0.0], 40 - idx))
    rows.append(bridge_row("heldout", 1, [1.0], [0.0], 100))
    rows.append(bridge_row("heldout", 0, [2.0], [0.0], 101))

    manifests = build.make_replay_manifests(rows)

    assert len(manifests["canary"]) == 12
    assert sum(row["label_name"] == "eligible_lowdiv" for row in manifests["canary"]) == 6
    assert sum(row["label_name"] == "benign_control" for row in manifests["canary"]) == 6
    assert len(manifests["calibration"]) == 16
    assert len(manifests["heldout"]) == 2
    assert manifests["canary"] == sorted(manifests["canary"], key=build.key_tuple)


def test_iter31_row_metrics_measure_intervention_geometry_and_benign_harm():
    analyze = load_module("iter31_analyze_intervention", ANALYZE)
    row = {
        "scene": "scene-a",
        "split": "heldout",
        "sample_index": 1,
        "timestamp_us": 10,
        "label_name": "benign_control",
        "intervention_alpha": 0.5,
        "objs": [[2.0, 0.0]],
        "futs": [[[[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]]],
        "original_traj": [[0.0, 8.0], [0.0, 8.0], [0.0, 8.0]],
        "intervened_traj": [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]],
        "original_cands": [
            [[0.0, 0.0], [0.0, 0.0]],
            [[0.0, 0.0], [3.0, 0.0]],
            [[0.0, 0.0], [0.0, 4.0]],
        ],
        "intervened_cands": [
            [[0.0, 0.0], [0.0, 0.0]],
            [[0.0, 0.0], [1.0, 0.0]],
            [[0.0, 0.0], [0.0, 1.0]],
        ],
    }

    metrics = analyze.row_metrics(row)

    assert metrics["gross_valid"]
    assert metrics["original_endpoint_spread"] == 5.0
    assert metrics["intervened_endpoint_spread"] == 2**0.5
    assert metrics["benign_crossed_danger"]
    assert metrics["benign_collapsed_lowdiv"]
    assert metrics["executed_endpoint_displacement"] == (68**0.5)


def test_iter31_gap_delta_handles_no_object_infinity():
    analyze = load_module("iter31_analyze_gap_delta", ANALYZE)

    assert analyze.gap_delta(float("inf"), float("inf")) == 0.0


def test_iter31_iter_jsonl_reads_split_gzip_part_shards(tmp_path):
    analyze = load_module("iter31_analyze_gzip_part", ANALYZE)
    payload = json.dumps({"scene": "scene-a", "sample_index": 1, "timestamp_us": 10}) + "\n"
    compressed = gzip.compress(payload.encode("utf-8"))
    midpoint = len(compressed) // 2
    (tmp_path / "rows.jsonl.gz.part-0000").write_bytes(compressed[:midpoint])
    (tmp_path / "rows.jsonl.gz.part-0001").write_bytes(compressed[midpoint:])

    rows = list(
        analyze.iter_jsonl(
            [
                tmp_path / "rows.jsonl.gz.part-0000",
                tmp_path / "rows.jsonl.gz.part-0001",
            ]
        )
    )

    assert rows == [{"scene": "scene-a", "sample_index": 1, "timestamp_us": 10}]


def test_iter31_alpha_zero_reference_check_passes_matching_originals():
    analyze = load_module("iter31_analyze_alpha_zero_reference_pass", ANALYZE)
    reference = [
        {
            "scene": "scene-a",
            "sample_index": 1,
            "timestamp_us": 10,
            "traj": [[0.0, 0.0], [1.0, 1.0]],
            "cands": [
                [[0.0, 0.0], [1.0, 0.0]],
                [[0.0, 0.0], [0.0, 1.0]],
                [[0.0, 0.0], [1.0, 1.0]],
            ],
        }
    ]
    canary = [
        {
            "scene": "scene-a",
            "sample_index": 1,
            "timestamp_us": 10,
            "intervention_alpha": 0.0,
            "intervention_applied": False,
            "original_traj": reference[0]["traj"],
            "intervened_traj": reference[0]["traj"],
            "original_cands": reference[0]["cands"],
            "intervened_cands": reference[0]["cands"],
        }
    ]

    report = analyze.alpha_zero_reference_report(canary, reference)

    assert report["alpha_zero_reference_pass"]
    assert report["alpha_zero_rows"] == 1
    assert report["alpha_zero_max_abs_coordinate_error"] == 0.0


def test_iter31_alpha_zero_reference_check_fails_coordinate_drift():
    analyze = load_module("iter31_analyze_alpha_zero_reference_fail", ANALYZE)
    reference = [
        {
            "scene": "scene-a",
            "sample_index": 1,
            "timestamp_us": 10,
            "traj": [[0.0, 0.0], [1.0, 1.0]],
            "cands": [
                [[0.0, 0.0], [1.0, 0.0]],
                [[0.0, 0.0], [0.0, 1.0]],
                [[0.0, 0.0], [1.0, 1.0]],
            ],
        }
    ]
    canary = [
        {
            "scene": "scene-a",
            "sample_index": 1,
            "timestamp_us": 10,
            "intervention_alpha": 0.0,
            "intervention_applied": False,
            "original_traj": reference[0]["traj"],
            "intervened_traj": [[0.0, 0.0], [1.001, 1.0]],
            "original_cands": reference[0]["cands"],
            "intervened_cands": reference[0]["cands"],
        }
    ]

    report = analyze.alpha_zero_reference_report(canary, reference)

    assert not report["alpha_zero_reference_pass"]
    assert report["alpha_zero_reference_failure_count"] == 1
    assert "intervened_traj_vs_iter29_traj" in report["alpha_zero_reference_failures"][0]


def test_iter31_calibration_selects_largest_spread_then_smallest_alpha():
    analyze = load_module("iter31_analyze_selection", ANALYZE)
    cells = [
        passing_cell(0.0, 10.0),
        passing_cell(0.25, 0.6),
        passing_cell(0.50, 0.8),
        passing_cell(0.75, 0.8),
        passing_cell(1.00, 0.7),
    ]

    selected = analyze.select_calibration_alpha(cells)

    assert selected["selected"]
    assert selected["selected_alpha"] == 0.50
    assert not selected["cells"][0]["calibration_eligible"]
    assert "alpha_zero_not_selectable" in selected["cells"][0]["calibration_failures"]


def test_iter31_heldout_bars_report_positive_and_benign_failures():
    analyze = load_module("iter31_analyze_heldout", ANALYZE)
    metrics = []
    for _ in range(4):
        metrics.append(
            {
                "label_name": "eligible_lowdiv",
                "gross_valid": True,
                "endpoint_spread_delta": 0.1,
                "best_candidate_gap_delta": -0.5,
                "executed_endpoint_displacement": 0.0,
                "benign_crossed_danger": False,
                "benign_collapsed_lowdiv": False,
            }
        )
    for _ in range(4):
        metrics.append(
            {
                "label_name": "benign_control",
                "gross_valid": True,
                "endpoint_spread_delta": -0.4,
                "best_candidate_gap_delta": 0.0,
                "executed_endpoint_displacement": 3.0,
                "benign_crossed_danger": True,
                "benign_collapsed_lowdiv": True,
            }
        )

    report = analyze.heldout_bars(metrics)

    assert not report["s2_pass"]
    assert not report["s3_pass"]
    assert report["s2_failures"]
    assert report["s3_failures"]
