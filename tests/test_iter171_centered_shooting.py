"""Analytic near-zero failure and physical coordinate/accounting regressions."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace
import numpy as np
import pytest
from scipy.optimize import least_squares
from experiments.iter171_centered_shooting import shooting
from experiments.iter171_centered_shooting.binding import compare
from experiments.iter169_full_horizon_control.check import accounting
from tests.test_iter169_full_horizon_control import case, OLD, PLAN


@pytest.mark.parametrize("sign", [-1, 1])
def test_translation_avoids_near_zero_termination(sign):
    initial = sign * 5.300924469105862e-17
    settings = dict(
        method="trf",
        jac="2-point",
        tr_solver="exact",
        x_scale="jac",
        diff_step=None,
        ftol=1e-12,
        xtol=1e-12,
        gtol=1e-12,
        max_nfev=100,
    )
    bad = least_squares(
        lambda q: np.array([q[0] - sign * 0.5]), [initial], bounds=(-1, 1), **settings
    )
    good = least_squares(
        lambda d: np.array([initial + d[0] - sign * 0.5]),
        [0.0],
        bounds=([-1 - initial], [1 - initial]),
        **settings,
    )
    assert bad.success and abs(bad.x[0] - sign * 0.5) > 0.49
    assert abs(initial + good.x[0] - sign * 0.5) < 1e-10


def test_translation_preserves_initial_bounds_return_and_accounting(monkeypatch):
    seen = {}

    def fake(fun, x, **kwargs):
        assert np.array_equal(x, np.zeros_like(x))
        lo, hi = kwargs["bounds"]
        seed = -1 - lo
        assert np.allclose(seed + hi, 1)
        fun(x)
        delta = np.full_like(x, 0.01)
        fun(delta)
        seen["seed"] = seed
        seen["delta"] = delta
        return SimpleNamespace(x=delta, success=False, status=0, message="mock cap", nfev=2, njev=0)

    monkeypatch.setattr(shooting, "least_squares", fake)
    c = case()
    ev = []
    req = []
    result = shooting.search(
        c["geometry"],
        c["task"],
        OLD,
        dict(PLAN, optimizer_diff_step=None),
        lambda s: dict(certain_inside=0, count=0, possible_inside=0, decision="clear"),
        lambda kind, row: (req if kind == "request" else ev).append(row),
    )
    trace = result.pop("trace")
    result["materialization_queries"] = len(trace)
    assert np.allclose(ev[0]["values"], seen["seed"])
    assert np.allclose(req[-1]["values"], seen["seed"] + seen["delta"])
    assert req[-1]["cached"] and result["attempts"] == 6
    accounting(ev, req, trace, result, c, OLD, PLAN)


def plans():
    root = Path(__file__).resolve().parents[1] / "experiments"
    return [
        json.loads((root / name / "PLAN.json").read_text())
        for name in ("iter170_derivative_step", "iter171_centered_shooting")
    ]


def test_only_coordinates_change():
    compare(*plans())


@pytest.mark.parametrize(
    "key,value",
    [
        ("attempt_budget", 16384),
        ("optimizer_diff_step", 1e-6),
        ("cases", []),
        ("optimizer_coordinates", "absolute"),
    ],
)
def test_other_changes_rejected(key, value):
    old, new = plans()
    new = copy.deepcopy(new)
    new[key] = value
    with pytest.raises(ValueError):
        compare(old, new)
