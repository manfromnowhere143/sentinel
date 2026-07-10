from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/iter35_response_heterogeneity_audit/analyze_response_heterogeneity.py"


def load_module():
    spec = importlib.util.spec_from_file_location("iter35_response_heterogeneity", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def record(
    label_name: str,
    spread_slope: float,
    gap_slope: float = 0.01,
    alpha1_spread: float = 0.30,
    benign_disp: float = 0.10,
    object_count: int = 1,
) -> dict:
    return {
        "label_name": label_name,
        "endpoint_spread_slope": spread_slope,
        "best_candidate_gap_slope": gap_slope,
        "alpha1_endpoint_spread_delta": alpha1_spread,
        "alpha1_best_candidate_gap_delta": gap_slope,
        "alpha1_executed_endpoint_displacement": benign_disp,
        "alpha1_benign_crossed_danger": False,
        "alpha1_benign_collapsed_lowdiv": False,
        "baseline": {
            "object_count": object_count,
            "original_endpoint_spread": 0.75,
            "original_best_candidate_gap": 7.0,
            "original_executed_gap": 7.0,
        },
    }


def test_iter35_s1_accepts_measurable_two_sided_heterogeneity():
    module = load_module()
    rows = [record("eligible_lowdiv", 0.08) for _ in range(54)]
    rows.extend(record("eligible_lowdiv", -0.02) for _ in range(20))
    rows.extend(record("eligible_lowdiv", 0.02) for _ in range(34))

    report = module.evaluate_s1(rows)

    assert report["pass"]
    assert report["eligible_spread_slope_ge_0p05_rows"] == 54
    assert report["eligible_spread_slope_lt_0_rows"] == 20
    assert report["eligible_spread_slope_iqr"] >= 0.05


def test_iter35_s1_rejects_uniform_response():
    module = load_module()
    rows = [record("eligible_lowdiv", 0.02) for _ in range(108)]

    report = module.evaluate_s1(rows)

    assert not report["pass"]
    assert "eligible_spread_slope_ge_0p05_rows=0 < 20" in report["failures"]
    assert "eligible_spread_slope_lt_0_rows=0 < 20" in report["failures"]


def test_iter35_s2_accepts_actionable_stratum_with_benign_headroom():
    module = load_module()
    rows = [record("eligible_lowdiv", 0.10, 0.02, 0.35) for _ in range(24)]
    rows.extend(record("benign_control", 0.01, 0.00, 0.00, 0.10) for _ in range(100))

    report = module.evaluate_s2(rows)

    assert report["pass"]
    assert "best_candidate_safe" in report["passing_strata"]
    best_safe = next(item for item in report["strata"] if item["name"] == "best_candidate_safe")
    assert best_safe["eligible_support"] == 24
    assert best_safe["benign_support"] == 100
    assert best_safe["eligible_median_spread_slope"] == pytest.approx(0.10)


def test_iter35_s2_rejects_benign_harm():
    module = load_module()
    rows = [record("eligible_lowdiv", 0.10, 0.02, 0.35) for _ in range(24)]
    rows.extend(record("benign_control", 0.01, 0.00, 0.00, 3.00) for _ in range(100))

    report = module.evaluate_s2(rows)

    assert not report["pass"]
    best_safe = next(item for item in report["strata"] if item["name"] == "best_candidate_safe")
    assert any("benign_alpha1_median_executed_displacement" in item for item in best_safe["failures"])


def test_iter35_verdict_order():
    module = load_module()

    assert module.verdict(False, None, None) == "INFRASTRUCTURE_NULL_S0_ARTIFACT_OR_ROW_INTEGRITY"
    assert (
        module.verdict(True, {"pass": False}, None)
        == "HETEROGENEITY_NULL_UNIFORM_OR_TOO_NARROW_RESPONSE"
    )
    assert module.verdict(True, {"pass": True}, {"pass": False}) == "HETEROGENEITY_NULL_NO_ACTIONABLE_STRATUM"
    assert (
        module.verdict(True, {"pass": True}, {"pass": True})
        == "HETEROGENEITY_PASS_CONDITIONED_SUCCESSOR_PREREG_AUTHORIZED"
    )
