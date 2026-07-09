from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/iter34_direction_specificity_audit/analyze_direction_specificity.py"


def load_module():
    spec = importlib.util.spec_from_file_location("iter34_direction_specificity", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def cell(alpha: float, eligible_spread: float, benign_spread: float, gap: float = 0.1) -> dict:
    return {
        "alpha": alpha,
        "eligible_lowdiv": {
            "median_endpoint_spread_delta": eligible_spread,
            "fraction_endpoint_spread_delta_gt_0p25": 0.75 if eligible_spread > 0.25 else 0.2,
            "median_best_candidate_gap_delta": gap,
            "p95_executed_endpoint_displacement": 0.0,
        },
        "benign_control": {
            "median_endpoint_spread_delta": benign_spread,
            "p95_executed_endpoint_displacement": 0.2,
        },
    }


def metric(label_name: str, spread_delta: float) -> dict:
    return {
        "scene": "scene-a",
        "sample_index": 1,
        "timestamp_us": 10,
        "label_name": label_name,
        "endpoint_spread_delta": spread_delta,
    }


def per_alpha_metrics(spread_values: list[float]) -> dict[float, dict[tuple, dict]]:
    return {
        alpha: {
            ("scene-a", 1, 10): metric("eligible_lowdiv", spread),
            ("scene-b", 1, 10): metric("eligible_lowdiv", spread + 0.01),
        }
        for alpha, spread in zip((0.0, 0.25, 0.5, 0.75, 1.0), spread_values)
    }


def test_iter34_s1_accepts_monotonic_ordered_response():
    module = load_module()
    cells = [
        cell(0.0, 0.0, 0.0),
        cell(0.25, 0.12, 0.01),
        cell(0.5, 0.24, 0.02),
        cell(0.75, 0.36, 0.03),
        cell(1.0, 0.48, 0.04),
    ]

    report = module.evaluate_s1(cells, per_alpha_metrics([0.0, 0.12, 0.24, 0.36, 0.48]))

    assert report["pass"]
    assert report["eligible_alpha_pearson"] == pytest.approx(1.0)
    assert report["eligible_nonnegative_endpoint_spread_slope"]["fraction"] == 1.0


def test_iter34_s1_rejects_nonmonotonic_response():
    module = load_module()
    cells = [
        cell(0.0, 0.0, 0.0),
        cell(0.25, 0.12, 0.01),
        cell(0.5, 0.08, 0.02),
        cell(0.75, 0.18, 0.03),
        cell(1.0, 0.20, 0.04),
    ]

    report = module.evaluate_s1(cells, per_alpha_metrics([0.0, 0.12, 0.08, 0.18, 0.20]))

    assert not report["pass"]
    assert "eligible_nonzero_median_endpoint_spread_delta_not_strictly_increasing" in report["failures"]


def test_iter34_s2_rejects_nonspecific_gap_negative_response():
    module = load_module()
    cells = [
        cell(0.0, 0.0, 0.0, 0.0),
        cell(0.25, 0.0045, 0.0145, -0.00008),
        cell(0.5, 0.0099, 0.0288, -0.00003),
        cell(0.75, 0.0193, 0.0427, -0.00002),
        cell(1.0, 0.0308, 0.0545, -0.00005),
    ]

    report = module.evaluate_s2(cells)

    assert not report["pass"]
    assert any("alpha1_eligible_median_endpoint_spread_delta" in item for item in report["failures"])
    assert any("alpha1_eligible_to_benign_spread_ratio" in item for item in report["failures"])
    assert any("alpha1_eligible_median_best_candidate_gap_delta" in item for item in report["failures"])


def test_iter34_alpha_needed_uses_linear_fit():
    module = load_module()
    fit = module.linear_fit([0.0, 0.5, 1.0], [0.0, 0.125, 0.25])

    assert fit["slope"] == pytest.approx(0.25)
    assert module.alpha_needed_for_target(fit, 0.5) == pytest.approx(2.0)
