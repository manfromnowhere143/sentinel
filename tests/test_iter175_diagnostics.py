"""Arithmetic and discarded-continuation controls for post-outcome diagnostics."""

import copy
import json
from pathlib import Path

import pytest

from experiments.iter175_connection_allocation.diagnostics import horizon_coverage
from experiments.iter175_connection_allocation import contract


def rows():
    return [dict(kind="request", id=83, evaluation=1, cached=False),
            dict(kind="evaluation", id=1, interrupted=None, valid_prefix=2, selected_prefix=1,
                 trace=[dict(frame=30), dict(frame=31), dict(frame=32, route=dict(rc=.95))]),
            dict(kind="connection", call=7, task=dict(terminal_frame=2), result=dict(attempts=2))]


def test_horizon_accounting_keeps_later_prefix_distinct_from_completion():
    result = horizon_coverage(rows())
    assert result["by_horizon"] == {2: dict(calls=1, transitions=2, halton_transitions=2)}
    assert result["truncated_prefixes_at_or_after_final_checkpoint"] == [
        dict(call=7, evaluation=1, frame=32, progress=.95, selected_prefix=1, valid_prefix=2)]


def test_horizon_accounting_rejects_uncharged_motion():
    bad = copy.deepcopy(rows())
    bad[-1]["result"]["attempts"] = 1
    with pytest.raises(AssertionError):
        horizon_coverage(bad)


def test_retained_reference_allowance_cannot_drift(monkeypatch):
    root = Path(__file__).resolve().parents[1]
    plan = json.loads((root / contract.BASE / "PLAN.json").read_text())
    original = contract.read

    def changed(path_root, path):
        data = original(path_root, path)
        if str(path) == contract.PREVIOUS + "PLAN.json":
            old = json.loads(data)
            old["connection_attempt_budget"] = 512
            return json.dumps(old).encode()
        return data

    monkeypatch.setattr(contract, "read", changed)
    with pytest.raises(ValueError, match="reference_cap"):
        contract.check_contract(root, plan)
