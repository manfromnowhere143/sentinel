"""Constructed control behavior and corruption checks; no original case runs."""

import copy
import itertools
import json
import math
from pathlib import Path
import random
import time

import numpy as np
import pytest

from experiments.iter153_action_feasibility.check import motion
from experiments.iter158_constraint_aware_search.search import summary
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter168_control_connector.check import physical, completed
from experiments.iter169_full_horizon_control.shooting import Controls
from experiments.iter172_integrated_rrt.connection import Evaluator, task_for
from experiments.iter173_matched_connector_cost.check import expected_proposal
from experiments.iter177_pose_aware_seed import adapter, check, contract, forward, seed, seed_check
from tests.test_iter169_full_horizon_control import case, OLD
from tests.test_iter175_connection_allocation import PLAN

ROOT = Path(__file__).resolve().parents[1]
BASE = Path("experiments/iter177_pose_aware_seed")


def controls(target=None, reset=None, horizon=8):
    return Controls(reset or [0., 0., 0., 1., 0.],
                    dict(target=target or [2., .2, .1, 1., 0.], terminal_frame=horizon,
                         wait_until=0, stop_from=None, tolerance=PLAN["target_tolerance"]))


def reflected(state):
    return [state[0], -state[1], -state[2], state[3], -state[4]]


def scalar_path(c, values):
    # Independent motion and physical constraints, not the producer transition.
    table = c.table(values)
    state = c.reset
    fixture = case()
    fixture["geometry"]["reset"] = state
    fixture["task"] = c.task
    for frame in range(1, c.task["terminal_frame"]+1):
        action = c.action(table, frame, state)
        after = motion(state, action)
        assert physical(state, after, action, frame, fixture, OLD) is None
        state = after
    return state


def cost(state, target):
    errors = [a-b for a, b in zip(state, target)]
    errors[2] = math.remainder(errors[2], 2*math.pi)
    return sum((d*w)**2 for d, w in zip(errors, [1, 1, 2, .5, 2]))


@pytest.mark.parametrize("side", [-1, 1])
def test_pose_targets_improve_but_are_not_exact_connections(side):
    c = controls(target=[2., side*.2, side*.1, 1., 0.])
    after = scalar_path(c, seed.initial(c))
    baseline = scalar_path(c, c.initial())
    assert cost(after, c.task["target"]) < cost(baseline, c.task["target"])
    assert not completed(after, 8, c.task)
    assert seed.initial(c)[1]*side > 0


def test_longitudinal_pose_changes_acceleration_with_fixed_target_speed():
    c = controls(target=[3., 0., 0., 1., 0.])
    assert c.initial()[0] == 0 and seed.initial(c)[0] > 0
    assert cost(scalar_path(c, seed.initial(c)), c.task["target"]) < cost(
        scalar_path(c, c.initial()), c.task["target"])


def test_adverse_exact_curved_baseline_is_lost_by_endpoint_approximation():
    c = controls()
    state = c.reset
    for _ in range(8):
        state = motion(state, [1., .2])
    c.task["target"] = state
    baseline = scalar_path(c, c.initial())
    candidate = scalar_path(c, seed.initial(c))
    assert completed(baseline, 8, c.task)
    assert not completed(candidate, 8, c.task)
    assert cost(candidate, state) > cost(baseline, state)+1e-5


@pytest.mark.parametrize("horizon", range(1, 17))
def test_independent_polynomial_reconstruction_reflection_and_endpoint_bounds(horizon):
    rng = random.Random(177+horizon)
    for _ in range(32):
        def state():
            return [rng.uniform(-10, 10), rng.uniform(-10, 10), rng.uniform(-math.pi, math.pi),
                    rng.uniform(0, 6), rng.uniform(-math.pi/3, math.pi/3)]
        c = controls(target=state(), reset=state(), horizon=horizon)
        values = seed.initial(c)
        np.testing.assert_allclose(values, seed_check.expected_seed(c.reset, c.task), rtol=0, atol=2e-14)
        reflected_values = seed.initial(controls(reflected(c.task["target"]), reflected(c.reset), horizon))
        np.testing.assert_allclose(reflected_values[::2], values[::2], rtol=0, atol=2e-14)
        np.testing.assert_allclose(reflected_values[1::2], -values[1::2], rtol=0, atol=2e-14)
        assert np.isfinite(values).all() and np.max(np.abs(values)) <= 1+1e-15
        duration = horizon/4
        assert -1e-12 <= c.reset[3]+2*values[0]*duration <= 6+1e-12
        assert abs(c.reset[4]+math.pi/12*values[1]*duration) <= math.pi/3+1e-12


def test_rigid_coordinates_preserve_control_guess():
    c = controls(reset=[1., 2., .3, 1.4, .1], target=[3., 3., .5, 2., .2])
    def move(state):
        x, y, heading, speed, steering = state
        a = .7
        return [5+x*math.cos(a)-y*math.sin(a), -3+x*math.sin(a)+y*math.cos(a),
                heading+a, speed, steering]
    other = controls(move(c.task["target"]), move(c.reset))
    np.testing.assert_allclose(seed.initial(c), seed.initial(other), rtol=0, atol=2e-14)


def test_one_step_cannot_use_new_steering_to_move_laterally():
    c = controls(target=[.25, 10., 0., 1., 0.], horizon=1)
    assert seed.initial(c).tolist() == [0., 0.]
    after = scalar_path(c, seed.initial(c))
    assert after[1] == 0 and not completed(after, 1, c.task)


