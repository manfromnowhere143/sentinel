"""Allocation, adverse-outcome and contract controls; no registered case execution."""

import copy
import json
from pathlib import Path

import pytest

from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter175_connection_allocation import adapter, check, comparison, contract
from tests.test_iter169_full_horizon_control import case, OLD
from tests.test_iter174_forward_integrated_rrt import PLAN as PREVIOUS

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("experiments/iter175_connection_allocation")
PLAN = dict(PREVIOUS, connection_attempt_budget=128)


def test_short_connection_charges_full_rollouts_and_exposes_family_truncation():
    c = case()
    q = query_for(c)
    events = []
    edges = adapter.Edges(c["geometry"], OLD, PLAN, lambda s: summary(q(s)),
                          lambda kind, row: events.append(dict(kind=kind, **row)))
    edges.directed([*c["geometry"]["reset"], 0], [100., .1, .03, 1.2, .02, 8.])
    row = events[-1]
    attempts, _ = check.connection_check(row, events[:-1], c, OLD, PLAN, 18000)
    assert attempts == edges.attempts == 128
    assert row["result"]["optimizer"]["started"] is False
    counts = comparison.coverage(events[:-1])
    assert counts["evaluations"] == dict(initial=1, fixed_pattern=15, halton=0)
    assert counts["transitions"] == dict(initial=8, fixed_pattern=120, halton=0)
    assert events[-2]["stopped"] == "attempt_budget"
    corrupted = copy.deepcopy(row)
    corrupted["result"]["attempts"] += 8
    with pytest.raises(ValueError):
        check.connection_check(corrupted, events[:-1], c, OLD, PLAN, 18000)


@pytest.mark.parametrize("key", ["attempt_budget", "per_run_seconds", "max_actions",
                               "connection_horizon", "max_proposals", "cases", "seeds"])
def test_only_connection_allowance_may_change(key):
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    contract.check_contract(ROOT, plan)
    plan[key] = list(reversed(plan[key])) if isinstance(plan[key], list) else plan[key] + 1
    with pytest.raises(ValueError, match="changed_contract:" + key):
        contract.check_contract(ROOT, plan)


@pytest.mark.parametrize("mutation,reason", [
    ("field", "plan_fields"), ("cap", "connection_cap"),
    ("reference", "reference_identity"), ("iteration", "study_identity"),
    ("adapter", "unchanged:adapter.py"), ("runtime", "unchanged:RUNTIME.json"),
    ("admission", "reference_changed:proof/admission.json"),
])
def test_contract_known_bads(monkeypatch, mutation, reason):
    plan = json.loads((ROOT / BASE / "PLAN.json").read_text())
    original = contract.read
    paths = {"adapter": str(BASE / "adapter.py"), "runtime": str(BASE / "RUNTIME.json"),
             "admission": contract.PREVIOUS + "proof/admission.json"}

    def altered(root, path):
        data = original(root, path)
        return data + b" " if str(path) == paths.get(mutation) else data

    monkeypatch.setattr(contract, "read", altered)
    if mutation == "field":
        plan["extra"] = True
    if mutation == "cap":
        plan["connection_attempt_budget"] = 256
    if mutation == "reference":
        plan["parent_commit"] = "0" * 40
    if mutation == "iteration":
        plan["iteration"] = 174
    with pytest.raises(ValueError, match=reason):
        contract.check_contract(ROOT, plan)


def paired():
    rows = [dict(case=str(i), seed=i, complete=i == 2, returned_frame=32 if i == 2 else 10,
                 attempts=100, directed_calls=2, accepted_connections=1, progress_checks=0)
            for i in range(4)]
    return copy.deepcopy(rows), dict(iteration=174, phase="closed", records=rows)


def test_paired_comparison_preserves_loss_even_when_another_case_gains():
    rows, old = paired()
    rows[2]["complete"] = False
    rows[0]["complete"] = True
    result = comparison.compare(rows, old)
    assert result["gained_cases"] == result["lost_cases"] == 1
    assert result["reference_complete_cases"] == 1
    assert result["pairs"][2]["reference_complete"] and not result["pairs"][2]["complete"]


@pytest.mark.parametrize("mutation,reason", [
    ("missing", "comparison_population"), ("order", "comparison_pair"),
    ("unknown", "comparison_outcome"), ("open", "reference_status"),
])
def test_invalid_comparisons_rejected(mutation, reason):
    rows, old = paired()
    if mutation == "missing":
        rows.pop()
    if mutation == "order":
        rows.reverse()
    if mutation == "unknown":
        rows[0]["complete"] = None
    if mutation == "open":
        old["phase"] = "running"
    with pytest.raises(ValueError, match=reason):
        comparison.compare(rows, old)


def test_family_counts_charge_each_evaluation_once_including_rejected_motion():
    rows = [dict(kind="request", id=1, evaluation=1, cached=False),
            dict(kind="request", id=2, evaluation=1, cached=True),
            dict(kind="request", id=3, evaluation=2, cached=False),
            dict(kind="request", id=83, evaluation=3, cached=False),
            dict(kind="request", id=84, evaluation=None, cached=False)]
    rows += [dict(kind="evaluation", id=i, trace=[{}] * (i+1)) for i in (1, 2, 3)]
    assert comparison.coverage(rows) == dict(
        evaluations=dict(initial=1, fixed_pattern=1, halton=1),
        transitions=dict(initial=1, fixed_pattern=2, halton=3))
