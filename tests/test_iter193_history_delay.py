"""Clock equivariance, history preservation, native transport and known-bads."""

import copy
import json
import os
from pathlib import Path
import time

import pytest
from experiments.iter153_action_feasibility.geometry import route_outcome
from experiments.iter153_action_feasibility.planner import transition
from experiments.iter159_route_search_qualification.run import query_for
from experiments.iter158_constraint_aware_search.search import summary, prior_reason
from experiments.iter153_action_feasibility.geometry import obstacles
from experiments.iter191_stop_wait_release import fixtures, policy
from experiments.iter193_history_delay import clock, check, common, contract, worker

ROOT = Path(__file__).resolve().parents[1]
OLD = json.loads((ROOT / common.OLD).read_text())
PLANNER = json.loads((ROOT / common.PLANNER).read_text())


def test_complete_frozen_contract():
    assert contract.check_contract(ROOT, json.loads((ROOT / common.BASE / "PLAN.json").read_text()))


@pytest.mark.parametrize(
    "key,value",
    [
        ("conditions", []),
        ("parent_commit", "0" * 40),
        ("search_producer_seconds", 1801),
        ("search_checker_seconds", 7201),
        ("worker_supervisor_seconds", 181),
        ("source_files", []),
    ],
)
def test_prospective_design_mutation_rejected(key, value):
    plan = json.loads((ROOT / common.BASE / "PLAN.json").read_text())
    plan[key] = value
    with pytest.raises(ValueError, match="plan_changed|source_inventory"):
        contract.check_contract(ROOT, plan)


def constructed():
    case = fixtures.case("timed_curve")
    case["geometry"]["reset"][3] = 0
    case["geometry"]["comparators"]["checkpoint"]["hazard_time"] = 1.25
    query = query_for(case)
    state = case["geometry"]["reset"]
    history = [
        dict(
            id=i,
            frame=i,
            parent=i - 1 if i else None,
            state=state[:],
            action=[0.0, 0.0] if i else None,
            route=route_outcome(state, case["geometry"]["route"]),
            reason="clear",
            background=summary(query(state)),
        )
        for i in range(3)
    ]
    return case, history, query


@pytest.mark.parametrize("origin,delay", [(1, 0), (1, 1), (1, 2), (2, 0), (2, 1), (2, 2)])
def test_translation_preserves_policy_and_absolute_deadlines(origin, delay):
    case, history, query = constructed()
    prefix = clock.extend(history, origin, delay, case, OLD, query)
    assert prefix[: origin + 1] == history[: origin + 1]
    check.prefix_check(prefix, history, dict(origin=origin, delay=delay))
    local, config = clock.translate(case, PLANNER, prefix, OLD)
    independent, alternative = check.local_inputs(case, OLD, PLANNER, prefix)
    assert local == independent and config == alternative
    offset = origin + delay
    assert config["max_actions"] + offset == 401
    before = [*prefix[-1]["state"], offset]
    a = policy.Feedback(before, case["geometry"], OLD)
    b = policy.Feedback([*before[:5], 0], local["geometry"], OLD)
    state = before[:5]
    for i in range(1, 9):
        action = a.action(None, i, state)
        assert action == b.action(None, i, state)
        after = transition(state, action, OLD)
        assert prior_reason(
            state, after, action, offset + i, case["geometry"], OLD, obstacles(case["geometry"])
        ) == prior_reason(
            state, after, action, i, local["geometry"], OLD, obstacles(local["geometry"])
        )
        state = after


def test_zero_delay_exact_history_and_hold_action():
    case, history, query = constructed()
    history[-1]["action"] = [0.1, 0.01]
    assert clock.extend(history, 2, 0, case, OLD, query) == history
    prefix = clock.extend(history, 2, 2, case, OLD, query)
    check.prefix_check(prefix, history, dict(origin=2, delay=2))
    assert all(r["action"] == [0.1, 0.01] for r in prefix[3:])
    prefix[-1]["action"][0] += 1
    with pytest.raises(ValueError, match="held_command"):
        check.prefix_check(prefix, history, dict(origin=2, delay=2))


@pytest.mark.parametrize("origin,delay", [(0, 0), (3, 0), (1, -1), (1, 3), (1, 0.5)])
def test_invalid_clock_rejected(origin, delay):
    case, history, query = constructed()
    with pytest.raises(ValueError, match="origin_domain|delay_domain"):
        clock.extend(history, origin, delay, case, OLD, query)


def test_passed_checkpoint_cannot_reset_clock():
    case, history, _ = constructed()
    case["geometry"]["comparators"]["checkpoint"]["hazard_time"] = 0.25
    with pytest.raises(ValueError, match="past_checkpoint"):
        clock.translate(case, PLANNER, history, OLD)


