"""Accepted-state composition and true excess rejection; no original-case solve."""

import copy
import json
import math
from pathlib import Path
import time

import numpy as np
import pytest

from experiments.iter153_action_feasibility.check import motion
from experiments.iter153_action_feasibility.planner import limits
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter169_full_horizon_control.shooting import Controls as StrictControls
from experiments.iter177_pose_aware_seed.seed import initial
from experiments.iter178_root_domain_consistency import adapter, check, connection, contract
from experiments.iter178_root_domain_consistency.controls import Controls
from tests.test_iter169_full_horizon_control import case, OLD
from tests.test_iter175_connection_allocation import PLAN

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("experiments/iter178_root_domain_consistency")
INSIDE = [(3, -1e-12), (3, 6+1e-12), (4, math.pi/3+1e-12), (4, -math.pi/3-1e-12)]
OUTSIDE = [(3, math.nextafter(-1e-12, -math.inf)), (3, math.nextafter(6+1e-12, math.inf)),
           (4, math.nextafter(math.pi/3+1e-12, math.inf)),
           (4, math.nextafter(-math.pi/3-1e-12, -math.inf))]


@pytest.mark.parametrize("index,value", INSIDE)
def test_existing_motion_tolerance_is_accepted_without_state_projection(index, value):
    c = case(); state = [0., 0., 0., .1, 0.]; state[index] = value
    assert limits(state, [0., 0.], OLD)
    control = Controls(state, c["task"])
    assert control.reset is state and control.reset[index] == value
    with pytest.raises(ValueError, match="reset_bounds"):
        StrictControls(state, c["task"])
    assert np.isfinite(initial(control)).all()


@pytest.mark.parametrize("index,value", OUTSIDE)
def test_real_excess_still_fails_the_constructor_and_physical_gate(index, value):
    c = case(); state = [0., 0., 0., .1, 0.]; state[index] = value
    assert not limits(state, [0., 0.], OLD)
    with pytest.raises(ValueError, match="reset_bounds"):
        Controls(state, c["task"])


def test_observed_boundary_sequence_composes_without_rounding_state():
    state = [0., 0., 0., 4., 0.]
    for _ in range(5):
        state = motion(state, [1.6, -math.pi/12])
        assert limits(state, [1.6, -math.pi/12], OLD)
    assert state[3] == 6.000000000000002
    control = Controls(state, case()["task"])
    assert control.reset is state
    with pytest.raises(ValueError, match="reset_bounds"):
        StrictControls(state, case()["task"])


def test_constructor_preserves_original_controls_for_strict_interior_state():
    c = case()
    corrected = Controls(c["geometry"]["reset"], c["task"])
    original = StrictControls(c["geometry"]["reset"], c["task"])
    assert corrected.variables == original.variables
    np.testing.assert_array_equal(corrected.initial(), original.initial())
    np.testing.assert_array_equal(initial(corrected), initial(original))


def test_composed_connection_keeps_clock_budget_and_separate_scalar_admission():
    c = case(); c["geometry"]["reset"][3] = 6.000000000000002
    q = query_for(c); events = []
    edges = adapter.Edges(c["geometry"], OLD, PLAN, lambda s: summary(q(s)),
                          lambda kind, row: events.append(dict(kind=kind, **row)))
    before = [*c["geometry"]["reset"], 5]
    edges.directed(before, [100., .1, .02, 6., 0., 13.])
    row = events[-1]
    attempts, _ = check.connection_check(row, events[:-1], c, OLD, PLAN, 18000)
    assert attempts == edges.attempts == 128 and row["before"] == before
    assert row["trace"][0]["state"][3] == 6.000000000000002
    assert row["trace"][0]["frame"] == 5
    for field in ["attempts", "queries"]:
        bad = copy.deepcopy(row); bad["result"][field] += 1
        with pytest.raises(ValueError):
            check.connection_check(bad, events[:-1], c, OLD, PLAN, 18000)


def test_scene_validation_remains_authoritative_after_domain_acceptance():
    c = case(); state = c["geometry"]["reset"]; state[3] = 6.000000000000002
    Controls(state, c["task"])
    before = [*state, 5]; target = [100., 0., 0., 1., 0., 13.]
    task = connection.task_for(before, target, PLAN)
    with pytest.raises(ValueError, match="connection_root"):
        connection.Evaluator(c["geometry"], before, target, task, OLD, PLAN, 128,
                             time.monotonic()+120, lambda state: dict(decision="collision"), lambda *args: None)


@pytest.mark.parametrize("key", ["attempt_budget", "per_run_seconds", "connection_attempt_budget",
                                "connection_horizon", "max_actions", "cases", "seeds"])
def test_corrective_trial_cannot_change_scientific_plan_fields(key):
    plan = json.loads((ROOT/BASE/"PLAN.json").read_text())
    contract.check_contract(ROOT, plan)
    plan[key] = list(reversed(plan[key])) if isinstance(plan[key], list) else plan[key]+1
    with pytest.raises(ValueError, match="changed_contract:"+key):
        contract.check_contract(ROOT, plan)


@pytest.mark.parametrize("name,reason", [("controls.py", "constructor_substitution"),
                                         ("connection.py", "evaluator_substitution"),
                                         ("adapter.py", "adapter_substitution"),
                                         ("RUNTIME.json", "runtime_unchanged")])
def test_source_substitution_known_bads(monkeypatch, name, reason):
    plan = json.loads((ROOT/BASE/"PLAN.json").read_text()); original = contract.read
    def altered(root, path):
        return original(root, path)+(b" " if Path(path) == BASE/name else b"")
    monkeypatch.setattr(contract, "read", altered)
    with pytest.raises(ValueError, match=reason):
        contract.check_contract(ROOT, plan)


@pytest.mark.parametrize("mutation,reason", [("field", "plan_fields"), ("parent", "parent_identity"),
                                             ("iteration", "study_identity"), ("reference", "reference_changed:")])
def test_correction_identity_known_bads(monkeypatch, mutation, reason):
    plan = json.loads((ROOT/BASE/"PLAN.json").read_text()); original = contract.read
    if mutation == "field":
        plan["extra"] = 0
    if mutation == "parent":
        plan["parent_commit"] = "0"*40
    if mutation == "iteration":
        plan["iteration"] = 177
    if mutation == "reference":
        def altered(root, path):
            return original(root, path)+(b" " if str(path) == contract.PREVIOUS+"proof/admission.json" else b"")
        monkeypatch.setattr(contract, "read", altered)
    with pytest.raises(ValueError, match=reason):
        contract.check_contract(ROOT, plan)


def test_false_valid_predecessor_cannot_replace_the_invalid_record(monkeypatch):
    plan = json.loads((ROOT/BASE/"PLAN.json").read_text())
    original_read, original_git = contract.read, contract.git
    path = contract.PREVIOUS+"proof/admission.json"
    doc = json.loads(original_read(ROOT, path)); doc["status"] = "supported"
    corrupted = json.dumps(doc).encode()
    monkeypatch.setattr(contract, "read", lambda root, name: corrupted if str(name) == path else original_read(root, name))
    monkeypatch.setattr(contract, "git", lambda root, *args: corrupted if args == ("show", contract.PARENT+":"+path) else original_git(root, *args))
    with pytest.raises(ValueError, match="invalid_predecessor"):
        contract.check_contract(ROOT, plan)