@pytest.mark.parametrize("wait,stop", [(2, None), (0, 3), (8, None)])
def test_prescribed_phases_and_all_fallback_proposals_are_unchanged(wait, stop):
    c = controls()
    c.task.update(wait_until=wait, stop_from=stop)
    c = Controls(c.reset, c.task)
    np.testing.assert_array_equal(seed.initial(c), c.initial())
    for number, values in enumerate(itertools.islice(forward.proposals(c), 220)):
        np.testing.assert_allclose(values, expected_proposal(c.reset, c.task, number), rtol=0, atol=2e-15)


def test_only_initial_program_changes_and_corruptions_are_rejected():
    c = controls()
    requests = []
    for number, values in enumerate(itertools.islice(forward.proposals(c), 220)):
        if number:
            np.testing.assert_allclose(values, expected_proposal(c.reset, c.task, number), rtol=0, atol=2e-15)
        requests.append(dict(kind="request", caller="initial" if number == 0 else "forward_proposal",
                             values=values.tolist()))
    result = dict(optimizer=dict(started=False))
    seed_check.proposal_check(requests, c.reset, c.task, 4096, result)
    for number in [0, 15, 83]:
        bad = copy.deepcopy(requests); bad[number]["values"][1] += .001
        with pytest.raises(ValueError, match="numeric_replay"):
            seed_check.proposal_check(bad, c.reset, c.task, 4096, result)
    with pytest.raises(ValueError, match="forward_scope"):
        seed_check.proposal_check(requests, c.reset, c.task, 1, result)


def test_seed_has_no_motion_or_scene_dependency_and_expiry_charges_no_rollout(monkeypatch):
    c = case(); q = query_for(c); calls = []
    before = [*c["geometry"]["reset"], 7]
    target = [100., .2, .1, 1.5, 0., 15.]
    task = task_for(before, target, PLAN)
    ev = Evaluator(c["geometry"], before, target, task, OLD, PLAN, 128,
                   time.monotonic()-1, lambda s: summary(q(s)), lambda k, r: calls.append((k, r)))
    import experiments.iter153_action_feasibility.planner as planner
    def forbidden(*args):
        raise AssertionError("hidden motion or scene call")
    monkeypatch.setattr(planner, "transition", forbidden)
    ev.query = forbidden
    result = forward.solve(ev, True, 4096)
    assert result["attempts"] == 0 and result["stop"] == "time_budget"
    assert calls[-1][1]["stopped"] == "time_budget"


def test_connection_keeps_absolute_clock_and_full_rollout_budget():
    c = case(); q = query_for(c); events = []
    edges = adapter.Edges(c["geometry"], OLD, PLAN, lambda s: summary(q(s)),
                          lambda k, r: events.append(dict(kind=k, **r)))
    edges.directed([*c["geometry"]["reset"], 7], [100., .2, .1, 1.5, 0., 15.])
    row = events[-1]
    attempts, _ = check.connection_check(row, events[:-1], c, OLD, PLAN, 18000)
    assert attempts == edges.attempts == 128
    assert row["trace"][0]["frame"] == 7
    assert all(e["trace"][0]["frame"] == 7 for e in events if e["kind"] == "evaluation")
    for key in ["attempts", "queries"]:
        bad = copy.deepcopy(row); bad["result"][key] += 1
        with pytest.raises(ValueError):
            check.connection_check(bad, events[:-1], c, OLD, PLAN, 18000)


@pytest.mark.parametrize("key", ["attempt_budget", "per_run_seconds", "connection_attempt_budget",
                                "connection_horizon", "max_actions", "seeds", "cases"])
def test_no_scientific_plan_field_can_change(key):
    plan = json.loads((ROOT/BASE/"PLAN.json").read_text())
    contract.check_contract(ROOT, plan)
    plan[key] = list(reversed(plan[key])) if isinstance(plan[key], list) else plan[key]+1
    with pytest.raises(ValueError, match="changed_contract:"+key):
        contract.check_contract(ROOT, plan)


@pytest.mark.parametrize("name,reason", [("adapter.py", "adapter_substitution"),
                                         ("forward.py", "generator_substitution"),
                                         ("RUNTIME.json", "runtime_unchanged")])
def test_substitution_contract_rejects_additional_source_changes(monkeypatch, name, reason):
    plan = json.loads((ROOT/BASE/"PLAN.json").read_text())
    original = contract.read
    def altered(root, path):
        return original(root, path)+(b" " if Path(path) == BASE/name else b"")
    monkeypatch.setattr(contract, "read", altered)
    with pytest.raises(ValueError, match=reason):
        contract.check_contract(ROOT, plan)


@pytest.mark.parametrize("mutation,reason", [("fields", "plan_fields"),
                                             ("parent", "parent_identity"),
                                             ("iteration", "study_identity"),
                                             ("reference", "reference_changed:")])
def test_contract_identity_known_bads(monkeypatch, mutation, reason):
    plan = json.loads((ROOT/BASE/"PLAN.json").read_text())
    if mutation == "fields":
        plan["extra"] = True
    if mutation == "parent":
        plan["parent_commit"] = "0"*40
    if mutation == "iteration":
        plan["iteration"] = 176
    if mutation == "reference":
        original = contract.read
        def altered(root, path):
            return original(root, path)+(b" " if str(path) == contract.PREVIOUS+"proof/admission.json" else b"")
        monkeypatch.setattr(contract, "read", altered)
    with pytest.raises(ValueError, match=reason):
        contract.check_contract(ROOT, plan)