def test_preserved_history_known_bad():
    case, history, query = constructed()
    prefix = clock.extend(history, 2, 0, case, OLD, query)
    prefix[1]["state"][0] += 0.01
    with pytest.raises(ValueError, match="preserved_history"):
        check.prefix_check(prefix, history, dict(origin=2, delay=0))


def test_integration_gate_rejects_miss_and_unadmitted_evidence():
    contract.integration_gate(dict(status="supported", complete_cases=4))
    for value in (
        dict(status="contradicted", complete_cases=3),
        dict(status="proposed", complete_cases=4),
    ):
        with pytest.raises(ValueError, match="integration_unqualified"):
            contract.integration_gate(value)


def test_rejected_prefix_never_searches(tmp_path, monkeypatch):
    case = fixtures.case("untimed")
    case["geometry"]["reset"] = [0, 0, 0, 0, 0]
    query = query_for(case)
    state = case["geometry"]["reset"]
    history = []
    for i, action in enumerate((None, [3, 0])):
        if action:
            state = transition(state, action, OLD)
        history.append(
            dict(
                id=i,
                frame=i,
                parent=0 if i else None,
                action=action,
                state=state[:],
                route=route_outcome(state, case["geometry"]["route"]),
                background=summary(query(state)),
                reason="controls" if i else "clear",
            )
        )

    def forbidden(*args, **kwargs):
        pytest.fail("search called on rejected prefix")

    monkeypatch.setattr(worker, "search", forbidden)
    condition = dict(id="rejected", origin=1, delay=0, seed=20261014)
    result = worker.collect(tmp_path, case, OLD, history, PLANNER, condition, None)
    result.update(worker_seconds=0.1, worker_peak_rss_bytes=common.rss())
    common.write(tmp_path / "result.json", result)
    value = check.case_check(
        tmp_path, case, OLD, history, PLANNER, condition, result, time.monotonic() + 60
    )
    assert value["stop"] == "prefix_ineligible" and len(value["rejections"]) == 1


def test_no_earlier_only_or_censored_success():
    rows = [
        dict(condition=c, complete=False, stop="attempt_budget")
        for c in contract.fixed()["conditions"]
    ]
    assert check.classify(rows) == "contradicted"
    rows[0]["complete"] = True
    assert check.classify(rows) == "contradicted"
    rows[3]["stop"] = "time_budget"
    assert check.classify(rows) == "inconclusive"
    rows[4]["complete"] = True
    assert check.classify(rows) == "supported"


@pytest.fixture(scope="module")
def acquired(tmp_path_factory):
    library = os.environ.get("SENTINEL_RRT186_LIBRARY")
    if not library:
        pytest.skip("qualified native library not supplied")
    case, history, _ = constructed()
    planner = dict(PLANNER, attempt_budget=512, per_run_seconds=10)
    condition = dict(id="constructed", origin=2, delay=1, seed=20261014)
    folder = tmp_path_factory.mktemp("iter193")
    started = time.monotonic()
    result = worker.collect(folder, case, OLD, history, planner, condition, Path(library))
    result.update(
        worker_seconds=time.monotonic() - started + 0.01, worker_peak_rss_bytes=common.rss()
    )
    common.write(folder / "result.json", result)
    return folder, case, history, planner, condition, result


def test_native_translation_execution_and_absolute_replay(acquired):
    folder, case, history, planner, condition, result = acquired
    value = check.case_check(
        folder, case, OLD, history, planner, condition, result, time.monotonic() + 60
    )
    assert value["complete"] and value["returned_frame"] > 5
    assert value["progress_checks"] == 1 and value["remaining_actions"] == 398


@pytest.mark.parametrize("kind", ["prefix", "join", "mask", "completion", "horizon"])
def test_native_corruption_rejected(acquired, kind, tmp_path):
    import shutil

    original, case, history, planner, condition, result = acquired
    folder = tmp_path / "raw"
    shutil.copytree(original, folder)
    result = copy.deepcopy(result)
    if kind == "prefix":
        path = folder / "prefix.json"
        value = json.loads(path.read_text())
        value[1]["state"][0] += 1
    elif kind == "join":
        path = folder / "selected/trace.json"
        value = json.loads(path.read_text())
        value[-1]["frame"] -= 1
    elif kind == "mask":
        path = folder / "selected/mask_000.bin"
        path.write_bytes(b"\xff")
        value = None
    else:
        result["complete" if kind == "completion" else "remaining_actions"] = (
            False if kind == "completion" else 401
        )
        path, value = folder / "result.json", result
    if value is not None:
        path.write_bytes(common.encode(value))
    with pytest.raises(ValueError):
        check.case_check(
            folder, case, OLD, history, planner, condition, result, time.monotonic() + 60
        )
