"""Analytic derivative known-bads and single-factor contract regressions."""

import copy
import json
from pathlib import Path
import numpy as np
import pytest
from scipy.optimize._numdiff import approx_derivative
from experiments.iter170_derivative_step.binding import compare


@pytest.mark.parametrize("sign", [-1, 1])
def test_near_zero_residual_derivative(sign):
    x = np.array([sign * 5.300924469105862e-17])

    def residual(x):
        return np.array([1 + x[0]])

    assert approx_derivative(residual, x, method="2-point", rel_step=1e-6).item() == 0
    assert approx_derivative(residual, x, method="2-point").item() == 1


def test_zero_uses_existing_fallback():
    assert (
        approx_derivative(
            lambda x: np.array([1 + x[0]]), np.zeros(1), method="2-point", rel_step=1e-6
        ).item()
        == 1
    )


def plans():
    root = Path(__file__).resolve().parents[1] / "experiments"
    return [
        json.loads((root / name / "PLAN.json").read_text())
        for name in ("iter169_full_horizon_control", "iter170_derivative_step")
    ]


def test_single_factor_accepted():
    compare(*plans())


@pytest.mark.parametrize(
    "key,value",
    [
        ("attempt_budget", 16384),
        ("cases", []),
        ("optimizer_tolerance", 1e-8),
        ("optimizer_diff_step", 1e-6),
    ],
)
def test_changed_contract_rejected(key, value):
    previous, current = plans()
    current = copy.deepcopy(current)
    current[key] = value
    with pytest.raises(ValueError):
        compare(previous, current)
